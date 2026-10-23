"""pod-shannon-ytd-avwap-first-touch-long - First test of the year-to-date anchored VWAP in an uptrend (LONG).

Source: Alpha Trends / Brian Shannon commentary (Traders Union summary: SMH needed to undercut the June low and
approach the year-to-date VWAP for a stronger bounce); Shannon 'Maximum Trading Gains With Anchored VWAP' (the YTD /
yearly VWAP as the primary bias line, per the TradingView 'Ultimate Master VWAP' description).
URL: https://tradersunion.com/news/market-voices/show/2772670-cbrs-ipo-vwap-supply/

NEW anchor (YTD). Not cwt-c-c6-event-avwap (daily bars, earnings / 252-day-high anchors, next-open entries).

Rules (plain English, LONG). Universe: adv20 >= $50M stocks plus the index / sector ETFs that clear it.
YTD-AVWAP = sum(typical x volume) / sum(volume) from the first session of the calendar year: completed sessions from
the regular-session 1-minute vendor bars, plus today's 5-minute bars up to bar i (today's part uses the bar close as
the price). DATA ADAPTATION (declared up front, not a tweak): the 2025 anchor would be 2025-01-02, inside the locked
block, so 2025 is anchored at the first open session after it (2025-03-03); 2024 has no anchor in the data and is
skipped. Skip January; the year must hold >= 30 completed sessions.
  1. Every daily close of the last 20 completed sessions is above that day's YTD-AVWAP (first touch in >= 20
     sessions) and the D-1 close > the daily SMA50.
  2. Today's low comes within 0.15 x atr_d of YTD-AVWAP (low <= YTD + 0.15 ATR) and the low of day never goes more
     than 0.3 x atr_d below it (LOD >= YTD - 0.3 ATR up to the trigger).
  3. The touch happens after 09:50: the low of day through the 09:50 bar is still above YTD + 0.15 ATR, and the
     touching bar closes at 09:55 or later.
  4. SPY fromOpen >= -1.0% at the trigger bar (context spy_fo).
  5. Trigger: after the touch, a 5-minute close above YTD-AVWAP and above the prior bar's high, buyPressure > 0.
  Entry: trigger close, bar close 10:00-14:30 ET. Stop (GEOM S): LOD - 0.05 x atr_d; skip if the risk > 0.7 x atr_d.
  Target: the session VWAP if it is >= 1R above the entry, else the D-1 close if that is >= 1R above, else 1.5R;
  flat 15:55.
No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r26_bars as RB  # noqa: E402
import _r24_bars as R24  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
MIN_ADV = 50e6
CONTEXT = ["spy_fo"]
LAYERS = ["20 closes above YTD-AVWAP, D-1 > SMA50", "low within +0.15 / -0.3 ATR of YTD-AVWAP",
          "touch after 09:50", "SPY fromOpen >= -1%", "close > YTD and > prior high, buyPressure > 0",
          "stop LOD - 0.05 ATR (<= 0.7 ATR), target VWAP / PDC / 1.5R"]
_ST = {}
_C = {}
_LOCK_END = "2025-02-28"


def _ytd_day():
    """Per (symbol, date D): YTD cumulative S / V through D-1, completed sessions in the year, 20-close test."""
    if "y" in _C:
        return _C["y"]
    d = RB.day()[["symbol", "date", "S", "V", "cls"]].copy()
    d = d[d["date"] > _LOCK_END].copy()                       # 2025-03-03 onward (2024 has no year anchor)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    d["yr"] = d["date"].str[:4]
    g = d.groupby(["symbol", "yr"], sort=False)
    d["cS"] = g["S"].cumsum()
    d["cV"] = g["V"].cumsum()
    d["Y"] = d["cS"] / d["cV"].where(d["cV"] > 0)
    d["above"] = (d["cls"] > d["Y"]).astype(float)
    d["k"] = g.cumcount() + 1
    gk = d.groupby(["symbol", "yr"], sort=False)
    d["n20"] = gk["above"].transform(lambda x: x.rolling(20, min_periods=20).sum())
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    for a, b in (("cS", "cS1"), ("cV", "cV1"), ("k", "k1"), ("n20", "n20_1")):
        out[b] = gk[a].shift(1)
    dl = RB.daily()
    s50 = dl.groupby("run")["close"].transform(lambda x: x.rolling(50, min_periods=50).mean())
    t = pd.DataFrame({"symbol": dl["symbol"], "date": dl["date"], "s50_1": s50.groupby(dl["run"]).shift(1),
                      "c_1": dl.groupby("run")["close"].shift(1)})
    out = out.merge(t, on=["symbol", "date"], how="left")
    _C["y"] = out
    return out


def _intraday(df):
    """Today's cumulative close x volume and volume per 5m bar (09:35 onward), from the _r24_bars cache."""
    syms = set(df["symbol"].astype(str))
    parts = []
    for mo in R24._months_of(df):
        p = R24._OUT / "bars" / f"month={mo}.parquet"
        if p.exists():
            b = pd.read_parquet(p, columns=["symbol", "dn", "tod", "c", "v"])
            b["symbol"] = b["symbol"].astype(str)
            parts.append(b[b["symbol"].isin(syms)])
    if not parts:
        return None
    B = pd.concat(parts, ignore_index=True).sort_values(["symbol", "dn", "tod"], kind="mergesort")
    B["cpv"] = B["c"].astype(float) * B["v"].astype(float)
    g = B.groupby(["symbol", "dn"], sort=False)
    B["cs"] = g["cpv"].cumsum()
    B["cv"] = g["v"].cumsum().astype(float)
    return B


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    if not n or "spy_fo" not in df:
        return m, stop, tgt
    ds = pd.Series(df["date"].to_numpy()).astype(str)
    sel = (ds > _LOCK_END).to_numpy() & (ds.str[5:7] != "01").to_numpy()
    if not sel.any():
        return m, stop, tgt
    B = _intraday(df)
    if B is None:
        return m, stop, tgt
    I = RB.map_bars(df, B, ["cs", "cv"])
    D = RB.map_day(df, _ytd_day(), ["cS1", "cV1", "k1", "n20_1", "s50_1", "c_1"])
    with np.errstate(invalid="ignore", divide="ignore"):
        Y = (D["cS1"] + I["cs"]) / (D["cV1"] + I["cv"])
    c, h, l = (df[k].to_numpy(float) for k in ("close", "high", "low"))
    atr = df["atr_d"].to_numpy(float)
    lod = c - df["dist_lod_atr"].to_numpy(float) * atr
    vwap = c / (1 + df["vwapDistPct"].to_numpy(float) / 100)
    pc = c / (1 + df["fromOpen"].to_numpy(float) / 100) / (1 + df["gap"].to_numpy(float) / 100)
    tod = df["tod"].to_numpy(np.int64)
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + ds)[0]
    st = np.r_[True, k[1:] != k[:-1]]
    gid = np.cumsum(st) - 1
    with np.errstate(invalid="ignore"):
        day_ok = sel & (D["k1"] >= 30) & (D["n20_1"] >= 20) & (D["c_1"] > D["s50_1"])
        # 09:50 bar: running LOD still above the zone (no touch through 09:50)
        pre = np.where(tod == 950, lod - (Y + 0.15 * atr), np.nan)
        pre_g = np.full(gid.max() + 1, np.nan)
        pre_g[gid[tod == 950]] = pre[tod == 950]
        pre_ok = pre_g[gid] > 0
        touch = (l <= Y + 0.15 * atr) & (tod >= 955)
        tcum = pd.Series(touch.astype(int)).groupby(gid).cumsum().to_numpy()
        touched_before = (tcum - touch.astype(int)) > 0        # a touch on an EARLIER bar today
        ph = np.r_[np.nan, h[:-1]]
        ph[st] = np.nan
        m = day_ok & pre_ok & touched_before & (lod >= Y - 0.3 * atr)
        m &= (c > Y) & (c > ph) & (df["buyPressure"].to_numpy(float) > 0)
        m &= df["spy_fo"].to_numpy(float) >= -1.0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        s = lod - 0.05 * atr
        risk = c - s
        m &= (risk > 0) & (risk <= 0.7 * atr)
        t = np.where(vwap >= c + risk, vwap, np.where(pc >= c + risk, pc, c + 1.5 * risk))
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
