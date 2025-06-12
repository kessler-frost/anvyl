from sqlmodel import Session, create_engine
from sqlalchemy.engine import Engine

def get_engine() -> Engine:
    return create_engine("sqlite:///sindri.db")

def get_session() -> Session:
    return Session(get_engine())

def init_db():
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(get_engine()) 