"""The OpenRouter backend of ``LlmClient``: the request it sends, how it reads the reply, and
how it copes with rate limits. No network: ``FakeHttp`` stands in for ``requests.post``."""

import json
from typing import Any

import pytest
from pydantic import model_validator

from saa.contracts.base import Contract, Tier
from saa.llm import (
    OPENROUTER_DEFAULT_MODEL,
    LlmClient,
    QuotaExhausted,
    openrouter_models,
    resolve_provider,
)
from tests.test_macro_agent import FakeAnthropic


class Verdict(Contract):
    score: float
    note: str | None = None

    @model_validator(mode="after")
    def _in_range(self) -> "Verdict":
        if not 0 <= self.score <= 1:
            raise ValueError("score must be in [0, 1]")
        return self


class FakeResponse:
    def __init__(self, status: int = 200, body: Any = None, headers: dict | None = None):
        self.status_code, self._body, self.headers = status, body, headers or {}

    def json(self):
        return self._body


def ok(content: str, cost: float | None = None) -> FakeResponse:
    usage = {"prompt_tokens": 100, "completion_tokens": 20}
    if cost is not None:
        usage["cost"] = cost
    return FakeResponse(
        200,
        {"choices": [{"message": {"content": content}, "finish_reason": "stop"}], "usage": usage},
    )


class FakeHttp:
    def __init__(self, responses: list[FakeResponse]):
        self.responses, self.payloads = list(responses), []

    def __call__(self, url, payload):
        self.payloads.append(payload)
        return self.responses.pop(0)


def client(responses, **kw) -> tuple[LlmClient, FakeHttp, list[float]]:
    http, slept = FakeHttp(responses), []
    llm = LlmClient(provider="openrouter", http=http, sleep=slept.append, **kw)
    llm._pacer.interval = 0.0  # pacing is tested separately
    return llm, http, slept


# --------------------------------------------------------------------------------- request
def test_the_request_constrains_the_output_to_the_contract_in_strict_mode():
    llm, http, _ = client([ok('{"score": 0.4, "note": null}')])
    llm.judge(Verdict, system="sys", prompt="p", tier=Tier.FLAGSHIP)
    payload = http.payloads[0]
    assert payload["model"] == OPENROUTER_DEFAULT_MODEL
    assert payload["messages"][0] == {"role": "system", "content": "sys"}
    fmt = payload["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["strict"] is True
    schema = fmt["json_schema"]["schema"]
    # Strict mode: every property required (nullable ones as an explicit null), no extras.
    assert set(schema["required"]) == {"score", "note"}
    assert schema["additionalProperties"] is False
    assert payload["provider"] == {"require_parameters": True}
    assert {"id": "response-healing"} in payload["plugins"]


# ----------------------------------------------------------------------------------- reply
def test_a_valid_reply_is_validated_and_costed():
    llm, _, _ = client([ok('```json\n{"score": 0.7, "note": "fine"}\n```')])
    result = llm.judge(Verdict, system="s", prompt="p")
    assert result.value.score == 0.7 and result.attempts == 1
    assert result.call.input_tokens == 100 and result.call.output_tokens == 20
    assert result.call.cost_usd == 0.0, "a :free model costs nothing even without a cost field"
    assert llm.budget.calls == 1


def test_a_contract_violation_is_fed_back_and_retried():
    llm, http, _ = client([ok('{"score": 3, "note": null}'), ok('{"score": 0.3, "note": null}')])
    result = llm.judge(Verdict, system="s", prompt="p")
    assert result.attempts == 2 and result.value.score == 0.3
    feedback = http.payloads[1]["messages"][-1]["content"]
    assert "did not satisfy the output contract" in feedback and "[0, 1]" in feedback


def test_a_reply_that_is_not_json_is_retried_then_refused():
    llm, _, _ = client([ok("I think 0.5."), ok("still prose"), ok("no")], max_retries=2)
    with pytest.raises(ValueError, match="not valid JSON"):
        llm.judge(Verdict, system="s", prompt="p")


def test_a_cut_off_reply_says_so():
    cut = FakeResponse(
        200,
        {"choices": [{"message": {"content": '{"score": 0.'}, "finish_reason": "length"}]},
    )
    llm, _, _ = client([cut], max_retries=0)
    with pytest.raises(ValueError, match="max_tokens"):
        llm.judge(Verdict, system="s", prompt="p")


# ----------------------------------------------------------------------------- rate limits
def test_a_rate_limit_is_waited_out():
    limited = FakeResponse(429, {"error": {"message": "rate limited"}}, {"Retry-After": "7"})
    llm, _, slept = client([limited, ok('{"score": 0.5, "note": null}')])
    assert llm.judge(Verdict, system="s", prompt="p").value.score == 0.5
    assert slept == [7.0]


def test_an_exhausted_daily_quota_stops_the_run_with_the_fix():
    daily = FakeResponse(429, {"error": {"message": "Rate limit exceeded: free-models-per-day"}})
    llm, _, _ = client([daily])
    with pytest.raises(QuotaExhausted, match=r"\$10 of credit"):
        llm.judge(Verdict, system="s", prompt="p")


def test_another_error_fails_loudly():
    llm, _, _ = client([FakeResponse(400, {"error": {"message": "bad schema"}})])
    with pytest.raises(RuntimeError, match="400.*bad schema"):
        llm.judge(Verdict, system="s", prompt="p")


def test_calls_are_paced_under_the_free_limit():
    llm, _, slept = client([ok('{"score": 0.1, "note": null}'), ok('{"score": 0.2, "note": null}')])
    llm._pacer.interval = 60.0 / 18
    llm.judge(Verdict, system="s", prompt="p")
    llm.judge(Verdict, system="s", prompt="p")
    assert slept and slept[-1] == pytest.approx(60.0 / 18, abs=0.5)


# --------------------------------------------------------------------------------- routing
def test_the_provider_follows_the_environment_unless_a_client_is_injected(monkeypatch):
    monkeypatch.setenv("SAA_LLM_PROVIDER", "openrouter")
    assert resolve_provider() == "openrouter"
    # A test injecting a fake Anthropic client can never be rerouted by a dry-run .env.
    assert LlmClient(FakeAnthropic([])).provider == "anthropic"
    with pytest.raises(ValueError, match="unknown LLM provider"):
        resolve_provider("bedrock")


def test_openrouter_models_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("SAA_OPENROUTER_MODEL", "dots-studio/dots-3-note-preview:free")
    monkeypatch.setenv("SAA_OPENROUTER_MODEL_FLAGSHIP", "nvidia/other:free")
    models = openrouter_models()
    assert models[Tier.FLAGSHIP] == "nvidia/other:free"
    assert models[Tier.LOW_COST] == "dots-studio/dots-3-note-preview:free"


def test_a_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    llm = LlmClient(provider="openrouter")
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        llm.judge(Verdict, system="s", prompt=json.dumps({}))
