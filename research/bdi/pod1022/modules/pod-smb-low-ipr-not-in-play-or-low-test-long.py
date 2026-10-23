"""pod-smb-low-ipr-not-in-play-or-low-test-long - 'Not in play' narrow-open stock (IPR <= 0.5): buy the opening-range
low test, target the OR high (LONG).

Source: SMB Capital - SMB Radar Opening Range / In Play filter posts + 'How to find the best stocks into the close'
(stocks not moving away from prices).
URL: https://www.smbtraining.com/blog/how-to-find-the-best-stocks-into-the-close

VARIANT of pod-smb-not-in-play-quiet-vwap-snap-long. What changes: the quiet gate is SMB's IPR opening-range ratio (low
tail) instead of RVOL; the level is the 30-minute opening-range low, not VWAP; the target is the opposite OR edge.

Data: IPR = (09:30-09:45 high - low) / mean of the same over the 20 prior sessions (min 10) and the 09:30-10:00 high /
low come from the 1-minute vendor bars (_r24_bars / _r33_util caches; the rule-19 locked block is never read). SPY's
running range since 09:30 and SPY's daily ATR14 as of D-1 come from _r27_util.spy_tab (completed days only).

Rules (plain English):
  1. At 10:00: IPR <= 0.5 and the 09:30-10:00 opening range (OR) width <= 0.4 x daily ATR.
  2. SPY's range 09:30-10:30 <= 0.4 x SPY's daily ATR (quiet tape), read on the 10:30 bar.
  3. Tag bar (bar close 10:30-14:30): its low comes within 0.1 x OR width of the OR low (low <= ORL + 0.1 x W), it
     closes at or above the OR low, and RSI(5) on 5m <= 30.
  4. Entry: the next 5m close above the prior bar's high (from the bar after the tag), by 15:00.
  Skip / kill: any 5m close below the OR low from 10:05 on (before or after the tag, up to entry) ends the day.
  Stop: ORL - 0.25 x W. Target: ORH - 0.1 x W (only if above entry). Time exit 15:30 (GEOM S+x, EXIT_TOD).
Tweak: none. 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r24_bars as R24
import _r27_util as R27
import _r33_util as U

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1530
WINDOW = (1035, 1500)
CONTEXT = []
LAYERS = ["IPR(09:30-09:45) <= 0.5, OR(09:30-10:00) <= 0.4 ATR", "SPY range by 10:30 <= 0.4 SPY ATR",
          "10:30-14:30 tag within 0.1 W of ORL, no close below ORL, rsi5 <= 30", "next close above prior bar high",
          "stop ORL - 0.25 W, target ORH - 0.1 W, time exit 15:30"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, r5, ok, orh, orl):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok[i0]:
            continue
        H, L = orh[i0], orl[i0]
        w = H - L
        if not (w > 0):
            continue
        tagged = False
        for i in range(i0, i1):
            if tod[i] <= 1000:
                continue
            if c[i] < L:
                break                                   # a 5m close below the OR low ends the day
            if tagged and tod[i] <= 1500 and c[i] > h[i - 1]:
                sp = L - 0.25 * w
                tp = H - 0.1 * w
                if tp > c[i] and sp < c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                break
            if (not tagged) and tod[i] >= 1030 and tod[i] <= 1430 and l[i] <= L + 0.1 * w and r5[i] <= 30:
                tagged = True
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n:
        return z
    bb = U.base(df)
    I = U.map_day(df, U.ipr_tab(), ["ipr"])
    D = R24.daymap(df, ["dr_h", "dr_l"])
    S = R27.map_spy(df, ["rng", "spy_atr"])
    k = bb["k"]
    st = np.r_[True, k[1:] != k[:-1]]
    sel = bb["tod"] == 1030
    gv = np.full(int(k.max()) + 1, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        q = S["rng"] / S["spy_atr"]
    gv[k[sel]] = q[sel]
    spyq = gv[k]
    with np.errstate(invalid="ignore"):
        ok = (I["ipr"] <= 0.5) & ((D["dr_h"] - D["dr_l"]) <= 0.4 * bb["atr"]) & (spyq <= 0.4)
    okd = ok[st][np.cumsum(st) - 1]
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], U.f(df, "rsi5"),
                         np.asarray(okd, np.bool_), D["dr_h"], D["dr_l"])
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
