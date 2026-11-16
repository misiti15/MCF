"""Effective sessions (owner 2026-11-16): how live, shadow and replay sessions count toward a setup's record.

The numbers live in config/effective_sessions.json - the ONE source the leaderboard (docs/live/index.html) and reviews
read. Rules:
  - 1 live session = live_weight (1.0) effective session (owner correction 2026-11-16; not 1.25).
  - 1 shadow or replay session = 0.35 when its source's held-out accuracy is >= 98% trade match, <= 2% extra trades and
    no optimism; 0.2 at 95-98% (or optimistic, or not yet calibrated = the lower tier); 0 below 95%.
  - 1 session of the 2-year history (full-universe backtest, no live counterpart) = history_weight (0.175): screening /
    experience only, never toward the On Deck or Primary minimums.
  - Shadow / replay R gets a haircut = measured optimism (mean shadow - live R per matched trade, when > 0) + 0.02R.
  - Shadow / replay can move a setup up the testing queue and toward On Deck; On Deck needs >= 5 real live sessions and
    Primary its full live record. If live and shadow disagree beyond noise, live wins.
Educational only - not financial advice."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "effective_sessions.json"


def load(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or CONFIG).read_text())


def optimism(bias_r: float | None, bias_t: float | None = None, cfg: dict | None = None) -> bool:
    """Optimistic = shadow beats live by more than the tolerance, or by a statistically clear margin (one-sided t)."""
    c = cfg or load()
    if bias_r is None or (isinstance(bias_r, float) and math.isnan(bias_r)):
        return False
    if bias_r > float(c["bias_tolerance_r"]):
        return True
    return bias_r > 0 and bias_t is not None and bias_t >= float(c["optimism_t"])


def tier(match: float | None, extra: float | None, bias_r: float | None, bias_t: float | None = None,
         n_days: int = 0, n_live: int = 0, cfg: dict | None = None) -> tuple[str, float]:
    """(tier name, weight per session) of a shadow/replay source measured on held-out days."""
    c = cfg or load()
    if match is None or n_days < int(c["calibration_min_days"]) or n_live < int(c["calibration_min_live_entries"]):
        return "uncalibrated", float(c["uncalibrated_weight"])
    opt = optimism(bias_r, bias_t, c)
    for t in c["tiers"]:
        if match < float(t["min_match"]):
            continue
        if t.get("max_extra") is not None and (extra is None or extra > float(t["max_extra"])):
            continue
        if t.get("no_optimism") and opt:
            continue
        return t["name"], float(t["weight"])
    return "below", float(c["below_weight"])


def haircut(bias_r: float | None, cfg: dict | None = None) -> float:
    """R to subtract from every shadow/replay trade: measured optimism (> 0 part of the bias) + haircut_extra_r."""
    c = cfg or load()
    b = 0.0 if bias_r is None or (isinstance(bias_r, float) and math.isnan(bias_r)) else max(0.0, float(bias_r))
    return round(b + float(c["haircut_extra_r"]), 4)


def effective_sessions(live: float, shadow: float = 0.0, replay: float = 0.0, w_shadow: float | None = None,
                       w_replay: float | None = None, cfg: dict | None = None, history: float = 0.0) -> float:
    """For ranking / the testing queue only; the On Deck and Primary minimums count real live sessions alone."""
    c = cfg or load()
    ws = float(c["uncalibrated_weight"]) if w_shadow is None else float(w_shadow)
    wr = float(c["uncalibrated_weight"]) if w_replay is None else float(w_replay)
    return round(float(c["live_weight"]) * live + ws * shadow + wr * replay + float(c["history_weight"]) * history, 3)


def replay_weight(cfg: dict | None = None) -> tuple[str, float]:
    c = cfg or load()
    r = c.get("replay") or {}
    return tier(r.get("match"), r.get("extra"), r.get("optimism_r"), None,
                n_days=99 if r.get("match") is not None else 0, n_live=10**6, cfg=c)


def on_deck_ready(live_sessions: int, cfg: dict | None = None) -> bool:
    """Shadow / replay never replace the real live sessions On Deck needs."""
    c = cfg or load()
    return int(live_sessions) >= int(c["on_deck_min_live_sessions"])
