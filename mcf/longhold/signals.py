"""S6_mom12_1rev_N20_W: the frozen long-hold signal, moved from research/longhold/study.py (lines marked "study:").

Rule (NOTES.md 1.4 / 2.2): at the close of the last trading day of the ISO week, among eligible stocks
(close >= $5, 20-day median dollar volume >= $20M, >= 253 daily bars, not an ETF, 12-1 momentum defined), drop the
top decile of the 21-day return, then hold the 20 highest 12-1 momentum names (C[t-21]/C[t-252]-1) at 5 % each.

Every line that computes a number is the study's expression, unchanged; tests/test_longhold_signals.py checks the
targets against the study's own code on a frozen data slice. Do not edit without a ledger entry (rules 9-11).
Educational only - not financial advice.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

STRATEGY = "S6_mom12_1rev_N20_W"
N = 20
FREQ = "W"
ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "research" / "swarm1010" / "w3_daily" / "assets_meta.csv"
SYMBOLS = ROOT / "research" / "lab_symbols.txt"
STUDY_EXTRA_ETFS = {"RSP", "MTUM", "USMV", "SPLV", "QUAL", "BIL", "SHY", "IEF", "AGG", "VTI"}


def universe() -> list[str]:
    """The study's stock universe: research/lab_symbols.txt (ETFs are dropped by the eligibility rule)."""
    return list(dict.fromkeys(s.strip() for s in SYMBOLS.read_text().split() if s.strip()))


def etf_set() -> set[str]:
    """ETF tags exactly as the study: assets_meta.csv is_etf plus the extra ETFs it downloaded."""
    meta = pd.read_csv(META)
    return set(meta.loc[meta.is_etf, "symbol"].astype(str)) | STUDY_EXTRA_ETFS


def wide(raw: pd.DataFrame, col: str) -> pd.DataFrame:
    return raw.pivot(index="date", columns="symbol", values=col).sort_index()       # study: wide()


def frames(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Long bars (symbol, date, close, volume; adjustment=all) -> wide closes and volumes, one row per session."""
    raw = raw.copy()
    raw["symbol"] = raw["symbol"].astype(str)
    raw["date"] = pd.to_datetime(raw["date"]).dt.normalize()
    return wide(raw, "close"), wide(raw, "volume")


def features(C: pd.DataFrame, V: pd.DataFrame, etf: set[str]) -> dict[str, np.ndarray]:
    syms = np.array(C.columns.astype(str))
    Cn = C.to_numpy()
    is_etf = np.array([s in etf for s in syms])                                       # study: is_etf
    adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()                   # study: adv20
    nbars = C.notna().cumsum().to_numpy()                                             # study: nbars
    elig = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]           # study: ELIG
    mom = (C.shift(21) / C.shift(252) - 1).to_numpy()                                 # study: FEAT["mom12_1"]
    ret21 = (C / C.shift(21) - 1).to_numpy()                                          # study: RET21
    return {"syms": syms, "elig": elig, "mom": mom, "ret21": ret21, "adv20": adv20, "close": Cn}


def weights_at(f: dict, t: int, n: int = N) -> np.ndarray | None:
    """study: stock_targets("mom12_1", n, reb, filt_rev=True) for one signal row t. None = too few names."""
    if t < 252:
        return None
    F = f["mom"]
    ok = f["elig"][t] & ~np.isnan(F[t])
    r21 = f["ret21"][t]
    okr = ok & ~np.isnan(r21)
    if okr.sum() > 10:
        ok &= ~(r21 >= np.nanquantile(r21[okr], 0.9))
    idx = np.flatnonzero(ok)
    if len(idx) < 2 * n:
        return None
    order = idx[np.argsort(-F[t, idx], kind="stable")]
    w = np.zeros(len(f["syms"]))
    w[order[:n]] = 1.0 / n
    return w


def week_end_rows(dates: pd.DatetimeIndex) -> np.ndarray:
    """study: WEEK_END (last row of each ISO week in the data)."""
    dser = pd.Series(np.arange(len(dates)), index=dates)
    iso = dates.isocalendar()
    return dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()


def compute(raw: pd.DataFrame, day: date, etf: set[str] | None = None, n: int = N) -> dict:
    """Targets for the signal at the close of `day` (must be the last row of the bars). Returns
    {"targets": {sym: w}, "eligible": [...], "ranked": [(sym, mom12_1, ret21), ...top 40], "reason": str|None}."""
    C, V = frames(raw)
    C = C.loc[:pd.Timestamp(day)]
    V = V.loc[:pd.Timestamp(day)]
    out = {"targets": {}, "eligible": [], "ranked": [], "reason": None, "rows": len(C)}
    if C.empty or C.index[-1].date() != day:
        out["reason"] = f"last bar {C.index[-1].date() if len(C) else None} is not the signal day {day}"
        return out
    f = features(C, V, etf if etf is not None else etf_set())
    t = len(C) - 1
    out["eligible"] = [str(s) for s in f["syms"][f["elig"][t]]]
    w = weights_at(f, t, n)
    if w is None:
        out["reason"] = f"too few eligible names ({len(out['eligible'])}) or fewer than 253 sessions ({len(C)})"
        return out
    out["targets"] = {str(f["syms"][i]): float(w[i]) for i in np.flatnonzero(w > 0)}
    ok = f["elig"][t] & ~np.isnan(f["mom"][t])
    idx = np.flatnonzero(ok)
    idx = idx[np.argsort(-f["mom"][t, idx], kind="stable")][:40]
    out["ranked"] = [(str(f["syms"][i]), round(float(f["mom"][t, i]), 4), round(float(f["ret21"][t, i]), 4)) for i in idx]
    return out
