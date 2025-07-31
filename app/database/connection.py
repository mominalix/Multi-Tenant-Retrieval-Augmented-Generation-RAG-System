"""
Database connection utilities and initialization
"""
import logging
from sqlalchemy import text
from app.database.base import Base
from app.database.session import engine

logger = logging.getLogger(__name__)


async def init_db():
    """
    Initialize database connection and create tables
    """
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Create all tables
        create_tables()
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def create_tables():
    """
    Create all database tables
    """
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from app.models import tenant, document, query
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")
        
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        raise


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
        
    except Exception as e:
        logger.error(f"Table dropping failed: {e}")
        raise