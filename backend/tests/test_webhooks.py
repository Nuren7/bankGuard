import hashlib
import hmac
import json


def test_clearing_webhook_rejects_missing_or_invalid_signature(client):
    payload = json.dumps({"event": "CLEARING_CONFIRMED"}).encode()

    missing = client.post("/api/webhooks/clearing", content=payload)
    invalid = client.post(
        "/api/webhooks/clearing",
        content=payload,
        headers={"X-Signature": "sha256=" + "0" * 64},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401


def test_clearing_webhook_accepts_valid_signature(client):
    payload = json.dumps({"event": "CLEARING_CONFIRMED"}).encode()
    signature = hmac.new(
        b"test-hmac-secret", payload, hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/webhooks/clearing",
        content=payload,
        headers={"X-Signature": f"sha256={signature}"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "verified", "event": "CLEARING_CONFIRMED"}