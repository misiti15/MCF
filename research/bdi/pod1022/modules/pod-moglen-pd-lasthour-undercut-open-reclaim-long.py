"""pod-moglen-pd-lasthour-undercut-open-reclaim-long - Opening undercut of the prior day's last-hour range low, then a
reclaim above it and above the open (daily momentum leader, LONG). Target A = 1.5R.

Source: TraderLion - Richard Moglen, 'Trade Opportunity Case Study of the Week: LEU Range Breakout and
Reconfirmation' (Sep 21 2025): 'the entry was in the first 5 minutes as LEU undercut the prior day's late intraday
range and rallied higher'.
URL: https://traderlion.com/profile/richard-moglen/trade-opportunity-case-study-of-the-week-leu-range-breakout-and-reconfirmation-sep-21-2025/

VARIANT of pod-traderlion-undercut-rally-long. What changes: the level is the prior day's LAST-HOUR range low instead
of the 10-day base low, the window is the first 30 minutes, and there is no wait for a 30-min high break.

Rules (plain English):
  1. Daily (as of D-1, completed days): close > SMA20 > SMA50, close within 10% of the 20-day high (max high
     D-20..D-1), adv20 >= $50M.
  2. Level L = low of the prior session's last-hour 5m bars (bars closing 15:05..15:55; the 15:55-16:00 bar is not in
     the head/tail table - stated proxy).
  3. Between 09:30 and 09:55 (bars closing 09:35..09:55) a 5m low trades below L; the deepest undercut so far is
     between 0.05 and 0.5 x daily ATR.
  4. Trigger: the first 5m close back above L that is also >= the 09:30 open, on a bar closing by 10:00. Enter at
     that close. The scorer frame starts at the 09:50 bar, so a first trigger on the 09:35-09:45 bars cannot be
     entered and the day is skipped (stated deviation; later bars are not used as a substitute).
  5. Stop: session low so far - 0.05 x ATR; skip when entry - stop > 0.6 x ATR. Target A: entry + 1.5R (this
     module); Target B: prior-day high (companion module -tB). Time stop: exit at the 11:30 bar close (GEOM S+x,
     EXIT_TOD 1130). Flat 15:55.
No tweak made. 2 configurations (target A / target B). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U27  # noqa: E402
import _r36_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1130
WINDOW = (950, 1000)
MIN_ADV = 50e6
TARGET = "A"
LAYERS = ["D-1 close > SMA20 > SMA50, within 10% of 20d high, adv >= 50M",
          "09:30-09:55 undercut of prior-day last-hour low by 0.05-0.5 ATR",
          "first close back above L and >= open by 10:00", "stop session low - 0.05 ATR (<= 0.6 ATR)",
          "target 1.5R (A) / PDH (B), time exit 11:30"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, atr, opn, L, pl, pc, pdh, tmode):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        lv = L[i0]
        o = opn[i0]
        if tod[i0] != 950 or not (a > 0) or not (lv == lv) or not (o == o):
            continue
        minlow = np.inf      # deepest low inside the 09:35-09:55 undercut window
        sesslow = np.inf
        done = False
        # pre-frame bars 09:35 / 09:40 / 09:45
        for q in range(3):
            if not (pl[i0, q] == pl[i0, q]):
                continue
            minlow = min(minlow, pl[i0, q])
            sesslow = min(sesslow, pl[i0, q])
            und = lv - minlow
            if pc[i0, q] > lv and pc[i0, q] >= o and und >= 0.05 * a and und <= 0.5 * a:
                done = True      # first trigger before 09:50: cannot be entered -> skip the day
                break
        if done:
            continue
        for i in range(i0, i1):
            if tod[i] > 1000:
                break
            if tod[i] <= 955:
                minlow = min(minlow, l[i])
            sesslow = min(sesslow, l[i])
            und = lv - minlow
            if not (c[i] > lv and c[i] >= o and und >= 0.05 * a and und <= 0.5 * a):
                continue
            sp = sesslow - 0.05 * a
            R = c[i] - sp
            if R > 0 and R <= 0.6 * a:
                t = c[i] + 1.5 * R if tmode == 0 else pdh[i]
                if t > c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = t
            break            # the first qualifying close decides the day
    return m, stop, tgt


def compute(df, tmode):
    n = len(df)
    k = U.key(df)
    b = U.base(df)
    dd = U27.map_daily(df, k, ["c1", "sma201", "sma501", "hi201"])
    hd = U.map_day(df, U.head_tab(), ["lhl_1", "l935", "l940", "l945", "c935", "c940", "c945"])
    with np.errstate(invalid="ignore"):
        ok = (dd["c1"] > dd["sma201"]) & (dd["sma201"] > dd["sma501"]) & (dd["c1"] >= 0.9 * dd["hi201"])
    L = np.where(ok, hd["lhl_1"], np.nan)
    pl = np.column_stack([hd["l935"], hd["l940"], hd["l945"]])
    pc = np.column_stack([hd["c935"], hd["c940"], hd["c945"]])
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["atr"], b["opn"], L, pl, pc, b["pdh"], tmode)


def mask(df):
    m, s, t = compute(df, 0 if TARGET == "A" else 1)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


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
