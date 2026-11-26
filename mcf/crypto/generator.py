"""Random crypto setup generator: seeded draws from a primitive grammar (in the spirit of mcf/research/generator).

A setup = timeframe + side + 1-3 condition primitives (+ optional session window / weekday-weekend filter) + exit
(ATR stop, ATR target or none, time stop). Every draw is counted (`draw_id` runs 0..N-1 from one seed) and every
draw is scored, including duplicates and ones with no trades, so N is the honest number of configurations tried.

Exit / hold ranges follow the cost break-even (research/crypto_r1/MARKET_RESEARCH.md): costs stay a small share of
R only with wide stops (>= ~1.5-2.5% of price) and multi-hour holds, so stops are 1.5-4 ATR on 15/60-minute bars
and holds run 2-12 hours (24 h max).

Primitives (all on bar closes, no look-ahead):
  window      session window (us_open 13:30-15:00 UTC, asia_open, eu_open, us, us_close) and weekday / weekend
  ret         return over N minutes in ATR units, above / below k
  stretch     (close - EMA20) / ATR above / below k
  vwap        distance from rolling-24h or UTC-session VWAP in ATR units
  volsurge    bar volume / trailing 24h mean >= k (thin pairs: needs real prints)
  btc_lead    BTC moved k ATR over N minutes while the alt lagged by >= g ATR (alts only)
  breakout    close above the prior N-hour high (long) / below the low (short)
  rsi         RSI(14) below / above a level
  round       close within d ATR below / above a round number
  trend       close above / below EMA200
  flush       1-bar drop <= -z sigma with a long lower wick and volume surge (flush-reclaim)
  orb_us      close breaks the 13:30-14:00 UTC range (15-min bars only), taken 14:00-17:00
  asia_break  compressed 00:00-04:00 UTC range (<= k ATR), close breaks it 04:00-12:00
  day_momo    UTC-day move >= k ATR by the US open window (intraday momentum continuation)
Educational only — not financial advice.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .backtest import WINDOWS, Exit

TIMEFRAMES = (15, 60)
PRIMS = ["ret", "stretch", "vwap", "volsurge", "btc_lead", "breakout", "rsi", "round", "trend", "flush", "orb_us",
         "asia_break", "day_momo"]
PRIM_W = np.array([1, 1, 1, 1, 1, 1, 1, 0.4, 0.7, 1, 1, 1, 1], float)   # round numbers de-weighted (MARKET_RESEARCH)
STOPS = (1.5, 2.0, 2.5, 3.0, 4.0)
TARGETS = (2.0, 3.0, 4.0, 6.0, None)
HOLD_H = (2, 4, 6, 8, 12, 24)
SHORT_P = 0.15


@dataclass
class Setup:
    draw_id: int
    tf: int
    side: int
    conds: list = field(default_factory=list)          # [(prim, {params})]
    window: str = "any"
    days: str = "all"
    stop_atr: float = 2.0
    target_atr: float | None = 3.0
    hold_h: int = 6

    @property
    def exit(self) -> Exit:
        return Exit(self.stop_atr, self.target_atr, max(1, self.hold_h * 60 // self.tf))

    @property
    def short_research_only(self) -> bool:
        return self.side < 0

    def key(self) -> str:
        return hashlib.sha1(json.dumps(self.spec(), sort_keys=True).encode()).hexdigest()[:10]

    def spec(self) -> dict:
        d = asdict(self)
        d.pop("draw_id")
        return d

    def label(self) -> str:
        cs = "+".join(f"{p}(" + ",".join(f"{k}={v}" for k, v in sorted(a.items())) + ")" for p, a in self.conds)
        tgt = "none" if self.target_atr is None else f"{self.target_atr:g}"
        return (f"{'L' if self.side > 0 else 'S*'} {self.tf}m {self.window}/{self.days} {cs} "
                f"| s{self.stop_atr:g} t{tgt} h{self.hold_h}h")


def _draw_prim(rng: np.random.Generator, p: str, side: int, tf: int) -> dict:
    c = lambda xs: xs[int(rng.integers(len(xs)))]  # noqa: E731
    if p == "ret":
        return {"m": c([30, 60, 240, 720]), "dir": c(["up", "down"]), "k": c([1.0, 2.0, 3.0, 4.0, 6.0])}
    if p == "stretch":
        return {"dir": c(["up", "down"]), "k": c([1.0, 1.5, 2.0, 3.0])}
    if p == "vwap":
        return {"kind": c(["24", "sess"]), "dir": c(["above", "below"]), "k": c([0.5, 1.0, 2.0, 3.0])}
    if p == "volsurge":
        return {"k": c([2.0, 3.0, 5.0])}
    if p == "btc_lead":
        return {"m": c([30, 60, 240]), "k": c([1.0, 2.0, 3.0]), "g": c([0.5, 1.0, 2.0])}
    if p == "breakout":
        return {"H": c([4, 12, 24])}
    if p == "rsi":
        return {"dir": c(["low", "high"]), "lvl": c([20, 25, 30]) if rng.random() < 0.5 else c([70, 75, 80])}
    if p == "round":
        return {"pos": c(["below", "above"]), "d": c([0.25, 0.5, 1.0])}
    if p == "trend":
        return {"dir": c(["up", "down"])}
    if p == "flush":
        return {"z": c([2.5, 3.5, 4.5]), "wick": c([0.3, 0.5]), "vol": c([1.5, 3.0])}
    if p == "orb_us":
        return {}
    if p == "asia_break":
        return {"k": c([3.0, 5.0, 8.0])}
    if p == "day_momo":
        return {"k": c([2.0, 4.0, 6.0]), "dir": c(["with", "against"])}
    raise KeyError(p)


def draw(rng: np.random.Generator, draw_id: int) -> Setup:
    tf = int(rng.choice(TIMEFRAMES))
    side = -1 if rng.random() < SHORT_P else 1
    k = int(rng.choice([1, 2, 2, 3]))
    w = PRIM_W.copy()
    if tf != 15:
        w[PRIMS.index("orb_us")] = 0
    prims = list(rng.choice(PRIMS, size=k, replace=False, p=w / w.sum()))
    conds = [(str(p), _draw_prim(rng, str(p), side, tf)) for p in prims]
    window = "any"
    if not any(p in ("orb_us", "asia_break", "day_momo") for p in prims) and rng.random() < 0.5:
        window = str(rng.choice(["us_open", "asia_open", "eu_open", "us", "us_close"]))
    days = str(rng.choice(["all", "all", "weekday", "weekend"]))
    return Setup(draw_id, tf, side, conds, window, days, float(rng.choice(STOPS)),
                 TARGETS[int(rng.integers(len(TARGETS)))], int(rng.choice(HOLD_H)))


def generate(n: int, seed: int) -> list[Setup]:
    rng = np.random.default_rng(seed)
    return [draw(rng, i) for i in range(n)]


def mask(s: Setup, f: pd.DataFrame, is_btc: bool = False) -> np.ndarray:
    """Boolean entry mask for one pair's feature frame (mcf/crypto/features.build)."""
    n = len(f)
    up = s.side > 0
    m = np.ones(n, bool)
    mod = f["mod"].to_numpy()
    if s.window != "any":
        a, z = WINDOWS[s.window]
        m &= (mod >= a) & (mod < z)
    dow = f["dow"].to_numpy()
    if s.days == "weekday":
        m &= dow < 5
    elif s.days == "weekend":
        m &= dow >= 5
    m &= ~f["filled"].to_numpy()                       # act only on bars with real prints
    col = lambda k: f[k].to_numpy(np.float64)          # noqa: E731
    c = col("c")
    for p, a in s.conds:
        if p == "ret":
            x = col(f"ret{a['m']}")
            m &= (x >= a["k"]) if a["dir"] == "up" else (x <= -a["k"])
        elif p == "stretch":
            x = col("stretch")
            m &= (x >= a["k"]) if a["dir"] == "up" else (x <= -a["k"])
        elif p == "vwap":
            x = col("d_vwap24" if a["kind"] == "24" else "d_vwap_sess")
            m &= (x >= a["k"]) if a["dir"] == "above" else (x <= -a["k"])
        elif p == "volsurge":
            m &= col("vol_ratio") >= a["k"]
        elif p == "btc_lead":
            if is_btc or f"btc{a['m']}" not in f:
                return np.zeros(n, bool)
            b, lag = col(f"btc{a['m']}"), col(f"lag{a['m']}")
            m &= (b >= a["k"]) & (lag >= a["g"]) if up else (b <= -a["k"]) & (lag <= -a["g"])
        elif p == "breakout":
            m &= (c > col(f"hi{a['H']}")) if up else (c < col(f"lo{a['H']}"))
        elif p == "rsi":
            x = col("rsi")
            m &= (x <= a["lvl"]) if a["dir"] == "low" else (x >= a["lvl"])
        elif p == "round":
            x = col("round_dist")
            m &= ((x > 0) & (x <= a["d"])) if a["pos"] == "below" else ((x < 0) & (x >= -a["d"]))
        elif p == "trend":
            e = col("ema200")
            m &= (c > e) if a["dir"] == "up" else (c < e)
        elif p == "flush":
            m &= (col("z1") <= -a["z"]) & (col("lwick") >= a["wick"]) & (col("vol_ratio") >= a["vol"])
        elif p == "orb_us":
            m &= (mod >= 840) & (mod < 1020)
            m &= (c > col("us_hi")) if up else (c < col("us_lo"))
        elif p == "asia_break":
            m &= (mod >= 240) & (mod < 720) & (col("asia_rng") <= a["k"])
            m &= (c > col("asia_hi")) if up else (c < col("asia_lo"))
        elif p == "day_momo":
            m &= (mod >= 810) & (mod < 1020)
            x = col("day_ret")
            sgn = 1 if (a["dir"] == "with") == up else -1
            m &= (x * sgn) >= a["k"]
        else:
            raise KeyError(p)
    return m & np.isfinite(col("atr"))


def window_mask(s: Setup, f: pd.DataFrame) -> np.ndarray:
    """The setup's time filter only (session window, weekday/weekend, time-gated primitives): the random baseline
    draws its entries from these bars."""
    t = Setup(s.draw_id, s.tf, s.side, [(p, a) for p, a in s.conds if p in ("orb_us", "asia_break", "day_momo")],
              s.window, s.days)
    mod = f["mod"].to_numpy()
    m = mask(Setup(s.draw_id, s.tf, s.side, [], s.window, s.days), f)
    for p, _ in t.conds:
        m &= {"orb_us": (mod >= 840) & (mod < 1020), "asia_break": (mod >= 240) & (mod < 720),
              "day_momo": (mod >= 810) & (mod < 1020)}[p]
    return m
