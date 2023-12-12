from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
import os

# DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = "mysql+pymysql://root:root123@34.68.249.238/buyer"
# Create a new engine instance
engine = create_engine(DATABASE_URL)

# Create a custom session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a new instance of the declarative base class
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
