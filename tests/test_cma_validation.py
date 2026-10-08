import pytest

from saa.contracts.asset_class import (
    CMA_CONTRACT,
    METHODS_CONTRACT,
    CmaBody,
    CmaJudgment,
    CmaMethodEstimate,
    CmaMethodId,
    CmaMethodsBody,
    Dispersion,
    SelectionMode,
)
from saa.contracts.base import Confidence
from saa.run import RunContext
from saa.skills.cma_methods.validation import (
    Status,
    load_validation_settings,
    validate_asset,
    validate_cross_section,
    validate_run,
)

M = CmaMethodId


@pytest.fixture(scope="module")
def settings(config):
    return load_validation_settings(config)


def methods_body(asset_id="ig_corporates", blend=5.5, yield_pct=5.0, vol=7.0, rf=4.0):
    methods = [
        CmaMethodEstimate(
            method=M.HISTORICAL_ERP,
            expected_return_pct=6.0,
            confidence=0.3,
            components={"risk_free_pct": rf},
            rationale="-",
        )
    ]
    if yield_pct is not None:
        methods.append(
            CmaMethodEstimate(
                method=M.YIELD_BUILDING_BLOCK,
                expected_return_pct=yield_pct,
                confidence=0.8,
                rationale="-",
            )
        )
    methods.append(
        CmaMethodEstimate(
            method=M.AUTO_BLEND, expected_return_pct=blend, confidence=0.5, rationale="-"
        )
    )
    return CmaMethodsBody(asset_id=asset_id, horizon_years=3, volatility_pct=vol, methods=methods)


def judged(asset_id, value, body):
    low, high = body.method_range
    judgment = CmaJudgment(
        selection=SelectionMode.AUTO_BLEND,
        method_weights={M.AUTO_BLEND: 1.0},
        expected_return_pct=value,
        confidence=Confidence.MEDIUM,
        dispersion=Dispersion.classify(high - low),
        regime_logic="-",
        valuation_context="-",
        signal_alignment="-",
        rationale="-",
    )
    return CmaBody(
        asset_id=asset_id,
        horizon_years=3,
        expected_return_pct=value,
        volatility_pct=body.volatility_pct,
        method_range=(low, high),
        judgment=judgment,
    )


def test_a_sensible_bond_cma_passes(settings):
    v = validate_asset("ig_corporates", "fixed_income", methods_body(), None, settings)
    assert v.status is Status.PASS
    assert v.source == "auto_blend"
    assert {c.name for c in v.checks} == {"plausible range", "yield anchor", "implied Sharpe"}


def test_a_unit_slip_fails(settings):
    """0.055 written where 5.5 belongs is outside every plausible range."""
    body = methods_body(blend=0.055, yield_pct=0.05)
    v = validate_asset("ig_corporates", "fixed_income", body, None, settings)
    # 0.055 sits inside [0, 12] for fixed income, and the yield slipped with it, so neither the
    # range nor the yield anchor catches it; the implied Sharpe ratio, far below zero, does.
    assert v.status is Status.WARN
    assert [c.name for c in v.checks if c.status is Status.WARN] == ["implied Sharpe"]
    v = validate_asset("ig_corporates", "fixed_income", methods_body(blend=55.0), None, settings)
    assert v.status is Status.FAIL


def test_a_bond_cma_far_from_its_yield_warns(settings):
    body = methods_body(blend=8.0, yield_pct=5.0)
    v = validate_asset("ig_corporates", "fixed_income", body, None, settings)
    assert v.status is Status.WARN
    assert any(c.name == "yield anchor" and "+3.00pp" in c.detail for c in v.checks)


def test_the_judged_cma_is_checked_when_it_exists(settings):
    body = methods_body(asset_id="us_growth", blend=10.0, yield_pct=None, vol=17.0)
    cma = judged("us_growth", 6.0, body)
    v = validate_asset("us_growth", "equity", body, cma, settings)
    assert v.source == "judge" and v.estimate_pct == 6.0
    paper = next(c for c in v.checks if c.name == "paper Exhibit 8")
    assert paper.status is Status.PASS  # 6.0 vs the paper's 6.2


def test_cross_section_flags_a_risky_asset_below_cash(settings):
    assets = {
        "cash": validate_asset("cash", "cash", methods_body("cash", 4.0, 4.0, 0.6), None, settings),
        "a": validate_asset("a", "equity", methods_body("a", 3.0, None, 15.0), None, settings),
        "b": validate_asset("b", "equity", methods_body("b", 9.0, None, 20.0), None, settings),
    }
    checks = {c.name: c for c in validate_cross_section(assets, settings)}
    assert checks["risky assets beat cash"].status is Status.WARN
    assert "a" in checks["risky assets beat cash"].detail


def test_validate_run_reads_every_asset_from_the_run(tmp_config, tmp_path, settings):
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    for i, asset in enumerate(tmp_config.universe.assets):
        vol = 0.6 if asset.id == "cash" else 2.0 + i
        body = methods_body(asset.id, blend=3.5 + 0.3 * i, yield_pct=None, vol=vol)
        run.write(METHODS_CONTRACT, "t", body, asset_id=asset.id)
    result = validate_run(run, tmp_config, settings)
    assert len(result.assets) == 18
    assert all(a.source == "auto_blend" for a in result.assets.values())

    gold = result.assets["gold"]
    body = methods_body("gold", blend=gold.estimate_pct, yield_pct=None, vol=gold.volatility_pct)
    run.write(CMA_CONTRACT, "t", judged("gold", gold.estimate_pct, body), asset_id="gold")
    assert validate_run(run, tmp_config, settings).assets["gold"].source == "judge"


def test_validate_run_needs_the_candidates(tmp_config, tmp_path, settings):
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    with pytest.raises(FileNotFoundError, match="cma-methods"):
        validate_run(run, tmp_config, settings)
