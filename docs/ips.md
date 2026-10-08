# Investment Policy Statement

The IPS is the governing document of this pipeline. Ang, Azimbayev & Kim (2026) put it at the
centre of the architecture: humans write it, every agent reads it, the CRO agent checks every
candidate portfolio against it, and the CIO agent is bound by it — compliance is
"non-negotiable" (§3.6).

**Where the hard limits bind.** On the portfolio the CIO recommends, and only there
(decision 32). The PC agents' candidates are checked against the same rules by the same
function, and the CRO reports every violation, but a candidate that breaks a limit stays in
the review, the vote and the CIO's ensemble pool; IPS compliance is one of the CIO's six scoring
dimensions (15%). That is how the paper works: its adversarial diversifier breaks the drawdown
limit (−46.3%) and still receives ensemble weight, because "the scoring gives the CIO agent
latitude to value ensemble diversification alongside standalone quality" (§4.4). §5.2 goes further: adjusting the IPS is how the system moves between
autonomy levels, so it is the one place a human stays in control of what the agents may do.

This document is the human-readable form. `config/ips.yaml` is the machine-readable form that
agents actually load, and `src/saa/ips.py` is the single implementation of the rules.

**Status: v0.2, draft.** Prof. Glasserman answered the open questions on 2026-09-25 and those
answers are encoded below, but the document has not been formally ratified — answering
individual questions is not the same as signing it off. `status` stays `draft` until someone
does, and `IPS.is_draft` remains true, so agents keep recording that they ran against a draft
policy. The YAML tags every figure `[paper]`, `[faculty]` or `[proposed]`.

## The three layers

Following §4 of the paper.

### Layer 1 — Universe

The 18 permissible asset classes, defined once in `config/universe.yaml` and referenced rather
than duplicated. On top of that the IPS adds what the paper implies but does not tabulate: long-only, no
leverage, no derivatives.

**There are no weight limits, per asset or per group.** Faculty, 2026-09-25: "Since the assets
are really asset classes, I'm not sure we need weight limits — why rule out the possibility of
going all in on one asset class." The volatility band, the drawdown limit and the
tracking-error budget are the binding constraints.

That also suits the deliberation protocol in §3.5, which assumes the 10–21 portfolio-
construction agents produce genuinely different portfolios worth reviewing and voting on.
Bounds tight enough to feel "safe" would pull equal-weight, inverse-volatility, risk parity and
maximum diversification onto broadly the same allocation, and the peer review would have
nothing left to deliberate about.

The bounds machinery is retained in `saa.ips` rather than deleted, so a future policy can
reintroduce limits by editing the YAML alone. `IPS.has_weight_bounds` reports whether any are
in force, and there is a test covering both paths.

### Layer 2 — Objectives

| Objective | Value | Source |
|---|---|---|
| Target real return | CPI + 3.0–4.0% | paper §4 |
| Expected volatility | 8–12% | paper §4 |
| Maximum drawdown | −25% peak-to-trough | paper §4 |
| CMA horizon | 3 years, nominal | paper Exhibit 8 |

**Every limit is hard.** Asked how strictly the pipeline should adhere to the IPS limits,
faculty answered "treat them as hard constraints" (2026-09-25). That includes the return
target, which binds from above as well as below — a portfolio forecast to earn more than
CPI + 4% is disqualified as surely as one forecast to earn less. Worth confirming at a
touchpoint, since a return target is arguably different in kind from a risk limit.

### Layer 3 — Active risk

Ex-ante tracking error against the 60/40 equity-bond benchmark must not exceed 6% (§4).

The paper never says what sits on either side of the 60/40. Faculty, 2026-09-25: "Agreed on
the equity component. For the bonds I would use 75% Intermediate Treasuries and 25% IG
Corporates." So the benchmark is **60% US Large Cap, 30% Intermediate Treasuries, 10%
Investment-Grade Corporates**.

All three legs sit inside the 18-asset universe, which matters mechanically: the CRO computes
tracking error from the same covariance matrix the PC agents already use, so a benchmark
holding an asset outside the universe would need a 19th row in every covariance estimate for
the sake of one constraint. All three also have return history from 1980
(`docs/asset_data_map.md`), comfortably covering the paper's 1996–2026 backtest window.

Note that **the benchmark is a measuring stick, not a candidate portfolio.** Load-time
validation checks only that it is well-formed — its assets exist, its weights are non-negative
and sum to one — and `check_compliance` is never applied to it. That distinction costs nothing
today, with no weight limits in force, but it is what stops a reintroduced per-asset cap from
rejecting the benchmark's own 60% equity leg.

## How compliance is checked

One function, called by both the CRO agent (Week 7) and the CIO agent (Week 9), so the two
cannot drift apart:

```python
from saa.config import load_config
from saa.ips import PortfolioMetrics, check_compliance

config = load_config()
report = check_compliance(weights, metrics, config.ips, config.universe)

report.compliant      # False if any hard violation
report.hard           # disqualifying for the CIO's recommendation
report.soft           # flag in the board memo
report.not_evaluated  # rules no metric was supplied for
report.to_dict()      # embed in risk_report.json / cio_decision.json
```

Three properties worth knowing:

- **Hard vs. soft.** Hard violations disqualify the CIO's recommended portfolio; soft ones
  are recorded and surfaced. Candidates' violations of either kind are reported and scored.
  Structural rules — universe membership, fully invested, long-only, no leverage, and weight
  bounds where a policy sets any — are always hard. The severity of each objective is set in
  the YAML, so moving one is a config change rather than a code change.
- **Unevaluated is never a pass.** Metrics arrive at different stages — ex-ante volatility
  exists at portfolio construction, realised drawdown only after a backtest. Anything missing
  lands in `not_evaluated`. A report can be `compliant` while having verified nothing, so
  callers should check both.
- **Every figure carries its provenance.** The YAML tags each one `[paper]` or `[faculty]`,
  and the table at the end of this document lists them all, so it stays clear which numbers
  come from Ang et al. and which were decided here.

## Rebalancing

Quarterly, on the calendar. §3.6 mentions "off-cycle drift triggers", but faculty removed them
on 2026-09-25: "Otherwise, we would need to specify what happens if the trigger is breached —
e.g., go to cash." A trigger without a stated remedy is not implementable, so `drift_trigger_pct`
is null.

## The paper's own portfolio fails this IPS

Encoding §4 faithfully disqualifies the allocation the same paper publishes in §4.4. The final
portfolio has expected volatility of **7.54%** against a band of 8–12%, a backtest maximum
drawdown of **−25.6%** against a −25% limit, and an expected real return of **4.37%** (6.87%
nominal against the §4.1 CPI reading of 2.4%) against a 3–4% target band. Only tracking error —
2.41% against a 6% budget — sits comfortably inside.

Faculty, 2026-09-25: *"Those look like cases of bad rounding. Let's treat them as hard
constraints."*

So the volatility band and the drawdown limit bind strictly — on both sides of the band, and on
the backtest as well as ex-ante — and we accept that the paper's published figures would not
clear them. The CIO may not recommend a portfolio that breaks them; the CRO reports candidates'
breaches without rejecting them (decision 32).

All three limits are hard, so all three would reject it. The return figure is the one worth a
second look: it binds from above as well as below, which means a portfolio forecast to earn
more than the target is disqualified. That follows from the literal reading of "treat them as
hard constraints", and we have implemented it that way, but it is flagged for confirmation.

This is pinned in
`tests/test_ips.py::test_the_papers_own_portfolio_breaches_three_of_its_own_limits`, so any
future relaxation of either limit has to change a test that says why.

## Provenance of every figure

| Item | Value | Source |
|---|---|---|
| Universe | 18 asset classes | paper §4 |
| Real return target | CPI + 3.0–4.0%, hard | paper §4, severity by faculty |
| Volatility band | 8–12%, hard both sides | paper §4, severity by faculty |
| Maximum drawdown | −25%, hard, incl. backtest | paper §4, severity by faculty |
| CMA horizon | 3 years nominal | paper Exhibit 8 |
| Tracking-error budget | ≤ 6% ex-ante | paper §4 |
| Benchmark | 60% US Large Cap / 30% Int. Treasuries / 10% IG Corporates | faculty |
| Permitted instruments | Long-only, no leverage, no derivatives | faculty |
| Weight limits | None | faculty |
| Rebalancing | Quarterly, no drift trigger | paper §3.6 cadence, faculty on triggers |
| Escalation triggers | Three conditions | ours (paper §5.2 requires them, unspecified) |

## Reference

Ang, Andrew, Nazym Azimbayev, and Andrey Kim. 2026. *"The Self-Driving Portfolio: Agentic
Architecture for Institutional Asset Management."* §3.1, §3.6, §4, §5.2.
