# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from talentscope.config import DBConfig

# Engine
engine = create_engine(DBConfig.URL, echo=False)

# SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Model
Base = declarative_base()

def get_db():
    """
    Dependency for FastAPI route handlers.
    Yields a DB session and ensures it closes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Creates tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)
