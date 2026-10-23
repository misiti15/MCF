"""pod-smb-spencer-monday-lower-low-pullback-index-long - Spencer market pullback: Monday lower low under Friday's
low, then reclaim (index ETFs) (LONG).

Source: SMB Capital / Steve Spencer - 'Buying A Market Pull Back' Part I and Part II (SMB Training blog): since 1990,
a Monday lower low came before the bounce about 90% of the time.
URL: https://www.smbtraining.com/blog/buying-a-market-pull-back-part-ii

VARIANT of pod-williams-oops-pdl-reclaim-long and pod-cal-turnaround-tuesday-index-reclaim-long. What changes: Monday
only (Tuesday when Monday is a holiday); a multi-day pullback depth gate; the reclaim can come any time in the first
3 hours, not only at the opening gap.

Universe: SPY, IWM, QQQ.
Rules (plain English):
  0. Today is the first session of its calendar week ('Monday'); 'Friday' = the previous session (completed day).
  1. Friday's close is >= 3% below the 10-day closing high (max close of the 10 sessions to Friday), and >= 3 of the
     last 5 sessions closed red (close < prior close).
  2. Monday trades below Friday's low between 09:30 and 11:00 (the day's low as of a bar closing by 11:00, which
     includes 09:30-09:45, is under Friday's low).
  3. Entry: the first 5m close back above Friday's low after that (previous 5m close at or under it; for the 09:50 bar
     the previous close is the 09:45 close from the 1-minute vendor bars), bar close 09:50-12:30.
  Stop: Monday's session low - 0.05 daily ATR. Target: Friday's high or entry + 1.5R, whichever is nearer (levels
  above the entry only). Exit 15:55 (GEOM S). One trade per symbol per week (one eligible day per week).
Frame note: entries start at the 09:50 bar (the frame has no earlier rows), so a 09:45 reclaim is taken at 09:50 only
if the 09:50 bar is the first close above. Tweak: none. 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r33_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1230)
SYMBOLS = ["SPY", "IWM", "QQQ"]
LAYERS = ["first session of the week", "D-1 close >= 3% under the 10-day closing high, >= 3 of 5 red",
          "low under Friday's low by 11:00", "first 5m close back above Friday's low 09:50-12:30",
          "stop LOD - 0.05 ATR, target min(Friday high, 1.5R)"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, lod, atr, ok, pdl, pdh, c945):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok[i0]:
            continue
        L = pdl[i0]
        broke = False
        for i in range(i0, i1):
            if tod[i] > 1230:
                break
            pc = c945[i0] if i == i0 else c[i - 1]
            if broke and c[i] > L and pc <= L:
                sp = lod[i] - 0.05 * atr[i]
                R = c[i] - sp
                tp = c[i] + 1.5 * R
                if pdh[i0] > c[i] and pdh[i0] < tp:
                    tp = pdh[i0]
                if R > 0:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                break
            if tod[i] <= 1100 and lod[i] < L:
                broke = True
                # the breach bar itself may close back above (handled on the next bar via pc <= L); if it already
                # closes above with the previous close under, take it now
                if c[i] > L and pc <= L:
                    sp = lod[i] - 0.05 * atr[i]
                    R = c[i] - sp
                    tp = c[i] + 1.5 * R
                    if pdh[i0] > c[i] and pdh[i0] < tp:
                        tp = pdh[i0]
                    if R > 0:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = tp
                    break
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(0, bool)
    T = U.c945_tab(df)
    if T is None:
        return np.zeros(n, bool)
    bb = U.base(df)
    d = U.map_day(df, U.daily_tab(), ["c1", "h1", "l1", "hi10c_1", "red5_1", "wk_first"])
    C = U.map_day(df, T, ["c945"])
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = (d["wk_first"] == 1) & ((d["hi10c_1"] - d["c1"]) / d["hi10c_1"] >= 0.03) & (d["red5_1"] >= 3)
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["lod"], bb["atr"], np.asarray(ok, np.bool_),
                         d["l1"], d["h1"], C["c945"])
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
