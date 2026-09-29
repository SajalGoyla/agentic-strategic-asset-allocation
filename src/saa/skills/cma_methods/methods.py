"""The CMA method calculators: one function per candidate of Exhibit 4, plus the fixed-income
builder of §3.3. Pure functions of a ``MarketInputs`` bundle -- no data access, no I/O.

Convention: every estimate is the arithmetic expected annual return, nominal, in percent. The
portfolio optimisers consume arithmetic means, and the historical and Black-Litterman methods
produce them natively. Methods whose natural output is a compound (geometric) return -- a
yield, a Gordon growth sum, a survey of average annual returns -- add half the variance,
recorded as the ``variance_addback_pct`` component, so all candidates are comparable.

A method that does not apply or lacks data raises ``Unavailable``; the runner records the reason
instead of a number.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from saa.contracts.asset_class import CmaMethodEstimate, CmaMethodId
from saa.contracts.portfolio import CovarianceBody
from saa.skills.cma_methods.settings import CmaSettings

MONTHS_PER_YEAR = 12
MIN_HISTORY_MONTHS = 60
EQUITY_ANCHOR = "us_large_cap"  # the only asset with a long valuation history (Shiller)


class Unavailable(Exception):  # noqa: N818 -- reads as `raise Unavailable("why")`
    """A method cannot produce an estimate for this asset; the message says why."""


@dataclass
class MarketInputs:
    """Everything the calculators read, already restricted to what was known on ``as_of``."""

    as_of: pd.Timestamp
    returns: pd.DataFrame  # monthly decimal returns, date x asset_id, from history.start
    risk_free: pd.Series  # monthly decimal T-bill return, same index convention
    risk_free_pct: float | None  # current T-bill yield
    covariance: CovarianceBody
    horizon_years: int
    groups: dict[str, str]
    tickers: dict[str, str]
    macro: pd.DataFrame  # month-end values, date x series_id
    shiller: pd.DataFrame | None = None
    fund_snapshot: pd.DataFrame = field(default_factory=pd.DataFrame)
    surveys: dict[str, tuple[float, pd.Timestamp]] = field(default_factory=dict)
    regime_labels: pd.Series | None = None  # month-end -> regime, as the macro skill scores it
    _equilibrium: dict[str, float] | None = field(default=None, repr=False)

    def volatility_pct(self, asset_id: str) -> float:
        return self.covariance.volatilities_pct[asset_id]

    def variance_addback_pct(self, asset_id: str) -> float:
        """Half the variance, in percent: arithmetic mean ~ geometric mean + sigma^2 / 2."""
        return 0.5 * (self.volatility_pct(asset_id) / 100) ** 2 * 100

    def latest(self, series_id: str, max_age_days: int) -> float:
        """Most recent value of a macro series, if not older than ``max_age_days``."""
        if series_id not in self.macro:
            raise Unavailable(f"{series_id} is not in the lake")
        values = self.macro[series_id].dropna()
        if values.empty:
            raise Unavailable(f"{series_id} has no observation by {self.as_of.date()}")
        age = (self.as_of - values.index[-1]).days
        if age > max_age_days:
            raise Unavailable(
                f"{series_id} last observed {values.index[-1].date()}, {age} days old"
            )
        return float(values.iloc[-1])

    def survey(self, variable: str, max_age_days: int) -> float:
        if variable not in self.surveys:
            raise Unavailable(f"SPF {variable} is not available by {self.as_of.date()}")
        value, when = self.surveys[variable]
        if (self.as_of - when).days > max_age_days:
            raise Unavailable(f"SPF {variable} last asked {when.date()}, too old")
        return value

    def snapshot(self, asset_id: str, column: str) -> float:
        ticker = self.tickers[asset_id]
        if self.fund_snapshot.empty or ticker not in self.fund_snapshot.index:
            raise Unavailable(f"no fund snapshot for {ticker} by {self.as_of.date()}")
        value = self.fund_snapshot.loc[ticker, column]
        if value is None or pd.isna(value):
            raise Unavailable(f"{ticker} snapshot has no {column}")
        return float(value)

    def excess_returns(self, asset_id: str) -> pd.Series:
        r = self.returns[asset_id].dropna() if asset_id in self.returns else pd.Series()
        return (r - self.risk_free.reindex(r.index)).dropna()

    def require_risk_free(self) -> float:
        if self.risk_free_pct is None:
            raise Unavailable("no current T-bill yield")
        return self.risk_free_pct


Calculator = Callable[[str, MarketInputs, CmaSettings], CmaMethodEstimate]


def _estimate(
    method: CmaMethodId,
    value: float,
    confidence: float,
    components: dict[str, float],
    rationale: str,
) -> CmaMethodEstimate:
    return CmaMethodEstimate(
        method=method,
        expected_return_pct=round(value, 4),
        confidence=round(min(max(confidence, 0.0), 1.0), 4),
        components={k: round(float(v), 4) for k, v in components.items()},
        rationale=rationale,
    )


# ------------------------------------------------------------------ 1. historical ERP
def historical_erp(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """Exhibit 4 method 1: mean realised excess return over T-bills since 1990, plus today's
    T-bill yield. Confidence grows with the months of history, up to 30 years."""
    rf = x.require_risk_free()
    excess = x.excess_returns(asset_id)
    if len(excess) < MIN_HISTORY_MONTHS:
        raise Unavailable(f"only {len(excess)} months of history; need {MIN_HISTORY_MONTHS}")
    premium = float(excess.mean() * MONTHS_PER_YEAR * 100)
    months = len(excess)
    group = x.groups[asset_id]
    confidence = s.base_confidence(CmaMethodId.HISTORICAL_ERP, asset_id, group) * min(
        1.0, months / s.history.full_confidence_months
    )
    return _estimate(
        CmaMethodId.HISTORICAL_ERP,
        rf + premium,
        confidence,
        {"risk_free_pct": rf, "excess_return_pct": premium, "months": months},
        f"{premium:+.2f}% mean excess return over T-bills across {months} months since "
        f"{excess.index[0]:%Y-%m}, plus the {rf:.2f}% T-bill yield.",
    )


# ------------------------------------------------------------------ 2. regime-adjusted
def forward_excess(excess: pd.Series, months: int) -> pd.Series:
    """Mean monthly excess return over the ``months`` after each month (t+1 .. t+months),
    indexed by that month; NaN where the full forward window has not happened yet."""
    ahead = excess[::-1].rolling(months, min_periods=months).mean()[::-1]
    return ahead.shift(-1)


def regime_adjusted(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """Exhibit 4 method 2: the historical premium conditioned on the current macro regime.

    Predictive, not contemporaneous: for each past month labelled like today it takes the mean
    excess return over the *following* horizon (3 years), which is what a CMA made in that
    month had to forecast. Averaging the returns *in* regime months instead uses information the
    label only has in hindsight -- recession months contain the crash.

    Credibility-weighted: premium = w * conditional + (1 - w) * unconditional, w = n / (n + k),
    so a regime seen only a few times stays near the unconditional premium. Forward windows
    overlap, so n overstates the independent evidence; k compensates.
    """
    rf = x.require_risk_free()
    if x.regime_labels is None or x.regime_labels.dropna().empty:
        raise Unavailable("no macro regime labels")
    labels = x.regime_labels.dropna()
    current = str(labels.iloc[-1])
    excess = x.excess_returns(asset_id)
    months_ahead = x.horizon_years * MONTHS_PER_YEAR
    if len(excess) < MIN_HISTORY_MONTHS + months_ahead:
        raise Unavailable(
            f"only {len(excess)} months of history; need {MIN_HISTORY_MONTHS + months_ahead}"
        )
    excess = excess.set_axis(excess.index.to_period("M"))
    by_month = pd.Series(labels.to_numpy(), index=pd.DatetimeIndex(labels.index).to_period("M"))
    ahead = pd.concat(
        [forward_excess(excess, months_ahead), by_month.reindex(excess.index)],
        axis=1,
        keys=["ahead", "label"],
    ).dropna()
    if ahead.empty:
        raise Unavailable("no labelled month has a complete forward window")
    in_regime = ahead.loc[ahead["label"] == current, "ahead"]

    unconditional = float(ahead["ahead"].mean() * MONTHS_PER_YEAR * 100)
    n = len(in_regime)
    conditional = float(in_regime.mean() * MONTHS_PER_YEAR * 100) if n else unconditional
    weight = n / (n + s.regime.credibility_months)
    premium = weight * conditional + (1 - weight) * unconditional
    confidence = s.base_confidence(CmaMethodId.REGIME_ADJUSTED, asset_id, x.groups[asset_id])
    return _estimate(
        CmaMethodId.REGIME_ADJUSTED,
        rf + premium,
        confidence,
        {
            "risk_free_pct": rf,
            "regime_excess_return_pct": conditional,
            "unconditional_excess_return_pct": unconditional,
            "regime_months": n,
            "credibility_weight": weight,
        },
        f"After the {n} past months labelled {current}, excess returns over the next "
        f"{x.horizon_years} years averaged {conditional:+.2f}% a year (all months "
        f"{unconditional:+.2f}%); credibility weight {weight:.2f}, plus {rf:.2f}% T-bill.",
    )


# ------------------------------------------------------------------ 3. Black-Litterman
def _equilibrium(x: MarketInputs, s: CmaSettings) -> dict[str, float]:
    """Reverse optimisation for all assets at once: pi = delta * Sigma * w (decimal excess).

    ``w`` is each ETF's share of the 18 ETFs' assets under management -- the public proxy for
    market-cap weights. ``delta`` is the configured risk aversion, or with ``"historical"`` the
    AUM portfolio's mean excess return over its variance, clamped to ``risk_aversion_bounds``.
    """
    if x._equilibrium is not None:
        return x._equilibrium
    ids = x.covariance.asset_ids
    aum = {}
    for asset_id in ids:
        aum[asset_id] = x.snapshot(asset_id, "total_assets")
    total = sum(aum.values())
    weights = np.array([aum[a] / total for a in ids])
    sigma = np.asarray(x.covariance.matrix)

    common = x.returns[ids].dropna(how="any")
    market_excess = (common.to_numpy() @ weights) - x.risk_free.reindex(common.index).to_numpy()
    market_excess = market_excess[~np.isnan(market_excess)]
    variance = float(weights @ sigma @ weights)
    low, high = s.black_litterman.risk_aversion_bounds
    raw = float(market_excess.mean() * MONTHS_PER_YEAR / variance)
    configured = s.black_litterman.risk_aversion
    delta = min(max(raw, low), high) if configured == "historical" else float(configured)
    implied = delta * sigma @ weights
    x._equilibrium = {
        "risk_aversion": delta,
        "risk_aversion_raw": raw,
        **{f"pi:{a}": float(implied[i]) for i, a in enumerate(ids)},
        **{f"w:{a}": float(weights[i]) for i, a in enumerate(ids)},
    }
    return x._equilibrium


def bl_equilibrium(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """Exhibit 4 method 3: the return the market portfolio implies, given the covariance."""
    rf = x.require_risk_free()
    eq = _equilibrium(x, s)
    if f"pi:{asset_id}" not in eq:
        raise Unavailable(f"{asset_id} is not in the covariance matrix")
    premium = eq[f"pi:{asset_id}"] * 100
    weight = eq[f"w:{asset_id}"] * 100
    return _estimate(
        CmaMethodId.BL_EQUILIBRIUM,
        rf + premium,
        s.base_confidence(CmaMethodId.BL_EQUILIBRIUM, asset_id, x.groups[asset_id]),
        {
            "risk_free_pct": rf,
            "implied_excess_return_pct": premium,
            "market_weight_pct": weight,
            "risk_aversion": eq["risk_aversion"],
        },
        f"Equilibrium excess return {premium:+.2f}% at a {weight:.1f}% AUM weight and risk "
        f"aversion {eq['risk_aversion']:.2f}, plus {rf:.2f}% T-bill. ETF AUM is a proxy for "
        "market size.",
    )


# ------------------------------------------------------------------ equity valuation inputs
def _shiller_now(x: MarketInputs, s: CmaSettings) -> tuple[float, float, float, pd.Timestamp]:
    """(dividend yield %, CAPE, CAPE anchor, date) from the Shiller data, if fresh."""
    if x.shiller is None or x.shiller.empty:
        raise Unavailable("no Shiller data")
    frame = x.shiller.dropna(subset=["dividend", "price"])
    cape = x.shiller["cape"].dropna()
    if frame.empty or cape.empty:
        raise Unavailable("Shiller data has no dividends or CAPE")
    when = frame.index[-1]
    if (x.as_of - when).days > s.valuation.max_stale_days:
        raise Unavailable(f"Shiller dividends last observed {when.date()}")
    dividend_yield = float(frame["dividend"].iloc[-1] / frame["price"].iloc[-1] * 100)
    anchor = float(cape[cape.index >= pd.Timestamp(s.valuation.cape_anchor_since)].median())
    return dividend_yield, float(cape.iloc[-1]), anchor, when


def _nominal_growth(x: MarketInputs, s: CmaSettings) -> tuple[float, float]:
    age = s.valuation.max_survey_age_days
    return x.survey(s.growth_survey, age), x.survey(s.inflation_survey, age)


# ------------------------------------------------------------------ 4. inverse Gordon
def inverse_gordon(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """Exhibit 4 method 4 (Grinold & Kroner 2002): yield + nominal growth + valuation change.

    US Large Cap uses the Shiller dividend yield and lets CAPE revert to its post-1990 median over
    ``reversion_years``. Other equity classes use the ETF distribution yield and assume no
    valuation change (no long P/E history exists for them), at reduced confidence. Growth is SPF
    10-year real GDP plus CPI for every class. There is no public buyback yield, and per-share
    dilution is ignored too; the two roughly offset for US large caps.
    """
    real_growth, inflation = _nominal_growth(x, s)
    group = x.groups[asset_id]
    confidence = s.base_confidence(CmaMethodId.INVERSE_GORDON, asset_id, group)
    if asset_id == EQUITY_ANCHOR:
        dividend_yield, cape, anchor, _ = _shiller_now(x, s)
        years = s.valuation.reversion_years
        drift = ((anchor / cape) ** (1 / years) - 1) * 100
        source = (
            f"Shiller dividend yield; CAPE {cape:.1f} reverting to {anchor:.1f} over {years:g}y"
        )
    else:
        dividend_yield = x.snapshot(asset_id, "distribution_yield") * 100
        drift = 0.0
        confidence *= s.adjustments.fallback_input
        source = f"{x.tickers[asset_id]} distribution yield; no valuation history, drift 0"
    addback = x.variance_addback_pct(asset_id)
    compound = dividend_yield + real_growth + inflation + drift
    return _estimate(
        CmaMethodId.INVERSE_GORDON,
        compound + addback,
        confidence,
        {
            "income_yield_pct": dividend_yield,
            "real_growth_pct": real_growth,
            "inflation_pct": inflation,
            "valuation_change_pct": drift,
            "variance_addback_pct": addback,
        },
        f"{dividend_yield:.2f}% yield + {real_growth:.1f}% real growth + {inflation:.1f}% "
        f"inflation {drift:+.2f}% valuation change + {addback:.2f}% variance add-back ({source}).",
    )


# ------------------------------------------------------------------ 5. CAPE-implied
def implied_erp_cape(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """Exhibit 4 method 5 (Campbell & Shiller 1998): the earnings yield is a real return.

    Nominal return = earnings yield + expected inflation (SPF CPI10). The paper's formula reads
    as the earnings yield alone, which is a real return compared against nominal ones; adding
    inflation keeps every candidate nominal. US Large Cap uses 1/CAPE; others the ETF's trailing
    earnings yield, which is noisier.
    """
    inflation = x.survey(s.inflation_survey, s.valuation.max_survey_age_days)
    group = x.groups[asset_id]
    confidence = s.base_confidence(CmaMethodId.IMPLIED_ERP_CAPE, asset_id, group)
    if asset_id == EQUITY_ANCHOR:
        _, cape, _, _ = _shiller_now(x, s)
        earnings_yield = 100 / cape
        source = f"1/CAPE, CAPE {cape:.1f}"
    else:
        earnings_yield = x.snapshot(asset_id, "earnings_yield") * 100
        confidence *= s.adjustments.fallback_input
        source = f"{x.tickers[asset_id]} trailing earnings yield"
    if asset_id == "reits":
        confidence *= s.adjustments.reits_valuation
        source += "; REIT earnings are net of depreciation, so this understates"
    addback = x.variance_addback_pct(asset_id)
    return _estimate(
        CmaMethodId.IMPLIED_ERP_CAPE,
        earnings_yield + inflation + addback,
        confidence,
        {
            "earnings_yield_pct": earnings_yield,
            "inflation_pct": inflation,
            "variance_addback_pct": addback,
        },
        f"{earnings_yield:.2f}% real earnings yield ({source}) + {inflation:.1f}% expected "
        f"inflation + {addback:.2f}% variance add-back.",
    )


# ------------------------------------------------------------------ 6. survey consensus
def survey_consensus(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """Exhibit 4 method 6: the SPF's 10-year return forecast where one covers the asset."""
    variable = s.survey.get(asset_id)
    if variable is None:
        raise Unavailable(
            "no public consensus forecast for this asset; the judge may use the macro agent's "
            "view instead (the paper's alternative)"
        )
    value = x.survey(variable, s.valuation.max_survey_age_days)
    addback = x.variance_addback_pct(asset_id)
    return _estimate(
        CmaMethodId.SURVEY_CONSENSUS,
        value + addback,
        s.base_confidence(CmaMethodId.SURVEY_CONSENSUS, asset_id, x.groups[asset_id]),
        {"survey_pct": value, "variance_addback_pct": addback},
        f"SPF median {variable} {value:.2f}% a year over 10 years + {addback:.2f}% variance "
        "add-back.",
    )


# ------------------------------------------------------------------ fixed-income builder
def yield_building_block(asset_id: str, x: MarketInputs, s: CmaSettings) -> CmaMethodEstimate:
    """§3.3's fixed-income CMA builder: starting yield less expected credit losses.

    Over a horizon near the bond's duration, the starting yield is the best single predictor of
    the return. The first yield recipe in ``cma.yaml`` with fresh data wins; a proxy recipe or
    an unhedged foreign yield lowers confidence.
    """
    recipes = s.yields.get(asset_id)
    if not recipes:
        raise Unavailable("no yield recipe configured")
    age = s.valuation.max_stale_days
    reasons = []
    for recipe in recipes:
        try:
            values = {sid: x.latest(sid, age) for sid in recipe.series}
            spread = x.latest(recipe.add_spread, age) if recipe.add_spread else 0.0
        except Unavailable as exc:
            reasons.append(str(exc))
            continue
        base_yield = float(np.mean(list(values.values())))
        loss = s.credit_loss_pct.get(asset_id, 0.0)
        addback = x.variance_addback_pct(asset_id)
        confidence = s.base_confidence(
            CmaMethodId.YIELD_BUILDING_BLOCK, asset_id, x.groups[asset_id]
        )
        notes = [f"mean of {', '.join(recipe.series)}"]
        if recipe.add_spread:
            notes.append(f"+ {recipe.add_spread} spread")
        if recipe.fallback:
            confidence *= s.adjustments.fallback_input
            notes.append("proxy yield")
        if recipe.unhedged:
            confidence *= s.adjustments.currency_unhedged
            notes.append("local-currency yield on an unhedged USD holding")
        components = {
            "yield_pct": base_yield,
            "credit_loss_pct": -loss,
            "variance_addback_pct": addback,
        }
        if recipe.add_spread:
            components["spread_pct"] = spread
        return _estimate(
            CmaMethodId.YIELD_BUILDING_BLOCK,
            base_yield + spread - loss + addback,
            confidence,
            components,
            f"{base_yield:.2f}% starting yield"
            + (f" + {spread:.2f}% spread" if recipe.add_spread else "")
            + f" - {loss:.2f}% expected credit loss + {addback:.2f}% variance add-back "
            f"({'; '.join(notes)}).",
        )
    raise Unavailable("; ".join(reasons))


# ------------------------------------------------------------------ 7. auto-blend
def auto_blend(estimates: list[CmaMethodEstimate]) -> CmaMethodEstimate:
    """Exhibit 4 method 7: the confidence-weighted average of the available methods."""
    usable = [e for e in estimates if e.unavailable_reason is None and e.confidence > 0]
    total = sum(e.confidence for e in usable)
    if not usable or total <= 0:
        raise ValueError("no method produced an estimate; nothing to blend")
    weights = {e.method: e.confidence / total for e in usable}
    value = sum(weights[e.method] * e.expected_return_pct for e in usable)  # type: ignore[operator]
    confidence = sum(weights[e.method] * e.confidence for e in usable)
    return _estimate(
        CmaMethodId.AUTO_BLEND,
        value,
        confidence,
        {f"weight:{m.value}": w for m, w in weights.items()},
        f"Confidence-weighted average of {len(usable)} methods: "
        + ", ".join(f"{m.value} {w:.0%}" for m, w in weights.items())
        + ".",
    )


CALCULATORS: dict[CmaMethodId, Calculator] = {
    CmaMethodId.HISTORICAL_ERP: historical_erp,
    CmaMethodId.REGIME_ADJUSTED: regime_adjusted,
    CmaMethodId.BL_EQUILIBRIUM: bl_equilibrium,
    CmaMethodId.INVERSE_GORDON: inverse_gordon,
    CmaMethodId.IMPLIED_ERP_CAPE: implied_erp_cape,
    CmaMethodId.SURVEY_CONSENSUS: survey_consensus,
    CmaMethodId.YIELD_BUILDING_BLOCK: yield_building_block,
}


def unavailable(method: CmaMethodId, reason: str) -> CmaMethodEstimate:
    return CmaMethodEstimate(
        method=method, confidence=0.0, rationale=f"Unavailable: {reason}", unavailable_reason=reason
    )


def run_methods(asset_id: str, x: MarketInputs, s: CmaSettings) -> list[CmaMethodEstimate]:
    """Every method for one asset, in Exhibit 4 order, ending with the auto-blend."""
    group = x.groups[asset_id]
    out = []
    for method, calculate in CALCULATORS.items():
        if not s.applies(method, asset_id, group):
            out.append(unavailable(method, f"not applicable to {group}"))
            continue
        try:
            out.append(calculate(asset_id, x, s))
        except Unavailable as exc:
            out.append(unavailable(method, str(exc)))
    out.append(auto_blend(out))
    return out
