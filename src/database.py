from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine
if "sqlite" in settings.database_url:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug  # Log SQL queries in debug mode
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        echo=settings.debug  # Log SQL queries in debug mode
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    from src.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def drop_tables():
    """Drop all database tables (use with caution!)"""
    from src.models import Base
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped successfully")

def init_db():
    """Initialize database with tables"""
    create_tables()
    logger.info("Database initialized successfully") 