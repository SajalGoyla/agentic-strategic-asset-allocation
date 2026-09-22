"""The macro agent end to end, and the LLM plumbing underneath it.

No network: a stub stands in for the Anthropic client, so these run in CI and cost nothing.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from saa.agents.macro import agent as macro_agent
from saa.contracts import MacroJudgment, read
from saa.contracts.macro import DIMENSIONS
from saa.llm import Budget, BudgetExceeded, LlmClient, estimate_cost_usd
from tests.conftest import macro_series, write_macro_lake


# ---------------------------------------------------------------------------------- stubs
@dataclass
class FakeUsage:
    input_tokens: int = 4_000
    output_tokens: int = 900
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class FakeResponse:
    parsed_output: Any
    usage: FakeUsage
    stop_reason: str = "end_turn"
    stop_details: Any = None


class FakeMessages:
    def __init__(self, outputs: list[Any]):
        self.outputs = list(outputs)
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        value = self.outputs.pop(0) if self.outputs else self.outputs
        if isinstance(value, Exception):
            raise value
        return FakeResponse(parsed_output=value, usage=FakeUsage())


class FakeAnthropic:
    def __init__(self, outputs: list[Any]):
        self.messages = FakeMessages(outputs)


def judgment_payload(**overrides) -> dict:
    payload = {
        "regime": "late_cycle",
        "regime_qualifier": "with stagflationary risk",
        "confidence": "medium_high",
        "confidence_score": 0.62,
        "recession_probability": {"low_pct": 25.0, "high_pct": 35.0},
        "dimension_rationales": [
            {"dimension": d, "rationale": f"{d} rationale"} for d in DIMENSIONS
        ],
        "key_risks": ["oil supply shock", "payrolls rolling over"],
        "narrative": "Growth is positive but decelerating while inflation re-accelerates.",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def store(tmp_config):
    return write_macro_lake(tmp_config, macro_series())


# ------------------------------------------------------------------------------ llm client
def test_judge_returns_a_validated_contract_model():
    client = LlmClient(FakeAnthropic([judgment_payload()]))
    result = client.judge(MacroJudgment, system="s", prompt="p")
    assert isinstance(result.value, MacroJudgment)
    assert result.value.regime.value == "late_cycle"
    assert result.attempts == 1


def test_the_judgment_schema_is_what_constrains_the_model():
    """Agents are constrained by the judgment contract, never asked for free-form JSON."""
    client = LlmClient(FakeAnthropic([judgment_payload()]))
    client.judge(MacroJudgment, system="s", prompt="p")
    assert client._client.messages.calls[0]["output_format"] is MacroJudgment


def test_system_prompt_is_cached():
    """18 asset agents and 21 PC agents resend the same instructions; caching is the lever."""
    client = LlmClient(FakeAnthropic([judgment_payload()]))
    client.judge(MacroJudgment, system="s", prompt="p")
    system = client._client.messages.calls[0]["system"]
    assert system[0]["cache_control"] == {"type": "ephemeral"}


def test_contract_violations_are_retried_with_the_error_fed_back():
    """A rationale is missing for three dimensions, which only our validator catches."""
    bad = judgment_payload(dimension_rationales=[{"dimension": "growth", "rationale": "x"}])
    client = LlmClient(FakeAnthropic([bad, judgment_payload()]))
    result = client.judge(MacroJudgment, system="s", prompt="p")

    assert result.attempts == 2
    followup = client._client.messages.calls[1]["messages"]
    assert followup[-1]["role"] == "user"
    assert "did not satisfy the output contract" in followup[-1]["content"]
    assert "no rationale given" in followup[-1]["content"]


def test_retries_are_bounded_then_the_agent_fails():
    bad = judgment_payload(dimension_rationales=[{"dimension": "growth", "rationale": "x"}])
    client = LlmClient(FakeAnthropic([bad, bad, bad]), max_retries=2)
    with pytest.raises(ValueError, match="did not satisfy its contract after 3 attempts"):
        client.judge(MacroJudgment, system="s", prompt="p")


def test_every_call_is_recorded_for_the_budget():
    budget = Budget()
    client = LlmClient(FakeAnthropic([judgment_payload()]), budget=budget)
    result = client.judge(MacroJudgment, system="s", prompt="p")
    assert budget.calls == 1
    assert budget.spent_usd == pytest.approx(result.call.cost_usd)
    assert result.call.model == "claude-opus-5"
    assert result.call.input_tokens == 4_000


def test_a_failed_attempt_still_costs_money():
    bad = judgment_payload(dimension_rationales=[{"dimension": "growth", "rationale": "x"}])
    budget = Budget()
    client = LlmClient(FakeAnthropic([bad, judgment_payload()]), budget=budget)
    client.judge(MacroJudgment, system="s", prompt="p")
    assert budget.calls == 2


def test_a_run_stops_at_its_spend_cap():
    budget = Budget(cap_usd=0.001)
    client = LlmClient(FakeAnthropic([judgment_payload(), judgment_payload()]), budget=budget)
    client.judge(MacroJudgment, system="s", prompt="p")
    with pytest.raises(BudgetExceeded, match="cap"):
        client.judge(MacroJudgment, system="s", prompt="p")


def test_cost_uses_the_published_rates():
    usage = FakeUsage(input_tokens=1_000_000, output_tokens=0)
    assert estimate_cost_usd("claude-opus-5", usage) == pytest.approx(5.00)
    assert estimate_cost_usd("claude-sonnet-5", usage) == pytest.approx(2.00)
    assert estimate_cost_usd("unknown-model", usage) is None


def test_cached_input_is_cheaper_than_fresh_input():
    fresh = FakeUsage(input_tokens=1_000_000, output_tokens=0)
    cached = FakeUsage(input_tokens=0, cache_read_input_tokens=1_000_000, output_tokens=0)
    assert estimate_cost_usd("claude-opus-5", cached) < estimate_cost_usd("claude-opus-5", fresh)


def test_a_refusal_is_surfaced_not_swallowed():
    class Refusing(FakeMessages):
        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return FakeResponse(parsed_output=None, usage=FakeUsage(), stop_reason="refusal")

    client = LlmClient(FakeAnthropic([]))
    client._client.messages = Refusing([])
    with pytest.raises(RuntimeError, match="declined the request"):
        client.judge(MacroJudgment, system="s", prompt="p")


# ----------------------------------------------------------------------------------- agent
def run_agent(tmp_config, store, tmp_path, outputs=None, **kwargs):
    client = LlmClient(FakeAnthropic(outputs or [judgment_payload()]))
    return macro_agent.run(
        config=tmp_config,
        store=store,
        llm=client,
        out_dir=tmp_path / "macro",
        pipeline_run_id="20260922T120000Z",
        **kwargs,
    )


def test_agent_writes_both_contract_files_and_a_report(tmp_config, store, tmp_path):
    result = run_agent(tmp_config, store, tmp_path)

    assert set(result.paths) == {"view", "history", "report"}
    assert result.paths["view"].name == "macro-view.json"
    assert result.paths["history"].name == "regime_history.json"
    assert result.paths["report"].name == "macro.md"

    # Re-read through the registry so the files are validated against the contract on disk.
    view = read("macro_view", result.paths["view"])
    assert view.body.judgment.regime.value == "late_cycle"
    assert len(view.body.scores.dimensions) == 4
    assert view.header.pipeline_run_id == "20260922T120000Z"


def test_the_script_computes_the_scores_and_the_model_only_judges(tmp_config, store, tmp_path):
    """§3.2: the LLM handles judgment; the scripts handle computation."""
    result = run_agent(tmp_config, store, tmp_path)
    scores = result.view.body.scores

    # Dimension scores come from the panel, not from anything the model returned.
    for dimension in scores.dimensions:
        assert dimension.score == pytest.approx(
            float(result.panel.scores.loc[result.panel.as_of, dimension.dimension])
        )
    assert set(MacroJudgment.model_fields) & {"dimensions", "scores"} == set()


def test_header_records_provenance_ips_and_cost(tmp_config, store, tmp_path):
    result = run_agent(tmp_config, store, tmp_path)
    header = result.view.header

    assert header.provenance  # which lake versions were read
    assert header.ips_version == tmp_config.ips.version
    assert header.ips_status == tmp_config.ips.status
    assert header.produced_by.value == "hybrid"
    assert len(header.model_calls) == 1
    assert header.cost_usd > 0


def test_the_data_end_lags_the_as_of_date(tmp_config, store, tmp_path):
    """The ragged edge is information, and the contract has to carry it."""
    result = run_agent(tmp_config, store, tmp_path, as_of="2026-09-22")
    scores = result.view.body.scores
    assert scores.data_end is not None
    assert scores.data_end < date(2026, 9, 22)
    assert result.view.header.as_of == date(2026, 9, 22)


def test_pit_quality_reports_how_much_was_really_point_in_time(tmp_config, store, tmp_path):
    result = run_agent(tmp_config, store, tmp_path)
    quality = result.view.body.scores.pit_quality
    assert {q.dimension for q in quality} == set(DIMENSIONS)
    # The synthetic lake carries no ALFRED vintages, so nothing is genuinely point-in-time.
    assert all(q.indicators_point_in_time == 0 for q in quality)
    assert result.view.body.scores.point_in_time is False


def test_regime_history_is_usable_as_conditioning_labels(tmp_config, store, tmp_path):
    """`historical_analysis.conditional_stats` needs a month -> label mapping."""
    result = run_agent(tmp_config, store, tmp_path)
    history = read("regime_history", result.paths["history"])

    labels = history.body.labels()
    assert len(labels) == len(history.body.months)
    assert all(isinstance(k, date) for k in labels)
    assert set(labels.values()) <= {"expansion", "late_cycle", "recession", "recovery"}
    # It must agree with the current call: same scorer, same run.
    assert labels[max(labels)] == result.panel.regimes.iloc[-1]


def test_report_states_the_regime_and_the_draft_ips(tmp_config, store, tmp_path):
    result = run_agent(tmp_config, store, tmp_path)
    report = result.report

    assert "# Macro View" in report
    assert "late_cycle with stagflationary risk" in report
    assert "25–35%" in report
    for dimension in DIMENSIONS:
        assert dimension in report
    if tmp_config.ips.status == "draft":
        assert "has not been ratified" in report


def test_a_model_that_cannot_satisfy_the_contract_fails_the_run(tmp_config, store, tmp_path):
    bad = judgment_payload(recession_probability={"low_pct": 60.0, "high_pct": 20.0})
    with pytest.raises((ValueError, ValidationError)):
        run_agent(tmp_config, store, tmp_path, outputs=[bad, bad, bad])


def test_the_prompt_carries_the_evidence_not_just_the_answer(tmp_config, store, tmp_path):
    result = run_agent(tmp_config, store, tmp_path)
    prompt = macro_agent.build_prompt(
        result.view.body.scores.dimensions,
        result.panel,
        as_of=date(2026, 9, 22),
        ips_status="draft",
    )
    assert "Rule-based prior" in prompt
    assert "prior, not an instruction" in prompt
    assert "PAYEMS" in prompt  # the indicator table, not only the composites
    for dimension in DIMENSIONS:
        assert dimension in prompt


def test_the_system_prompt_is_the_agent_description_plus_the_skill():
    """§3.2: an agent is its description, its skills, its scripts and its output contract."""
    system = macro_agent.system_prompt()
    assert "# Macro Regime Agent" in system
    assert "# Macro Regime Skill" in system
    assert "Do not restate the dimension scores as your own" in system
