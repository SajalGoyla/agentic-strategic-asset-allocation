# Investment Policy Statement

The IPS is the governing document of this pipeline. Ang, Azimbayev & Kim (2026) put it at the
centre of the architecture: humans write it, every agent reads it, the CRO agent checks every
candidate portfolio against it, and the CIO agent is bound by it — compliance is
"non-negotiable" (§3.6). §5.2 goes further: adjusting the IPS is how the system moves between
autonomy levels, so it is the one place a human stays in control of what the agents may do.

This document is the human-readable form. `config/ips.yaml` is the machine-readable form that
agents actually load, and `src/saa/ips.py` is the single implementation of the rules.

**Status: v0.1, draft.** Six numbers are ours rather than the paper's and need Prof.
Glasserman's ratification — they are tagged `[proposed]` in the YAML and listed at the bottom
of this document. Agents should state in their output when they ran against a draft IPS
(`IPS.is_draft`).

## The three layers

Following §4 of the paper.

### Layer 1 — Universe

The 18 permissible asset classes, defined once in `config/universe.yaml` and referenced rather
than duplicated. On top of that the IPS adds what the paper implies but does not tabulate:
long-only, no leverage, no derivatives, and weight bounds per asset and per group.

**The bounds are deliberately wide, and that is a design decision rather than an oversight.**
The deliberation protocol in §3.5 assumes the 10–21 portfolio-construction agents produce
genuinely different portfolios worth reviewing and voting on. Bounds tight enough to feel
"safe" would pull equal-weight, inverse-volatility, risk parity and maximum diversification
onto broadly the same allocation, and the peer review would have nothing left to deliberate
about — we would have built the machinery of the paper with none of its content. The
volatility band, the drawdown limit and the tracking-error budget are the intended binding
constraints; the weight bounds exist to rule out degenerate portfolios, not to shape the
answer.

### Layer 2 — Objectives

| Objective | Value | Source |
|---|---|---|
| Target real return | CPI + 3.0–4.0% | paper §4 |
| Expected volatility | 8–12% | paper §4 |
| Maximum drawdown | −25% peak-to-trough | paper §4 |
| CMA horizon | 3 years, nominal | paper Exhibit 8 |

The return target is **soft**: a portfolio cannot guarantee a return, so missing the target is
reported in the board memo rather than disqualifying a candidate. The risk limits are what the
IPS can actually bind, and those are **hard**.

### Layer 3 — Active risk

Ex-ante tracking error against the 60/40 equity-bond benchmark must not exceed 6% (§4).

The paper never says which bond index makes up the 40%. We propose **60% US Large Cap / 40%
Intermediate Treasuries**, both drawn from the 18-asset universe. The reason is mechanical: the
CRO computes tracking error from the same covariance matrix the PC agents already use, so a
benchmark holding an asset outside the universe would require a 19th row in every covariance
estimate for the sake of one constraint. Both legs have return history from 1980
(`docs/asset_data_map.md`), comfortably covering the paper's 1996–2026 backtest window.

A closer match to a US Aggregate index — splitting the 40% as 70/30 intermediate Treasuries /
IG corporates — is noted in the YAML as the alternative for faculty review.

Note that **the benchmark is a measuring stick, not a candidate portfolio.** A 60% single-asset
weight would be a hard violation for a PC agent's proposal, but a 60/40 index is concentrated
by construction. Load-time validation therefore checks only that the benchmark is well-formed,
and `check_compliance` is never applied to it.

## How compliance is checked

One function, called by both the CRO agent (Week 7) and the CIO agent (Week 9), so the two
cannot drift apart:

```python
from saa.config import load_config
from saa.ips import PortfolioMetrics, check_compliance

config = load_config()
report = check_compliance(weights, metrics, config.ips, config.universe)

report.compliant      # False if any hard violation
report.hard           # disqualifying
report.soft           # flag in the board memo
report.not_evaluated  # rules no metric was supplied for
report.to_dict()      # embed in risk_report.json / cio_decision.json
```

Three properties worth knowing:

- **Hard vs. soft.** Hard violations disqualify; soft ones are recorded and surfaced.
  Structural rules (universe membership, fully invested, long-only, leverage, weight bounds)
  are always hard. The severity of each objective is set in the YAML so faculty can move one
  without touching code.
- **Unevaluated is never a pass.** Metrics arrive at different stages — ex-ante volatility
  exists at portfolio construction, realised drawdown only after a backtest. Anything missing
  lands in `not_evaluated`. A report can be `compliant` while having verified nothing, so
  callers should check both.
- **The `[paper]` / `[proposed]` tags stay in the YAML** until `status: ratified`. They make
  the faculty conversation a review of six specific numbers rather than of the whole document.

## Open question: the paper's own portfolio fails this IPS

Encoding §4 faithfully disqualifies the allocation the same paper publishes in §4.4. The final
portfolio has expected volatility of **7.54%** against a band of 8–12%, a backtest maximum
drawdown of **−25.6%** against a −25% limit, and an expected real return of **4.37%**
(6.87% nominal against the §4.1 CPI reading of 2.4%) against a 3–4% target band. Only tracking
error — 2.41% against a 6% budget — sits comfortably inside its limit. This is pinned in
`tests/test_ips.py::test_the_papers_own_portfolio_breaches_three_of_its_own_limits`.

This needs a decision before the CRO agent starts rejecting candidates on these rules in
Week 7. The three questions, in the order they matter:

1. **Should the volatility band bind from below?** Being *less* risky than policy contemplates
   is not obviously a fiduciary breach. Making the lower bound soft — or dropping it and
   keeping only the 12% ceiling — would resolve the largest of the three.
2. **Does the drawdown limit bind ex-ante or on the backtest?** −25.6% is a realised 1996–2026
   figure, not a forward-looking estimate. If the limit is meant as an ex-ante risk budget,
   the backtest number should be reported rather than enforced.
3. **Should exceeding the return target count at all?** It currently does, as a soft
   violation, on the reasoning that a portfolio forecast well above target may be taking more
   risk than policy contemplates. Here it sits alongside *below-band* volatility, so the two
   signals conflict — the portfolio is forecast to earn more while risking less.

The cleanest reading is that the paper's IPS is illustrative rather than binding on its own
example. We should decide which of its limits we intend to enforce literally, because we are
building the machinery that will enforce them.

## Numbers needing ratification

Everything tagged `[proposed]` in `config/ips.yaml`:

| Item | Proposed | Why it is ours |
|---|---|---|
| 60/40 benchmark composition | 60% US Large Cap / 40% Intermediate Treasuries | Paper says only "60/40 equity-bond" |
| Per-asset weight bounds | 0–25% | Not published |
| Per-group weight bounds | equity 30–70%, FI 20–60%, real assets 0–15%, cash 0–15% | Not published |
| Permitted instruments | Long-only, no leverage, no derivatives | Implied by an ETF-investable universe, never stated |
| Rebalancing drift trigger | 5% absolute weight drift | Paper says "off-cycle drift triggers" without a threshold |
| Escalation triggers | Three conditions (see YAML) | Paper says §5.2 the IPS sets them, without specifics |

Plus the three severity questions in the section above.

## Reference

Ang, Andrew, Nazym Azimbayev, and Andrey Kim. 2026. *"The Self-Driving Portfolio: Agentic
Architecture for Institutional Asset Management."* §3.1, §3.6, §4, §5.2.
