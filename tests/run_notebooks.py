"""FR-T-6 and gate G-5: execute notebooks 02-07 end to end against the simulated exports.

Notebooks are copied into tests/_sandbox/notebooks and executed there, so the
repository's own reports/figures and data/processed folders stay untouched: a
chart drawn from invented data must never sit where a reviewer would read it as
a finding. Notebook 01 is skipped because it is the only notebook that talks to
BigQuery, which a coding agent cannot reach.

Run tests/run_views_duckdb.py first; it writes the CSVs this harness feeds in.
"""
import os                                                               # set the chart backend before the kernel starts
import shutil                                                           # copy notebooks into the sandbox
import sys                                                              # exit code
import time                                                             # measure how long each notebook takes
import nbformat                                                         # read and write notebook files
from nbclient import NotebookClient                                     # execute a notebook like "Restart Kernel and Run All"
from pathlib import Path                                                # paths

ROOT = Path(__file__).resolve().parent.parent                           # repository root
SANDBOX = ROOT / "tests" / "_sandbox"                                   # isolated copy of the project tree
NOTEBOOKS = ["02_kpis_retention.ipynb", "03_player_eda_tests.ipynb", "04_survival.ipynb",
             "05_churn_model.ipynb", "06_segmentation.ipynb", "07_anomaly_forecast.ipynb"]   # every notebook that reads CSVs
EXPECTED_FIGURES = ["01_dau_stickiness.png", "02_retention_curve.png", "03_cohort_heatmap.png",
                    "04_first_day_funnel.png", "05_retention_by_milestone.png", "06_retention_by_country.png",
                    "07_features_by_churn.png", "08_spearman_correlations.png", "09_completion_rate_vs_return.png",
                    "10_km_overall.png", "11_km_platform.png", "12_km_milestone.png",
                    "13_roc_pr_curves.png", "14_calibration.png", "15_permutation_importance.png",
                    "16_choose_k.png", "17_segment_retention.png", "18_segments_pca.png",
                    "19_stl_decomposition.png", "20_dau_anomalies.png", "21_forecast_backtest.png",
                    "22_dau_forecast.png"]                              # the 22 charts SC-4 requires
EXPECTED_CSVS = ["feature_tests.csv", "model_comparison.csv", "permutation_importance.csv", "test_predictions.csv",
                 "player_segments.csv", "segment_profiles.csv", "dau_forecast.csv", "dau_anomalies.csv"]   # the 8 derived CSVs

os.environ["MPLBACKEND"] = "Agg"                                        # draw charts to files, never to a window
data_dir = SANDBOX / "data" / "processed"                               # where run_views_duckdb.py put the exports
if not (data_dir / "player_features.csv").exists():                     # the harness order matters
    print("MISSING INPUT: run tests/run_views_duckdb.py first")         # say exactly what to do
    sys.exit(1)                                                         # stop here
figures_dir = SANDBOX / "reports" / "figures"                           # sandbox chart folder
if figures_dir.exists():                                                # clear old charts so the count means something
    shutil.rmtree(figures_dir)                                          # remove the folder
figures_dir.mkdir(parents=True, exist_ok=True)                          # recreate it empty
sandbox_notebooks = SANDBOX / "notebooks"                               # sandbox notebook folder
sandbox_notebooks.mkdir(parents=True, exist_ok=True)                    # create it if needed

failures = []                                                           # notebooks that raised
for name in NOTEBOOKS:                                                  # one loop, one notebook per iteration
    source = ROOT / "notebooks" / name                                  # the notebook in the repository
    target = sandbox_notebooks / name                                   # its sandbox copy
    shutil.copyfile(source, target)                                     # copy it verbatim, so the repository file is what is tested
    notebook = nbformat.read(target, as_version=4)                      # parse it
    client = NotebookClient(notebook, timeout=1800, kernel_name="python3",
                            resources={"metadata": {"path": str(sandbox_notebooks)}})   # fresh kernel, sandbox working folder
    started = time.time()                                               # start the clock
    try:                                                                # a raised cell is a failure
        client.execute()                                                # run every cell top to bottom
        print(f"PASS  {name}  ({time.time() - started:.0f}s)")           # how long it took
    except Exception as error:                                          # capture the failing cell
        failures.append(f"{name}: {str(error).strip().splitlines()[-1]}")   # keep the last line of the traceback
        print(f"FAIL  {name}  ({time.time() - started:.0f}s)  {str(error).strip().splitlines()[-1]}")
    nbformat.write(notebook, target)                                    # keep the executed copy for inspection

produced = sorted(path.name for path in figures_dir.glob("*.png"))      # charts the run actually created
missing_figures = [name for name in EXPECTED_FIGURES if name not in produced]   # charts that never appeared
extra_figures = [name for name in produced if name not in EXPECTED_FIGURES]     # charts nobody asked for
missing_csvs = [name for name in EXPECTED_CSVS if not (data_dir / name).exists()]   # derived tables that never appeared
print("\n" + "=" * 72)                                                  # separator
print(f"notebooks executed: {len(NOTEBOOKS) - len(failures)}/{len(NOTEBOOKS)} (01 skipped: it is the only notebook that needs BigQuery)")
print(f"charts produced:    {len(produced)}/{len(EXPECTED_FIGURES)}" + (f"  missing: {missing_figures}" if missing_figures else ""))
print(f"derived CSVs:       {len(EXPECTED_CSVS) - len(missing_csvs)}/{len(EXPECTED_CSVS)}" + (f"  missing: {missing_csvs}" if missing_csvs else ""))
for failure in failures:                                                # one loop, one failure per iteration
    print("  FAILED:", failure)                                         # name it
if extra_figures:                                                       # unexpected files are worth knowing about
    print("  unexpected charts:", extra_figures)                        # list them
ok = not failures and not missing_figures and not missing_csvs          # every condition must hold
print("all notebook checks passed" if ok else "notebook harness FAILED")   # the headline
sys.exit(0 if ok else 1)                                                # non-zero exit on any failure
