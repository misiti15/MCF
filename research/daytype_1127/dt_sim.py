"""DAYTYPE-1127 day table: for every session, SPY / QQQ entries at 11:30 and 13:00 (and +1 minute), both directions,
1R = 1.0 x ATR14 stop (stop-first, gap-through at the open), flat at the open of the last-bar-minus-4 bar (15:55).
Also SPY trend confirmation (VWAP side + 60-min slope) at each T. Gross R only; costs in dt_score.py.
Locked block 2024-11-01..2025-02-28 dropped and asserted. Usage: python dt_sim.py RAW_2016_2022_DIR OUTDIR
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

MAIN = Path("/home/user/MCF")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
TS = (1130, 1300)


def load(sym, raw):
    parts = [pd.read_parquet(raw / f"{sym}_2016_2022.parquet"),
             pd.read_parquet(MAIN / "data/cache_fresh/1Min" / f"{sym}.parquet"),
             pd.read_parquet(MAIN / "data/cache_hist/1Min" / f"{sym}.parquet")]
    out = []
    for p in parts:
        p = p[["open", "high", "low", "close", "volume"]].copy()
        p.index = pd.DatetimeIndex(p.index).tz_convert("America/New_York")
        out.append(p)
    df = pd.concat(out).sort_index()
    df = df[~df.index.duplicated(keep="last")].between_time("09:30", "15:59")
    d = df.index.date
    df = df[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    assert not ((df.index.date >= LOCK[0]) & (df.index.date <= LOCK[1])).any()
    return df


def split_of(s):
    if "2024-11-01" <= s <= "2025-02-28":
        raise AssertionError("locked")
    if s < "2023-01-01":
        return "EARLY"
    if s < "2024-10-01":
        return "T2"
    if s < "2025-10-01":
        return "FIT"
    if s <= "2026-11-04":
        return "CHECK"
    return "LATE"


def walk(o, h, l, mins, j, xj, side, risk):
    """entry at o[j]; stop = entry -/+ risk; returns gross R, kind (0 market, 1 stop), exit px."""
    e = o[j]; stop = e - side * risk
    for k in range(j, xj):
        if side > 0:
            if o[k] <= stop:
                return (o[k] - e) / risk, 1, o[k]
            if l[k] <= stop:
                return (stop - e) / risk, 1, stop
        else:
            if o[k] >= stop:
                return (e - o[k]) / risk, 1, o[k]
            if h[k] >= stop:
                return (e - stop) / risk, 1, stop
    return side * (o[xj] - e) / risk, 0, o[xj]


def main(raw, out):
    data = {s: load(s, raw) for s in ("SPY", "QQQ")}
    atr = {}
    for s, df in data.items():
        dd = df.groupby(df.index.date).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
        # locked block days are absent: ATR uses the prior 14 available sessions (gap at 2025-03 disclosed)
        tr = np.maximum(dd.h - dd.l, np.maximum((dd.h - dd.c.shift()).abs(), (dd.l - dd.c.shift()).abs()))
        atr[s] = tr.rolling(14).mean().shift(1)
    rows = []
    gS = {d: g for d, g in data["SPY"].groupby(data["SPY"].index.date)}
    gQ = {d: g for d, g in data["QQQ"].groupby(data["QQQ"].index.date)}
    for d in sorted(gS):
        if d not in gQ:
            continue
        ds = str(d)
        sp = gS[d]
        if sp.index[0].hour * 100 + sp.index[0].minute != 930:
            continue
        smin = np.array([x.hour * 60 + x.minute for x in sp.index])
        typ = (sp.high + sp.low + sp.close).to_numpy() / 3; v = sp.volume.to_numpy(float)
        cvw = np.cumsum(typ * v) / np.maximum(np.cumsum(v), 1)
        sc = sp.close.to_numpy()
        for T in TS:
            tm = (T // 100) * 60 + T % 100
            r = dict(date=ds, split=split_of(ds), T=T)
            ib = np.flatnonzero(smin < tm)
            ia = np.flatnonzero(smin <= tm - 61)
            if len(ib) == 0 or len(ia) == 0 or smin[ib[-1]] < tm - 5:
                continue
            k1, k0 = ib[-1], ia[-1]
            r["spy_vw_side"] = float(np.sign(sc[k1] - cvw[k1])); r["spy_slope60"] = float(sc[k1] / sc[k0] - 1)
            r["spy_fo_T"] = float(sc[k1] / sp.open.iloc[0] - 1)
            ok = True
            for s, g in (("SPY", sp), ("QQQ", gQ[d])):
                a = atr[s].get(d, np.nan)
                mins = np.array([x.hour * 60 + x.minute for x in g.index])
                o, h, l = g.open.to_numpy(), g.high.to_numpy(), g.low.to_numpy()
                xm = mins[-1] - 4
                xj = np.flatnonzero(mins >= xm)
                if not np.isfinite(a) or a <= 0 or not len(xj):
                    ok = False; break
                xj = xj[0]
                for lag in (0, 1):
                    jj = np.flatnonzero(mins >= tm + lag)
                    if not len(jj) or jj[0] >= xj or mins[jj[0]] > tm + lag + 2:
                        ok = False; break
                    j = jj[0]
                    for side in (1, -1):
                        gR, kind, px = walk(o, h, l, mins, j, xj, side, a)
                        tag = f"{s}_{lag}_{'L' if side > 0 else 'S'}"
                        r[tag + "_g"] = gR; r[tag + "_k"] = kind; r[tag + "_x"] = px
                    r[f"{s}_{lag}_e"] = o[j]
                r[f"{s}_risk"] = a
                if not ok:
                    break
            if ok:
                rows.append(r)
    df = pd.DataFrame(rows)
    d = pd.to_datetime(df.date).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    df.to_csv(out / "daytab.csv.gz", index=False)
    print(len(df), "rows", df.groupby(["split", "T"]).size().to_dict())


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
