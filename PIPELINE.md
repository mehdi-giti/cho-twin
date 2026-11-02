# CHO twin platform - batch import pipeline (v1.0)

## Loop for every new batch
1. **Validate**  columns, units (titer must be mg/L, glucose/lactate g/L), ranges, time order. Errors reject the file; warnings flag inputs outside the trained range.
2. **Predict first**  the current model forecasts the batch from day 0 using only its inputs. The error is logged before the batch is used for training (honest out-of-sample test).
3. **Store**  the batch joins the run store as a real training run.
4. **Retrain**  ML rate corrections are re-learned (real runs weighted x5). `--refit-mech` also refits the 26 mechanistic parameters.
5. **Evaluate**  fixed benchmark of 6 real runs that are never trained on (STD, LoG, HiF replicate 1 + all 3 HIP+), band coverage, correction size, 6 direction checks.
6. **Gate**  the candidate replaces the current model only if: titer error not worse by > 1 pt (vs current) and > 1.5 pt (vs best so far), VCD error not worse by > 2 pt, all direction checks pass, band coverage 60-95%, median correction < x1.42, < 25% of corrections at the x0.5/x2 limit.
7. **Publish**  registry/<version>/ (parameters, ML models, band, report) and web/model.json; the page is rebuilt.

## Commands
    python import_batch.py my_run.csv                 # one batch
    python import_batch.py my_run.csv --refit-mech    # also refit mechanistic parameters
    python import_batch.py --report                   # current model report card
    python import_batch.py --init                     # rebuild store + model 1.0 from v0.8
    python retrain_from_platform.py <folder>          # batches saved on the page (exported JSON)

## Batch file
CSV, one row per sample; inputs on a row act right after that sample.
time_h, VCD (1e6/mL), viability (%), glucose (g/L), lactate (g/L), titer (mg/L), feed_pct (% v/v), glucose_target (g/L, blank = none), galplus (0/1), temperature (degC)
Optional header lines: `# batch_id:`, `# recipe:`, `# note:`

## Folders
dtwin/ (model, pipeline) · store/ (run store, predict-first log) · registry/ (model versions, champion.txt) · example_batches/ · web/ (engine, template, built page)
