"""pod-r3-eod-loser-reversal-spy-newhod-long - Afternoon loser snap-back when SPY prints a new session high (LONG).

Source: Baltussen, Da & Soebhag, 'End-of-Day Reversal' (OptionMetrics research summary); parent idea wi-eod-reversal
in research/backlog.jsonl.
URL: https://optionmetrics.com/research/a-soebhag-g-baltussen-and-z-da-end-of-day-reversal/

Variant of wi-eod-reversal (never scored) and the Baltussen last-30-minute low-minus-high reversal: (a) an index
event trigger, SPY at a new session high after 13:30; (b) entry 14:00-15:00, inside the harness window, instead of
15:30; (c) the stock must already have stopped falling.
Rules (plain English):
  1. SPY event: spy_fo at this (date, tod) equals the max spy_fo of the day so far (from the 09:50 bar on; the
     frame has no earlier bars) and spy_fo > +0.2.
  2. Intraday loser: fromOpen <= -2.0% and gap > -6% (the earnings blackout is already applied by the scorer).
  3. Stabilised: dist_lod_atr >= 0.15 and the LOD was set at least 6 bars ago (min low of the last 6 bars > LOD).
  4. flow3 > 0 and rsi between 30 and 50.
  Window 14:00-15:00. Entry at close. Stop (GEOM S): LOD - 0.05 x atr_d. No target: hold to 15:55 (the
  reversal-into-close thesis). Scorer control: hold. The stated second geometry t05s1 is the sibling module
  pod-r3-eod-loser-reversal-spy-newhod-long-t05s1 (same mask).
Harness notes (pre-declared): the LOD comes from close - dist_lod_atr x atr_d (running low of day). No tweak used.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r28_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1400, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["SPY at a new session high (spy_fo = running max) and spy_fo > 0.2", "fromOpen <= -2, gap > -6",
          "dist_lod_atr >= 0.15, LOD set >= 6 bars ago", "flow3 > 0, rsi 30..50", "14:00-15:00",
          "stop LOD - 0.05 ATR, hold to 15:55"]
_ST = {}


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[i])


def spy_newhigh(df):
    d = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                      "s": U.f(df, "spy_fo")})
    t = d.dropna().drop_duplicates(["date", "tod"]).sort_values(["date", "tod"])
    t["mx"] = t.groupby("date")["s"].cummax()
    t = t.set_index(["date", "tod"])["mx"]
    mx = t.reindex(pd.MultiIndex.from_arrays([d["date"], d["tod"]])).to_numpy(float)
    return d["s"].to_numpy(float), mx


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not U.ctx_ok(df, ["spy_fo"]):
        _ST[id(df)] = np.full(n, np.nan)
        return np.zeros(n, bool)
    c, l, atr = U.f(df, "close"), U.f(df, "low"), U.f(df, "atr_d")
    dk = U.daykey(df)
    s, mx = spy_newhigh(df)
    lod = c - U.f(df, "dist_lod_atr") * atr
    lo6 = U.roll_min(l, dk, 6)
    rsi = U.f(df, "rsi")
    tod = df["tod"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        m = (s >= mx - 1e-9) & (s > 0.2)
        m &= (U.f(df, "fromOpen") <= -2.0) & (U.f(df, "gap") > -6.0)
        m &= (U.f(df, "dist_lod_atr") >= 0.15) & (lo6 > lod + 1e-9)
        m &= (U.f(df, "flow3") > 0) & (rsi >= 30) & (rsi <= 50)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = lod - 0.05 * atr
    return np.asarray(m, bool)
