from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now()) 