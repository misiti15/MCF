"""GEN exposure 2026-10-25: what-if replay of a clock-aligned 5-minute gate (research only, in-process patch).

    python research/ops/genexposure1025_clockgate.py <python -m mcf.replay run arguments>

Today a lab setup evaluates a symbol only when its 1-minute bar count is a multiple of 5 (LabStrategy.eligible) and
the runner acts only when the signal's bar is the latest bar. A symbol with any missing minute is then out of phase:
its decision bars land on counts that are not multiples of 5 and are never evaluated (genexposure1025.md section 3).
This script patches, IN THIS PROCESS ONLY (no file under mcf/ changes), the alternative the screen measures:
  eligible   the bar-count test (len(bars) % 5 == 0) is replaced by its intent: the latest 1-minute bar is the
             decision bar of a 5-minute clock bucket, i.e. the first bar at or after the bucket's 4th minute
             (LabStrategy._signal's own `end`), and that bucket closes inside the window. For a symbol trading every
             minute this is the same poll as today; for a symbol with a missing minute earlier in the day it is the
             poll the count test now skips. _signal and the runner are unchanged (acts only when the signal's bar is
             the latest bar; first qualifying bar per symbol-day; no refire; no late catch-up)
  fast path  the replay's poll gate (mcf/replay/fast.FastSession.can_act) without its bar-count shortcut
Everything else (masks, frames, context, caps, fills, filters) is the live code. Then runs `python -m mcf.replay run`.
Research only; nothing here trades. Educational only - not financial advice.
"""
from __future__ import annotations

import inspect
import sys
import textwrap

import pandas as pd

from mcf.replay import fast as F
from mcf.strategies import setups as S


def eligible(self, ctx):
    if ctx.avg_dollar_volume < self.min_adv:
        return False
    if self.symbols is not None and ctx.symbol not in self.symbols:
        return False
    n = len(ctx.bars)
    if n < 5:
        return False
    if n == 390:
        return True
    b = ctx.bars.index[-1]
    if b.minute % 5 == 4:
        start = b.floor("5min")                  # the bucket's own 4th-minute bar
    else:
        start = b.floor("5min") - pd.Timedelta(minutes=5)
        if ctx.bars.index[-2] >= start + pd.Timedelta(minutes=4):
            return False                         # not a decision bar: the previous bucket had its own
    close = start + pd.Timedelta(minutes=5)
    hhmm = close.hour * 100 + close.minute
    lo, hi = self.window or (950, 1500)
    if not lo <= hhmm <= hi:
        return False
    if self.prefilter and self.prefilter.startswith(("gap_le:", "gap_ge:")):
        o = float(ctx.bars["open"].iloc[0])
        g = (o / ctx.prev_close - 1) * 100 if ctx.prev_close else float("nan")
        x = float(self.prefilter.split(":", 1)[1])
        return g <= x if self.prefilter.startswith("gap_le:") else g >= x
    if self.prefilter == "new_high_100m":
        h = ctx.bars["high"].to_numpy()
        return len(h) >= 100 and h[-5:].max() >= h[-100:].max()
    return True


def _patch_can_act():
    src = textwrap.dedent(inspect.getsource(F.FastSession.can_act))
    assert "if n < 5 or n % 5:" in src, "FastSession.can_act changed: re-check this patch"
    src = src.replace("if n < 5 or n % 5:", "if n < 5:")
    ns = dict(F.__dict__)
    exec(compile(src, F.__file__, "exec"), ns)
    F.FastSession.can_act = ns["can_act"]


S.LabStrategy.eligible = eligible
_patch_can_act()

if __name__ == "__main__":
    from mcf.replay.__main__ import main

    main(["run", *sys.argv[1:]])
