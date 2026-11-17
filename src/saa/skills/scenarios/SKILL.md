# Scenarios skill

Bull, base and bear expected returns for one asset class, taken from the spread of the CMA
candidate methods.

Ang, Azimbayev & Kim (2026), Exhibit 3 step 8: **"Scenario analysis (bull/bear from method
range)"**. That phrase is the whole specification — the paper names `scenarios.json` among the
asset-class agent's outputs and never says more about it — so the construction here follows the
phrase literally and the derivation is stated in every narrative.

## What it computes

The eight candidates in `cma_methods.json` disagree, often by several points. The judge
collapses them to one number in `cma.json`. This skill publishes the disagreement that the
judge collapsed, so a reader can see how much was discarded.

| Scenario | Estimate | Meaning |
|---|---|---|
| `bear` | the lowest available candidate | the most pessimistic defensible method |
| `base` | the judge's final estimate | the recommendation |
| `bull` | the highest available candidate | the most optimistic defensible method |

The bounds are therefore the same `[min_method, max_method]` interval that Exhibit 4's hard
constraint confines the judge to. A scenario is never an extrapolation beyond what some method
actually produced, which is the point: these are the range of views the methodology supports,
not a confidence interval and not a stress test.

`probability` is left unset. The paper assigns none, and nothing in the candidate set carries a
probability a scenario could inherit — the methods' `confidence` scores say how much to trust a
method, not how likely its number is to be realised. Filling the field would invent a
distribution, so `Scenario.probability` stays `None` and the contract permits that.

## Why this is not a stress test

The range comes from methodological disagreement under today's conditions, not from adverse
states of the world. A bear case of "the implied-ERP method is right" is a far milder statement
than "equities fall 40%". Drawdown and tail risk are the CRO's job (`skills/risk/`), computed
from the return history at the portfolio level. Read these two together and do not substitute
one for the other.

## Reading the width

The spread is the honest error bar on the least reliable input in the pipeline. §3.4's case for
risk-structured methods is that "the covariance matrix is more reliably estimated than expected
returns" (Merton 1980); this skill is what makes that claim measurable per asset.

A wide range is informative rather than embarrassing. On the `claude2` inputs, US Growth spans
7.12–14.38% (the widest in the universe: valuation methods disagree violently with historical
ones when the earnings yield is near the risk-free rate) while International Developed spans
7.79–8.94%. A judge's point estimate carries very different weight in those two cases, and a
portfolio-construction agent reading only `cma.json` cannot tell them apart.

## Usage

```bash
uv run saa-skill scenarios --run-id <run>            # all 18 assets
uv run saa-skill scenarios --run-id <run> --assets gold us_growth
```

Requires `cma_methods.json` and `cma.json` for each asset, so it runs after the CMA judge.
Writes `cma/<asset>/scenarios.json` and `reports/scenarios.md`.

## Limitations

- **It inherits every limitation of the candidate set.** If all eight methods share a bias, the
  range is narrow and wrong rather than wide and honest.
- **Methods that report themselves unavailable are excluded**, so an asset with few available
  methods has an artificially narrow range. The output records how many candidates it used.
- **Gold and commodities have no cash-flow method available at all**, so their ranges rest on
  fewer and more heterogeneous candidates than the equity sleeves'. Their asset description
  files say so.
