"""PMDIR-1127 feature builder (PREREG.md): one row per day, features known at 12:00, target 12:00->15:55, SPY trade sims.
    python research/pmdir_1127/pm_build.py <raw_2016_2022_dir> <out_csv>
Locked block 2024-11-01..2025-02-28 dropped at load and asserted absent. Educational only - not financial advice."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

MAIN = Path("/home/user/MCF")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
SECT = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]


def load(sym, raw):
    parts = []
    for f in (raw / f"{sym}_2016_2022.parquet", MAIN / "data/cache_fresh/1Min" / f"{sym}.parquet",
              MAIN / "data/cache_hist/1Min" / f"{sym}.parquet"):
        if f.exists():
            p = pd.read_parquet(f)[["open", "high", "low", "close", "volume"]].copy()
            p.index = pd.DatetimeIndex(p.index).tz_convert("America/New_York")
            parts.append(p)
    df = pd.concat(parts).sort_index()
    df = df[~df.index.duplicated(keep="last")].between_time("09:30", "15:59")
    d = df.index.date
    df = df[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    assert not ((df.index.date >= LOCK[0]) & (df.index.date <= LOCK[1])).any()
    df = df[df.index.date <= pd.Timestamp("2026-11-04").date()]
    return df


def split_of(s):
    d = pd.Timestamp(s).date()
    assert not (LOCK[0] <= d <= LOCK[1]), "locked block"
    s = str(s)
    if s < "2023-01-01": return "EARLY"
    if s < "2024-10-01": return "T2"
    if s < "2025-10-01": return "FIT"
    return "CHECK"


def sim(o, h, l, mins, j, side, exit_k, width=0.005, extra=0.0):
    fill = o[j]; stop = fill * (1 - side * width); risk = fill * width
    for k in range(j, exit_k):
        hit = l[k] <= stop if side == 1 else h[k] >= stop
        if hit:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            return side * (px - fill) / risk, 1, fill, px
    px = o[exit_k]
    return side * (px - fill) / risk, 0, fill, px


def main():
    raw = Path(sys.argv[1]); out = Path(sys.argv[2])
    spy = load("SPY", raw); qqq = load("QQQ", raw); iwm = load("IWM", raw)
    sect = {s: load(s, raw) for s in SECT}
    gq = {d: g for d, g in qqq.groupby(qqq.index.date)}; gi = {d: g for d, g in iwm.groupby(iwm.index.date)}
    gs = {s: {d: g for d, g in v.groupby(v.index.date)} for s, v in sect.items()}
    rows = []
    for d, g in spy.groupby(spy.index.date):
        mins = np.array([t.hour * 60 + t.minute for t in g.index])
        if mins[0] != 570 or len(g) < 150: continue
        o, h, l, c, v = (g[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
        last = mins[-1]
        exit_min = min(955, last + 1 - 5)
        k12 = np.where(mins == 720)[0]; kx = np.where(mins == exit_min)[0]
        if not len(k12) or not len(kx): continue
        k12 = int(k12[0]); kx = int(kx[0])
        if kx <= k12 + 5: continue
        m = mins < 720
        O = o[0]; C = c[m][-1]
        tp = (h[m] + l[m] + c[m]) / 3
        vw = (tp * v[m]).sum() / max(v[m].sum(), 1)
        lr = np.diff(np.log(c[m]))
        def fo(gg):
            if gg is None: return np.nan
            mm = np.array([t.hour * 60 + t.minute for t in gg.index])
            gg2 = gg[mm < 720]
            if len(gg2) < 30: return np.nan
            return gg2.close.iloc[-1] / gg2.open.iloc[0] - 1
        q = fo(gq.get(d)); iw = fo(gi.get(d))
        sv = [fo(gs[s].get(d)) for s in SECT]; sv = [x for x in sv if np.isfinite(x)]
        br = (np.mean([x > 0 for x in sv]) - 0.5) if len(sv) >= 8 else np.nan
        k11 = np.where(mins == 660)[0]
        lmom = C / c[k11[0] - 1] - 1 if len(k11) and k11[0] > 0 else np.nan
        # W60 proxy
        marks = [660, 675, 690, 705]
        sg = [np.sign(c[np.where(mins == mk)[0][0] - 1] / O - 1) for mk in marks if len(np.where(mins == mk)[0])]
        s0 = np.sign(C / O - 1)
        persist = len(sg) == 4 and all(x == s0 for x in sg) and s0 != 0
        agree = s0 if (np.sign(q) == s0 and np.sign(iw) == s0) else 0
        votes = s0 + np.sign(C - vw) + (np.sign(br) if np.isfinite(br) else 0) + agree
        w60 = int(np.sign(votes)) if (abs(votes) >= 3 and persist and np.sign(votes) == s0) else 0
        y = int(o[kx] > o[k12])
        rec = dict(date=str(d), split=split_of(d), mret=C / O - 1, mrange=(h[m].max() - l[m].min()) / O,
                   vwap=(C / vw - 1) * 1e4, breadth=br, rvm=lr.std() * np.sqrt(390 * 252), qi=q - iw,
                   dow=pd.Timestamp(d).dayofweek, lmom=lmom, w60=w60, open=O, close=c[-1],
                   ret_pm=o[kx] / o[k12] - 1, y=y, half=int(last < 959), entry=o[k12], tod=1201)
        for side, nm in ((1, "L"), (-1, "S")):
            r, kind, fill, px = sim(o, h, l, mins, k12, side, kx)
            r1, kind1, fill1, px1 = sim(o, h, l, mins, k12 + 1, side, kx)
            rec.update({f"r{nm}": r, f"k{nm}": kind, f"x{nm}": px, f"r{nm}1": r1, f"k{nm}1": kind1, f"x{nm}1": px1,
                        f"e{nm}1": fill1})
        rows.append(rec)
    df = pd.DataFrame(rows)
    dd = pd.to_datetime(df.date)
    gapd = dd.diff().dt.days
    df["prev_close"] = df.close.shift(1)
    df["gap"] = df.open / df.prev_close - 1
    df["prev"] = df.close.shift(1) / df.close.shift(2) - 1
    cc = np.log(df.close / df.close.shift(1))
    df["rv20"] = cc.shift(1).rolling(20).std() * np.sqrt(252)
    # invalidate anything that needs a day across a >5-calendar-day gap (locked block / data holes)
    bad = (gapd > 5).astype(int)
    seg = bad.cumsum()
    pos = df.groupby(seg).cumcount()
    df.loc[pos < 1, ["gap", "prev"]] = np.nan
    df.loc[pos < 2, "prev"] = np.nan
    df.loc[pos < 21, "rv20"] = np.nan
    df = df.drop(columns=["prev_close"])
    df.to_csv(out, index=False)
    print(df.split.value_counts().to_dict(), "nan rows", int(df[["gap", "prev", "rv20", "breadth", "qi", "lmom"]].isna().any(axis=1).sum()))


if __name__ == "__main__":
    main()
