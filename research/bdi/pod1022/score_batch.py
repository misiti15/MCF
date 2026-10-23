"""pod1022 batch scorer: score many candidate LAB setup modules in one pass over the open two-year history.

Usage:
    python research/bdi/pod1022/score_batch.py MODULE.py [MODULE.py ...] --out results.jsonl
        [--ref MODULE.py ...] [--ref-config] [--trades-dir DIR] [--months 2025-03,2026-01]

A module is the LabStrategy format (mcf/strategies/setups.py): SIDE 'long'|'short'; GEOM t1s1 / t05s1 / t1s05 /
t05s05 / hold / holdtr, or 'S' with stop_price(f, i) [+ optional target_price(f, i, stop)]; WINDOW (hhmm, hhmm) bar
close; optional SYMBOLS (allow-list), MIN_ADV (default $20M, 0 when SYMBOLS is set), CONTEXT (informational - every
context column is always present); mask(df) over the lab feature frame (see HARNESS.md for the columns).

What is reused (nothing re-derived):
  * frames + context: research/history2y/lib.py (refuses the rule-19 locked block 2024-11-01..2025-02-28; only open
    months are listed); qqq_vwap is filled from the QQQ frame `vwapDistPct` when the stored context predates it
    (mcf/strategies/lab_context.context_from_frames definition)
  * universe: the Setup Generator's (mcf/research/generator/data.py): adv20 >= $20M, earnings blackout (4 trading days
    either side) removed, decision bars 09:50..15:00 bar close
  * trades: FIRST qualifying bar per symbol-day inside WINDOW (mcf.research.gates.first_per_symbol_day), entry at that
    bar's close, R = 0.25 x daily ATR, flat 15:55 - the LabStrategy model (no refire)
  * costs (RESEARCH_RULES rule 1, config/default.yaml costs): 1c + 1 bps per side, entry side x time-of-day multiplier,
    exit side free on a target (limit) fill, +2c on stop fills, x3 on the extended tier (|gap| >= 20% or price < $5).
    t1s1 / t05s1 / t1s05: frame lab outcomes -> production R (mcf.research.arena.data.outcomes).
    t05s05 / hold / holdtr: the generator's 5-minute path simulator (generator.data.sim) over frame rows + the
    15:05-15:55 tail rows (research/bdi/cwt/test_b/data/headtail.parquet).
    S: the same path simulator with the module's own stop / target; R = |entry - stop| (the structural risk).
  * random control: same-date same-minute mean outcome of the same side x geometry over the module's own population
    (universe rows, its SYMBOLS / MIN_ADV), as the generator's quick screen; S modules use the 'hold' outcome.
  * day-clustered t (generator screen): se = sqrt(sum_d (S_d - n_d mu)^2) / n.
  * regimes Bull / Bear / Choppy / Quiet: research/bdi/regime1022 definition on SPY's regular session (hindsight).
  * split: train <= 2025-12-31, valid 2026-01-01+.

Duplicates (owner: variants yes, copies of setups already put through the process no): every module's symbol-day
trades are compared with the other modules of the batch and with --ref modules (--ref-config adds every type: lab
setup of config/*.yaml - live, testing, generator and graveyard). overlap = |A and B| / min(|A|, |B|) on (symbol, date)
of the same side; >= 0.60 (the generator's OVERLAP_MAX) sets dup_flag. Reference modules are scored for overlap only.

Frames are loaded ONCE per month and every module is scored on them, then the month is freed (peak ~ one month of
frames, ~1-2 GB). No secrets, no orders, no locked data. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import math
import re
import signal
import sys
import time
import traceback
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402  (research/history2y/lib.py)

from mcf.research import gates  # noqa: E402
from mcf.research.arena import data as AD  # noqa: E402
from mcf.research.generator import data as GD  # noqa: E402
from mcf.strategies.lab_context import CONTEXT_COLS  # noqa: E402

TRAIN_END = "2025-12-31"
BASE_MIN_ADV = GD.MIN_ADV                     # $20M, the generator universe
FRAME_GEOMS = ("t1s1", "t05s1", "t1s05")
SIM_GEOMS = GD.SIMG                           # t05s05 / hold / holdtr -> (up, dn, trail_r, trail_after_r)
S_GEOMS = ("S", "S+ts2", "S+bar1", "S+x")   # structural; S+ts2 = S + "breakout or bailout" time stop; S+bar1 = S + 1-bar trail; S+x = S + module exit bar / EXIT_TOD
ALL_GEOMS = (*FRAME_GEOMS, *SIM_GEOMS, *S_GEOMS)
OVERLAP_MAX = 0.60
CACHE_VERSION = "pod1022-v1"
REGIMES = ("Bull", "Bear", "Choppy", "Quiet")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pod")
FOOT = "Educational only - not financial advice."


# ------------------------------------------------------------------------------------------------ modules
class Mod:
    def __init__(self, path: str, ref: bool = False, window=None, symbols=None, min_adv=None, name=None, geom=None):
        self.path = str(path)
        self.name = name or Path(path).stem
        self.ref = ref
        self.error = None
        self.secs = 0.0
        self.trades = []            # per month DataFrames
        self.keys = set()           # (symbol, date) for overlap
        self.cached = False
        self.params = (window, symbols, min_adv, geom)
        try:
            p = Path(path)
            if not p.is_absolute():
                p = ROOT / p
            sys.path.insert(0, str(p.parent))
            spec = importlib.util.spec_from_file_location("pod_" + re.sub(r"\W", "_", self.name), p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            self.m = m
            self.side = str(m.SIDE)
            if self.side not in ("long", "short"):
                raise ValueError(f"SIDE {self.side!r} must be 'long' or 'short'")
            self.geom = geom or getattr(m, "GEOM", "t1s1")
            if self.geom not in ALL_GEOMS:
                raise ValueError(f"unknown GEOM {self.geom!r}; known {list(ALL_GEOMS)}")
            if self.geom in S_GEOMS and not hasattr(m, "stop_price"):
                raise ValueError(f"GEOM {self.geom!r} needs stop_price(f, i)")
            w = window or getattr(m, "WINDOW", None) or (950, 1500)
            self.window = (max(950, int(w[0])), min(1500, int(w[1])))
            sy = symbols if symbols is not None else getattr(m, "SYMBOLS", None)
            self.symbols = None if sy is None else frozenset(str(x) for x in ([sy] if isinstance(sy, str) else sy))
            ma = min_adv if min_adv is not None else getattr(m, "MIN_ADV", None)
            self.min_adv = float(ma) if ma is not None else (0.0 if self.symbols else BASE_MIN_ADV)
            self.sgn = 1 if self.side == "long" else -1
            self.ctrl_out = f"{self.side}_{'hold' if self.geom in S_GEOMS else self.geom}"
        except Exception as e:  # noqa: BLE001
            self.error = f"load: {type(e).__name__}: {e}"


def config_refs() -> list[Mod]:
    """Every type: lab setup in config/*.yaml (YAML window / symbols / min_adv / geom override the module's)."""
    import yaml

    out, seen = [], set()
    for f in sorted((ROOT / "config").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text()) or {}
        st = cfg.get("strategies") or {}
        if not isinstance(st, dict):
            continue
        for name, p in st.items():
            if not isinstance(p, dict) or p.get("type") != "lab" or not p.get("module"):
                continue
            sy = p.get("symbols")
            key = (p["module"], str(p.get("window")), str(sy), p.get("geom"))
            if key in seen:
                continue
            seen.add(key)
            mod = Mod(p["module"], ref=True, window=p.get("window"), symbols=None if sy == "module" else sy,
                      min_adv=p.get("min_adv"), name=f"{f.stem}:{name}", geom=p.get("geom"))
            out.append(mod)
    return out


# ------------------------------------------------------------------------------------------------ simulation
@numba.njit(cache=True)
def sim_s(h, l, c, tod, dend, ent, stop0, tgt0, cm, side):
    """Structural exit on the 5-minute path (generator.data.sim conventions): entry at bar ent's close, stop checked
    first in a bar, then the target (NaN = none), flat at the symbol-day's last row (15:55 bar). R = |entry - stop|."""
    n = len(ent)
    r = np.full(n, np.nan, np.float64)
    for q in range(n):
        i = ent[q]
        if i < 0:
            continue
        end = dend[i]
        e = c[i]
        stop = stop0[q]
        tgt = tgt0[q]
        R = side * (e - stop)
        if not (R > 0) or end <= i:
            continue
        ec = (0.01 + e * 1e-4) * GD._mult(tod[i])
        x = 0.0
        cd = 0
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if tgt == tgt and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
        if cd == 0:
            x = c[end]
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - cm[q] * (ec + xc) / R
    return r


@numba.njit(cache=True)
def sim_s_bail(h, l, c, tod, dend, ent, stop0, tgt0, cm, side, nbail, be_r):
    """GEOM 'S+ts2': sim_s plus Ross Cameron's 'breakout or bailout'. If none of the next nbail path bars makes a new
    extreme beyond the entry bar's (high for a long, low for a short), exit at the close of bar entry + nbail (stop and
    target are still checked first inside those bars). be_r > 0: once the trade has been +be_r R (bar high / low), the
    stop moves to the entry price from the NEXT bar on. A break-even exit is costed as a stop fill."""
    n = len(ent)
    r = np.full(n, np.nan, np.float64)
    for q in range(n):
        i = ent[q]
        if i < 0:
            continue
        end = dend[i]
        e = c[i]
        stop = stop0[q]
        tgt = tgt0[q]
        R = side * (e - stop)
        if not (R > 0) or end <= i:
            continue
        ref = h[i] if side == 1 else l[i]
        ec = (0.01 + e * 1e-4) * GD._mult(tod[i])
        x = 0.0
        cd = 0
        newx = False
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if tgt == tgt and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
            if side * (fav - ref) > 0:
                newx = True
            if k == i + nbail and not newx:
                x = c[k]
                cd = 3
                break
            if be_r > 0 and side * (fav - e) >= be_r * R and side * (e - stop) > 0:
                stop = e
        if cd == 0:
            x = c[end]
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - cm[q] * (ec + xc) / R
    return r


@numba.njit(cache=True)
def sim_s_bar1(h, l, c, tod, dend, ent, stop0, tgt0, cm, side, be_r):
    """GEOM 'S+bar1': sim_s plus a one-bar trailing exit (Hiltz / Baehr 'exit on the first new 1-bar low'): stop and
    target are checked first inside each bar; then, at the close of the first bar after entry whose low < the previous
    bar's low (long; mirror for a short), exit at that close. be_r > 0: once the trade has been +be_r R, the stop moves
    to entry from the NEXT bar on (costed as a stop fill). The bar-close exit is costed like a time exit."""
    n = len(ent)
    r = np.full(n, np.nan, np.float64)
    for q in range(n):
        i = ent[q]
        if i < 0:
            continue
        end = dend[i]
        e = c[i]
        stop = stop0[q]
        tgt = tgt0[q]
        R = side * (e - stop)
        if not (R > 0) or end <= i:
            continue
        ec = (0.01 + e * 1e-4) * GD._mult(tod[i])
        x = 0.0
        cd = 0
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            padv = l[k - 1] if side == 1 else h[k - 1]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if tgt == tgt and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
            if side * (adv - padv) < 0:
                x = c[k]
                cd = 3
                break
            if be_r > 0 and side * (fav - e) >= be_r * R and side * (e - stop) > 0:
                stop = e
        if cd == 0:
            x = c[end]
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - cm[q] * (ec + xc) / R
    return r


@numba.njit(cache=True)
def sim_s_x(h, l, c, tod, dend, ent, stop0, tgt0, cm, side, xend, exit_tod, max_bars):
    """GEOM 'S+x': sim_s plus a module-defined exit (added 2026-10-23, pod r3_3). Stop and target are checked first
    inside each bar; then exit at the close of path bar xend[q] (the module's exit_index, -1 = none) or of the first
    bar whose close time is >= exit_tod (EXIT_TOD, 0 = none) or of path bar entry + max_bars (MAX_BARS, 0 = none),
    whichever comes first. Costed like a time exit."""
    n = len(ent)
    r = np.full(n, np.nan, np.float64)
    for q in range(n):
        i = ent[q]
        if i < 0:
            continue
        end = dend[i]
        e = c[i]
        stop = stop0[q]
        tgt = tgt0[q]
        R = side * (e - stop)
        if not (R > 0) or end <= i:
            continue
        ec = (0.01 + e * 1e-4) * GD._mult(tod[i])
        x = 0.0
        cd = 0
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if tgt == tgt and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
            if k == xend[q] or (exit_tod > 0 and tod[k] >= exit_tod) or (max_bars > 0 and k - i >= max_bars):
                x = c[k]
                cd = 3
                break
        if cd == 0:
            x = c[end]
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - cm[q] * (ec + xc) / R
    return r


class Month:
    """One open month of frames (all columns + context) over the base universe, with lazily built outcomes."""

    def __init__(self, month: str, min_adv: float):
        if month in lib.LOCKED_MONTHS or month in AD.LOCKED_MONTHS:
            raise PermissionError("locked block")
        df = lib.load_month(month, context=True)
        if "qqq_vwap" not in df or not np.isfinite(df["qqq_vwap"].to_numpy(float)).any():
            q = df.loc[df["symbol"].astype(str) == "QQQ", ["date", "tod", "vwapDistPct"]]
            q = q.drop_duplicates(["date", "tod"]).rename(columns={"vwapDistPct": "qqq_vwap"})
            df = df.drop(columns=["qqq_vwap"], errors="ignore").merge(q, on=["date", "tod"], how="left")
        for c in CONTEXT_COLS:
            if c not in df:
                df[c] = np.nan
        d = df["date"].astype(str).to_numpy()
        assert not ((d >= lib.LOCKED[0]) & (d <= lib.LOCKED[1])).any(), "locked block row found"
        keep = (df["adv20"].to_numpy(float) >= min_adv) & (df["tod"].to_numpy() >= 950) & (df["tod"].to_numpy() <= 1500)
        sd = pd.DataFrame({"s": df["symbol"].to_numpy(dtype=object), "d": df["date"].to_numpy()})
        code, uniq = pd.MultiIndex.from_frame(sd).factorize()       # blackout per unique symbol-day, mapped back
        us = np.array([u[0] for u in uniq], dtype=object)
        ud = np.array([u[1] for u in uniq], dtype=object)
        keep &= ~GD._blackout(us, ud)[code]
        del sd, code, uniq
        df = df[keep]
        df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        df["symbol"] = df["symbol"].to_numpy(dtype=object)
        self.df = df
        self.month = month
        self.n = len(df)
        self.sym = df["symbol"].to_numpy()
        self.date = df["date"].to_numpy()
        self.tod = df["tod"].to_numpy().astype(np.int64)
        self.adv = df["adv20"].to_numpy(float)
        dc, du = pd.factorize(self.date)
        self.dstr = np.array([str(x) for x in du], dtype=object)[dc]
        self.days = sorted(set(self.dstr))
        dcode = pd.Index(self.days).get_indexer(self.dstr)
        self.slot = dcode.astype(np.int64) * 2400 + self.tod
        c = df["close"].to_numpy(float)
        self.tier = np.where((np.abs(df["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
        self.R = 0.25 * df["atr_d"].to_numpy(float)
        # frame outcomes -> production R now, then the outcome columns leave the frame (masks must not see the future)
        self._out = {k: v.astype(np.float64) for k, v in AD.outcomes(df).items()}
        df.drop(columns=[c for c in df.columns if c.startswith(("r_long_", "r_short_", "win_long_", "win_short_"))],
                inplace=True)
        self._path = None
        self.shared_secs = 0.0        # lazily built shared outcomes / paths (not charged to the module that asked first)

    # outcomes (production R) per side_geom for every row
    def outcome(self, key: str) -> np.ndarray:
        if key in self._out:
            return self._out[key]
        self.path()
        t0 = time.time()
        side, geom = key.split("_", 1)
        if geom in SIM_GEOMS:
            ph, pl, pc, pt, dend, f2P = self.path()
            up, dn, trr, tra = SIM_GEOMS[geom]
            self._out[key] = GD.sim(ph, pl, pc, pt, dend, f2P, self.R, self.tier, 1 if side == "long" else -1,
                                    up, dn, trr, tra).astype(np.float64)
        else:
            raise KeyError(key)
        self.shared_secs += time.time() - t0
        return self._out[key]

    def path(self):
        """Frame rows + 15:05-15:55 tail rows per symbol-day (generator.data.build_month's path)."""
        if self._path is not None:
            return self._path
        t0 = time.time()
        a = pd.Timestamp(self.month + "-01")
        ht = pd.read_parquet(GD.HEADTAIL, columns=["symbol", "date", "tod", "h", "l", "c"],
                             filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
        ht["symbol"] = ht["symbol"].astype(str)
        ht["date"] = pd.to_datetime(ht["date"]).dt.date
        ht = ht[ht["tod"] > 1500].merge(pd.DataFrame({"symbol": self.sym, "date": self.date}).drop_duplicates(),
                                        on=["symbol", "date"], how="inner")
        df = self.df
        P = pd.concat([pd.DataFrame({"symbol": self.sym, "date": self.date, "tod": self.tod,
                                     "h": df["high"].to_numpy(float), "l": df["low"].to_numpy(float),
                                     "c": df["close"].to_numpy(float), "_fi": np.arange(self.n)}),
                       pd.DataFrame({"symbol": ht["symbol"].to_numpy(), "date": ht["date"].to_numpy(),
                                     "tod": ht["tod"].to_numpy().astype(np.int64), "h": ht["h"].to_numpy(float),
                                     "l": ht["l"].to_numpy(float), "c": ht["c"].to_numpy(float), "_fi": -1})],
                      ignore_index=True)
        del ht
        P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        seg = pd.MultiIndex.from_arrays([P["symbol"].to_numpy(), pd.Index(P["date"]).astype(str)]).factorize()[0]
        new = np.r_[True, seg[1:] != seg[:-1]]
        last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
        dend = last[np.cumsum(new) - 1].astype(np.int64)
        fi = P["_fi"].to_numpy()
        f2P = np.full(self.n, -1, np.int64)
        f2P[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
        self._path = (P["h"].to_numpy(float), P["l"].to_numpy(float), P["c"].to_numpy(float),
                      P["tod"].to_numpy(np.int64), dend, f2P)
        self.shared_secs += time.time() - t0
        return self._path

    def control(self, key: str, pop: np.ndarray | None, idx: np.ndarray) -> np.ndarray:
        """Same-date same-minute mean outcome over the population rows (pop None = every universe row)."""
        v = self.outcome(key)
        ok = np.isfinite(v) if pop is None else (np.isfinite(v) & pop)
        u, inv = np.unique(self.slot[ok], return_inverse=True)
        mu = np.bincount(inv, v[ok]) / np.bincount(inv)
        if not len(u):
            return np.full(len(idx), np.nan)
        j = np.clip(np.searchsorted(u, self.slot[idx]), 0, len(u) - 1)
        return np.where(u[j] == self.slot[idx], mu[j], np.nan)


def score_month(M: Month, mod: Mod) -> None:
    t0, sh0 = time.time(), M.shared_secs
    try:
        _score_month(M, mod)
    finally:
        mod.secs += time.time() - t0 - (M.shared_secs - sh0)


def _score_month(M: Month, mod: Mod) -> None:
    pop = M.adv >= mod.min_adv
    if mod.symbols is not None:
        pop &= np.isin(M.sym, list(mod.symbols))
    if pop.all():
        pop = None
    rows = np.arange(M.n) if pop is None else np.flatnonzero(pop)
    if not len(rows):
        return
    f = M.df if pop is None else M.df.iloc[rows].reset_index(drop=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.asarray(mod.m.mask(f), dtype=bool)
    if m.shape != (len(f),):
        raise ValueError(f"mask returned shape {m.shape}, expected ({len(f)},)")
    tod = M.tod[rows]
    m &= (tod >= mod.window[0]) & (tod <= mod.window[1]) & (M.R[rows] > 0)
    stop = tgt = None
    if mod.geom in S_GEOMS:
        cand = np.flatnonzero(m)
        sp = np.full(len(f), np.nan)
        tp = np.full(len(f), np.nan)
        cl = M.df["close"].to_numpy(float)[rows]
        # first VALID bar per symbol-day (LabStrategy skips a stop / target on the wrong side), in frame order
        done = set()
        for i in cand:
            k = (M.sym[rows[i]], M.dstr[rows[i]])
            if k in done:
                continue
            s = float(mod.m.stop_price(f, int(i)))
            if not np.isfinite(s) or mod.sgn * (cl[i] - s) <= 0:
                continue
            t = np.nan
            if hasattr(mod.m, "target_price"):
                t = float(mod.m.target_price(f, int(i), s))
                if not np.isfinite(t) or mod.sgn * (t - cl[i]) <= 0:
                    continue
            sp[i], tp[i] = s, t
            done.add(k)
        m = np.isfinite(sp)
        idx_l = gates.first_per_symbol_day(M.sym[rows], M.date[rows], m)
        stop, tgt = sp[idx_l], tp[idx_l]
        idx = rows[idx_l]
        ph, pl, pc, pt, dend, f2P = M.path()
        if mod.geom == "S+ts2":
            r = sim_s_bail(ph, pl, pc, pt, dend, f2P[idx], stop, tgt, M.tier[idx], mod.sgn,
                           int(getattr(mod.m, "BAILOUT_BARS", 2)), float(getattr(mod.m, "BE_AT_R", 0.0)))
        elif mod.geom == "S+x":
            xe = np.full(len(idx_l), -1, np.int64)
            if hasattr(mod.m, "exit_index"):
                for q, j in enumerate(idx_l):
                    xj = int(mod.m.exit_index(f, int(j), float(stop[q]), float(tgt[q])))
                    if xj > j and xj < len(f):
                        xe[q] = f2P[rows[xj]]
            r = sim_s_x(ph, pl, pc, pt, dend, f2P[idx], stop, tgt, M.tier[idx], mod.sgn, xe,
                        int(getattr(mod.m, "EXIT_TOD", 0)), int(getattr(mod.m, "MAX_BARS", 0)))
        elif mod.geom == "S+bar1":
            r = sim_s_bar1(ph, pl, pc, pt, dend, f2P[idx], stop, tgt, M.tier[idx], mod.sgn,
                           float(getattr(mod.m, "BE_AT_R", 0.0)))
        else:
            r = sim_s(ph, pl, pc, pt, dend, f2P[idx], stop, tgt, M.tier[idx], mod.sgn)
    else:
        key = f"{mod.side}_{mod.geom}"
        out = M.outcome(key)
        m &= np.isfinite(out[rows])
        idx = rows[gates.first_per_symbol_day(M.sym[rows], M.date[rows], m)]
        r = out[idx]
    ctrl = M.control(mod.ctrl_out, pop, idx)
    t = pd.DataFrame({"date": M.dstr[idx], "symbol": M.sym[idx], "tod": M.tod[idx], "r": r, "ctrl": ctrl})
    if stop is not None:
        t["stop"], t["target"] = stop, tgt
    t = t[np.isfinite(t["r"].to_numpy())]
    mod.trades.append(t)
    mod.keys |= set(zip(t["symbol"], t["date"]))


def ref_cache_path(mod: Mod, months: list[str], cache_dir: Path) -> Path:
    """Reference trades are deterministic for (module file bytes, YAML overrides, months, scorer version): cache them
    so the slow config modules are masked once, not once per batch. Helper modules a module imports are not hashed -
    delete the cache dir after changing one."""
    import hashlib

    p = Path(mod.path)
    p = p if p.is_absolute() else ROOT / p
    h = hashlib.sha1(p.read_bytes() if p.exists() else b"")
    h.update(json.dumps([str(x) for x in mod.params] + months + [CACHE_VERSION]).encode())
    return cache_dir / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', mod.name)[:80]}-{h.hexdigest()[:12]}.json"


def ref_cache_load(mod: Mod, f: Path) -> bool:
    if not f.exists():
        return False
    x = json.loads(f.read_text())
    mod.error = x.get("error")
    mod.keys = {tuple(k) for k in x.get("keys", [])}
    mod.secs = float(x.get("secs", 0.0))
    mod.cached = True
    return True


def ref_cache_save(mod: Mod, f: Path) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"module": mod.name, "path": mod.path, "error": mod.error, "secs": round(mod.secs, 2),
                             "keys": sorted([list(k) for k in mod.keys])}))


# ------------------------------------------------------------------------------------------------ statistics
def day_t(r: np.ndarray, day: np.ndarray) -> float | None:
    n = len(r)
    if n < 2:
        return None
    mu = r.mean()
    s = pd.DataFrame({"d": day, "r": r}).groupby("d")["r"].agg(["sum", "count"])
    se = math.sqrt(float(((s["sum"] - s["count"] * mu) ** 2).sum())) / n
    return None if se <= 0 else round(float(mu / se), 3)


def rnd(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def regime_table() -> dict:
    """date (str) -> Bull / Bear / Choppy / Quiet (research/bdi/regime1022/scripts/regime.py, cut 0.5%)."""
    d = lib.daily()
    spy = d[d["symbol"] == "SPY"][["date", "open", "high", "low", "close"]].copy().sort_values("date")
    o2c = (spy["close"] / spy["open"] - 1) * 100
    rng = (spy["high"] - spy["low"]) / spy["open"] * 100
    med = rng.shift(1).rolling(20, min_periods=10).median()
    lab = np.where(o2c >= 0.5, "Bull", np.where(o2c <= -0.5, "Bear", np.where(rng >= med, "Choppy", "Quiet")))
    lab = np.where(med.isna() & (o2c.abs() < 0.5), None, lab)
    return dict(zip(spy["date"].astype(str), lab))


def summarize(mod: Mod, days: dict, reg: dict) -> dict:
    out = {"module": mod.name, "path": mod.path, "side": getattr(mod, "side", None), "geom": getattr(mod, "geom", None),
           "window": list(getattr(mod, "window", ())) or None,
           "symbols": sorted(mod.symbols) if getattr(mod, "symbols", None) else None,
           "min_adv": getattr(mod, "min_adv", None), "error": mod.error, "mask_seconds": round(mod.secs, 2)}
    T = pd.concat(mod.trades, ignore_index=True) if mod.trades else pd.DataFrame(columns=["date", "symbol", "tod", "r", "ctrl"])
    T["split"] = np.where(T["date"].astype(str) <= TRAIN_END, "train", "valid")
    for sp, sub in (("train", T[T.split == "train"]), ("valid", T[T.split == "valid"]), ("pooled", T)):
        r = sub["r"].to_numpy(float)
        c = sub["ctrl"].to_numpy(float)
        nd = days["train"] + days["valid"] if sp == "pooled" else days[sp]
        out[f"n_{sp}"] = int(len(r))
        out[f"avg_r_{sp}"] = rnd(r.mean()) if len(r) else None
        out[f"t_{sp}"] = day_t(r, sub["date"].to_numpy())
        out[f"per_day_{sp}"] = rnd(len(r) / nd, 3) if nd else None
        out[f"win_rate_{sp}"] = rnd((r > 0).mean(), 3) if len(r) else None
        out[f"total_r_{sp}"] = rnd(r.sum(), 2)
        ok = np.isfinite(c)
        out[f"ctrl_avg_r_{sp}"] = rnd(c[ok].mean()) if ok.any() else None
        out[f"excess_{sp}"] = rnd((r[ok] - c[ok]).mean()) if ok.any() else None
        out[f"active_days_{sp}"] = int(sub["date"].nunique())
    tot = T["r"].sum()
    if len(T):
        dsum = T.groupby("date")["r"].sum()
        best = dsum.idxmax()
        out["best_day"] = str(best)
        out["best_day_r"] = rnd(dsum.max(), 3)
        out["best_day_share"] = rnd(dsum.max() / tot, 3) if tot > 0 else None
        rest = T[T["date"] != best]["r"]
        out["avg_r_ex_best_day"] = rnd(rest.mean()) if len(rest) else None
    else:
        out.update(best_day=None, best_day_r=None, best_day_share=None, avg_r_ex_best_day=None)
    T["regime"] = T["date"].astype(str).map(reg)
    br = {}
    for g in REGIMES:
        s = T[T.regime == g]
        br[g] = {"n": int(len(s)), "avg_r": rnd(s["r"].mean()) if len(s) else None,
                 "t": day_t(s["r"].to_numpy(float), s["date"].to_numpy()),
                 "n_train": int((s.split == "train").sum()),
                 "avg_r_train": rnd(s.loc[s.split == "train", "r"].mean()) if (s.split == "train").any() else None,
                 "n_valid": int((s.split == "valid").sum()),
                 "avg_r_valid": rnd(s.loc[s.split == "valid", "r"].mean()) if (s.split == "valid").any() else None}
    out["by_regime"] = br
    return out


def overlaps(mods: list[Mod]) -> dict:
    """name -> list of (other, overlap) sorted desc; same side only; overlap = |A&B| / min(|A|,|B|) on symbol-days."""
    res = {}
    ok = [m for m in mods if m.error is None and m.keys]
    for a in ok:
        if a.ref:
            continue
        lst = []
        for b in ok:
            if b is a or b.side != a.side:
                continue
            inter = len(a.keys & b.keys)
            if inter:
                lst.append((b.name + (" [ref]" if b.ref else ""), round(inter / min(len(a.keys), len(b.keys)), 3),
                            inter))
        res[a.name] = sorted(lst, key=lambda x: -x[1])
    return res


# ------------------------------------------------------------------------------------------------ main
class ModuleTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise ModuleTimeout("timeout: mask over the per-month time budget")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("modules", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", nargs="*", default=[], help="reference modules: overlap only, not scored in --out")
    ap.add_argument("--ref-config", action="store_true", help="add every type: lab setup of config/*.yaml as a reference")
    ap.add_argument("--ref-cache", default=str(SCR / "refcache"),
                    help="cache dir for reference trade keys ('' = off); default the pod scratch dir")
    ap.add_argument("--ref-max-seconds", type=float, default=60,
                    help="per reference module and month; a slower reference is dropped (error 'timeout', cached)")
    ap.add_argument("--max-seconds", type=float, default=0, help="the same for scored modules (0 = no limit)")
    ap.add_argument("--trades-dir", default=None, help="write each module's trades (parquet) here")
    ap.add_argument("--months", default=None, help="comma list of open months (default: every open month)")
    a = ap.parse_args(argv)
    t_start = time.time()
    mods = [Mod(p) for p in a.modules]
    refs = [Mod(p, ref=True) for p in a.ref] + (config_refs() if a.ref_config else [])
    allm = mods + refs
    months = [m for m in lib.months(locked=False) if m not in lib.LOCKED_MONTHS]
    if a.months:
        want = set(a.months.split(","))
        months = [m for m in months if m in want]
    cdir = Path(a.ref_cache) if a.ref_cache else None
    if cdir:
        for r in refs:
            if r.error is None:
                ref_cache_load(r, ref_cache_path(r, months, cdir))
    live = [m for m in allm if m.error is None and not m.cached]
    min_adv = min([BASE_MIN_ADV] + [m.min_adv for m in live])
    days = {"train": 0, "valid": 0}
    t_load = 0.0
    for mo in months:
        t0 = time.time()
        M = Month(mo, min_adv)
        t_load += time.time() - t0
        uni = M.adv >= BASE_MIN_ADV
        for d in sorted(set(M.dstr[uni])):
            days["train" if d <= TRAIN_END else "valid"] += 1
        for mod in live:
            if mod.error is not None:
                continue
            s0 = mod.secs
            budget = a.ref_max_seconds if mod.ref else a.max_seconds
            if budget > 0:
                signal.signal(signal.SIGALRM, _alarm)
                signal.alarm(int(budget))
            try:
                score_month(M, mod)
            except Exception as e:  # noqa: BLE001
                tb = traceback.format_exc(limit=3).strip().splitlines()[-1]
                mod.error = f"{mo}: {type(e).__name__}: {e} | {tb}"[:500]
            finally:
                if budget > 0:
                    signal.alarm(0)
            if mod.secs - s0 > 30:
                print(f"[pod] {mo} slow module {mod.name}: {mod.secs - s0:.0f}s", file=sys.stderr, flush=True)
        print(f"[pod] {mo} rows {M.n} load+build {time.time() - t0:.1f}s", file=sys.stderr, flush=True)
        del M
        gc.collect()
    reg = regime_table()
    ov = overlaps(allm)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.trades_dir:
        Path(a.trades_dir).mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for mod in mods:
            row = summarize(mod, days, reg)
            o = ov.get(mod.name, [])
            row["overlap_max"] = o[0][1] if o else 0.0
            row["overlap_with"] = o[0][0] if o else None
            row["overlap_top"] = [list(x) for x in o[:5]]
            row["dup_flag"] = bool(o and o[0][1] >= OVERLAP_MAX)
            row["n_days"] = days
            row["months"] = months
            row["note"] = FOOT
            fh.write(json.dumps(row, default=str) + "\n")
            if a.trades_dir and mod.trades:
                pd.concat(mod.trades, ignore_index=True).to_parquet(Path(a.trades_dir) / f"{mod.name}.parquet", index=False)
            print(f"[pod] {mod.name}: n {row['n_train']}/{row['n_valid']} avgR {row['avg_r_train']}/{row['avg_r_valid']} "
                  f"t {row['t_train']}/{row['t_valid']} excess {row['excess_train']}/{row['excess_valid']} "
                  f"overlap {row['overlap_max']} ({row['overlap_with']}) mask {mod.secs:.1f}s err {mod.error}",
                  file=sys.stderr)
    for r in refs:
        if cdir and not r.cached and not (r.error or "").startswith("load:"):
            ref_cache_save(r, ref_cache_path(r, months, cdir))
        print(f"[pod] ref {r.name}: {len(r.keys)} symbol-days, mask {r.secs:.1f}s{' (cached)' if r.cached else ''}"
              f"{' error: ' + r.error if r.error else ''}", file=sys.stderr)
    print(f"[pod] {len(mods)} modules + {len(refs)} refs, {len(months)} months, frames {t_load:.0f}s, "
          f"total {time.time() - t_start:.0f}s. {FOOT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
