"""pod-shannon-wtd-avwap-reclaim-mtd-hold-etf-long - Week-to-date AVWAP reclaim while the month-to-date AVWAP holds
(index / sector ETF LONG).

Source: Alpha Trends / Brian Shannon market note 'Brian Shannon notes market rebound above weekly anchored VWAP'
(2026-05-21): the indexes dipped below a rising 5-period MA, recovered the week-to-date AVWAP and never reached the
month-to-date AVWAP, which he read as buyers back in control.
URL: https://alphatrends.net/archives/podcast/brian-shannon-notes-market-rebound-above-weekly-anchored-vwap/

NEW anchor family (calendar week / month anchored VWAPs). Closest relatives: pod-shannon-avwap-handoff-long and the
session-VWAP reclaims; here the reference lines are multi-day calendar AVWAPs, not the session VWAP.

Rules (plain English, LONG). Universe: SPY, QQQ, IWM, DIA and the 11 SPDR sector ETFs.
WTD-AVWAP = sum(typical x volume) / sum(volume) over every 5-minute bar from the first session open of the calendar
week up to bar i; MTD-AVWAP the same from the first session open of the month (bars 09:35..16:00 from the 1-minute
vendor bars, completed sessions + today's bars up to bar i only).
  1. Tue-Fri and the week already holds at least one completed session (WTD is not just today).
  2. Daily SMA5 at D-1 > SMA5 at D-2 and the D-1 close > the daily SMA20 (uptrend).
  3. + 5. Trigger bar i: the first 5-minute close above WTD-AVWAP after a close below it, where the previous bar (today,
     or D-1's last bar when D-1 is in this week) closed below WTD-AVWAP; the trigger also needs close > session VWAP
     and volumeRatio >= 1.0.
  4. Today is at least the 3rd session of the month, and the lowest 5-minute low from the month's 3rd session up to
     bar i is above the current MTD-AVWAP + 0.05 x atr_d (the month anchor was never touched).
  Entry: trigger close, bar close 10:00-14:30 ET, one per symbol-day. Stop (GEOM S): min(LOD, MTD-AVWAP) - 0.05 x
  atr_d; skip if the risk > 0.6 x atr_d. Target: the week-to-date high, or entry + 2R when that is nearer (2R when
  the WTD high is not above the entry); otherwise flat 15:55.
Reading of rule 3/5: the source's "first close above after a close below" is taken as the bar that crosses up from a
close below (the scorer then keeps the first qualifying bar per day). No tweak made. Costs per config/default.yaml.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r26_bars as RB  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
LAYERS = ["Tue-Fri, WTD has a completed session", "SMA5 rising at D-1, D-1 close > SMA20",
          "close crosses up through WTD-AVWAP from below", "month low since session 3 > MTD-AVWAP + 0.05 ATR",
          "close > session VWAP, volumeRatio >= 1", "stop min(LOD, MTD) - 0.05 ATR (risk <= 0.6 ATR)",
          "target WTD high or 2R if nearer"]
_ST = {}
_C = {}


def _feat():
    """Per ETF 5m bar: WTD / MTD AVWAP, cross flag, month-low-since-session-3, WTD high, calendar flags."""
    if "bars" in _C:
        return _C["bars"]
    B = RB.etf_bars(SYMBOLS).copy()
    sy = B["symbol"].to_numpy()
    dn = B["dn"].to_numpy(np.int64)
    tpv, v = B["tpv"].to_numpy(float), B["v"].to_numpy(float)
    c, h, l = B["c"].to_numpy(float), B["h"].to_numpy(float), B["l"].to_numpy(float)
    n = len(B)
    ar = np.arange(n)
    scode = pd.factorize(sy)[0].astype(np.int64)
    week = (dn + 3) // 7                                    # Monday-based calendar week
    mon = pd.to_datetime(dn, unit="D")
    mkey = (mon.year * 12 + mon.month).to_numpy(np.int64)
    Ctp, Cv = np.cumsum(tpv), np.cumsum(v)

    def anchored(gkey):
        new = np.r_[True, gkey[1:] != gkey[:-1]]
        a = np.maximum.accumulate(np.where(new, ar, 0))
        num = Ctp - Ctp[a] + tpv[a]
        den = Cv - Cv[a] + v[a]
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / den, np.nan), a

    wk = scode * 10_000_000 + week
    mk = scode * 10_000_000 + mkey
    wtd, wa = anchored(wk)
    mtd, ma = anchored(mk)
    # completed session in this week before today
    B["wtd"], B["mtd"] = wtd, mtd
    B["wk_prior"] = (dn[wa] < dn).astype(float)
    B["dow"] = ((dn + 3) % 7).astype(float)                # Monday = 0
    # session number of the day inside its month (1-based)
    dkey = scode * 100_000 + dn
    dstart = np.r_[True, dkey[1:] != dkey[:-1]]
    sess = pd.Series(dstart.astype(int)).groupby(mk).cumsum().to_numpy()
    B["sess_m"] = sess.astype(float)
    lo3 = np.where(sess >= 3, l, np.inf)
    B["low3"] = pd.Series(lo3).groupby(mk).cummin().to_numpy()
    B["wtdh"] = pd.Series(h).groupby(wk).cummax().to_numpy()
    prev_ok = np.r_[False, wk[1:] == wk[:-1]]
    pc = np.r_[np.nan, c[:-1]]
    pw = np.r_[np.nan, wtd[:-1]]
    with np.errstate(invalid="ignore"):
        B["xup"] = (prev_ok & (pc < pw) & (c > wtd)).astype(float)
    _C["bars"] = B
    return B


def _daily():
    if "d" in _C:
        return _C["d"]
    d = RB.daily()
    d = d[d["symbol"].isin(SYMBOLS)].copy()
    g = d.groupby("run")["close"]
    s5 = g.transform(lambda x: x.rolling(5, min_periods=5).mean())
    s20 = g.transform(lambda x: x.rolling(20, min_periods=20).mean())
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["s5_1"] = s5.groupby(d["run"]).shift(1)
    out["s5_2"] = s5.groupby(d["run"]).shift(2)
    out["s20_1"] = s20.groupby(d["run"]).shift(1)
    out["c_1"] = d.groupby("run")["close"].shift(1)
    _C["d"] = out
    return out


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    if not n:
        return m, stop, tgt
    F = RB.map_bars(df, _feat(), ["wtd", "mtd", "wk_prior", "dow", "sess_m", "low3", "wtdh", "xup"])
    D = RB.map_day(df, _daily(), ["s5_1", "s5_2", "s20_1", "c_1"])
    c, atr = df["close"].to_numpy(float), df["atr_d"].to_numpy(float)
    lod = c - df["dist_lod_atr"].to_numpy(float) * atr
    tod = df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        m = (F["dow"] >= 1) & (F["dow"] <= 4) & (F["wk_prior"] > 0)
        m &= (D["s5_1"] > D["s5_2"]) & (D["c_1"] > D["s20_1"])
        m &= F["xup"] > 0
        m &= (F["sess_m"] >= 3) & (F["low3"] > F["mtd"] + 0.05 * atr)
        m &= (df["vwapDistPct"].to_numpy(float) > 0) & (df["volumeRatio"].to_numpy(float) >= 1.0)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        s = np.minimum(lod, F["mtd"]) - 0.05 * atr
        risk = c - s
        m &= (risk > 0) & (risk <= 0.6 * atr)
        t2 = c + 2 * risk
        t = np.where(F["wtdh"] > c, np.minimum(F["wtdh"], t2), t2)
    stop = np.where(m, s, np.nan)
    tgt = np.where(m, t, np.nan)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = _compute(df)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
