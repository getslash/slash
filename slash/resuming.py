import os
import logbook
from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from datetime import datetime

_RESUME_DIR = os.path.expanduser("~/.slash/session_states")
_DB_NAME = 'resume_state.db'
_logger = logbook.Logger(__name__)
Base = declarative_base()
session = sessionmaker()
is_db_initialized = False

class ResumeState(Base):
    __tablename__ = 'resume_state'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    test_name = Column(String, nullable=False)

class SessionMetadata(Base):
    __tablename__ = 'session_metadata'
    session_id = Column(String, primary_key=True)
    src_folder = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)

def init_db():
    engine = create_engine('sqlite:///{0}/{1}'.format(_RESUME_DIR, _DB_NAME))
    session.configure(bind=engine)
    Base.metadata.create_all(engine)

@contextmanager
def connecting_to_db():
    global is_db_initialized
    if not is_db_initialized:
        init_db()
        is_db_initialized = True
    new_session = session()
    try:
        yield new_session
        new_session.commit()
    except:
        raise
    finally:
        new_session.close()

def save_resume_state(session_result, collected):
    metadata = SessionMetadata(
                    session_id=session_result.session.id,
                    src_folder=os.getcwd(),
                    created_at=datetime.now())

    passed_tests_names = [result.test_metadata.resume_repr for result in session_result.iter_test_results() if result.is_success_finished()]
    collected_test_names = [test.__slash__.resume_repr for test in collected]
    failed_test_names = list(set(collected_test_names) - set(passed_tests_names))
    session_tests = [ResumeState(session_id=session_result.session.id, test_name=test_name) for test_name in failed_test_names]

    with connecting_to_db() as conn:
        conn.add(metadata)
        conn.add_all(session_tests)
    _logger.debug('Saved resume state to DB')

def get_last_resumeable_session_id():
    current_folder = os.getcwd()
    with connecting_to_db() as conn:
        session_id = conn.query(SessionMetadata).filter(SessionMetadata.src_folder == current_folder).order_by(SessionMetadata.created_at.desc()).first()
        if not session_id:
            raise CannotResume("No sessions found for folder {0}".format(current_folder))
        return session_id.session_id

def get_tests_to_resume(session_id):
    session_tests = []
    with connecting_to_db() as conn:
        session_tests_query = conn.query(ResumeState).filter(ResumeState.session_id == session_id)
        session_tests = [test.test_name for test in session_tests_query.all()]
    if not session_tests:
        raise CannotResume("Could not find resume data for session {0}".format(session_id))
    return session_tests

class CannotResume(Exception):
    pass
