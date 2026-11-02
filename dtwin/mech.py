"""Mechanistic core of the CHO fed-batch twin (NISTCHO, D2 process).

A run is a sequence of SEGMENTS (steps). At the start of each segment the operator inputs are
applied as an event (feed volume, glucose top-up, galactose), then the culture is integrated
until the next boundary at the segment's temperature. This is what lets a user set inputs at
every step: a sampling interval in the data, or one day in a what-if scenario.

State y = [Xv, Xd, Glc, Lac, P, Gal, V, N, Dm]
  Xv, Xd : viable / dead cells (1e6 cells/mL)     Glc, Lac, Gal : g/L
  P      : titer (mg/L)                            V : relative volume (start = 1)
  N      : amino-acid pool (basal medium = 1)      Dm: starvation damage (h of starvation, decays when fed)
Segment inputs: feed_pct (% v/v), glc_after (g/L, NaN = no top-up), gal (g/L added), T (degC)
"""
import numpy as np

GAL_PER_EVENT = 1.25 * 180.16 / 1000          # 1.25 mM galactose in g/L
# fitted parameters (log-scale bounds) ---------------------------------------------------
PARAMS = {  # name: (initial, low, high)
    "mu_max": (0.035, 0.01, 0.08),    # 1/h
    "Kg": (0.3, 0.01, 3.0),           # g/L
    "Xmax": (28.0, 15.0, 60.0),       # 1e6 cells/mL, crowding capacity
    "kd0": (5e-4, 1e-5, 5e-3),        # 1/h basal death
    "kd_starv": (0.05, 0.005, 0.4),   # 1/h max starvation death
    "Ks": (0.15, 0.01, 1.5),          # g/L energy level of half-maximal starvation death
    "kd_age": (0.004, 1e-4, 0.03),    # 1/h max culture-ageing death
    "t50": (240.0, 150.0, 400.0),     # h
    "klys": (2e-3, 1e-4, 0.03),       # 1/h lysis of dead cells
    "Yxg": (3.0, 0.5, 15.0),          # 1e6 cells/mL per g/L glucose
    "mg": (0.005, 5e-4, 0.03),        # g/L/h per 1e6 cells/mL, maintenance uptake
    "Kgu": (0.5, 0.02, 5.0),          # g/L uptake half-saturation
    "Ylg": (0.5, 0.05, 1.2),          # g lactate per g glucose (overflow)
    "qLc": (0.004, 2e-4, 0.03),       # g/L/h per 1e6 cells/mL, max lactate consumption
    "Ksw": (0.5, 0.05, 5.0),          # g/L glucose level of the lactate-consumption switch
    "qGal": (0.002, 1e-4, 0.02),      # g/L/h per 1e6 cells/mL
    "wl": (0.5, 0.05, 2.0),           # energy weight of lactate in starvation term
    "qP0": (0.55, 0.1, 1.5),          # pg/cell/h basal productivity
    "Kn": (0.1, 0.005, 1.0),          # amino-acid pool half-saturation (relative)
    "yn": (0.03, 0.002, 0.3),         # pool consumed per 1e6 cells/mL grown
    "Nfeed": (8.0, 1.0, 40.0),        # pool concentration in feed (relative to basal medium)
    "eN": (0.5, 0.01, 5.0),           # energy equivalent of the pool (g/L glucose per unit)
    "kr": (0.05, 0.005, 0.5),         # 1/h recovery from starvation damage when fed
    "Kdm": (10.0, 1.0, 50.0),         # h of accumulated starvation at half-maximal death
    "kgo": (0.1, 0.001, 1.0),         # 1/(g/L): glucose uptake rises with glucose level (overflow)
    "kGP": (0.3, 0.01, 2.0),          # qP gain at high glucose (x(1 + kGP G/(2+G)))
}
LINEAR = {"aP": (0.0, -0.8, 0.8)}     # pg/cell/h growth-associated productivity (can be <0)
# temperature priors (not fitted: no T variation in D2) -----------------------------------
PRIOR = dict(kT_mu=0.14,   # growth x exp(-0.14 (37-T)): growth at 33 C ~57% (lit. 47-67%; Trummer 2006, Hwang 2011)
             kT_qP=0.08,   # qP x (1 + 0.08 (37-T)): +36% at 32.5 C (D3 pair +46% at -4.5 C)
             cT_lac=0.15,  # lactate consumption x (1 + 0.15 (37-T)) (D3 pair: switch to consumption)
             Q10=2.0)      # death and uptake

NAMES = list(PARAMS) + list(LINEAR)


def default_params():
    p = {k: v[0] for k, v in PARAMS.items()}; p.update({k: v[0] for k, v in LINEAR.items()}); p.update(PRIOR)
    return p


def rhs(t, y, T, p, c):
    """Vectorised over runs. c = (R,5) multiplicative corrections on mu, kd, qGlc, lactate balance, qP."""
    Xv, Xd, G, L, P, Ga, V, N, Dm = [np.maximum(y[:, i], 0) for i in range(9)]
    fT = np.exp(-p["kT_mu"] * (37 - T)); Q = p["Q10"] ** ((T - 37) / 10)
    mu_n = p["mu_max"] * fT * G / (p["Kg"] + G) * N / (p["Kn"] + N) * np.clip(1 - Xv / p["Xmax"], 0, None)
    energy = G + p["wl"] * L + Ga + p["eN"] * N
    starv = p["Ks"] ** 2 / (p["Ks"] ** 2 + energy ** 2)
    a6 = (t / p["t50"]) ** 6
    h4 = Dm ** 4 / (p["Kdm"] ** 4 + Dm ** 4)
    kd = Q * (p["kd0"] + p["kd_starv"] * h4 + p["kd_age"] * a6 / (1 + a6))
    mu = mu_n * c[:, 0]; kd = kd * c[:, 1]
    qG = Q * (mu / p["Yxg"] + p["mg"]) * G / (p["Kgu"] + G) * (1 + p["kgo"] * G) * c[:, 2]
    sw = np.maximum(p["Ksw"] / (p["Ksw"] + G), 1 - mu_n / (p["mu_max"] * fT))
    qLp = p["Ylg"] * qG * (1 - sw) * c[:, 3]
    qLc = p["qLc"] * L / (0.05 + L) * sw * (1 + p["cT_lac"] * (37 - T)) / c[:, 3]
    qGa = p["qGal"] * Ga / (0.05 + Ga) * p["Ksw"] / (p["Ksw"] + G)
    qP = (np.maximum(p["qP0"] + p["aP"] * mu_n / p["mu_max"], 0) * (1 + p["kT_qP"] * (37 - T))
          * (1 + p["kGP"] * G / (2 + G)) * c[:, 4])
    d = np.zeros_like(y)
    d[:, 0] = (mu - kd) * Xv; d[:, 1] = kd * Xv - p["klys"] * Xd
    d[:, 2] = -qG * Xv; d[:, 3] = (qLp - qLc) * Xv; d[:, 4] = qP * Xv; d[:, 5] = -qGa * Xv
    d[:, 7] = -p["yn"] * mu * Xv
    d[:, 8] = starv - p["kr"] * Dm * (1 - starv)
    return d


def apply_event(y, feed, glc_after, gal, nfeed=8.0):
    y = y.copy(); f = 1 + feed / 100
    y[:, 6] *= f
    for i in (0, 1, 2, 3, 4, 5, 7):
        y[:, i] /= f
    y[:, 7] += (feed / 100) * nfeed / f
    top = ~np.isnan(glc_after)
    y[top, 2] = np.maximum(y[top, 2], glc_after[top])
    y[:, 5] += gal
    return y


def simulate(p, batch, dt=0.5, corr=None, corr_fn=None):
    """batch: dict y0 (R,7); B (R,J+1) boundary times in h (NaN padded); feed, glc, gal, T (R,J).
    corr: (R,J,5) fixed corrections, or corr_fn(seg, y, t, batch, idx) -> (len(idx),5) chosen online.
    Returns states at every boundary BEFORE that boundary's event: (R, J+1, 7)."""
    y0 = batch["y0"]; R = len(y0)
    Bi = np.round(batch["B"] / dt)
    J = batch["feed"].shape[1]
    nseg = (~np.isnan(batch["B"])).sum(1) - 1
    endi = np.nanmax(Bi, 1).astype(int)
    Bi = np.nan_to_num(Bi, nan=1e9).astype(np.int64)
    Nf = np.broadcast_to(np.asarray(p["Nfeed"], float), (R,))
    out = np.full((R, J + 1, 9), np.nan)
    y = y0.astype(float).copy(); ptr = np.zeros(R, int); cur = np.zeros(R, int)
    c = np.ones((R, 5)); ar = np.arange(R)
    for i in range(endi.max() + 1):
        hit = Bi[ar, np.minimum(ptr, J)] == i
        if hit.any():
            h = ar[hit]; out[h, ptr[h]] = y[h]
            ev = h[ptr[h] < nseg[h]]
            if len(ev):
                s = ptr[ev]
                y[ev] = apply_event(y[ev], batch["feed"][ev, s], batch["glc"][ev, s], batch["gal"][ev, s], Nf[ev])
                cur[ev] = s
                if corr is not None:
                    c[ev] = corr[ev, s]
                elif corr_fn is not None:
                    c[ev] = corr_fn(s, y[ev], i * dt, batch, ev)
            ptr[h] += 1
        act = (i < endi) & (i >= Bi[:, 0])
        if not act.any():
            break
        T = batch["T"][ar, cur]; t = i * dt
        k1 = rhs(t, y, T, p, c); k2 = rhs(t + dt / 2, y + dt / 2 * k1, T, p, c)
        k3 = rhs(t + dt / 2, y + dt / 2 * k2, T, p, c); k4 = rhs(t + dt, y + dt * k3, T, p, c)
        y = np.where(act[:, None], np.maximum(y + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4), 0), y)
    return out


def observe(states):
    """Map states to measured outputs: VCD, viability %, glucose, lactate, titer."""
    Xv, Xd = states[..., 0], states[..., 1]
    via = 100 * Xv / np.maximum(Xv + Xd, 1e-9)
    return np.stack([Xv, via, states[..., 2], states[..., 3], states[..., 4]], -1)


OUT = ["VCD", "viability", "glucose", "lactate", "titer"]
