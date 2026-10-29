"""The OpenRouter backend of ``LlmClient``: the request it sends, how it reads the reply, and
how it copes with rate limits. No network: ``FakeHttp`` stands in for ``requests.post``."""

import json
from typing import Any

import pytest
from pydantic import model_validator

from saa.contracts.asset_class import CmaJudgment
from saa.contracts.base import Contract, Tier
from saa.llm import (
    AGENT_TIERS,
    GEMINI_DEFAULT_MODEL,
    OPENROUTER_DEFAULT_MODEL,
    LlmClient,
    QuotaExhausted,
    openrouter_models,
    resolve_provider,
    tier_for,
)
from tests.test_macro_agent import FakeAnthropic


@pytest.fixture(autouse=True)
def _no_dry_run_env(monkeypatch):
    # A developer's .env (loaded by other test modules) must not change what these assert.
    for name in (
        "SAA_LLM_PROVIDER",
        "SAA_OPENROUTER_MODEL",
        "SAA_OPENROUTER_MODEL_FLAGSHIP",
        "SAA_OPENROUTER_MODEL_LOW_COST",
        "SAA_OPENROUTER_RPM",
        "SAA_GEMINI_MODEL",
        "SAA_GEMINI_MODEL_FLAGSHIP",
        "SAA_GEMINI_MODEL_LOW_COST",
        "SAA_GEMINI_RPM",
        "SAA_ANTHROPIC_MODEL_FLAGSHIP",
        "SAA_ANTHROPIC_MODEL_LOW_COST",
    ):
        monkeypatch.delenv(name, raising=False)


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
        self.url = url
        self.payloads.append(payload)
        return self.responses.pop(0)


def client(responses, provider="openrouter", **kw) -> tuple[LlmClient, FakeHttp, list[float]]:
    http, slept = FakeHttp(responses), []
    llm = LlmClient(provider=provider, http=http, sleep=slept.append, **kw)
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


class Keyed(Contract):
    weights: dict[Tier, float]


def test_keywords_a_provider_rejects_are_dropped_from_the_schema():
    # A dict keyed by an enum -> "propertyNames", which NVIDIA's grammar engine rejects.
    assert "propertyNames" in json.dumps(Keyed.model_json_schema())
    llm, http, _ = client([ok("{}")], max_retries=0)
    with pytest.raises(ValueError):
        llm.judge(Keyed, system="s", prompt="p")
    sent = json.dumps(http.payloads[0]["response_format"]["json_schema"]["schema"])
    assert "propertyNames" not in sent and "weights" in sent


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


def test_an_agent_check_is_fed_back_and_retried():
    def check(verdict: Verdict) -> None:
        if not verdict.note or len(verdict.note) < 10:
            raise ValueError("note is too thin to review")

    llm, http, _ = client(
        [ok('{"score": 0.5, "note": "..."}'), ok('{"score": 0.5, "note": "a real, long note"}')]
    )
    result = llm.judge(Verdict, system="s", prompt="p", check=check)
    assert result.attempts == 2 and result.value.note == "a real, long note"
    assert "too thin to review" in http.payloads[1]["messages"][-1]["content"]


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


def test_an_upstream_timeout_inside_a_200_is_retried():
    timeout = FakeResponse(
        200, {"error": {"message": "Upstream idle timeout exceeded", "code": 504}}
    )
    llm, _, slept = client([timeout, ok('{"score": 0.6, "note": null}')])
    assert llm.judge(Verdict, system="s", prompt="p").value.score == 0.6
    assert slept == [2.0]


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


# ---------------------------------------------------------------------------------- gemini
def test_gemini_gets_the_schema_without_openrouter_only_fields():
    llm, http, _ = client([ok('{"score": 0.4, "note": null}')], provider="gemini")
    result = llm.judge(Verdict, system="s", prompt="p", effort="medium")
    payload = http.payloads[0]
    assert "generativelanguage.googleapis.com" in http.url
    assert payload["model"] == GEMINI_DEFAULT_MODEL
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["reasoning_effort"] == "medium"
    assert not {"provider", "plugins", "reasoning", "usage"} & set(payload)
    assert result.call.cost_usd is None, "a Gemini key may be paid; the cost is not assumed"


def test_gemini_tiers_come_from_their_own_variables(monkeypatch):
    monkeypatch.setenv("SAA_GEMINI_MODEL_FLAGSHIP", "gemini-3.5-flash-lite")
    monkeypatch.setenv("SAA_GEMINI_MODEL_LOW_COST", "gemini-3.1-flash-lite")
    llm = LlmClient(provider="gemini", http=FakeHttp([]))
    assert llm.models == {
        Tier.FLAGSHIP: "gemini-3.5-flash-lite",
        Tier.LOW_COST: "gemini-3.1-flash-lite",
    }
    assert llm._pacer.interval == pytest.approx(60.0 / 14)


def test_googles_daily_quota_stops_the_run():
    # Google wraps the error in a list and names the quota rather than saying "per-day".
    body = [
        {
            "error": {
                "code": 429,
                "message": "Quota exceeded for quota metric 'Generate Content requests' "
                "(GenerateRequestsPerDayPerProjectPerModel-FreeTier)",
            }
        }
    ]
    llm, _, _ = client([FakeResponse(429, body)], provider="gemini")
    with pytest.raises(QuotaExhausted, match="per model"):
        llm.judge(Verdict, system="s", prompt="p")


def test_a_missing_gemini_key_is_reported(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        LlmClient(provider="gemini").judge(Verdict, system="s", prompt="p")


# ------------------------------------------------------------------------------- anthropic
def test_anthropic_tiers_default_to_opus_and_sonnet_and_can_be_overridden(monkeypatch):
    llm = LlmClient(FakeAnthropic([]))
    assert llm.models == {Tier.FLAGSHIP: "claude-opus-5-5", Tier.LOW_COST: "claude-sonnet-5-5"}
    monkeypatch.setenv("SAA_ANTHROPIC_MODEL_LOW_COST", "claude-haiku-5-5")
    assert LlmClient(FakeAnthropic([])).models[Tier.LOW_COST] == "claude-haiku-5-5"


def test_every_agent_has_a_tier_and_a_typo_fails_loudly():
    agents = {"macro", "cma_judge", "pc", "pc_researcher", "cro", "peer_review", "vote"}
    agents |= {"revision", "cio"}
    assert set(AGENT_TIERS) == agents
    assert tier_for("cio") is Tier.FLAGSHIP and tier_for("peer_review") is Tier.LOW_COST
    with pytest.raises(KeyError, match="no tier set"):
        tier_for("chief_risk_officer")


def _closed_empty_objects(node, path="$"):
    """Objects that allow no keys: what a dict with open keys becomes in a strict schema."""
    found = []
    if isinstance(node, dict):
        if (
            node.get("type") == "object"
            and not node.get("properties")
            and node.get("additionalProperties") is False
        ):
            found.append(path)
        for key, child in node.items():
            found += _closed_empty_objects(child, f"{path}.{key}")
    elif isinstance(node, list):
        for i, child in enumerate(node):
            found += _closed_empty_objects(child, f"{path}[{i}]")
    return found


def test_every_judgment_can_be_answered_under_anthropics_strict_schema():
    """Decision 52: a dict field reached Claude as an object allowing no keys, so every CMA
    judgment came back with empty method weights."""
    import anthropic

    from saa.agents.pc.agent import Rationale
    from saa.agents.pc_researcher.agent import ResearchChoice
    from saa.agents.revision.agent import RevisionJudgment
    from saa.contracts import (
        BallotJudgment,
        CioJudgment,
        CmaJudgment,
        CroJudgment,
        MacroJudgment,
        ReviewJudgment,
    )

    for model in (
        MacroJudgment,
        CmaJudgment,
        Rationale,
        ResearchChoice,
        CroJudgment,
        ReviewJudgment,
        BallotJudgment,
        RevisionJudgment,
        CioJudgment,
    ):
        assert not _closed_empty_objects(anthropic.transform_schema(model)), model.__name__


def test_an_anthropic_contract_miss_is_retried_and_charged():
    weights = [{"method": "historical_erp", "weight": 1.0}]
    judgment = {
        "selection": "single_method",
        "expected_return_pct": 7.0,
        "confidence": "medium",
        "dispersion": "tight",
        "regime_logic": "r",
        "valuation_context": "v",
        "signal_alignment": "s",
        "rationale": "x",
    }
    empty = {**judgment, "method_weights": []}
    good = {**judgment, "method_weights": weights}
    llm = LlmClient(FakeAnthropic([empty, good]))
    result = llm.judge(CmaJudgment, system="s", prompt="p")
    assert result.attempts == 2 and result.value.weights == {"historical_erp": 1.0}
    assert llm.budget.calls == 2, "the failed attempt is billed, so it is counted"
    # The header records the judgment once, with both attempts' tokens.
    assert result.call.attempts == 2 and result.call.input_tokens == 2 * 4_000
