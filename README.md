# CHO Fed-Batch Twin

A hybrid (mechanistic + machine learning) digital twin of a CHO fed-batch antibody process.
Plan a culture day by day and see predicted titer, cell density, viability, glucose and lactate
with calibrated 80% ranges. Import finished batches; the model retrains itself on GitHub and
replaces the current version only if it passes its checks.

**Website:** `https://<your-user>.github.io/<this-repo>/` (after setup below)

## One-time setup (about 5 minutes)
1. Create a new repository on GitHub (Public for free GitHub Pages; Private needs a paid plan).
2. Upload this folder: on your computer run
   ```
   git remote add origin https://github.com/<your-user>/<this-repo>.git
   git push -u origin main
   ```
   (or GitHub Desktop: *Add existing repository*, then *Publish*).
3. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. **Actions** tab → *Retrain and publish the twin* → *Run workflow*. After 2–3 minutes the site is live.

## Adding a new batch
1. On the website, **Batches** → drop your CSV → check the predict-first result → **Download for upload**.
2. Upload that file to `batches/incoming/` in the repository (the website links to the upload page).
3. The GitHub Action validates it, predicts it first, retrains, runs the promotion checks and
   republishes the site (about 1–2 minutes per batch). Rejected files move to `batches/rejected/`
   with the reason, shown in the website's batch log.

To also refit the mechanistic parameters: Actions → *Run workflow* → tick *refit_mech*.

## Run locally
```
pip install -r requirements.txt
python import_batch.py example_batches/D2_STDp_R1.csv   # one batch
python process_incoming.py                              # everything in batches/incoming
python build_site.py                                    # site/index.html
```
Details: `PIPELINE.md`. Batch format: see the website's *File format* panel or `PIPELINE.md`.

## What is in here
| Folder | Content |
|---|---|
| `dtwin/` | mechanistic model, data handling, pipeline |
| `registry/` | every model version (parameters, ML models, report); `champion.txt` = current |
| `store/` | run store and the predict-first log |
| `batches/` | incoming, imported and rejected batch files |
| `web/` | browser engine (`twin.js`) and page template |
| `data/` | real NISTCHO runs (Schaepertoens et al. 2026) and derived runs |

The website runs entirely in the visitor's browser; no data are sent anywhere while checking a batch.
