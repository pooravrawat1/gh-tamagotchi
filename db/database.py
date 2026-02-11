"""
Database initialization and connection management.

This module provides database engine creation, session management,
and table initialization functions. It supports both SQLite and PostgreSQL.
"""

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from db.models import Base
from config.settings import get_settings


# Global engine and session factory (initialized on first use)
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """
    Get or create the database engine.
    
    The engine is created once and reused for all connections.
    For SQLite, enables foreign key constraints and uses StaticPool
    for in-memory databases.
    
    Returns:
        SQLAlchemy Engine instance
    """
    global _engine
    
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url
        
        # Configure engine based on database type
        if database_url.startswith("sqlite"):
            # SQLite-specific configuration
            connect_args = {"check_same_thread": False}
            
            # Use StaticPool for in-memory databases
            if ":memory:" in database_url or "mode=memory" in database_url:
                _engine = create_engine(
                    database_url,
                    connect_args=connect_args,
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                _engine = create_engine(
                    database_url,
                    connect_args=connect_args,
                    echo=False
                )
            
            # Enable foreign key constraints for SQLite
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # PostgreSQL or other databases
            _engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                echo=False
            )
    
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the session factory.
    
    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Provides automatic session cleanup and rollback on errors.
    
    Usage:
        with get_db_session() as session:
            # Use session here
            session.query(PetDB).all()
    
    Yields:
        SQLAlchemy Session instance
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """
    Create all database tables defined in the models.
    
    This function is idempotent - it will only create tables that don't exist.
    Existing tables are not modified.
    
    Should be called during application startup to ensure database schema exists.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data in the database.
    Should only be used in testing or development environments.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


def reset_database() -> None:
    """
    Drop and recreate all tables.
    
    WARNING: This will delete all data in the database.
    Useful for testing or resetting development environment.
    """
    drop_tables()
    create_tables()


def close_db_connection() -> None:
    """
    Close database connections and dispose of the engine.
    
    Should be called during application shutdown to clean up resources.
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
    
    _SessionLocal = None


async def check_db_health() -> bool:
    """
    Check if database connection is healthy.
    
    Attempts a simple query to verify database connectivity.
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Simple query to test connection
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
