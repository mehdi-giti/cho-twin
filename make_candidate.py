"""Candidate model: lactate refit + retrained corrections + lactate band in g/L. Promoted only through the gates."""
import json, datetime, numpy as np, sys
from dtwin import pipeline as pl, mech

champ_v = pl.champion(); champ = pl.load_version(champ_v); df, idx = pl.load_store()
P = mech.default_params(); P.update(json.load(open(sys.argv[1])))
models, tr = pl.retrain(P, df, idx)
cand = dict(version=pl.next_version(champ_v), P=P, models=models, band=dict(champ["band"]))

# lactate band: absolute half-width (g/L), calibrated as the 80% quantile of |error| on the 3 known-recipe benchmark runs,
# ramping in over the first 3 days (error is ~0 at inoculation). Checked afterwards on the unseen recipe.
ids = idx[idx.role == "benchmark"].run_id.tolist(); b, o = pl.batch_from(df, ids); pr = pl.rollout(cand, b)
known = np.array([not r.startswith("D2_HIPp") for r in ids])
t = b["B"][:, 1:] / 24; ramp = np.minimum(1, np.sqrt(t / 3))
z = np.abs(pr[:, 1:, 3] - o[:, 1:, 3]) / ramp
w = float(np.nanquantile(z[known], 0.80))
cand["band"]["lactate_abs"] = round(w, 3)
inside = lambda K: float(np.nanmean((z[K] <= w)[~np.isnan(z[K])]) * 100)
print(f"lactate band +/- {w:.2f} g/L; inside: known {inside(known):.0f}%, unseen {inside(~known):.0f}%")

rep = pl.evaluate(cand, df, idx) | tr | dict(version=cand["version"], parent=champ_v, date=f"{datetime.date.today()}",
      trained_after="lactate refit + pH/DO priors", mechanistic_refit=True)
# coverage for lactate with the new absolute band
m = ~np.isnan(z); rep["band_coverage"]["lactate"] = float(np.mean(z[m] <= w) * 100)
ok, rules = pl.gate(champ["report"], rep); rep["gate"] = rules; rep["promoted"] = ok
pl.save_version(cand["version"], P, models, cand["band"], rep)
if ok: open(pl.os.path.join(pl.REG, "champion.txt"), "w").write(cand["version"])
c, n = champ["report"]["benchmark_all"], rep["benchmark_all"]
for k in ("titer_MAPE_%", "VCD_MAPE_%", "viability_MAE", "glucose_MAE", "lactate_MAE"):
    print(f"{k:15s} {c[k]:7.3f} -> {n[k]:7.3f}")
print("gate:", [(r["rule"][:45], r["ok"], r["value"]) for r in rules]); print("PROMOTED" if ok else "kept", champ_v, "->", cand["version"])
