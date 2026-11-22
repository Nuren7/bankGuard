import asyncio
import json
import logging
import threading
import time
from datetime import datetime

from groq import AsyncGroq

from app.config import settings
from app.services.rule_engine import RiskAssessment, evaluate_rules


logger = logging.getLogger(__name__)
_TIMEOUT_SECONDS = 3.0
_CLEANUP_TIMEOUT_SECONDS = 0.1
_FAILURE_THRESHOLD = 3
_BREAKER_COOLDOWN_SECONDS = 30.0
_breaker_lock = threading.Lock()
_failure_count = 0
_open_until = 0.0


def _breaker_is_open() -> bool:
    with _breaker_lock:
        return time.monotonic() < _open_until


def _record_success() -> None:
    global _failure_count, _open_until
    with _breaker_lock:
        _failure_count = 0
        _open_until = 0.0


def _record_failure() -> None:
    global _failure_count, _open_until
    with _breaker_lock:
        _failure_count += 1
        if _failure_count >= _FAILURE_THRESHOLD:
            _open_until = time.monotonic() + _BREAKER_COOLDOWN_SECONDS


def _combine_assessments(rules: RiskAssessment, ai: RiskAssessment) -> RiskAssessment:
    priorities = {"APPROVE": 0, "STEP_UP_AUTH": 1, "BLOCK": 2}
    score_decision = (
        "BLOCK"
        if ai.risk_score >= 80
        else "STEP_UP_AUTH"
        if ai.risk_score >= 50
        else "APPROVE"
    )
    ai_decision = max((ai.decision, score_decision), key=priorities.__getitem__)
    decision = max((rules.decision, ai_decision), key=priorities.__getitem__)
    score = max(rules.risk_score, ai.risk_score)
    if decision == "BLOCK":
        score = max(score, 80)
    elif decision == "STEP_UP_AUTH":
        score = max(score, 50)

    reason = rules.reason
    if ai.decision != "APPROVE" or ai.risk_score > rules.risk_score:
        reason = f"{rules.reason} AI-bedömning: {ai.reason}"
    return RiskAssessment(risk_score=min(score, 100), decision=decision, reason=reason)


async def analyze_transaction_with_ai(
    amount: float,
    is_foreign: bool,
    timestamp: datetime,
    recipient: str,
) -> RiskAssessment:
    rules = evaluate_rules(amount, is_foreign, timestamp, recipient)
    if rules.decision == "BLOCK" or not settings.GROQ_API_KEY or _breaker_is_open():
        return rules

    client = None
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    cleanup_budget = min(_CLEANUP_TIMEOUT_SECONDS, _TIMEOUT_SECONDS / 10)
    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=_TIMEOUT_SECONDS)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Assess payment fraud risk. Return only JSON with integer "
                            "risk_score from 1 to 100, decision (APPROVE, STEP_UP_AUTH, "
                            "or BLOCK), and a short reason."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "amount_sek": amount,
                                "is_foreign": is_foreign,
                                "timestamp": timestamp.isoformat(),
                                "recipient": recipient,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0,
            ),
            timeout=max(0.001, deadline - time.monotonic() - cleanup_budget),
        )
        ai_result = RiskAssessment.model_validate_json(response.choices[0].message.content)
        _record_success()
        return _combine_assessments(rules, ai_result)
    except (asyncio.TimeoutError, ValueError, TypeError, AttributeError) as exc:
        logger.warning("Groq AI assessment failed; using deterministic rules: %s", exc)
        _record_failure()
        return rules
    except Exception as exc:
        # SDK/API errors do not share one stable exception type across SDK versions.
        logger.warning("Groq AI assessment failed; using deterministic rules: %s", exc)
        _record_failure()
        return rules
    finally:
        if client is not None:
            remaining = deadline - time.monotonic()
            try:
                if remaining > 0:
                    await asyncio.wait_for(
                        client.close(), timeout=min(cleanup_budget, remaining)
                    )
            except Exception as exc:
                logger.warning("Could not close Groq client cleanly: %s", exc)