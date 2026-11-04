# CMA method candidates as of 2026-10-01

Arithmetic expected annual return, nominal, percent; 3-year horizon. A dash means the method does not apply or lacks data (reasons below). Current regime: expansion; Black-Litterman risk aversion: 2.50.

| Asset | Vol | Hist | Regime | BL | Gordon | CAPE | Survey | Yield | Blend | Range |
|---|---|---|---|---|---|---|---|---|---|---|
| us_large_cap | 14.8 | 12.7 | 13.5 | 8.3 | 3.6 | 5.9 | 8.1 | - | 8.3 | 3.6-13.5 |
| us_small_cap | 19.5 | 12.4 | 12.3 | 8.8 | 6.7 | 10.0 | - | - | 10.1 | 6.7-12.4 |
| us_value | 14.8 | 12.0 | 12.5 | 8.0 | 9.0 | 8.1 | - | - | 10.1 | 8.0-12.5 |
| us_growth | 16.9 | 13.5 | 14.4 | 8.5 | 7.6 | 7.1 | - | - | 10.4 | 7.1-14.4 |
| intl_developed | 16.0 | 8.3 | 7.8 | 8.0 | 8.5 | 8.9 | - | - | 8.3 | 7.8-8.9 |
| emerging_markets | 22.1 | 11.4 | 8.0 | 9.0 | 9.0 | 11.8 | - | - | 9.9 | 8.0-11.8 |
| short_treasuries | 1.7 | 4.9 | 4.9 | 4.0 | - | - | - | 4.8 | 4.7 | 4.0-4.9 |
| intermediate_treasuries | 6.5 | 6.4 | 6.6 | 4.1 | - | - | 4.2 | 5.4 | 5.2 | 4.1-6.6 |
| long_treasuries | 12.4 | 7.0 | 8.2 | 4.2 | - | - | - | 6.4 | 6.3 | 4.2-8.2 |
| ig_corporates | 7.1 | 6.7 | 6.7 | 5.0 | - | - | - | 6.2 | 6.1 | 5.0-6.7 |
| hy_corporates | 8.4 | 7.8 | 7.1 | 5.8 | - | - | - | 6.0 | 6.4 | 5.8-7.8 |
| intl_sovereigns | 8.5 | 5.3 | 4.2 | 5.1 | - | - | - | 4.0 | 4.6 | 4.0-5.3 |
| intl_corporates | 9.2 | 6.1 | 5.0 | 5.5 | - | - | - | 5.2 | 5.4 | 5.0-6.1 |
| usd_em_debt | 14.0 | 10.3 | 10.2 | 6.5 | - | - | - | 6.4 | 7.9 | 6.4-10.3 |
| reits | 19.0 | 11.9 | 11.5 | 7.8 | 7.7 | 7.4 | - | - | 9.6 | 7.4-11.9 |
| gold | 17.9 | 8.9 | 5.7 | 5.4 | - | - | - | - | 6.8 | 5.4-8.9 |
| commodities | 19.1 | 6.5 | 4.2 | 5.9 | - | - | - | - | 5.6 | 4.2-6.5 |
| cash | 0.6 | 3.9 | 3.9 | 4.0 | - | - | 3.0 | 4.0 | 3.8 | 3.0-4.0 |

## Rationales

### us_large_cap

- **historical_erp** 12.67% (confidence 0.50): +8.64% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 13.52% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +9.75% a year (all months +8.70%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 8.26% (confidence 0.40): Equilibrium excess return +4.23% at a 48.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 3.63% (confidence 0.60): 0.93% dividends +1.28% net buybacks + 2.1% real growth + 2.3% inflation -4.08% valuation change + 1.09% variance add-back (net payout from WRDS 2025-12, rolled forward by SPY's price change; CAPE 40.0 reverting to 26.4 over 10y).
- **implied_erp_cape** 5.89% (confidence 0.50): 2.50% real earnings yield (1/CAPE, CAPE 40.0) + 2.3% expected inflation + 1.09% variance add-back.
- **survey_consensus** 8.09% (confidence 0.50): SPF median STOCK10 7.00% a year over 10 years + 1.09% variance add-back.
- **yield_building_block** unavailable: not applicable to equity
- **auto_blend** 8.35% (confidence 0.49): Confidence-weighted average of 6 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 14%, inverse_gordon 21%, implied_erp_cape 17%, survey_consensus 17%.

### us_small_cap

- **historical_erp** 12.38% (confidence 0.50): +8.35% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 12.33% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +8.20% a year (all months +8.59%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 8.82% (confidence 0.40): Equilibrium excess return +4.79% at a 4.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 6.65% (confidence 0.42): 1.21% dividends -0.86% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.90% variance add-back (net payout from WRDS 2025-12, rolled forward by IWM's price change; no long valuation history, drift 0).
- **implied_erp_cape** 9.98% (confidence 0.35): 5.78% real earnings yield (IWM trailing earnings yield) + 2.3% expected inflation + 1.90% variance add-back.
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** unavailable: not applicable to equity
- **auto_blend** 10.11% (confidence 0.42): Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%.

### us_value

- **historical_erp** 11.99% (confidence 0.50): +7.96% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 12.51% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +8.59% a year (all months +8.15%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 8.00% (confidence 0.40): Equilibrium excess return +3.97% at a 5.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 9.00% (confidence 0.42): 1.78% dividends +1.72% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.10% variance add-back (net payout from WRDS 2025-12, rolled forward by IWD's price change; no long valuation history, drift 0).
- **implied_erp_cape** 8.11% (confidence 0.35): 4.71% real earnings yield (IWD trailing earnings yield) + 2.3% expected inflation + 1.10% variance add-back.
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** unavailable: not applicable to equity
- **auto_blend** 10.06% (confidence 0.42): Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%.

### us_growth

- **historical_erp** 13.46% (confidence 0.50): +9.43% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 14.38% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +10.68% a year (all months +9.37%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 8.54% (confidence 0.40): Equilibrium excess return +4.51% at a 7.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 7.61% (confidence 0.42): 0.65% dividends +1.12% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.43% variance add-back (net payout from WRDS 2025-12, rolled forward by IWF's price change; no long valuation history, drift 0).
- **implied_erp_cape** 7.12% (confidence 0.35): 3.39% real earnings yield (IWF trailing earnings yield) + 2.3% expected inflation + 1.43% variance add-back.
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** unavailable: not applicable to equity
- **auto_blend** 10.43% (confidence 0.42): Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%.

### intl_developed

- **historical_erp** 8.29% (confidence 0.50): +4.26% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 7.79% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +3.48% a year (all months +4.60%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 8.02% (confidence 0.40): Equilibrium excess return +3.99% at a 4.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 8.47% (confidence 0.29): 2.79% dividends +0.00% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.28% variance add-back (dividends from WRDS 2026-09; no buyback data; no long valuation history, drift 0).
- **implied_erp_cape** 8.94% (confidence 0.35): 5.37% real earnings yield (EFA trailing earnings yield) + 2.3% expected inflation + 1.28% variance add-back.
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** unavailable: not applicable to equity
- **auto_blend** 8.28% (confidence 0.40): Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 15%, implied_erp_cape 18%.

### emerging_markets

- **historical_erp** 11.45% (confidence 0.50): +7.42% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 8.03% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +3.04% a year (all months +6.87%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 9.02% (confidence 0.40): Equilibrium excess return +4.99% at a 1.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 8.98% (confidence 0.29): 2.13% dividends +0.00% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 2.45% variance add-back (dividends from WRDS 2026-09; no buyback data; no long valuation history, drift 0).
- **implied_erp_cape** 11.76% (confidence 0.35): 7.01% real earnings yield (EEM trailing earnings yield) + 2.3% expected inflation + 2.45% variance add-back.
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** unavailable: not applicable to equity
- **auto_blend** 9.93% (confidence 0.40): Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 15%, implied_erp_cape 18%.

### short_treasuries

- **historical_erp** 4.88% (confidence 0.30): +0.85% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 4.86% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +0.82% a year (all months +0.86%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 4.03% (confidence 0.40): Equilibrium excess return +0.00% at a 1.6% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 4.82% (confidence 0.80): 4.81% starting yield - 0.00% expected credit loss + 0.01% variance add-back (mean of DGS1, DGS2, DGS3).
- **auto_blend** 4.66% (confidence 0.54): Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%.

### intermediate_treasuries

- **historical_erp** 6.41% (confidence 0.30): +2.38% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 6.61% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +2.55% a year (all months +2.65%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 4.13% (confidence 0.40): Equilibrium excess return +0.10% at a 2.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** 4.21% (confidence 0.50): SPF median BOND10 4.00% a year over 10 years + 0.21% variance add-back.
- **yield_building_block** 5.45% (confidence 0.80): 5.24% starting yield - 0.00% expected credit loss + 0.21% variance add-back (mean of DGS7, DGS10).
- **auto_blend** 5.20% (confidence 0.53): Confidence-weighted average of 5 methods: historical_erp 13%, regime_adjusted 11%, bl_equilibrium 18%, survey_consensus 22%, yield_building_block 36%.

### long_treasuries

- **historical_erp** 6.98% (confidence 0.30): +2.95% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 8.23% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +4.41% a year (all months +3.55%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 4.19% (confidence 0.40): Equilibrium excess return +0.16% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 6.43% (confidence 0.80): 5.66% starting yield - 0.00% expected credit loss + 0.77% variance add-back (mean of DGS20, DGS30).
- **auto_blend** 6.27% (confidence 0.54): Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%.

### ig_corporates

- **historical_erp** 6.71% (confidence 0.30): +2.68% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 6.71% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +2.59% a year (all months +2.94%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 5.01% (confidence 0.40): Equilibrium excess return +0.98% at a 1.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 6.17% (confidence 0.80): 6.02% starting yield - 0.10% expected credit loss + 0.25% variance add-back (mean of BAMLC0A0CMEY).
- **auto_blend** 6.08% (confidence 0.54): Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%.

### hy_corporates

- **historical_erp** 7.76% (confidence 0.30): +3.73% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 7.10% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +2.76% a year (all months +3.98%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 5.79% (confidence 0.40): Equilibrium excess return +1.76% at a 1.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 6.02% (confidence 0.80): 8.16% starting yield - 2.50% expected credit loss + 0.36% variance add-back (mean of BAMLH0A0HYM2EY).
- **auto_blend** 6.42% (confidence 0.54): Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%.

### intl_sovereigns

- **historical_erp** 5.32% (confidence 0.30): +1.29% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 4.23% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged -0.17% a year (all months +1.29%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 5.11% (confidence 0.40): Equilibrium excess return +1.08% at a 0.1% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 4.00% (confidence 0.48): 3.64% starting yield - 0.00% expected credit loss + 0.36% variance add-back (mean of IRLTLT01DEM156N, IRLTLT01JPM156N, IRLTLT01GBM156N, IRLTLT01FRM156N, IRLTLT01CAM156N; local-currency yield on an unhedged USD holding).
- **auto_blend** 4.63% (confidence 0.38): Confidence-weighted average of 4 methods: historical_erp 21%, regime_adjusted 17%, bl_equilibrium 28%, yield_building_block 34%.

### intl_corporates

- **historical_erp** 6.14% (confidence 0.30): +2.11% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 4.99% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +0.59% a year (all months +2.07%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 5.45% (confidence 0.40): Equilibrium excess return +1.42% at a 0.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 5.16% (confidence 0.48): 4.00% starting yield + 0.84% spread - 0.10% expected credit loss + 0.42% variance add-back (mean of IRLTLT01DEM156N, IRLTLT01GBM156N; + BAMLC0A0CM spread; local-currency yield on an unhedged USD holding).
- **auto_blend** 5.42% (confidence 0.38): Confidence-weighted average of 4 methods: historical_erp 21%, regime_adjusted 17%, bl_equilibrium 28%, yield_building_block 34%.

### usd_em_debt

- **historical_erp** 10.33% (confidence 0.30): +6.30% mean excess return over T-bills across 400 months since 1993-06, plus the 4.03% T-bill yield.
- **regime_adjusted** 10.17% (confidence 0.25): After the 173 past months labelled expansion, excess returns over the next 3 years averaged +5.98% a year (all months +6.60%); credibility weight 0.74, plus 4.03% T-bill.
- **bl_equilibrium** 6.55% (confidence 0.40): Equilibrium excess return +2.52% at a 0.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to fixed_income
- **implied_erp_cape** unavailable: not applicable to fixed_income
- **survey_consensus** unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative)
- **yield_building_block** 6.45% (confidence 0.56): 6.47% starting yield - 1.00% expected credit loss + 0.98% variance add-back (mean of BAMLEMCBPIEY; proxy yield).
- **auto_blend** 7.86% (confidence 0.41): Confidence-weighted average of 4 methods: historical_erp 20%, regime_adjusted 17%, bl_equilibrium 26%, yield_building_block 37%.

### reits

- **historical_erp** 11.94% (confidence 0.50): +7.91% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 11.45% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +7.08% a year (all months +8.47%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 7.77% (confidence 0.40): Equilibrium excess return +3.74% at a 4.3% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** 7.68% (confidence 0.42): 3.75% dividends -2.27% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.80% variance add-back (net payout from WRDS 2025-12, rolled forward by VNQ's price change; no long valuation history, drift 0).
- **implied_erp_cape** 7.42% (confidence 0.21): 3.31% real earnings yield (VNQ trailing earnings yield; REIT earnings are net of depreciation, so this understates) + 2.3% expected inflation + 1.80% variance add-back.
- **survey_consensus** unavailable: not applicable to real_assets
- **yield_building_block** unavailable: not applicable to real_assets
- **auto_blend** 9.56% (confidence 0.41): Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 22%, implied_erp_cape 11%.

### gold

- **historical_erp** 8.90% (confidence 0.50): +4.87% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 5.71% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged +0.41% a year (all months +5.51%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 5.39% (confidence 0.40): Equilibrium excess return +1.36% at a 9.2% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to real_assets
- **implied_erp_cape** unavailable: not applicable to real_assets
- **survey_consensus** unavailable: not applicable to real_assets
- **yield_building_block** unavailable: not applicable to real_assets
- **auto_blend** 6.84% (confidence 0.44): Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%.

### commodities

- **historical_erp** 6.54% (confidence 0.50): +2.51% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 4.24% (confidence 0.40): After the 180 past months labelled expansion, excess returns over the next 3 years averaged -0.43% a year (all months +2.12%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 5.87% (confidence 0.40): Equilibrium excess return +1.84% at a 0.1% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to real_assets
- **implied_erp_cape** unavailable: not applicable to real_assets
- **survey_consensus** unavailable: not applicable to real_assets
- **yield_building_block** unavailable: not applicable to real_assets
- **auto_blend** 5.63% (confidence 0.44): Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%.

### cash

- **historical_erp** 3.93% (confidence 0.30): -0.10% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield.
- **regime_adjusted** 3.92% (confidence 0.25): After the 180 past months labelled expansion, excess returns over the next 3 years averaged -0.11% a year (all months -0.10%); credibility weight 0.75, plus 4.03% T-bill.
- **bl_equilibrium** 4.03% (confidence 0.40): Equilibrium excess return +0.00% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size.
- **inverse_gordon** unavailable: not applicable to cash
- **implied_erp_cape** unavailable: not applicable to cash
- **survey_consensus** 3.00% (confidence 0.50): SPF median BILL10 3.00% a year over 10 years + 0.00% variance add-back.
- **yield_building_block** 4.03% (confidence 0.80): 4.03% starting yield - 0.00% expected credit loss + 0.00% variance add-back (mean of DTB3).
- **auto_blend** 3.78% (confidence 0.53): Confidence-weighted average of 5 methods: historical_erp 13%, regime_adjusted 11%, bl_equilibrium 18%, survey_consensus 22%, yield_building_block 36%.

Method definitions and caveats: `src/saa/skills/cma_methods/SKILL.md`.
