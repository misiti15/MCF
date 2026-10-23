"""pod-smb-strong-today-rank-quiet-pm-long - SMB Radar 'Strong Today' rank: afternoon hold of the top in-play names on a
quiet index day (LONG).

Source: SMB Training 'SMB Radar Update' posts (Strong Today column = change vs today's open; IPR > 3 = highly in play).
URL: https://www.smbtraining.com/blog/smb-radar-update-2

VARIANT of pod-smb-trend-trend-pm-consolidation-hold-long. Stated changes: a cross-sectional rank entry at a fixed time,
no consolidation pattern, a quiet-SPY gate.

Rules (plain English, LONG), decision bar = the 13:25-13:30 bar (entry at its close = the 13:35 bar's open):
  0. Rank: among the universe names with cumulative relative volume 09:30-13:30 >= 2.5 (volume so far / the mean of
     the same-time cumulative volume of the 20 prior sessions), rank by score = (13:30 close - today's open) / daily
     ATR14 and keep the top 3 of the day.
  1. score >= 0.6.
  2. >= 80% of the 5-minute bars closing 10:00..13:30 closed above session VWAP.
  3. Quiet tape: SPY's range 09:30..13:30 < 0.7 x its 20-day average daily range (completed days D-20..D-1), and SPY is
     within +/-0.4% of its 09:30 open at 13:30.
  4. The stock is within 0.5 x ATR(5m) of its high of day.
  Entry: 13:30 bar close. Stop (GEOM S): VWAP (at 13:30) - 0.1 x ATR(5m). Exit: flat 15:55, no target.
Harness deviations (stated): the source's stop is 'on a 5m close'; the harness checks stops intrabar, so the stop here
is a fixed intrabar stop at the 13:30 VWAP - 0.1 ATR(5m) (stricter). The source's control (a random in-play stock at
13:35) is replaced by the scorer's same-minute random control over the universe.
Data: volume / rvol from _r24_bars (1-minute vendor bars, locked block never read); SPY intraday from _smbv5_bars
evbars; SPY 20-day range from lib.daily() completed days.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1330, 1330)
CONTEXT = ["spy_fo"]
LAYERS = ["cum rvol 13:30 >= 2.5, top 3 by (close - open)/ATR", "score >= 0.6", ">= 80% of bars since 10:00 above VWAP",
          "SPY range < 0.7 x 20d avg range, |SPY from open| <= 0.4%", "within 0.5 ATR5m of HOD",
          "stop VWAP - 0.1 ATR5m, flat 15:55"]

import numpy as np
import pandas as pd

import _cwt3_bars as C
import _r24_bars as R

_ST = {}


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    if not n:
        return m, stop
    b = C.base(df)
    k = C.key(df)
    tod, c = b["tod"], b["c"]
    st = C.start(k)
    a = ((tod >= 1000) & (tod <= 1330)).astype(float)
    ab = (a * (c > b["vwap"])).astype(float)
    ca = pd.Series(a).groupby(k).cumsum().to_numpy()
    cb = pd.Series(ab).groupby(k).cumsum().to_numpy()
    sel = np.flatnonzero(tod == 1330)
    if not len(sel):
        return m, stop
    sub = df.iloc[sel]
    rv = R.bars_for(sub, ["rvc"])["rvc"]
    score = (c[sel] - b["opn"][sel]) / b["atr"][sel]
    dates = pd.Series(sub["date"].to_numpy()).astype(str).to_numpy()
    T = pd.DataFrame({"i": sel, "date": dates, "score": score, "rv": rv})
    T = T[(T["rv"] >= 2.5) & np.isfinite(T["score"])]
    T = T.sort_values(["date", "score"], ascending=[True, False])
    T = T.groupby("date").head(3)
    if not len(T):
        return m, stop
    S = R.spy_bars()
    S = S[S["tod"] == 1330][["date", "run_h", "run_l", "o935", "c"]]
    dfe = R.daily_feats()
    sr = dfe[dfe["symbol"] == "SPY"][["date", "rng20"]]
    T = T.merge(S, on="date", how="left").merge(sr, on="date", how="left")
    i = T["i"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = T["score"].to_numpy() >= 0.6                                                           # (1)
        ok &= cb[i] >= 0.8 * ca[i]                                                                  # (2)
        ok &= ca[i] > 0
        ok &= (T["run_h"] - T["run_l"]).to_numpy() < 0.7 * T["rng20"].to_numpy()                    # (3)
        ok &= np.abs(T["c"].to_numpy() / T["o935"].to_numpy() - 1) <= 0.004
        ok &= (b["hod"][i] - c[i]) <= 0.5 * b["atr5"][i]                                            # (4)
        sp = b["vwap"][i] - 0.1 * b["atr5"][i]
        ok &= sp < c[i]
    m[i[ok]] = True
    stop[i[ok]] = sp[ok]
    return m, stop


def mask(df) -> np.ndarray:
    try:
        m, stop = _compute(df)
    except (KeyError, FileNotFoundError):
        m, stop = np.zeros(len(df), bool), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = stop
    return np.asarray(m, bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
