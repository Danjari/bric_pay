from sqlalchemy import Column, Integer, String, DateTime, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
from .base import Base

class User(Base):
    """User model for Bric Pay application"""
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User information
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Personal information
    date_of_birth = Column(DateTime, nullable=False)
    place_of_birth = Column(String(100), nullable=False)
    
    # Account information
    account_number = Column(String(20), nullable=False, unique=True, index=True)
    balance = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('phone', name='uq_user_phone'),
        UniqueConstraint('account_number', name='uq_user_account_number'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', account_number='{self.account_number}')>"
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'place_of_birth': self.place_of_birth,
            'account_number': self.account_number,
            'balance': float(self.balance) if self.balance else 0.00,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 