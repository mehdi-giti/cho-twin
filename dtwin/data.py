"""Turn D2 runs (real or real_augmented) into simulation batches: segments = sampling intervals."""
import numpy as np, pandas as pd
from .mech import GAL_PER_EVENT, OUT

LAC0 = 0.15   # g/L, lactate at inoculation (not measured in D2; carried over from seed medium)


def feed_schedule(meta, g):
    """Per-sample feed inputs following the D2 protocol (feed directly after the sample).
    HIP/HIP+: glucose to 2 g/L 'when pH >= 7.2'; pH is not recorded, so a top-up to 2 g/L is
    assumed whenever measured glucose < 1 g/L (imputed)."""
    t = g.time_h.values; n = len(t)
    feed = np.zeros(n - 1); glc = np.full(n - 1, np.nan); gal = np.zeros(n - 1)
    k = 0
    for j in range(n - 1):
        if t[j] < 66:
            continue
        if meta["feed_interval_h"] == 48 and not any(abs(t[j] - d * 24) < 6 for d in (3, 5, 7, 9)):
            continue
        feed[j] = meta["feed_pct_per_event"]
        gm = g.glucose.values[j]
        if str(meta["strategy"]).startswith("HIP"):
            glc[j] = 2.0 if (np.isnan(gm) or gm < 1.0) else np.nan
        else:
            glc[j] = meta["glc_target_gL"]
        if meta["galplus"] and k % 2 == 0:
            gal[j] = GAL_PER_EVENT
        k += 1
    return feed, glc, gal


def build(ts, runs, run_ids):
    """Return batch dict + observed outputs (R, J+1, 5) with NaN for missing."""
    gs = [ts[ts.run_id == r].sort_values("time_h") for r in run_ids]
    J = max(len(g) for g in gs) - 1; R = len(gs)
    B = np.full((R, J + 1), np.nan); F = np.zeros((R, J)); G = np.full((R, J), np.nan); Ga = np.zeros((R, J))
    T = np.full((R, J), 37.0); y0 = np.zeros((R, 9)); obs = np.full((R, J + 1, 5), np.nan)
    meta = runs.set_index("run_id")
    for i, (r, g) in enumerate(zip(run_ids, gs)):
        m = meta.loc[r]; n = len(g)
        B[i, :n] = g.time_h.values
        f, gl, ga = feed_schedule(m, g)
        F[i, :n - 1], G[i, :n - 1], Ga[i, :n - 1] = f, gl, ga
        T[i, :n - 1] = g.temperature.values[:-1]
        v0 = g.viability.iloc[0]; x0 = g.VCD.iloc[0]
        g0 = g.glucose.iloc[0] if not np.isnan(g.glucose.iloc[0]) else 8.0   # D2 medium starts at 8 g/L
        y0[i] = [x0, x0 * (100 - v0) / v0, g0, LAC0, 0.0, 0.0, 1.0, 1.0, 0.0]
        obs[i, :n] = g[OUT].values
    return dict(y0=y0, B=B, feed=F, glc=G, gal=Ga, T=T, run_ids=list(run_ids)), obs
