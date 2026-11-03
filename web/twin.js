// Browser port of dtwin (mechanistic core + GBM rate corrections + calibrated band). Mirrors dtwin/mech.py and dtwin/twin.py.
(function (root) {
  "use strict";
  const OUT = ["VCD", "viability", "glucose", "lactate", "titer"];
  const TR = [x => Math.log(Math.max(x, 0) + 0.1), v => { const c = Math.min(Math.max(v, 0.5), 99.5); return Math.log(c / (100 - c)); },
    x => Math.log(Math.max(x, 0) + 0.2), x => Math.log(Math.max(x, 0) + 0.1), x => Math.log(Math.max(x, 0) + 20)];
  const INV = [z => Math.exp(z) - 0.1, z => 100 / (1 + Math.exp(-z)), z => Math.exp(z) - 0.2, z => Math.exp(z) - 0.1, z => Math.exp(z) - 20];
  const RECIPES = { "STD": [48, 5.0, 8.0, false], "STD+": [48, 5.0, 8.0, true], "LoG": [48, 5.0, 4.0, false], "LoG+": [48, 5.0, 4.0, true],
    "HiF": [24, 2.5, 4.0, false], "HIP": [24, 2.5, 2.0, false], "HIP+": [24, 2.5, 2.0, true] };

  function protocol(name, days) {
    days = days || 11; const c = RECIPES[name]; const steps = []; let k = 0;
    for (let d = 0; d < days; d++) {
      const fed = d >= 3 && (c[0] === 24 || d % 2 === 1);
      const gal = c[3] && fed && k % 2 === 0;
      steps.push({ feed_pct: fed ? c[1] : 0, glucose_target: fed ? c[2] : null, galplus: !!gal, temperature: 37.0 });
      if (fed) k++;
    }
    return steps;
  }

  function envFactors(pH, DO, p) {
    let fmu = 1, flac = 1;
    if (pH != null && pH !== "" && !isNaN(+pH)) { fmu *= Math.exp(-Math.pow((+pH - p.pH_ref) / p.pH_sd, 2)); flac *= Math.exp(p.pH_lac * (+pH - p.pH_ref)); }
    if (DO != null && DO !== "" && !isNaN(+DO)) {
      const d = Math.min(Math.max(+DO, 0.5), 100), h = x => Math.pow(x, p.DO_n) / (Math.pow(p.K_DO, p.DO_n) + Math.pow(x, p.DO_n));
      fmu *= Math.min(h(d) / h(p.DO_ref), 1);
      flac *= Math.max((1 + p.DO_lac * (1 - h(d))) / (1 + p.DO_lac * (1 - h(p.DO_ref))), 1);
    }
    return [fmu, flac];
  }

  function rhs(t, y, T, p, c, env) {
    const Xv = Math.max(y[0], 0), Xd = Math.max(y[1], 0), G = Math.max(y[2], 0), L = Math.max(y[3], 0), Ga = Math.max(y[5], 0),
      N = Math.max(y[7], 0), Dm = Math.max(y[8], 0);
    const fT = Math.exp(-p.kT_mu * (37 - T)), Q = Math.pow(p.Q10, (T - 37) / 10);
    const fmu = env ? env[0] : 1, flac = env ? env[1] : 1;
    const mu_n = p.mu_max * fT * fmu * G / (p.Kg + G) * N / (p.Kn + N) * Math.max(1 - Xv / p.Xmax, 0);
    const energy = G + p.wl * L + Ga + p.eN * N;
    const starv = p.Ks * p.Ks / (p.Ks * p.Ks + energy * energy);
    const a6 = Math.pow(t / p.t50, 6), h4 = Math.pow(Dm, 4) / (Math.pow(p.Kdm, 4) + Math.pow(Dm, 4));
    let kd = Q * (p.kd0 + p.kd_starv * h4 + p.kd_age * a6 / (1 + a6));
    const mu = mu_n * c[0]; kd *= c[1];
    const qG = Q * (mu / p.Yxg + p.mg) * G / (p.Kgu + G) * (1 + p.kgo * G) * c[2];
    const sw = Math.max(p.Ksw / (p.Ksw + G), 1 - mu_n / (p.mu_max * fT * fmu));
    const qLp = p.Ylg * qG * (1 - sw) * c[3] * flac;
    const qLc = p.qLc * L / (0.05 + L) * sw * (1 + p.cT_lac * (37 - T)) / c[3];
    const qGa = p.qGal * Ga / (0.05 + Ga) * p.Ksw / (p.Ksw + G);
    const qP = Math.max(p.qP0 + p.aP * mu_n / p.mu_max, 0) * (1 + p.kT_qP * (37 - T)) * (1 + p.kGP * G / (2 + G)) * c[4];
    return [(mu - kd) * Xv, kd * Xv - p.klys * Math.max(y[1], 0), -qG * Xv, (qLp - qLc) * Xv, qP * Xv, -qGa * Xv, 0, -p.yn * mu * Xv,
      starv - p.kr * Dm * (1 - starv)];
  }

  function predictTree(M, x) {
    let s = M.base;
    for (let r = 0; r < M.roots.length; r++) {
      let i = M.roots[r];
      while (M.f[i] >= 0) i = x[M.f[i]] <= M.th[i] ? M.l[i] : M.r[i];
      s += M.th[i];
    }
    return s;
  }

  function corrections(model, y, t, feed, glc, gal) {
    const via = 100 * y[0] / Math.max(y[0] + y[1], 1e-9);
    const x = [y[0], via, y[2], y[3], y[4], y[7], y[8], t, feed, glc == null ? -1 : glc, gal];
    return model.models.map(M => Math.exp(Math.min(Math.max(predictTree(M, x), -0.7), 0.7)));
  }

  // core: boundaries in hours (sample times or day starts); inputs act right after each boundary
  // opts.theta: run-specific multipliers on the 5 corrected rates (growth, death, glucose uptake, lactate, productivity)
  // opts.y0: full 9-element start state (for forecasting from the middle of a run); opts.bandFrom: hour the band starts from
  function core(model, boundsH, steps, initial, useML, opts) {
    const p = model.params, dt = 0.5;
    opts = opts || {}; initial = initial || {};
    const theta = opts.theta || [1, 1, 1, 1, 1], t0b = opts.bandFrom || 0;
    const x0 = initial.VCD ?? 0.4, v0 = initial.viability ?? 97.5;
    let y = opts.y0 ? opts.y0.slice() : [x0, x0 * (100 - v0) / v0, initial.glucose ?? 8.0, initial.lactate ?? 0.15, initial.titer ?? 0, 0, 1, 1, 0];
    const Bi = boundsH.map(t => Math.round(t / dt)), states = [];
    for (let s = 0; s < Bi.length; s++) {
      states.push(y.slice());
      if (s === Bi.length - 1) break;
      const st = steps[s] || {}, feed = +st.feed_pct || 0;
      const glc = (st.glucose_target == null || st.glucose_target === "" || isNaN(+st.glucose_target) || +st.glucose_target === 0) ? null : +st.glucose_target;
      const gal = st.galplus ? model.gal : 0, T = (st.temperature == null || st.temperature === "" || isNaN(+st.temperature)) ? 37 : +st.temperature;
      const f = 1 + feed / 100; y = y.slice(); y[6] *= f;
      [0, 1, 2, 3, 4, 5, 7].forEach(i => { y[i] /= f; });
      y[7] += (feed / 100) * p.Nfeed / f;
      if (glc != null) y[2] = Math.max(y[2], glc);
      y[5] += gal;
      const c = (useML ? corrections(model, y, Bi[s] * dt, feed, glc, gal) : [1, 1, 1, 1, 1]).map((v, i) => v * theta[i]);
      const env = envFactors(st.pH, st.DO, p);
      for (let i = Bi[s]; i < Bi[s + 1]; i++) {
        const t = i * dt;
        const k1 = rhs(t, y, T, p, c, env), y2 = y.map((v, j) => v + dt / 2 * k1[j]);
        const k2 = rhs(t + dt / 2, y2, T, p, c, env), y3 = y.map((v, j) => v + dt / 2 * k2[j]);
        const k3 = rhs(t + dt / 2, y3, T, p, c, env), y4 = y.map((v, j) => v + dt * k3[j]);
        const k4 = rhs(t + dt, y4, T, p, c, env);
        y = y.map((v, j) => Math.max(v + dt / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]), 0));
      }
    }
    const rows = states.map((yy, s) => {
      const day = boundsH[s] / 24, r = { day: day, time_h: boundsH[s] }, ahead = Math.max(boundsH[s] - t0b, 0) / 24;
      const out = [yy[0], 100 * yy[0] / Math.max(yy[0] + yy[1], 1e-9), yy[2], yy[3], yy[4]];
      OUT.forEach((v, k) => {
        const w = model.band[v] * Math.sqrt(ahead); r[v] = out[k];
        if (v === "lactate" && model.band.lactate_abs != null) {          // lactate band in g/L (log band overstated it)
          const a = model.band.lactate_abs * Math.min(1, Math.sqrt(ahead / 3));
          r.lactate_lo = Math.max(out[k] - a, 0); r.lactate_hi = out[k] + a; return;
        }
        r[v + "_lo"] = Math.max(INV[k](TR[k](out[k]) - w), 0);
        r[v + "_hi"] = v === "viability" ? Math.min(INV[k](TR[k](out[k]) + w), 100) : INV[k](TR[k](out[k]) + w);
      });
      return r;
    });
    rows.states = states;
    return rows;
  }

  function supportOf(st) {
    const f = +st.feed_pct || 0, g = st.glucose_target, T = (st.temperature == null || st.temperature === "") ? 37 : +st.temperature;
    if (f > 5 || (g != null && g !== "" && +g !== 0 && (+g < 2 || +g > 8))) return "extrapol";
    if (Math.abs(T - 37) > 0.25) return "prior";
    if ((st.pH != null && st.pH !== "" && Math.abs(+st.pH - 7.0) > 0.05) || (st.DO != null && st.DO !== "" && +st.DO < 25)) return "prior";
    return "data";
  }

  function simulate(model, steps, initial, opts) {
    opts = opts || {}; const stepH = opts.stepH || 24;
    const rows = core(model, steps.map((_, s) => s * stepH).concat([steps.length * stepH]), steps, initial, opts.mode !== "mechanistic");
    const support = steps.map(supportOf);
    let ivcd = 0;
    for (let i = 1; i < rows.length; i++) ivcd += (rows[i].day - rows[i - 1].day) * (rows[i].VCD + rows[i - 1].VCD) / 2;
    const last = rows[rows.length - 1];
    const kpi = { titer: last.titer, titer_lo: last.titer_lo, titer_hi: last.titer_hi, peakVCD: Math.max(...rows.map(r => r.VCD)), ivcd: ivcd,
      viability: last.viability, viability_lo: last.viability_lo, viability_hi: last.viability_hi,
      peakLactate: Math.max(...rows.map(r => r.lactate)),
      nData: support.filter(s => s === "data").length, nPrior: support.filter(s => s === "prior").length, nExtrapol: support.filter(s => s === "extrapol").length };
    return { rows: rows, support: support, kpi: kpi };
  }

  // predict a real batch from its own sample times and inputs (predict-first)
  function simulateBatch(model, samples) {
    const t = samples.map(r => r.time_h), first = samples[0];
    const init = { VCD: first.VCD, viability: first.viability ?? 97, glucose: first.glucose ?? 8, lactate: first.lactate ?? 0.15, titer: first.titer ?? 0 };
    const steps = samples.slice(0, -1).map(r => ({ feed_pct: r.feed_pct, glucose_target: r.glucose_target, galplus: !!r.galplus, temperature: r.temperature, pH: r.pH, DO: r.DO }));
    return { rows: core(model, t, steps, init, true), support: steps.map(supportOf) };
  }

  // error metrics as in the pipeline (MAPE for VCD > 1 and titer > 50; MAE otherwise; day-10 titer by interpolation)
  function errors(rows, samples) {
    const res = {};
    const pick = (v) => samples.map((s, i) => [rows[i][v], s[v]]).slice(1).filter(p => p[1] != null && !isNaN(p[1]));
    [["VCD", 1.0], ["titer", 50]].forEach(([v, th]) => { const q = pick(v).filter(p => p[1] > th); res[v + "_MAPE_%"] = q.length ? 100 * q.reduce((a, p) => a + Math.abs(p[0] - p[1]) / p[1], 0) / q.length : null; });
    ["viability", "glucose", "lactate"].forEach(v => { const q = pick(v); res[v + "_MAE"] = q.length ? q.reduce((a, p) => a + Math.abs(p[0] - p[1]), 0) / q.length : null; });
    const ok = samples.map((s, i) => [s.time_h, s.titer, rows[i].titer]).filter(p => p[1] != null && !isNaN(p[1]));
    if (ok.length >= 2 && ok[ok.length - 1][0] >= 240) {
      const interp = (k) => { for (let i = 1; i < ok.length; i++) if (ok[i][0] >= 240) { const a = ok[i - 1], b = ok[i], w = (240 - a[0]) / (b[0] - a[0]); return a[k] + w * (b[k] - a[k]); } };
      res["titer_d10_APE_%"] = Math.abs(interp(2) / interp(1) - 1) * 100;
    } else res["titer_d10_APE_%"] = null;
    return res;
  }

  // ================= running batch: self-adjustment to the data so far, forecast from today, input suggestions
  // past: [{day, VCD, viability, glucose, lactate, titer}] measured at day boundaries 0..k (null = not measured)
  // steps: inputs for every day 0..n-1 (past days = what was done; future days = the plan)
  const LSIG = [0.10, 0.30, 0.15, 0.20, 0.10];
  // Back-test on the 6 benchmark runs (data to day 4-7): fitting all 5 factors overfits 3-4 samples and worsens forecasts;
  // re-anchoring to today plus ONE growth factor (prior sd 0.1) gave the lowest titer error. So only growth is calibrated.
  const CAL = { priorSd: [0.1, 0.25, 0.25, 0.25, 0.1], free: [true, false, false, false, false] };
  function lres(model, past, steps, logth) {
    const k = past.length - 1, bounds = past.map((_, i) => i * 24);
    const init = { VCD: past[0].VCD ?? 0.4, viability: past[0].viability ?? 97.5, glucose: past[0].glucose ?? 8, lactate: past[0].lactate ?? 0.15, titer: past[0].titer ?? 0 };
    const rows = core(model, bounds, steps.slice(0, k), init, true, { theta: logth.map(Math.exp) });
    const r = [];
    for (let i = 1; i <= k; i++) OUT.forEach((v, j) => { const m = past[i][v]; if (m != null && !isNaN(m) && !(v === "titer" && m < 20)) r.push((TR[j](rows[i][v]) - TR[j](m)) / LSIG[j]); });
    logth.forEach((x, j) => { if (CAL.free[j]) r.push(x / CAL.priorSd[j]); });   // pulls each factor toward 1 when the data say little
    return { r, rows };
  }
  function calibrate(model, past, steps) {
    let th = [0, 0, 0, 0, 0];
    if (past.length < 3) return { theta: th.map(Math.exp), rows: lres(model, past, steps, th).rows };
    let cur = lres(model, past, steps, th), lam = 1e-2;
    const cost = r => r.reduce((a, b) => a + b * b, 0);
    for (let it = 0; it < 12; it++) {
      const J = th.map((_, j) => { if (!CAL.free[j]) return cur.r.map(() => 0); const t2 = th.slice(); t2[j] += 1e-3; const r2 = lres(model, past, steps, t2).r; return r2.map((v, i) => (v - cur.r[i]) / 1e-3); });
      const A = th.map((_, a) => th.map((_, b) => J[a].reduce((s, v, i) => s + v * J[b][i], 0) + (a === b ? lam + (CAL.free[a] ? 0 : 1e6) : 0)));
      const g = th.map((_, a) => -J[a].reduce((s, v, i) => s + v * cur.r[i], 0));
      const d = solve(A, g), cand = th.map((v, j) => Math.max(Math.min(v + d[j], 0.7), -0.7));
      const nx = lres(model, past, steps, cand);
      if (cost(nx.r) < cost(cur.r)) { th = cand; cur = nx; lam = Math.max(lam / 3, 1e-4); if (d.every(x => Math.abs(x) < 1e-3)) break; } else lam *= 5;
    }
    return { theta: th.map(Math.exp), rows: cur.rows };
  }
  function solve(A, b) {
    const n = b.length, M = A.map((row, i) => row.concat([b[i]]));
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      [M[c], M[p]] = [M[p], M[c]];
      for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
    }
    return M.map((row, i) => row[n] / row[i]);
  }
  // forecast: calibrate on days 0..k, take the state at day k, replace what was measured that day, run the plan to the end
  function liveForecast(model, past, steps, opts) {
    opts = opts || {};
    const k = past.length - 1, n = steps.length;
    const cal = opts.theta ? { theta: opts.theta, rows: null } : calibrate(model, past, steps);
    const init = { VCD: past[0].VCD ?? 0.4, viability: past[0].viability ?? 97.5, glucose: past[0].glucose ?? 8, lactate: past[0].lactate ?? 0.15, titer: past[0].titer ?? 0 };
    const hist = cal.rows || core(model, past.map((_, i) => i * 24), steps.slice(0, k), init, true, { theta: cal.theta });
    const y = hist.states[k].slice(), m = past[k];
    if (m.VCD != null && !isNaN(m.VCD)) { const dead = y[0] > 0 ? y[1] / y[0] : 0; y[0] = m.VCD; y[1] = m.viability != null ? m.VCD * (100 - m.viability) / Math.max(m.viability, 0.5) : m.VCD * dead; }
    else if (m.viability != null) y[1] = y[0] * (100 - m.viability) / Math.max(m.viability, 0.5);
    if (m.glucose != null && !isNaN(m.glucose)) y[2] = m.glucose;
    if (m.lactate != null && !isNaN(m.lactate)) y[3] = m.lactate;
    if (m.titer != null && !isNaN(m.titer) && m.titer >= 20) y[4] = m.titer;
    const fut = core(model, Array.from({ length: n - k + 1 }, (_, i) => (k + i) * 24), steps.slice(k), {}, true, { theta: cal.theta, y0: y, bandFrom: k * 24 });
    const rows = hist.slice(0, k).map(r => { const q = Object.assign({}, r); OUT.forEach(v => { q[v + "_lo"] = q[v]; q[v + "_hi"] = q[v]; }); q.fit = true; return q; }).concat(fut);
    const support = steps.map((st, d) => d < k ? "done" : supportOf(st));
    let ivcd = 0; for (let i = 1; i < rows.length; i++) ivcd += (rows[i].day - rows[i - 1].day) * (rows[i].VCD + rows[i - 1].VCD) / 2;
    const last = rows[rows.length - 1], fs = support.slice(k);
    // fit quality on the measured days (titer % and VCD %)
    const fe = v => { const q = past.slice(1).map((pp, i) => [hist[i + 1][v], pp[v]]).filter(x => x[1] != null && x[1] > (v === "titer" ? 50 : 1)); return q.length ? 100 * q.reduce((a, x) => a + Math.abs(x[0] - x[1]) / x[1], 0) / q.length : null; };
    const kpi = { titer: last.titer, titer_lo: last.titer_lo, titer_hi: last.titer_hi, peakVCD: Math.max(...rows.map(r => r.VCD)), ivcd,
      viability: last.viability, viability_lo: last.viability_lo, viability_hi: last.viability_hi, peakLactate: Math.max(...rows.map(r => r.lactate)),
      nData: fs.filter(s => s === "data").length, nPrior: fs.filter(s => s === "prior").length, nExtrapol: fs.filter(s => s === "extrapol").length, nDone: k };
    return { rows, support, kpi, theta: cal.theta, k, fitErr: { titer: fe("titer"), VCD: fe("VCD") } };
  }
  // suggest future inputs: search feeding regime, glucose target, Gal+ and (optionally) a temperature shift; maximise final titer
  function suggest(model, past, steps, opts) {
    opts = opts || {};
    const k = past.length - 1, n = steps.length, minVia = opts.minViability ?? 80, allowT = !!opts.allowTemperature;
    const cal = calibrate(model, past, steps);
    const cands = [];
    const regimes = [{ id: "48h", every: 2, vol: 5.0 }, { id: "24h", every: 1, vol: 2.5 }];
    const shifts = [null]; if (allowT) for (const T of [33, 34, 35]) for (let d = Math.max(k, 3); d <= n - 3; d++) shifts.push({ T, d });
    for (const rg of regimes) for (const g of [2, 3, 4, 5, 6, 7, 8]) for (const gal of [false, true]) for (const sh of shifts) {
      const st = steps.map((s, d) => {
        if (d < k) return s;
        const fed = d >= 3 && (rg.every === 1 || d % 2 === 1);
        return { feed_pct: fed ? rg.vol : 0, glucose_target: fed ? g : null, galplus: gal && fed && (rg.every === 2 || d % 2 === 1), temperature: sh && d >= sh.d ? sh.T : 37, pH: s.pH, DO: s.DO };
      });
      const f = liveForecast(model, past, st, { theta: cal.theta });
      if (f.kpi.viability < minVia) continue;
      cands.push({ steps: st, titer: f.kpi.titer, viability: f.kpi.viability, lo: f.kpi.titer_lo, hi: f.kpi.titer_hi, regime: rg.id, glucose: g, gal, shift: sh,
        basis: f.kpi.nExtrapol ? "extrapol" : f.kpi.nPrior ? "prior" : "data" });
    }
    cands.sort((a, b) => b.titer - a.titer);
    const out = [], seen = new Set();               // keep options that differ in kind, not only by a small tweak
    for (const c of cands) { const key = c.regime + (c.shift ? "T" : "") + (c.gal ? "G" : ""); if (seen.has(key)) continue; seen.add(key); out.push(c); if (out.length === 3) break; }
    const now = liveForecast(model, past, steps, { theta: cal.theta });
    return { options: out, current: now.kpi, tried: cands.length, theta: cal.theta };
  }

  root.Twin = { protocol: protocol, simulate: simulate, simulateBatch: simulateBatch, errors: errors, liveForecast: liveForecast, suggest: suggest, calibrate: calibrate, RECIPES: RECIPES, OUT: OUT, CAL: CAL };
  if (typeof module !== "undefined") module.exports = root.Twin;
})(typeof window !== "undefined" ? window : globalThis);
