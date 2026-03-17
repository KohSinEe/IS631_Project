"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create engine
# For SQLite, we need check_same_thread=False
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=settings.DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def apply_startup_schema_patches() -> None:
    """Apply lightweight compatibility patches for local SQLite databases.

    This avoids runtime failures when models evolve but a local DB file still
    has an older schema.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as conn:
        table_exists = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not table_exists:
            return

        cols = {
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
        }

        if "cognito_sub" not in cols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN cognito_sub VARCHAR(255)")

        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_cognito_sub ON users (cognito_sub)"
        )


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
