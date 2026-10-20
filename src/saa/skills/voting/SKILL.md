# Voting Skill

Used by: the vote stage (stage 5, `agents/vote`) and, through the shortlist, the revision step
and the CIO. Paper reference: Ang, Azimbayev & Kim (2026) §3.5 and Exhibit 9.

## What it does

Tallies the fifteen modified-Borda ballots, blends the points with the six-dimension metric
score, ranks the field, and picks a five-member shortlist that satisfies the diversity rule.
Pure arithmetic; the ballots come from the vote agent.

```bash
uv run saa-agent vote --run-id <run> [--no-llm]   # ballots, then the tally
```

It writes `review/<voter>/vote.json` per ballot, `review/vote_tally.json` (contract
`vote_tally`, one row per candidate as in Exhibit 9) and `reports/vote_tally.md`.

## The steps

1. **Points.** Each ballot gives 5, 4, 3, 2, 1 to its top five and -2 to its bottom flag,
   excluding the voter (§3.5). A candidate on no ballot scores 0.
2. **Blend.** Points are min-max normalised to [0, 1] and blended with the metric score
   (`skills/method_scoring`) at a regime-dependent weight: `vote_weight` in
   `config/voting.yaml`, 0.4-0.6 on the vote, the rest on the metric.
3. **Composite.** The blend is rescaled so the top candidate is 1.000 and the bottom 0.000 —
   Exhibit 9's convention. Ties are broken by the metric score, then the agent id.
4. **Diversity.** The top five must span at least three of the four canonical families; the
   PC-researcher does not count toward them. While it does not, the lowest-ranked shortlist
   member from a family represented more than once is replaced by the highest-ranked
   candidate from a family not yet on it. Every substitution is recorded in the report, and the
   contract refuses a shortlist that still fails the rule.
5. **Dissent.** A candidate bottom-flagged on at least half the ballots is listed — §4.3's
   bottom-ranked methods "trigger dissent reports".

## What the paper leaves open, and our choices

| Open point | Ours | Why |
|---|---|---|
| The blend weight | 0.6 on the vote in expansion and recovery, 0.5 late-cycle, 0.4 in recession [proposed] | lean on the objective metric when the regime is hostile |
| How points and metric combine | normalise points to [0, 1] first | points and a 0-1 score are on different scales; normalising keeps the weight meaningful |
| How the diversity rule is met | swap the lowest duplicate for the best missing family | keeps the vote's order as far as the rule allows |
| The dissent threshold | half the ballots | the paper's dissent cases were near-unanimous (18 of 21 flagged the adversarial diversifier) |

## Caveats

- `--no-llm` ballots all rank by the same metric, so they agree with each other far more than
  agents would: on the 2026-10-01 free run 12 of 15 bottom-flagged the same candidate. The free
  tally checks the arithmetic, not the deliberation.
- The voter is shown every proposal, CRO figure and review, but not the metric score, so the
  blend does not count the metric twice.
