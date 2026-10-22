"""swing1022 prep: per-symbol arrays for the 15-minute swing-level study (PLAN.md).

1-minute RTH bars (row-filtered, locked block never read; reddit1021 common.load_rth), 15m RTH bars [nd, 26],
ATR15 / 20-bar volume average (continuous across sessions), fractal swing points on the continuous 15m series
(regular hours, or regular + extended hours where the read-only SIP fetch exists), the pre-open level pair per day,
the POI list per day, prior-session H/L, premarket H/L, round-number step.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / "reddit1021" / "scripts"))
from common import SCR as R21SCR, assert_open, load_ext, load_rth, split_of  # noqa: E402,F401

NB = 26          # 15m RTH bars per session
K_SESS = 5       # lookback sessions for swing points / POIs
NPOI = 64
STEPS = np.array([0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 100])


def round_step(px: float) -> float:
    if not np.isfinite(px) or px <= 0:
        return np.nan
    ok = STEPS[STEPS >= 0.005 * px]
    return float(ok[0]) if len(ok) else 100.0


def bars15(df: pd.DataFrame) -> pd.DataFrame:
    """15m bars from 1-minute bars (09:30-anchored buckets also tile 04:00-20:00). Index = bar start."""
    g = df.resample("15min", origin="start_day", offset="30min", label="left", closed="left")
    b = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["close"])
    return b


def pivots(b: pd.DataFrame, n: int):
    """Fractal pivots on the continuous series b. Returns list of (bar_start, confirm_end, price, +1 high / -1 low)."""
    h = b["high"].to_numpy(float); l = b["low"].to_numpy(float)
    t0 = b.index
    out = []
    m = len(h)
    for i in range(n, m - n):
        if h[i] > h[i - n:i].max() and h[i] > h[i + 1:i + n + 1].max():
            out.append((t0[i], t0[i + n] + pd.Timedelta(minutes=15), h[i], 1))
        if l[i] < l[i - n:i].min() and l[i] < l[i + 1:i + n + 1].min():
            out.append((t0[i], t0[i + n] + pd.Timedelta(minutes=15), l[i], -1))
    return out


def prep_symbol(sym: str, with_ext: bool):
    rth = load_rth(sym)
    if rth is None or len(rth) < 1000:
        return None
    days = sorted(set(rth.index.date))
    nd = len(days)
    idx = {d: i for i, d in enumerate(days)}
    mins = ((rth.index.hour * 60 + rth.index.minute) - 570).to_numpy()
    di = np.array([idx[d] for d in rth.index.date])
    order = np.lexsort((mins, di))
    Z = {"days": np.array([str(d) for d in days])}
    for c in ("open", "high", "low", "close"):
        Z["m_" + c[0]] = rth[c].to_numpy(float)[order]
    Z["m_min"] = mins[order].astype(np.int16)
    Z["start"] = np.searchsorted(di[order], np.arange(nd + 1))
    # 15m RTH bars
    b = bars15(rth)
    b = b[(b.index.hour * 60 + b.index.minute >= 570) & (b.index.hour * 60 + b.index.minute < 960)]
    pc = b["close"].shift(1)
    tr = pd.concat([b.high - b.low, (b.high - pc).abs(), (b.low - pc).abs()], axis=1).max(axis=1)
    b = b.assign(atr_prev=tr.rolling(14).mean().shift(1), v20_prev=b["volume"].rolling(20).mean().shift(1))
    bd = np.array([idx[d] for d in b.index.date]); bk = ((b.index.hour * 60 + b.index.minute) - 570) // 15
    for col, key in (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"), ("volume", "v"),
                     ("atr_prev", "atr"), ("v20_prev", "v20")):
        a = np.full((nd, NB), np.nan)
        a[bd, bk] = b[col].to_numpy(float)
        Z["f_" + key] = a
    # session VWAP / open at each 15m close (trend context when this symbol is SPY)
    typ = (rth.high + rth.low + rth.close) / 3
    cum = (typ * rth.volume).groupby(rth.index.date).cumsum() / rth.volume.groupby(rth.index.date).cumsum().replace(0, np.nan)
    vw = np.full((nd, NB), np.nan)
    cm = pd.Series(cum.to_numpy(), index=rth.index)
    last = cm[(rth.index.minute % 15) == 14]
    vw[[idx[d] for d in last.index.date], ((last.index.hour * 60 + last.index.minute) - 570) // 15] = last.to_numpy()
    Z["f_vwap"] = vw
    dl = rth.groupby(rth.index.date).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"), o=("open", "first"))
    # prior session (never across the locked block: gap > 5 calendar days -> none)
    prev = [None] + [days[i - 1] if (days[i] - days[i - 1]).days <= 5 else None for i in range(1, nd)]
    PD = np.full((nd, 2), np.nan); gap = np.full(nd, np.nan); step = np.full(nd, np.nan)
    for i, d in enumerate(days):
        p = prev[i]
        if p is not None:
            PD[i] = dl.loc[p, "h"], dl.loc[p, "l"]
            gap[i] = dl.loc[d, "o"] / dl.loc[p, "c"] - 1
            step[i] = round_step(dl.loc[p, "c"])
        else:
            step[i] = round_step(dl.loc[d, "o"])
    Z["PD"] = PD; Z["step"] = step
    Z["tier"] = np.where((dl["o"].to_numpy(float) < 5) | (np.abs(np.nan_to_num(gap)) >= 0.20), 3.0, 1.0)
    Z["gap"] = gap
    # premarket H/L and extended series
    PM = np.full((nd, 2), np.nan)
    ext = load_ext(sym, "1Min") if with_ext else None
    if ext is not None and len(ext):
        hm = ext.index.hour * 100 + ext.index.minute
        pm = ext[(hm >= 400) & (hm < 930)]
        pml = pm.groupby(pm.index.date).agg(h=("high", "max"), l=("low", "min"))
        for i, d in enumerate(days):
            if d in pml.index:
                PM[i] = pml.loc[d, "h"], pml.loc[d, "l"]
    Z["PM"] = PM
    # swing levels per (N, source)
    srcs = {"rth": bars15(rth)}
    srcs["rth"] = srcs["rth"][(srcs["rth"].index.hour * 60 + srcs["rth"].index.minute >= 570)
                              & (srcs["rth"].index.hour * 60 + srcs["rth"].index.minute < 960)]
    if ext is not None and len(ext):
        e = ext[[c for c in ("open", "high", "low", "close", "volume")]]
        srcs["ext"] = bars15(e)
    opens = {d: pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30) for d in days}
    for sname, sb in srcs.items():
        for n in (1, 2, 3):
            pv = pivots(sb, n)
            P = pd.DataFrame(pv, columns=["t", "conf", "px", "typ"]).sort_values("conf", kind="stable")
            conf = pd.DatetimeIndex(P["conf"]).as_unit("ns").asi8 if len(P) else np.zeros(0, np.int64)
            pt = pd.DatetimeIndex(P["t"]).as_unit("ns").asi8 if len(P) else np.zeros(0, np.int64)
            px = P["px"].to_numpy(float); ty = P["typ"].to_numpy(int)
            SH = np.full(nd, np.nan); SL = np.full(nd, np.nan)
            CH = np.zeros((nd, 2), np.int8)       # 1 = a break of it would be a change of character
            FR = np.zeros((nd, 2), np.int8)       # 1 = no 15m RTH close beyond it since it formed (before today)
            POI = np.full((nd, NPOI), np.nan)
            sct = srcs["rth"].index.as_unit("ns").asi8
            scv = srcs["rth"]["close"].to_numpy(float)
            for i, d in enumerate(days):
                j = i
                for _ in range(K_SESS):
                    if j > 0 and prev[j] is not None:
                        j -= 1
                    else:
                        break
                if j == i and sname == "rth":
                    continue
                lo_t = (opens[days[j]] - pd.Timedelta(hours=6)) if j < i else (opens[d] - pd.Timedelta(hours=6))
                lo = lo_t.value; hi = opens[d].value
                s0 = np.searchsorted(conf, lo, "left"); e0 = np.searchsorted(conf, hi, "right")
                ii = np.arange(s0, e0)
                ii = ii[pt[ii] >= lo]
                if not len(ii):
                    continue
                hs = ii[ty[ii] == 1]; ls = ii[ty[ii] == -1]
                if len(hs):
                    SH[i] = px[hs[-1]]
                    CH[i, 0] = 1 if len(hs) >= 2 and px[hs[-2]] > px[hs[-1]] else 0
                    a1 = np.searchsorted(sct, pt[hs[-1]], "right"); b1 = np.searchsorted(sct, hi, "left")
                    FR[i, 0] = 0 if (scv[a1:b1] > SH[i]).any() else 1
                if len(ls):
                    SL[i] = px[ls[-1]]
                    CH[i, 1] = 1 if len(ls) >= 2 and px[ls[-2]] < px[ls[-1]] else 0
                    a1 = np.searchsorted(sct, pt[ls[-1]], "right"); b1 = np.searchsorted(sct, hi, "left")
                    FR[i, 1] = 0 if (scv[a1:b1] < SL[i]).any() else 1
                u = np.unique(px[ii])[-NPOI:]
                POI[i, :len(u)] = u
            Z[f"SH_{sname}{n}"] = SH; Z[f"SL_{sname}{n}"] = SL; Z[f"CH_{sname}{n}"] = CH
            Z[f"FR_{sname}{n}"] = FR; Z[f"POI_{sname}{n}"] = POI
    assert_open(days)
    return Z
