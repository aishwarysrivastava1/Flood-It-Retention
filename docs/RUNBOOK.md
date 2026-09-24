# Runbook

The order to do things in, what each step costs, and what to commit. Follow it top to bottom the first time.

## One-time setup (about 2 hours)
1. Create a Google Cloud project; confirm the **Sandbox** badge in BigQuery. No credit card.
2. Note your **project ID** (not the display name).
3. Clone the repo, create the virtual environment, `pip install -r requirements.txt`.
4. Put your project ID in `notebooks/01_extract_from_bigquery.ipynb`, cell 2.
5. Commit: `Set up project structure, environment and gitignore`.

## Build the data layer (about 3 hours, mostly reading output)
| Step | What | Where | Cost note |
|---|---|---|---|
| 1 | Run `sql/01`-`05` one at a time, read every result | BigQuery console | These scan the full event table; the most expensive step |
| 2 | Record the numbers from `04_data_quality.sql` for your README | — | Free |
| 3 | Run `sql/00_create_dataset.sql` once | BigQuery console | Free |
| 4 | Run notebook 01 cells 1-5 (creates all views) | Jupyter | Views store nothing |
| 5 | Run `sql/18_verification_checks.sql`; every row must say PASS | BigQuery console | Cheap |
| 6 | Run notebook 01 cell 6 (exports 7 CSVs) | Jupyter | One scan per view |

**If any check fails, stop and fix it before analysing.** A failing check means a number later in the project is wrong.

## Verify without BigQuery (about 2 minutes, free)
The harness in `tests/` proves the SQL and the notebooks are correct on a simulated event log, so a
change can be checked before spending any query allowance, and by anyone without cloud access.

```bash
pip install -r tests/requirements-test.txt   # sqlglot, duckdb, nbclient, nbformat
python tests/make_simulated_events.py        # writes tests/_simulated/stg_events.parquet (seed 42)
python tests/run_views_duckdb.py             # G-0 parse, views 07-17 on DuckDB, sql/18, pandas cross-checks
python tests/run_notebooks.py                # runs notebooks 02-07 in a fresh kernel, counts the 22 charts
```

Both runners exit non-zero on failure. Everything they write lands in `tests/_simulated/` and
`tests/_sandbox/`, which are git-ignored: **no number from the simulated data may reach the README, the
memo or a resume.** The harness cannot check notebook 01, the only notebook that talks to BigQuery.

## Analyse (about 18 hours across several sittings)
Run in order; each notebook reads the CSVs, so none of them costs BigQuery credit.

| Notebook | Produces | Commit message |
|---|---|---|
| 02 | KPI overview, retention curve, cohort heatmap, funnel, segment comparisons (6 charts) | `Add KPI, retention, cohort and funnel analysis` |
| 03 | Feature distributions, rank-based tests with effect sizes, correlations (3 charts) | `Add player-level EDA and statistical testing` |
| 04 | Kaplan-Meier curves, log-rank tests, Cox model (3 charts) | `Add survival analysis` |
| 05 | Model comparison, ROC/PR curves, calibration, lift, importance (3 charts) | `Add churn model with out-of-time validation` |
| 06 | Cluster selection, segment profiles, stability, PCA view (3 charts) | `Add player segmentation with stability check` |
| 07 | STL decomposition, anomalies, backtest, forecast (4 charts) | `Add anomaly detection and forecasting` |

## Deliver (about 6 hours)
1. Build the Looker Studio dashboard; share as **Anyone with the link · Viewer**; paste the link into
   `dashboard/looker_studio_notes.md` and the README.
2. Write `reports/decision_memo.md` in your own words.
3. Fill in the README placeholders with your real findings.
4. Re-run every notebook after a kernel restart, save with outputs, and commit.

## If you come back after a break
BigQuery sandbox objects expire after **60 days**. If your views are gone, re-run notebook 01 cells 4-6
and everything is rebuilt in a few minutes. Your SQL files are the real artifact, not the views.

## Cost control habits
- Read the byte estimate before running anything.
- While developing, add `WHERE _TABLE_SUFFIX BETWEEN '20180701' AND '20180707'` to work on one week.
- Never `SELECT *` on the raw table without a `LIMIT`.
- Export once, iterate in pandas.
- Leave Looker Studio auto-refresh off.
