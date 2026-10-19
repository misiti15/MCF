"""Setup Generator history panel: the open two-year lab frames as compact arrays for the quick screen.

Per open month (research/history2y/lib.py; the rule-19 locked block 2024-11..2025-02 is never read - lib refuses it
and months() lists only the open frames):
  * universe rows: adv20 >= $20M, bar close 09:50..15:00, live earnings blackout removed (4 trading days either side of
    a report, as config/default.yaml universe.earnings_blackout_days)
  * the generator's indicators (mcf.research.arena.indicators.compute, float16 to fit memory) + the four lab
    context columns (spy_fo, qqq_fo, breadth, breadth_open; lib.load_month(context=True))
  * production-cost R per side x geometry (RESEARCH_RULES rule 1: 1c + 1 bps x time-of-day multiplier on entry, +2c on
    stop fills, x3 costs on the extended tier |gap| >= 20% or price < $5):
      t05s1 / t1s1 / t1s05 from the frames' lab outcomes (arena.data.outcomes),
      t05s05 / hold / holdtr from a 5-minute path simulation over the frame rows plus the 15:05-15:55 tail rows
      (research/bdi/cwt/test_b/data/headtail.parquet), flat at the 15:55 bar - the LabStrategy exits.
Train = open months <= 2025-12, valid = 2026-01 onward (arena split). Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

from ..arena import data as AD
from ..arena.indicators import compute
from .spec import CONTEXT, GEOMS, INDICATOR_NAMES, SIDES

ROOT = Path(__file__).resolve().parents[3]
HEADTAIL = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
EARN = ROOT / "research" / "bdi" / "earnings" / "data" / "earnings_yf.parquet"
MIN_ADV = 20e6
OUTS = [f"{s}_{g}" for s in SIDES for g in GEOMS]
SIMG = {"t05s05": (0.5, 0.5, 0.0, 0.0), "hold": (0.0, 1.0, 0.0, 0.0), "holdtr": (0.0, 1.0, 1.0, 1.0)}
LOAD_COLS = ["symbol", "date", "tod", "close", "high", "low", "adv20", "atr_d", "gap", "fromOpen", "momentum", "rsi",
             "rsi5", "rsiSlope", "vwapDistPct", "sma20_dist_pct", "sma50_dist_pct", "dist_hod_atr", "dist_lod_atr",
             "pricePosition", "emaDiff", "macdPct", "sma20_slope_pct", "atrPct", "volumeRatio", "volumeSurge",
             "vol_climax", "buyPressure", "flow3", "flow9prev", "vwapReclaim", "heat", "volumeHeat", "dist_pdh_atr",
             "dist_pdl_atr", "dist_round_atr", "upper_wick", "lower_wick", "bear_div", "bull_div"] + \
            [f"{k}_{s}_{g}" for s in SIDES for g in ("t1s1", "t05s1", "t1s05") for k in ("r", "win")]


@numba.njit(cache=True)
def _mult(t):
    if t < 935:
        return 3.8
    if t < 950:
        return 2.1
    if t < 1030:
        return 1.4
    return 1.0


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, ent, Rv, cm, side, up, dn, trr, tra):
    """5-minute path: entry at bar ent's close, stop checked first in a bar, then target; trailing stop (trr R behind
    the best price once +tra R) from the next bar; flat at the symbol-day's last row. cm = cost multiplier (tier)."""
    n = len(ent)
    r = np.full(n, np.nan, np.float32)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        if end <= i:
            continue
        e = c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        stop = e - side * dn * R
        tgt = e + side * up * R
        mfe = 0.0
        x = 0.0
        cd = 0
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if up > 0 and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
            mfe = max(mfe, side * (fav - e) / R)
            if trr > 0 and mfe >= tra:
                ts = e + side * (mfe - trr) * R
                stop = max(stop, ts) if side == 1 else min(stop, ts)
        if cd == 0:
            x = c[end]
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - cm[q] * (ec + xc) / R
    return r


def _blackout(sym: np.ndarray, date: np.ndarray) -> np.ndarray:
    """True where (symbol, date) is within 4 trading days of an earnings report (busday approximation)."""
    if not EARN.exists():
        return np.zeros(len(sym), bool)
    er = pd.read_parquet(EARN, columns=["symbol", "date"]).dropna()
    d = np.array(pd.to_datetime(er["date"]).dt.date.astype(str), dtype="datetime64[D]")
    parts = []
    for k in range(-4, 5):
        parts.append(pd.DataFrame({"symbol": er["symbol"].astype(str).to_numpy(),
                                   "date": np.busday_offset(d, k, roll="forward").astype(str)}))
    bl = pd.concat(parts).drop_duplicates()
    key = pd.Index(pd.Series(sym).astype(str) + "|" + pd.Series(pd.Index(date).astype(str)))
    bk = set(bl["symbol"] + "|" + bl["date"])
    uk = key.unique()
    flags = np.array([k in bk for k in uk], bool)
    return flags[uk.get_indexer(key)]


def build_month(month: str, names=INDICATOR_NAMES) -> dict:
    """Compact arrays for one open month (see module doc)."""
    if month in AD.LOCKED_MONTHS:
        raise PermissionError("locked block")
    lib = AD._lib()
    df = lib.load_month(month, columns=LOAD_COLS, context=True)
    df = df[df["adv20"].to_numpy(float) >= MIN_ADV].reset_index(drop=True)
    df["symbol"] = df["symbol"].astype(str)
    ind = compute(df, names=list(names), context=False)
    # outcomes: frame geometries (arena) + path-simulated geometries
    out = AD.outcomes(df)       # long_/short_ x t05s1/t1s1/t1s05 (prod costs, tier x3)
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HEADTAIL, columns=["symbol", "date", "tod", "h", "l", "c"],
                         filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    ht = ht[ht["tod"] > 1500].merge(df[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    P = pd.concat([pd.DataFrame({"symbol": df["symbol"], "date": df["date"], "tod": df["tod"].astype(np.int64),
                                 "h": df["high"].astype(float), "l": df["low"].astype(float),
                                 "c": df["close"].astype(float), "_fi": np.arange(len(df))}),
                   pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"].astype(np.int64),
                                 "h": ht["h"].astype(float), "l": ht["l"].astype(float), "c": ht["c"].astype(float),
                                 "_fi": -1})], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    seg = pd.MultiIndex.from_arrays([P["symbol"].to_numpy(), pd.Index(P["date"]).astype(str)]).factorize()[0]
    new = np.r_[True, seg[1:] != seg[:-1]]
    last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
    dend = last[np.cumsum(new) - 1].astype(np.int64)
    fi = P["_fi"].to_numpy()
    f2P = np.full(len(df), -1, np.int64)
    f2P[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    c = df["close"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    Rv = 0.25 * atr
    cm = np.where((np.abs(df["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
    ph, pl, pc = P["h"].to_numpy(float), P["l"].to_numpy(float), P["c"].to_numpy(float)
    pt = P["tod"].to_numpy(np.int64)
    for s in SIDES:
        sd = 1 if s == "long" else -1
        for g, (up, dn, trr, tra) in SIMG.items():
            out[f"{s}_{g}"] = sim(ph, pl, pc, pt, dend, f2P, Rv, cm, sd, up, dn, trr, tra)
    tod = df["tod"].to_numpy()
    uni = (tod >= 950) & (tod <= 1500) & ~_blackout(df["symbol"].to_numpy(), df["date"].to_numpy())
    res = {"symbol": df["symbol"].to_numpy()[uni], "date": np.array(pd.Index(df["date"]).astype(str))[uni],
           "tod": tod[uni].astype(np.int16), "adv20": df["adv20"].to_numpy(np.float32)[uni]}
    for k in OUTS:
        res["r_" + k] = np.asarray(out[k], np.float32)[uni]
    for k in names:
        res[k] = ind[k].to_numpy(np.float32)[uni].astype(np.float16)
    for k in CONTEXT:
        res[k] = df[k].to_numpy(np.float32)[uni]
    return res


def _job(m):
    return m, build_month(m)


class Panel:
    """All open months concatenated. Rows ordered by month, symbol, date, tod (each symbol-day contiguous)."""

    def __init__(self, parts: list[dict], months: list[str]):
        self.months = months
        cols = list(parts[0].keys())
        self.a = {}
        for k in cols:                      # column by column, freeing the month copies (memory peak ~ 1 panel)
            self.a[k] = np.concatenate([p[k] for p in parts])
            for p in parts:
                del p[k]
        sym, date = self.a.pop("symbol"), self.a.pop("date")
        self.n = len(date)
        self.sd = pd.MultiIndex.from_arrays([sym, date]).factorize()[0].astype(np.int32)
        self.sym_codes, self.sym_names = pd.factorize(sym)
        self.day, self.days = pd.factorize(date)
        self.day = self.day.astype(np.int32)
        self.days = np.asarray(self.days)
        self.split = np.where(self.days[self.day] <= "2025-12-31", 0, 1).astype(np.int8)    # 0 train, 1 valid
        reg = AD.regimes()
        rmap = {str(k): {"down": 0, "flat": 1, "up": 2}.get(v, -1) for k, v in reg.items()}
        self.day_regime = np.array([rmap.get(d, -1) for d in self.days], np.int8)
        self.n_days = len(self.days)
        self.n_days_split = [int((np.array(sorted(self.days)) <= "2025-12-31").sum()), 0]
        self.n_days_split[1] = self.n_days - self.n_days_split[0]
        # same-date same-minute universe mean per outcome (random baseline); key = day * 2400 + tod
        self.slot = (self.day.astype(np.int64) * 2400 + self.a["tod"].astype(np.int64))
        self._ctrl = {}

    def col(self, k):
        return self.a[k]

    def control(self, out: str, idx: np.ndarray) -> np.ndarray:
        if out not in self._ctrl:
            v = self.a["r_" + out].astype(np.float64)
            ok = np.isfinite(v)
            u, inv = np.unique(self.slot[ok], return_inverse=True)
            s = np.bincount(inv, v[ok])
            n = np.bincount(inv)
            self._ctrl[out] = (u, s / n)
        u, mu = self._ctrl[out]
        j = np.searchsorted(u, self.slot[idx])
        j = np.clip(j, 0, len(u) - 1)
        return np.where(u[j] == self.slot[idx], mu[j], np.nan)


def load(workers: int = 3, months=None, log=print) -> Panel:
    ms = list(months or AD.months("all"))
    assert not set(ms) & set(AD.LOCKED_MONTHS)
    parts = {}
    if workers > 1:
        from multiprocessing import get_context

        with get_context("spawn").Pool(workers) as pool:
            for m, x in pool.imap_unordered(_job, ms):
                parts[m] = x
                log(f"generator: {m} {len(x['tod'])} rows")
    else:
        for m in ms:
            parts[m] = build_month(m)
            log(f"generator: {m} {len(parts[m]['tod'])} rows")
    return Panel([parts[m] for m in ms], ms)
