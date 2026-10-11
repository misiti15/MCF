"""Backlog re-test of lab-module entries on the research 1-minute bar cache (forward / open data).

Rule 17 (docs/RESEARCH_RULES.md): the backlog is re-tested continuously on all collected data. Since rule 19 the
setups are lab modules (SIDE, GEOM, mask(df); see mcf/strategies/setups.py LabStrategy). This module scores every
runnable backlog entry that carries `lab_module` on whatever the 1-minute cache holds (data/cache/1Min: 2026-06-15
onward on the weekly runner), with the SAME pipeline as the research history (research/history2y/build_frames.py):
1-minute -> 5-minute -> mcf.research.setup_lab.build (features + lab outcomes), point-in-time adv20 >= min_adv, the
setup's window, first qualifying bar per symbol-day, production costs incl. time-of-day entry costs
(mcf.research.gates.lab_trades / prod_r).

Reported per entry: n, sessions, win rate, exp R, day-clustered t on the whole cache; up / down-session split (session
regimes from the cache's own universe, terciles over the cache sessions); and the same on sessions AFTER the entry's
approval date (`approved`, else `added`) - the true forward sample. Monitoring only: no status changes here.

The rule-19 locked block (2024-11-01 .. 2025-02-28) is never read: bars dated inside it are dropped before any
feature is built, and the scored trades are asserted to contain none.
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"
LOCKED = (date(2024, 11, 1), date(2025, 2, 28))       # RESEARCH_RULES rule 19
DEFAULT_WINDOW = (950, 1500)


# ------------------------------------------------------------------------------------------------ entry parameters
def load_module(path: str | Path, name: str):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        raise FileNotFoundError(f"lab_module not found: {path}")
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def spec_for(e: dict) -> dict:
    """Side, exit geometry, window and min_adv for a lab_module entry. Entry fields `lab_window` / `lab_min_adv`
    win (backfilled from config/*.yaml for live setups); else the module docstring ("min_adv N", "window [a, b]",
    as research/history2y/rescore.py); else the module's WINDOW; else 09:50-15:00 and no ADV floor."""
    m = load_module(e["lab_module"], "bl_" + re.sub(r"\W", "_", e["id"]))
    side, geom = getattr(m, "SIDE", None), getattr(m, "GEOM", "t1s1")
    if side not in ("long", "short"):
        raise ValueError(f"SIDE {side!r} is not long/short")
    if geom not in ("t1s1", "t05s1", "t1s05"):
        raise ValueError(f"GEOM {geom!r} is not a lab geometry (structural exits cannot be scored here)")
    doc = m.__doc__ or ""
    mn = re.search(r"min_adv (\d+)", doc)
    w = re.search(r"window \[(\d+), (\d+)\]", doc)
    window = e.get("lab_window") or ((int(w.group(1)), int(w.group(2))) if w else getattr(m, "WINDOW", None)) or DEFAULT_WINDOW
    min_adv = e.get("lab_min_adv")
    if min_adv is None:
        min_adv = float(mn.group(1)) if mn else 0.0
    return {"id": e["id"], "path": e["lab_module"], "side": side, "geom": geom, "window": tuple(int(x) for x in window),
            "min_adv": float(min_adv), "since": str(e.get("approved") or e.get("added") or "")}


# ------------------------------------------------------------------------------------------------ frames
def daily_table(df: pd.DataFrame, sym: str) -> pd.DataFrame:
    """Per symbol-day open / close and point-in-time adv20 (prior 20 sessions' RTH dollar volume, min 5), as
    research/history2y/build_frames.py."""
    g = df.groupby(df.index.date)
    d = pd.DataFrame({"open": g["open"].first(), "close": g["close"].last(),
                      "dollar_volume": (df["close"] * df["volume"]).groupby(df.index.date).sum()})
    d["adv20"] = d["dollar_volume"].shift(1).rolling(20, min_periods=5).mean()
    d.index.name = "date"
    d = d.reset_index()
    d.insert(0, "symbol", sym)
    return d


def drop_locked(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    d = np.asarray(df.index.date)
    return df[~((d >= LOCKED[0]) & (d <= LOCKED[1]))]


def symbol_frame(df1m: pd.DataFrame, sym: str) -> tuple[pd.DataFrame | None, pd.DataFrame]:
    from ..data.bars import resample
    from .setup_lab import build

    df1m = drop_locked(df1m)
    if df1m.empty:
        return None, pd.DataFrame()
    dd = daily_table(df1m, sym)
    x = build({sym: resample(df1m, "5min")}, log=lambda *_: None) if len(df1m) else None
    if x is None or not len(x):
        return None, dd
    x = x.reset_index(names="ts").merge(dd[["date", "adv20"]], on="date", how="left")
    return x, dd


# ------------------------------------------------------------------------------------------------ worker
_W: dict = {}


def _init(specs: list[dict], cache: str) -> None:
    _W["cache"] = cache
    _W["specs"] = specs
    _W["mods"] = {s["id"]: load_module(s["path"], "blw_" + re.sub(r"\W", "_", s["id"])) for s in specs}


def _chunk(syms: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    from ..data.store import BarStore
    from . import gates as G

    store = BarStore(_W["cache"])
    trades, dailies, errors = [], [], {}
    for sym in syms:
        try:
            df, dd = symbol_frame(store.load(sym), sym)
        except Exception as ex:                    # one bad file must not sink the run; reported per symbol
            errors.setdefault("_symbols", []).append(f"{sym}: {type(ex).__name__}: {ex}")
            continue
        if len(dd):
            dailies.append(dd[["symbol", "date", "open", "close"]])
        if df is None:
            continue
        tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
        for s in _W["specs"]:
            if s["id"] in errors:
                continue
            lo, hi = s["window"]
            base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"])
            try:
                with np.errstate(invalid="ignore", divide="ignore"):
                    mk = np.asarray(_W["mods"][s["id"]].mask(df), bool) & base
            except Exception as ex:
                errors[s["id"]] = f"mask failed: {type(ex).__name__}: {ex}"
                continue
            if mk.any():
                tr = G.lab_trades(df, mk, s["side"], s["geom"])
                tr["id"] = s["id"]
                trades.append(tr)
    t = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame(columns=["date", "symbol", "tod", "r", "id"])
    d = pd.concat(dailies, ignore_index=True) if dailies else pd.DataFrame(columns=["symbol", "date", "open", "close"])
    return t, d, errors


# ------------------------------------------------------------------------------------------------ scoring
def _metrics(tr: pd.DataFrame) -> dict:
    from . import gates as G

    m = G.summary(tr)
    m["t_day_clustered"] = m.get("t")
    return m


def score(specs: list[dict], cache: str | Path = CACHE, workers: int | None = None, chunk: int = 25,
          log=print) -> tuple[dict, dict, dict]:
    """Score every spec on the cache. Returns (metrics by id, errors by id, info about the sample)."""
    from ..data.store import BarStore
    from . import gates as G

    cache = str(cache)
    syms = BarStore(cache).symbols()
    info = {"symbols": len(syms), "cache": cache}
    if not syms or not specs:
        return {}, {}, info
    jobs = [syms[i:i + chunk] for i in range(0, len(syms), chunk)]
    workers = workers or min(4, os.cpu_count() or 1)
    t0 = time.time()
    parts, dailies, errors = [], [], {}
    if workers <= 1:
        _init(specs, cache)
        results = map(_chunk, jobs)
        pool = None
    else:
        import multiprocessing as mp

        pool = mp.get_context("fork" if sys.platform != "win32" else "spawn").Pool(workers, _init, (specs, cache))
        results = pool.imap_unordered(_chunk, jobs)
    try:
        for k, (t, d, err) in enumerate(results, 1):
            parts.append(t)
            dailies.append(d)
            for i, msg in err.items():
                if i == "_symbols":
                    errors.setdefault(i, []).extend(msg)
                else:
                    errors.setdefault(i, msg)
            if k % 10 == 0 or k == len(jobs):
                log(f"  backlog lab: {k}/{len(jobs)} symbol chunks ({time.time() - t0:.0f}s)")
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    trades = pd.concat(parts, ignore_index=True)
    daily = pd.concat(dailies, ignore_index=True)
    if len(trades):
        dt = pd.to_datetime(trades["date"]).dt.date
        assert not ((dt >= LOCKED[0]) & (dt <= LOCKED[1])).any(), "locked block (rule 19) leaked into the backlog re-test"
        trades["date"] = dt
    if not len(daily):
        return {}, errors, info
    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    reg = G.session_regimes(daily)
    sessions = sorted(reg.index)
    info.update({"first": str(sessions[0]), "last": str(sessions[-1]), "sessions": len(sessions),
                 "seconds": round(time.time() - t0, 1)})
    out = {}
    for s in specs:
        if s["id"] in errors:
            continue
        tr = trades[trades["id"] == s["id"]]
        m = _metrics(tr)
        rs = G.regime_split(tr, reg, min_n=1)
        m["up"] = {k: rs["up"].get(k) for k in ("n", "exp_r", "t")}
        m["down"] = {k: rs["down"].get(k) for k in ("n", "exp_r", "t")}
        m["sample"] = f"{info['first']}..{info['last']}"
        m["side"], m["geom"], m["window"], m["min_adv"] = s["side"], s["geom"], list(s["window"]), s["min_adv"]
        since = s.get("since")
        if since:
            fw = tr[pd.to_datetime(tr["date"]) > pd.Timestamp(since)] if len(tr) else tr
            m["forward"] = {"since": since, "sessions_after": sum(1 for d in sessions if str(d) > since), **_metrics(fw)}
        out[s["id"]] = m
    return out, errors, info
