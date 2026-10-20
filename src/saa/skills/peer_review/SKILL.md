# Peer Review Skill

Used by: the peer-review stage (stage 5). Paper reference: Ang, Azimbayev & Kim (2026) §3.5.

Deterministic: this skill decides **who reviews whom** and renders **what each reviewer is
shown**. It never calls a model. The reviewing agent that sends the prompt is the second half
of stage 5 and lands with the review cycle.

```bash
uv run saa-skill review-assign --run-id <run>             # pairing from the run's proposals
uv run saa-skill review-assign --run-id <run> --seed 42   # override the derived seed
```

## The protocol

§3.5: "Each PC agent reviews exactly two peers — one from its own category, which is more
likely to identify technical errors within a shared framework, and one from a different
category, which can challenge foundational assumptions. Assignments are randomized with a
recorded seed."

So for a 15-agent roster there are 30 reviews: 15 intra-category and 15 inter-category. The
pairing is built from the proposals the run actually produced, not the static roster, so a
method that failed to run is never assigned a reviewer.

## The seed

The seed defaults to the first 32 bits of the SHA-256 of the run id, so the pairing is
reproducible from the run's name alone — a reader with the run id can re-derive who reviewed
whom without being handed a separate number. `--seed` overrides it. Either way the seed goes
in the assignment report and in `header.seed` of every review the run writes, which is what
§3.5's "recorded seed" asks for.

## Two things the paper leaves open

**Balance.** A free random draw leaves some proposals with four reviews and others with none,
and an unreviewed proposal still goes to the vote carrying its own unexamined case. So each
reviewer picks the eligible peer with the fewest reviews so far, with ties broken by the seeded
shuffle. The pairing stays random; the load does not. `validate_plan` refuses a plan that would
send any proposal to the vote unreviewed.

The greedy pass alone still left about one seed in seven unbalanced on the 15-agent roster —
one proposal with a single review, another with three — so a repair pass follows it
(decision 43). Reviews are redirected along an augmenting path: a review of an over-reviewed
proposal moves to a fully-reviewed one, freeing one of its reviews to move on, until the short
proposal gains one. Every move keeps the reviewer and the review kind, and the search is
deterministic, so the seed still reproduces the plan. Measured over 2,000 seeds: every proposal
gets exactly two reviews (was 1,723 of 2,000).

## The reviews themselves

`uv run saa-agent peer-review --run-id <run> [--no-llm]` (`agents/peer_review`) writes the 30
reviews over this plan. The model fills only `ReviewJudgment` — strengths, weaknesses,
technical errors, score, rationale — and who reviewed whom and the review kind come from the
plan. `--no-llm` writes a metric-based review: the six-dimension composite from
`skills/method_scoring` as the score, and the proposal's best and worst dimensions as its
strengths and weaknesses.

**A category of one.** The PC-researcher is its own category (Exhibit 9 lists it as "E:
PC-Researcher"), so it has no intra-category peer and no shuffle will find one. Rather than
drop its second review, it writes a second inter-category review instead, and the substitution
is recorded in the plan's `fallbacks` and printed in the report (decision 35). The same rule
covers any family that happens to have one member in a given run.

## What a reviewer is shown

| Given | Why |
|---|---|
| its own id, method and family | the brief depends on which side of the pairing it is on |
| the reviewed proposal's weights, active weights, statistics and rationale | §3.5 reviews an argued proposal, not a weight vector |
| the reviewed portfolio's IPS compliance result | with the reminder that a breach does not disqualify a candidate (decision 32) |
| the CRO's risk report on that portfolio | realised risk the ex-ante statistics do not show |
| that reviews are simultaneous | it cannot see what was written about it, so there is nothing to trade |

And deliberately **not** the other candidates. A review is of one proposal on its merits;
ranking the field is the vote, which is a separate call with the whole field in view.

The two briefs in `REVIEW_FRAMING` are the paper's own account of why each pairing exists.
Intra-category: audit the execution, is the estimator applied correctly, does the result look
like this method working or like this method with a degenerate input. Inter-category: go after
the premise, what does the method have to believe about expected returns or the covariance
matrix, and does the regime support it. Both are told that a portfolio being unlike the
reviewer's own is not a weakness.
