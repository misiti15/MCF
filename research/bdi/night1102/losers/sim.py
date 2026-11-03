"""1-minute path simulator for the what-ifs (paired: every variant vs the same engine's baseline, never vs live P/L).
Costs (production, as research/history2y rescore): 1c + 1 bps per side, exit side free on target fills, +2c on stop
fills; stop-first inside a bar; a gap through the stop fills at the open; flatten at 15:55 close.
Educational only - not financial advice."""
import numpy as np

C_PS, C_BPS, STOP_X = 0.01, 1e-4, 0.02


def cost(px, kind):
    c = C_PS + C_BPS * px  # entry side
    if kind != "target":
        c += C_PS + C_BPS * px
    if kind == "stop":
        c += STOP_X
    return c


def run(o, h, l, c, i0, side, entry, d, td, end, be_at=None, time_stop=None, partial=None, wide=1.0, scratch=None):
    """Trade entered at `entry` (price) at the START of bar i0 (bars i0.. are live). d = stop distance/share, td = target
    distance (np.nan = no target). Returns (R in units of the ORIGINAL $ risk, exit kind, exit bar, mfe_R before exit).
    scratch=(N, m): exit at the close of the N-th bar if the MFE so far is < m R.
    wide: stop distance x wide at the same $ risk (shares / wide); target price unchanged."""
    ds = d * wide
    stop = entry - side * ds
    tgt = entry + side * td if td == td else np.nan
    sh = 1.0 / wide  # shares relative to baseline (risk $ = d per baseline share)
    mfe = 0.0
    realized = 0.0
    left = 1.0
    beon = False
    last = end if time_stop is None else min(end, i0 + time_stop - 1)
    for i in range(i0, last + 1):
        st = entry if beon else stop
        # stop first (gap through: open)
        if side * (l[i] if side > 0 else h[i]) <= side * st:
            px = o[i] if side * o[i] <= side * st else st
            kind = "be" if beon else "stop"
            pnl = side * (px - entry) - cost(entry, "stop")
            return realized + left * pnl * sh / d, kind, i, mfe
        fav = (h[i] - entry) if side > 0 else (entry - l[i])
        if partial is not None and left == 1.0 and fav >= partial * d:
            realized += 0.5 * (partial * d - cost(entry, "target")) * sh / d
            left = 0.5
        if tgt == tgt and side * ((h[i] if side > 0 else l[i]) - tgt) >= 0:
            pnl = side * (tgt - entry) - cost(entry, "target")
            return realized + left * pnl * sh / d, "target", i, max(mfe, fav / d)
        mfe = max(mfe, fav / d)
        if scratch is not None and i - i0 + 1 == scratch[0] and mfe < scratch[1]:  # no progress: out at this bar's close
            pnl = side * (c[i] - entry) - cost(entry, "flat")
            return realized + left * pnl * sh / d, "scratch", i, mfe
        if be_at is not None and mfe >= be_at:
            beon = True  # active from the next bar
    px = c[last]
    pnl = side * (px - entry) - cost(entry, "flat")
    return realized + left * pnl * sh / d, "time" if time_stop and last < end else "flatten", last, mfe
