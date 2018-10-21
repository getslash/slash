import os
import logbook
from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from contextlib import contextmanager, closing
from datetime import datetime, timedelta
from slash.plugins import manager
from ast import literal_eval
from .utils.path import ensure_directory
from .conf import config
from .__version__ import __backslash_version__

_DB_NAME = 'resume_state_v1.db'
_logger = logbook.Logger(__name__)
Base = declarative_base()
_session = sessionmaker()
_db_initialized = False

class ResumeState(Base):
    __tablename__ = 'resume_state'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False, index=True)
    function_name = Column(String, nullable=False, index=True)
    variation = Column(String, index=True)
    status = Column(String, nullable=False, index=True)


class SessionMetadata(Base):
    __tablename__ = 'session_metadata'
    session_id = Column(String, primary_key=True)
    src_folder = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)


class ResumeTestStatus(object):
    PLANNED = 'planned'
    SUCCESS = 'success'
    FAILED = 'failed'


class ResumedTestData(object):

    def __init__(self, file_name, function_name, variation=None, status=None):
        self.file_name = file_name
        self.function_name = function_name
        self.variation = variation
        self.status = status

    def __repr__(self):
        return '<ResumedTestData({!r}, {!r}, {!r}, {!r})>'.format(self.file_name, self.function_name, self.variation, self.status)

    def __eq__(self, other):
        return self.file_name == other.file_name and self.function_name == other.function_name and \
               self.variation == other.variation and self.status == other.status

def _init_db():
    resume_dir = os.path.expanduser(config.root.run.resume_state_path)
    ensure_directory(resume_dir)
    engine = create_engine('sqlite:///{}/{}'.format(resume_dir, _DB_NAME))
    _session.configure(bind=engine)
    Base.metadata.create_all(engine)


@contextmanager
def connecting_to_db():
    global _db_initialized  # pylint: disable=global-statement
    if not _db_initialized:
        _init_db()
        _db_initialized = True
    with closing(_session()) as new_session:
        yield new_session
        max_retries = 3
        for i in range(max_retries):
            try:
                new_session.commit() # pylint: disable=no-member
            except OperationalError:
                if i == max_retries - 1:
                    raise


def clean_old_entries():
    # pylint: disable=no-member
    with connecting_to_db() as conn:
        old_sessions_query = conn.query(SessionMetadata).filter \
            (SessionMetadata.created_at < datetime.now() - timedelta(days=config.root.resume.state_retention_days))
        old_sessions_ids = [session.session_id for session in old_sessions_query.all()]
        if old_sessions_ids:
            conn.query(ResumeState).filter(ResumeState.session_id.in_(old_sessions_ids)).delete(synchronize_session=False)
        old_sessions_query.delete(synchronize_session=False)


def save_resume_state(session_result):
    session_metadata = SessionMetadata(
        session_id=session_result.session.id,
        src_folder=os.path.abspath(os.getcwd()),
        created_at=datetime.now())

    tests_to_resume = []
    for result in session_result.iter_test_results():
        metadata = result.test_metadata
        test_to_resume = ResumeState(session_id=session_result.session.id, file_name=metadata.file_path, function_name=metadata.function_name)
        test_to_resume.variation = str(metadata.variation.id) if metadata.variation else None
        if result.is_success_finished():
            test_to_resume.status = ResumeTestStatus.SUCCESS
        elif not result.is_started() or result.is_skip():
            test_to_resume.status = ResumeTestStatus.PLANNED
        else:
            test_to_resume.status = ResumeTestStatus.FAILED
        tests_to_resume.append(test_to_resume)

    with connecting_to_db() as conn:
        conn.add(session_metadata) # pylint: disable=no-member
        conn.add_all(tests_to_resume) # pylint: disable=no-member
    _logger.debug('Saved resume state to DB')


def get_last_resumeable_session_id():
    current_folder = os.path.abspath(os.getcwd())
    with connecting_to_db() as conn:
         # pylint: disable=no-member
        session_id = conn.query(SessionMetadata).filter(SessionMetadata.src_folder == current_folder) \
                                                .order_by(SessionMetadata.created_at.desc()).first()
        if not session_id:
            raise CannotResume("No sessions found for folder {}".format(current_folder))
        return session_id.session_id

def _get_resume_status_from_backslash_status(backslash_status):
    if backslash_status in ['FAILURE', 'ERROR', 'INTERRUPTED']:
        return ResumeTestStatus.FAILED
    elif backslash_status in ['SUCCESS']:
        return ResumeTestStatus.SUCCESS
    else:
        return ResumeTestStatus.PLANNED

def get_tests_from_remote(session_id, get_successful_tests):
    backslash_plugin = manager.get_active_plugins().get('backslash', None)
    if not backslash_plugin:
        raise CannotResume("Could not find backslash plugin")
    if not hasattr(backslash_plugin, 'is_session_exist') or not hasattr(backslash_plugin, 'get_tests_to_resume'):
        raise CannotResume("Backslash plugin doesn't support remote resuming")
    if not backslash_plugin.is_session_exist(session_id):
        raise CannotResume("Could not find resume data for session {}".format(session_id))
    backslash_version = tuple([int(x) for x in __backslash_version__.split(".")[:2]])
    kwargs = {'filters_dict': {'show_successful': get_successful_tests}} if backslash_version > (2, 32) else {'get_successful': get_successful_tests}
    remote_tests = backslash_plugin.get_tests_to_resume(session_id, **kwargs)
    return [ResumedTestData(test.info['file_name'],
                            test.info['name'],
                            variation=test.variation,
                            status=_get_resume_status_from_backslash_status(test.status))
            for test in remote_tests]

def get_tests_locally(session_id):
    resumed_tests = []
    with connecting_to_db() as conn:
        # pylint: disable=no-member
        if conn.query(SessionMetadata).filter(SessionMetadata.session_id == session_id).first():
            local_tests = conn.query(ResumeState).filter(ResumeState.session_id == session_id).all()
            resumed_tests = [ResumedTestData(test.file_name,
                                             test.function_name,
                                             variation=literal_eval(test.variation) if test.variation else None,
                                             status=test.status)
                            for test in local_tests]
    return resumed_tests

def _filter_tests(tests, get_successful_tests):
    unstarted_only, failed_only = config.root.resume.unstarted_only, config.root.resume.failed_only
    if unstarted_only and failed_only:
        raise CannotResume("Got both unstarted_only and failed_only, cannot resume")
    filtered_status = [ResumeTestStatus.SUCCESS] if get_successful_tests else []
    if unstarted_only:
        filtered_status.append(ResumeTestStatus.PLANNED)
    elif failed_only:
        filtered_status.append(ResumeTestStatus.FAILED)
    else:
        filtered_status.extend([ResumeTestStatus.FAILED, ResumeTestStatus.PLANNED])
    return list(filter(lambda test: test.status in filtered_status, tests))

def _sort_tests(tests):
    unstarted_first, failed_first = config.root.resume.unstarted_first, config.root.resume.failed_first
    if unstarted_first and failed_first:
        raise CannotResume("Got both failed_first and planned_first, cannot choose")
    if failed_first or unstarted_first:
        wanted_status_first = ResumeTestStatus.PLANNED if unstarted_first else ResumeTestStatus.FAILED
        first_tests = list(filter(lambda test: test.status in wanted_status_first, tests))
        other_tests = list(filter(lambda test: test.status not in wanted_status_first, tests))
        return first_tests + other_tests
    return tests

def get_tests_from_previous_session(session_id, get_successful_tests=False):
    resumed_tests = get_tests_locally(session_id)
    if not resumed_tests:
        _logger.debug('No local entry for session {}, searching remote session', session_id)
        resumed_tests = get_tests_from_remote(session_id, get_successful_tests)

    return _sort_tests(_filter_tests(resumed_tests, get_successful_tests))
class CannotResume(Exception):
    pass
