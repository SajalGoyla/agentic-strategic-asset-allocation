# Agentic Strategic Asset Allocation Pipeline
## 12-Week Project Plan

**Proposed by:** Sajal Kumar Goyla and Shambhawi Bhure
**Supervised by:** Prof. Paul Glasserman
**Reference Architecture:** Ang, Azimbayev, and Kim, *"The Self-Driving Portfolio: Agentic Architecture for Institutional Asset Management"* (2026)

---

## 1. Project Overview

We propose to build a scaled-down, reproducible version of the agentic Strategic Asset Allocation (SAA) pipeline described in Ang et al. (2026). Our system will coordinate specialized LLM-based agents across four functional stages — macroeconomic regime classification, Capital Market Assumption (CMA) generation, portfolio construction, and structured multi-agent peer review/voting — all governed by an institutional Investment Policy Statement (IPS). A CIO agent will synthesize the surviving candidate portfolios into a final ensemble recommendation accompanied by a written board memo.

**Our primary deliverable is a fully functional, end-to-end working pipeline** — a modular, reproducible codebase that executes the multi-agent SAA workflow from data ingestion through final portfolio allocation. Getting this pipeline running correctly and reproducibly is the core goal we are committing to, and it is where we plan to spend the majority of our effort across the semester.

Alongside the pipeline, we will also build a lightweight educational visualization layer — a small set of dashboards and reasoning-trace views that make the pipeline's outputs easier to present and explain in a classroom setting. We have scheduled this work for the later part of the project, after the pipeline itself is complete and validated, so that our early effort stays focused on getting the pipeline working correctly.

---

## 2. Scope & Milestones

To keep the project realistically achievable within the semester, we are deliberately narrowing the reference architecture in a few dimensions. We see these as sensible defaults we can expand on if our pipeline is running ahead of schedule — not hard ceilings.

| Dimension | Full Reference Design (Ang et al. 2026) | Our Proposed Scope |
|---|---|---|
| Asset universe | 18 liquid asset classes | Full 18-asset IPS universe retained, since data ingestion is largely automatable |
| Asset-class CMA candidate methods | 6 return-estimation methods + auto-blend + LLM judge | Same 7-candidate framework, applied to all 18 asset classes |
| Portfolio construction (PC) agents | 21 agents across 4 categories + researcher + adversarial diversifier | 10 PC agents to start: 2–3 per category (heuristic, return-optimized, risk-structured, non-traditional) plus the adversarial diversifier and PC-researcher agent. *We plan to extend this to the full 21-agent roster later in the project if our API budget allows — see Section 6.* |
| Peer review structure | 21-agent randomized dual review, 42 reviews | Same protocol (1 intra-category + 1 inter-category review per agent), scaled to 10 agents |
| Meta-agent (self-learning feedback loop) | Fully implemented | Out of scope for this project; we will document it as a future-work extension |
| Educational visualization layer | Not part of reference design | Additive, lightweight, built only after the pipeline is validated end-to-end (Section 7) |

### Milestones

| Milestone | Target Week | Description |
|---|---|---|
| M1 — Data & Macro Layer Complete | Week 3 | Data ingestion pipeline live; macro agent produces a regime classification (JSON + narrative) |
| M2 — CMA Layer Complete | Week 6 | All 18 asset-class agents produce candidate CMAs, auto-blend, and LLM-judge selection; covariance agent operational |
| M3 — Portfolio Construction & Deliberation Complete | Week 9 | 10 PC agents produce candidate portfolios; CRO risk reports, peer review, Borda-count voting, and revision cycle complete; CIO agent produces final ensemble allocation and board memo |
| M4 — Pipeline Validated & Visualization Layer Delivered | Week 12 | Full pipeline reproducible end-to-end and stress-tested; visualization layer and final presentation delivered |

---

## 3. Workload Distribution

Rather than splitting the project into two separate tracks — one of us building the pipeline while the other works on something else — we want to work in parallel on the pipeline itself throughout the semester, so that we are both equally invested in, and equally responsible for, the core deliverable. We will divide the pipeline's agents and stages between us within each phase, pair-review each other's components before integration, and rotate who leads on shared/joint pieces so neither of us is idle while the other works.

### How We Will Split the Pipeline Work, Phase by Phase

| Phase | Sajal's Focus | Shambhawi's Focus | Done Together |
|---|---|---|---|
| Phase 1 (Weeks 1–3) | Data ingestion layer; historical-analysis skill (returns, vol, drawdowns, correlations) | Macro agent (regime scoring and classification); IPS encoding as machine-readable constraints | Repo/environment setup; output-contract (JSON) schema design |
| Phase 2 (Weeks 4–6) | Asset-class CMA agents for all 18 asset classes; covariance agent | CMA-judge skill implementation and rationale generation; heuristic and return-optimized PC agents | Validation of CMA outputs against expected ranges |
| Phase 3 (Weeks 7–9) | Risk-structured and non-traditional PC agents; adversarial diversifier and PC-researcher agents; CRO agent | Peer-review assignment logic and Borda-count voting; CIO agent ensemble-combination logic and board memo generation | Integration of peer critiques into the PC agent revision step; end-to-end pipeline wiring |
| Phase 4 (Weeks 10–12) | Backtesting, stress-testing scenarios, and reproducibility/documentation pass on the full codebase | Lightweight visualization extension (Section 7) and final presentation materials | Final dry-run of the full pipeline; final report |

### Shared Responsibilities Throughout

- Weekly pair check-ins to review each other's agent implementations before integration, so both of us stay fluent across the whole pipeline rather than only our own half
- Joint drafting of the IPS and output schemas, since these govern every downstream component
- Joint integration testing at the end of each phase
- Weekly check-ins with Prof. Glasserman and shared documentation of design decisions
- Joint ownership of the final report and codebase handoff package

---

## 4. 12-Week Phased Timeline

**Investment universe (18 ETFs):** US Large Cap, US Small Cap, US Value, US Growth, International Developed, Emerging Markets *(equities)*; Short-Term Treasuries, Intermediate Treasuries, Long-Term Treasuries, Investment-Grade Corporates, High-Yield Corporates, International Sovereign Bonds, International Corporates, USD Emerging Market Debt *(fixed income)*; REITs, Gold, Commodities, Cash *(real assets/cash)*.

### Phase 1: Data Ingestion, Macro Framework & Baseline Setup (Weeks 1–3)

| Week | Phase | Tasks — Sajal | Tasks — Shambhawi | Joint Deliverables |
|---|---|---|---|---|
| 1 | 1 | Set up repo structure, environment, and API access (FRED, market data provider); draft data-ingestion scripts | Draft IPS structure (universe, objectives, risk budget) with faculty input; research LLM orchestration frameworks | Project charter; finalized IPS v0.1; tool/framework selection memo |
| 2 | 1 | Build historical-analysis skill (returns, vol, drawdowns, correlations); pull and validate 18-asset price histories | Design output-contract schema (JSON conventions) for all agent stages; begin macro agent scaffolding | Shared JSON schema spec; data quality validation report |
| 3 | 1 | Support macro agent with validated historical data feeds; begin historical-analysis integration testing | Build macro agent: regime scoring (growth, inflation, policy, financial conditions) → 4-regime classifier; produce macro-view.json | **M1: Macro & data layer live** |

### Phase 2: Agentic CMA Generation & Portfolio Optimization (Weeks 4–6)

| Week | Phase | Tasks — Sajal | Tasks — Shambhawi | Joint Deliverables |
|---|---|---|---|---|
| 4 | 2 | Implement asset-class agent template (6 CMA methods + auto-blend) for 3–4 pilot asset classes | Implement CMA-judge skill (candidate evaluation logic and rationale generation) against the pilot asset classes | Reviewed CMA-judge skill spec; pilot CMA outputs |
| 5 | 2 | Extend asset-class agents to full 18-asset universe; implement covariance agent | Begin heuristic-category PC agents (equal weight, inverse volatility, inverse variance) | Mid-project check-in with faculty; CMA outputs for all 18 asset classes |
| 6 | 2 | Implement risk-structured PC agents (risk parity, hierarchical risk parity) and non-traditional PC agents | Finish return-optimized PC agents (max Sharpe, Black–Litterman); implement PC-researcher and adversarial diversifier agents | **M2: CMA layer complete**; candidate portfolios generated from all 10 PC agents |

### Phase 3: Deliberation Protocol & CIO Ensemble (Weeks 7–9)

| Week | Phase | Tasks — Sajal | Tasks — Shambhawi | Joint Deliverables |
|---|---|---|---|---|
| 7 | 3 | Build CRO agent (risk metrics, IPS compliance checks) for all 10 candidate portfolios | Implement randomized peer-review assignment (intra-/inter-category pairing) and review-prompt templates | CRO risk reports for all candidate portfolios |
| 8 | 3 | Support integration of peer critiques into PC agent revision logic; debug agent-to-agent data flow | Implement Borda-count voting logic and diversity constraint (≥3 of 4 categories in top-5) | Completed peer-review + voting cycle; revised top-5 proposals |
| 9 | 3 | Build CIO agent scoring rubric and ensemble-combination methods | Build CIO agent's board memo generation logic; draft IPS compliance statement language | **M3: Deliberation & CIO ensemble complete**; final allocation + board memo (v1) |

### Phase 4: Stress Testing, Visualization Layer & Final Presentation (Weeks 10–12)

With the pipeline itself complete and validated by the end of Phase 3, Phase 4 covers hardening and proving out the pipeline alongside building the visualization layer described in Section 7.

| Week | Phase | Tasks — Sajal | Tasks — Shambhawi | Joint Deliverables |
|---|---|---|---|---|
| 10 | 4 | Run backtests and stress scenarios (alternate macro regimes, sensitivity checks) on the completed pipeline | Reproducibility pass on the full codebase in parallel (README, run scripts, environment lock files) | Stress-test results memo; fully reproducible pipeline confirmed |
| 11 | 4 | Address any bugs surfaced from stress testing; finalize technical documentation | Build the visualization layer (Section 7) using the pipeline's existing JSON outputs | Full dry-run of end-to-end pipeline |
| 12 | 4 | Final code freeze; prepare technical appendix for final report | Finalize presentation deck and live demo script, incorporating the visualization layer | **M4: Final report, validated codebase, visualization layer, and presentation delivered** |

---

## 5. Data Sources & Technical Resources

### Public / Free / Open-Access Data Sources

| Source | Use | Notes |
|---|---|---|
| **FRED (Federal Reserve Economic Data)** | Macro indicators (growth, inflation, labor market, monetary policy proxies) for the macro agent | Free API with registration key |
| **Yahoo Finance / `yfinance`** | Historical price series for the 18 liquid asset-class ETF proxies (equities, fixed income, real assets, cash) | Free; used for return, volatility, drawdown, and correlation calculations |
| **Kenneth French Data Library** | Factor benchmarks (market, size, value, momentum) for validating CMA/valuation signals | Free, widely used academic dataset |
| **U.S. Treasury / Treasury.gov** | Risk-free rate and yield-curve data for CMA building-block methods | Free |
| **FRED-hosted CPI/PCE series** | Inflation targets and CPI+ objective benchmarking in the IPS | Free |

### Development Tools & Orchestration (core pipeline)

- **Language/runtime:** Python for all computational scripts (data fetching, statistics, optimization), keeping LLM judgment and deterministic computation cleanly separated.
- **Agent orchestration framework:** LangGraph or AutoGen for multi-agent workflow management, state passing between pipeline stages, and structured tool invocation.
- **LLM access:** Anthropic API (Claude models) via the standard `/v1/messages` endpoint, with model routing as described in Section 6.
- **Portfolio optimization libraries:** open-source Python optimization/risk libraries (e.g., `cvxpy`, `scipy.optimize`, `PyPortfolioOpt`) for the 10 PC-agent methods.
- **Version control & reproducibility:** Git repository with environment lock files; run scripts that reproduce a full pipeline execution from a single command.

### Visualization Tooling (Phase 4)

For the visualization layer scheduled in Phase 4, we plan to use a small Streamlit app with Plotly/Dash charts to present pipeline outputs:

- **Streamlit** — lightweight front end for a simple dashboard.
- **Plotly / Dash** — for a capital-flow diagram and macro-regime scorecard.

---

## 6. Cost & Budget Estimation

Our pipeline will be run many times over the course of the project — during development and debugging of individual agents, during phase-level integration testing, and during full end-to-end validation and stress-testing runs. We want our budget to reflect that realistically rather than pricing a single hypothetical run, so we've broken the estimate into (a) cost per full pipeline run, and (b) expected number of runs by phase.

### Model Routing Strategy

| Tier | Used For | Rationale |
|---|---|---|
| **Low-cost, high-throughput models** | Data extraction and formatting, historical-statistics summarization, PC proposal write-ups, routine narrative text | High-volume, low-ambiguity tasks where a smaller/faster model gives sufficient quality at a fraction of the cost |
| **Flagship reasoning models** | Macro regime classification, CMA-judge selections, PC peer-review critiques, Borda-count deliberation synthesis, CIO agent ensemble decisions and board memo generation | Steps where nuanced, well-justified reasoning materially affects the credibility of the output |

### Cost per Full Pipeline Run

| Stage | Approx. Calls | Model Tier | Approx. Cost |
|---|---|---|---|
| Macro agent (data formatting + regime classification) | 2 low-cost + 1 flagship | Mixed | ~$0.25 |
| Asset-class agents (18 classes × narrative + CMA-judge) | 18 low-cost + 18 flagship | Mixed | ~$3.90 |
| Covariance agent | 1 low-cost | Low-cost | ~$0.02 |
| PC agent proposal generation (10 agents) | 10 low-cost | Low-cost | ~$0.15 |
| CRO risk reports (10 portfolios) | 10 low-cost | Low-cost | ~$0.15 |
| Peer review (10 agents × 2 reviews) | 20 flagship | Flagship | ~$4.00 |
| Top-5 revision cycle | 5 flagship | Flagship | ~$1.00 |
| CIO agent (scoring, ensemble selection, board memo) | 3 flagship | Flagship | ~$0.60 |
| **Total per full run** | ~78 calls | — | **~$10** |

*(Per-call costs are approximate planning estimates based on typical short-context vs. long-context reasoning calls; we will confirm exact figures against Anthropic's current published API pricing before finalizing our budget, since rates and models may change.)*

### Estimated Number of Runs by Phase

| Phase | Activity | Estimated Runs / Calls |
|---|---|---|
| Phase 1 (Weeks 1–3) | Unit-level testing of macro agent and data layer (not full runs) | Low-cost dev calls only, ~$10–$15 |
| Phase 2 (Weeks 4–6) | Partial-pipeline runs while building out 18 asset-class agents and 10 PC agents | ~6–8 partial runs, ~$25–$35 |
| Phase 3 (Weeks 7–9) | Full pipeline runs during peer-review, voting, and CIO integration testing | ~8–10 full runs, ~$80–$100 |
| Phase 4 (Weeks 10–12) | Full validation runs, stress-test scenarios (alternate macro regimes), and final demo run(s) | ~6–8 full runs, ~$60–$80 |
| **Contingency buffer (~20%, covers re-runs from bugs and debugging)** | — | ~$35–$50 |

### Total Estimated Budget

**Estimated total project budget: $210–$290** over the 12-week period, based on our proposed 10-agent PC roster. This assumes roughly 15–20 full end-to-end pipeline runs plus ongoing partial/unit-level development calls, which we believe is a realistic reflection of the iteration our project will actually require. We will track actual spend weekly against this budget and can shift more or fewer PC agents into the full 21-agent roster (Section 2) depending on how much budget headroom we have by Phase 3.

**If we were instead to replicate the reference paper's full architecture (21 PC agents rather than 10)**, per-run cost rises mainly through the peer-review stage, since each additional PC agent adds two more review calls (42 reviews total vs. 20) and a larger CIO evaluation pool. We estimate this would put the cost per full run at roughly $15–$20, and — allowing for the additional debugging and integration overhead a larger agent roster typically brings, plus the same ~20–25% contingency buffer — a **total estimated project budget of approximately $450–$650** for a full 21-agent replication. We are not proposing this as our default scope, but flagging it here in case we have budget headroom to expand toward it later in the semester.

---

## 7. Visualization Layer

Alongside the working pipeline, we will build a small, simple set of visualizations on top of the pipeline's existing JSON outputs and natural-language audit trail, to make the results easier to present and explain. This work is scheduled for Phase 4 (Weeks 11–12), once the pipeline itself is complete and validated, and we are keeping it deliberately lightweight so that it builds directly on outputs the pipeline already produces rather than requiring new infrastructure.

### Planned Visualizations

1. **Macro-Regime Scorecard** — the four macro dimensions and the resulting regime classification, with the macro agent's narrative rationale.
2. **Capital-Flow Diagram** — a simple Sankey-style view tracing weight flow from PC agent proposals through voting to the CIO agent's final allocation.
3. **CMA Method-Comparison View** — for each asset class, the candidate method estimates alongside the CMA-judge's final selection and rationale.
4. **Board Memo Viewer** — a readable summary panel of the CIO agent's recommendation, macro rationale, and IPS compliance statement.

### Approach

- Built after M3 (pipeline complete) using the pipeline's existing structured outputs — no new pipeline infrastructure required.
- Streamlit front end with Plotly/Dash charts, chosen for how quickly they can be assembled in the final two weeks.
- Prioritizes clear, simple visuals that support our final presentation and make the pipeline's reasoning easy to follow for a classroom audience.

---

## 8. Reference

Ang, Andrew, Nazym Azimbayev, and Andrey Kim. 2026. *"The Self-Driving Portfolio: Agentic Architecture for Institutional Asset Management."* Working paper, April 1, 2026 draft.
