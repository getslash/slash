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

_RESUME_DIR = os.path.expanduser("~/.slash/session_states")
_DB_NAME = 'resume_state.db'
_MAX_DAYS_SAVED_SESSIONS = 10
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


class SessionMetadata(Base):
    __tablename__ = 'session_metadata'
    session_id = Column(String, primary_key=True)
    src_folder = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)


class ResumedTestData(object):

    def __init__(self, file_name, function_name, variation=None):
        self.file_name = file_name
        self.function_name = function_name
        self.variation = variation

    def __repr__(self):
        return '<ResumedTestData({!r}, {!r}, {!r})>'.format(self.file_name, self.function_name, self.variation)


def _init_db():
    ensure_directory(_RESUME_DIR)
    engine = create_engine('sqlite:///{0}/{1}'.format(_RESUME_DIR, _DB_NAME))
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
            (SessionMetadata.created_at < datetime.now() - timedelta(days=_MAX_DAYS_SAVED_SESSIONS))
        old_sessions_ids = [session.session_id for session in old_sessions_query.all()]
        if old_sessions_ids:
            conn.query(ResumeState).filter(ResumeState.session_id.in_(old_sessions_ids)).delete(synchronize_session=False)
        old_sessions_query.delete(synchronize_session=False)


def save_resume_state(session_result, collected):
    session_metadata = SessionMetadata(
        session_id=session_result.session.id,
        src_folder=os.path.abspath(os.getcwd()),
        created_at=datetime.now())

    passed_tests_names = [result.test_metadata for result in session_result.iter_test_results() if result.is_success_finished()]
    collected_test_names = [test.__slash__ for test in collected]
    failed_metadata = list(set(collected_test_names) - set(passed_tests_names))

    tests_to_resume = []
    for metadata in failed_metadata:
        test_to_resume = ResumeState(session_id=session_result.session.id, file_name=metadata.file_path, function_name=metadata.function_name)
        if metadata.variation:
            test_to_resume.variation = str(metadata.variation.id)
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
            raise CannotResume("No sessions found for folder {0}".format(current_folder))
        return session_id.session_id


def get_tests_to_resume(session_id):
    returned = []
    with connecting_to_db() as conn:
         # pylint: disable=no-member
        session_metadata = conn.query(SessionMetadata).filter(SessionMetadata.session_id == session_id).first()
        if session_metadata:
            session_tests = conn.query(ResumeState).filter(ResumeState.session_id == session_id).all()
            if not session_tests:
                _logger.debug('Found session {0} locally, but no failed tests exist'.format(session_id))
                return returned
            for test in session_tests:
                new_entry = ResumedTestData(test.file_name, test.function_name)
                if test.variation:
                    new_entry.variation = literal_eval(test.variation)
                returned.append(new_entry)
    if not returned:
        _logger.debug('No local entry for session {0}, searching remote session'.format(session_id))
        returned = resume_remote_session(session_id)
    return returned


def resume_remote_session(session_id):
    active_plugins = manager.get_active_plugins()
    backslash_plugin = active_plugins.get('backslash', None)
    if not backslash_plugin:
        raise CannotResume("Could not find backslash plugin")
    if not hasattr(backslash_plugin, 'is_session_exist') or not hasattr(backslash_plugin, 'get_tests_to_resume'):
        raise CannotResume("Backslash plugin doesn't support remote resuming")
    if not backslash_plugin.is_session_exist(session_id):
        raise CannotResume("Could not find resume data for session {0}".format(session_id))
    remote_tests = backslash_plugin.get_tests_to_resume(session_id)
    returned = [ResumedTestData(test.info['file_name'], test.info['name'], test.variation) for test in remote_tests]
    return returned


class CannotResume(Exception):
    pass
