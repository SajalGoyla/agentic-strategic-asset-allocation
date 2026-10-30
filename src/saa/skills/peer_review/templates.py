"""The review prompt: what one PC agent is shown about the proposal it has to review.

Ang, Azimbayev & Kim (2026) §3.5 gives the two framings and says what they are for -- an
intra-category review "is more likely to identify technical errors within a shared framework",
an inter-category review "can challenge foundational assumptions" -- so they are two different
prompts over the same material, not one prompt with a label.

Rendering the prompt is deterministic, so it sits in the skill. The reviewing agent that sends
it, with its own ``AGENT.md``, is stage 5's second half.

What a reviewer is and is not given is itself part of the protocol:

* **The reviewed proposal's weights, statistics, rationale and CRO report.** The review is of
  an argued proposal, not of a weight vector.
* **Its own method, and the fact that review is simultaneous.** A reviewer cannot see the
  reviews written about it, so it has no incentive to trade.
* **Not the other candidates.** §3.5 reviews a proposal on its merits; ranking happens in the
  vote, which is a separate call over the whole field.
"""

from __future__ import annotations

import pandas as pd

from saa.contracts import CroReportBody, PcProposalBody, ReviewKind
from saa.skills.peer_review.assignment import Assignment

# §3.5's own account of why each pairing exists, handed to the reviewer as its brief.
REVIEW_FRAMING: dict[ReviewKind, str] = {
    ReviewKind.INTRA_CATEGORY: (
        "You and this agent belong to the same family, so you share its framework and its "
        "assumptions. §3.5 pairs you for that reason: a reviewer inside the framework **is "
        "more likely to identify technical errors within a shared framework**. Audit the "
        "execution. Is the estimator applied correctly for this universe? Is the objective "
        "the one the method is supposed to optimise? Does the result look like what this "
        "method does when it is working, or like what it does when an input is degenerate? "
        "Do not spend the review arguing against the family you are also in."
    ),
    ReviewKind.INTER_CATEGORY: (
        "You and this agent belong to different families and optimise for different things. "
        "§3.5 pairs you for that reason: a reviewer outside the framework **can challenge "
        "foundational assumptions**. Go after the premise. What does this method have to "
        "believe about expected returns, about the covariance matrix, or about the stability "
        "of either, for its portfolio to make sense? Does the current regime support that? "
        "Judge the method's own logic, not its distance from yours -- a portfolio being "
        "unlike the one you would build is not a weakness."
    ),
}

_SIMULTANEITY = (
    "Reviews are written simultaneously. You cannot see what was written about your own "
    "proposal, and the agent you are reviewing cannot respond to this. Write what you would "
    "stand behind if it were read aloud."
)


def _weights_table(
    weights: dict[str, float], asset_ids: list[str], benchmark: pd.Series | None = None
) -> str:
    header = "| asset | weight |" if benchmark is None else "| asset | weight | vs benchmark |"
    lines = [header, "|---|---|" if benchmark is None else "|---|---|---|"]
    for asset_id in asset_ids:
        weight = weights.get(asset_id, 0.0)
        if weight <= 0.0005:
            continue
        if benchmark is None:
            lines.append(f"| {asset_id} | {weight:.1%} |")
        else:
            active = weight - float(benchmark.get(asset_id, 0.0))
            lines.append(f"| {asset_id} | {weight:.1%} | {active:+.1%} |")
    held = sum(1 for w in weights.values() if w > 0.0005)
    lines.append(f"\n{held} of {len(asset_ids)} assets held.")
    return "\n".join(lines)


def _risk_block(report: CroReportBody | None) -> str:
    if report is None:
        return (
            "No CRO report was produced for this portfolio in this run, so judge it on the "
            "ex-ante statistics above."
        )

    def num(value: float | None, suffix: str = "%") -> str:
        return "not available" if value is None else f"{value:.2f}{suffix}"

    return f"""| metric | value |
|---|---|
| backtest volatility | {num(report.backtest_volatility_pct)} |
| backtest Sharpe | {num(report.backtest_sharpe, "")} |
| monthly 95% VaR (loss) | {num(report.var_95_pct)} |
| maximum drawdown | {num(report.max_drawdown_pct)} |
| composite risk score | {report.risk_score:.2f} of 1.00 |

The CRO's assessment: {report.judgment.commentary}

Key risks it named: {"; ".join(report.judgment.key_risks)}"""


def _backtest_compliance(report: CroReportBody | None) -> str:
    """The CRO's full check, which adds the drawdown limit on the backtest. Shown beside the
    ex-ante result because a proposal that passes one can fail the other."""
    if report is None:
        return "No CRO check: the backtest drawdown limit was not evaluated."
    breaches = [v for v in report.ips_compliance.violations if v.severity == "hard"]
    listed = "".join(f"\n- {v.rule}: {v.message}" for v in breaches)
    return (
        "With the backtest (the CRO's check, including the drawdown limit): "
        f"**{'compliant' if not breaches else 'breaches'}**{listed}"
    )


def render_review_prompt(
    assignment: Assignment,
    reviewed: PcProposalBody,
    *,
    asset_ids: list[str],
    as_of,
    regime: str | None = None,
    ips_status: str = "draft",
    benchmark: pd.Series | None = None,
    cro_report: CroReportBody | None = None,
    reviewer_method: str | None = None,
) -> str:
    """The user prompt for one review. ``assignment`` fixes who is reviewing whom, and why."""
    if assignment.reviewer == assignment.reviewed:
        raise ValueError(f"{assignment.reviewer} cannot review itself")

    te = (
        "not computed"
        if reviewed.ex_ante_tracking_error_pct is None
        else f"{reviewed.ex_ante_tracking_error_pct:.2f}%"
    )
    effective_n = "–" if reviewed.effective_n is None else f"{reviewed.effective_n:.1f}"
    violations = (
        "\n".join(
            f"- [{v.severity}] {v.rule}: {v.message}" for v in reviewed.ips_compliance.violations
        )
        or "None."
    )
    return f"""Review one peer's portfolio proposal.

You are agent `{assignment.reviewer}`{f" ({reviewer_method})" if reviewer_method else ""}, in the
{assignment.reviewer_category.value} family. You are reviewing `{assignment.reviewed}`
(**{reviewed.method}**, {assignment.reviewed_category.value} family). This is an
{assignment.kind.value.replace("_", "-")} review.

As-of date: {as_of}
Macro regime: {regime or "unknown"}
Governing IPS status: {ips_status}

## Your brief

{REVIEW_FRAMING[assignment.kind]}

{_SIMULTANEITY}

## The proposal

| metric | value |
|---|---|
| expected return | {reviewed.expected_return_pct:.2f}% |
| expected volatility | {reviewed.expected_volatility_pct:.2f}% |
| Sharpe ratio | {reviewed.sharpe_ratio:.2f} |
| effective number of assets (exp of weight entropy, Meucci 2009; not 1/HHI) | {effective_n} of {len(asset_ids)} |
| ex-ante tracking error vs. the IPS benchmark | {te} |

{_weights_table(reviewed.weights, asset_ids, benchmark)}

### IPS compliance
Ex-ante (return, volatility, tracking error; no hard violation): **{reviewed.ips_compliance.compliant}**
{violations}

{_backtest_compliance(cro_report)}

A breach does not disqualify a candidate — the hard limits bind on the CIO's final portfolio,
not on each proposal. Treat a breach as evidence about what this portfolio would contribute,
not as grounds for dismissing it.

### Its own case

{reviewed.rationale}

{("Its notes: " + reviewed.notes) if reviewed.notes else ""}

## The CRO's risk report

{_risk_block(cro_report)}

## What to write

- `strengths`: what this proposal gets right, specifically. If you can find nothing, say so
  rather than inventing something.
- `weaknesses`: where it is vulnerable, and under what conditions the vulnerability bites.
- `technical_errors`: anything you believe is actually wrong — a misapplied estimator, a
  mis-specified objective, a number that cannot follow from the stated method. Leave it empty
  if you found none; do not pad it with disagreements.
- `score`: 0 to 1, your overall assessment of the proposal's quality. This is not a vote and
  does not decide anything on its own.
- `rationale`: the reasoning behind the score, for a reader who will also see the other
  reviews of this proposal.

Judge the proposal, not the agent, and do not argue for your own method.
"""
