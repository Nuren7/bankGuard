import json
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction, AuditLog
from app.security import verify_webhook_signature

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/clearing", status_code=status.HTTP_200_OK)
async def clearing_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    db: Session = Depends(get_db)
):
    """
    Receive a clearing event and verify its HMAC-SHA256 signature.
    """
    raw_body = await request.body()

    if not verify_webhook_signature(raw_body, x_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid HMAC signature.",
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON webhook payload.",
        )

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must be a JSON object.",
        )

    transaction_id = payload.get("transaction_id")
    event = payload.get("event", "CLEARING_CONFIRMED")

    if transaction_id is not None:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if tx:
            audit_entry = AuditLog(
                transaction_id=tx.id,
                event_type=f"WEBHOOK_{event}",
                details=f"Verified clearing event received: {json.dumps(payload)}",
                created_at=datetime.utcnow()
            )
            db.add(audit_entry)
            db.commit()

    return {"status": "verified", "event": event}