"""CWT package C: the three pieces that need the two-year 1-minute history (NOTES.md 1.3).

C2 intraday entry (4 configs), C5a FOMC 13:55 exit (2), C7 day-5 reclaim (2). Locked-block rows (2024-11-01..
2025-02-28) are dropped right after each symbol's 1-minute file is read; daily paths use common.walk (locked NaN).
Run after families.py (one process at a time). Output: raw_intraday.csv. Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import common as cm
from common import ATR14, Cn, Cx, Ln, SPY, T, col, dates, locked, score
import families as fa

CACHE = cm.ROOT / "data" / "cache_hist" / "1Min"
H_FIRST, H_LAST = pd.Timestamp("2024-09-16"), pd.Timestamp("2026-10-07")
_one = {}


def minute_day(sym, day):
    """1-minute RTH bars of one session (09:30-15:59) as a DataFrame indexed by minute-of-day (0 = 09:30)."""
    if sym not in _one:
        _one.clear()
        df = pd.read_parquet(CACHE / f"{sym}.parquet")
        idx = df.index.tz_convert("America/New_York")
        dd = pd.DatetimeIndex(idx.date)
        keep = ~((dd >= cm.LOCK_A) & (dd <= cm.LOCK_B))          # locked rows dropped at load
        df = df[keep]
        idx = idx[keep]
        df["day"] = pd.DatetimeIndex(idx.date)
        df["m"] = (idx.hour * 60 + idx.minute) - (9 * 60 + 30)
        df = df[(df.m >= 0) & (df.m < 390)]
        _one[sym] = {d: g.set_index("m") for d, g in df.groupby("day")}
    return _one[sym].get(pd.Timestamp(day))


def adj_day(sym, i):
    """Minute bars of session row i scaled to the split/dividend-adjusted daily file (the 1-minute cache is raw):
    factor = adjusted daily close / last raw 1-minute close of that session."""
    d1 = minute_day(sym, dates[i])
    if d1 is None or not len(d1):
        return None
    f = Cn[i, col[sym]] / float(d1.close.iloc[-1])
    if not np.isfinite(f):
        return None
    d1 = d1.copy()
    for c in ("open", "high", "low", "close"):
        d1[c] = d1[c] * f
    return d1


def five(day1):
    """5-minute bars from 1-minute bars: index k = bar starting 09:30 + 5k, close time = 09:35 + 5k."""
    g = day1.groupby(day1.index // 5)
    return pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                         "mlast": g.apply(lambda x: x.index.max())})


def in_hist(i):
    return H_FIRST <= dates[i] <= H_LAST and not locked[i]


def tod_mult(k):
    return 2.0 if (35 + 5 * k) < 50 else 1.0        # bar close before 09:50 -> 2x cost (plan section 0)


# ------------------------------------------------------------------------------------------------ C2 intraday entry
def c2_intraday(orw, X):
    """Breakout day t: setup known at the close of t-1 (trend, momentum, base t-B..t-1)."""
    s_prev, bh, bl = fa.c2_signals(0.10, 10, 0.08)            # s_prev unused: needs close(t) > bh (not causal)
    M = fa.xs_top(fa.MOM63, fa.ELIGB, 0.10)
    setup = fa.TREND2 & M                                       # evaluated at t-1
    with np.errstate(invalid="ignore"):
        width_ok = (bh - bl) / fa.prevCn < 0.08                 # base t-B..t-1 / close(t-1), known before t
    XS = fa.SMA10 if X == "sma10" else fa.SMA20
    rows = []
    busy = {}
    cand = [(t, j) for t, j in zip(*np.nonzero(np.vstack([np.zeros((1, cm.N), bool), setup[:-1]]) & width_ok
                                                & (cm.Hn > bh)))]
    for t, j in sorted(cand, key=lambda x: (x[1], x[0])):
        if not in_hist(t) or t <= busy.get(j, -1):
            continue
        d1 = adj_day(cm.syms[j], t)
        if d1 is None or len(d1) < 60:
            continue
        b5 = five(d1)
        orh = b5.high.iloc[0] if orw == 5 else d1.loc[d1.index < 30, "high"].max()
        k0 = 0 if orw == 5 else 5                             # first decision bar closes 09:35 / 10:00
        hit = b5.index[(b5.index >= k0) & (b5.close > orh) & (b5.close > bh[t, j]) & (b5.index <= 77)]
        if not len(hit):
            continue
        k = int(hit[0])
        ep = float(b5.close.loc[k]); stop = bl[t, j]
        if not stop < ep:
            continue
        cm_mult = tod_mult(k)
        after = d1[d1.index > b5.mlast.loc[k]]
        xi = xp = None
        if (after.low <= stop).any():
            r = after[after.low <= stop].iloc[0]
            xi, xp, why = t, min(float(r.open), stop), "stop"
        elif Cx[t, j] < XS[t, j]:
            xi, xp, why = t, Cx[t, j], "rule"
        else:
            w = cm.walk(j, t, ep, 1, "C", stop, None, lambda d: Cx[d, j] < XS[d, j], t + 40)
            if w is None:
                continue
            xi, xp, why = w[0], w[1], w[3]
        busy[j] = xi
        rows.append({"i": t, "j": j, "ei": t, "ep": ep, "ek": "O", "xi": xi, "xp": xp, "xk": "C", "why": why,
                     "cmult": cm_mult, "stopx": why == "stop"})
    t = cm.finish(rows, 1)
    if len(t):
        t["net"] = t.gross - cm.cost(t.ep) * t.cmult - cm.cost(t.xp) - np.where(t.stopx, 0.02 / t.xp, 0.0)
    return t


# ------------------------------------------------------------------------------------------------ C5a 13:55 exit
def c5a_1355(cond):
    rows = []
    for f in fa.FOMC_ROWS:
        e = f - 1
        if not (in_hist(e) and in_hist(f)):
            continue
        if cond == "neg" and not (Cn[e, SPY] / Cn[e - 1, SPY] - 1 < 0):
            continue
        d1 = adj_day("SPY", f)
        if d1 is None or 264 not in d1.index:
            continue
        xp = float(d1.loc[264, "close"])                     # 1-min bar 13:54 -> price at 13:55
        rows.append({"i": e, "j": SPY, "ei": e, "ep": Cx[e, SPY], "ek": "C", "xi": f, "xp": xp, "xk": "C", "why": "1355"})
    return cm.finish(rows, 1)


# ------------------------------------------------------------------------------------------------ C7 day-5 reclaim
def c7_day5(ex):
    rows = []
    for s in ("SPY", "QQQ", "IWM"):
        j = col[s]
        lo = Ln[:, j]
        for t in range(5, T - 1):
            if not (lo[t] < lo[t - 1] < lo[t - 2] < lo[t - 3] < lo[t - 4]):
                continue
            d = t + 1
            if not in_hist(d) or locked[t]:
                continue
            d1 = adj_day(s, d)
            if d1 is None or len(d1) < 300:
                continue
            b5 = five(d1)
            pdl = lo[t]
            below = (b5.low < pdl).cumsum() > 0                # traded below the prior-day low (this bar or earlier)
            ok = below & (b5.close > pdl) & (b5.index >= 0) & (b5.index <= 65)
            if not ok.any():
                continue
            k = int(b5.index[ok.to_numpy()][0])
            ep = float(b5.close.loc[k])
            sess_low = float(d1.loc[d1.index <= b5.mlast.loc[k], "low"].min())
            R = 0.25 * ATR14[t, j]
            if ex == "t1s1":
                stop, tgt = ep - R, ep + R
            else:
                stop, tgt = sess_low, None
            after = d1[(d1.index > b5.mlast.loc[k]) & (d1.index <= 384)]
            xp, why = float(after.close.iloc[-1]), "1555"
            for _, r in after.iterrows():
                if r.low <= stop:
                    xp, why = min(float(r.open), stop), "stop"; break
                if tgt is not None and r.high >= tgt:
                    xp, why = max(float(r.open), tgt), "target"; break
            rows.append({"i": d, "j": j, "ei": d, "ep": ep, "ek": "O", "xi": d, "xp": xp, "xk": "C", "why": why,
                         "cmult": tod_mult(k), "stopx": why == "stop", "R": R})
    t = cm.finish(rows, 1)
    if len(t):
        t["net"] = t.gross - cm.cost(t.ep) * t.cmult - np.where(t.why == "target", 0.0, cm.cost(t.xp)) \
            - np.where(t.stopx, 0.02 / t.xp, 0.0)
    return t


def regime_rows(cid, t):
    """Rule-19 session regimes (history2y), up / flat / down, on the entry session."""
    import sys
    sys.path.insert(0, str(cm.ROOT / "research" / "history2y"))
    from lib import regimes                                   # noqa: E402  (open history only)
    rg = regimes()
    rmap = dict(zip(pd.to_datetime(rg["date"]), rg["regime"])) if "date" in rg else \
        dict(zip(pd.to_datetime(rg.index), rg["regime"]))
    out = []
    ed = pd.to_datetime(dates[t.ei.to_numpy()]) if len(t) else []
    for k in ("up", "flat", "down"):
        g = t[np.array([rmap.get(x) == k for x in ed], bool)] if len(t) else t
        out.append({"id": cid, "split": f"session_{k}", **cm.summ(g)})
    return out


def main():
    extra = []
    for orw in (5, 30):
        for X in ("sma10", "sma20"):
            t = c2_intraday(orw, X)
            cid = f"C2i_or{orw}_{X}"
            score(cid, "C2", 1, f"tight base (M10 B10 w8%) intraday: first 5-min close above the {orw}-min OR high and the base high; stop base low; exit close<{X}",
                  t, {"or": orw, "X": X, "M": 0.10, "B": 10, "w": 0.08, "intraday": 1}, keep=True)
            extra += regime_rows(cid, t)
            print(cid, len(t), flush=True)
    for cond in ("all", "neg"):
        t = c5a_1355(cond)
        cid = f"C5a_fomc_{cond}_1355"
        score(cid, "C5", 1, f"SPY FOMC eve close -> FOMC-day 13:55 (two-year history), {cond}", t,
              {"cond": cond, "exit": "1355", "intraday": 1}, stock=False, keep=True)
        extra += regime_rows(cid, t)
    for ex in ("1555", "t1s1"):
        t = c7_day5(ex)
        cid = f"C7_day5_{ex}"
        score(cid, "C7", 1, f"SPY/QQQ/IWM after 4 lower lows: day-5 5-min reclaim of the prior-day low, exit {ex}", t,
              {"exit": ex, "intraday": 1}, stock=False, keep=True)
        extra += regime_rows(cid, t)
        print(cid, len(t), flush=True)
    pd.DataFrame(cm.RESULTS + extra).to_csv(cm.HERE / "raw_intraday.csv", index=False)
    cm.save_trades(cm.DATA / "trades_intraday.parquet")


if __name__ == "__main__":
    main()
