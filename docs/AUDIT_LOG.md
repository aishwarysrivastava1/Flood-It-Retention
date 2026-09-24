# Audit Log

A record of issues found during a full review of this project, and what changed.
Keeping this in the repo is deliberate: it shows the work was checked, not just written.

## Corrections applied

| # | Issue | Why it mattered | Fix |
|---|---|---|---|
| 1 | Session gaps were measured with `TIMESTAMP_DIFF(..., MINUTE)`, which truncates | A 30.9-minute gap counted as 30, so two sessions were merged into one | Measure in seconds and compare against `30 * 60` (`sql/09`) |
| 2 | `cohort_date` came from `MIN(event_date)` while `first_engagement_ts` came from `MIN(event_ts)` | Those are different aggregations over different columns; near midnight, the date and the timestamp could come from different events | Both are now taken from the same first-engagement row, selected with `ROW_NUMBER` (`sql/07`) |
| 3 | `sessions_per_dau` divided all sessions by DAU | Sessions could exist on days that were not "active" (interactive events but no `user_engagement`), so numerator and denominator used different populations | Sessions are now joined to `fct_player_days` before counting (`sql/10`) |
| 4 | `d0_distinct_event_types` counted automatic events | `os_update` or `app_remove` inflated a feature that is supposed to measure how much of the *game* a player touched | Automatic events are excluded from the distinct count (`sql/14`) |
| 5 | The milestone chart rebuilt player counts from rounded percentages | Reversing a rounded percentage introduces small errors into the chi-square test and the confidence intervals | The view now returns raw counts, and the notebook uses them (`sql/15`, `notebooks/02`) |
| 6 | Top-10 countries were selected with `RANK()` | Ties would return more than 10 named countries and change the segment table's shape | `ROW_NUMBER()` with a deterministic tie-break (`sql/17`) |
| 7 | No single command proved the data layer was consistent | Sanity checks were scattered through the guide, so they were easy to skip | Added `sql/18_verification_checks.sql`: 14 invariants that must all report PASS |
| 8 | The churn model reported no PR-AUC baseline | "PR-AUC 0.62" means nothing without knowing the churn rate it must beat | The notebook now prints both baselines (`notebooks/05`) |
| 9 | The verification described in this log could not be re-run by anyone else: the simulated dataset and the harness lived outside the repository | "It was checked once" is not "it is checked on every change", and a reviewer could reproduce none of it | Added `tests/` (IMP-1): `make_simulated_events.py` plants an outage, passive-only days, duplicates and placeholder countries; `run_views_duckdb.py` parses all 19 files, builds views 07-17 on DuckDB, runs `sql/18` and cross-checks against pandas; `run_notebooks.py` executes notebooks 02-07 in a fresh kernel |
| 10 | This log claimed "all seven notebooks run end to end" | Notebook 01 is the only one that queries BigQuery, so no offline harness can execute it; the claim overstated what had been verified | Corrected below: six notebooks are executed automatically, notebook 01 is verified only by a live run |

## Verified, no change needed
Re-runnable with the three commands in `docs/RUNBOOK.md` ("Verify without BigQuery"); the figures below
come from the most recent harness run on the seeded simulated log, not from the live dataset.

- All 19 SQL files parse as valid BigQuery SQL (`sqlglot`, BigQuery dialect).
- Views 07-17 build and run in dependency order after transpilation to DuckDB.
- Retention counts, DAU, session rebuilding, cohort eligibility and day-0 features match an independent
  pandas calculation on a simulated dataset with a known structure: 15 of 15 harness checks pass.
- All 14 invariants in `sql/18` pass on that dataset.
- Notebooks 02-07 run end to end in a fresh kernel and produce all 22 charts and all 8 derived CSVs.
  Notebook 01 cannot be included: it is the only notebook that queries BigQuery.
- On the simulated data the model gates hold: dummy ROC-AUC 0.500, tuned test ROC-AUC inside
  (0.55, 0.95), test PR-AUC above the test churn rate, and the train-test gap reported for every model.
- Every view referenced by a notebook is created by a SQL file, and every CSV read by a notebook is
  exported by notebook 01.

## Known limitations that are deliberate, not bugs
- **Views, not tables.** They cost no storage and always reflect the source; the trade-off is that each read
  re-runs the query.
- **The 30-minute session rule** is a convention, not a measurement.
- **`first_seen_players` in `kpi_daily`** includes week-1 players, unlike the cohort analysis. They answer
  different questions and are named differently on purpose.
- **Funnel step 3** requires both a recorded start and a completion, so lost start events push players down
  one step rather than creating an impossible funnel.
- **Simulated-data verification** proves the logic, not the findings. The real numbers come from BigQuery.
