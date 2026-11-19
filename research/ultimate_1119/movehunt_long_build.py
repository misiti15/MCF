"""Move-hunt LONG evidence builder (ultimate_1119, consultant). FIT HALF ONLY.

Reads the 2-year 1-minute cache (data/cache_hist/1Min) with a pyarrow row filter that never loads the rule-19 locked
block (2024-11-01..2025-02-28) nor the check half (>= 2025-10-01). Scored sessions: 2024-10-01..2024-10-31 and
2025-03-01..2025-09-30 (Sept 2024 is warm-up only). Daily ATR / ADV20 need >= 5 prior sessions, so the first five
sessions of March 2025 have no features (no warm-up taken from the locked block).

Per symbol, per 5-minute decision bar closing at T in 09:50..15:15 ET, point-in-time features (only bars <= T) and
forward outcomes on 1-minute bars from T (entry = open of the 1-min bar starting at T):
  r_g1   target +1R / stop -1R, max hold 45 min, flat 15:55   (R = 0.25 x daily ATR(14) of prior sessions)
  r_g2   target +2R / stop -1R, max hold 45 min
  r_t30  timed 30-min exit, no stop/target
  mfe45  max favourable excursion within 45 min (R, gross), mae_first: whether -1R came before +1R is in r_g1
Costs (conservative LR8 basis): every fill pays 1 bp + $0.01/share; stop exits pay +$0.02/share more; target exits are
charged like the others (LR8 charges limit exits nothing - so these figures UNDER-state target fills slightly).
Same-minute stop and target -> stop. Stop gap-through fills at the worse of open/stop.

    python research/ultimate_1119/movehunt_long_build.py OUT.parquet [--workers 4]
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
START = pd.Timestamp("2024-09-16", tz="America/New_York")
LOCK0 = pd.Timestamp("2024-11-01", tz="America/New_York")
LOCK1 = pd.Timestamp("2025-03-01", tz="America/New_York")
CHECK0 = pd.Timestamp("2025-10-01", tz="America/New_York")
SCORE0 = pd.Timestamp("2024-10-01").date()
HOLD = 45
BPS, PS, STOPX = 1e-4, 0.01, 0.02


def load(sym: str) -> pd.DataFrame:
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    f = pads.field("__index_level_0__")
    t = d.to_table(filter=((f >= START) & (f < LOCK0)) | ((f >= LOCK1) & (f < CHECK0)))
    df = t.to_pandas()
    if "__index_level_0__" in df.columns:
        df = df.set_index("__index_level_0__")
    df.index = pd.DatetimeIndex(df.index).tz_convert("America/New_York")
    df = df.sort_index()
    m = df.index.hour * 100 + df.index.minute
    return df[(m >= 930) & (m < 1600)]


def wilder_rsi(c: np.ndarray, n: int) -> np.ndarray:
    d = np.diff(c, prepend=c[0])
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    a = 1.0 / n
    au = pd.Series(up).ewm(alpha=a, adjust=False).mean().to_numpy()
    ad = pd.Series(dn).ewm(alpha=a, adjust=False).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = au / ad
        r = 100 - 100 / (1 + rs)
    r[ad == 0] = 100.0
    return r


def spy_state() -> pd.DataFrame:
    s = load("SPY")
    s["date"] = s.index.date
    s["m"] = s.index.hour * 100 + s.index.minute
    rows = []
    for dt, g in s.groupby("date"):
        o = g["open"].iloc[0]
        c5 = g["close"].resample("5min", label="right", closed="left").last().dropna()
        lo5 = g["low"].cummin().resample("5min", label="right", closed="left").last().dropna()
        tod = c5.index.hour * 100 + c5.index.minute
        c950 = c5[tod == 950]
        c950 = c950.iloc[0] if len(c950) else np.nan
        x = pd.DataFrame({"tod": tod, "spy_fo": (c5.values / o - 1) * 100, "spy_950": (c5.values / c950 - 1) * 100,
                          "spy_r30": (c5 / c5.shift(6) - 1).values * 100,
                          "spy_lod": (c5.values / lo5.values - 1) * 100})
        x["date"] = dt
        rows.append(x)
    return pd.concat(rows, ignore_index=True)


def one(sym: str):
    try:
        df = load(sym)
    except Exception:
        return None
    if len(df) < 5000:
        return None
    df["date"] = df.index.date
    g = df.groupby("date")
    day = pd.DataFrame({"o": g["open"].first(), "h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last(),
                        "dv": (df["close"] * df["volume"]).groupby(df["date"]).sum()})
    pc = day["c"].shift(1)
    tr = np.maximum(day["h"], pc) - np.minimum(day["l"], pc)
    tr = tr.fillna(day["h"] - day["l"])
    # sessions are not contiguous across the excluded blocks: reset the rolling windows at the gap
    seg = (pd.Series(pd.to_datetime(day.index)).diff().dt.days > 20).cumsum().values
    day["seg"] = seg
    day["atr_d"] = tr.groupby(seg).transform(lambda x: x.shift(1).rolling(14, min_periods=5).mean()).values
    day["adv20"] = day["dv"].groupby(seg).transform(lambda x: x.shift(1).rolling(20, min_periods=5).mean()).values
    day["pc"] = pc.where(pd.Series(seg, index=day.index).diff().fillna(0).values == 0)
    # 5-min continuous RSI on closes (right-labelled 5-min bars)
    c5all = df["close"].resample("5min", label="right", closed="left").last().dropna()
    r2 = pd.Series(wilder_rsi(c5all.values, 2), index=c5all.index)
    r5 = pd.Series(wilder_rsi(c5all.values, 5), index=c5all.index)
    r14 = pd.Series(wilder_rsi(c5all.values, 14), index=c5all.index)
    v5all = df["volume"].resample("5min", label="right", closed="left").sum().loc[c5all.index]
    vavg = v5all.shift(1).rolling(20, min_periods=10).mean()
    vr_all = (v5all / vavg)
    out = []
    for dt, d in df.groupby("date"):
        if dt < SCORE0:
            continue
        dd = day.loc[dt]
        atr = dd["atr_d"]
        if not np.isfinite(atr) or atr <= 0 or not np.isfinite(dd["adv20"]):
            continue
        m = (d.index.hour * 100 + d.index.minute).to_numpy()
        o, h, l, c, v = (d[k].to_numpy() for k in ("open", "high", "low", "close", "volume"))
        tp = (h + l + c) / 3
        cv = np.cumsum(v)
        cv = np.where(cv == 0, np.nan, cv)
        vw = np.cumsum(tp * v) / cv
        var = np.cumsum(tp * tp * v) / cv - vw * vw
        sd = np.sqrt(np.clip(var, 0, None))
        hod = np.maximum.accumulate(h)
        lod = np.minimum.accumulate(l)
        dopen = o[0]
        ormask = m < 945
        orl = l[ormask].min() if ormask.any() else np.nan
        # minute index of each decision time T (bar closes at T => last minute T-1, entry minute T)
        mins = np.array([(t // 100) * 60 + t % 100 for t in m])
        n = len(m)
        dec = []
        for T in range(9 * 60 + 50, 15 * 60 + 16, 5):
            j = np.searchsorted(mins, T)  # first minute >= T (entry minute)
            if j == 0 or j >= n or mins[j] - T > 2 or mins[j - 1] < T - 5:
                continue
            dec.append((T, j))
        if not dec:
            continue
        # forward windows
        tod_l, rows = [], []
        cut = np.searchsorted(mins, 15 * 60 + 55)  # exits by the 15:55 bar
        for T, j in dec:
            i = j - 1  # last minute of decision bar
            ts5 = pd.Timestamp(d.index[i]).floor("5min") + pd.Timedelta(minutes=5)
            px = c[i]
            R = 0.25 * atr
            e_raw = o[j]
            e_fill = e_raw * (1 + BPS) + PS
            end = min(j + HOLD, cut)
            if end <= j:
                continue
            hh, ll, oo, cc = h[j:end], l[j:end], o[j:end], c[j:end]
            res = {}
            for nm, k in (("r_g1", 1.0), ("r_g2", 2.0)):
                tgt, stp = e_raw + k * R, e_raw - R
                hs = np.where(ll <= stp)[0]
                ht = np.where(hh >= tgt)[0]
                fs = hs[0] if len(hs) else 10**9
                ft = ht[0] if len(ht) else 10**9
                if fs <= ft and fs < 10**9:
                    xp = min(oo[fs], stp)
                    xf = xp * (1 - BPS) - PS - STOPX
                elif ft < 10**9:
                    xf = tgt * (1 - BPS) - PS  # target fill at the limit (no gap-up bonus)
                else:
                    xf = cc[-1] * (1 - BPS) - PS
                res[nm] = (xf - e_fill) / R
            e30 = min(j + 30, cut)
            res["r_t30"] = ((c[e30 - 1] * (1 - BPS) - PS) - e_fill) / R if e30 > j else np.nan
            res["mfe45"] = (hh.max() - e_raw) / R
            res["cost_r"] = (2 * (e_raw * BPS + PS) + STOPX) / R
            # point-in-time features at minute i
            lo_age_min = i - int(np.where(l[: i + 1] == lod[i])[0][-1])
            rec3 = slice(max(0, i - 14), i + 1)
            row = dict(tod=(T // 60) * 100 + T % 60, px=px, R_pct=R / px * 100, atr_pct=atr / px * 100,
                       adv20=dd["adv20"], gap=(dopen / dd["pc"] - 1) * 100 if np.isfinite(dd["pc"]) else np.nan,
                       fo_atr=(px - dopen) / atr, hod_atr=(hod[i] - px) / atr, lod_atr=(px - lod[i]) / atr,
                       pc_atr=(px - dd["pc"]) / atr if np.isfinite(dd["pc"]) else np.nan,
                       vwap_atr=(px - vw[i]) / atr, vwap_z=(px - vw[i]) / sd[i] if sd[i] > 0 else np.nan,
                       lod_age=lo_age_min, or_reclaim=float(np.isfinite(orl) and px > orl and l[rec3].min() < orl),
                       vwap_reclaim=float(px > vw[i] and (c[rec3] < vw[rec3]).any()),
                       ret15_atr=(px - c[max(0, i - 15)]) / atr, ret60_atr=(px - c[max(0, i - 60)]) / atr)
            row.update(res)
            row["ts5"] = ts5
            rows.append(row)
        x = pd.DataFrame(rows)
        x["date"] = dt
        out.append(x)
    if not out:
        return None
    x = pd.concat(out, ignore_index=True)
    x = x[(x["px"] >= 5) & (x["adv20"] >= 2e7)].reset_index(drop=True)  # base universe: price >= $5, ADV20 >= $20M
    if x.empty:
        return None
    x["rsi2"] = r2.reindex(x["ts5"]).values
    x["rsi5"] = r5.reindex(x["ts5"]).values
    x["rsi14"] = r14.reindex(x["ts5"]).values
    vr = vr_all.reindex(x["ts5"]).values
    x["vr"] = vr
    # capitulation volume: max 5-min volume ratio over the last 4 bars (incl. current)
    vr4 = vr_all.rolling(4).max()
    x["vr4"] = vr4.reindex(x["ts5"]).values
    prevc = c5all.shift(1).reindex(x["ts5"]).values
    x["up_bar"] = (x["px"].values > prevc).astype(np.float32)
    x["symbol"] = sym
    x = x.drop(columns=["ts5"])
    for k in x.columns:
        if x[k].dtype == np.float64:
            x[k] = x[k].astype(np.float32)
    return x


def main():
    out = sys.argv[1]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    syms = sorted(p.stem for p in CACHE.glob("*.parquet"))
    if "--limit" in sys.argv:
        syms = syms[: int(sys.argv[sys.argv.index("--limit") + 1])]
    spy = spy_state()
    parts = []
    with Pool(workers) as p:
        for k, x in enumerate(p.imap_unordered(one, syms, chunksize=4)):
            if x is not None:
                parts.append(x)
            if k % 100 == 0:
                print(k, len(syms), flush=True)
    df = pd.concat(parts, ignore_index=True)
    df = df.merge(spy, on=["date", "tod"], how="left")
    for k in ("spy_fo", "spy_950", "spy_r30", "spy_lod"):
        df[k] = df[k].astype(np.float32)
    df["date"] = pd.to_datetime(df["date"])
    df["symbol"] = df["symbol"].astype("category")
    assert not ((df["date"] >= "2024-11-01") & (df["date"] < "2025-03-01")).any()
    assert not (df["date"] >= "2025-10-01").any()
    df.to_parquet(out, compression="zstd")
    print("rows", len(df), "symbols", df.symbol.nunique(), "dates", df.date.nunique())


if __name__ == "__main__":
    main()
