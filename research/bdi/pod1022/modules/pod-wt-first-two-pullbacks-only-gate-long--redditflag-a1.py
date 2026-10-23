"""pod-wt-first-two-pullbacks-only-gate-long--redditflag-a1 - Ross Cameron 'first or second pullback only' gate: block 3rd-and-later continuation entries on
existing long setups (LONG). Sibling configuration: bdi-reddit-bull-flag-pole, gate a1 (ordinal <= 2).

Source: Warrior Trading / Ross Cameron pullback checklist (prefer the first or second pullback; later pullbacks fail
more) via the video-summary checklist; BBT on fading late momentum.
URL: https://youtubesummary.com/summary/BUCPPCXOHbs

LAYER VARIANT on existing long-continuation parents (CWT12-coil-k4-long, pod-wt-bull-flag-breakout-or-bailout-long,
bdi-reddit-bull-flag-pole). The parent trigger, entry, stop and exit stay unchanged; the new condition is a pullback
count.

Rules (plain English):
  Pullback definition: after a new high of day (HOD), the bars up to the next new HOD; it counts when it holds >= 2
  consecutive 5-minute bars with lower highs and retraces >= 0.3 x ATR14(5m) (ATR at the HOD bar) from that HOD.
  Counted per symbol-day from 09:50 (the 09:50 anchor is the HOD so far, which includes 09:30-09:45). State is taken
  as of the bar BEFORE the decision bar, so a breakout bar that makes the new HOD is judged on the pullback it ends.
  1. The parent signal fires (the same bull-flag trigger as bdi-reddit-bull-flag-pole (pole / flag / break of the flag high), 10:00-14:30).
  2. Gate a1: the pullback ordinal (completed qualifying pullbacks + the current one if it already qualifies) <= 2,
     i.e. the entry is on the first or second pullback.
  3. Arm a2 = a1 + the current pullback's depth <= the previous qualifying pullback's depth (no expanding pullbacks;
     passes when there is no earlier one).
  4. Arm a3 = a1 + HOD - today's open < 2.5 x daily ATR14 (not overextended).
  Entry / stop / exit: as in the parent (plain structural exit: stop flag low - 0.02 ATR, target flag high + pole, flat 15:55 (GEOM S)).
This file: parent bdi-reddit-bull-flag-pole, gate a1 (ordinal <= 2).
Gate configurations tried (all scored in the same batch, pre-declared, no tuning): 3 parents x (ungated, a1, a1+a2,
a1+a3), except the reddit structural-exit parent which is scored ungated and a1 only = 7 gated configurations + 3
ungated references. Primary (pre-declared) = CWT12-coil-k4 + a1. Thresholds as in the source idea (0.3 ATR5, <= 2,
2.5 daily ATR); no tweak. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numpy as np

import _r33_util as U

SIDE = "long"
GEOM = 'S'
BAILOUT_BARS = 2
BE_AT_R = 0.0
WINDOW = (1000, 1430)
ARM = 'a1'
LAYERS = ["bull-flag parent (pole, flag, break of flag high)", "pullback gate " + str(ARM)]
_ST = {}


def mask(df):
    _ST.clear()
    if not len(df):
        return np.zeros(0, bool)
    m, stop, tgt = U.flag_signal(df)
    m = np.asarray(m, bool)
    if ARM:
        m &= U.gate(df, U.base(df), ARM)
    _ST[id(df)] = (stop, tgt)
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
