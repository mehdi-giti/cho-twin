"""Digital twin engine: set inputs at every step, get predicted outputs.

    from dtwin.twin import Twin
    tw = Twin()                                   # hybrid (mechanistic + ML corrections), 5-member ensemble
    steps = Twin.protocol("STD")                  # or build your own list, one dict per day
    steps[5]["temperature"] = 33.0                # change any input at any step
    df, kpi = tw.simulate(steps, initial=dict(VCD=0.4, viability=97, glucose=8))

Each step (default 24 h) = dict(feed_pct, glucose_target, galplus, temperature).
Output: one row per step boundary with median and p10/p90 for VCD, viability, glucose, lactate,
titer, plus a 'support' flag per step:
  data      inputs inside the range of the real D2 runs
  prior     temperature != 37 C: effect from literature + D3 temperature pair, not D2 data
  extrapol  feed or glucose target outside what the real runs covered
"""
import json, pickle, os
import numpy as np, pandas as pd
from . import mech

HERE = os.path.dirname(__file__)
TR = [lambda x: np.log(np.maximum(x, 0) + 0.1), lambda v: np.log(np.clip(v, 0.5, 99.5) / (100 - np.clip(v, 0.5, 99.5))),
      lambda x: np.log(np.maximum(x, 0) + 0.2), lambda x: np.log(np.maximum(x, 0) + 0.1), lambda x: np.log(np.maximum(x, 0) + 20)]
INV = [lambda z: np.exp(z) - 0.1, lambda z: 100 / (1 + np.exp(-z)), lambda z: np.exp(z) - 0.2,
       lambda z: np.exp(z) - 0.1, lambda z: np.exp(z) - 20]
SUPPORT = dict(feed_pct=(0.0, 5.0), glucose_target=(2.0, 8.0), temperature=(37.0, 37.0))


def _feats(y, t, feed, glc, gal):
    via = 100 * y[:, 0] / np.maximum(y[:, 0] + y[:, 1], 1e-9)
    return np.column_stack([y[:, 0], via, y[:, 2], y[:, 3], y[:, 4], y[:, 7], y[:, 8], t, feed,
                            np.nan_to_num(glc, nan=-1.0), gal])


class Twin:
    def __init__(self, mode="hybrid"):
        self.p = mech.default_params(); self.p.update(json.load(open(os.path.join(HERE, "mech_params.json"))))
        self.mode = mode
        self.ens = pickle.load(open(os.path.join(HERE, "ensemble.pkl"), "rb")) if mode == "hybrid" else []

    @staticmethod
    def protocol(name="STD", days=11):
        """Real D2 strategies as editable step lists (feed after the daily sample, from day 3)."""
        cfg = {"STD": (48, 5.0, 8.0, False), "STD+": (48, 5.0, 8.0, True), "LoG": (48, 5.0, 4.0, False),
               "LoG+": (48, 5.0, 4.0, True), "HiF": (24, 2.5, 4.0, False), "HIP": (24, 2.5, 2.0, False)}[name]
        steps, k = [], 0
        for d in range(days):
            fed = d >= 3 and (cfg[0] == 24 or d % 2 == 1)
            gal = cfg[3] and fed and k % 2 == 0
            steps.append(dict(feed_pct=cfg[1] if fed else 0.0, glucose_target=cfg[2] if fed else None,
                              galplus=bool(gal), temperature=37.0))
            k += fed
        return steps

    def _batch(self, steps, initial, step_h):
        n = len(steps)
        B = np.arange(n + 1, dtype=float)[None] * step_h
        feed = np.array([[s.get("feed_pct", 0.0) or 0.0 for s in steps]])
        glc = np.array([[np.nan if s.get("glucose_target") in (None, 0) else float(s["glucose_target"]) for s in steps]])
        gal = np.array([[mech.GAL_PER_EVENT if s.get("galplus") else 0.0 for s in steps]])
        T = np.array([[float(s.get("temperature", 37.0)) for s in steps]])
        x0 = initial.get("VCD", 0.4); v0 = initial.get("viability", 97.0)
        y0 = np.array([[x0, x0 * (100 - v0) / v0, initial.get("glucose", 8.0), initial.get("lactate", 0.15),
                        initial.get("titer", 0.0), 0.0, 1.0, 1.0, 0.0]])
        return dict(y0=y0, B=B, feed=feed, glc=glc, gal=gal, T=T)

    def simulate(self, steps, initial=None, step_h=24.0):
        initial = initial or {}
        b = self._batch(steps, initial, step_h)
        runs = []
        if self.mode == "mechanistic" or not self.ens:
            runs.append(mech.observe(mech.simulate(self.p, b))[0])
        else:
            for models in self.ens:
                def fn(s, y, t, batch, idx, models=models):
                    X = _feats(y, np.full(len(y), t), batch["feed"][idx, s], batch["glc"][idx, s], batch["gal"][idx, s])
                    return np.exp(np.clip(np.column_stack([m.predict(X) for m in models]), -0.7, 0.7))
                runs.append(mech.observe(mech.simulate(self.p, b, corr_fn=fn))[0])
        A = np.stack(runs)                                    # members, steps+1, 5
        df = pd.DataFrame({"day": b["B"][0] / 24, "time_h": b["B"][0]})
        band = json.load(open(os.path.join(HERE, "band.json"))) if os.path.exists(os.path.join(HERE, "band.json")) else None
        for k, v in enumerate(mech.OUT):
            md = np.median(A[:, :, k], 0); df[v] = md
            lo, hi = np.percentile(A[:, :, k], 10, 0), np.percentile(A[:, :, k], 90, 0)
            if band:   # calibrated on real validation runs: grows with sqrt(days predicted ahead)
                w = band[v] * np.sqrt(df.time_h.values / 24)
                lo = np.minimum(lo, np.maximum(INV[k](TR[k](md) - w), 0)); hi = np.maximum(hi, INV[k](TR[k](md) + w))
                if v == "viability": hi = np.minimum(hi, 100)
            df[v + "_p10"] = lo; df[v + "_p90"] = hi
        sup = []
        for s in steps:
            T = float(s.get("temperature", 37.0)); f = s.get("feed_pct", 0) or 0; g = s.get("glucose_target")
            if f > SUPPORT["feed_pct"][1] or (g not in (None, 0) and not (2.0 <= g <= 8.0)):
                sup.append("extrapol")
            elif abs(T - 37.0) > 0.25:
                sup.append("prior")
            else:
                sup.append("data")
        df["support_next_step"] = sup + [""]
        df["inputs_feed_pct"] = list(b["feed"][0]) + [np.nan]
        df["inputs_glucose_target"] = list(b["glc"][0]) + [np.nan]
        df["inputs_galplus"] = [bool(s.get("galplus")) for s in steps] + [False]
        df["inputs_temperature"] = list(b["T"][0]) + [np.nan]
        ivcd = np.concatenate([[0], np.cumsum(np.diff(df.time_h) / 24 * (df.VCD.values[1:] + df.VCD.values[:-1]) / 2)])
        kpi = dict(final_titer=df.titer.iloc[-1], final_titer_p10=df.titer_p10.iloc[-1], final_titer_p90=df.titer_p90.iloc[-1],
                   peak_VCD=df.VCD.max(), IVCD=ivcd[-1], final_viability=df.viability.iloc[-1],
                   steps_data=sup.count("data"), steps_prior=sup.count("prior"), steps_extrapolated=sup.count("extrapol"))
        return df, kpi
