"""pod-smb-gap-above-lt-level-rebid-long - Gap and Go above a long-term level, with a buyer re-bidding the level (LONG).

Source: SMB PlayBook entry 'Gap and Go Above LT Level w/ Buyer' (SYY), 'The SMB PlayBook: Compiling our best trades'
(Bellafiore).
URL: https://www.smbtraining.com/blog/the-smb-playbook-compiling-our-best-trades

VARIANT of pod-smb-20d-high-time-acceptance-long. Stated changes: the stock must OPEN above the level (gap), not cross
it intraday, and the trigger is a re-bid double test of the level, not time spent above it.

Data: LT level L = the 60-day high = max daily high of the 60 COMPLETED sessions D-60..D-1 (lib.daily()). Today's open
and the 09:30-09:45 volume come from the 1-minute vendor bars (helper _smbv5_bars, the locked block is never read);
first-15m rvol = 09:30-09:45 volume / its mean over the 20 prior sessions (min 10). ATR14(5m) = atrPct x close; daily
ATR = atr_d (frame). The source has no premarket volume here, so the first-15m rvol is used.

Rules (plain English):
  1. gap >= +2%, and today's open is above L by no more than 1.0 x daily ATR.
  2. First-15m rvol >= 2.
  3. Between 09:45 and 11:30 (bars closing 09:50-11:30) price pulls back to within 0.15 x ATR14(5m) of L (bar low <=
     L + 0.15 ATR5) at least twice, the two touches >= 3 bars apart, and no 5m close below L - 0.1 x ATR14(5m) from
     09:50 through the decision bar (the held bid / re-bid).
  4. After the second touch, a 5m close above the high of the second touch bar (decision bar i, by 12:00 at the
     latest - pre-declared, the source gives no cut-off).
  Entry: next bar open (scorer: close_i). Stop (GEOM S): L - 0.25 x ATR14(5m). Target: HOD retest (the high of day at
  bar i). When bar i itself is at the high of day there is nothing to retest and the source trails under the prior
  bar low once HOD breaks; the scorer has no conditional trail, so that case holds to 15:55 with the stop (no limit).
  Flat 15:55. Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

import _smbv5_bars as V

SIDE = "long"
GEOM = "S"
WINDOW = (955, 1200)
LAYERS = ["gap >= 2%, open above the 60-day high by <= 1 ATR", "09:30-09:45 rvol >= 2",
          "two touches of L (<= L + 0.15 ATR5) >= 3 bars apart 09:50-11:30, no close < L - 0.1 ATR5",
          "close above the 2nd touch bar high", "stop L - 0.25 ATR5, target HOD retest", "09:55-12:00 ET"]
_STASH = {}
_C = {}


def _ctx():
    if "c" in _C:
        return _C["c"]
    dc = V.daily_ctx()[["symbol", "date", "h601"]]
    c = dc.merge(V.dayagg()[["symbol", "date", "o935", "rv0945"]], on=["symbol", "date"], how="inner")
    c = c[(c["rv0945"] >= 2) & (c["o935"] > c["h601"])]
    _C["c"] = c
    return c


@numba.njit(cache=False)
def _kernel(b, e, L, opn, tod, c, h, l, gp, ap, dh, atr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        lv, op = L[s], opn[s]
        a = atr[i0]
        if not (lv == lv and op == op and a > 0 and gp[i0] >= 2.0 and op > lv and op - lv <= 1.0 * a):
            continue
        t1 = -1
        t2 = -1
        for i in range(i0, i1):
            if tod[i] > 1200:
                break
            a5 = ap[i] / 100.0 * c[i]
            if c[i] < lv - 0.1 * a5:
                break
            if t2 >= 0 and i > t2 and c[i] > h[t2]:
                sp = lv - 0.25 * a5
                hod = c[i] + dh[i] * atr[i]
                if sp < c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = hod if hod > c[i] + 0.01 else c[i] + 50.0 * atr[i]
                break
            if t2 < 0 and tod[i] <= 1130 and l[i] <= lv + 0.15 * a5:
                if t1 < 0:
                    t1 = i
                elif i - t1 >= 3:
                    t2 = i
    return m, stop, tgt


def compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if n == 0:
        return z
    try:
        C = _ctx()
    except Exception:  # noqa: BLE001 - no cache -> no trades
        return z
    sym, dat, b, e = V.keys(df)
    g = V.segmap(sym, dat, b, C, ["h601", "o935"])
    f = lambda k: df[k].to_numpy(float)
    return _kernel(b, e, g["h601"], g["o935"], df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"),
                   f("gap"), f("atrPct"), f("dist_hod_atr"), f("atr_d"))


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
