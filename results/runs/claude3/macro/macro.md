# Macro View

**Regime:** expansion fragile, late-cycle-adjacent expansion with sticky above-history inflation  
**Confidence:** low (0.35)  
**Recession probability:** 20–30%  
**As of:** 2026-10-01 (data through 2026-08-31)  
**IPS:** v0.2 (ratified)

## Dimension scores

| dimension | score | indicators | point-in-time | rationale |
|---|---|---|---|---|
| growth | +0.053 | 11 | 0/11 | The composite sits barely above zero, and that masks a split. Industrial production, retail sales, claims, CFNAI and GDPNow are mildly positive, while payrolls are flat, JOLTS openings are slightly negative and consumer sentiment is weak. The GDP reading is stale (April) and negative. This looks like moderate, not strong, growth with a softening labour core, though the Sahm rule remains benign. |
| inflation | -0.270 | 9 | 0/9 | The negative sign means inflation is high relative to its own history, not low. It is broad-based: core PCE and headline PCE are the weakest realised measures, and market and survey expectations (breakevens, Michigan, Cleveland Fed 10-year) are elevated. That makes this a sticky-inflation backdrop rather than a transitory spike. |
| monetary_policy | -0.217 | 7 | 0/7 | Direction and level disagree. The positive score on the change in the target-range upper limit points to cuts, so direction is easing. But real 10-year yields, the effective funds rate level and a rising 2-year yield are all restrictive, and both curve spreads score flat relative to history. I read this as easing from a still-restrictive level, with the market partly pricing cuts back out. |
| financial_conditions | +0.353 | 7 | 0/7 | This is the clearest supportive signal. Every component is positive, led by tight high-yield, Baa and IG spreads, with low stress indices, a subdued VIX and a softer dollar. As the leading block, it argues against near-term recession risk. |

## Narrative

We retain the rule-based classification of expansion but at low confidence (0.35, below even the deterministic 0.43), with a qualifier: this is a fragile, late-cycle-adjacent expansion with sticky inflation. We do not override the prior. Financial conditions, the most forward-looking block, are clearly loose. Policy direction is easing. Measured growth momentum is positive. Together these give no defensible basis yet to call late-cycle. That said, the label has held for only 3 of the last 13 months after a long late-cycle run, and the late-cycle rule (positive growth alongside an inflation or policy squeeze) is close to firing. Downstream agents should treat expansion and late-cycle as near-equal-weight scenarios rather than lean hard on the expansion label.

The growth composite of roughly zero is not steady moderate growth across the board. Activity and spending indicators (industrial production, retail sales, CFNAI, GDPNow, claims) are mildly positive, while payroll momentum is flat, job openings are soft and consumer sentiment is weak. The real GDP reading is as of April and negative year-on-year, so part of the growth picture is stale. Inflation scores negative, meaning it is running above its own history. That holds across core and headline PCE and CPI and across market and survey expectations, which is what keeps stagflationary risk on the table. Policy is the classic split: the Fed has been cutting, which is supportive in direction, but real yields and the funds-rate level remain restrictive. A rising 2-year yield suggests markets are pricing out some easing. Curve spreads are flat relative to history, a late-cycle marker but not a recession call. Where conditions and activity disagree on the near-term risk read, we follow financial conditions: tight credit spreads and low stress argue against imminent recession. Hence a baseline recession probability of 20-30%, slightly below a neutral late-cycle baseline.

Data coverage: the newest scoreable month is August 2026, 31 days before the 1 October as-of date, so September is unobserved. This is a live run on latest vintages; none of the contributing series are flagged point-in-time, which is acceptable for a current call but would not be for a backtest. The momentum figure was supplied over a stated window of 380 months rather than the usual six-month window. We have treated its sign as indicative only, and the window should be checked in the scoring output. The governing IPS (config/ips.yaml) is reported as ratified, so this view operates under the approved policy. The main triggers that would move us to late-cycle are any of the following:
- a renewed rise in unemployment or claims;
- a pause in Fed easing driven by inflation;
- a widening in high-yield spreads.

## Key risks

- Labour-market roll-over: flat payroll momentum and soft openings could tip the Sahm indicator if unemployment starts rising.
- Sticky inflation constraining the Fed: elevated core PCE and expectations, alongside a rising 2-year yield, may halt the easing path and push the regime to late-cycle with stagflationary risk.
- Complacent credit pricing: HY and IG spreads tight versus history leave little cushion if growth disappoints, and a reversal in financial conditions would be the leading signal of a regime change.
- Data staleness: GDP is as of April, and GDPNow and JOLTS as of July. The August cut-off leaves September unobserved, and GDP-based growth evidence is several months old.
- Label instability: the regime has flipped between expansion and late-cycle four times in 13 months, so threshold effects may be driving the call more than the economy is.

## Provenance

- Scored history: 1995-01-31 to 2026-08-31 (380 months)
- Point-in-time scoring: no (latest vintage)
- Datasets: macro/fred_observations
- Model: claude-opus-5-5 (effort high), $0.0857
