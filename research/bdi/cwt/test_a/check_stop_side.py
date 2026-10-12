"""Regression check for the package A stop-side bug (RECHECK_1012.md). Educational only - not financial advice.

Before the 2026-10-12 fix, a structural-exit SHORT entered at or above its stop was "stopped" on the entry minute at
the stop price (below the entry) and booked as a gain; the mirror held for longs entered at or below their stop.
The engine now skips such entries (NaN -> not emitted), like the live LabStrategy structural guard.

    python research/bdi/cwt/test_a/check_stop_side.py      # exits 0 on pass, raises AssertionError on failure
Synthetic one-day frames only: no market data, no locked block.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402


class Fake:
    """Minimal stand-in for engine.Sym: one flat day at `px` (two days for the multi-day exits)."""

    def __init__(self, px=10.0, atr=1.0, days=3):
        self.O = np.full((days, E.NM), px)
        self.H = self.O + 0.05
        self.L = self.O - 0.05
        self.C = self.O.copy()
        self.atr = np.full(days, atr)
        self.ext = np.ones(days)
        self.D = days
        self.seg = np.zeros(days, int)
        self.dnum = np.array(["2025-06-02", "2025-06-03", "2025-06-04"], dtype="datetime64[D]")[:days]

    def next_day(self, d, k=1):
        return d + k if d + k < self.D else None


def main():
    s = Fake()
    m0, e = 100, 10.0
    # the old behaviour, reproduced directly with sim(): a short with its stop BELOW the entry exits at the stop
    px, kind, _ = E.sim(s, 0, m0, -1, 9.9, np.nan)
    assert kind == 1 and px == 9.9 and -1 * (px - e) > 0, "sim no longer shows the raw artifact (check the test)"
    bad = [(-1, 9.9), (-1, 10.0), (1, 10.1), (1, 10.0), (-1, np.nan), (1, np.nan)]
    for side, stop in bad:
        assert not E.stop_ok(side, e, stop)
        assert np.isnan(E.exit_struct(s, 0, m0, side, e, stop)), ("S", side, stop)
        assert np.isnan(E.exit_overnight(s, 0, m0, side, e, stop)), ("ON", side, stop)
        assert np.isnan(E.exit_hold_days(s, 0, m0, side, e, stop, 2)), ("S2", side, stop)
        assert np.isnan(E.exit_half_2r(s, 0, m0, side, e, stop)), ("A3 S", side, stop)
    # stops on the correct side still trade, and a flat day costs money (no free gain)
    for side, stop in [(-1, 10.5), (1, 9.5)]:
        r = E.exit_struct(s, 0, m0, side, e, stop)
        assert np.isfinite(r) and r < 0, ("S ok", side, stop, r)
        assert np.isfinite(E.exit_overnight(s, 0, m0, side, e, stop))
        assert np.isfinite(E.exit_hold_days(s, 0, m0, side, e, stop, 2))
        assert np.isfinite(E.exit_half_2r(s, 0, m0, side, e, stop))
    # geometric exits are untouched (their stop is always e -/+ k R)
    assert np.isfinite(E.exit_geom(s, 0, m0, -1, e, "t1s1"))
    print("check_stop_side: ok (6 wrong-side cases skipped on S / ON / S2 / A3-S; correct-side stops trade)")


if __name__ == "__main__":
    main()
