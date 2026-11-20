# BEGINNER SETUP BEG-06-noise-area-breakout (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B06"; backtest research/beginner_1120/BEG-06-noise-area-breakout/RESULTS.md
# Educational only - not financial advice.
"""BEG-06 Noise-area breakout on index ETFs (long and short), on 1-minute RTH bars.

Spec (implemented as written; plainest readings marked [R]):
  universe  SPY, QQQ
  bounds    m_t = 14-day average |close/open - 1| at the same minute of session (ctx.avg_move[t]; the live priors build:
            last 14 prior sessions fetched within 24 calendar days, >= 5 needed, else no trade).
            upper = max(open, prev_close) x (1 + m_t), lower = min(open, prev_close) x (1 - m_t).
            [R: the spec's clause "if the gap is positive the upper bound is anchored at max(open, prev_close); if
            negative the lower bound at min(open, prev_close)" is a no-op if read literally (on a gap-up day
            max(open, pc) IS the open). The cited paper (Zarattini, Aziz & Barbon 2024) and MCF's own
            noise_band_momentum use upper = max(open, pc) x (1+m), lower = min(open, pc) x (1-m) on every day, i.e. the
            gap-fill side of the band is widened. That reading is used.]
  checks    half-hour marks 10:00, 10:30, ..., 15:00 = the close of the 09:59, 10:29, ..., 14:59 bars [R]
  trigger   at a check, if flat: long if close > max(upper, VWAP); short if close < min(lower, VWAP)
            (VWAP = session typical-price VWAP, mcf.features.vwap). Fill at the next bar's open (global convention).
  position  one at a time; re-entry allowed at a LATER check after an exit [R: an exit signalled at a check does not
            reverse at that same check; a hard-stop exit inside bar m allows entry at a check bar k > m]
  stop      hard stop = fill -/+ 0.25 x ATR (daily ATR(14) as of the prior close), intrabar, stop first (gap-through
            fills at the worse of open/stop); 1R = 0.25 x ATR.
            trailing: at each check after entry, long exits if close < max(upper, VWAP), short if close > min(lower,
            VWAP); fill at the next bar's open.
  exit      15:55 bar open if neither stop is hit.
Tweak parameters (pre-registered in PLAN.md; default = base).
"""
from __future__ import annotations

from datetime import time

import numpy as np

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal = Strategy = object

SYMBOLS = ("SPY", "QQQ")
P = dict(first_check=959, last_check=1459, step=30, exit_hhmm=1555, stop_atr=0.25, band_mult=1.0, trail=True,
         side_only=0, max_entries=99)

KIND_TIME, KIND_STOP, KIND_TRAIL = 0, 1, 3


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def is_check(hhmm, p=P):
    mins = (hhmm // 100) * 60 + hhmm % 100 + 1          # bar END minute
    return (hhmm >= p["first_check"]) & (hhmm <= p["last_check"]) & ((mins - 570) % p["step"] == 0)


def session_trades(o, h, l, c, v, hhmm, prev_close, atr, move, p=P):
    """Run one session (bars 09:30..). move = avg |close/open-1| by minute of session (len >= 390) or None.
    -> list of dict(k, j, side, fill, stop, px, kind, xt, x, m, upper, lower, vw). Causal: a decision at check bar k
    uses bars <= k only."""
    if move is None or not (prev_close > 0 and atr > 0) or len(o) < 2:
        return []
    o0 = o[0]
    up_ref, dn_ref = max(o0, prev_close), min(o0, prev_close)
    mos = (hhmm // 100) * 60 + hhmm % 100 - 570
    vw = vwap(h, l, c, v)
    chk = is_check(hhmm, p)
    dist = p["stop_atr"] * atr
    out, pos, last_exit_bar, n_entries = [], None, -1, 0
    n = len(o)
    for k in range(n):
        if hhmm[k] >= p["exit_hhmm"]:
            if pos is not None:
                pos.update(px=o[k], kind=KIND_TIME, xt=int(hhmm[k]), x=k)
                out.append(pos)
                pos = None
            break
        if pos is not None and k >= pos["j"]:
            s, st = pos["side"], pos["stop"]
            if (s == 1 and l[k] <= st) or (s == -1 and h[k] >= st):
                pos.update(px=(min(o[k], st) if s == 1 else max(o[k], st)), kind=KIND_STOP, xt=int(hhmm[k]) + 1, x=k)
                out.append(pos)
                pos, last_exit_bar = None, k
                continue
        if not chk[k]:
            continue
        m = move[min(max(mos[k], 0), len(move) - 1)] * p["band_mult"]
        if not np.isfinite(m) or not np.isfinite(vw[k]):
            continue
        upper, lower = up_ref * (1 + m), dn_ref * (1 - m)
        lo_long, hi_short = max(upper, vw[k]), min(lower, vw[k])
        if pos is not None:
            if k >= pos["j"] and p["trail"]:
                s = pos["side"]
                if (s == 1 and c[k] < lo_long) or (s == -1 and c[k] > hi_short):
                    x = k + 1
                    if x < n and hhmm[x] < p["exit_hhmm"]:
                        pos.update(px=o[x], kind=KIND_TRAIL, xt=int(hhmm[x]), x=x)
                        out.append(pos)
                        pos, last_exit_bar = None, x
            continue
        if k <= last_exit_bar or n_entries >= p["max_entries"]:
            continue
        side = 1 if c[k] > lo_long else (-1 if c[k] < hi_short else 0)
        if side == 0 or (p["side_only"] and side != p["side_only"]):
            continue
        j = k + 1
        if j >= n or hhmm[j] >= p["exit_hhmm"]:
            continue
        pos = dict(k=k, j=j, side=side, fill=float(o[j]), stop=float(o[j] - side * dist), check=int(hhmm[k]) + (41 if hhmm[k] % 100 == 59 else 1),
                   m=float(m), upper=float(upper), lower=float(lower), vw=float(vw[k]))
        n_entries += 1
    if pos is not None:                                   # data ended before 15:55
        pos.update(px=c[-1], kind=KIND_TIME, xt=int(hhmm[-1]) + 1, x=n - 1)
        out.append(pos)
    return out


class BEG06(Strategy):
    """Live interface (mcf.strategies.base): generate(ctx) on the session's 1-minute bars so far. The session is
    replayed causally so the strategy knows whether it is flat; only entries are emitted as Signals (hard stop, exit_by
    15:55). The check-time trailing exit is carried in meta (`trail_check`) - MCF's engine has no check-time trailing
    exit, so a live run would need an engine hook; research only."""
    name = "BEG-06-noise-area-breakout"
    max_signals_per_day = 12

    def eligible(self, ctx) -> bool:
        return ctx.symbol in SYMBOLS and ctx.avg_move is not None

    def generate(self, ctx):
        if not self.eligible(ctx):
            return []
        b = ctx.bars
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        a = [b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
        # add a phantom bar so an entry decided on the last bar is reported (its fill is the next bar's open)
        nxt = hhmm[-1] + 1 if hhmm[-1] % 100 != 59 else hhmm[-1] + 41
        a = [np.r_[x, x[-1]] for x in a]
        trs = session_trades(*a, np.r_[hhmm, nxt], ctx.prev_close, ctx.atr, ctx.avg_move)
        eh = P["exit_hhmm"]
        out = []
        for t in trs:
            ref = a[3][t["k"]]
            out.append(Signal(symbol=ctx.symbol, strategy=self.name, side=t["side"], bar_index=t["k"],
                              stop=ref - t["side"] * P["stop_atr"] * ctx.atr, target=None,
                              exit_by=time(eh // 100, eh % 100),
                              meta={"trail_check": True, "upper": t["upper"], "lower": t["lower"], "m": t["m"]}))
        return out
