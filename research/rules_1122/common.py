"""Shared helpers for rules_1122 (live journal replays). Educational only - not financial advice."""
import re
import numpy as np
import pandas as pd

LATCHED = {  # account -> first session the per-setup -2R latch was live (config/*.yaml comments; ledger ST-P / ST-A)
    "primary": ("2026-10-29", "2099-12-31"),
    "graveyard": ("2026-10-21", "2099-12-31"),   # default 2.0; some residents override null (their rows show no latch skips)
    "testing": ("2026-10-19", "2026-10-22"),     # Testing 1/2 latch 10-19..10-22 (off from ST-A)
    "testing2": ("2026-10-19", "2026-10-22"),
}


def family(name: str, side: int = 0) -> str:
    s = str(name)
    if s.startswith("GEN-"):
        return "GEN"
    if "ETF" in s or s.startswith("IDX"):
        return "ETF"
    if re.search(r"gapdn|gap-slope|gap-down", s):
        return "gap-down short" if side < 0 or "short" in s or s.startswith("L3") else "gap other"
    m = re.match(r"^(CWT14|CWT12|CWT13|CWT|RW|MF|NS|ST|LIQ|LD|ULT|NM|orb)", s)
    if m:
        return {"CWT": "CWT other"}.get(m.group(1), m.group(1))
    return "classic (heat/exhaustion/intraday)"


def ts(x):
    return pd.to_datetime(x, utc=True, format="mixed")


def whatif_cost_adjust(w: pd.DataFrame, live: pd.DataFrame) -> pd.Series:
    """What-if R after an estimated cost: the setup's median live (raw r_multiple - LR8 r) gap, else the global median,
    plus the C3 corrected-what-if haircut of 0.05R (mcf/report/c3score.py HAIRCUT_R)."""
    g = (live["r_multiple"] - live["r"]).groupby(live["strategy"]).median()
    glob = float((live["r_multiple"] - live["r"]).median())
    c = w["strategy"].map(g).fillna(glob)
    return w["r_multiple"] - c - 0.05


def one_lot_at_a_time(w: pd.DataFrame) -> pd.DataFrame:
    """keep a what-if row only when the previous kept row of the same account/setup/symbol/day has exited (refire spam)."""
    w = w.sort_values("et").copy()
    keep, last = [], {}
    for i, r in zip(w.index, w.itertuples()):
        k = (r.account, r.strategy, r.symbol, r.date)
        if k in last and r.et < last[k]:
            continue
        last[k] = r.xt
        keep.append(i)
    return w.loc[keep]


def day_wobd(g: pd.DataFrame) -> float:
    """avg R without the best session (per-trade average of the remaining trades)."""
    if g.empty:
        return float("nan")
    d = g.groupby("date").r.sum()
    rest = g[g.date != d.idxmax()]
    return float(rest.r.mean()) if len(rest) else float("nan")
