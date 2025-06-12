from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from typing import Generator

DATABASE_URL = "sqlite:///./sindri.db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None:
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup.

    Usage:
        with get_session() as session:
            # do something with session
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()