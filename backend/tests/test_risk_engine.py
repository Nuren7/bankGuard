import asyncio
import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import ai_analyzer
from app.services.rule_engine import evaluate_rules


def test_rules_block_extreme_amounts():
    result = evaluate_rules(100_000, False, datetime(2026, 1, 1, 12))

    assert result.risk_score == 100
    assert result.decision == "BLOCK"
    assert "hard limit" in result.reason


def test_rules_require_step_up_for_large_foreign_overnight_payment():
    result = evaluate_rules(25_000, True, datetime(2026, 1, 1, 2))

    assert result.risk_score == 100
    assert result.decision == "BLOCK"
    assert "High amount" in result.reason
    assert "Foreign payment" in result.reason
    assert "overnight" in result.reason


def test_rules_approve_low_risk_payment():
    result = evaluate_rules(500, False, datetime(2026, 1, 1, 12))

    assert result.risk_score == 5
    assert result.decision == "APPROVE"


def test_rules_require_step_up_for_large_payment():
    result = evaluate_rules(25_000, False, datetime(2026, 1, 1, 12))

    assert result.risk_score == 55
    assert result.decision == "STEP_UP_AUTH"


def _mock_groq_response(content: str):
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
        close=AsyncMock(),
    )
    return client, create


@pytest.mark.asyncio
async def test_ai_valid_json_response_is_combined_with_rules(monkeypatch):
    client, _ = _mock_groq_response(
        json.dumps(
            {
                "risk_score": 65,
                "decision": "STEP_UP_AUTH",
                "reason": "Unusual recipient.",
            }
        )
    )
    monkeypatch.setattr(ai_analyzer, "AsyncGroq", lambda **_: client)
    monkeypatch.setattr(ai_analyzer.settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(ai_analyzer, "_record_success", lambda: None)

    result = await ai_analyzer.analyze_transaction_with_ai(
        500, False, datetime(2026, 1, 1, 12), "Test recipient"
    )

    assert result.risk_score == 65
    assert result.decision == "STEP_UP_AUTH"
    assert "Unusual recipient" in result.reason


@pytest.mark.asyncio
async def test_ai_invalid_json_falls_back_to_deterministic_rules(monkeypatch):
    client, _ = _mock_groq_response("not json")
    monkeypatch.setattr(ai_analyzer, "AsyncGroq", lambda **_: client)
    monkeypatch.setattr(ai_analyzer.settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(ai_analyzer, "_record_failure", lambda: None)

    result = await ai_analyzer.analyze_transaction_with_ai(
        500, False, datetime(2026, 1, 1, 12), "Test recipient"
    )

    assert result == evaluate_rules(500, False, datetime(2026, 1, 1, 12), "Test recipient")


@pytest.mark.asyncio
async def test_ai_timeout_falls_back_to_deterministic_rules(monkeypatch):
    client, create = _mock_groq_response("")

    async def timeout(*args, **kwargs):
        await asyncio.sleep(1)

    create.side_effect = timeout
    monkeypatch.setattr(ai_analyzer, "AsyncGroq", lambda **_: client)
    monkeypatch.setattr(ai_analyzer.settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(ai_analyzer, "_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(ai_analyzer, "_record_failure", lambda: None)

    result = await ai_analyzer.analyze_transaction_with_ai(
        500, False, datetime(2026, 1, 1, 12), "Test recipient"
    )

    assert result == evaluate_rules(500, False, datetime(2026, 1, 1, 12), "Test recipient")


@pytest.mark.asyncio
async def test_ai_api_error_falls_back_to_deterministic_rules(monkeypatch):
    client, create = _mock_groq_response("")
    create.side_effect = RuntimeError("API unavailable")
    monkeypatch.setattr(ai_analyzer, "AsyncGroq", lambda **_: client)
    monkeypatch.setattr(ai_analyzer.settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(ai_analyzer, "_record_failure", lambda: None)

    result = await ai_analyzer.analyze_transaction_with_ai(
        500, False, datetime(2026, 1, 1, 12), "Test recipient"
    )

    assert result == evaluate_rules(500, False, datetime(2026, 1, 1, 12), "Test recipient")