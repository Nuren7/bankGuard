from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Decision = Literal["APPROVE", "STEP_UP_AUTH", "BLOCK"]


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=1, le=100)
    decision: Decision
    reason: str


def evaluate_rules(
    amount: float,
    is_foreign: bool,
    timestamp: datetime | None = None,
    recipient: str = "",
) -> RiskAssessment:
    """Evaluate the fixed, deterministic payment risk rules."""
    local_time = timestamp or datetime.now()
    hour = local_time.hour
    reasons = []
    score = 5

    if amount >= 100_000:
        return RiskAssessment(
            risk_score=100,
            decision="BLOCK",
            reason="Amount reaches the hard limit of 100,000 SEK.",
        )

    if amount > 20_000:
        score += 50
        reasons.append("High amount above 20,000 SEK")
    if is_foreign:
        score += 35
        reasons.append("Foreign payment")
    if 1 <= hour < 5:
        score += 30
        reasons.append("Transaction during overnight hours (01:00–05:00)")

    score = min(score, 100)
    if score >= 80:
        decision: Decision = "BLOCK"
    elif score >= 50:
        decision = "STEP_UP_AUTH"
    else:
        decision = "APPROVE"

    reason = "; ".join(reasons) if reasons else "No risk rules were triggered."
    return RiskAssessment(risk_score=score, decision=decision, reason=reason)