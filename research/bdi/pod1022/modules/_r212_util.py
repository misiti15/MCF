"""_r212_util - shared helpers for the pod r2_12 modules (macro-news-day 10:00 momentum, hourly RSI(2), 3-down-day
ORH break, VWAP sigma-band ride, chop-day inner-band reclaim). Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry:
  * macro release calendar (08:30 ET BLS releases): CPI (the vetted list in _r24_bars.CPI_DATES), NFP (Employment
    Situation) and PPI. Calendars are published in advance, so using them is not lookahead. Locked-block dates are
    omitted on purpose.
  * daily values as of D-1's close (lib.daily(), completed days only; the rule-19 locked block is not in lib.daily();
    each series restarts after a > 7-day gap so nothing is bridged across the block): close D-1..D-4, open D-1,
    SMA20, SMA200 (min 100 sessions, because the open daily history restarts on 2025-03-03).
  * the 09:30-10:00 high / low and the 09:30..bar cumulative relative volume `rvc` (_r24_bars cache, 1-min vendor
    bars, locked block dropped at read).
  * own session VWAP and its volume-weighted standard deviation (the usual VWAP band sigma) per 5-min bar:
    typical price (h + l + c) / 3 from _cwt3_bars.full_bars (09:35..15:55) x 5-min volume from the _r24_bars cache
    (09:35..15:00). Cumulative sums run from 09:35 to the bar, so a bar's VWAP / sigma use bars <= that bar only.
  * continuous 60-minute bars built from 5-min closes (hours ending 10:30, 11:30, ..., 15:30 and a last half hour
    ending at the 15:55 bar, the last bar the history carries), with RSI(2) (Wilder) and SMA5 of hourly closes, over
    the frame month plus the previous open month as warm-up; restart after a > 7-day gap.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as CB  # noqa: E402
import _r24_bars as R24  # noqa: E402

f, key, start, lag, base, at_tod, map_daily = CB.f, CB.key, CB.start, CB.lag, CB.base, CB.at_tod, CB.map_daily
_MEM = {}

CPI = list(R24.CPI_DATES)
# BLS Employment Situation (08:30 ET). 2025-10-03 was not released (shutdown); the September report came 2025-11-20
# and the October / November report 2025-12-16; the January 2026 report was delayed to 2026-02-11.
NFP = ["2024-10-04", "2025-03-07", "2025-04-04", "2025-05-02", "2025-06-06", "2025-07-03", "2025-08-01",
       "2025-09-05", "2025-11-20", "2025-12-16", "2026-01-09", "2026-02-11", "2026-03-06", "2026-05-08",
       "2026-06-05", "2026-07-02", "2026-08-07", "2026-09-04", "2026-10-02"]
# BLS PPI (08:30 ET). Only dates known with confidence are listed (2026 dates after February omitted rather than
# guessed); the October 2025 release was cancelled and the September report came 2025-11-25.
PPI = ["2024-10-11", "2025-03-13", "2025-04-11", "2025-05-15", "2025-06-12", "2025-07-16", "2025-08-14",
       "2025-09-10", "2025-11-25", "2026-01-14", "2026-01-30", "2026-02-27"]
RELEASE = sorted(set(CPI) | set(NFP) | set(PPI))

INDEX3 = ["SPY", "QQQ", "IWM"]
ETF4 = ["SPY", "QQQ", "IWM", "DIA"]
CORE = list(CB.LARGE30)


def dstr(df):
    return pd.Series(df["date"].to_numpy()).astype(str).to_numpy()


def daily_ext():
    """Per (symbol, date D): c1..c4 = close D-1..D-4, o1 = open D-1, sma20_1 / sma200_1 as of D-1's close."""
    if "dx" in _MEM:
        return _MEM["dx"]
    d = CB.lib().daily()[["symbol", "date", "open", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, o = d["close"], d["open"]
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    for n in (1, 2, 3, 4):
        out[f"c{n}"] = c.groupby(g).shift(n)
    out["o1"] = o.groupby(g).shift(1)
    s20 = c.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).mean())
    s200 = c.groupby(g).transform(lambda x: x.rolling(200, min_periods=100).mean())
    out["sma20_1"] = s20.groupby(g).shift(1)
    out["sma200_1"] = s200.groupby(g).shift(1)
    _MEM["dx"] = out
    return out


def map_dx(df, k, cols):
    t = daily_ext()
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": dstr(df)[st]})
    m = u.merge(t, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def drive(df):
    """09:30-10:00 high / low (dr_h, dr_l) per row (use only on rows with tod >= 1000)."""
    return R24.daymap(df, ["dr_h", "dr_l"])


def rvc(df):
    """Cumulative volume 09:30..bar / its 20-session same-time mean, on each row."""
    return R24.bars_for(df, ["rvc"])["rvc"]


def _vol_month(m):
    ck = ("v", m)
    if ck not in _MEM:
        for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "v"]:
            del _MEM[kk]
        p = R24._OUT / "bars" / f"month={m}.parquet"
        _MEM[ck] = pd.read_parquet(p, columns=["symbol", "dn", "tod", "v"]) if p.exists() else None
    return _MEM[ck]


def side_switches_by(df, T):
    """Number of times the 5-min close switched sides of VWAP (bars 09:35..T), broadcast to the symbol-day."""
    fb = CB.full_bars(df, warm=False)
    out = np.full(len(df), np.nan)
    if fb is None:
        return out
    fb = fb[(fb["tod"] <= T)].copy()
    vv = vwap_sigma_table(df)
    if vv is None:
        return out
    x = fb.merge(vv, on=["symbol", "date", "tod"], how="inner")
    x = x.sort_values(["symbol", "date", "tod"], kind="mergesort")
    s = np.sign(x["c"].to_numpy(float) - x["vw"].to_numpy(float))
    x["s"] = s
    x = x[np.isfinite(s) & (s != 0)]
    gk = (x["symbol"].astype(str) + "|" + x["date"].astype(str)).to_numpy()
    prev = pd.Series(x["s"].to_numpy()).groupby(gk).shift(1).to_numpy()
    sw = (np.isfinite(prev) & (prev != x["s"].to_numpy())).astype(float)
    cnt = pd.Series(sw).groupby(gk).sum()
    k2 = (df["symbol"].astype(str).to_numpy(object) + "|" + dstr(df).astype(object))
    out = pd.Series(k2).map(cnt).to_numpy(float)
    return out


def vwap_sigma_table(df):
    """(symbol, date, tod, vw, sig) table for the frame's symbols and months (cached per frame)."""
    ck = ("vst", id(df), len(df))
    if ck in _MEM:
        return _MEM[ck]
    for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "vst"]:
        del _MEM[kk]
    fb = CB.full_bars(df, warm=False)
    if fb is None or not len(fb):
        return None
    fb = fb[fb["tod"] <= 1500].copy()
    fb["dn"] = pd.to_datetime(pd.Series(fb["date"]).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    parts = [x for x in (_vol_month(m) for m in R24._months_of(df)) if x is not None]
    if not parts:
        return None
    V = pd.concat(parts, ignore_index=True)
    V = V[V["symbol"].isin(set(fb["symbol"]))].copy()
    V["symbol"] = V["symbol"].astype(str)
    V["dn"] = V["dn"].astype(np.int64)
    V["tod"] = V["tod"].astype(np.int64)
    x = fb.merge(V, on=["symbol", "dn", "tod"], how="left")
    x = x.sort_values(["symbol", "dn", "tod"], kind="mergesort").reset_index(drop=True)
    tp = (x["h"].to_numpy(float) + x["l"].to_numpy(float) + x["c"].to_numpy(float)) / 3.0
    v = np.nan_to_num(x["v"].to_numpy(float))
    gk = (x["symbol"] + "|" + x["dn"].astype(str)).to_numpy()
    sv = pd.Series(v).groupby(gk).cumsum().to_numpy()
    spv = pd.Series(v * tp).groupby(gk).cumsum().to_numpy()
    sp2 = pd.Series(v * tp * tp).groupby(gk).cumsum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = np.where(sv > 0, spv / sv, np.nan)
        sig = np.sqrt(np.maximum(np.where(sv > 0, sp2 / sv, np.nan) - vw * vw, 0.0))
    x["vw"], x["sig"] = vw, sig
    t = x[["symbol", "date", "tod", "vw", "sig"]]
    _MEM[ck] = t
    return t


def vwap_sigma_rows(df):
    t = vwap_sigma_table(df)
    if t is None:
        return np.full(len(df), np.nan), np.full(len(df), np.nan)
    r = CB.map_rows(df, t, ["vw", "sig"])
    return r["vw"], r["sig"]


def hourly(df):
    """Per (symbol, date, tod = hourly close bar) the hourly RSI(2) (Wilder) and SMA5 of hourly closes, continuous
    across sessions (frame month + previous open month as warm-up, restart after a > 7-day gap)."""
    fb = CB.full_bars(df, warm=True)
    if fb is None or not len(fb):
        return None
    x = fb.copy()
    tod = x["tod"].to_numpy(np.int64)
    mins = (tod // 100) * 60 + tod % 100 - 570                   # minutes since 09:30 at the bar close
    x["hb"] = (mins - 1) // 60                                     # 0 = 09:30-10:30 ... 6 = 15:30-16:00
    x = x[(mins > 0)]
    h = x.groupby(["symbol", "date", "hb"], sort=True).agg(c=("c", "last"), tod=("tod", "last")).reset_index()
    full_end = np.array([1030, 1130, 1230, 1330, 1430, 1530, 1555])
    h = h[h["tod"].to_numpy() == full_end[h["hb"].to_numpy()]]   # keep complete hours only
    h = h.sort_values(["symbol", "date", "hb"], kind="mergesort").reset_index(drop=True)
    dt = pd.to_datetime(pd.Series(h["date"]).astype(str))
    g = ((h["symbol"] != h["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum().to_numpy()
    c = h["c"].to_numpy(float)
    rsi = np.full(len(c), np.nan)
    sma5 = pd.Series(c).groupby(g).transform(lambda s: s.rolling(5, min_periods=5).mean()).to_numpy()
    N = 2
    i = 0
    while i < len(c):
        j = i
        while j + 1 < len(c) and g[j + 1] == g[i]:
            j += 1
        d = np.diff(c[i:j + 1])                                    # changes within this continuous series
        if len(d) >= N:
            u, dn = np.maximum(d, 0.0), np.maximum(-d, 0.0)
            au, ad = u[:N].mean(), dn[:N].mean()                   # Wilder seed: mean of the first N changes
            for q in range(N - 1, len(d)):
                if q >= N:
                    au = (au * (N - 1) + u[q]) / N
                    ad = (ad * (N - 1) + dn[q]) / N
                rsi[i + q + 1] = 100.0 if ad == 0 else 100.0 - 100.0 / (1.0 + au / ad)
        i = j + 1
    h["rsi2h"] = rsi
    h["sma5h"] = sma5
    return h[["symbol", "date", "tod", "rsi2h", "sma5h"]]
