"""Beginner-experiment setups admitted to the testing arenas (owner 2026-11-20 "BEG-ORB yes", "BEG-GNG yes").

Source: research/beginner_1120 (REPORT.md; BEG-01-orb15-in-play/BEG-01.py, BEG-03-gap-and-go/beg03.py). The rules are the
ones scored there, ported to the live Strategy interface so the backtester and the runner share one code path:

* ``beg_orb15`` (BEG-ORB): BEG-01 ORB-15 on stocks in play with the TW-b "stopOR" tweak (stop at the far side of the
  09:30-09:44 range; the one tweak that held on CHECK). Long and short.
* ``beg_gap_and_go`` (BEG-GNG): BEG-03 gap-and-go continuation, long only, as written (base). Its CHECK record is a
  ``1 day`` record (2026-04-23 = 1.77 x the window's total R; -0.004 avg R without it).

Live rules every setup here keeps (MCF standing rules): entries at or after 09:50 ET; flat by 15:55 (BEG-GNG exits at
12:00); shorts only in names the broker flags easy to borrow (the runner's shorts.require_easy_to_borrow) and never in
inverse / leveraged-inverse / volatility funds (the frozen classes of research/owner1120/inverse/shadow.py, plus a
built-in fallback list).

Research results (backtests, costs in; not live results). Educational only - not financial advice.
"""

from __future__ import annotations

import importlib.util
from datetime import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .base import DayContext, Signal, Strategy

ROOT = Path(__file__).resolve().parents[2]
INV_SHADOW = ROOT / "research" / "owner1120" / "inverse" / "shadow.py"
# fallback when the frozen shadow file cannot be read: BEG-01's own list (research/beginner_1120/BEG-01-orb15-in-play)
# plus the short-volatility funds
_FALLBACK_NO_SHORT = frozenset(
    "SQQQ SH SPXU SDS SPXS QID PSQ UVXY VXX SVXY VIXY UVIX SVIX TZA SRTY RWM SOXS TECS FAZ LABD DOG DXD SDOW TWM YANG "
    "TSLQ NVDQ VIXM VXZ".split())
_SHORT_VOL = frozenset("SVXY SVIX".split())   # beta +1 short-vol funds: still volatility funds, never shorted here
_NO_SHORT_CLASSES = ("inv_broad", "inv_sector", "inv_single", "inv_crypto", "long_vol", "inv_name")


@lru_cache(maxsize=1)
def _inverse_classifier():
    """pclass() of the frozen inverse shadow (research/owner1120/inverse/shadow.py), or None if it cannot be loaded."""
    try:
        spec = importlib.util.spec_from_file_location("mcf_inv_shadow_1120", INV_SHADOW)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.pclass
    except Exception:  # noqa: BLE001 - a missing research file must not take the account down; fallback list applies
        return None


def never_short(symbol: str) -> bool:
    """True for inverse / leveraged-inverse / volatility funds (never shorted by the BEG setups)."""
    s = str(symbol).upper()
    if s in _FALLBACK_NO_SHORT or s in _SHORT_VOL:
        return True
    pc = _inverse_classifier()
    return bool(pc is not None and pc(s) in _NO_SHORT_CLASSES)


def _hm(index) -> np.ndarray:
    idx = pd.DatetimeIndex(index)
    return (idx.hour * 100 + idx.minute).to_numpy()


def _vwap(h, l, c, v) -> np.ndarray:
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def _minutes(hhmm: int) -> int:
    return (hhmm // 100) * 60 + hhmm % 100


class BegORB15(Strategy):
    """BEG-ORB: ORB-15 on stocks in play, stop at the far side of OR15 (research/beginner_1120 BEG-01, tweak stopOR).

    Universe at the 09:49 close: price >= $10 (09:49 close; U0 price >= $5), 20-day average dollar volume >= $20M, daily
    ATR(14) >= $0.50, RVOL20 (09:30-09:49 volume / its 14-session average) >= 2.0 and rank by RVOL20 <= 20 (the shared
    rank_rvol20). OR15 = 09:30-09:44 high / low; up candle (09:44 close > 09:30 open) -> buy-stop OR15 high + $0.01,
    down candle -> sell-stop OR15 low - $0.01, doji -> none. Decided at the 09:49 close, the order works on the bars
    09:50-11:29. Stop = the far side of OR15; target 2R from the trigger; breakeven at +1R; flat 15:55. One trade per
    symbol-day. Shorts: ETB only (runner) and never inverse / volatility funds."""

    name = "beg_orb15"
    max_signals_per_day = 1
    OR_END, DECISION = 944, 949

    def _p(self, k, default):
        v = self.params.get(k)
        return default if v is None else v

    def eligible(self, ctx: DayContext) -> bool:
        return (ctx.rank_rvol20 is not None and ctx.rank_rvol20 <= int(self._p("rank_max", 20))
                and ctx.atr is not None and ctx.atr >= float(self._p("min_atr", 0.50))
                and (ctx.avg_dollar_volume or 0) >= float(self._p("min_adv", 20e6)))

    def generate(self, ctx: DayContext) -> list[Signal]:
        b = ctx.bars
        if not len(b):
            return []
        hm = _hm(b.index)
        if hm[0] != 930 or hm[-1] < self.DECISION:
            return []
        d = int(np.flatnonzero(hm <= self.DECISION)[-1])
        if hm[d] != self.DECISION:
            return []
        rv = float(ctx.rvol().iloc[d])
        px = float(b["close"].iloc[d])
        if not (rv >= float(self._p("min_rvol", 2.0)) and px >= float(self._p("min_price", 10.0)) and px >= 5.0):
            return []
        orb = b.iloc[: int((hm <= self.OR_END).sum())]
        o, c = float(b["open"].iloc[0]), float(orb["close"].iloc[-1])
        hi, lo = float(orb["high"].max()), float(orb["low"].min())
        if c == o or hi <= lo:
            return []
        side = 1 if c > o else -1
        if side < 0 and never_short(ctx.symbol):
            return []
        trig = round(hi + 0.01, 2) if side == 1 else round(lo - 0.01, 2)
        stop = lo if side == 1 else hi                                    # stopOR: the far side of OR15
        target = trig + side * float(self._p("target_r", 2.0)) * abs(trig - stop)
        until = int(self._p("order_until", 1130))
        valid = _minutes(until) - _minutes(950)                           # bars 09:50 .. until-1
        return [Signal(ctx.symbol, self.name, side, d, stop, target, "stop", trig, entry_valid_bars=int(valid),
                       exit_by=time(15, 55), be_at_r=float(self._p("be_at_r", 1.0)),
                       meta={"rvol20": rv, "rank20": ctx.rank_rvol20, "or_hi": hi, "or_lo": lo})]


class BegGapAndGo(Strategy):
    """BEG-GNG: gap-and-go continuation, long only, as written (research/beginner_1120 BEG-03 base).

    Universe: prior close $5-$200, 20-day average dollar volume >= $20M, gap (09:30 open / prior close - 1) >= +3.0%,
    RVOL20 >= 3.0. R20 = 09:30-09:49 high / low. Buy-stop R20 high + $0.01 on the bars 09:50-10:59; bar k is armed only
    when the close of bar k-1 is above session VWAP; stop = max(R20 low, VWAP at k-1) - $0.02, and the bar is armed only
    when the stop distance is 0.4%-3% of the trigger. Target 2R (R = trigger - stop); once the trade is +1R the stop
    trails 1R behind the best price; time exit 12:00. One trade per symbol-day.

    The signal is a one-bar stop order decided at the close of bar k-1 (entry_valid_bars=1): the backtester and the
    runner both see the first armed bar whose high reaches the trigger. The 12:00 exit is carried as exit_by (the
    backtester) and as a clock time stop (time_stop_min from the fill bar to 12:00, time_stop_min_r 99) so the runner,
    which manages time stops but not exit_by, also closes at 12:00."""

    name = "beg_gap_and_go"
    max_signals_per_day = 1
    P = dict(min_price=5.0, max_price=200.0, min_adv=20e6, gap_min=3.0, rvol_min=3.0, r20_hi=949, win_lo=950,
             win_hi=1059, stop_off=0.02, trig_off=0.01, min_stop_pct=0.4, max_stop_pct=3.0, tgt_r=2.0, exit_by=1200)

    def _pp(self) -> dict:
        return {**self.P, **{k: v for k, v in self.params.items() if k in self.P and v is not None}}

    def eligible(self, ctx: DayContext) -> bool:
        p = self._pp()
        return (ctx.prev_close is not None and p["min_price"] <= ctx.prev_close <= p["max_price"]
                and (ctx.avg_dollar_volume or 0) >= p["min_adv"])

    @staticmethod
    def arm(k, h, l, c, vw, hhmm, p) -> dict | None:
        """Order for bar k, decided at the close of bar k-1 (uses bars < k only); None = not armed."""
        r20 = hhmm <= p["r20_hi"]
        if k < 1 or not r20[:k].any() or hhmm[0] != 930:
            return None
        hi, lo = float(h[:k][r20[:k]].max()), float(l[:k][r20[:k]].min())
        trig = round(hi + p["trig_off"], 2)
        if not c[k - 1] > vw[k - 1]:
            return None
        stop = max(lo, float(vw[k - 1])) - p["stop_off"]
        dist = trig - stop
        if dist <= 0 or not (p["min_stop_pct"] <= dist / trig * 100 <= p["max_stop_pct"]):
            return None
        return {"trig": float(trig), "stop": float(stop), "tgt": float(trig + p["tgt_r"] * dist)}

    def generate(self, ctx: DayContext) -> list[Signal]:
        p = self._pp()
        b = ctx.bars
        if not len(b) or not ctx.prev_close:
            return []
        hhmm = _hm(b.index)
        if hhmm[0] != 930 or hhmm[-1] < p["win_lo"]:
            return []
        r20 = hhmm <= p["r20_hi"]
        if int(r20.sum()) == 0 or hhmm[int(r20.sum()) - 1] != p["r20_hi"]:
            return []                                                     # the 09:49 bar is needed for RVOL20
        rv = float(ctx.rvol().iloc[int(r20.sum()) - 1])
        gap = (float(b["open"].iloc[0]) / ctx.prev_close - 1) * 100
        if not (gap >= p["gap_min"] and rv >= p["rvol_min"]):
            return []
        h, l, c, v = (b[x].to_numpy(float) for x in ("high", "low", "close", "volume"))
        vw = _vwap(h, l, c, v)
        for k in np.flatnonzero((hhmm >= p["win_lo"]) & (hhmm <= p["win_hi"])):
            a = self.arm(int(k), h, l, c, vw, hhmm, p)
            if a is None or h[k] < a["trig"]:
                continue
            eb = int(p["exit_by"])
            # clock exit for the runner: minutes from the bar after the fill bar (the runner's entry poll) to exit_by
            ts_min = max(1, _minutes(eb) - _minutes(int(hhmm[k])) - 1)
            return [Signal(ctx.symbol, self.name, 1, int(k) - 1, a["stop"], a["tgt"], "stop", a["trig"],
                           entry_valid_bars=1, exit_by=time(eb // 100, eb % 100), trail_r=1.0, trail_after_r=1.0,
                           time_stop_min=int(ts_min), time_stop_min_r=99.0,
                           meta={"rvol20": rv, "gap_pct": gap, "armed_bar": int(hhmm[k])})]
        return []


BEGINNER_REGISTRY = {s.name: s for s in (BegORB15, BegGapAndGo)}
