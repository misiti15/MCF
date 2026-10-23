"""pod-bbt-dileo-vwap-bounce-break-level-bottom-long - VWAP Bounce & Break: a morning bottom at a prior-day level,
EMA9/21 reclaim below VWAP, break of VWAP, buy the first VWAP bounce (LONG).

Source: Bear Bull Traders - Brendon Dileo, 'Strategy 19: VWAP Bounce and Break' / TT Strategy Template 2025 +
'From FOMO to Focus' webinar (Dec 2025).
URL: https://members.bearbulltraders.com/wp-content/uploads/2025/02/TT-Strategy-Template-2025-Brendon-VWAP-Bounce-Break.pdf

VARIANT of the backlog idea 'VWAP reclaim after >= 15-30 min below, entry on the first pullback that holds' and
pod-bbt-vwap-false-breakdown-long. Stated changes: the morning low must be made AT a prior-day level (PDC or PDL, the
template's 'PDC / Y&YY levels') on rising volume; the stock must first close above both EMA9 and EMA21 while still
below VWAP; only the first bounce off VWAP after the break is bought, before 11:00.

Rules (plain English), decision bar i (only bars up to i):
  1. Initial sell-off: the running LOD <= today's open (open proxy = prior close x (1 + gap)) - 0.4 x daily ATR, and
     it was made on frame bar k (the last bar whose low equals the running LOD) closing before 10:40. A LOD set
     before 09:50 cannot be dated on frame bars and does not qualify.
  2. Level: |LOD - prior close| <= 0.10 x daily ATR or |LOD - prior-day low| <= 0.10 x daily ATR.
  3. Bottom volume: volumeRatio of bar k or k-1 >= 1.5, and close_k in the upper half of bar k's range.
  4. After k, a bar j closed above both EMA9 and EMA21 (EMA9 recovered from emaDiff, EMA21 = EMA9 / (1+emaDiff))
     while still below VWAP; later the first bar b > j closed above VWAP (the break).
  5. Bounce: bar i is the first bar after b with low_i <= VWAP_i + 0.05 x daily ATR, and it closes above VWAP_i.
  Entry: close_i, bar close 09:55-11:00. Stop (GEOM S): min(low_i, VWAP_i - 0.10 x daily ATR). Target: entry + 2R
  (template 'typical 2-3R, minimum 1.5R'). Flat 15:55. ADV >= $20M (scorer default) and price > $5 (template: float
  > 20M, price > $5; float is not in the frame). Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

from _bbtr22_util import base

SIDE = "long"
GEOM = "S"
WINDOW = (955, 1100)
MIN_ADV = 20e6
CONTEXT = []
LAYERS = ["LOD <= open - 0.4 ATR set before 10:40", "LOD within 0.10 ATR of PDC or PDL",
          "volumeRatio >= 1.5 at the bottom, close upper half", "close above EMA9 and EMA21 below VWAP, then VWAP break",
          "first VWAP touch after the break closes above VWAP", "stop min(low, VWAP - 0.10 ATR), target 2R",
          "09:55-11:00 ET, price > $5"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, vw, op, pdc, pdl, vr, e9, e21, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        k = -1
        j = -1        # EMA reclaim below VWAP after k
        bb = -1       # VWAP break after j
        done = False  # the first touch after bb has been used
        for i in range(i0, i1):
            if l[i] <= lod[i] + 1e-5 * c[i]:
                k = i            # new / equal low: the sequence restarts
                j = -1
                bb = -1
                done = False
                continue
            if k < 0:
                continue
            if bb >= 0:
                if done:
                    continue
                if l[i] <= vw[i] + 0.05 * atr[i]:
                    done = True
                    if tod[i] < w0 or tod[i] > w1 or not (c[i] > vw[i]) or not (c[i] > 5.0):
                        continue
                    a = atr[i]
                    if not (a > 0 and tod[k] < 1040 and lod[i] <= op[i] - 0.4 * a):
                        continue
                    if not (abs(lod[i] - pdc[i]) <= 0.10 * a or abs(lod[i] - pdl[i]) <= 0.10 * a):
                        continue
                    v_ok = vr[k] >= 1.5 or (k - 1 >= i0 and vr[k - 1] >= 1.5)
                    if not (v_ok and (c[k] - l[k]) >= 0.5 * (h[k] - l[k])):
                        continue
                    sp = min(l[i], vw[i] - 0.10 * a)
                    if sp < c[i]:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = c[i] + 2.0 * (c[i] - sp)
                continue
            if j < 0:
                if e9[i] == e9[i] and c[i] > e9[i] and c[i] > e21[i] and c[i] < vw[i]:
                    j = i
                continue
            if c[i] > vw[i]:
                bb = i
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    if len(df) == 0:
        return np.zeros(0, bool)
    d = base(df)
    m, sp, tp = _kern(d["b"], d["e"], d["tod"], d["c"], d["h"], d["l"], d["lod"], d["vw"], d["op"], d["pdc"],
                      d["pdl"], d["vr"], d["e9"], d["e21"], d["atr"], WINDOW[0], WINDOW[1])
    _ST[id(df)] = (sp, tp)
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
