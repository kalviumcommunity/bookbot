"""
database.py — SQLAlchemy engine, session factory, and table initialisation.

Uses SQLite stored at backend/bookbot.db.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================
# DATABASE URL
# ============================================================

# Support DATABASE_URL env var for cloud deployments (PostgreSQL, etc.).
# Falls back to a local SQLite file for development.
_here = os.path.dirname(os.path.abspath(__file__))
_sqlite_default = f"sqlite:///{os.path.join(_here, 'bookbot.db')}"
DATABASE_URL: str = os.getenv("DATABASE_URL", _sqlite_default)

# ============================================================
# ENGINE & SESSION
# ============================================================

# SQLite requires check_same_thread=False; PostgreSQL does not accept it.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
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


def migrate_tables() -> None:
    """
    Safely add any new columns that don't yet exist in the DB.

    SQLAlchemy's create_all() only creates brand-new tables; it never alters
    existing ones.  When we add nullable columns to an ORM model we must also
    issue ALTER TABLE … ADD COLUMN for databases that were created before the
    column existed.

    This function is idempotent — it reads PRAGMA table_info first and only
    issues ALTER TABLE when the column is genuinely absent.
    """
    _ensure_column("quiz_attempts", "source_type",    "VARCHAR(20)")
    _ensure_column("quiz_attempts", "questions_json", "TEXT")
    _ensure_column("quiz_attempts", "answers_json",   "TEXT")


def _ensure_column(table: str, column: str, col_type: str) -> None:
    """Add *column* to *table* if it does not already exist."""
    with engine.connect() as conn:
        # PRAGMA table_info returns one row per column
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        existing = {row[1] for row in rows}  # index 1 = column name
        if column not in existing:
            conn.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            )
            conn.commit()


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
