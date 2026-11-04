# Macro View

**Regime:** expansion stall-speed expansion with sticky inflation and restrictive real rates, borderline late-cycle  
**Confidence:** low (0.36)  
**Recession probability:** 20–30%  
**As of:** 2026-10-01 (data through 2026-08-31)  
**IPS:** v0.2 (draft)

## Dimension scores

| dimension | score | indicators | point-in-time | rationale |
|---|---|---|---|---|
| growth | +0.053 | 11 | 0/11 | Barely positive and uniformly near zero. Payrolls are flat. Industrial production, retail sales, claims and GDPNow are mildly positive. Real GDP (stale, April) and sentiment are soft. This reads as broad stall-speed growth rather than a hidden split, with modestly positive momentum. |
| inflation | -0.270 | 9 | 0/9 | The negative score means inflation is running above its own history, not contained. Core PCE, headline measures and market and survey expectations are all elevated, and the Cleveland Fed 10-year measure is especially high. That is a persistent squeeze rather than a spike. |
| monetary_policy | -0.217 | 7 | 0/7 | Restrictive in level but easing in direction. The target-range change is supportive, so the Fed has been cutting. High real yields, a still-elevated funds rate, flat curves and a rising 2-year yield offset that. The rising 2-year suggests the market is pricing fewer cuts than the Fed's direction implies. |
| financial_conditions | +0.347 | 7 | 0/7 | Clearly loose and the most supportive dimension. Credit spreads are tight (HY and Baa especially), volatility and stress indices are low, and the dollar is softer. Because conditions lead activity, this is the main reason not to call late-cycle on the near-term read. |

## Narrative

We retain the rule-based prior of expansion, but at low confidence (0.36, slightly below the deterministic 0.43), and carry a qualifier: this is a stall-speed expansion with sticky inflation and restrictive real rates that sits on the border of late-cycle. The label has held for only three consecutive months after a long late-cycle run, briefly interrupted in March. The underlying scores have barely moved across that boundary. We are not overriding the rules, but downstream agents should treat expansion and late-cycle as near-equally plausible and avoid positioning that depends on a crisp expansion call.

Growth is close to zero rather than split. Payrolls are flat, while industrial production, retail sales, claims and GDPNow are mildly positive. Real GDP is the weakest hard series, but its latest scored reading dates from April and is stale. Momentum is modestly positive, which supports the expansion label. Inflation is the clearest negative: the inflation score is negative, which in this framework means inflation is above its own history, with core PCE and inflation expectations elevated. That is the stagflationary undertone the four-way label would otherwise lose. Policy is easing in direction, since the target range has been lowered, but remains restrictive in level, with high real yields and flat curves. The rising 2-year yield signals that markets doubt how far cuts can go. Following our guidance to prefer financial conditions for the near-term risk read, the loose conditions are decisive: tight credit spreads, low volatility and low stress argue against an imminent late-cycle deterioration. They also leave little cushion if sentiment turns.

We put the recession probability at 20-30%. That is slightly below the 25-35% baseline in our reference case, because the Sahm indicator and claims are benign and credit is supportive. Flat payrolls and elevated inflation keep it from going lower. On coverage, the newest scoreable month is August, 31 days before the as-of date, which is a normal lag. However, GDP, GDPNow and JOLTS are older, nothing for September is captured, and recent payroll prints are subject to revision. A soft September jobs print or a widening in credit spreads would be enough to flip this back to late-cycle. Governing policy (config/ips.yaml) is still in draft, so the regime-conditioned guidance downstream should be read as provisional.

## Key risks

- Labour market rolling over: payroll growth is already flat, and a negative turn in payrolls or a rise in claims would quickly push the growth composite below zero.
- Inflation re-acceleration or de-anchoring expectations, which would turn the easing path back toward tightening and satisfy the late-cycle inflation-squeeze rule.
- Rising 2-year yields against Fed cuts: market repricing could tighten financial conditions from currently tight-spread, low-vol levels.
- Credit spreads near historic tights leave little cushion. A spread widening shock would remove the one clearly supportive dimension.
- Stale coverage: real GDP is last scored at April, GDPNow and JOLTS at July, and nothing for September is in the table. Recent payroll prints are subject to revision.
- Regime instability: 10 of the last 13 months were late-cycle, so threshold-driven flips back are likely on small data moves.

## Provenance

- Scored history: 1995-01-31 to 2026-08-31 (380 months)
- Point-in-time scoring: no (latest vintage)
- Datasets: macro/fred_observations
- Model: claude-opus-5-5 (effort high), $0.0843

> The governing IPS has not been ratified. Figures are provisional.
