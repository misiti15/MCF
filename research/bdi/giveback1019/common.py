"""Shared loaders for giveback1019: live trades (run 1, all sessions through 2026-10-16) for Primary (p), Testing 1 (t1),
Testing 2 (t2); SIP 1-min bars; marking; a per-trade 1-min exit simulator with production costs.
Educational only - not financial advice."""
import sqlite3
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/gb")
OUT = Path(__file__).resolve().parent
LAST = "2026-10-16"
ACCTS = ("p", "t1", "t2")
NAMES = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2"}
TZ = "America/New_York"
# config/default.yaml costs (per side, against us): 1 bps + $0.01/sh; stop exits +$0.02/sh; limit/target exits no slippage.
SLIP_BPS, SLIP_SH, STOP_SH = 1.0, 0.01, 0.02
RUNIT = {"p": 19.81, "t1": 9.5, "t2": 6.79}      # median $ risk per trade over all sessions (account "R unit")


def mkt_cost(px, q):            # market exit (flatten / time stop / account flatten)
    return q * (SLIP_SH + px * SLIP_BPS / 1e4)


def stop_cost(px, q):           # stop exit: market cost + extra stop slippage
    return q * (SLIP_SH + STOP_SH + px * SLIP_BPS / 1e4)


def load_trades():
    rows = []
    for a in ACCTS:
        c = sqlite3.connect(S / a / "journal.db")
        t = pd.read_sql("select * from trades where run_id=1 and date<=?", c, params=(LAST,))
        t["acct"] = a
        rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    for x, y in [("nt", "entry_time"), ("et", "exit_time"), ("st", "signal_time")]:
        T[x] = pd.to_datetime(T[y], utc=True, format="mixed").dt.tz_convert(TZ)
    T["R"] = (T.entry - T.stop).abs()
    T["risk"] = T.R * T.shares
    T["radj"] = np.where(T.risk > 0, T.pnl_adj / T.risk, 0.0)        # realized R, costs in (journal pnl_adj)
    T["hold"] = (T.et - T.nt).dt.total_seconds() / 60
    T["hour"] = T.nt.dt.hour
    T["poll"] = T.st.dt.floor("5min").dt.strftime("%H:%M")
    T["uid"] = T.acct + ":" + T.id.astype(str)
    return T.sort_values(["acct", "nt"]).reset_index(drop=True)


@lru_cache(maxsize=4000)
def bars(day, sym):
    f = S / "bars" / day / f"{sym}.parquet"
    if not f.exists():
        return None
    b = pd.read_parquet(f)
    b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    return b[["open", "high", "low", "close"]].sort_index()


def flat_deadline(r):
    """Time a trade would be flattened: the actual exit if it was a time/EOD flatten, else 15:55."""
    if r.exit_reason == "flatten":
        return r.et
    return pd.Timestamp(f"{r.date} 15:55", tz=TZ)


def simulate(r, be_at=None, trail_after=None, trail_r=None, time_n=None, time_r=0.3, stop_mult=1.0,
             scale_at=None, scale_be=False, cut_at=None, b=None):
    """Replay one live trade on 1-min SIP bars from the bar after the entry minute. Stop-first inside a bar, gaps through
    stops fill at the open, targets fill at the limit, management moves take effect on the next bar.
    stop_mult k: stop k x farther, size 1/k (same $ risk), target price unchanged. cut_at: force a market exit at that
    time (account-level flatten). Returns (pnl_after_costs, exit_reason, exit_time) or None without bars."""
    if b is None:
        b = bars(r.date, r.symbol)
    if b is None or r.R <= 0:
        return None
    s, E, R0 = int(r.side), float(r.entry), float(r.R)
    q = float(r.shares) / stop_mult
    R = R0 * stop_mult
    stop = E - s * R
    tgt = None if pd.isna(r.target) else float(r.target)
    dl = flat_deadline(r)
    if cut_at is not None and cut_at < dl:
        dl = cut_at
    t0 = r.nt.floor("1min") + pd.Timedelta(minutes=1)
    w = b[(b.index >= t0)]
    left, pnl, best, scaled, ts_done = q, 0.0, 0.0, False, False
    for t, o, h, l, c in zip(w.index, w.open.values, w.high.values, w.low.values, w.close.values):
        if t >= dl:
            return pnl + s * (o - E) * left - mkt_cost(o, left), "flatten", t
        fav, adv = (h, l) if s == 1 else (l, h)
        if (adv - stop) * s <= 0:                                   # stop first
            fill = o if (o - stop) * s < 0 else stop
            return pnl + s * (fill - E) * left - stop_cost(fill, left), "stop", t
        if scale_at is not None and not scaled and (fav - (E + s * scale_at * R0)) * s >= 0:
            px = E + s * scale_at * R0
            half = left / 2
            pnl += s * (px - E) * half
            left -= half
            scaled = True
        if tgt is not None and (fav - tgt) * s >= 0:
            return pnl + s * (tgt - E) * left, "target", t
        best = max(best, s * (fav - E) / R0)
        if time_n is not None and not ts_done and (t + pd.Timedelta(minutes=1) - r.nt).total_seconds() / 60 >= time_n:
            ts_done = True                                          # checked once, at the bar close N minutes in
            if s * (c - E) / R0 < time_r:
                return pnl + s * (c - E) * left - mkt_cost(c, left), "time", t
        if be_at is not None and best >= be_at:
            stop = E if (E - stop) * s > 0 else stop
        if scaled and scale_be:
            stop = E if (E - stop) * s > 0 else stop
        if trail_after is not None and best >= trail_after:
            tr = E + s * (best - trail_r) * R0
            if (tr - stop) * s > 0:
                stop = tr
    if len(w) == 0:
        return None
    c = w.close.values[-1]
    return pnl + s * (c - E) * left - mkt_cost(c, left), "eod", w.index[-1]


def mark(r, t):
    """Marked value of a trade at minute t (close of the bar that ends at t): 0 before entry, pnl_adj once exited,
    else open P/L at the last 1-min close before t less a market exit cost."""
    if r.nt >= t:
        return 0.0
    if r.et <= t:
        return float(r.pnl_adj)
    b = bars(r.date, r.symbol)
    if b is None:
        return 0.0
    bb = b[b.index < t]
    if bb.empty:
        return 0.0
    px = bb.close.values[-1]
    return float(r.side * (px - r.entry) * r.shares - mkt_cost(px, r.shares))


def grid(day, start="09:31", end="16:00"):
    return pd.date_range(pd.Timestamp(f"{day} {start}", tz=TZ), pd.Timestamp(f"{day} {end}", tz=TZ), freq="1min")


def marked_matrix(d, day):
    """Matrix trades x minutes of marked value (vectorised per trade)."""
    g = grid(day)
    M = np.zeros((len(d), len(g)))
    for i, r in enumerate(d.itertuples()):
        b = bars(day, r.symbol)
        closed = g >= r.et
        openm = (g > r.nt) & ~closed
        M[i, closed] = r.pnl_adj
        if openm.any() and b is not None:
            # 1-min bar labelled t covers [t, t+1); its close is known at t+1 -> value at grid time g uses bar g-1min
            cl = b.close.reindex(g - pd.Timedelta(minutes=1)).ffill().values
            if np.isnan(cl).all():
                continue
            cl = pd.Series(cl).ffill().bfill().values
            M[i, openm] = r.side * (cl[openm] - r.entry) * r.shares - r.shares * (SLIP_SH + cl[openm] * SLIP_BPS / 1e4)
    return g, M
