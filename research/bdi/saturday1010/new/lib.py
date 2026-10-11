"""Shared data + simulator for the Saturday 2026-10-10 new-ideas scan (PEAD, FINRA short-volume ratio).

The data block, eligibility, cost model, locked-block handling, rebalance calendars and `simulate` are copied
verbatim from research/longhold/study.py (study.py runs its whole grid and rewrites its outputs on import, so it is not
imported). Parity check: `stock_targets("mom12_1", 20, "W", filt_rev=True)` reproduces longhold's
S6_mom12_1rev_N20_W daily returns (see check_parity()).

Every daily return inside the rule-19 locked block (2024-11-01..2025-02-28) is set to 0 before any simulation, and
locked days are dropped before any statistic. *_lockedblock.parquet files are never read.
Educational only - not financial advice.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
W3 = ROOT / "research" / "swarm1010" / "w3_daily"
LH = ROOT / "research" / "longhold"
DATA = HERE / "data"

LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
BORROW = 0.03

# ---------------------------------------------------------------------------------------------- data (study.py)
raw = pd.read_parquet(W3 / "data" / "daily_2016.parquet", columns=["symbol", "date", "open", "high", "close", "volume"])
raw["symbol"] = raw["symbol"].astype(str)
extra = pd.read_parquet(LH / "data" / "etf_extra.parquet", columns=["symbol", "date", "open", "high", "close", "volume"])
raw = pd.concat([raw, extra[~extra.symbol.isin(raw.symbol.unique())]], ignore_index=True)
meta = pd.read_csv(W3 / "assets_meta.csv")
etf = set(meta.loc[meta.is_etf, "symbol"]) | set(extra.symbol.unique())


def _wide(col):
    return raw.pivot(index="date", columns="symbol", values=col).sort_index()


C = _wide("close"); O = _wide("open"); V = _wide("volume")
del raw
dates = C.index
syms = np.array(C.columns.astype(str))
col = {s: i for i, s in enumerate(syms)}
T, NS = C.shape
locked = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))

Cn, On, Vn = C.to_numpy(), O.to_numpy(), V.to_numpy()
prevC = np.vstack([np.full(NS, np.nan), Cn[:-1]])
R_cc = np.nan_to_num(Cn / prevC - 1)
R_co = np.nan_to_num(On / prevC - 1)
R_oc = np.nan_to_num(Cn / On - 1)
for _R in (R_cc, R_co, R_oc):
    _R[locked] = 0.0                                  # locked block: no outcome enters any simulation
COST_O = 0.01 / On + 0.0001                           # per traded $ at the open (NaN = no open -> cannot trade)
caldays = np.r_[1, np.diff(dates.values).astype("timedelta64[D]").astype(int)]

is_etf = np.array([s in etf for s in syms])
adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()
nbars = C.notna().cumsum().to_numpy()
ELIG = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]

MOM12_1 = (C.shift(21) / C.shift(252) - 1).to_numpy()
RET21 = (C / C.shift(21) - 1).to_numpy()

dser = pd.Series(np.arange(T), index=dates)
MONTH_END = dser.groupby([dates.year, dates.month]).max().to_numpy()
iso = dates.isocalendar()
WEEK_END = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()
REB = {"M": MONTH_END, "W": WEEK_END}
START_ROW = int(np.searchsorted(dates.values, np.datetime64("2018-12-31")))   # first signal row of this scan


# ---------------------------------------------------------------------------------------------- simulator (study.py)
def simulate(targets: dict[int, np.ndarray], cost_mult: float = 1.0):
    """targets: {signal row t: weight vector}; executed at open t+1. Copied from longhold/study.py (+ cost_mult)."""
    h = np.zeros(NS); cash = 1.0; E_prev = 1.0
    out_r = np.zeros(T); out_to = np.zeros(T); out_c = np.zeros(T)
    started = False
    for d in range(1, T):
        w = targets.get(d - 1)
        if w is not None:
            started = True
            h *= 1 + R_co[d]
            E = cash + h.sum()
            tgt = w * E
            co = COST_O[d] * cost_mult
            bad = np.isnan(co)
            if bad.any():
                tgt = np.where(bad, h, tgt)
            trade = tgt - h
            cost = np.nansum(np.abs(trade) * co)
            cash -= trade.sum() + cost
            h = tgt * (1 + R_oc[d])
            out_to[d] = np.abs(trade).sum() / 2 / E
            out_c[d] = cost / E_prev
        elif started:
            h *= 1 + R_cc[d]
        if started:
            short = -h[h < 0].sum()
            if short > 0 and not locked[d]:
                cash -= BORROW / 365 * caldays[d] * short
            E = cash + h.sum()
            out_r[d] = E / E_prev - 1
            E_prev = E
    return out_r, out_to, out_c


def simulate_slots(entries: dict[int, list[tuple[int, float]]], hold: int, K: int, cost_mult: float = 1.0):
    """Event book with K equal slots (PEAD). entries: {signal row t: [(symbol idx, score), ...]}.
    At the open of t+1: positions whose holding period is over are sold first, then the highest-score candidates
    not already held fill the free slots, each bought with 1/K of current equity (capped by cash; no leverage).
    Names that stay are not re-weighted (no drift trades). Idle cash earns 0. Same cost model as simulate().
    Returns net return, turnover, cost and exposure (invested fraction at the close), all per day."""
    h = np.zeros(NS); cash = 1.0; E_prev = 1.0
    exit_row = {}                                   # sym -> row whose open it is sold at
    out_r = np.zeros(T); out_to = np.zeros(T); out_c = np.zeros(T); expo = np.zeros(T)
    for d in range(1, T):
        cand = entries.get(d - 1)
        due = [s for s, x in exit_row.items() if x == d]
        if cand or due:
            h *= 1 + R_co[d]
            E = cash + h.sum()
            co = COST_O[d] * cost_mult
            traded = 0.0; cost = 0.0
            for s in due:
                if np.isnan(co[s]):                 # no open print: try again next session
                    exit_row[s] = d + 1
                    continue
                v = h[s]; c = abs(v) * co[s]
                cash += v - c; traded += abs(v); cost += c; h[s] = 0.0
                del exit_row[s]
            if cand:
                free = K - len(exit_row)
                for s, _sc in sorted(cand, key=lambda x: -x[1]):
                    if free <= 0:
                        break
                    if s in exit_row or np.isnan(co[s]):
                        continue
                    amt = min(E / K, cash / (1 + co[s]))
                    if amt <= 0:
                        break
                    c = amt * co[s]
                    cash -= amt + c; h[s] += amt; traded += amt; cost += c
                    exit_row[s] = d + hold
                    free -= 1
            h *= 1 + R_oc[d]
            out_to[d] = traded / 2 / E
            out_c[d] = cost / E_prev
        else:
            h *= 1 + R_cc[d]
        E = cash + h.sum()
        out_r[d] = E / E_prev - 1
        expo[d] = h.sum() / E if E > 0 else 0.0
        E_prev = E
    return out_r, out_to, out_c, expo


# ---------------------------------------------------------------------------------------------- targets
def stock_targets(score, n, reb, filt_rev=False, elig=None, start=START_ROW, lowest=False):
    """Top-n equal weight by `score` (T x NS array, higher = better unless lowest=True), study.py convention.
    `elig` (T x NS bool) further restricts the universe (filters)."""
    out = {}
    for t in REB[reb]:
        if t < max(252, start) or t >= T - 1:
            continue
        F = score[t]
        ok = ELIG[t] & ~np.isnan(F)
        if elig is not None:
            ok &= elig[t]
        if filt_rev:
            r21 = RET21[t]
            okr = ok & ~np.isnan(r21)
            if okr.sum() > 10:
                ok &= ~(r21 >= np.nanquantile(r21[okr], 0.9))
        idx = np.flatnonzero(ok)
        if len(idx) < 2 * n:
            continue
        order = idx[np.argsort(F[idx] if lowest else -F[idx], kind="stable")]
        w = np.zeros(NS)
        w[order[:n]] = 1.0 / n
        out[t] = w
    return out


def ew_universe_targets(start=START_ROW):
    out = {}
    for t in MONTH_END:
        if t < max(252, start) or t >= T - 1:
            continue
        ok = ELIG[t]
        w = np.zeros(NS)
        w[ok] = 1.0 / ok.sum()
        out[t] = w
    return out


def bh_targets(names, start=START_ROW):
    out = {}
    for t in MONTH_END:
        if t < max(252, start) or t >= T - 1:
            continue
        avail = [s for s in names if not np.isnan(Cn[t, col[s]])]
        w = np.zeros(NS)
        for s in avail:
            w[col[s]] = 1.0 / len(avail)
        out[t] = w
    return out


def check_parity():
    """S6_mom12_1rev_N20_W from this loader vs longhold's saved daily returns (2017+ start convention)."""
    r = simulate(stock_targets(MOM12_1, 20, "W", filt_rev=True, start=0))[0]
    ref = pd.read_parquet(LH / "data" / "daily_returns.parquet", columns=["S6_mom12_1rev_N20_W"]).iloc[:, 0]
    ref = ref.reindex(dates).to_numpy()
    return float(np.nanmax(np.abs(r - ref)))


# ---------------------------------------------------------------------------------------------- statistics
SPLITS = {"train": ("2019-01-01", "2022-12-31"), "valid": ("2023-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
month_key = np.asarray(dates.year * 100 + dates.month)


def period_mask(name):
    if name in SPLITS:
        a, b = SPLITS[name]
        msk = (dates >= a) & (dates <= b)
    elif name == "all":
        msk = dates >= SPLITS["train"][0]
    else:
        y = int(name[1:])
        msk = (dates.year == y) & (dates >= SPLITS["train"][0])
    return np.asarray(msk) & ~locked


def mdd(r):
    eq = np.cumprod(1 + r)
    return float((eq / np.maximum.accumulate(eq) - 1).min())


def monthly(r, msk):
    return pd.Series(r[msk]).groupby(month_key[msk]).apply(lambda x: (1 + x).prod() - 1)


def t_stat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")
