"""Command line: import one or more batch files through the pipeline.

    python import_batch.py example_batches/D2_STDp_R1.csv
    python import_batch.py my_run.csv --refit-mech        # also refit the mechanistic parameters
    python import_batch.py --init                         # (re)build store + registry version 1.0 from v0.8
    python import_batch.py --report                       # print the current model report card
"""
import sys, json, argparse
from dtwin import pipeline as pl

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="*"); ap.add_argument("--refit-mech", action="store_true")
ap.add_argument("--init", action="store_true"); ap.add_argument("--report", action="store_true")
a = ap.parse_args()
if a.init:
    pl.init_store(); rep = pl.init_registry()
    print("store + registry initialised; model 1.0 benchmark titer error", round(rep["benchmark_all"]["titer_MAPE_%"], 2), "%")
for f in a.files:
    print(f"importing {f}")
    r = pl.import_batch(f, refit_mechanistic=a.refit_mech)
    if r["status"] == "rejected":
        print("  REJECTED:", "; ".join(r["errors"]))
if a.report or a.files:
    v = pl.champion(); rep = pl.load_version(v)["report"]
    print(f"\ncurrent model {v}: benchmark titer {rep['benchmark_all']['titer_MAPE_%']:.2f}%  VCD {rep['benchmark_all']['VCD_MAPE_%']:.2f}%  "
          f"coverage {sum(rep['band_coverage'].values()) / 5:.1f}%  checks {sum(d['ok'] for d in rep['direction_checks'])}/6")
