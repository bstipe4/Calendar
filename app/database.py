import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_HOST = os.environ.get("DB_HOST") or "127.0.0.1"
DB_USER = os.environ.get("DB_USER") or "postgres"
DB_PASS = os.environ.get("DB_PASS") or "postgres"
DB_NAME = os.environ.get("DB_NAME") or "postgres"


SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
