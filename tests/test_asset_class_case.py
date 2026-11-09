"""The per-asset agent descriptions, the scenarios skill, and the 13-section investment case.

All three are Exhibit 3's content: "Each agent has its own description file with appropriate
asset class-specific instructions", "Scenario analysis (bull/bear from method range)", and the
"13-section investment case" (decision 57).
"""

import re

import pytest

from saa.agents.cma_judge.agent import (
    ASSETS_DIR,
    asset_description,
    build_prompt,
    load_evidence,
    system_prompt,
)
from saa.contracts import CmaBody, CmaMethodId, read
from saa.contracts.asset_class import CmaJudgment
from saa.skills.asset_class_report import (
    N_SECTIONS,
    key_considerations,
    render_case,
    run_reports,
    write_outputs,
)
from saa.skills.scenarios import build_scenarios, render_report, run_scenarios
from tests.test_cma_judge import (  # noqa: F401
    ASSET,
    judgment_payload,
    methods_body,
    run,
    seed_asset,
)

REQUIRED_HEADINGS = (
    "## Required skills",
    "## Workflow (Exhibit 3)",
    "## Key considerations",
    "## Output contract",
)


def cma_body(asset_id=ASSET, expected=6.8, low=4.0, high=12.5) -> CmaBody:
    return CmaBody(
        asset_id=asset_id,
        horizon_years=3,
        expected_return_pct=expected,
        volatility_pct=15.2,
        method_range=(low, high),
        judgment=CmaJudgment.model_validate(judgment_payload(expected)),
    )


def seed_judged(run, asset_id=ASSET, **kw):  # noqa: F811
    seed_asset(run, asset_id)
    run.write("cma", "x", cma_body(asset_id, **kw), asset_id=asset_id)


# ------------------------------------------------------------------- the 18 description files
def test_every_asset_in_the_universe_has_a_description_file(config):
    """§3.3: "Each agent has its own description file". One per asset, no orphans either way."""
    ids = {a.id for a in config.universe.assets}
    files = {p.stem for p in ASSETS_DIR.glob("*.md")}
    assert files == ids, f"missing {sorted(ids - files)}, orphaned {sorted(files - ids)}"
    assert len(files) == 18


@pytest.mark.parametrize("asset_id", sorted(p.stem for p in ASSETS_DIR.glob("*.md")))
def test_each_description_has_exhibit_3s_components(asset_id):
    text = asset_description(asset_id)
    for heading in REQUIRED_HEADINGS:
        assert heading in text, f"{asset_id} is missing {heading}"
    for label in ("Macro sensitivity", "Primary valuation lens", "Slug"):
        assert f"**{label}:**" in text, f"{asset_id} is missing {label}"
    assert len(key_considerations(text)) >= 4, f"{asset_id} has too few key considerations"


def test_the_considerations_are_asset_specific_not_boilerplate():
    """The point of 18 files is that they differ. Nothing shared beyond the template."""
    per_asset = {
        p.stem: set(key_considerations(asset_description(p.stem))) for p in ASSETS_DIR.glob("*.md")
    }
    everywhere = set.intersection(*per_asset.values())
    assert not everywhere, f"identical considerations across all assets: {everywhere}"
    seen: dict[str, str] = {}
    for asset_id, items in per_asset.items():
        for item in items:
            assert item not in seen, f"{asset_id} repeats {seen[item]}'s consideration"
            seen[item] = asset_id


def test_a_missing_description_is_an_error_not_a_silent_fallback():
    """A judge that never saw its asset's instructions is not Exhibit 3's agent, and the
    difference would be invisible in the output. So it raises."""
    with pytest.raises(FileNotFoundError, match="no asset description"):
        asset_description("not_an_asset")


def test_the_description_reaches_the_prompt_but_not_the_cached_prefix(run):  # noqa: F811
    """The per-asset file goes in the asset's own message so the system prompt stays one cached
    prefix for all 18 (decision 57)."""
    seed_asset(run)
    prompt = build_prompt(
        load_evidence(run, ASSET), None, as_of=run.as_of, ips_status="owner_approved"
    )
    assert "## Key considerations" in prompt
    assert "S&P 500 is the benchmark" in prompt
    # The shared prefix may *point at* the per-asset files -- it does -- but must carry no
    # asset's own instructions, or the prefix would differ per asset and stop being cacheable.
    shared = system_prompt()
    assert "## Key considerations" not in shared
    assert "S&P 500 is the benchmark" not in shared


def test_the_shared_prefix_carries_no_assets_considerations():
    shared = system_prompt()
    for path in ASSETS_DIR.glob("*.md"):
        for item in key_considerations(asset_description(path.stem)):
            assert item not in shared, f"{path.stem}'s guidance leaked into the cached prefix"


# ------------------------------------------------------------------------------- scenarios
def test_scenarios_bound_the_judge_with_the_extreme_candidates():
    """Exhibit 3 step 8: "bull/bear from method range"."""
    result = build_scenarios(methods_body(), cma_body())
    by_name = {s.name: s.expected_return_pct for s in result.body.scenarios}
    assert by_name["bear"] == 4.0  # implied_erp_cape, the lowest candidate
    assert by_name["base"] == 6.8  # the judge
    assert by_name["bull"] == 12.5  # historical_erp, the highest
    assert result.bear_method == "implied_erp_cape"
    assert result.bull_method == "historical_erp"
    assert result.spread_pct == pytest.approx(8.5)


def test_the_base_case_sits_inside_the_range_because_exhibit_4_requires_it():
    result = build_scenarios(methods_body(), cma_body())
    by_name = {s.name: s.expected_return_pct for s in result.body.scenarios}
    assert by_name["bear"] <= by_name["base"] <= by_name["bull"]


def test_unavailable_methods_do_not_set_the_bounds():
    """A method with no estimate cannot be the bear case; the count records the shrunk set."""
    methods = methods_body(unavailable=(CmaMethodId.SURVEY_CONSENSUS,))
    result = build_scenarios(methods, cma_body())
    assert result.n_available == 6
    assert all(s.expected_return_pct >= 4.0 for s in result.body.scenarios)


def test_probability_is_left_unset_rather_than_invented():
    """The paper assigns none and the candidates carry no probability to inherit."""
    result = build_scenarios(methods_body(), cma_body())
    assert all(s.probability is None for s in result.body.scenarios)


def test_every_narrative_names_the_method_it_came_from():
    result = build_scenarios(methods_body(), cma_body())
    by_name = {s.name: s.narrative for s in result.body.scenarios}
    assert "implied_erp_cape" in by_name["bear"]
    assert "historical_erp" in by_name["bull"]


def test_mismatched_assets_are_rejected():
    with pytest.raises(ValueError, match="asset mismatch"):
        build_scenarios(methods_body("gold"), cma_body("us_large_cap"))


def test_scenarios_write_a_valid_contract_and_a_report(run):  # noqa: F811
    from saa.skills.scenarios import write_outputs as write_scenarios

    seed_judged(run)
    result = run_scenarios(run, [ASSET])
    write_scenarios(result, run)
    body = read("scenarios", run.path("scenarios", asset_id=ASSET)).body
    assert {s.name for s in body.scenarios} == {"bear", "base", "bull"}
    assert "Spread" in render_report(result)


def test_scenarios_without_a_judged_cma_say_what_to_run(run):  # noqa: F811
    seed_asset(run)
    with pytest.raises(FileNotFoundError, match="cma-judge"):
        run_scenarios(run, [ASSET])


# ------------------------------------------------------------------- the 13-section case
def test_the_case_has_exactly_thirteen_sections(run, config):  # noqa: F811
    seed_judged(run)
    result = run_reports(run, config, [ASSET])
    case = result.cases[ASSET]
    assert case.sections == N_SECTIONS == 13
    numbered = re.findall(r"^## (\d+)\. ", case.text, re.M)
    assert [int(n) for n in numbered] == list(range(1, 14))


def test_the_case_quotes_the_judge_rather_than_writing_its_own_prose(run, config):  # noqa: F811
    """Decision 8: skills never call an LLM, so every judgement here is the judge's."""
    seed_judged(run)
    text = run_reports(run, config, [ASSET]).cases[ASSET].text
    for quoted in ("late-cycle tilts to valuation", "CAPE 25", "signals confirm"):
        assert quoted in text


def test_the_case_carries_this_assets_key_considerations(run, config):  # noqa: F811
    seed_judged(run)
    text = run_reports(run, config, [ASSET]).cases[ASSET].text
    assert "S&P 500 is the benchmark" in text
    assert "Buyback yield" in text


def test_the_case_states_the_section_list_is_our_reconstruction(run, config):  # noqa: F811
    """The paper names the report twice and never lists its sections; the report says so."""
    seed_judged(run)
    text = run_reports(run, config, [ASSET]).cases[ASSET].text
    assert "reconstruction" in text
    assert "without listing its sections" in text


def test_the_case_reports_the_ips_standing_from_the_policy(run, config):  # noqa: F811
    seed_judged(run)
    text = run_reports(run, config, [ASSET]).cases[ASSET].text
    assert config.ips.standing in text


def test_a_missing_scenarios_file_is_named_not_hidden(run, config):  # noqa: F811
    """Section 11 degrades to the candidate range and says which command fills it."""
    seed_judged(run)
    text = run_reports(run, config, [ASSET]).cases[ASSET].text
    assert "saa-skill scenarios" in text
    assert "4.00%–12.50%" in text


def test_the_case_notes_the_sentiment_gap(run, config):  # noqa: F811
    """Exhibit 3 step 5 has no section, so section 13 says why (decision 26)."""
    seed_judged(run)
    text = run_reports(run, config, [ASSET]).cases[ASSET].text
    assert "No sentiment, flows or positioning" in text


def test_the_case_overwrites_the_historical_analysis_stub(run, config):  # noqa: F811
    """Both write analysis.md; this skill runs last and supersedes it."""
    seed_judged(run)
    path = run.root / "cma" / ASSET / "analysis.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# stub\n\n## Return history sources\n", encoding="utf-8")
    write_outputs(run_reports(run, config, [ASSET]), run)
    text = path.read_text(encoding="utf-8")
    assert "# stub" not in text
    assert "## 13." in text


def test_a_case_without_stage_2_says_what_to_run(run, config):  # noqa: F811
    with pytest.raises(FileNotFoundError, match="run stage 2 first"):
        run_reports(run, config, [ASSET])


def test_key_considerations_parses_the_numbered_block():
    text = (
        "# x\n\n## Key considerations\n\nlead-in\n\n1. **First.** one\n   wrapped\n\n"
        "2. **Second.** two\n\n## Output contract\n\nnot a consideration\n"
    )
    items = key_considerations(text)
    assert len(items) == 2
    assert items[0] == "**First.** one wrapped"
    assert "not a consideration" not in " ".join(items)


def test_render_case_is_pure(run, config):  # noqa: F811
    """Same inputs, same bytes: the report writes nothing of its own invention."""
    from saa.skills.asset_class_report import load_case_inputs

    seed_judged(run)
    data = load_case_inputs(run, ASSET)
    assert render_case(ASSET, data, config) == render_case(ASSET, data, config)
