"""
database.py — SQLAlchemy engine, session factory, and table initialisation.

Uses SQLite stored at backend/bookbot.db.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================
# DATABASE URL
# ============================================================

# Store the database file alongside this module (backend/bookbot.db).
_here = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(_here, 'bookbot.db')}"

# ============================================================
# ENGINE & SESSION
# ============================================================

engine = create_engine(
    DATABASE_URL,
    # Required for SQLite when used with FastAPI's async-style requests
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base class for all ORM models
Base = declarative_base()


# ============================================================
# HELPERS
# ============================================================

def create_tables() -> None:
    """Create all tables that don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is
    closed after the request, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
