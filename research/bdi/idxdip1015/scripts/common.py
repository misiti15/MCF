"""Shared loading / sample definitions for research/bdi/idxdip1015 (see PLAN.md). Educational only - not financial advice."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "research" / "bdi" / "idxdip1015"
H = ROOT / "data" / "cache_hist" / "1Min"

LOCK = (date(2024, 11, 1), date(2025, 2, 28))
HOLDOUTS = [(date(2026, 4, 1), date(2026, 6, 30)), (date(2026, 9, 16), date(2026, 10, 7))]
H2_START = date(2025, 9, 1)

VARIANTS = {   # owner numbering from the 2026-10-15 scan
    "V1": dict(signal_symbol="QQQ", dip_pct=1.0, dip_by="09:55", symbols=["QQQ", "QLD", "TQQQ"]),
    "V2": dict(signal_symbol="SPY", dip_pct=0.75, dip_by="09:45", symbols=["SPY", "SSO", "SPUU", "SPXL", "UPRO"]),
    "V3": dict(signal_symbol="SPY", dip_pct=0.75, dip_by="09:55", symbols=["SPY", "SSO", "SPUU", "SPXL", "UPRO"]),
    "V5": dict(signal_symbol="SPY", dip_pct=0.5, dip_by="09:45", symbols=["SPY", "SSO", "SPUU", "SPXL", "UPRO"]),
}
TRIGGERS = {"rec05": dict(trigger="recovery", recovery_frac=0.05), "rec10": dict(trigger="recovery", recovery_frac=0.10),
            "rec15": dict(trigger="recovery", recovery_frac=0.15), "rec20": dict(trigger="recovery", recovery_frac=0.20),
            "hi3": dict(trigger="hi3"), "vwap": dict(trigger="vwap")}
EXITS = {"T1030": dict(target=None, exit_by="10:30"),
         "R50": dict(target="retrace", target_frac=0.5), "R75": dict(target="retrace", target_frac=0.75),
         "R100": dict(target="retrace", target_frac=1.0), "VWAP": dict(target="vwap"),
         "TRAIL": dict(target=None, trail_r=1.0, trail_after_r=1.0), "HOLD": dict(target=None)}
EXTENDED = {"SPUU"}   # ADV ~$3M: extended-tier costs (3c/share)


def sample(d: date) -> str:
    if LOCK[0] <= d <= LOCK[1]:
        return "LOCKED"
    if any(a <= d <= b for a, b in HOLDOUTS):
        return "HOLDOUT"
    return "DEV"


def load(sym: str) -> dict:
    """symbol -> {date: RTH 1-minute bars}, locked block removed."""
    df = pd.read_parquet(H / f"{sym}.parquet")
    df = df.between_time("09:30", "15:59")
    out = {}
    for d, g in df.groupby(df.index.date):
        if sample(d) != "LOCKED":
            out[d] = g
    return out
