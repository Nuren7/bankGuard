import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Account(Base):
  __tablename__: "accounts"
  
  id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(32), unique=True, index=True, nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="SEK")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    transactions = relationship("Transaction",back_populates="account")
    
class Transaction(Base):
  __tablename__ = "transactions"
  
  id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    recipient = Column(String(128), nullable=False)
    is_foreign = Column(Integer, default=0) # 0 = No, 1 = Yes
    status = Column(String(32), nullable=False) # PENDING, APPROVED, STEP_UP_REQUIRED, BLOCKED
    risk_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")
    audit_logs = relationship("AuditLog", back_populates="transactions")
    
    class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    event_type = Column(String(64), nullable=False) # e.g. RULE_EVALUATION, AI_ANALYSIS, PAYMENT_PROCESSED
    details = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transaction = relationship("Transaction", back_populates="audit_logs")
    