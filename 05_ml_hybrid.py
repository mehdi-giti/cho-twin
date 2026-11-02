"""Step 5 - Pure-ML step model vs mechanistic vs hybrid, evaluated by full rollout on REAL val/test runs.

Rollout = start from the measured state at t=0 and predict every later sample using ONLY the
per-step inputs (feed, glucose target, Gal+, temperature). This is exactly how the twin is used.
"""
import numpy as np, pandas as pd, json, pickle
from sklearn.ensemble import HistGradientBoostingRegressor
from dtwin import mech
from dtwin.data import build

ts = pd.read_csv("data/DT_timeseries_v0.7_2026-11-01.csv"); runs = pd.read_csv("data/DT_runs_v0.7_2026-11-01.csv")
P = mech.default_params(); P.update(json.load(open("dtwin/mech_params.json")))
d2 = runs[runs.dataset == "D2"]
ids = {k: d2[(d2.data_type == "real") & (d2.ml_split == k)].run_id.tolist() for k in ("train", "val", "test")}
ids["aug"] = d2[d2.data_type == "real_augmented"].run_id.tolist()
TR = [lambda x: np.log(np.maximum(x, 0) + 0.1), lambda v: np.log(np.clip(v, 0.5, 99.5) / (100 - np.clip(v, 0.5, 99.5))),
      lambda x: np.log(np.maximum(x, 0) + 0.2), lambda x: np.log(np.maximum(x, 0) + 0.1), lambda x: np.log(np.maximum(x, 0) + 20)]
INV = [lambda z: np.exp(z) - 0.1, lambda z: 100 / (1 + np.exp(-z)), lambda z: np.exp(z) - 0.2, lambda z: np.exp(z) - 0.1, lambda z: np.exp(z) - 20]
SIG = np.array([0.10, 0.30, 0.15, 0.20, 0.10])


def fill_obs(o):
    """Within-run linear interpolation of missing measurements (for START states only)."""
    o = o.copy()
    for r in range(len(o)):
        for k in range(5):
            y = o[r, :, k]; ok = ~np.isnan(y); n = (~np.isnan(o[r, :, 0])).sum()
            if k == 3 and np.isnan(y[0]): y[0] = 0.15
            if k == 4 and np.isnan(y[0]): y[0] = 0.0
            ok = ~np.isnan(y[:n])
            if ok.sum() >= 1:
                o[r, :n, k] = np.interp(np.arange(n), np.where(ok)[0], y[:n][ok])
    return o


def intervals(run_ids):
    """One row per sampling interval: start state (measured + hidden mechanistic states), inputs, next obs."""
    b, o = build(ts, runs, run_ids); of = fill_obs(o)
    nom = mech.simulate(P, b)                         # nominal run supplies hidden states Gal, N, Dm
    rows = []
    R, J1 = o.shape[:2]
    for r in range(R):
        n = (~np.isnan(b["B"][r])).sum()
        for j in range(n - 1):
            y = nom[r, j].copy()                      # fallback where a variable was never measured
            via = of[r, j, 1]
            y[0] = of[r, j, 0]; y[1] = y[0] * (100 - via) / max(via, 0.5)
            for k, si in ((2, 2), (3, 3), (4, 4)):
                if not np.isnan(of[r, j, k]):
                    y[si] = of[r, j, k]
            rows.append(dict(run=b["run_ids"][r], j=j, t0=b["B"][r, j], t1=b["B"][r, j + 1], y0=y,
                             feed=b["feed"][r, j], glc=b["glc"][r, j], gal=b["gal"][r, j], T=b["T"][r, j],
                             obs1=o[r, j + 1], real=not b["run_ids"][r].startswith("AUG")))
    return rows


def iv_batch(rows):
    return dict(y0=np.stack([r["y0"] for r in rows]), B=np.array([[r["t0"], r["t1"]] for r in rows]),
                feed=np.array([[r["feed"]] for r in rows]), glc=np.array([[r["glc"]] for r in rows]),
                gal=np.array([[r["gal"]] for r in rows]), T=np.array([[r["T"]] for r in rows]))


def feats(y, t, feed, glc, gal):
    via = 100 * y[:, 0] / np.maximum(y[:, 0] + y[:, 1], 1e-9)
    return np.column_stack([y[:, 0], via, y[:, 2], y[:, 3], y[:, 4], y[:, 7], y[:, 8], t, feed,
                            np.nan_to_num(glc, nan=-1.0), gal])


# ------------------------------------------------ hybrid: invert per-interval rate corrections
def invert(rows, lam=4.0, iters=8, h=1e-3):
    b = iv_batch(rows); obs = np.stack([r["obs1"] for r in rows]); I = len(rows)
    tobs = np.stack([TR[k](obs[:, k]) for k in range(5)], 1); m = ~np.isnan(tobs); tobs = np.nan_to_num(tobs)
    g = np.zeros((I, 5))

    def resid(gg):
        pr = mech.observe(mech.simulate(P, b, corr=np.exp(gg)[:, None, :]))[:, 1]
        tp = np.stack([TR[k](pr[:, k]) for k in range(5)], 1)
        return np.where(m, (tp - tobs) / SIG, 0.0)
    for _ in range(iters):
        r0 = resid(g); Jm = np.zeros((I, 5, 5))
        for k in range(5):
            gk = g.copy(); gk[:, k] += h; Jm[:, :, k] = (resid(gk) - r0) / h
        A = np.einsum("iak,ial->ikl", Jm, Jm) + lam * np.eye(5)
        rhs = -(np.einsum("iak,ia->ik", Jm, r0) + lam * g)
        g = np.clip(g + np.linalg.solve(A, rhs[..., None])[..., 0], -1.5, 1.5)
    return g


def train_gbm(X, Y, w):
    ms = []
    for k in range(Y.shape[1]):
        ok = ~np.isnan(Y[:, k])
        ms.append(HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20,
                                                l2_regularization=1.0, random_state=0).fit(X[ok], Y[ok, k], sample_weight=w[ok]))
    return ms


def hybrid_fn(models, clip=0.7):
    def fn(s, y, t, batch, idx):
        X = feats(y, np.full(len(y), t), batch["feed"][idx, s], batch["glc"][idx, s], batch["gal"][idx, s])
        return np.exp(np.clip(np.column_stack([m.predict(X) for m in models]), -clip, clip))
    return fn


# ------------------------------------------------ pure ML one-step model (state -> next state)
def ml_targets(rows):
    y = np.stack([r["y0"] for r in rows]); o = np.stack([r["obs1"] for r in rows])
    via0 = 100 * y[:, 0] / np.maximum(y[:, 0] + y[:, 1], 1e-9)
    s0 = np.column_stack([y[:, 0], via0, y[:, 2], y[:, 3], y[:, 4]])
    return np.stack([TR[k](o[:, k]) - TR[k](s0[:, k]) for k in range(5)], 1)


def ml_X(s, t, dt, feed, glc, gal):
    return np.column_stack([s, t, dt, feed, np.nan_to_num(glc, nan=-1.0), gal])


def rows_X(rows):
    y = np.stack([r["y0"] for r in rows]); via0 = 100 * y[:, 0] / np.maximum(y[:, 0] + y[:, 1], 1e-9)
    s0 = np.column_stack([y[:, 0], via0, y[:, 2], y[:, 3], y[:, 4]])
    return ml_X(s0, np.array([r["t0"] for r in rows]), np.array([r["t1"] - r["t0"] for r in rows]),
                np.array([r["feed"] for r in rows]), np.array([r["glc"] for r in rows]), np.array([r["gal"] for r in rows]))


def ml_rollout(models, b):
    R, J = b["feed"].shape; out = np.full((R, J + 1, 5), np.nan)
    v0 = b["y0"]; s = np.column_stack([v0[:, 0], 100 * v0[:, 0] / (v0[:, 0] + v0[:, 1]), v0[:, 2], v0[:, 3], v0[:, 4]])
    out[:, 0] = s
    for j in range(J):
        ok = ~np.isnan(b["B"][:, j + 1])
        if not ok.any(): break
        X = ml_X(s, b["B"][:, j], b["B"][:, j + 1] - b["B"][:, j], b["feed"][:, j], b["glc"][:, j], b["gal"][:, j])
        d = np.column_stack([m.predict(np.nan_to_num(X)) for m in models])
        z = np.stack([TR[k](s[:, k]) for k in range(5)], 1) + d
        s = np.where(ok[:, None], np.stack([np.maximum(INV[k](z[:, k]), 0) for k in range(5)], 1), s)
        s[:, 1] = np.clip(s[:, 1], 0, 100)
        out[ok, j + 1] = s[ok]
    return out


# ------------------------------------------------ metrics
def metrics(pred, obs, b, label, split):
    res = dict(model=label, split=split)
    for k, v in enumerate(mech.OUT):
        p = pred[:, 1:, k]; o = obs[:, 1:, k]; mm = ~np.isnan(o) & ~np.isnan(p)
        if v in ("VCD", "titer"):
            sel = mm & (o > (1.0 if v == "VCD" else 50))
            res[f"{v}_MAPE_%"] = 100 * np.mean(np.abs(p[sel] - o[sel]) / o[sel])
        else:
            res[f"{v}_MAE"] = np.mean(np.abs(p[mm] - o[mm]))
    t = b["B"]; ft = []
    for r in range(len(t)):
        ok = ~np.isnan(obs[r, :, 4]) & ~np.isnan(t[r])
        if t[r][ok].max() >= 240:
            ft.append(abs(np.interp(240, t[r][ok], pred[r, ok, 4]) / np.interp(240, t[r][ok], obs[r, ok, 4]) - 1) * 100)
    res["titer_d10_APE_%"] = np.mean(ft)
    return res


if __name__ == "__main__":
    rows_real = intervals(ids["train"]); rows_aug = intervals(ids["aug"])
    print("intervals real/aug:", len(rows_real), len(rows_aug))
    g_real = invert(rows_real); g_aug = invert(rows_aug)
    print("median |log corr| real:", np.round(np.median(np.abs(g_real), 0), 3))
    X_real = np.stack([feats(r["y0"][None], np.array([r["t0"]]), np.array([r["feed"]]), np.array([r["glc"]]), np.array([r["gal"]]))[0] for r in rows_real])
    X_aug = np.stack([feats(r["y0"][None], np.array([r["t0"]]), np.array([r["feed"]]), np.array([r["glc"]]), np.array([r["gal"]]))[0] for r in rows_aug])
    W_REAL = 5.0
    hyb_real = train_gbm(X_real, g_real, np.ones(len(X_real)))
    hyb_all = train_gbm(np.vstack([X_real, X_aug]), np.vstack([g_real, g_aug]), np.r_[np.full(len(X_real), W_REAL), np.ones(len(X_aug))])
    Yr, Ya = ml_targets(rows_real), ml_targets(rows_aug)
    ml_real = train_gbm(np.nan_to_num(rows_X(rows_real)), Yr, np.ones(len(Yr)))
    ml_all = train_gbm(np.nan_to_num(np.vstack([rows_X(rows_real), rows_X(rows_aug)])), np.vstack([Yr, Ya]),
                       np.r_[np.full(len(Yr), W_REAL), np.ones(len(Ya))])
    table, preds = [], {}
    for split in ("train", "val", "test"):
        b, o = build(ts, runs, ids[split])
        cand = {"mechanistic": mech.observe(mech.simulate(P, b)),
                "ML only (real)": ml_rollout(ml_real, b), "ML only (real+new)": ml_rollout(ml_all, b),
                "hybrid (real)": mech.observe(mech.simulate(P, b, corr_fn=hybrid_fn(hyb_real))),
                "hybrid (real+new)": mech.observe(mech.simulate(P, b, corr_fn=hybrid_fn(hyb_all)))}
        for k, pr in cand.items():
            table.append(metrics(pr, o, b, k, split)); preds[(split, k)] = pr
    T = pd.DataFrame(table).round(2)
    T.to_csv("qc/model_comparison.csv", index=False)
    pd.set_option("display.width", 200); print(T.to_string(index=False))
    pickle.dump(dict(hyb_real=hyb_real, hyb_all=hyb_all, ml_real=ml_real, ml_all=ml_all), open("dtwin/models.pkl", "wb"))
    pickle.dump(preds, open("qc/rollout_preds.pkl", "wb"))
