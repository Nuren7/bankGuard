import hashlib
import hmac
import re

from app.config import settings


_SIGNATURE_PATTERN = re.compile(r"(?:sha256=)?([0-9a-fA-F]{64})\Z")


def verify_webhook_signature(payload: bytes, signature: str | None) -> bool:
    """Verify an HMAC-SHA256 signature supplied as hex or ``sha256=<hex>``."""
    secret = settings.HMAC_SECRET
    if not secret or not signature:
        return False

    match = _SIGNATURE_PATTERN.fullmatch(signature)
    if match is None:
        return False

    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, match.group(1).lower())