# BEGINNER SETUP BEG-08-vwap-stretch-snapback (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B08"; backtest research/beginner_1120/BEG-08-vwap-stretch-snapback/RESULTS.md
# Educational only - not financial advice.
"""BEG-08 Stretched-from-VWAP snap-back (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B08, implemented as written; plainest readings marked [R]):
  universe  U0 (prior close >= $5, ADV20 >= $20M) + price >= $20 [R: prior close] + ADV20 >= $100M
            + rank_rvol20 > 30 (RVOL20 = 09:30-09:49 volume / 14-session average, ranked in the day's U0 universe;
            [R] a day without a rank is not traded). Shorts: ETB only (book E90 proxy), never inverse/vol funds.
  RSI5      Wilder RSI(14) on 5-minute RTH closes. [R] continuous across sessions (the prior session seeds it, as on
            a chart); the series restarts after a gap of > 5 calendar days. At 1-minute bar i the value used is the
            last COMPLETED 5-minute bar (bucket ending at or before bar i's close).
  setup     active at bar i (short) when close_i - VWAP_i >= 0.8 x ATR and RSI5_i > 80; (long) VWAP_i - close_i
            >= 0.8 x ATR and RSI5_i < 20. ATR = daily ATR(14) as of the prior close; VWAP = session VWAP from 09:30
            (typical price).
  trigger   [R] on the close of bar k with the setup active at bar k-1: short when close_k < low_{k-1}; long when
            close_k > high_{k-1}. Decision bars 10:00..14:29, fill at the NEXT bar's open (DESIGN global
            convention), so fills fall in 10:01..14:30.
  stop      [R] "the day's extreme since the setup": the highest high (short) / lowest low (long) from the first bar of
            the current setup run (the contiguous run of active bars ending at k-1) through bar k, +/- 0.05 x ATR.
  target    VWAP at bar k (fixed at entry). [R] the 1.0R test uses the decision-bar close: skip if
            |VWAP_k - close_k| < 1.0 x |close_k - stop|. A skipped trigger does not end the day: a later trigger may
            trade. [R] one open position per symbol; after an exit the scan resumes from the exit bar.
  exit      stop first; target fills only when traded through by >= $0.01 (bench10 / Workbench rule); time stop:
            flat at the open of the first bar >= 45 min after the entry bar; never later than 15:55.
Tweaks (PLAN.md) override P keys, one part each.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal, Strategy = None, object

NAME = "BEG-08-vwap-stretch-snapback"
NO_SHORT = {"SQQQ", "SH", "SPXU", "SDS", "QID", "PSQ", "SPXS", "TZA", "SOXS", "UVXY", "VXX", "VIXY", "SVXY", "UVIX",
            "SVIX", "TECS", "FAZ", "LABD", "DOG", "RWM", "SRTY", "TWM", "YANG", "FNGD", "SDOW", "DXD", "TSLQ", "NVDQ"}
P = dict(min_price=20.0, min_adv=100e6, rank_min=30, stretch=0.8, rsi_hi=80.0, rsi_lo=20.0, rsi_n=14,
         win_lo=1000, win_hi=1429, stop_atr=0.05, stop_mult=1.0, min_tgt_r=1.0, hold_min=45, exit_at=1555,
         tgt_frac=1.0, max_run=None)


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def wilder_rsi(close, n=14):
    """Wilder RSI over a 1-D array (NaN until n changes are seen)."""
    c = np.asarray(close, float)
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    d = np.diff(c)
    g, ls = np.clip(d, 0, None), np.clip(-d, 0, None)
    ag, al = g[:n].mean(), ls[:n].mean()
    for i in range(n, len(c)):
        if i > n:
            ag = (ag * (n - 1) + g[i - 1]) / n
            al = (al * (n - 1) + ls[i - 1]) / n
        out[i] = 100.0 if al == 0 and ag > 0 else (50.0 if al == 0 else 100 - 100 / (1 + ag / al))
    return out


def rsi5_on_1min(idx, close, n=14, max_gap_days=5):
    """idx: tz-aware DatetimeIndex of RTH 1-minute bar starts (sorted); close: 1-minute closes.
    -> per-1-minute-bar RSI(14) of the last completed 5-minute bar (NaN if none)."""
    s = pd.Series(np.asarray(close, float), index=idx)
    b5 = s.groupby(idx.floor("5min")).last()                      # 5-minute close = last 1-minute close in bucket
    ends = b5.index + pd.Timedelta(minutes=5)
    days = pd.Series(b5.index.normalize())
    seg = (days.diff().dt.days.fillna(0) > max_gap_days).cumsum().to_numpy()
    rsi = np.full(len(b5), np.nan)
    for sg in np.unique(seg):
        m = seg == sg
        rsi[m] = wilder_rsi(b5.to_numpy()[m], n)
    close_t = (idx + pd.Timedelta(minutes=1)).asi8
    pos = np.searchsorted(ends.asi8, close_t, side="right") - 1
    out = np.where(pos >= 0, rsi[np.clip(pos, 0, None)], np.nan)
    return out


def active(c, vw, rsi, atr, p=P):
    """-> int array: -1 short setup active, +1 long setup active, 0 none (per bar)."""
    st = p["stretch"] * atr
    sh = (c - vw >= st) & (rsi > p["rsi_hi"])
    lg = (vw - c >= st) & (rsi < p["rsi_lo"])
    return np.where(sh, -1, np.where(lg, 1, 0))


def decide(k, act, h, l, c, vw, hhmm, atr, p=P):
    """Trigger test on the close of bar k (bars <= k only). -> None, 'skip' or dict(side, stop, tgt, ref, s0)."""
    if k < 1 or not (p["win_lo"] <= hhmm[k] <= p["win_hi"]):
        return None
    side = int(act[k - 1])
    if side == 0:
        return None
    if side < 0 and not c[k] < l[k - 1]:
        return None
    if side > 0 and not c[k] > h[k - 1]:
        return None
    s0 = k - 1
    while s0 - 1 >= 0 and act[s0 - 1] == side:
        s0 -= 1
    if p.get("max_run") and k - s0 > p["max_run"]:      # tweak only: the setup run must be fresh
        return None
    ck = float(c[k])
    off = p["stop_atr"] * atr
    if side < 0:
        stop = float(h[s0:k + 1].max()) + off
    else:
        stop = float(l[s0:k + 1].min()) - off
    dist = abs(ck - stop) * p.get("stop_mult", 1.0)
    if not dist > 0:
        return "skip"
    stop = ck - side * dist
    if side * (float(vw[k]) - ck) < p["min_tgt_r"] * dist:   # the 1.0R test is on the VWAP distance
        return "skip"
    tgt = ck + p.get("tgt_frac", 1.0) * (float(vw[k]) - ck)  # tgt_frac 1.0 = VWAP (the base); tweak only otherwise
    return dict(side=side, stop=float(stop), tgt=float(tgt), ref=ck, s0=int(s0))


def walk(o, h, l, c, hhmm, j, side, stop, tgt, p=P):
    """From entry bar j (filled at its open). -> (px, kind, xt, kx); kind 0 time, 1 stop, 2 target; kx exit bar."""
    m0 = (hhmm[j] // 100) * 60 + hhmm[j] % 100
    for k in range(j, len(o)):
        mk = (hhmm[k] // 100) * 60 + hhmm[k] % 100
        if hhmm[k] >= p["exit_at"] or mk - m0 >= p["hold_min"]:
            return float(o[k]), 0, int(hhmm[k]), k
        if (side > 0 and l[k] <= stop) or (side < 0 and h[k] >= stop):
            fx = float(min(o[k], stop)) if side > 0 else float(max(o[k], stop))   # gap-through: worse of open/stop
            return fx, 1, int(hhmm[k]) + 1, k + 1
        if tgt is not None and ((side > 0 and h[k] >= tgt + 0.01) or (side < 0 and l[k] <= tgt - 0.01)):
            return float(tgt), 2, int(hhmm[k]) + 1, k + 1
    return float(c[-1]), 0, int(hhmm[-1]) + 1, len(o)


def day_trades(o, h, l, c, v, hhmm, rsi, atr, can_short=True, p=P):
    """All trades of one symbol-day. -> list of dict(k, j, fill, side, stop, tgt, ref, s0, px, kind, xt)."""
    vw = vwap(h, l, c, v)
    act = active(c, vw, rsi, atr, p)
    if not can_short:
        act = np.where(act < 0, 0, act)
    out, k = [], 1
    n = len(o)
    while k < n - 1:
        d = decide(k, act, h, l, c, vw, hhmm, atr, p)
        if not isinstance(d, dict):
            k += 1
            continue
        j = k + 1
        fill = float(o[j])
        if d["side"] * (fill - d["stop"]) <= 0 or d["side"] * (d["tgt"] - fill) <= 0:
            k += 1
            continue
        px, kind, xt, kx = walk(o, h, l, c, hhmm, j, d["side"], d["stop"], d["tgt"], p)
        out.append(dict(k=int(k), j=int(j), fill=fill, px=px, kind=kind, xt=xt, **d))
        k = max(kx, k + 1)
    return out


def rsi5_live(bars, prior5=None, n=14):
    """Live form: today's 1-minute bars + ctx.prior5 (prior sessions' 5-minute bars) -> per-1-minute-bar RSI of the
    last completed 5-minute bar (same rule as rsi5_on_1min)."""
    idx = bars.index
    today5 = bars["close"].groupby(idx.floor("5min")).last()
    hist = today5 if prior5 is None or prior5.empty else pd.concat([prior5["close"], today5])
    r = wilder_rsi(hist.to_numpy(float), n)[len(hist) - len(today5):]
    ends = (today5.index + pd.Timedelta(minutes=5)).asi8
    pos = np.searchsorted(ends, (idx + pd.Timedelta(minutes=1)).asi8, side="right") - 1
    return np.where(pos >= 0, r[np.clip(pos, 0, None)], np.nan)


class Beg08VwapStretchSnapback(Strategy):
    """Live class (mcf.strategies.base). Called on each bar close with the session's 1-minute bars so far. Needs
    ctx.rank_rvol20 and ctx.prior5 (prior sessions' 5-minute bars, which seed the 5-minute RSI). Emits a market signal
    (next bar open) with the structural stop, the VWAP target and exit_by = fill time + 45 min."""
    name = NAME
    max_signals_per_day = 20

    def eligible(self, ctx) -> bool:
        return (ctx.prev_close >= P["min_price"] and (ctx.avg_dollar_volume or 0) >= P["min_adv"]
                and ctx.rank_rvol20 is not None and ctx.rank_rvol20 > P["rank_min"])

    def generate(self, ctx):
        p = dict(P, **getattr(self, "params", {}))
        b = ctx.bars
        if not len(b) or not self.eligible(ctx):
            return []
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        k = len(b) - 1
        if not (p["win_lo"] <= hhmm[k] <= p["win_hi"]):
            return []
        o, h, l, c, v = (b[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume"))
        rs = rsi5_live(b, ctx.prior5, p["rsi_n"])
        vw = vwap(h, l, c, v)
        act = active(c, vw, rs, ctx.atr, p)
        if ctx.symbol in NO_SHORT:
            act = np.where(act < 0, 0, act)
        d = decide(k, act, h, l, c, vw, hhmm, ctx.atr, p)
        if not isinstance(d, dict):
            return []
        m = (hhmm[k] // 100) * 60 + hhmm[k] % 100 + 1 + p["hold_min"]
        m = min(m, (p["exit_at"] // 100) * 60 + p["exit_at"] % 100)
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=d["side"], bar_index=k, stop=d["stop"],
                       target=d["tgt"], entry_type="market", exit_by=time(m // 60, m % 60),
                       meta={"rsi5": float(rs[k - 1]), "stretch_atr": float((c[k - 1] - vw[k - 1]) / ctx.atr)})]
