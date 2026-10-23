"""pod-of3-responsive-val-reclaim-inside-value-open-long - Open inside prior value, look below the value-area low and
fail: responsive buying back to the prior TPO POC (LONG).

Source: auction market theory responsive vs initiative activity (Steidlmayer / Dalton) as summarised by LuxAlgo
'Responsive vs Initiative Activity' ('an open in range and in value... market is in balance'; 'initiative attempts
that fail are a classic setup for rotation back through the old range'); Day One Traders-style value-area open
location.
URL: https://www.luxalgo.com/library/concept/responsive-vs-initiative-activity/

VARIANT of 'Volume profile: 80% rule' (requires an open OUTSIDE value) and 'Prior-day volume profile (POC / value
area) touches'. Stated changes: the open must be INSIDE prior value, value is TPO-based, and the trigger is a
look-below-and-fail at VAL.
TPO profile of D-1 (_r210_util): every completed D-1 5m bar (09:35..15:55) adds one count to each 0.05 x atr_d price
bin it touches; POC = the most-counted bin; the value area grows from the POC to >= 70% of all counts.
Rules (plain English, LONG):
  1. Today's open is between D-1 VAL and VAH, and |open - prior close| <= 0.3 x atr_d.
  2. Between 09:45 and 11:30 (bar close 09:50-11:30; the frame starts at the 09:50 bar) a bar trades >= 0.10 x atr_d
     below VAL (the look-below).
  3. After the look-below bar, 2 consecutive 5m closes back above VAL; the second is the signal, with flow3 >= 0.
     Only the first such pair of the day counts.
  4. |spy_fo| <= 0.6%.
  5. D-1 POC is >= 0.25 x atr_d above the entry.
  Entry: signal close, window 09:55-11:30. Stop (GEOM S): session low - 0.05 x atr_d. Target: D-1 TPO POC. Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (955, 1130)
CONTEXT = ["spy_fo"]
LAYERS = ["open inside D-1 TPO value, |gap| <= 0.3 ATR", "look-below VAL by >= 0.10 ATR by 11:30",
          "2 consecutive closes back above VAL, flow3 >= 0", "|spy_fo| <= 0.6", "POC >= 0.25 ATR above entry",
          "stop LOD - 0.05 ATR, target D-1 POC"]

import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r210_util as U  # noqa: E402

_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i])


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _scan(st, tod, l, c, val, atr):
    n = len(c)
    sig = np.zeros(n, np.bool_)
    lb = False
    cnt = 0
    done = False
    for i in range(n):
        if st[i]:
            lb = False
            cnt = 0
            done = False
        if done or not np.isfinite(val[i]) or not np.isfinite(atr[i]):
            continue
        if lb:
            if c[i] > val[i]:
                cnt += 1
                if cnt == 2:
                    sig[i] = True
                    done = True
                    continue
            else:
                cnt = 0
        if not lb and tod[i] <= 1130 and l[i] <= val[i] - 0.10 * atr[i]:
            lb = True
            cnt = 0
    return sig


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    sess = U.session_table(df).copy()
    for nm, v in U.prior(sess, ["poc", "val", "vah"], 1).items():
        sess[nm] = v
    P = U.map_sess(df, k, sess, ["poc_1", "val_1", "vah_1"])
    poc, val, vah = P["poc_1"], P["val_1"], P["vah_1"]
    sig = _scan(U.start(k), tod, b["l"], c, val, atr)
    with np.errstate(invalid="ignore"):
        m = sig & (b["opn"] >= val) & (b["opn"] <= vah) & (np.abs(b["opn"] - b["pc"]) <= 0.3 * atr)
        m &= (U.f(df, "flow3") >= 0) & (np.abs(U.f(df, "spy_fo")) <= 0.6)
        m &= (poc - c) >= 0.25 * atr
        stop[:] = b["lod"] - 0.05 * atr
        tgt[:] = poc
        m &= (stop < c) & (tgt > c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
