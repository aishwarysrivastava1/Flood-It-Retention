# Flood-It! Player Retention and Churn Analysis

> Starter repository. Replace every [bracketed] placeholder with your own findings
> once you have run the analysis. See the masterplan guide, Phase 13.

**Live dashboard:** [your Looker Studio link]
**Decision memo:** [reports/decision_memo.md](reports/decision_memo.md)

End-to-end analysis of ~5.7 million raw Google Analytics 4 events from a real mobile
game: BigQuery data modeling, retention and cohort analysis, survival analysis,
churn prediction, segmentation, anomaly detection and forecasting.

## Headline findings
- [Retention finding with confidence interval]
- [Biggest funnel drop-off]
- [Model performance vs baseline, plus lift in the riskiest decile]
- [Anomaly and your diagnosis]

## Data
Public BigQuery dataset `firebase-public-project.analytics_153293282` (Flood-It!,
114 days, ~15K players, ~5.7M events). No download needed; queried in place using
the free BigQuery sandbox.

## How it works
| Layer | Files | What it does |
|---|---|---|
| Exploration | `sql/01`-`05` | Event dictionary, nested parameter discovery, data quality |
| Staging | `sql/06` | One flat, typed, readable row per event |
| Dimensions and facts | `sql/07`-`09` | Players with cohorts, player-days, rebuilt sessions |
| Metrics | `sql/10`-`13`, `15`-`17` | DAU/WAU/MAU, retention, cohorts, funnel, segments |
| Modeling table | `sql/14` | Day-0 features + days 1-7 label, leakage-guarded |
| Analysis | `notebooks/02`-`07` | Statistics, survival analysis, ML, time series |

## Documentation
| File | What it holds |
|---|---|
| [docs/ANALYSIS_PLAN.md](docs/ANALYSIS_PLAN.md) | Definitions and modeling rules, fixed before analysing |
| [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) | Every view, grain and column, plus columns banned as features |
| [docs/METRIC_DEFINITIONS.md](docs/METRIC_DEFINITIONS.md) | Each metric's formula, source and pitfalls |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | What to run, in what order, at what cost |
| [docs/INTERVIEW_PREP.md](docs/INTERVIEW_PREP.md) | 35 questions with answer outlines |
| [docs/AUDIT_LOG.md](docs/AUDIT_LOG.md) | Issues found in review and what changed |

## Verification
`sql/18_verification_checks.sql` runs 14 invariants over the data layer (one row per player,
day-0 cohort retention exactly 100%, funnel step 1 equal to the modeling table size, and more).
Every row must report PASS before any analysis is trusted.

## Key analytical decisions
- **Leakage prevention:** features from the joining day only; label from days 1-7.
- **Out-of-time validation:** trained on earlier cohorts, tested on later ones.
- **Censoring:** first-week players excluded; retention denominators require
  sufficient observation time.
- **Threshold selection:** chosen on out-of-fold training predictions, never on test.
- **Descriptive vs causal:** milestone and segment differences are associations only.

## Limitations
[Your list from the decision memo.]

## Reproduce it
1. Create a Google Cloud project and open the free BigQuery sandbox (no card needed).
2. `pip install -r requirements.txt`
3. Set `PROJECT_ID` in `notebooks/01_extract_from_bigquery.ipynb`.
4. Run notebook 01 (creates all views and exports CSVs), then notebooks 02-07 in order.

## How I used AI tools
[2-4 sentences: what AI helped with and how you verified it.]
