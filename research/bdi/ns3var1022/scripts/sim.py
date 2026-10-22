"""ns3var1022 exit simulator on the stored 5-minute forward paths (PLAN.md). Entry at the signal bar close; stop-first
when stop and target fall in the same bar; timed exit at the close of the last bar <= 15:55 (lab convention,
mcf/research/setup_lab._outcomes_asym). Production costs as mcf.research.gates.prod_r (1c + 1 bps per side, exit
side free on a target limit fill, +2c on stop fills, time-of-day entry multiplier) and x3 on the extended tier
(|gap| >= 20% or price < $5) as gates1021 scan.prod_r_tier. Returns R in units of the $ risk per share
(kd x 0.25 x daily ATR). Educational only - not financial advice."""
from __future__ import annotations

import numpy as np

from nv import ROOT  # noqa: F401  (puts the repo on sys.path)
from mcf.research.gates import SLIP_BPS, SLIP_PS, STOP_EXTRA, tod_cost_mult

STOP, TGT, TIMED, TSTOP = 1, 2, 0, 3


def simulate(E, D, H, L, C, T, side, tod_entry, gap, ku=1.0, kd=1.0, be=None, trail=None, trail_after=None,
             time_bars=None, flat_tod=None, scale=None, scale_be=False):
    """Vectorised over trades. E entry price, D = 0.25 x daily ATR, H/L/C/T forward paths (n x m, NaN padded).
    ku target (x D, None = no target), kd stop (x D). be: move the stop to entry once +be x D was reached (from the next
    bar). trail: trailing stop trail x D behind the best price (from the next bar), active once +trail_after x D
    was reached (None = from entry). time_bars: exit at the close of bar k (k = 1 is the first bar after entry).
    flat_tod: exit at the close of the first bar with tod >= flat_tod. scale: half the position exits at +scale x D
    (limit); scale_be moves the rest's stop to entry after the scale-out. Returns (r, exit_tod, kind)."""
    E, D = np.asarray(E, float), np.asarray(D, float)
    n, m = H.shape
    s = 1.0 if side == "long" else -1.0
    stop = E - s * kd * D
    tgt = E + s * ku * D if ku is not None else np.full(n, np.nan)
    alive = np.isfinite(E) & np.isfinite(D) & (D > 0)
    best = E.copy()
    scaled = np.zeros(n, bool)
    pnl_rest = np.full(n, np.nan)       # price P/L per share of the (remaining) position, signed
    kind = np.full(n, TIMED)
    ex_t = np.asarray(tod_entry, float).copy()
    last_c = E.copy()
    last_t = np.asarray(tod_entry, float).copy()
    stop_fill = np.zeros(n, bool)
    tgt_fill = np.zeros(n, bool)
    done = ~alive
    for j in range(m):
        h, l, c, t = H[:, j], L[:, j], C[:, j], T[:, j]
        ok = (~done) & np.isfinite(c) & (t <= 1555)
        if not ok.any():
            break
        hs = ok & ((l <= stop) if s > 0 else (h >= stop))
        ht = ok & ~hs & np.isfinite(tgt) & ((h >= tgt) if s > 0 else (l <= tgt))
        pnl_rest = np.where(hs, s * (stop - E), pnl_rest)
        pnl_rest = np.where(ht, s * (tgt - E), pnl_rest)
        kind = np.where(hs, STOP, np.where(ht, TGT, kind))
        stop_fill |= hs
        tgt_fill |= ht
        ex_t = np.where(hs | ht, t, ex_t)
        done = done | hs | ht
        still = ok & ~hs & ~ht
        if scale is not None:
            sp = E + s * scale * D
            hsc = still & ~scaled & ((h >= sp) if s > 0 else (l <= sp))
            scaled |= hsc
            if scale_be:
                stop = np.where(hsc, E, stop)
        last_c = np.where(still, c, last_c)
        last_t = np.where(still, t, last_t)
        ex_now = np.zeros(n, bool)
        if time_bars is not None and j + 1 == time_bars:
            ex_now |= still
        if flat_tod is not None:
            ex_now |= still & (t >= flat_tod)
        pnl_rest = np.where(ex_now, s * (c - E), pnl_rest)
        kind = np.where(ex_now, TSTOP, kind)
        ex_t = np.where(ex_now, t, ex_t)
        done = done | ex_now
        upd = still & ~ex_now
        best = np.where(upd, np.maximum(best, h) if s > 0 else np.minimum(best, l), best)
        fav = s * (best - E)
        if be is not None:
            mv = upd & (fav >= be * D - 1e-12)
            stop = np.where(mv, np.maximum(stop, E) if s > 0 else np.minimum(stop, E), stop)
        if trail is not None:
            act = upd & (fav >= (trail_after or 0.0) * D - 1e-12)
            ts = best - s * trail * D
            stop = np.where(act, np.maximum(stop, ts) if s > 0 else np.minimum(stop, ts), stop)
    # still open after the last bar <= 15:55: timed exit at that close
    op = (~done) & alive
    pnl_rest = np.where(op, s * (last_c - E), pnl_rest)
    ex_t = np.where(op, last_t, ex_t)
    risk = kd * D
    px = E
    ent = (SLIP_PS + px * SLIP_BPS) * tod_cost_mult(tod_entry)
    exit_mkt = SLIP_PS + px * SLIP_BPS
    # remaining leg cost (per share of that leg)
    leg_cost = np.where(tgt_fill, 0.0, exit_mkt) + np.where(stop_fill, STOP_EXTRA, 0.0)
    if scale is not None:
        w = np.where(scaled, 0.5, 1.0)
        pnl = np.where(scaled, 0.5 * scale * D, 0.0) + w * pnl_rest
        cost = ent + w * leg_cost          # the scale-out half exits on a limit (free)
    else:
        pnl, cost = pnl_rest, ent + leg_cost
    tier = np.where((np.abs(np.asarray(gap, float)) >= 20) | (px < 5), 3.0, 1.0)
    r = (pnl - tier * cost) / risk
    r = np.where(alive, r, np.nan)
    return r, ex_t, kind
