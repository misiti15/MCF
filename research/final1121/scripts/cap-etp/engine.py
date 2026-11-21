"""cap-etp engine: index-trend state (W60-style compass from computable inputs) + ETP triggers, 1-minute exits,
LR8 costs (+1.2 bp borrow on shorts), testing book (cap 100, <= 3 lots/symbol, price >= $5, cost filter 0.15R, shorts ETB
>= 90%). Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import INV, BULL, bars1, no_locked  # noqa: E402

W = Path(__file__).resolve().parent
ETB = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-rw5/etb_rate.parquet").rate
BORROW = 1.2e-4
GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}
RULES = dict(cap=100, symcap=3, cf=0.15)


def lab_daily():
    """point-in-time atr_d / adv20 / gap from the lab frames (T1 open months; fixes the locked-gap boundary in 2025-03)."""
    import research.history2y.lib as lib
    out = []
    syms = INV + BULL + ["SPY", "QQQ", "IWM"]
    for m in lib.months():
        p = lib.DATA / "frames" / f"month={m}"
        t = pads.dataset(str(p), format="parquet").to_table(
            columns=["symbol", "date", "tod", "atr_d", "adv20", "gap"],
            filter=pads.field("symbol").isin(syms) & (pads.field("tod") == 950)).to_pandas()
        out.append(t)
    d = pd.concat(out, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"]).dt.date.astype(str)
    no_locked(d.date.unique())
    return d.drop(columns="tod").rename(columns={"atr_d": "atr_l", "adv20": "adv_l", "gap": "gap_l"})


def load(test):
    F = pd.read_parquet(W / f"frames_{test}.parquet")
    if test == "T1":
        L = lab_daily()
        F = F.merge(L, on=["symbol", "date"], how="left")
        F["atr_d"] = F.atr_l.where(F.atr_l.notna(), F.atr_d)
        F["adv20"] = F.adv_l.where(F.adv_l.notna(), F.adv20)
        F["gap"] = F.gap_l.where(F.gap_l.notna(), F.gap)
        F = F.drop(columns=["atr_l", "adv_l", "gap_l"])
        F = F[F.date >= "2024-10-01"]
    no_locked(F.date.unique())
    return F


def compass(F):
    """per (date, tod): votes = sgn SPY fo + sgn SPY vwap side + sgn QQQ vwap side + agreement(SPY/QQQ/IWM fo) + persistence
    (SPY fo sign identical at every 15-min mark of the last 60 min, marks >= 09:45, >= 2 marks). DN = votes <= -4 & persist -1."""
    piv = {}
    for s in ("SPY", "QQQ", "IWM"):
        x = F[F.symbol == s].set_index(["date", "tod"])
        piv[s] = x
    c = pd.DataFrame(index=piv["SPY"].index)
    c["spy_fo"] = piv["SPY"].fo
    c["spy_vw"] = piv["SPY"].vw
    c["qqq_fo"] = piv["QQQ"].fo.reindex(c.index)
    c["qqq_vw"] = piv["QQQ"].vw.reindex(c.index)
    c["iwm_fo"] = piv["IWM"].fo.reindex(c.index)
    c = c.reset_index()
    sg = lambda v: np.sign(v.fillna(0)).astype(int)
    s = sg(c.spy_fo)
    agree = np.where((sg(c.qqq_fo) == s) & (sg(c.iwm_fo) == s), s, 0)
    c["s"] = s
    # persistence
    mins = (c.tod // 100) * 60 + c.tod % 100
    c["mins"] = mins
    pers = np.zeros(len(c), int)
    key = c.set_index(["date", "mins"]).s
    kd = key.to_dict()
    for i, (d, m, sv) in enumerate(zip(c.date.values, mins.values, s.values)):
        if m % 15 != 0 and False:
            pass
        marks = [m - k * 15 for k in range(5) if m - k * 15 >= 585]
        vals = [kd.get((d, mm)) for mm in marks]
        vals = [v for v in vals if v is not None]
        if len(vals) >= 2 and all(v == sv for v in vals) and sv != 0:
            pers[i] = sv
    c["pers"] = pers
    c["votes"] = s + sg(c.spy_vw) + sg(c.qqq_vw) + agree + pers
    c["state"] = np.where((c.votes <= -4) & (c.pers == -1), -2, np.where((c.votes >= 4) & (c.pers == 1), 2, 0))
    return c[["date", "tod", "spy_fo", "qqq_fo", "iwm_fo", "spy_vw", "votes", "pers", "state"]]


def signals(F, C, cfg):
    """cfg: dict(name, group INV/BULL, side +1/-1, want state -2/+2, trig onset/brk/vwhold, geom, lo, hi)."""
    syms = INV if cfg["group"] == "INV" else BULL
    x = F[F.symbol.isin(syms)].merge(C, on=["date", "tod"], how="left")
    x = x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    st = x.state.to_numpy()
    tod = x.tod.to_numpy()
    stok = (st == cfg["want"]) if cfg["want"] is not None else np.ones(len(x), bool)
    if cfg.get("spyfo") is not None:   # strong-move filter: SPY >= |spyfo|% from open on the state's side
        stok = stok & (x.spy_fo.to_numpy() * np.sign(cfg["spyfo"]) >= abs(cfg["spyfo"]))
    ok = stok & (tod >= cfg["lo"]) & (tod <= cfg["hi"]) & (x.atr_d.to_numpy() > 0)
    sd = cfg["dir"]  # direction of the ETP move we bet on: +1 ETP rising (long), -1 ETP falling (short)
    c = x.close.to_numpy()
    if cfg["trig"] == "onset":
        pass
    elif cfg["trig"] == "brk":
        ok &= (c > x.hod_prev.to_numpy()) if sd > 0 else (c < x.lod_prev.to_numpy())
    elif cfg["trig"] == "vwhold":
        dist = (c - x.vwap.to_numpy()) / x.atr_d.to_numpy() * sd
        above = (x.close > x.vwap) if sd > 0 else (x.close < x.vwap)
        run = above.groupby([x.symbol, x.date]).transform(lambda v: v.astype(int).rolling(6, min_periods=6).min().shift(1))
        ok &= (dist >= 0) & (dist <= 0.10) & (run.to_numpy() == 1) & ((x.fo.to_numpy() * sd) > 0)
    elif cfg["trig"] == "rand":       # null: state-free, the given tods
        pass
    hit = np.flatnonzero(ok)
    if not len(hit):
        return pd.DataFrame()
    h = x.iloc[hit]
    h = h.groupby(["symbol", "date"], sort=False).head(1)   # first hit per symbol-day
    up, dn = GEOMS[cfg["geom"]]
    R = 0.25 * h.atr_d.to_numpy()
    side = cfg["side"]
    e = h.close.to_numpy()
    o = pd.DataFrame({"symbol": h.symbol.values, "date": h.date.values, "tod": h.tod.values.astype(int), "side": side,
                      "entry": e, "stop": e - side * dn * R, "tgt": e + side * up * R, "risk": dn * R,
                      "gap": h.gap.fillna(0).values, "adv20": h.adv20.values})
    return o


def walk(T, bars):
    res = np.full((len(T), 3), np.nan)
    for sym, g in T.groupby("symbol"):
        b = bars[sym]
        hh = b.index.hour * 100 + b.index.minute
        dd = b.index.date.astype(str)
        O, H, L, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        byday = {d: np.flatnonzero(dd == d) for d in np.unique(dd)}
        for r in g.itertuples():
            ix = byday.get(r.date)
            if ix is None:
                continue
            hm = hh[ix]
            sel = ix[(hm >= r.tod) & (hm < 1555)]
            after = ix[hm >= 1555]
            s, stop, tgt = r.side, r.stop, r.tgt
            px = None
            for k in sel:
                if (s == 1 and L[k] <= stop) or (s == -1 and H[k] >= stop):
                    px, kd, xt = (min(O[k], stop) if s == 1 else max(O[k], stop)), 1, hh[k]
                    break
                if (s == 1 and H[k] >= tgt + 0.01) or (s == -1 and L[k] <= tgt - 0.01):
                    px, kd, xt = tgt, 2, hh[k]
                    break
            if px is None:
                if len(after):
                    px, kd, xt = O[after[0]], 0, 1555
                elif len(sel):
                    px, kd, xt = Cc[sel[-1]], 0, hh[sel[-1]] + 1
                else:
                    continue
            res[r.Index] = (px, kd, xt)
    T = T.copy()
    T["px"], T["kind"], T["xt"] = res[:, 0], res[:, 1], res[:, 2]
    return T


def add_r(t):
    t = t[t.kind.notna()].copy()
    tier = np.where((np.abs(t.gap) >= 20) | (t.entry < 5), 3.0, 1.0)
    ec = (0.01 + t.entry * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xc = np.where(t.kind == 2, 0.0, 0.01 + t.px * 1e-4) + np.where(t.kind == 1, 0.02, 0.0)
    bw = np.where(t.side < 0, BORROW * t.entry, 0.0)
    gross = t.side * (t.px - t.entry)
    t["r_gross"] = gross / t.risk
    t["r"] = (gross - tier * (ec + xc) - bw) / t.risk
    t["em"] = (t.tod // 100) * 60 + t.tod % 100
    t["xm"] = (t.xt // 100) * 60 + t.xt % 100
    t["stop_cost_r"] = (2 * (0.01 + t.entry * 1e-4) + 0.02) / t.risk
    return t


def book(t, rules=RULES):
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(ETB).fillna(0).ge(0.9)]
    t = t[t.stop_cost_r <= rules["cf"]]
    if not len(t):
        return t
    t = t.sort_values(["date", "em", "symbol"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    em, xm, sy = t.em.values, t.xm.values, t.symbol.values
    for _, idx in t.groupby("date").indices.items():
        open_ = []
        for i in idx:
            open_ = [o for o in open_ if o[0] > em[i]]
            if len(open_) >= rules["cap"] or sum(1 for o in open_ if o[1] == sy[i]) >= rules["symcap"]:
                continue
            keep[i] = True
            open_.append((xm[i], sy[i]))
    return t[keep].reset_index(drop=True)


def half(d):
    d = pd.Series(d).astype(str)
    fit = ((d >= "2024-10-01") & (d <= "2024-10-31")) | ((d >= "2025-03-01") & (d <= "2025-09-30"))
    return np.where(fit, "fit", np.where(d >= "2025-10-01", "check", "none"))


def ctl(t):
    if len(t) < 3:
        return float("nan")
    m = t.r.mean()
    e = (t.r - m).groupby(t.date).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(t)
    return float(m / se) if se > 0 else float("nan")


def stats(t, nses, spyday=None):
    if not len(t):
        return dict(n=0)
    day = t.groupby("date").r.sum().sort_values(ascending=False)
    tot = float(t.r.sum())
    b1 = day.index[:1]
    b2 = day.index[:2]
    o = dict(n=len(t), sess=int(day.size), per_sess=round(len(t) / nses, 2), win=round(float((t.r > 0).mean()), 3),
             avg=round(float(t.r.mean()), 4), gross=round(float(t.r_gross.mean()), 4),
             wo1=round(float(t[~t.date.isin(b1)].r.mean()), 4) if day.size > 1 else None,
             wo2=round(float(t[~t.date.isin(b2)].r.mean()), 4) if day.size > 2 else None,
             share1=round(float(day.iloc[0] / tot), 2) if tot > 0 else None,
             tot=round(tot, 2), r_per_sess=round(tot / nses, 3), worst=round(float(day.min()), 2),
             t=round(ctl(t), 2), pos_days=round(float((day > 0).mean()), 3))
    mo = t.assign(m=t.date.str[:7]).groupby("m").r.sum()
    o["pos_months"] = f"{int((mo > 0).sum())}/{len(mo)}"
    if spyday is not None:
        ty = t.date.map(spyday)
        for k in ("up", "flat", "down"):
            z = t.r[ty == k]
            o[f"{k}"] = f"{z.mean():+.3f}({len(z)})" if len(z) else "-"
    return o
