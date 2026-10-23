"""pod-rule201-ssr-day2-or-break-long - Rule 201 day 2: the short-sale restriction is still active after a -10% day,
break of the 09:30-10:15 range high (LONG).

Source: Barardehi et al., 'Are Short-Selling Restrictions Effective?' (Management Science 2025; price effects persist)
+ Univ. Alicante thesis 'Three essays on short selling bans' (Rule 201 effect sticky up to 3 days).
URL: https://www.financialresearch.gov/working-papers/files/OFRwp-23-08-are-short-selling-restrictions-effective.pdf

NEW trigger family (prior-day SSR state). Distinct from pod-smb-first-green-day-multiday-loser-long (needs no
multi-day run, keys on the regulatory threshold) and from SMB day-2 ideas (those are day 2 of an UP drive).

Data: daily closes / opens as of D-1 (_r34_util, completed days only); the 09:30-10:15 high / low = the frame's
running high / low of day on the 10:15 bar (09:30-09:45 included). Context: breadth_open.

Rules (plain English), universe adv20 >= $50M (MIN_ADV), price >= $10:
  1. Prior day D-1: close <= -10% vs the D-2 close (Rule 201 carries through today), and D-1 did not open on a gap
     <= -15% vs D-2's close (exclude bankruptcy / news gaps).
  2. Today's gap between -3% and +2%.
  3. The 09:30-10:15 range (high - low) <= 1.2 x atr_d (no second leg down), and a 5m bar after 10:15 closes above the
     09:30-10:15 high.
  4. breadth_open >= 0.45 on that bar.
  Entry: that bar's close, bar close 10:20-12:00, one per symbol-day. Stop (GEOM S): 09:30-10:15 low - 0.05 x atr_d.
  Target: 1R limit (the source's 'simplest' choice), else flat 15:55.
Reading (pre-declared): the source suggests S+ts2 as a control; only the S form is scored here (1 configuration).
Tweak: none. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import numpy as np

import _cwt3_bars as C3
import _r33_util as U
import _r34_util as D34

SIDE = "long"
GEOM = "S"
WINDOW = (1020, 1200)
MIN_ADV = 50e6
CONTEXT = ["breadth_open"]
LAYERS = ["D-1 close <= -10% vs D-2, D-1 open gap > -15%", "gap -3%..+2%", "09:30-10:15 range <= 1.2 ATR",
          "close above the 09:30-10:15 high after 10:15", "breadth_open >= 0.45", "price >= 10, adv20 >= 50M",
          "stop 10:15 low - 0.05 ATR, target 1R"]
_ST = {}


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n or "breadth_open" not in df:
        return z
    bb = U.base(df)
    k = bb["k"]
    tod = bb["tod"]
    d = D34.map_daily(df, ["c1", "c2", "o1"])
    h1015 = C3.at_tod(bb["hod"], k, tod, 1015)
    l1015 = C3.at_tod(bb["lod"], k, tod, 1015)
    c, a = bb["c"], bb["atr"]
    gap = U.f(df, "gap")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (d["c1"] / d["c2"] - 1 <= -0.10) & (d["o1"] / d["c2"] - 1 > -0.15)
        m &= (gap >= -3) & (gap <= 2) & (c >= 10)
        m &= (h1015 - l1015) <= 1.2 * a
        m &= (tod > 1015) & (c > h1015)
        m &= U.f(df, "breadth_open") >= 0.45
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        sp = l1015 - 0.05 * a
        tp = c + (c - sp)
        m &= sp < c
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
