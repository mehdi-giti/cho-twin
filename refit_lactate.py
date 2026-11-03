"""Refit only the lactate parameters (overflow yield, consumption rate, switch level) with the ML corrections
in the loop, then retrain corrections and evaluate. Writes a candidate; promotion goes through the normal gates."""
import json, numpy as np, sys
from scipy.optimize import least_squares
from dtwin import pipeline as pl, mech

champ = pl.load_version(pl.champion()); df, idx = pl.load_store()
ids = idx[(idx.role == "train") & (idx.kind != "derived")].run_id.tolist()
b, o = pl.batch_from(df, ids)
KEYS = ["Ylg", "qLc", "Ksw"]
x0 = np.log([champ["P"][k] for k in KEYS])
lo = np.log([mech.PARAMS[k][1] for k in KEYS]); hi = np.log([mech.PARAMS[k][2] for k in KEYS])


def model_with(x):
    P = dict(champ["P"]); P.update({k: float(np.exp(v)) for k, v in zip(KEYS, x)}); return dict(champ, P=P)


def res(x):
    pr = pl.rollout(model_with(x), b)
    out = []
    for k, s in ((3, 0.15), (2, 0.5), (0, 1.5)):          # lactate (g/L) leads; glucose and VCD guard against side effects
        m = ~np.isnan(o[:, 1:, k]); out.append((pr[:, 1:, k][m] - o[:, 1:, k][m]) / s)
    return np.concatenate(out + [0.3 * (x - x0)])

r0 = res(x0); f = least_squares(res, x0, bounds=(lo + 1e-6, hi - 1e-6), diff_step=1e-2, max_nfev=40)
P = model_with(f.x)["P"]
print("lactate params:", {k: (round(champ["P"][k], 4), round(P[k], 4)) for k in KEYS}, "cost", round(0.5 * r0 @ r0, 1), "->", round(f.cost, 1))
json.dump({k: float(P[k]) for k in mech.NAMES + list(mech.PRIOR)}, open("/tmp/claude-0/-home-claude/99ea2342-4247-5ddd-93f4-c5127cc324a8/scratchpad/P_lac.json", "w"))
