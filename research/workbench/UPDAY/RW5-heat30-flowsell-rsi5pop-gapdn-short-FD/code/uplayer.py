"""UPDAY up-state layers as a wrapper around ANY Workbench setup bench (Mechanic 2026-11-17; same layers as
research/workbench/UPDAY/L3-gap-slope-fromopen-FD/code/sim3.py). The setup's own signals() (incl. its own WB gates) pick the
entries; up-state entry layers act by removing U rows from the candidate frame BEFORE the setup's first-bar / refire chain
(as a module mask would); exits are walked with the setup's stop / target / flat plus the optional up-state exits and the
in-trade SPY exit. All layers OFF by default -> parent / WB3 score exactly as in their Workbench runs.
U (up state at the signal bar; post-09:50 anchors): ust = ("spy950", x) | ("spy30", x) | ("both", x).
Layers: up_skip, up_w (R-weighted size), up_gap, up_fo, up_wend, up_wstart, up_hold, up_tgt, up_stop, spyx (exit once SPY
+x % since entry), spyx_u (U trades only), spyx_loss (only while under water). Educational only - not financial advice."""
import numpy as np, pandas as pd
SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
UPDEF = dict(ust=None, up_skip=False, up_w=1.0, up_gap=None, up_fo=None, up_wend=None, up_wstart=None, up_hold=None,
             up_tgt=None, up_stop=None, spyx=None, spyx_u=False, spyx_loss=False)


def spy_tables(s):
    s = s.assign(date=s.index.strftime("%Y-%m-%d"), mn=s.index.hour * 60 + s.index.minute)
    out, closes = [], {}
    for d, g in s.groupby("date"):
        g = g[~g.mn.duplicated()].set_index("mn")
        if 589 not in g.index:
            continue
        ref = g.close.loc[589]
        c = g.close.reindex(range(570, 960)).ffill().bfill()
        closes[d] = c.values
        prev30 = c.shift(30).fillna(c.iloc[0])
        tods = [(m + 1) // 60 * 100 + (m + 1) % 60 for m in c.index]
        out.append(pd.DataFrame({"date": d, "tod": tods, "spy950": (c.values / ref - 1) * 100,
                                 "spy30": (c.values / prev30.values - 1) * 100}))
    return pd.concat(out, ignore_index=True), closes


def add_spy(c, SPY):
    return c.drop(columns=[x for x in ("spy950", "spy30") if x in c]).merge(SPY, on=["date", "tod"], how="left")


def up_state(c, v):
    k = v["ust"]
    if k is None:
        return np.zeros(len(c), bool)
    kind, x = k
    if kind == "spy950":
        return (c.spy950 > x).to_numpy()
    if kind == "spy30":
        return (c.spy30 > x).to_numpy()
    return ((c.spy950 > x) & (c.spy30 > 0)).to_numpy()


def filt(c, v):
    U = up_state(c, v)
    drop = np.zeros(len(c), bool)
    if v["up_skip"]:
        drop |= U
    if v["up_gap"] is not None:
        drop |= U & ~(c.gap <= v["up_gap"]).to_numpy()
    if v["up_fo"] is not None:
        drop |= U & ~(c.fromOpen > v["up_fo"]).to_numpy()
    if v["up_wend"] is not None:
        drop |= U & (c.tod > v["up_wend"]).to_numpy()
    if v["up_wstart"] is not None:
        drop |= U & (c.tod < v["up_wstart"]).to_numpy()
    return c.assign(U=U)[~drop]


def walk(path, tod, e, R, v, up, dn, hold, spyc, spyx):
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if hold:
        flat = min(flat, t0 + hold)
    stop, tgt = e + dn * R, e - up * R
    j = np.searchsorted(mn, t0, side="left")
    s0 = spyc[t0 - 1 - 570] if (spyx is not None and spyc is not None and 570 <= t0 - 1 < 960) else None
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time"
        if (s0 is not None and 571 <= mn[k] < 960 and (spyc[mn[k] - 1 - 570] / s0 - 1) * 100 > spyx
                and (not v["spyx_loss"] or (k > j and c[k - 1] > e))):
            return o[k], mn[k], "spyx"
        if h[k] >= stop:
            return max(o[k], stop), mn[k], "stop"
        if l[k] <= tgt - 0.01:
            return tgt, mn[k], "target"
    k = len(mn) - 1
    return ((c[k], mn[k], "time") if k >= j else (e, t0, "time"))


def cost(e, px, kind):
    return e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind == "stop" else
                                                (max(0.01, 1e-4 * px) if kind in ("time", "spyx") else 0.0))


def trades(c, v, getpath, spyc, signals_fn):
    s = signals_fn(filt(c, v), v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        U = bool(r.U)
        R = v["rf"] * r.atr_d; e = r.close
        up = v["up_tgt"] if (U and v["up_tgt"] is not None) else v["up"]
        dn = v["up_stop"] if (U and v["up_stop"] is not None) else v["dn"]
        hold = v["up_hold"] if (U and v["up_hold"] is not None) else v.get("maxhold")
        sx = v["spyx"] if (v["spyx"] is not None and (U or not v["spyx_u"])) else None
        px, xm, kind = walk(p, int(r.tod), e, R, v, up, dn, hold, spyc.get(r.date), sx)
        w = v["up_w"] if U else 1.0
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind,
                     ((e - px) - cost(e, px, kind)) / R * w, w, U, r.spy950, r.spy30))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r", "w", "U", "spy950", "spy30"])


def stats(t):
    if not len(t):
        return dict(trades=0, win=np.nan, avg=np.nan, avg_wo_best=np.nan, total=0.0, worst_day=0.0, best_day=0.0,
                    best_share=np.nan, days=0)
    d = t.groupby("date").agg(s=("r", "sum"), w=("w", "sum"))
    b = d.s.idxmax(); wo_w = t.w.sum() - d.loc[b, "w"]
    return dict(trades=len(t), win=(t.r > 0).mean(), avg=t.r.sum() / t.w.sum(),
                avg_wo_best=(t.r.sum() - d.loc[b, "s"]) / wo_w if wo_w else np.nan, total=t.r.sum(),
                worst_day=d.s.min(), best_day=d.s.max(), best_share=d.s.max() / t.r.sum() if t.r.sum() > 0 else np.nan,
                days=len(d))
