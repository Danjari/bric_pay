from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base import Base

class TransactionType(enum.Enum):
    """Transaction type enumeration"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"

class Transaction(Base):
    """Transaction model for Bric Pay application"""
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Transaction details
    from_account = Column(String(20), ForeignKey('users.account_number'), nullable=True, index=True)
    to_account = Column(String(20), ForeignKey('users.account_number'), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    from_user = relationship("User", foreign_keys=[from_account], backref="sent_transactions")
    to_user = relationship("User", foreign_keys=[to_account], backref="received_transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, from='{self.from_account}', to='{self.to_account}', amount={self.amount})>"
    
    def to_dict(self):
        """Convert transaction object to dictionary"""
        return {
            'id': self.id,
            'from_account': self.from_account,
            'to_account': self.to_account,
            'amount': float(self.amount) if self.amount else 0.00,
            'transaction_type': self.transaction_type.value if self.transaction_type else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 