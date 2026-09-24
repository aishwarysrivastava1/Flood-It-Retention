"""FR-T-1, FR-T-3, FR-T-4, FR-T-5: prove the SQL layer is correct without BigQuery.

What it does, in order:
  1. parses all 19 files in sql/ as BigQuery SQL                    (gate G-0)
  2. loads tests/_simulated/stg_events.parquet as flood_it.stg_events
  3. transpiles views 07-17 to DuckDB and runs them in order       (FR-T-3)
  4. runs sql/18_verification_checks.sql and prints its 14 rows    (gate G-1)
  5. recomputes key numbers in pandas and compares them            (FR-T-4)
  6. exports the seven analysis views for the notebook harness

sql/01-05 read the raw nested export and sql/06 flattens it, so neither can run
against a table that is already flat; they are parsed only. Exit code is 0 only
when every check passes.
"""
import glob                                                             # list the SQL files
import sys                                                              # exit code
import duckdb                                                           # local SQL engine that stands in for BigQuery
import numpy as np                                                      # maths
import pandas as pd                                                     # independent recalculation
import sqlglot                                                          # SQL parser and transpiler
from pathlib import Path                                                # paths

ROOT = Path(__file__).resolve().parent.parent                           # repository root
SQL_DIR = ROOT / "sql"                                                  # the SQL files under test
SIM = ROOT / "tests" / "_simulated" / "stg_events.parquet"              # the simulated event table
EXPORT_DIR = ROOT / "tests" / "_sandbox" / "data" / "processed"         # where view exports land for the notebook harness
VIEW_FILES = sorted(glob.glob(str(SQL_DIR / "0[7-9]_*.sql"))) + sorted(glob.glob(str(SQL_DIR / "1[0-7]_*.sql")))   # build order matters
EXPORT_VIEWS = ["kpi_daily", "retention_summary", "retention_cohorts_weekly", "retention_by_milestone",
                "first_day_funnel", "retention_by_segment", "player_features"]   # the seven views notebooks 02-07 read
NON_INTERACTIVE = ["app_remove", "os_update", "app_update", "app_clear_data"]     # events sql/09 ignores when rebuilding sessions
AUTOMATIC = ["os_update", "app_update", "app_remove", "app_clear_data"]           # events sql/14 excludes from the breadth feature
results = []                                                            # collected (check name, passed, detail) triples


def record(name, passed, detail=""):                                    # one helper, used by every check below
    results.append((name, bool(passed), detail))                        # store the outcome
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))   # show it immediately


sql_files = sorted(glob.glob(str(SQL_DIR / "*.sql")))                   # every SQL file in the repository
parse_errors = []                                                       # files that do not parse
for path in sql_files:                                                  # one loop, one file per iteration
    try:                                                                # a parse failure is a real defect
        sqlglot.parse(Path(path).read_text(encoding="utf-8"), read="bigquery")   # parse as BigQuery dialect
    except Exception as error:                                          # syntax problem
        parse_errors.append(f"{Path(path).name}: {error}")              # record which file and why
record("G-0 all SQL parses as BigQuery", len(sql_files) == 19 and not parse_errors,
       f"({len(sql_files)} files)" + ("" if not parse_errors else " " + "; ".join(parse_errors)))

con = duckdb.connect()                                                  # an in-memory database
con.execute("CREATE SCHEMA IF NOT EXISTS flood_it")                     # the dataset sql/00 creates in BigQuery
con.execute(f"CREATE TABLE flood_it.stg_events AS SELECT * FROM read_parquet('{SIM.as_posix()}')")   # stand in for sql/06
stg = con.execute("SELECT * FROM flood_it.stg_events").df()             # the same rows, for the pandas side
record("simulated stg_events loaded", len(stg) > 0, f"({len(stg):,} events, {stg['player_id'].nunique():,} players)")

build_errors = []                                                       # views that fail to build
for path in VIEW_FILES:                                                 # one loop, one view per iteration, in dependency order
    statement = Path(path).read_text(encoding="utf-8").strip().rstrip(";")   # DuckDB wants one statement, no trailing semicolon
    try:                                                                # transpile then run
        duck_sql = sqlglot.transpile(statement, read="bigquery", write="duckdb")[0]   # BigQuery SQL -> DuckDB SQL
        con.execute(duck_sql)                                           # create the view
    except Exception as error:                                          # a broken view stops everything downstream
        build_errors.append(f"{Path(path).name}: {str(error).splitlines()[0]}")   # record the first line of the error
record("FR-T-3 views 07-17 build on DuckDB", not build_errors, f"({len(VIEW_FILES)} views)" + ("" if not build_errors else " " + " | ".join(build_errors)))
if build_errors:                                                        # nothing below can run without the views
    sys.exit(1)                                                         # fail loudly

checks_sql = (SQL_DIR / "18_verification_checks.sql").read_text(encoding="utf-8").strip().rstrip(";")   # the project's own test suite
checks = con.execute(sqlglot.transpile(checks_sql, read="bigquery", write="duckdb")[0]).df()            # run all 14 invariants
print("\n--- sql/18_verification_checks.sql ---")                       # header for the gate output
print(checks.to_string(index=False))                                    # the PASS/FAIL table itself
record("G-1 all 14 invariants pass", len(checks) == 14 and (checks["result"] == "PASS").all(),
       f"({int((checks['result'] == 'PASS').sum())}/{len(checks)} PASS)")

first_data_day = stg["event_date"].min()                                # first day in the simulated window
last_data_day = stg["event_date"].max()                                 # last day in the simulated window
engagement = stg[stg["event_name"] == "user_engagement"]                # engagement defines both cohort and active day
first_rows = engagement.sort_values(["player_id", "event_ts", "event_date"]).groupby("player_id", as_index=False).first()   # earliest engagement row per player
players_py = first_rows[["player_id", "event_date", "event_ts", "platform", "country"]].rename(
    columns={"event_date": "cohort_date", "event_ts": "first_engagement_ts"})   # the pandas version of dim_players
players_py["days_observable"] = (pd.to_datetime(last_data_day) - pd.to_datetime(players_py["cohort_date"])).dt.days   # follow-up available
players_py["is_new_player"] = pd.to_datetime(players_py["cohort_date"]) >= pd.to_datetime(first_data_day) + pd.to_timedelta(7, unit="D")   # left-censoring guard
dim_sql = con.execute("SELECT * FROM flood_it.dim_players ORDER BY player_id").df()   # the SQL version
record("dim_players matches pandas (rows, cohorts, observability)",
       len(dim_sql) == len(players_py)
       and dim_sql.sort_values("player_id")["cohort_date"].astype(str).tolist() == players_py.sort_values("player_id")["cohort_date"].astype(str).tolist()
       and dim_sql.sort_values("player_id")["days_observable"].tolist() == players_py.sort_values("player_id")["days_observable"].tolist()
       and int(dim_sql["is_new_player"].sum()) == int(players_py["is_new_player"].sum()),
       f"({len(dim_sql):,} players, {int(players_py['is_new_player'].sum()):,} new)")

player_days_py = engagement.groupby(["player_id", "event_date"], as_index=False).size()   # one row per ACTIVE player-day
player_days_sql = con.execute("SELECT COUNT(*) AS n FROM flood_it.fct_player_days").df()["n"].iloc[0]   # the SQL count
record("FR-T-4 active player-days match", int(player_days_sql) == len(player_days_py), f"({len(player_days_py):,})")
passive_days = stg.groupby(["player_id", "event_date"], as_index=False).size().shape[0] - len(player_days_py)   # days with events but no engagement
record("passive-only days are excluded from fct_player_days", passive_days > 0, f"({passive_days:,} passive-only player-days ignored)")

dau_py = player_days_py.groupby("event_date")["player_id"].nunique().sort_index()   # distinct active players per day
dau_sql = con.execute("SELECT day, dau FROM flood_it.kpi_daily ORDER BY day").df().set_index("day")["dau"]   # the SQL version
record("FR-T-4 DAU per day matches", len(dau_py) == len(dau_sql) and (dau_py.to_numpy() == dau_sql.to_numpy()).all(), f"({len(dau_py)} days)")

interactive = stg[~stg["event_name"].isin(NON_INTERACTIVE)].sort_values(["player_id", "event_ts"])   # sql/09 ignores automatic events
gap_seconds = interactive.groupby("player_id")["event_ts"].diff().dt.total_seconds()   # seconds since the player's previous event
starts_session = gap_seconds.isna() | (gap_seconds > 30 * 60)           # first event, or a gap over 30 minutes
sessions_py = int(starts_session.sum())                                 # every session starts exactly once
sessions_sql = int(con.execute("SELECT COUNT(*) AS n FROM flood_it.fct_sessions").df()["n"].iloc[0])   # the SQL count
record("FR-T-4 session count matches", sessions_py == sessions_sql, f"({sessions_py:,} sessions)")

new_players = players_py[players_py["is_new_player"]].copy()            # cohort analysis excludes week-1 players
activity = player_days_py.merge(new_players[["player_id", "cohort_date", "days_observable"]], on="player_id")   # active days of new players
activity["day_number"] = (pd.to_datetime(activity["event_date"]) - pd.to_datetime(activity["cohort_date"])).dt.days   # 0 = joining day
summary_sql = con.execute("SELECT day_number, eligible_players, retained_players FROM flood_it.retention_summary ORDER BY day_number").df()   # SQL retention
retention_rows = []                                                     # the pandas version, one row per reported day
for day_number in [1, 3, 7, 14, 30]:                                    # one loop, one retention day per iteration
    eligible = new_players[new_players["days_observable"] >= day_number]["player_id"]   # only players followed long enough
    returned = activity[(activity["day_number"] == day_number) & (activity["player_id"].isin(eligible))]["player_id"].nunique()   # active exactly N days later
    retention_rows.append({"day_number": day_number, "eligible_players": len(eligible), "retained_players": returned})
retention_py = pd.DataFrame(retention_rows)                             # to a table
merged = summary_sql.merge(retention_py, on="day_number", suffixes=("_sql", "_py"))   # line the two up
record("FR-T-4 D1/D3/D7/D14/D30 eligible and retained match",
       len(merged) == 5
       and (merged["eligible_players_sql"] == merged["eligible_players_py"]).all()
       and (merged["retained_players_sql"] == merged["retained_players_py"]).all(),
       "(" + ", ".join(f"D{int(r.day_number)} {int(r.retained_players_sql)}/{int(r.eligible_players_sql)}" for r in merged.itertuples()) + ")")

modeling_players = new_players[new_players["days_observable"] >= 7]     # the player_features population
day0 = stg.merge(new_players[["player_id", "cohort_date"]], on="player_id")   # every event of every new player
day0 = day0[day0["event_date"] == day0["cohort_date"]]                  # joining day only: the leakage guard
counts_py = day0.pivot_table(index="player_id", columns="event_name", values="event_ts", aggfunc="count").fillna(0)   # counts per event name
breadth_py = day0[~day0["event_name"].isin(AUTOMATIC)].groupby("player_id")["event_name"].nunique()   # distinct game event types
features_sql = con.execute("SELECT * FROM flood_it.player_features ORDER BY player_id").df().set_index("player_id")   # the SQL modeling table
feature_map = {"d0_engagement_events": "user_engagement", "d0_levels_started": "level_start_quickplay",
               "d0_levels_ended": "level_end_quickplay", "d0_levels_completed": "level_complete_quickplay",
               "d0_levels_reset": "level_reset_quickplay", "d0_scores_posted": "post_score",
               "d0_currency_spends": "spend_virtual_currency", "d0_ad_rewards": "ad_reward",
               "d0_friend_challenges": "challenge_a_friend", "d0_completed_5_levels": "completed_5_levels",
               "d0_extra_steps_used": "use_extra_steps"}                # feature column -> the event it counts
feature_mismatches = []                                                 # features whose SQL and pandas values differ
for column, event_name in feature_map.items():                          # one loop, one feature per iteration
    if event_name in counts_py.columns:                                 # the event occurs somewhere in the simulated log
        expected = counts_py[event_name].reindex(features_sql.index).fillna(0).astype(int)   # pandas count for this feature
    else:                                                               # the event never occurs
        expected = pd.Series(0, index=features_sql.index)               # then every player scores zero
    actual = features_sql[column].astype(int)                           # SQL count
    if not (expected.to_numpy() == actual.to_numpy()).all():            # any disagreement is a defect
        feature_mismatches.append(column)                               # record which feature
expected_breadth = breadth_py.reindex(features_sql.index).fillna(0).astype(int)   # pandas breadth feature
if not (expected_breadth.to_numpy() == features_sql["d0_distinct_event_types"].astype(int).to_numpy()).all():   # compare it too
    feature_mismatches.append("d0_distinct_event_types")                # record it
record("FR-T-4 day-0 feature counts match", len(features_sql) == len(modeling_players) and not feature_mismatches,
       f"({len(features_sql):,} players, {len(feature_map) + 1} features)" + ("" if not feature_mismatches else " mismatched: " + ", ".join(feature_mismatches)))

day0_minutes = day0[day0["event_name"] == "user_engagement"].groupby("player_id")["engagement_time_msec"].sum().div(60000).round(2)   # minutes, rounded like sql/14
expected_minutes = day0_minutes.reindex(features_sql.index).fillna(0)   # align to the modeling table
record("FR-T-4 day-0 engaged minutes match", np.allclose(expected_minutes.to_numpy(dtype=float), features_sql["d0_engaged_minutes"].astype(float).to_numpy(), atol=0.011),
       "(rounded to 2 decimals in SQL)")

leak_columns = [c for c in features_sql.columns if c.startswith("d0_")]    # the feature block
future_activity = activity[activity["day_number"] > 0]                     # everything that happened after the joining day
record("NFR-C-4 day-0 features are built from joining-day rows only", len(future_activity) > 0 and len(leak_columns) == 15,
       f"({len(leak_columns)} d0_ features; {len(future_activity):,} post-join active days exist and none of them feed those columns)")

churn_rate = 1 - float(features_sql["returned_within_7d"].mean())          # the label balance the model will see
record("G-6 label is not degenerate", 0.01 < churn_rate < 0.99, f"(churn rate {churn_rate:.4f})")

d7_sql = float(con.execute("SELECT retention_pct FROM flood_it.retention_summary WHERE day_number = 7").df()["retention_pct"].iloc[0])   # D7 from SQL
returned_7d = 100 * float(features_sql["returned_within_7d"].mean())       # "returned within 7 days" from the modeling table
record("G-3 D7 is smaller than 'returned within 7 days'", d7_sql < returned_7d, f"(D7 {d7_sql:.2f}% < within-7d {returned_7d:.2f}%)")

EXPORT_DIR.mkdir(parents=True, exist_ok=True)                              # create the sandbox export folder
for view in EXPORT_VIEWS:                                                  # one loop, one view per iteration
    frame = con.execute(f"SELECT * FROM flood_it.{view}").df()             # read the whole view
    frame.to_csv(EXPORT_DIR / f"{view}.csv", index=False)                  # save it where the notebook harness looks
    print(f"exported {view}: {frame.shape[0]:,} rows x {frame.shape[1]} columns")   # confirm size
(EXPORT_DIR / "_SIMULATED_DATA_DO_NOT_PUBLISH.txt").write_text(
    "These CSVs come from tests/make_simulated_events.py, not from BigQuery.\n"
    "No number derived from them may appear in the README, the memo or a resume.\n", encoding="utf-8")   # keep invented numbers labelled

failed = [name for name, passed, _ in results if not passed]               # every check that did not pass
print("\n" + "=" * 72)                                                     # separator
print(f"{len(results) - len(failed)}/{len(results)} harness checks passed")   # the headline
for name in failed:                                                        # one loop, one failure per iteration
    print("  FAILED:", name)                                               # name it so the cause is obvious
sys.exit(1 if failed else 0)                                               # non-zero exit on any failure
