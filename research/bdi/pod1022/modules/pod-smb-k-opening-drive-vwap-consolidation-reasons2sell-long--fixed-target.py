"""pod-smb-k-opening-drive-vwap-consolidation-reasons2sell-long--fixed-target - REFERENCE configuration (same entry,
the parent's fixed measured-move target box high + 2 x box height, stop box low, GEOM S, flat 15:55) for the idea below.

Opening drive, consolidation above VWAP, then break,
managed as a Trade2Hold with Reasons2Sell exits (LONG).

Source: SMB Capital - 'PlayBook Checkup: Opening Drive - Consolidation Above VWAP $K' and the Reasons2Sell / 'How to
exit your winning trades properly' posts (Bellafiore).
URL: https://www.smbtraining.com/blog/playbook-checkup-opening-drive-consolidation-above-vwap-k

Exit-logic VARIANT of pod-smb-big-dog-consolidation-above-vwap-break-long. The entry is the same family; what changes
is the exit: no fixed target, the trade is held until a Reason2Sell fires. The sibling file '--fixed-target' has the
SAME entry with the parent's fixed measured-move target (box high + 2 x box height), so the exit change is visible.

Data: the 09:30 open and the 10:00 close per symbol-day from the 1-minute vendor bars (_r24_bars day cache; locked
block never read); VWAP, 5m volume ratio and wicks from the frame.

Rules (plain English):
  Entry:
  1. Opening drive: 10:00 close - 09:30 open >= 0.5 x daily ATR14 and the 10:00 close is above VWAP.
  2. Consolidation: >= 6 consecutive 5m bars, all closing 10:05-11:30, ending on the bar before the entry bar, with
     range (max high - min low) <= 0.35 x daily ATR and every 5m close above VWAP (longest valid box used).
  3. Buy the first 5m close above the consolidation high, bar close by 12:00.
  Initial stop: consolidation low. No target.
  Reasons2Sell (first one wins, exit at that 5m bar's close; the stop is checked first inside every bar):
  (a) a 5m close below VWAP;
  (b) after the trade has made a new high of day, a completed 15-minute bar (clock-aligned :00 / :15 / :30 / :45)
      makes a lower low than the previous 15-minute bar;
  (c) a volume-climax bar (5m volume >= 4x its 20-bar average and upper wick >= 50% of the bar range) once the trade
      has had >= 1.5R open profit (highest high since entry);
  (d) 15:55. Reasons (a)-(c) are evaluated on frame bars up to 15:00; after that only the stop and 15:55 apply.
  GEOM S+x with exit_index. Tweak: none. 2 configurations (this exit + the fixed-target reference). Costs per
  config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r33_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1200)
FIXED_TARGET = True
LAYERS = ["09:30-10:00 drive >= 0.5 ATR, 10:00 close > VWAP", ">= 6-bar box 10:05-11:30, range <= 0.35 ATR, closes > VWAP",
          "close above box high by 12:00", "stop box low; Reasons2Sell: close < VWAP, 15m lower low after new HOD, "
          "volume climax after 1.5R, 15:55"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, atr, o935, c1000, vr, uw, fixed):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    xi = np.full(n, -1, np.int64)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        if not (a > 0 and o935[i0] == o935[i0] and c1000[i0] == c1000[i0]):
            continue
        if c1000[i0] - o935[i0] < 0.5 * a:
            continue
        v10 = False
        for k in range(i0, i1):
            if tod[k] == 1000:
                v10 = c[k] > vw[k]
                break
        if not v10:
            continue
        for i in range(i0 + 1, i1):
            if tod[i] > 1200:
                break
            if tod[i] < 1035:
                continue
            # longest valid box ending at i-1
            bh = -np.inf
            bl = np.inf
            best = -1
            bbh = 0.0
            bbl = 0.0
            for j in range(i - 1, i0 - 1, -1):
                if tod[j] < 1005 or tod[i - 1] > 1130:
                    break
                if not (c[j] > vw[j]):
                    break
                bh = max(bh, h[j])
                bl = min(bl, l[j])
                if bh - bl > 0.35 * a:
                    break
                if i - j >= 6:
                    best = j
                    bbh = bh
                    bbl = bl
            if best < 0 or not (c[i] > bbh):
                continue
            e0 = c[i]
            if not (bbl < e0):
                continue
            m[i] = True
            stop[i] = bbl
            R = e0 - bbl
            if fixed:
                tgt[i] = bbh + 2.0 * (bbh - bbl)
                break
            # Reasons2Sell on frame bars after entry
            H0 = hod[i]
            newh = False
            mx = h[i]
            for k in range(i + 1, i1):
                if c[k] < vw[k]:
                    xi[i] = k
                    break
                if h[k] > H0:
                    newh = True
                mx = max(mx, h[k])
                mm = tod[k] % 100
                if newh and (mm == 0 or mm == 15 or mm == 30 or mm == 45) and k - 5 >= i0:
                    l15 = min(l[k], min(l[k - 1], l[k - 2]))
                    p15 = min(l[k - 3], min(l[k - 4], l[k - 5]))
                    if l15 < p15:
                        xi[i] = k
                        break
                if vr[k] >= 4.0 and uw[k] >= 0.5 and mx - e0 >= 1.5 * R:
                    xi[i] = k
                    break
            break
    return m, stop, tgt, xi


def mask(df):
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(0, bool)
    bb = U.base(df)
    import _r24_bars as R24
    D = U.map_day(df, R24.day(), ["o935", "c1000"])
    m, stop, tgt, xi = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], bb["hod"], bb["vwap"],
                             bb["atr"], D["o935"], D["c1000"], U.f(df, "volumeRatio"), U.f(df, "upper_wick"),
                             bool(FIXED_TARGET))
    _ST[id(df)] = (stop, tgt, xi)
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
