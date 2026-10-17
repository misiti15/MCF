"""Arena data layer: per-month lab frames -> indicators + production-cost outcomes + same-minute random controls.

For every row of the universe (adv20 >= min_adv, default 95e6 as the live lab setups) and every side x geometry
(t05s1, t1s1, t1s05):
  r_<side>_<geom>   production R of an entry at this bar close (mcf.research.gates.prod_r with time-of-day entry
                    costs) with x3 costs on the extended tier (|gap| >= 20% or price < $5; RESEARCH_RULES rule 1,
                    as research/bdi/opp1014)
  c_<side>_<geom>   the random same-minute control: mean r over ALL universe rows at the same date and bar close
                    (computed before any sampling)
The rule-19 locked block is never read: research/history2y/lib.load_month refuses it, and months() lists only the
open frames. Split (swarm 2026-10-17): TRAIN = open months <= 2025-12, VALID = 2026-01 onward.
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from .. import gates
from .indicators import INDICATORS, compute

ROOT = Path(__file__).resolve().parents[3]
SIDES = ("long", "short")
GEOMS_ = ("t05s1", "t1s1", "t1s05")
OUTS = [f"{s}_{g}" for s in SIDES for g in GEOMS_]
TRAIN_END = "2025-12"          # last train month (inclusive)
LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
BASE_COLS = ["symbol", "date", "tod"] + [f"r_{o}" for o in OUTS] + [f"c_{o}" for o in OUTS]


def _lib():
    p = str(ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402

    return lib


def months(split: str = "all") -> list[str]:
    """Open months for 'train' (<= 2025-12), 'valid' (>= 2026-01) or 'all'. Never the locked block."""
    ms = [m for m in _lib().months(locked=False) if m not in LOCKED_MONTHS]
    if split == "train":
        return [m for m in ms if m <= TRAIN_END]
    if split == "valid":
        return [m for m in ms if m > TRAIN_END]
    return ms


def regimes() -> pd.Series:
    """date -> up / flat / down (gates.session_regimes, cut points from the open history; locked block excluded)."""
    return _lib().regimes()["regime"]


def keep_sample(symbol, date, mod: int = 2, rem: int = 0) -> np.ndarray:
    """Deterministic symbol-day sample: crc32('SYMBOL|YYYY-MM-DD') % mod == rem."""
    keys = pd.Series(np.asarray(symbol).astype(str)) + "|" + pd.Series(pd.Index(date).astype(str))
    uniq = pd.Index(keys.unique())
    flags = np.array([zlib.crc32(k.encode()) % mod == rem for k in uniq], bool)
    return flags[uniq.get_indexer(keys)]


def outcomes(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Production R per side x geometry for every row (NaN where the lab outcome is missing)."""
    c = df["close"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    tod = df["tod"].to_numpy(float)
    tier = np.where((np.abs(df["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
    R = 0.25 * atr
    out = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        for s in SIDES:
            for g in GEOMS_:
                lab = df[f"r_{s}_{g}"].to_numpy(float)
                p = gates.prod_r(lab, df[f"win_{s}_{g}"].to_numpy(float), c, atr, g, tod=tod)
                gross = lab + 2 * gates.SLIP_PS / R
                v = gross - tier * (gross - p)
                out[f"{s}_{g}"] = np.where(np.isfinite(lab) & (atr > 0), v, np.nan).astype(np.float32)
    return out


def build_month(month: str, names=None, min_adv: float = 95e6, sample: tuple[int, int] | None = None,
                context: bool = True) -> pd.DataFrame:
    """One month: universe rows with BASE_COLS + the requested indicators (default all)."""
    if month in LOCKED_MONTHS:
        raise PermissionError("locked block")
    df = _lib().load_month(month)
    names = list(INDICATORS) if names is None else list(names)
    ind = compute(df, names=names, context=context)
    uni = (df["adv20"].to_numpy(float) >= min_adv) & (df["tod"].to_numpy() >= 950) & (df["tod"].to_numpy() <= 1500)
    out = outcomes(df)
    key = pd.MultiIndex.from_arrays([pd.Index(df["date"]), df["tod"].to_numpy()])
    res = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy(),
                        "tod": df["tod"].to_numpy().astype(np.int16)})
    for o, v in out.items():
        res[f"r_{o}"] = v
        ctl = pd.Series(np.where(uni, v, np.nan), index=key).groupby(level=[0, 1]).mean()
        res[f"c_{o}"] = ctl.reindex(key).to_numpy(np.float32)
    keep = uni
    if sample:
        keep = keep & keep_sample(df["symbol"].to_numpy(), df["date"].to_numpy(), *sample)
    res = pd.concat([res, ind.reset_index(drop=True)], axis=1)[keep].reset_index(drop=True)
    return res


def _job(a):
    month, names, min_adv, sample, cache_dir, context = a
    f = None if cache_dir is None else Path(cache_dir) / f"month={month}.parquet"
    if f is not None and f.exists():
        import pyarrow.parquet as pq

        have = set(pq.ParquetFile(f).schema_arrow.names)
        cols = BASE_COLS + (list(INDICATORS) if names is None else list(names))
        if set(cols) <= have:
            x = pd.read_parquet(f, columns=cols)
            x["date"] = pd.to_datetime(x["date"]).dt.date
            return month, x
    x = build_month(month, None if f is not None else names, min_adv, sample, context)
    if f is not None:
        f.parent.mkdir(parents=True, exist_ok=True)
        x.to_parquet(f, index=False, compression="zstd")
        if names is not None:
            x = x[BASE_COLS + list(names)]
    return month, x


def load(names=None, split: str = "all", min_adv: float = 95e6, sample: tuple[int, int] | None = None,
         cache_dir: str | Path | None = None, workers: int = 3, context: bool = True, log=print) -> pd.DataFrame:
    """Concatenated arena rows for the split. With cache_dir, each month is stored once with ALL indicators
    (cache_dir/month=YYYY-MM.parquet) and later calls read only the requested columns. Adds 'split' and 'regime'."""
    ms = months(split)
    jobs = [(m, names, min_adv, sample, cache_dir, context) for m in ms]
    parts = {}
    if workers > 1:
        from multiprocessing import get_context

        with get_context("spawn").Pool(workers) as pool:
            for m, x in pool.imap_unordered(_job, jobs):
                parts[m] = x
                log(f"arena: {m} {len(x)} rows")
    else:
        for j in jobs:
            m, x = _job(j)
            parts[m] = x
            log(f"arena: {m} {len(x)} rows")
    x = pd.concat([parts[m] for m in ms], ignore_index=True)
    mo = pd.to_datetime(x["date"]).dt.strftime("%Y-%m")
    x["split"] = np.where(mo <= TRAIN_END, "train", "valid")
    x["regime"] = pd.Series(x["date"]).map(regimes()).to_numpy()
    return x
