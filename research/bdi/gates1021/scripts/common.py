"""Shared helpers for research/bdi/gates1021 (see PLAN.md). Educational only - not financial advice.

The rule-19 locked block (2024-11-01..2025-02-28) is never read: lab frames come from research/history2y/lib, which
refuses the locked months, and every loader here asserts that no locked date survives. MCF_HIST_ALLOW_LOCKED must be
unset."""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

from mcf.config import _merge  # noqa: E402
from mcf.research import gates  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "gates1021 never reads the locked block"

HERE = Path(__file__).resolve().parents[1]
SCR = Path(os.environ.get("G21SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/g1021"))
SCR.mkdir(parents=True, exist_ok=True)
TRAIN_END = pd.Timestamp("2025-12-31").date()
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
ACCOUNTS = {"primary": [], "testing": ["account_testing.yaml"], "testing2": ["account_testing2.yaml"]}


def no_locked(dates) -> None:
    d = pd.to_datetime(pd.Series(dates)).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def split_of(dates) -> np.ndarray:
    d = pd.to_datetime(pd.Series(dates)).dt.date.to_numpy()
    return np.where(d <= TRAIN_END, "train", "valid")


def account_cfg(acct: str) -> dict:
    cfg = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())
    for f in ACCOUNTS[acct]:
        cfg = _merge(cfg, yaml.safe_load((ROOT / "config" / f).read_text()) or {})
    return cfg


def load_mod(name: str, module: str):
    path = ROOT / module
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("g21_" + re.sub(r"\W", "_", name), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def bar_no(tod) -> np.ndarray:
    t = np.asarray(tod, int)
    return ((t // 100) * 60 + t % 100 - 9 * 60 - 30) // 5     # 09:35 close = 1, 09:50 = 4, 15:00 = 66


def chain(sym, date, tod, refire: bool, cooldown: int) -> np.ndarray:
    """Positions (into the given hit arrays, sorted by symbol, date, tod) that emit a signal: the first hit per
    symbol-day, or the LabStrategy refire chain (mcf.strategies.setups.refire_select) on decision-bar numbers."""
    sym = np.asarray(sym).astype(str)
    date = np.asarray(date).astype(str)
    key = np.char.add(np.char.add(sym, "|"), date)
    if not len(key):
        return np.zeros(0, int)
    brk = np.r_[True, key[1:] != key[:-1]]
    starts = np.flatnonzero(brk)
    ends = np.r_[starts[1:], len(key)]
    if not refire:
        return starts
    b = bar_no(tod)
    out = []
    for a, e in zip(starts, ends):
        sel = refire_select(list(b[a:e]), cooldown)
        bb = b[a:e]
        pos = {int(x): a + j for j, x in enumerate(bb)}
        out.extend(pos[int(x)] for x in sel)
    return np.asarray(sorted(out), int)


def summ(r, dates) -> dict:
    t = pd.DataFrame({"date": list(dates), "r": np.asarray(r, float)})
    return gates.summary(t)


def clustered_t(values, dates) -> tuple[float, float, int]:
    """Mean of per-trade values with a day-clustered SE (gates.summary convention). Returns (mean, t, n)."""
    s = summ(values, dates)
    if not s.get("n"):
        return float("nan"), float("nan"), 0
    return s["exp_r"], (s["t"] if s["t"] is not None else float("nan")), s["n"]


def delta_t(r, blocked, dates) -> tuple[float, float]:
    """Gate improvement per PARENT trade: delta = -sum(r over blocked) / n_parent, with a day-clustered t
    (per-trade contribution -r*blocked, clustered by day)."""
    x = -np.asarray(r, float) * np.asarray(blocked, bool)
    s = summ(x, dates)
    return s.get("exp_r", float("nan")), (s.get("t") if s.get("t") is not None else float("nan"))
