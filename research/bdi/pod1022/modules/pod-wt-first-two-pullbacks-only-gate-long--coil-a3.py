"""pod-wt-first-two-pullbacks-only-gate-long--coil-a3 - Ross Cameron 'first or second pullback only' gate: block 3rd-and-later continuation entries on
existing long setups (LONG). Sibling configuration: CWT12-coil-k4-long, gate a1 + a3 (HOD - open < 2.5 daily ATR).

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
  1. The parent signal fires (CWT12-coil-k4-long: 09:50-11:30, the HOD touched >= 3 times and the last 4 bars each narrower than half the mean range of the earlier bars and closing within 0.25 daily ATR under it; port of cwt_live_lib.b4a).
  2. Gate a1: the pullback ordinal (completed qualifying pullbacks + the current one if it already qualifies) <= 2,
     i.e. the entry is on the first or second pullback.
  3. Arm a2 = a1 + the current pullback's depth <= the previous qualifying pullback's depth (no expanding pullbacks;
     passes when there is no earlier one).
  4. Arm a3 = a1 + HOD - today's open < 2.5 x daily ATR14 (not overextended).
  Entry / stop / exit: as in the parent (t05s1: target 0.5R, stop 1R, R = 0.25 x daily ATR, flat 15:55; the live config's 0.35R scale-out is not modelled; min ADV $95M as in the live config).
This file: parent CWT12-coil-k4-long, gate a1 + a3 (HOD - open < 2.5 daily ATR).
Gate configurations tried (all scored in the same batch, pre-declared, no tuning): 3 parents x (ungated, a1, a1+a2,
a1+a3), except the reddit structural-exit parent which is scored ungated and a1 only = 7 gated configurations + 3
ungated references. Primary (pre-declared) = CWT12-coil-k4 + a1. Thresholds as in the source idea (0.3 ATR5, <= 2,
2.5 daily ATR); no tweak. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import _r33_util as U

SIDE = "long"
GEOM = "t05s1"
WINDOW = (950, 1130)
MIN_ADV = 95e6
ARM = 'a3'
LAYERS = ["CWT12-coil-k4 parent (HOD tested 3x, last 4 bars tight under it)", "pullback gate " + str(ARM)]


def mask(df):
    bb = U.base(df)
    m = U.coil_k4(df, bb)
    if ARM:
        m &= U.gate(df, bb, ARM)
    return m
