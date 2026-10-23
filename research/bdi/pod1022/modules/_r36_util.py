"""_r36_util - shared helpers for the pod r3_6 modules (LPS 60-day loser intraday drift, Moglen prior-day last-hour
undercut, Raschke SMA5 7-bar runs, Raschke MACD/EMA20 scalping box, Shannon gap-down dual-VWAP reclaim).
Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry (all causal):
  * 60-session close-to-close return as of D-1 (c[D-1] / c[D-61] - 1, lib.daily() completed days; every series
    restarts after a > 7-day gap so nothing bridges the rule-19 locked block), and its cross-sectional percentile
    rank per date D over the universe adv20(D-1) >= $100M and close(D-1) >= $10.
  * the head/tail 5m table (research/bdi/cwt/test_b, bar-close tods 09:35-09:45 and 15:05-15:55): today's opening
    bars (used only on bars closing at or after them) and the PRIOR session's last-hour low (bars closing 15:05..15:55;
    the 15:55-16:00 bar is not in the table - stated proxy). The locked block is filtered out right after reading.
  * the prior session's last RTH 5m bar (15:55-16:00) typical x volume and volume (_r26_bars day aggregates,
    S - ctp_1555 and V - cvl_1555 of D-1) and today's cumulative 5m volume (_r24 bars via _r27_util.vol_bars), giving
    the AVWAP anchored at the prior day's last bar: (session VWAP x cum vol + tpv_last) / (cum vol + v_last).
  * continuous 5m EMA20 / MACD line (EMA12 - EMA26) over the full-session bars (_cwt3_bars.full_bars: frames 09:50-15:00
    + head/tail 09:35-09:45 / 15:05-15:55, previous open month as warm-up; restart after a > 7-day gap), and the count
    of consecutive bars with the MACD line > 0 / < 0 ending at each bar.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as C3  # noqa: E402
import _r26_bars as R26  # noqa: E402
import _r27_util as U27  # noqa: E402
import _r31_util as U31  # noqa: E402

_LOCKED = ("2024-11-01", "2025-02-28")
_MEM = {}
f, key, start, lag, base, segments = U31.f, U31.key, U31.start, U31.lag, U31.base, U31.segments


def _runs(d):
    dt = pd.to_datetime(d["date"])
    return ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()


def ret60_tab():
    if "r60" in _MEM:
        return _MEM["r60"]
    d = C3.lib().daily()[["symbol", "date", "close", "adv20"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((d["date"] >= _LOCKED[0]) & (d["date"] <= _LOCKED[1])).any()
    g = _runs(d)
    c = d["close"]
    r60 = c / c.groupby(g).shift(60) - 1.0
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["r60_1"] = r60.groupby(g).shift(1)
    out["adv_1"] = d["adv20"].groupby(g).shift(1)
    out["c_1"] = c.groupby(g).shift(1)
    u = (out["adv_1"] >= 100e6) & (out["c_1"] >= 10) & out["r60_1"].notna()
    out["r60_pct"] = np.nan
    out.loc[u, "r60_pct"] = out[u].groupby("date")["r60_1"].rank(pct=True)
    _MEM["r60"] = out
    return out


def map_day(df, tab, cols):
    return U31.map_day(df, tab, cols)


def _headtail():
    if "ht" in _MEM:
        return _MEM["ht"]
    t = pd.read_parquet(C3._HEADTAIL, columns=["symbol", "date", "tod", "h", "l", "c"])
    t["symbol"] = t["symbol"].astype(str)
    t["date"] = pd.to_datetime(t["date"]).dt.strftime("%Y-%m-%d")
    t = t[((t["date"] < _LOCKED[0]) | (t["date"] > _LOCKED[1])) & ((t["tod"] < 950) | (t["tod"] > 1500))]
    t = t.reset_index(drop=True)
    _MEM["ht"] = t
    return t


def head_tab():
    """Per (symbol, date D): 09:35 / 09:40 / 09:45 bar lows and closes of D, and lhl_1 = the prior session's low of
    the bars closing 15:05..15:55 (prior session = previous lib.daily() row of the symbol in the same run)."""
    if "head" in _MEM:
        return _MEM["head"]
    t = _headtail()
    hd = t[t["tod"] < 950].pivot_table(index=["symbol", "date"], columns="tod", values=["l", "c"], aggfunc="last")
    hd.columns = [f"{a}{b}" for a, b in hd.columns]
    hd = hd.reset_index()
    tl = t[t["tod"] > 1500].groupby(["symbol", "date"], as_index=False).agg(lhl=("l", "min"), ntl=("l", "size"))
    tl.loc[tl["ntl"] < 8, "lhl"] = np.nan
    d = C3.lib().daily()[["symbol", "date"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = _runs(d)
    d = d.merge(tl[["symbol", "date", "lhl"]], on=["symbol", "date"], how="left")
    d["lhl_1"] = d["lhl"].groupby(g.to_numpy()).shift(1)
    out = d[["symbol", "date", "lhl_1"]].merge(hd, on=["symbol", "date"], how="left")
    for col in ("l935", "l940", "l945", "c935", "c940", "c945"):
        if col not in out:
            out[col] = np.nan
    _MEM["head"] = out
    return out


def pc_anchor_tab():
    """Per (symbol, date D): tpv_last_1 / v_last_1 = typical x volume and volume of D-1's 15:55-16:00 bar."""
    if "pca" in _MEM:
        return _MEM["pca"]
    D = R26.day()[["symbol", "date", "S", "V", "ctp_1555", "cvl_1555"]].copy()
    D["date"] = D["date"].astype(str)
    D = D.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = _runs(D)
    tpv = D["S"].astype(float) - D["ctp_1555"].astype(float)
    vl = D["V"].astype(float) - D["cvl_1555"].astype(float)
    bad = ~(vl > 0)
    tpv[bad] = np.nan
    vl[bad] = np.nan
    out = pd.DataFrame({"symbol": D["symbol"], "date": D["date"]})
    out["tpv_last_1"] = tpv.groupby(g.to_numpy()).shift(1)
    out["v_last_1"] = vl.groupby(g.to_numpy()).shift(1)
    _MEM["pca"] = out
    return out


def pc_avwap(df):
    """AVWAP anchored at the prior session's last RTH bar, per frame row (NaN when an input is missing)."""
    b = base(df)
    B = U27.vol_bars(df)
    n = len(df)
    if B is None:
        return np.full(n, np.nan)
    cv = U27.map_bars(df, B, ["cv"])["cv"]
    a = map_day(df, pc_anchor_tab(), ["tpv_last_1", "v_last_1"])
    with np.errstate(invalid="ignore", divide="ignore"):
        av = (b["vwap"] * cv + a["tpv_last_1"]) / (cv + a["v_last_1"])
    av[~(cv > 0)] = np.nan
    return av


@numba.njit(cache=False)
def _ema_macd(newrun, c):
    n = len(c)
    e12 = np.full(n, np.nan)
    e20 = np.full(n, np.nan)
    e26 = np.full(n, np.nan)
    cntp = np.zeros(n, np.int64)
    cntn = np.zeros(n, np.int64)
    a12, a20, a26 = 2.0 / 13.0, 2.0 / 21.0, 2.0 / 27.0
    age = 0
    for i in range(n):
        if newrun[i] or not (c[i] == c[i]):
            if not (c[i] == c[i]):
                age = 0
                continue
            e12[i] = c[i]
            e20[i] = c[i]
            e26[i] = c[i]
            age = 1
        else:
            p12 = e12[i - 1] if e12[i - 1] == e12[i - 1] else c[i]
            p20 = e20[i - 1] if e20[i - 1] == e20[i - 1] else c[i]
            p26 = e26[i - 1] if e26[i - 1] == e26[i - 1] else c[i]
            e12[i] = a12 * c[i] + (1 - a12) * p12
            e20[i] = a20 * c[i] + (1 - a20) * p20
            e26[i] = a26 * c[i] + (1 - a26) * p26
            age += 1
        md = e12[i] - e26[i]
        if age < 60:                  # warm-up: ~2.3 x the slow span before the line is trusted
            continue
        if md > 0:
            cntp[i] = (cntp[i - 1] if i > 0 and not newrun[i] else 0) + 1
        elif md < 0:
            cntn[i] = (cntn[i - 1] if i > 0 and not newrun[i] else 0) + 1
    out_e20 = e20.copy()
    md = e12 - e26
    return out_e20, md, cntp, cntn


def ema_macd(df):
    """Per frame row: continuous 5m EMA20, MACD line, consecutive MACD > 0 / < 0 bar counts (full-session bars)."""
    n = len(df)
    P = C3.full_bars(df)
    if P is None or not len(P):
        return {k: np.full(n, np.nan) for k in ("e20", "macd", "cntp", "cntn")}
    ck = ("em", id(P))
    if ck not in _MEM:
        for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "em"]:
            del _MEM[kk]
        sym = P["symbol"].to_numpy()
        dt = pd.to_datetime(pd.Series(P["date"].to_numpy())).to_numpy("datetime64[D]").astype(np.int64)
        newrun = np.r_[True, (sym[1:] != sym[:-1]) | (dt[1:] - dt[:-1] > 7)]
        e20, md, cp, cn = _ema_macd(newrun, P["c"].to_numpy(float))
        T = P[["symbol", "date", "tod"]].copy()
        T["e20"], T["macd"], T["cntp"], T["cntn"] = e20, md, cp.astype(float), cn.astype(float)
        _MEM[ck] = T
    return C3.map_rows(df, _MEM[ck], ["e20", "macd", "cntp", "cntn"])
