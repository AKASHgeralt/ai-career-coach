from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Without this, create_engine(None) fails with "Expected string or URL
    # object, got None", which says nothing about the missing variable. The
    # same guard exists in alembic/env.py.
    raise RuntimeError(
        "DATABASE_URL is not set. Set it in backend/.env for local development, "
        "or in the hosting provider's environment settings."
    )

engine = create_engine(
    DATABASE_URL,
    # Serverless Postgres (Neon) suspends an idle database, and the host may
    # keep this process alive across that suspension — so a pooled connection
    # can be dead by the time it is handed out. pool_pre_ping tests each one
    # and transparently replaces it, instead of failing the first request
    # after an idle period with "server closed the connection unexpectedly".
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()