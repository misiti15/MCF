"""GATE2-R (plan REWORK_PLAN.md, frozen 2026-11-09 22:15 ET before any score): GATE2 B1/B2 with the MX failed-hold exit
(flat at the next bar open once SPY is within +-0.15% of its open at a 5-min bar close) and MXH (MX + half size for
entries before 13:00, judged against a uniform size-cut control). C1m (matched random bar) uses the same exit.
Lineage N 127 -> BAR90 2.80. Re-uses gate2.py's top half verbatim (data, reading, trigger, costs).
    python gate2r.py > gate2r_out.txt        Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
src = (HERE / "gate2.py").read_text()
exec(compile(src[:src.index("rows, ALLT = [], []")], "gate2_top", "exec"))
N_R = 127; T90R = round(max(1.35, 0.9 * G.t_required(N_R)), 2)
RNG3 = np.random.default_rng(20261110)
DB = np.array([0.25, 0.5, 0.75, 1.0, 1.5]); I1300b = I[1300]
CONF = [("B1", "I-HB", .30, .60), ("B2", "I-HB", .30, .40)]


def trade_mx(a, s, ib, atr, spy_fo, mx):
    """as gate2.trade E1, plus (mx) exit at the next bar open after a bar close with |SPY fo| <= 0.15%.
    -> (net R, gross R, kind, R/ATR) or None."""
    j = ib + 1
    if j > I1555: return None
    e = float(a[j, 0]); stop = a[0, 0] - s * .10 * atr; R = s * (e - stop)
    if not np.isfinite(e) or R < .10 * atr: return None
    kind, xp = "time", float(a[I1555, 3])
    for i in range(j, I1555 + 1):
        o, h, l, c = a[i]
        if i > j and s * (o - stop) <= 0: kind, xp = "stop", float(o); break
        if (s > 0 and l <= stop) or (s < 0 and h >= stop): kind, xp = "stop", float(stop); break
        if mx and i < I1555 and abs(spy_fo[i]) <= .0015:
            kind, xp = "mx", float(a[i + 1, 0]); break
    mult = G.tod_cost_mult(np.array([END_TOD[ib]]))[0]
    cost = (G.SLIP_PS + e * G.SLIP_BPS) * mult + SPREAD_BPS * e * mult + G.SLIP_PS + e * G.SLIP_BPS + (G.STOP_EXTRA if kind == "stop" else 0)
    g = s * (xp - e) / R
    return g - cost / R, g, kind, R / atr


def tb(i): return (int(END_MIN[i]) - 570) // 30


rows = []
HBd = HB.groupby("date").symbol.apply(list).to_dict()
for tag, inst, X, RET in CONF:
    rd = reading(X); T = []
    for d, (s, ic) in rd.items():
        sa = PATH[("SPY", d)]; spy_fo = sa[:, 3] / sa[0, 0] - 1
        held = np.sign(SPYD.close[d] - SPYD.open[d]) == s
        for sym in HBd.get(d, []):
            a = PATH.get((sym, d)); atr = ATR.get((sym, d))
            if a is None or not atr or not np.isfinite(atr): continue
            ib = trigger(a, s, ic, atr, RET)
            if ib < 0: continue
            base = trade_mx(a, s, ib, atr, spy_fo, False); mxr = trade_mx(a, s, ib, atr, spy_fo, True)
            if base is None or mxr is None: continue
            o = a[0, 0]; dist = lambda b: np.searchsorted(DB, s * (a[b, 3] - o) / atr)
            mb = [b for b in range(ic + 1, I1430 + 1) if s * (a[b, 3] - o) > 0 and b != ib and dist(b) == dist(ib) and tb(b) == tb(ib)]
            cm = trade_mx(a, s, int(RNG3.choice(mb)), atr, spy_fo, True) if mb else None
            T.append(dict(date=d, held=held, w=0.5 if ib < I1300b else 1.0, base=base[0], r=mxr[0], g=mxr[1], kind=mxr[2],
                          ra=mxr[0] * mxr[3], cm=cm[0] if cm else np.nan, cma=cm[0] * cm[3] if cm else np.nan))
    t = pd.DataFrame(T)
    D_ = lib.daily(); Sd = D_[D_.symbol == "SPY"].set_index("date"); oc = Sd.close / Sd.open - 1
    dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=Sd.index)
    for v in ("MX", "MXH"):
        x = t.copy()
        if v == "MXH": x["r"] = x.r * x.w; x["g"] = x.g * x.w; x["ra"] = x.ra * x.w; x["cm"] = x.cm * x.w; x["cma"] = x.cma * x.w
        s_ = G.summary(x); tr_, va_ = G.summary(x[x.date <= SPLIT]), G.summary(x[x.date > SPLIT])
        m = x.dropna(subset=["cm"])
        er, ea = G.summary(m.assign(r=m.r - m.cm)), G.summary(m.assign(r=m.ra - m.cma))
        ty = x.groupby(x.date.map(dtype)).r.mean()
        gd = x.groupby("date").r.sum(); share = round(gd.max() / gd.sum(), 2) if gd.sum() > 0 else None
        mxd = t[t.kind == "mx"]
        row = dict(config=f"GATE2R-{tag}-{v}", n=s_["n"], gross=round(x.g.mean(), 4), net=s_["exp_r"], t=s_.get("t"),
                   plain_e1=round(t.base.mean(), 4), wo_best=s_.get("ex_best_day"), best_share=share, train=tr_.get("exp_r"),
                   valid=va_.get("exp_r"), up=round(ty.get("up", np.nan), 3), down=round(ty.get("down", np.nan), 3),
                   quiet=round(ty.get("quiet", np.nan), 3), r_held=round(x.r[x.held].mean(), 3), r_failed=round(x.r[~x.held].mean(), 3),
                   mx_share=round(len(mxd) / len(t), 3), mx_r=round(mxd.r.mean(), 3), mx_plain=round(mxd.base.mean(), 3),
                   ex_c1m_r=er.get("exp_r"), ex_c1m_r_t=er.get("t"), ex_c1m_atr=ea.get("exp_r"), ex_c1m_atr_t=ea.get("t"))
        ok = ((row["gross"] or -1) > 0 and (row["net"] or -1) > 0 and (row["t"] or 0) >= T90R and (row["ex_c1m_r"] or -1) > 0
              and (row["ex_c1m_atr"] or -1) > 0 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0 and row["up"] > 0
              and row["down"] > 0 and (row["wo_best"] or -1) > 0)
        if v == "MXH":                                     # size-cut control: uniform weight = mean weight
            wbar = t.w.mean(); sc = t.assign(r=t.r * t.w - wbar * t.r)
            z = G.summary(sc); row.update(sizectl_ex=z["exp_r"], sizectl_t=z.get("t"), w_mean=round(wbar, 3))
            ok = ok and (z.get("t") or 0) >= T90R
        row["pass"] = bool(ok); rows.append(row)
    print(tag, "done", flush=True)
R = pd.DataFrame(rows); pd.set_option("display.width", 420); pd.set_option("display.max_columns", 50)
print(R.to_string(index=False))
print(f"\nlineage N {N_R}, BAR90 {T90R}; gross reported first and required; plain_e1 = the same trades without MX; mx_* = trades MX exited"
      "\n(their MX R vs their plain-E1 R); C1m = matched random bar (distance-from-open + 30-min bucket) with the same exit;"
      "\nMXH: weights 0.5 before 13:00, sizectl = sum(w r) - w_mean x sum(r) per trade (must clear the bar too).")
print(f"configs 4 (lineage {N_R}), pass {int(R['pass'].sum())}")
R.to_csv(HERE / "gate2r_results.csv", index=False)
print("Educational only - not financial advice.")
