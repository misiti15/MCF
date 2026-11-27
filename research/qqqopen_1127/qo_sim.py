"""QQQOPEN-1127 simulator: index open-dip / open-move rules on 2016-2026 minute history (PREREG.md).

Replicates mcf/strategies/index_dip.find_trigger + IndexDipBounce.build_signal and mcf/backtest/engine.simulate
(next-bar-open market entry, stop-first, gap-through at the open, trail updated at bar end) on gross prices; costs are
applied afterwards (qo_score.py). Locked block 2024-11-01..2025-02-28 is never read (asserted).
    python research/qqqopen_1127/qo_sim.py <raw_2016_2022_dir>   -> trades.csv.gz (scratch) + summary in qo_score.py
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = Path("/home/user/MCF")          # data lives in the read-only main clone (not in git)
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
PAIRS = {"QQQ": "TQQQ", "SPY": "SPXL"}


def load(sym: str, raw_dir: Path) -> pd.DataFrame:
    parts = [pd.read_parquet(raw_dir / f"{sym}_2016_2022.parquet"),
             pd.read_parquet(MAIN / "data/cache_fresh/1Min" / f"{sym}.parquet"),
             pd.read_parquet(MAIN / "data/cache_hist/1Min" / f"{sym}.parquet")]
    out = []
    for p in parts:
        p = p[["open", "high", "low", "close", "volume"]].copy()
        p.index = pd.DatetimeIndex(p.index).tz_convert("America/New_York")
        out.append(p)
    df = pd.concat(out).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.between_time("09:30", "15:59")
    d = df.index.date
    df = df[~((d >= LOCK[0]) & (d <= LOCK[1]))]          # locked block dropped before anything is computed
    assert not ((df.index.date >= LOCK[0]) & (df.index.date <= LOCK[1])).any()
    return df


def split_of(day) -> str:
    s = str(day)
    if LOCK[0] <= day <= LOCK[1]:
        raise AssertionError("locked block day")
    if s < "2023-01-01":
        return "EARLY"
    if s < "2024-10-01":
        return "T2"
    if s < "2025-10-01":
        return "FIT"
    if s <= "2026-11-04":
        return "CHECK"
    return "LATE"


def tmin(ts) -> np.ndarray:
    return np.array([x.hour * 60 + x.minute for x in ts])


def simulate(o, h, l, c, mins, j, fill, stop, side, exit_min, trail):
    """Gross R and exit kind (0 market/time, 1 stop) from bar j (entry at o[j]=fill)."""
    risk = side * (fill - stop)
    if risk <= 0:
        return None
    mfe = 0.0
    n = len(o)
    for k in range(j, n):
        if mins[k] >= exit_min:
            return side * (o[k] - fill) / risk, 0, k, o[k], risk
        hit = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hit:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            return side * (px - fill) / risk, 1, k, px, risk
        fav = h[k] if side == 1 else l[k]
        mfe = max(mfe, side * (fav - fill) / risk)
        if trail and mfe >= 1.0:
            tr = fill + side * (mfe - 1.0) * risk
            stop = max(stop, tr) if side == 1 else min(stop, tr)
    return side * (c[-1] - fill) / risk, 0, n - 1, c[-1], risk


def day_trades(ix: pd.DataFrame, tx: pd.DataFrame, sig: str, trd: str):
    """All configs for one day: list of dict rows (gross)."""
    rows = []
    if len(ix) < 40 or len(tx) < 40:
        return rows
    imin = tmin(ix.index); tmn = tmin(tx.index)
    if imin[0] != 570 or tmn[0] != 570:
        return rows
    last = max(imin[-1], tmn[-1])
    exit_min = min(955, last + 1 - 5)            # 15:55, or close - 5 min on a half day (LR1)
    io, ih, il, ic = (ix[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    to_, th, tl, tc = (tx[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    O = io[0]
    ends = imin + 1                                # bar close minute
    run_lo = np.minimum.accumulate(il); run_hi = np.maximum.accumulate(ih)
    tO = to_[0]
    day = ix.index[0].date()
    # move since the open at the 09:54 bar close (known at 09:55)
    k954 = np.where(imin == 594)[0]
    mv955 = (ic[k954[0]] / O - 1) * 100 if len(k954) else np.nan

    def entry_after(ts_min_idx_bar):
        """traded bar k at/before the index trigger bar minute; entry at k+1 open."""
        k = int(np.searchsorted(tmn, ts_min_idx_bar, side="right")) - 1
        return k

    for X in (0.5, 0.75, 1.0, 1.5):
        for rule in ("FADE-LONG", "FADE-SHORT", "FOLLOW-SHORT", "FOLLOW-LONG"):
            k = None; side = None; stop = None; meta = {}
            if rule in ("FADE-LONG", "FADE-SHORT"):
                side = 1 if rule == "FADE-LONG" else -1
                thr = O * (1 - X / 100) if side == 1 else O * (1 + X / 100)
                dipped = ((run_lo <= thr) if side == 1 else (run_hi >= thr)) & (ends <= 595)
                if not dipped.any():
                    continue
                i0 = int(np.argmax(dipped)); trig = None
                for i in range(i0, len(ix)):
                    if ends[i] > 605:
                        break
                    if ends[i] < 590:
                        continue
                    if side == 1:
                        ok = ic[i] >= run_lo[i] + 0.20 * (O - run_lo[i])
                    else:
                        ok = ic[i] <= run_hi[i] - 0.20 * (run_hi[i] - O)
                    if ok:
                        trig = i; break
                if trig is None:
                    continue
                k = entry_after(imin[trig])
                if k < 0 or k + 1 >= len(tx):
                    continue
                seg_lo = tl[: k + 1].min(); seg_hi = th[: k + 1].max(); px = tc[k]
                if side == 1:
                    drop = tO - seg_lo
                    if not (drop > 0 and px > seg_lo):
                        continue
                    stop = seg_lo - 0.10 * drop
                else:
                    rise = seg_hi - tO
                    if not (rise > 0 and px < seg_hi):
                        continue
                    stop = seg_hi + 0.10 * rise
                meta = dict(idx_ext=round(((run_lo[trig] if side == 1 else run_hi[trig]) / O - 1) * 100, 3))
            else:
                if not np.isfinite(mv955):
                    continue
                side = -1 if rule == "FOLLOW-SHORT" else 1
                if side == -1 and mv955 > -X:
                    continue
                if side == 1 and mv955 < X:
                    continue
                k = int(np.searchsorted(tmn, 594, side="right")) - 1   # traded bar at/before 09:54
                if k < 0 or k + 1 >= len(tx):
                    continue
                mvt = abs(tc[k] - tO)
                if mvt <= 0:
                    continue
                stop = tO + 0.10 * mvt if side == -1 else tO - 0.10 * mvt
                if side * (tc[k] - stop) <= 0:
                    continue
                meta = dict(idx_ext=round(mv955, 3))
            j = k + 1
            if tmn[j] >= exit_min:
                continue
            fill = to_[j]
            for ex in ("HOLD", "TRAIL"):
                r = simulate(to_, th, tl, tc, tmn, j, fill, stop, side, exit_min, ex == "TRAIL")
                if r is None:
                    continue
                g, kind, kx, px, risk = r
                rows.append(dict(date=str(day), split=split_of(day), sig=sig, trd=trd, X=X, rule=rule, exit=ex,
                                 side=side, entry=fill, exit_px=px, risk=risk, kind=kind, gross=g,
                                 tod=int(tx.index[j].hour * 100 + tx.index[j].minute), emin=int(tmn[j]),
                                 xmin=int(tmn[kx]), stop_pct=risk / fill * 100, mv955=mv955, **meta))
    return rows


def main(raw_dir: str):
    raw = Path(raw_dir)
    data = {s: load(s, raw) for s in ("QQQ", "SPY", "TQQQ", "SPXL")}
    allrows = []
    for sig, trd in PAIRS.items():
        I = data[sig]; T = data[trd]
        gI = {d: g for d, g in I.groupby(I.index.date)}
        gT = {d: g for d, g in T.groupby(T.index.date)}
        for d in sorted(gI):
            if d not in gT:
                continue
            allrows += day_trades(gI[d], gT[d], sig, trd)
            # 1x instrument check for the live replicas (the index ETF traded on its own signal)
            for r in day_trades(gI[d], gI[d], sig, sig):
                if r["rule"] == "FADE-LONG" and ((sig == "QQQ" and r["X"] == 1.0) or (sig == "SPY" and r["X"] == 0.75 and r["exit"] == "TRAIL")):
                    allrows.append(r)
    df = pd.DataFrame(allrows)
    d = pd.to_datetime(df.date).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    # daily index context for regimes (prior-close info only) and the per-day calendar for controls
    ctx = []
    for s in ("QQQ", "SPY"):
        dd = data[s].groupby(data[s].index.date).agg(o=("open", "first"), c=("close", "last"))
        dd["sma50"] = dd.c.rolling(50).mean().shift(1)
        dd["above50"] = (dd.c.shift(1) > dd.sma50)
        dd["rv20"] = np.log(dd.c).diff().rolling(20).std().shift(1)
        dd["sig"] = s
        ctx.append(dd.reset_index(names="date"))
    ctx = pd.concat(ctx); ctx["date"] = ctx.date.astype(str)
    out = Path(sys.argv[2] if len(sys.argv) > 2 else HERE)
    df.to_csv(out / "trades.csv.gz", index=False)
    ctx.to_csv(out / "dayctx.csv.gz", index=False)
    print(len(df), "rows;", df.groupby(["sig", "trd"]).size().to_dict())


if __name__ == "__main__":
    main(sys.argv[1])
