from decimal import Decimal
from unittest.mock import AsyncMock

from app.models import Account, Transaction
from app.routers import payments
from app.services.rule_engine import RiskAssessment


def test_repeated_payment_with_same_key_is_charged_once(client, test_db, monkeypatch):
    with test_db() as db:
        db.add(Account(account_number="TEST-001", balance=Decimal("500.00"), currency="SEK"))
        db.commit()
        account_id = db.query(Account).filter_by(account_number="TEST-001").one().id

    monkeypatch.setattr(
        payments,
        "analyze_transaction_with_ai",
        AsyncMock(
            return_value=RiskAssessment(
                risk_score=5,
                decision="APPROVE",
                reason="No elevated risk.",
            )
        ),
    )
    request = {
        "account_id": account_id,
        "amount": 100.00,
        "recipient": "Test recipient",
        "is_foreign": 0,
    }
    headers = {"Idempotency-Key": "repeat-payment-1"}

    first = client.post("/api/payments", json=request, headers=headers)
    second = client.post("/api/payments", json=request, headers=headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    with test_db() as db:
        assert db.query(Account).filter_by(id=account_id).one().balance == Decimal("400.00")
        assert db.query(Transaction).count() == 1