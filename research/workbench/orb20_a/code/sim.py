"""Mechanic orb20_a: candidate table + 1-minute simulator (numba) for the parent and every copy, identical pipeline.
Entry: stop order at the 09:30-09:49 extreme +-1c, working 09:50 .. entry_until; fill = max(open, level) on the first
bar that trades through (as mcf.backtest.engine.simulate). Stop / target from the entry LEVEL (as ORB20.generate):
stop = level -+ stop_or x range, target = level +- target_or x range. Stop checked before target in every bar (entry bar
included); gap through the stop after the entry bar fills at the open. Time exit at the open of the exit_by bar (15:50).
R = net P/L / |fill - stop| (the live R definition). Costs (LR8 production model, identical for every config):
  entry  (s + 1 bp) x time-of-day mult (gates.TOD_COST, at the fill bar's close) + LR8 1 bp entry cushion
  target 0 (limit) ; stop (s + 1 bp) + max(2c, 4 bp) ; time / market exit (s + 1 bp) + max(1c, 1 bp)
  fees   SEC 20.60/M on the sale (exit for longs, entry for shorts), TAF 0.000195/sh on the sale, CAT 0.00005/sh/side
  s = 1c (3c for extended-tier names, ADV < $5M, as the production Costs)
Locked block 2024-11-01..2025-02-28: not in the candidate files (ext.py never loads it); asserted on load.
Educational only - not financial advice."""
import glob, math
import numpy as np, pandas as pd
from numba import njit
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-orb20/"
REPLAY = ("2026-10-06", "2026-11-10")
TWO_Y = ("2024-10-01", "2026-10-05")
TRAIN_END = "2025-12-31"
LOCK = ("2024-11-01", "2025-02-28")
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005


def load():
    F = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(OUT + "feat_c*.parquet"))], ignore_index=True)
    B = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(OUT + "bars_c*.parquet"))], ignore_index=True)
    assert not F.date.between(*LOCK).any() and not B.date.between(*LOCK).any()
    F = F.drop_duplicates(["symbol", "date"]).sort_values(["date", "rank20"]).reset_index(drop=True)
    B["ts"] = pd.to_datetime(B.ts, utc=True).dt.tz_convert("America/New_York")
    B["m"] = B.ts.dt.hour * 100 + B.ts.dt.minute
    B = B.drop_duplicates(["symbol", "date", "m"]).sort_values(["symbol", "date", "m"]).reset_index(drop=True)
    spy = B[B.symbol == "SPY"]
    B = B.merge(F[["symbol", "date"]].assign(k=np.arange(len(F))), on=["symbol", "date"], how="inner")
    B = B.sort_values(["k", "m"]).reset_index(drop=True)
    start = np.searchsorted(B.k.values, np.arange(len(F)))
    end = np.searchsorted(B.k.values, np.arange(len(F)), side="right")
    F["b0"], F["b1"] = start, end
    arr = {c: B[c].to_numpy(np.float64) for c in ("open", "high", "low", "close", "volume")}
    arr["m"] = B.m.to_numpy(np.int64)
    return F, arr, spy


@njit(cache=True)
def tod_mult(hhmm):
    if hhmm < 935: return 3.8
    if hhmm < 950: return 2.1
    if hhmm < 1030: return 1.4
    return 1.0


@njit(cache=True)
def add1(hhmm):
    h = hhmm // 100; mm = hhmm % 100 + 1
    if mm == 60: h += 1; mm = 0
    return h * 100 + mm


@njit(cache=True)
def sim_all(b0, b1, side, level, stop0, tgt0, slip, M, O, H, L, C, start_m, until_m, exit_m, skip950,
            be_r, trail_r, trail_after, tstop_min, tstop_r, prodcost):
    n = len(b0)
    R = np.full(n, np.nan); WHY = np.zeros(n, np.int64); ET = np.zeros(n, np.int64); XT = np.zeros(n, np.int64)
    MFE = np.zeros(n); MAE = np.zeros(n); FILL = np.zeros(n)
    for q in range(n):
        if side[q] == 0: continue
        s = side[q]; px = level[q]
        j = -1; fill = 0.0
        for k in range(b0[q], b1[q]):
            if M[k] < start_m: continue
            if M[k] >= until_m or M[k] >= exit_m: break
            if (s == 1 and H[k] >= px) or (s == -1 and L[k] <= px):
                if skip950 and M[k] == 950: break
                j = k; fill = max(O[k], px) if s == 1 else min(O[k], px)
                break
        if j < 0: continue
        stop = stop0[q]; tgt = tgt0[q]
        if prodcost:
            fe = fill * (1 + s * 1e-4) + s * slip[q]
            risk = s * (fe - stop)
        else:
            fe = fill
            risk = s * (fill - stop)
        if risk <= 0: continue
        if not math.isnan(tgt) and s * (tgt - fe) <= 0: continue
        why = 0; xp = 0.0; kx = -1; mfe = 0.0; mae = 0.0; st = stop
        for k in range(j, b1[q]):
            if M[k] >= exit_m:
                xp = O[k]; why = 3; kx = k; break
            adv = L[k] if s == 1 else H[k]; fav = H[k] if s == 1 else L[k]
            mae = min(mae, s * (adv - fill) / risk)
            hs = (L[k] <= st) if s == 1 else (H[k] >= st)
            ht = (not math.isnan(tgt)) and ((H[k] >= tgt) if s == 1 else (L[k] <= tgt))
            if hs:
                gt = (O[k] < st) if s == 1 else (O[k] > st)
                xp = O[k] if (gt and k > j) else st
                why = 1 if st == stop else 4; kx = k; break
            mfe = max(mfe, s * (fav - fill) / risk)
            if ht:
                xp = tgt; why = 2; kx = k; break
            if tstop_min > 0 and (k - j + 1) >= tstop_min and mfe < tstop_r and k + 1 < b1[q]:
                xp = O[k + 1]; why = 5; kx = k + 1; break
            if be_r > 0 and mfe >= be_r:
                st = max(st, fill) if s == 1 else min(st, fill)
            if trail_r > 0 and mfe >= trail_after:
                tr = fill + s * (mfe - trail_r) * risk
                st = max(st, tr) if s == 1 else min(st, tr)
        if kx < 0:
            kx = b1[q] - 1; xp = C[kx]; why = 3
        if prodcost:
            if why == 2: xe = xp
            else:
                extra = 0.02 if why == 1 else 0.0
                xe = xp * (1 - s * 1e-4) - s * (slip[q] + extra)
            r = s * (xe - fe) / risk
        else:
            base = slip[q] + fill * 1e-4
            ce = base * tod_mult(add1(M[j])) + fill * 1e-4 + CAT
            bx = slip[q] + xp * 1e-4
            if why == 2: cx = 0.0
            elif why == 1 or why == 4: cx = bx + max(0.02, 4e-4 * xp)
            else: cx = bx + max(0.01, 1e-4 * xp)
            cx += CAT
            sale = xp if s == 1 else fill
            fees = FEE_SEC * sale + TAF
            r = (s * (xp - fill) - ce - cx - fees) / risk
        R[q] = r; WHY[q] = why; ET[q] = M[j]; XT[q] = M[kx]; MFE[q] = mfe; MAE[q] = mae; FILL[q] = fill
    return R, WHY, ET, XT, MFE, MAE, FILL


WHYN = {1: "stop", 2: "target", 3: "time", 4: "trail", 5: "timestop"}
BASE = dict(top_n=20, min_rvol=1.5, vwap=True, stop_or=0.5, target_or=0.75, start=950, until=1130, exit=1550,
            skip950=False, be_r=0.0, trail_r=0.0, trail_after=1.0, tstop_min=0, tstop_r=0.0, sides=(1, -1),
            extra=None, prodcost=False, max_per_day=None)


def run(F, A, v=None, rows=None):
    """Simulate config v (dict over BASE) on candidate frame F (or its subset `rows`). Returns trades frame."""
    v = {**BASE, **(v or {})}
    G = F if rows is None else F.loc[rows]
    side = np.where(G.c49 > G.op, 1, np.where(G.c49 < G.op, -1, 0))
    ok = (G.rank20 <= v["top_n"]) & (G.rv20 >= v["min_rvol"]) & (G.hi > G.lo)
    if v["vwap"]:
        ok &= side * (G.c49 - G.vw49) > 0
    ok &= np.isin(side, v["sides"])
    if v["extra"] is not None:
        ok &= v["extra"](G, side)
    side = np.where(ok, side, 0).astype(np.int64)
    width = (G.hi - G.lo).to_numpy()
    level = np.where(side == 1, G.hi + 0.01, G.lo - 0.01)
    stop = level - side * v["stop_or"] * width
    tgt = level + side * v["target_or"] * width if v["target_or"] is not None else np.full(len(G), np.nan)
    slip = np.where(G.ext, 0.03, 0.01)
    R, WHY, ET, XT, MFE, MAE, FILL = sim_all(G.b0.to_numpy(np.int64), G.b1.to_numpy(np.int64), side, level, stop,
                                             np.asarray(tgt, np.float64), slip, A["m"], A["open"], A["high"], A["low"], A["close"],
                                             v["start"], v["until"], v["exit"], v["skip950"], v["be_r"], v["trail_r"],
                                             v["trail_after"], v["tstop_min"], v["tstop_r"], v["prodcost"])
    T = G.assign(side=side, level=level, stop=stop, tgt=tgt, r=R, why=WHY, et=ET, xt=XT, mfe=MFE, mae=MAE, fill=FILL)
    T = T[~np.isnan(R)].copy()
    if v["max_per_day"]:
        T = T.sort_values(["date", "et", "rank20"]).groupby("date").head(v["max_per_day"])
    T["exit_reason"] = T.why.map(WHYN)
    return T.sort_values(["date", "et", "symbol"]).reset_index(drop=True)


def period(T, rng):
    return T[(T.date >= rng[0]) & (T.date <= rng[1])]


def stats(T, col="r"):
    if not len(T):
        return dict(n=0)
    r = T[col]; day = T.groupby("date")[col].sum()
    best = day.idxmax(); nb = (T.date != best).sum(); worst = day.idxmin()
    w, l = r[r > 0], r[r <= 0]
    return dict(n=len(T), days=int(T.date.nunique()), win=float((r > 0).mean()), avg=float(r.mean()),
                wo_best=float((r.sum() - day[best]) / nb) if nb else float("nan"),
                wo_worst=float((r.sum() - day[worst]) / (T.date != worst).sum()) if (T.date != worst).sum() else float("nan"),
                total=float(r.sum()), worst_day=float(day.min()), best_day=float(day.max()),
                best_share=float(day[best] / r.sum()) if r.sum() > 0 else None,
                avg_win=float(w.mean()) if len(w) else 0.0, avg_loss=float(l.mean()) if len(l) else 0.0)


def paired(Tv, Tp, days):
    a = Tv.groupby("date").r.sum().reindex(days, fill_value=0.0)
    b = Tp.groupby("date").r.sum().reindex(days, fill_value=0.0)
    d = (a - b) / max(len(Tp), 1) * len(days)      # per-trade-of-parent scale, by day
    sd = d.std(ddof=1)
    return float(d.mean()), float(d.mean() / (sd / math.sqrt(len(d)))) if sd > 0 else float("nan")
