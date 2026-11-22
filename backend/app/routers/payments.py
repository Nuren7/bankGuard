from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Account, Transaction, AuditLog
from app.schemas import PaymentRequest, PaymentResponse
from app.services.ai_analyzer import analyze_transaction_with_ai

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.post("", response_model=PaymentResponse)
async def process_payment(payment: PaymentRequest, idempotency_key: str = Header(..., description="Idempotency key"), db: Session = Depends(get_db)):
  
  """
  Process a payment with idempotency protection, row-level locking,
  and AI-assisted fraud risk analysis.
  """
  
  # Check for an existing transaction with the same idempotency key.
  existing_tx = db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()
  if existing_tx:
    account = db.query(Account).filter(Account.id == existing_tx.account_id).first()
    return PaymentResponse(
            transaction_id=existing_tx.id,
            status=existing_tx.status,
            risk_score=existing_tx.risk_score,
            reason=existing_tx.reason,
            new_balance=float(existing_tx.balance_after)
      )
    
  # Lock the account row to prevent concurrent balance updates.
  account = db.query(Account).filter(Account.id == payment.account_id).with_for_update().first()
  if not account:
    raise HTTPException(status_code=404, detail="Account not found")

  # Check that the account has sufficient funds.
  current_balance = Decimal(account.balance)
  payment_amount = Decimal(str(payment.amount))
  if current_balance < payment_amount:
    raise HTTPException(status_code=400, detail="Insufficient funds")
  
  # Evaluate transaction risk.
  timestamp = datetime.utcnow()
  risk_result = await analyze_transaction_with_ai(
    amount=payment.amount,
    is_foreign=bool(payment.is_foreign),
    timestamp=timestamp,
    recipient=payment.recipient
  )
  
  # Map the risk decision to a transaction status.
  tx_status = "APPROVED" 
  if risk_result.decision == "BLOCK":
    tx_status = "BLOCKED"
  elif risk_result.decision == "STEP_UP_AUTH":
    tx_status = "STEP_UP_REQUIRED"
    
  # Deduct the amount only when the payment is approved.
  if tx_status == "APPROVED":
    account.balance = current_balance - payment_amount
  
  # Save the transaction and its audit record.
  
  new_transaction = Transaction(
        idempotency_key=idempotency_key,
        account_id=account.id,
        amount=payment_amount,
        recipient=payment.recipient,
        is_foreign=payment.is_foreign,
        status=tx_status,
        risk_score=risk_result.risk_score,
        reason=risk_result.reason,
        balance_after=account.balance,
        created_at=timestamp
      )
  db.add(new_transaction)
  try:
    db.flush()
    audit_log = AuditLog(
          transaction_id=new_transaction.id,
          event_type="AI_RISK_EVALUATION",
          details=f"Decision: {risk_result.decision}, risk score: {risk_result.risk_score}. Reason: {risk_result.reason}",
          created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()
  except IntegrityError:
    db.rollback()
    existing_tx = db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()
    if existing_tx is None:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Could not process idempotency key")
    return PaymentResponse(
        transaction_id=existing_tx.id,
        status=existing_tx.status,
        risk_score=existing_tx.risk_score,
        reason=existing_tx.reason,
        new_balance=float(existing_tx.balance_after),
    )
  db.refresh(new_transaction)

  return PaymentResponse(
        transaction_id=new_transaction.id,
        status=new_transaction.status,
        risk_score=new_transaction.risk_score,
        reason=risk_result.reason,
        new_balance=float(account.balance)
  )