from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, SQLModel, Session
from .config import settings


connect_args = {}#"check_same_thread": False}
engine = create_engine(str(settings.database.url), connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine) 

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
