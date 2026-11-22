from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Account, AuditLog
from app.schemas import AccountResponse, AuditLogResponse

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.get("", response_model=List[AccountResponse])
def list_accounts(db: Session = Depends(get_db)):
    """
    List all accounts
    """
    accounts = db.query(Account).order_by(Account.id.asc()).all()
    return accounts
  
@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(db: Session = Depends(get_db)):
    """
    List all audit logs
    """
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).all()
    return logs


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account by ID."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account