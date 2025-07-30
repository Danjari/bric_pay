"""
Database Transaction Management Utilities
Provides robust transaction handling with proper rollback mechanisms and concurrent access handling
"""
import logging
import time
from contextlib import contextmanager
from typing import Optional, Callable, Any, Dict
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy.exc import (
    IntegrityError, 
    OperationalError, 
    DisconnectionError,
    TimeoutError as SQLAlchemyTimeoutError
)
from sqlalchemy import text

logger = logging.getLogger(__name__)

class TransactionManager:
    """Enhanced transaction management for database operations"""
    
    # Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # seconds
    LOCK_TIMEOUT = 30  # seconds
    DEADLOCK_RETRY_DELAY = 0.5  # seconds
    
    @classmethod
    @contextmanager
    def transaction(cls, db: Session, description: str = "Database operation"):
        """
        Context manager for database transactions with automatic rollback on error
        
        Args:
            db (Session): Database session
            description (str): Description of the operation for logging
            
        Yields:
            Session: Database session
            
        Raises:
            Exception: Any exception that occurs during the transaction
        """
        logger.debug(f"Starting transaction: {description}")
        
        try:
            yield db
            db.commit()
            logger.debug(f"Transaction committed successfully: {description}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction rolled back due to error: {description} - {e}")
            raise
    
    @classmethod
    def with_retry(cls, max_retries: int = None, retry_delay: float = None):
        """
        Decorator for retrying database operations with exponential backoff
        
        Args:
            max_retries (int): Maximum number of retry attempts
            retry_delay (float): Base delay between retries
            
        Returns:
            Callable: Decorated function
        """
        max_retries = max_retries or cls.MAX_RETRIES
        retry_delay = retry_delay or cls.RETRY_DELAY
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                        
                    except (OperationalError, DisconnectionError, SQLAlchemyTimeoutError) as e:
                        last_exception = e
                        if attempt < max_retries:
                            delay = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                            logger.info(f"Retrying in {delay:.2f} seconds...")
                            time.sleep(delay)
                        else:
                            logger.error(f"Database operation failed after {max_retries + 1} attempts: {e}")
                            raise
                            
                    except IntegrityError as e:
                        # Integrity errors (constraint violations) should not be retried
                        logger.error(f"Integrity error in database operation: {e}")
                        raise
                        
                    except Exception as e:
                        # Other exceptions should not be retried
                        logger.error(f"Unexpected error in database operation: {e}")
                        raise
                
                # This should never be reached, but just in case
                raise last_exception
                
            return wrapper
        return decorator
    
    @classmethod
    def with_deadlock_handling(cls, db: Session, operation: Callable, *args, **kwargs):
        """
        Execute operation with deadlock detection and handling
        
        Args:
            db (Session): Database session
            operation (Callable): Operation to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Any: Result of the operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        max_attempts = cls.MAX_RETRIES + 1
        
        for attempt in range(max_attempts):
            try:
                with cls.transaction(db, f"Deadlock-protected operation (attempt {attempt + 1})"):
                    return operation(*args, **kwargs)
                    
            except IntegrityError as e:
                # Check if it's a deadlock (SQLite doesn't have deadlocks, but other DBs might)
                if "deadlock" in str(e).lower() or "lock" in str(e).lower():
                    if attempt < max_attempts - 1:
                        delay = cls.DEADLOCK_RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Deadlock detected (attempt {attempt + 1}/{max_attempts}): {e}")
                        logger.info(f"Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Deadlock persisted after {max_attempts} attempts: {e}")
                        raise
                else:
                    # Non-deadlock integrity error
                    raise
            except Exception as e:
                # Non-deadlock error
                raise
        
        # This should never be reached
        raise Exception("Unexpected error in deadlock handling")
    
    @classmethod
    def acquire_row_lock(cls, db: Session, table: str, row_id: int, timeout: int = None):
        """
        Acquire a row-level lock for concurrent access control
        
        Args:
            db (Session): Database session
            table (str): Table name
            row_id (int): Row ID to lock
            timeout (int): Lock timeout in seconds
            
        Note:
            This is a placeholder for row-level locking.
            SQLite doesn't support row-level locks, but this can be implemented
            for other databases like PostgreSQL or MySQL.
        """
        timeout = timeout or cls.LOCK_TIMEOUT
        
        # For SQLite, we'll use a simple approach
        # In production with other databases, this would use SELECT ... FOR UPDATE
        try:
            # Execute a query that would lock the row in other databases
            result = db.execute(text(f"SELECT id FROM {table} WHERE id = :row_id"), {"row_id": row_id})
            if not result.fetchone():
                raise ValueError(f"Row {row_id} not found in table {table}")
            
            logger.debug(f"Row lock acquired for {table}.id = {row_id}")
            
        except Exception as e:
            logger.error(f"Failed to acquire row lock for {table}.id = {row_id}: {e}")
            raise
    
    @classmethod
    def check_connection_health(cls, db: Session) -> bool:
        """
        Check if database connection is healthy
        
        Args:
            db (Session): Database session
            
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            # Execute a simple query to test connection
            db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection health check failed: {e}")
            return False
    
    @classmethod
    def get_transaction_info(cls, db: Session) -> Dict[str, Any]:
        """
        Get information about the current transaction
        
        Args:
            db (Session): Database session
            
        Returns:
            Dict: Transaction information
        """
        try:
            # Get transaction isolation level (SQLite specific)
            result = db.execute(text("PRAGMA journal_mode"))
            journal_mode = result.fetchone()[0] if result.fetchone() else "unknown"
            
            result = db.execute(text("PRAGMA synchronous"))
            synchronous = result.fetchone()[0] if result.fetchone() else "unknown"
            
            return {
                "isolation_level": "SERIALIZABLE",  # SQLite default
                "journal_mode": journal_mode,
                "synchronous": synchronous,
                "is_active": db.is_active,
                "autoflush": db.autoflush,
                "autocommit": db.autocommit
            }
        except Exception as e:
            logger.error(f"Failed to get transaction info: {e}")
            return {"error": str(e)}

def atomic_operation(description: str = None):
    """
    Decorator for atomic database operations
    
    Args:
        description (str): Description of the operation
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find database session in arguments
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            
            if not db:
                for value in kwargs.values():
                    if isinstance(value, Session):
                        db = value
                        break
            
            if not db:
                raise ValueError("Database session not found in function arguments")
            
            op_description = description or f"{func.__name__} operation"
            
            with TransactionManager.transaction(db, op_description):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def with_connection_retry(max_retries: int = 3):
    """
    Decorator for retrying operations on connection failures
    
    Args:
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return TransactionManager.with_retry(max_retries)(func)(*args, **kwargs)
        return wrapper
    return decorator 