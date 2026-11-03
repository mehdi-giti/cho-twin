"""Batch-import pipeline for the CHO fed-batch twin.

One deterministic loop per new batch:
  1. validate      check columns, units, ranges, time order
  2. predict first forecast the batch from day 0 with the CURRENT model, before it is used for training
  3. store         add the batch to the run store (as a real training run)
  4. retrain       re-learn the ML rate corrections (optionally refit the mechanistic parameters)
  5. evaluate      fixed benchmark of real runs the model never trains on + direction checks + band coverage
  6. gate          promote the new version only if it is not worse; otherwise keep the current one
  7. publish       write registry/<version>/ and the web model file

Batch file format (CSV, one row per sample; inputs on a row act right AFTER that sample):
  time_h, VCD, viability, glucose, lactate, titer, feed_pct, glucose_target, galplus, temperature
  units: h, 1e6 cells/mL, %, g/L, g/L, mg/L, % v/v, g/L (blank = no top-up), 0/1, degC
  optional header lines:  # batch_id: ...   # recipe: ...   # note: ...
"""
import os, io, json, pickle, shutil, datetime, importlib.util
import numpy as np, pandas as pd
from . import mech
from .data import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "store"); REG = os.path.join(ROOT, "registry")
COLS = ["time_h", "VCD", "viability", "glucose", "lactate", "titer", "feed_pct", "glucose_target", "galplus", "temperature"]
OPTIONAL = ["pH", "DO", "agitation"]   # set-points from this sample to the next; blank = not controlled / not recorded
BENCHMARK = ["D2_HIPp_R1", "D2_HIPp_R2", "D2_HIPp_R3", "D2_STD_R1", "D2_LoG_R1", "D2_HiF_R1"]   # never trained on
W_REAL = 5.0

_spec = importlib.util.spec_from_file_location("hyb", os.path.join(ROOT, "05_ml_hybrid.py"))
H = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(H)


# ------------------------------------------------------------------ store
def _explicit(b, o):
    rows = []
    for r, rid in enumerate(b["run_ids"]):
        n = (~np.isnan(b["B"][r])).sum()
        for j in range(n):
            last = j == n - 1
            rows.append(dict(run_id=rid, time_h=b["B"][r, j], VCD=o[r, j, 0], viability=o[r, j, 1], glucose=o[r, j, 2],
                             lactate=o[r, j, 3], titer=o[r, j, 4],
                             feed_pct=np.nan if last else b["feed"][r, j],
                             glucose_target=np.nan if last else b["glc"][r, j],
                             galplus=np.nan if last else float(b["gal"][r, j] > 0),
                             temperature=np.nan if last else b["T"][r, j]))
    return pd.DataFrame(rows)


def init_store():
    """Create the run store from the v0.7 data: real D2 runs + derived (augmented) D2 runs, all in explicit-input form."""
    os.makedirs(STORE, exist_ok=True)
    ts = pd.read_csv(os.path.join(ROOT, "data/DT_timeseries_v0.7_2026-11-01.csv")); runs = pd.read_csv(os.path.join(ROOT, "data/DT_runs_v0.7_2026-11-01.csv"))
    d2 = runs[runs.dataset == "D2"]
    real = d2[d2.data_type == "real"]; aug = d2[d2.data_type == "real_augmented"]
    held = real[(real.ml_split != "train") & (~real.run_id.isin(BENCHMARK))]          # kept out: example "new" batches
    real = real[~real.run_id.isin(held.run_id)]
    os.makedirs(os.path.join(ROOT, "example_batches"), exist_ok=True)
    rec0 = {"D2_STDp": "STD+", "D2_LoGp": "LoG+", "D2_HIP": "HIP", "D2_STD": "STD", "D2_LoG": "LoG", "D2_HiF": "HiF", "D2_HIPp": "HIP+"}
    bh, oh = build(ts, runs, held.run_id.tolist()); eh = _explicit(bh, oh)
    for rid, g in eh.groupby("run_id"):
        cond = held.set_index("run_id").condition[rid]
        with open(os.path.join(ROOT, "example_batches", f"{rid}.csv"), "w") as fh:
            fh.write(f"# batch_id: {rid}\n# recipe: {rec0[cond]}\n# note: real NISTCHO run (Schaepertoens 2026), never used for training\n")
            g[COLS].round(4).to_csv(fh, index=False)
    b, o = build(ts, runs, real.run_id.tolist()); df = _explicit(b, o)
    b2, o2 = build(ts, runs, aug.run_id.tolist()); df = pd.concat([df, _explicit(b2, o2)], ignore_index=True)
    rec = {"D2_STD": "STD", "D2_STDp": "STD+", "D2_LoG": "LoG", "D2_LoGp": "LoG+", "D2_HiF": "HiF", "D2_HIP": "HIP", "D2_HIPp": "HIP+"}
    idx = []
    for _, r in real.iterrows():
        role = "benchmark" if r.run_id in BENCHMARK else ("train" if r.ml_split == "train" else "held_out")
        idx.append(dict(run_id=r.run_id, kind="real", role=role, recipe=rec[r.condition], source="Schaepertoens 2026 (D2)", added=""))
    for _, r in aug.iterrows():
        idx.append(dict(run_id=r.run_id, kind="derived", role="train", recipe=rec[r.condition], source="v0.7 replicate resampling", added=""))
    df.to_csv(os.path.join(STORE, "timeseries.csv"), index=False)
    pd.DataFrame(idx).to_csv(os.path.join(STORE, "runs.csv"), index=False)
    json.dump([], open(os.path.join(STORE, "prospective.json"), "w"))


def load_store():
    return pd.read_csv(os.path.join(STORE, "timeseries.csv")), pd.read_csv(os.path.join(STORE, "runs.csv"), keep_default_na=False)


def batch_from(df, run_ids):
    gs = [df[df.run_id == r].sort_values("time_h") for r in run_ids]
    J = max(len(g) for g in gs) - 1; R = len(gs)
    b = dict(y0=np.zeros((R, 9)), B=np.full((R, J + 1), np.nan), feed=np.zeros((R, J)), glc=np.full((R, J), np.nan),
             gal=np.zeros((R, J)), T=np.full((R, J), 37.0), pH=np.full((R, J), np.nan), DO=np.full((R, J), np.nan), run_ids=list(run_ids))
    o = np.full((R, J + 1, 5), np.nan)
    for i, g in enumerate(gs):
        n = len(g); b["B"][i, :n] = g.time_h.values
        b["feed"][i, :n - 1] = np.nan_to_num(g.feed_pct.values[:-1]); b["glc"][i, :n - 1] = g.glucose_target.values[:-1]
        b["gal"][i, :n - 1] = np.nan_to_num(g.galplus.values[:-1]) * mech.GAL_PER_EVENT
        b["T"][i, :n - 1] = np.where(np.isnan(g.temperature.values[:-1]), 37.0, g.temperature.values[:-1])
        for c in ("pH", "DO"):
            if c in g.columns: b[c][i, :n - 1] = pd.to_numeric(g[c], errors="coerce").values[:-1]
        x0 = g.VCD.iloc[0]; v0 = g.viability.iloc[0] if not np.isnan(g.viability.iloc[0]) else 97.0
        g0 = g.glucose.iloc[0] if not np.isnan(g.glucose.iloc[0]) else 8.0
        l0 = g.lactate.iloc[0] if not np.isnan(g.lactate.iloc[0]) else 0.15
        p0 = g.titer.iloc[0] if not np.isnan(g.titer.iloc[0]) else 0.0
        b["y0"][i] = [x0, x0 * (100 - v0) / v0, g0, l0, p0, 0, 1, 1, 0]
        o[i, :n] = g[["VCD", "viability", "glucose", "lactate", "titer"]].values
    return b, o


# ------------------------------------------------------------------ 1. validate
def read_batch(path_or_text):
    text = open(path_or_text).read() if os.path.exists(str(path_or_text)) else str(path_or_text)
    meta = {}
    body = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            if ":" in line:
                k, v = line.strip("# ").split(":", 1); meta[k.strip().lower()] = v.strip()
        elif line.strip():
            body.append(line)
    df = pd.read_csv(io.StringIO("\n".join(body)))
    df.columns = [c.strip() for c in df.columns]
    return df, meta


def validate(df):
    errors, warnings = [], []
    miss = [c for c in COLS if c not in df.columns]
    if miss:
        return [f"missing columns: {', '.join(miss)}"], warnings
    for c in COLS + [c for c in OPTIONAL if c in df.columns]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "pH" in df.columns and ((df.pH.dropna() < 6.0) | (df.pH.dropna() > 8.0)).any(): errors.append("pH outside 6.0-8.0")
    if "DO" in df.columns and ((df.DO.dropna() < 0) | (df.DO.dropna() > 200)).any(): errors.append("DO outside 0-200 % air saturation")
    if "pH" in df.columns and df.pH.notna().any(): warnings.append("pH given: the model uses literature priors for pH effects (no varied-pH runs yet)")
    if "DO" in df.columns and df.DO.notna().any(): warnings.append("DO given: the model uses literature priors and one DO-failure pair for DO effects")
    if "agitation" in df.columns and df.agitation.notna().any(): warnings.append("agitation is stored for future models but not used yet (no data that separate its effect)")
    t = df.time_h.values
    if len(df) < 4: errors.append("at least 4 samples are needed")
    if abs(t[0]) > 1: errors.append("first sample must be at time 0 h (inoculation)")
    if np.any(np.diff(t) <= 0): errors.append("time_h must increase from row to row")
    if np.isnan(df.VCD.iloc[0]) or df.VCD.iloc[0] <= 0: errors.append("VCD at time 0 is required")
    rng = dict(VCD=(0, 40), viability=(0, 100), glucose=(0, 20), lactate=(0, 10), titer=(0, 6000))
    for c, (lo, hi) in rng.items():
        bad = df[c].dropna(); bad = bad[(bad < lo) | (bad > hi)]
        if len(bad): errors.append(f"{c} outside {lo}-{hi}: {len(bad)} value(s)")
    if df.titer.dropna().max() < 20 and df.titer.notna().sum() > 2:
        errors.append("titer looks like g/L; the file expects mg/L")
    if df.glucose.dropna().max() > 15:
        warnings.append("glucose above 15: check it is g/L, not mM")
    if df.lactate.dropna().max() > 5:
        warnings.append("lactate above 5: check it is g/L, not mM")
    inp = df.iloc[:-1]
    if inp.feed_pct.isna().any(): warnings.append("blank feed_pct treated as no feed")
    if (inp.feed_pct > 15).any(): errors.append("feed_pct above 15% v/v")
    if (inp.temperature.dropna() < 28).any() or (inp.temperature.dropna() > 39).any(): errors.append("temperature outside 28-39 degC")
    if (inp.feed_pct > 5).any(): warnings.append("feed above 5% v/v: outside the range the model was trained on")
    g = inp.glucose_target.dropna(); g = g[g > 0]
    if ((g < 2) | (g > 8)).any(): warnings.append("glucose target outside 2-8 g/L: outside the trained range")
    if (inp.temperature.dropna() != 37).any(): warnings.append("temperature differs from 37 degC: the model uses a literature prior here")
    for c in ("titer", "glucose", "viability"):
        if df[c].notna().sum() < 3: warnings.append(f"fewer than 3 {c} measurements: little to learn from")
    return errors, warnings


# ------------------------------------------------------------------ model versions
def load_version(v):
    d = os.path.join(REG, v)
    P = mech.default_params(); P.update(json.load(open(os.path.join(d, "mech_params.json"))))
    return dict(version=v, P=P, models=pickle.load(open(os.path.join(d, "models.pkl"), "rb")),
                band=json.load(open(os.path.join(d, "band.json"))), report=json.load(open(os.path.join(d, "report.json"))))


def champion():
    return open(os.path.join(REG, "champion.txt")).read().strip()


def rollout(model, b):
    H.P = model["P"]
    return mech.observe(mech.simulate(model["P"], b, corr_fn=H.hybrid_fn(model["models"])))


def errors_of(pred, o, b):
    m = H.metrics(pred, o, b, "", "")
    return {k: float(v) for k, v in m.items() if k not in ("model", "split")}


# ------------------------------------------------------------------ 4. retrain
def train_rows(df, idx, P, ids):
    b, o = batch_from(df, ids); of = H.fill_obs(o); nom = mech.simulate(P, b)
    kind = idx.set_index("run_id").kind
    rows = []
    for r, rid in enumerate(ids):
        n = (~np.isnan(b["B"][r])).sum()
        for j in range(n - 1):
            y = nom[r, j].copy(); via = of[r, j, 1]
            y[0] = of[r, j, 0]; y[1] = y[0] * (100 - via) / max(via, 0.5)
            for k in (2, 3, 4):
                if not np.isnan(of[r, j, k]): y[k] = of[r, j, k]
            rows.append(dict(run=rid, j=j, t0=b["B"][r, j], t1=b["B"][r, j + 1], y0=y, feed=b["feed"][r, j], glc=b["glc"][r, j],
                             gal=b["gal"][r, j], T=b["T"][r, j], obs1=o[r, j + 1], real=kind[rid] != "derived"))
    return rows


def retrain(P, df, idx):
    ids = idx[idx.role == "train"].run_id.tolist()
    H.P = P
    rows = train_rows(df, idx, P, ids)
    g = H.invert(rows)
    X = np.stack([H.feats(r["y0"][None], np.array([r["t0"]]), np.array([r["feed"]]), np.array([r["glc"]]), np.array([r["gal"]]))[0] for r in rows])
    w = np.array([W_REAL if r["real"] else 1.0 for r in rows])
    real = np.array([r["real"] for r in rows])
    models = H.train_gbm(X, g, w)
    corr_med = float(np.median(np.abs(g[real]))) if real.any() else float("nan")
    return models, dict(n_train_runs=len(ids), n_real_train_runs=int(idx[(idx.role == "train") & (idx.kind != "derived")].shape[0]),
                        median_abs_log_correction=corr_med)


def refit_mech(P0, df, idx, max_nfev=40):
    """Refit mechanistic parameters on all REAL training runs (one start from the current values)."""
    from scipy.optimize import least_squares
    ids = idx[(idx.role == "train") & (idx.kind != "derived")].run_id.tolist()
    b, o = batch_from(df, ids)
    TR = [lambda x: np.log(x + 0.1), lambda v: np.log(np.clip(v, 0.5, 99.5) / (100 - np.clip(v, 0.5, 99.5))),
          lambda x: np.log(x + 0.2), lambda x: np.log(x + 0.1), lambda x: np.log(x + 20)]
    SIG = np.array([0.10, 0.30, 0.15, 0.20, 0.10]); nP = len(mech.PARAMS)
    lo = np.array([np.log(v[1]) for v in mech.PARAMS.values()] + [v[1] for v in mech.LINEAR.values()])
    hi = np.array([np.log(v[2]) for v in mech.PARAMS.values()] + [v[2] for v in mech.LINEAR.values()])
    x0 = np.array([np.log(P0[k]) if i < nP else P0[k] for i, k in enumerate(mech.NAMES)])
    x0 = np.clip(x0, lo + 1e-6, hi - 1e-6)

    def to_p(x):
        p = dict(P0)
        for i, k in enumerate(mech.NAMES): p[k] = np.exp(x[i]) if i < nP else x[i]
        return p

    def res(pred):
        out = []
        for k in range(5):
            a, bb = TR[k](np.maximum(pred[:, 1:, k], 0)), TR[k](o[:, 1:, k]); m = ~np.isnan(bb); out.append(((a - bb) / SIG[k])[m])
        return np.concatenate(out)
    f = least_squares(lambda x: np.concatenate([res(mech.observe(mech.simulate(to_p(x), b))), 0.05 * (x - x0)]),
                      x0, bounds=(lo, hi), max_nfev=max_nfev, diff_step=1e-3)
    return to_p(f.x)


# ------------------------------------------------------------------ 5. evaluate
def scenario(model, steps):
    n = len(steps)
    b = dict(y0=np.array([[0.4, 0.4 * 2.5 / 97.5, 8.0, 0.15, 0, 0, 1, 1, 0]]), B=np.arange(n + 1, dtype=float)[None] * 24,
             feed=np.array([[s["feed_pct"] for s in steps]]), glc=np.array([[np.nan if s["glucose_target"] is None else s["glucose_target"] for s in steps]]),
             gal=np.array([[mech.GAL_PER_EVENT if s["galplus"] else 0 for s in steps]]), T=np.array([[s["temperature"] for s in steps]]),
             pH=np.array([[s.get("pH", np.nan) for s in steps]], float), DO=np.array([[s.get("DO", np.nan) for s in steps]], float))
    return rollout(model, b)[0]


def protocol(name, days=11):
    cfg = {"STD": (48, 5.0, 8.0, False), "LoG": (48, 5.0, 4.0, False), "LoG+": (48, 5.0, 4.0, True), "HiF": (24, 2.5, 4.0, False)}[name]
    steps, k = [], 0
    for d in range(days):
        fed = d >= 3 and (cfg[0] == 24 or d % 2 == 1)
        steps.append(dict(feed_pct=cfg[1] if fed else 0.0, glucose_target=cfg[2] if fed else None, galplus=bool(cfg[3] and fed and k % 2 == 0), temperature=37.0))
        k += fed
    return steps


def direction_checks(model):
    S = {n: scenario(model, protocol(n)) for n in ("STD", "LoG", "LoG+", "HiF")}
    s33 = protocol("STD")
    for d in range(5, 11): s33[d]["temperature"] = 33.0
    S["T33"] = scenario(model, s33)
    lowdo = protocol("STD"); [st.update(DO=5.0) for st in lowdo]; S["DO5"] = scenario(model, lowdo)
    hiph = protocol("STD"); [st.update(pH=7.3) for st in hiph]; S["pH73"] = scenario(model, hiph)
    f = lambda n, k: S[n][-1, k]
    return [
        dict(check="Glucose target 4 vs 8 lowers final titer", ok=bool(f("LoG", 4) < f("STD", 4)), evidence="data"),
        dict(check="Glucose target 4 vs 8 collapses the culture", ok=bool(f("LoG", 1) < f("STD", 1) - 20), evidence="data"),
        dict(check="Gal+ extends viability under glucose limitation", ok=bool(f("LoG+", 1) > f("LoG", 1)), evidence="data"),
        dict(check="Daily feeding gives lower titer than 48 h feeding", ok=bool(f("HiF", 4) < f("STD", 4)), evidence="data"),
        dict(check="33 degC shift lowers peak VCD", ok=bool(S["T33"][:, 0].max() < S["STD"][:, 0].max()), evidence="prior"),
        dict(check="33 degC shift extends viability", ok=bool(f("T33", 1) > f("STD", 1)), evidence="prior"),
        dict(check="DO held at 5% lowers peak VCD", ok=bool(S["DO5"][:, 0].max() < S["STD"][:, 0].max()), evidence="prior"),
        dict(check="pH 7.3 raises peak lactate", ok=bool(S["pH73"][:, 3].max() > S["STD"][:, 3].max()), evidence="prior")]


def band_coverage(pred, o, b, band):
    TR = [lambda x: np.log(np.maximum(x, 0) + 0.1), lambda v: np.log(np.clip(v, 0.5, 99.5) / (100 - np.clip(v, 0.5, 99.5))),
          lambda x: np.log(np.maximum(x, 0) + 0.2), lambda x: np.log(np.maximum(x, 0) + 0.1), lambda x: np.log(np.maximum(x, 0) + 20)]
    out = {}
    for k, v in enumerate(mech.OUT):
        t = b["B"][:, 1:] / 24; m = ~np.isnan(o[:, 1:, k]) & ~np.isnan(t)
        if v == "lactate" and "lactate_abs" in band:
            z = np.abs(o[:, 1:, k][m] - pred[:, 1:, k][m]) / np.minimum(1, np.sqrt(t[m] / 3)); out[v] = float(100 * np.mean(z <= band["lactate_abs"]))
            continue
        z = np.abs(TR[k](o[:, 1:, k][m]) - TR[k](pred[:, 1:, k][m])) / np.sqrt(t[m])
        out[v] = float(100 * np.mean(z <= band[v]))
    return out


def evaluate(model, df, idx):
    ids = idx[idx.role == "benchmark"].run_id.tolist()
    b, o = batch_from(df, ids); pred = rollout(model, b)
    known = [i for i, r in enumerate(ids) if not r.startswith("D2_HIPp")]; unseen = [i for i, r in enumerate(ids) if r.startswith("D2_HIPp")]
    sub = lambda I: ({k: v[I] for k, v in b.items() if k != "run_ids"} | {"run_ids": [ids[i] for i in I]})
    # clip rate of predicted corrections on the benchmark
    clipped, total = [0], [0]
    def fn(s, y, t, batch, idx_):
        X = H.feats(y, np.full(len(y), t), batch["feed"][idx_, s], batch["glc"][idx_, s], batch["gal"][idx_, s])
        g = np.column_stack([m.predict(X) for m in model["models"]]); clipped[0] += int((np.abs(g) >= 0.7).sum()); total[0] += g.size
        return np.exp(np.clip(g, -0.7, 0.7))
    H.P = model["P"]; mech.simulate(model["P"], b, corr_fn=fn)
    return dict(benchmark_all=errors_of(pred, o, b), benchmark_known=errors_of(pred[known], o[known], sub(known)),
                benchmark_unseen=errors_of(pred[unseen], o[unseen], sub(unseen)),
                band_coverage=band_coverage(pred, o, b, model["band"]), clip_rate=clipped[0] / max(total[0], 1),
                direction_checks=direction_checks(model))


# ------------------------------------------------------------------ 6. gate
GATES = dict(drift_tol=1.5, titer_mape_tol=1.0, vcd_mape_tol=2.0, coverage_min=60.0, coverage_max=95.0, corr_max=0.35, clip_max=0.25)


def best_titer_error():
    vals = []
    for v in os.listdir(REG):
        f = os.path.join(REG, v, "report.json")
        if os.path.exists(f):
            r = json.load(open(f))
            if r.get("promoted"): vals.append(r["benchmark_all"]["titer_MAPE_%"])
    return min(vals) if vals else float("inf")


def gate(champ, chall):
    c, n = champ["benchmark_all"], chall["benchmark_all"]; cov = np.mean(list(chall["band_coverage"].values()))
    best = best_titer_error()
    res = [
        dict(rule=f"Titer error not worse than the best version so far by more than {GATES['drift_tol']} pt (stops slow drift)",
             ok=n["titer_MAPE_%"] <= best + GATES["drift_tol"], value=f"{n['titer_MAPE_%']:.2f}% (best {best:.2f}%)"),
        dict(rule=f"Titer error on benchmark not worse by more than {GATES['titer_mape_tol']} pt",
             ok=n["titer_MAPE_%"] <= c["titer_MAPE_%"] + GATES["titer_mape_tol"], value=f"{n['titer_MAPE_%']:.2f}% (current {c['titer_MAPE_%']:.2f}%)"),
        dict(rule=f"VCD error on benchmark not worse by more than {GATES['vcd_mape_tol']} pt",
             ok=n["VCD_MAPE_%"] <= c["VCD_MAPE_%"] + GATES["vcd_mape_tol"], value=f"{n['VCD_MAPE_%']:.2f}% (current {c['VCD_MAPE_%']:.2f}%)"),
        dict(rule="All direction checks pass", ok=all(d["ok"] for d in chall["direction_checks"]),
             value=f"{sum(d['ok'] for d in chall['direction_checks'])}/{len(chall['direction_checks'])}"),
        dict(rule=f"Band coverage between {GATES['coverage_min']:.0f}% and {GATES['coverage_max']:.0f}%",
             ok=GATES["coverage_min"] <= cov <= GATES["coverage_max"], value=f"{cov:.1f}%"),
        dict(rule="ML corrections stay moderate (median below x1.42)", ok=chall["median_abs_log_correction"] < GATES["corr_max"],
             value=f"x{np.exp(chall['median_abs_log_correction']):.2f}"),
        dict(rule="Few corrections hit the x0.5/x2 limit (below 25%)", ok=chall["clip_rate"] < GATES["clip_max"], value=f"{100 * chall['clip_rate']:.1f}%"),
    ]
    for r in res: r["ok"] = bool(r["ok"])
    return all(r["ok"] for r in res), res


def next_version(v):
    """Next free minor version (a candidate that was not promoted keeps its number in the history)."""
    a = v.split(".")[0]
    used = [int(d.split(".")[1]) for d in os.listdir(REG) if d.startswith(a + ".") and d.split(".")[1].isdigit()]
    return f"{a}.{max(used) + 1}"


def save_version(v, P, models, band, report):
    d = os.path.join(REG, v); os.makedirs(d, exist_ok=True)
    json.dump({k: float(P[k]) for k in mech.NAMES + list(mech.PRIOR)}, open(os.path.join(d, "mech_params.json"), "w"), indent=1)
    pickle.dump(models, open(os.path.join(d, "models.pkl"), "wb")); json.dump(band, open(os.path.join(d, "band.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(d, "report.json"), "w"), indent=1, default=float)


# ------------------------------------------------------------------ the full import
def import_batch(path_or_text, batch_id=None, refit_mechanistic=False, recipe=None, log=print):
    df_new, meta = read_batch(path_or_text)
    batch_id = batch_id or meta.get("batch_id") or f"B{datetime.datetime.now():%Y%m%d%H%M%S}"
    errors, warnings = validate(df_new)
    for w in warnings: log("  warning:", w)
    if errors:
        for e in errors: log("  error:", e)
        return dict(batch_id=batch_id, status="rejected", errors=errors, warnings=warnings)
    df, idx = load_store()
    if batch_id in set(idx.run_id): raise ValueError(f"batch {batch_id} is already in the store")
    champ_v = champion(); champ = load_version(champ_v)
    # 2. predict first
    df_new = df_new[COLS + [c for c in OPTIONAL if c in df_new.columns]].copy(); df_new.insert(0, "run_id", batch_id)
    b, o = batch_from(df_new, [batch_id]); pred = rollout(champ, b)
    pf = dict(batch_id=batch_id, model_version=champ_v, date=f"{datetime.date.today()}", recipe=recipe or meta.get("recipe", ""),
              errors=errors_of(pred, o, b), day=[float(x) / 24 for x in b["B"][0]],
              pred={v: [float(x) for x in pred[0, :, k]] for k, v in enumerate(mech.OUT)},
              obs={v: [None if np.isnan(x) else float(x) for x in o[0, :, k]] for k, v in enumerate(mech.OUT)})
    log(f"  predict-first with model {champ_v}: titer error {pf['errors']['titer_MAPE_%']:.1f}%, VCD error {pf['errors']['VCD_MAPE_%']:.1f}%")
    # 3. store
    df = pd.concat([df, df_new], ignore_index=True)
    idx = pd.concat([idx, pd.DataFrame([dict(run_id=batch_id, kind="imported", role="train", recipe=pf["recipe"],
                                             source=meta.get("note", "imported batch"), added=pf["date"])])], ignore_index=True)
    # 4. retrain
    P = refit_mech(champ["P"], df, idx) if refit_mechanistic else champ["P"]
    models, tr = retrain(P, df, idx)
    chall = dict(version=next_version(champ_v), P=P, models=models, band=champ["band"])
    rep = evaluate(chall, df, idx) | tr | dict(version=chall["version"], parent=champ_v, date=pf["date"], trained_after=batch_id,
                                                mechanistic_refit=bool(refit_mechanistic))
    ok, rules = gate(champ["report"], rep)
    rep["gate"] = rules; rep["promoted"] = ok
    # persist store + prospective log regardless of the gate (the batch is real data)
    df.to_csv(os.path.join(STORE, "timeseries.csv"), index=False); idx.to_csv(os.path.join(STORE, "runs.csv"), index=False)
    log_p = json.load(open(os.path.join(STORE, "prospective.json"))); log_p.append(pf)
    json.dump(log_p, open(os.path.join(STORE, "prospective.json"), "w"), default=float)
    # 6/7. gate + publish
    save_version(chall["version"], P, models, champ["band"], rep)
    if ok:
        open(os.path.join(REG, "champion.txt"), "w").write(chall["version"])
        log(f"  model {chall['version']} PROMOTED (benchmark titer error {rep['benchmark_all']['titer_MAPE_%']:.2f}% vs {champ['report']['benchmark_all']['titer_MAPE_%']:.2f}%)")
    else:
        log(f"  model {chall['version']} NOT promoted; keeping {champ_v}. Failed: " + "; ".join(r["rule"] for r in rules if not r["ok"]))
    return dict(batch_id=batch_id, status="imported", warnings=warnings, predict_first=pf, challenger=chall["version"], promoted=ok, gate=rules)


def init_registry():
    """Version 1.0 = the v0.8 hybrid (mechanistic fit on 16 real runs + ML corrections on real + derived runs)."""
    os.makedirs(REG, exist_ok=True)
    P = mech.default_params(); P.update(json.load(open(os.path.join(ROOT, "dtwin/mech_params.json"))))
    models = pickle.load(open(os.path.join(ROOT, "dtwin/models.pkl"), "rb"))["hyb_all"]
    band = json.load(open(os.path.join(ROOT, "dtwin/band.json")))
    df, idx = load_store(); H.P = P
    rows = train_rows(df, idx, P, idx[(idx.role == "train") & (idx.kind != "derived")].run_id.tolist())
    corr = float(np.median(np.abs(H.invert(rows))))
    m = dict(version="1.0", P=P, models=models, band=band)
    rep = evaluate(m, df, idx) | dict(version="1.0", parent="", date=f"{datetime.date.today()}", trained_after="initial build (v0.8)",
                                      mechanistic_refit=True, n_train_runs=int((idx.role == "train").sum()),
                                      n_real_train_runs=int(((idx.role == "train") & (idx.kind != "derived")).sum()),
                                      median_abs_log_correction=corr, promoted=True, gate=[])
    save_version("1.0", P, models, band, rep)
    open(os.path.join(REG, "champion.txt"), "w").write("1.0")
    return rep


# ------------------------------------------------------------------ 7. web export
TEMPLATE_CSV = ("# batch_id: MY_RUN_01\n# recipe: STD\n# note: free text\n"
                "time_h,VCD,viability,glucose,lactate,titer,feed_pct,glucose_target,galplus,temperature\n"
                "0,0.40,97.5,8.0,,,0,,0,37\n72,3.6,98.8,5.2,1.18,72,5,8,0,37\n96,5.9,98.6,,,120,0,,0,37\n"
                "120,10.7,98.5,4.8,1.14,234,5,8,0,37\n")


def export_web(out_path):
    v = champion(); m = load_version(v); df, idx = load_store()
    sig = lambda x: float(f"{x:.6g}")
    models = []
    for gm in m["models"]:
        F, TH, L, R_, roots = [], [], [], [], []
        for pr in gm._predictors:
            nd = pr[0].nodes; off = len(F); roots.append(off)
            for n in nd:
                leaf = bool(n["is_leaf"])
                F.append(-1 if leaf else int(n["feature_idx"])); TH.append(sig(n["value"] if leaf else n["num_threshold"]))
                L.append(-1 if leaf else off + int(n["left"])); R_.append(-1 if leaf else off + int(n["right"]))
        models.append(dict(base=sig(float(np.ravel(gm._baseline_prediction)[0])), roots=roots, f=F, th=TH, l=L, r=R_))
    real = {}
    for _, r in idx[idx.kind != "derived"].iterrows():
        g = df[df.run_id == r.run_id].sort_values("time_h")
        real.setdefault(r.recipe or "other", []).append(dict(id=r.run_id, kind=r.kind, role=r.role, day=[round(t / 24, 3) for t in g.time_h],
            **{c: [None if np.isnan(x) else round(float(x), 3) for x in g[c]] for c in mech.OUT}))
    ids = idx[idx.role == "benchmark"].run_id.tolist(); b, o = batch_from(df, ids); pred = rollout(m, b)
    fits = []
    for i, rid in enumerate(ids):
        ok = ~np.isnan(b["B"][i])
        fits.append(dict(id=rid, unseen=rid.startswith("D2_HIPp"), day=[round(t / 24, 3) for t in b["B"][i][ok]],
                         inputs=[dict(feed_pct=float(b["feed"][i, j]), glucose_target=None if np.isnan(b["glc"][i, j]) else float(b["glc"][i, j]),
                                      galplus=bool(b["gal"][i, j] > 0), temperature=float(b["T"][i, j])) for j in range(int(ok.sum()) - 1)],
                         pred={c: [round(float(x), 3) for x in pred[i, ok, k]] for k, c in enumerate(mech.OUT)},
                         obs={c: [None if np.isnan(x) else round(float(x), 3) for x in o[i, ok, k]] for k, c in enumerate(mech.OUT)}))
    history = []
    for vv in sorted(os.listdir(REG), key=lambda s: [int(x) for x in s.split(".")] if s[0].isdigit() else [999]):
        f = os.path.join(REG, vv, "report.json")
        if os.path.exists(f):
            rp = json.load(open(f))
            history.append({k: rp.get(k) for k in ("version", "parent", "date", "trained_after", "mechanistic_refit", "n_train_runs", "n_real_train_runs",
                                                   "median_abs_log_correction", "clip_rate", "promoted", "gate", "band_coverage", "direction_checks",
                                                   "benchmark_all", "benchmark_known", "benchmark_unseen")})
    # typical spread between real replicates of the same recipe (deviation from the recipe mean at the same sample index)
    spread = {}
    reals = idx[(idx.kind == "real")]
    for c in mech.OUT:
        devs = []
        for rec, g in reals.groupby("recipe"):
            runs_ = [df[df.run_id == r].sort_values("time_h")[c].values for r in g.run_id]
            if len(runs_) < 2: continue
            n = min(len(x) for x in runs_); A = np.array([x[:n] for x in runs_], float)[:, 1:]
            with __import__("warnings").catch_warnings():
                __import__("warnings").simplefilter("ignore"); mu = np.nanmean(A, 0)
            with np.errstate(all="ignore"):
                d = np.abs(A - mu)
                if c in ("VCD", "titer"):
                    thr = 1.0 if c == "VCD" else 50
                    d = np.where(mu > thr, 100 * d / mu, np.nan)
            devs.append(d[~np.isnan(d)])
        spread[c] = float(np.mean(np.concatenate(devs))) if devs else None
    pk = mech.NAMES + list(mech.PRIOR)
    out = dict(version=v, params={k: sig(m["P"][k]) for k in pk}, gal=mech.GAL_PER_EVENT, band=m["band"], models=models, real=real,
               bench=dict(runs=fits, known=m["report"]["benchmark_known"], unseen=m["report"]["benchmark_unseen"]),
               spread=spread, history=history, prospective=json.load(open(os.path.join(STORE, "prospective.json"))), gates=GATES, template=TEMPLATE_CSV,
               examples={f[:-4]: open(os.path.join(ROOT, "example_batches", f)).read() for f in sorted(os.listdir(os.path.join(ROOT, "example_batches")))},
               in_store=sorted(idx[idx.kind != "derived"].run_id.tolist()),
               rejected=[json.load(open(f)) for f in sorted(__import__("glob").glob(os.path.join(ROOT, "batches", "rejected", "*.json")))],
               store=dict(real=int((idx.kind == "real").sum()), imported=int((idx.kind == "imported").sum()), derived=int((idx.kind == "derived").sum()),
                          benchmark=len(ids)))
    json.dump(out, open(out_path, "w"), separators=(",", ":"), default=float)
    return out
