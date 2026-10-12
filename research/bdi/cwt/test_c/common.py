"""CWT package C: shared daily data, features, trade engine and statistics (NOTES.md section 1).

Single process. Outcome prices inside the rule-19 locked block (2024-11-01..2025-02-28) are NaN-ed before any trade is
simulated and any trade whose path reaches a locked row is dropped. Look-back features use the full price history
(inputs only, W3/longhold convention). Educational only - not financial advice.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import t_required  # noqa: E402

W3 = ROOT / "research" / "swarm1010" / "w3_daily"
DATA = HERE / "data"
LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
SPLITS = {"train": ("2016-01-01", "2022-12-31"), "valid1": ("2023-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
BORROW = 0.03

# ------------------------------------------------------------------------------------------------ data
raw = pd.read_parquet(W3 / "data" / "daily_2016.parquet", columns=["symbol", "date", "open", "high", "low", "close", "volume"])
raw["symbol"] = raw["symbol"].astype(str)
meta = pd.read_csv(W3 / "assets_meta.csv")
etf = set(meta.loc[meta.is_etf, "symbol"])


def _wide(c):
    return raw.pivot(index="date", columns="symbol", values=c).sort_index()


C = _wide("close"); O = _wide("open"); H = _wide("high"); L = _wide("low"); V = _wide("volume")
del raw
dates = C.index
syms = np.array(C.columns.astype(str))
col = {s: i for i, s in enumerate(syms)}
T, N = C.shape
locked = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))

# ------------------------------------------------------------------------------------------------ features (full history)
Cn, On, Hn, Ln, Vn = (x.to_numpy(float) for x in (C, O, H, L, V))
prevC = np.vstack([np.full(N, np.nan), Cn[:-1]])


def sma(n, X=C):
    return X.rolling(n, min_periods=n).mean().to_numpy()


def ema(n):
    return C.ewm(span=n, adjust=False, ignore_na=True).mean().where(C.notna()).to_numpy()


def rsi(n):
    d = C.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, ignore_na=True).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False, ignore_na=True).mean()
    r = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    return r.where(dn > 0, 100.0).where(d.notna()).to_numpy()


tr = np.fmax(Hn - Ln, np.fmax(np.abs(Hn - prevC), np.abs(Ln - prevC)))
ATR14 = pd.DataFrame(tr, index=dates).ewm(alpha=1 / 14, adjust=False, ignore_na=True).mean().to_numpy().copy()
ATR14[np.isnan(Cn)] = np.nan
adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()
nbars = C.notna().cumsum().to_numpy()
is_etf = np.array([s in etf for s in syms])
ELIG = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]
SPY = col["SPY"]
spy_c = Cn[:, SPY]
SPY_SMA200 = sma(200)[:, SPY]
SPY_SMA10 = sma(10)[:, SPY]

# ------------------------------------------------------------------------------------------------ outcome arrays (locked NaN)
Ox, Hx, Lx, Cx = (a.copy() for a in (On, Hn, Ln, Cn))
for a in (Ox, Hx, Lx, Cx):
    a[locked] = np.nan


def cost(px):
    return 0.01 / px + 1e-4


# ------------------------------------------------------------------------------------------------ regimes (W3)
spy = C["SPY"]
mret = spy.resample("ME").last().pct_change()
mret.index = mret.index.to_period("M")
lk_m = {pd.Period(m, "M") for m in ["2024-11", "2024-12", "2025-01", "2025-02"]}
_mo = mret[~mret.index.isin(lk_m)].dropna()
_lo, _hi = np.quantile(_mo, [1 / 3, 2 / 3])
month_class = pd.Series(np.where(mret <= _lo, "down", np.where(mret >= _hi, "up", "flat")), index=mret.index)
month_class[mret.isna()] = "flat"
_yl = spy.groupby(spy.index.year).last()
_yr = _yl / _yl.shift(1).fillna(spy.iloc[0]) - 1
year_class = pd.Series(np.where(_yr > 0.10, "up", np.where(_yr < 0, "down", "flat")), index=_yr.index)


# ------------------------------------------------------------------------------------------------ trade engine
def walk(j, ei, ep, side, mode, stop=None, target=None, close_rule=None, max_xi=None, start_close=None):
    """Simulate one position from entry row ei at price ep. mode: 'C' (MOC: checks start next session),
    'O' (MOO), 'I' (intraday limit/stop fill: stop checked on the entry day, target not).
    stop / target: None, a float, or a callable(d) -> level (NaN = none). close_rule(d) -> True exits at close d.
    max_xi: time stop row (exit at its close). Returns (xi, xp, xk, reason) or None (locked / no data)."""
    last = min(max_xi if max_xi is not None else T - 1, T - 1)
    d0 = ei + 1 if mode == "C" else ei
    if start_close is None:
        start_close = d0
    for d in range(d0, last + 1):
        if locked[d]:
            return None
        o, h, lo, c = Ox[d, j], Hx[d, j], Lx[d, j], Cx[d, j]
        if not np.isfinite(c):
            continue                                   # no bar today (halt / missing): carry
        s = stop(d) if callable(stop) else stop
        tg = target(d) if callable(target) else target
        s = s if s is not None and np.isfinite(s) else None
        tg = tg if tg is not None and np.isfinite(tg) else None
        first_intraday = (mode == "I" and d == ei)
        if side == 1:
            if not first_intraday:
                if s is not None and o <= s:
                    return d, o, "C", "stop"
                if tg is not None and o >= tg:
                    return d, o, "C", "target"
            if s is not None and lo <= s:
                return d, (min(o, s) if not first_intraday else s), "C", "stop"
            if tg is not None and not first_intraday and h >= tg:
                return d, max(o, tg), "C", "target"
        else:
            if not first_intraday:
                if s is not None and o >= s:
                    return d, o, "C", "stop"
                if tg is not None and o <= tg:
                    return d, o, "C", "target"
            if s is not None and h >= s:
                return d, (max(o, s) if not first_intraday else s), "C", "stop"
            if tg is not None and not first_intraday and lo <= tg:
                return d, min(o, tg), "C", "target"
        if close_rule is not None and d >= start_close and close_rule(d):
            return d, c, "C", "rule"
        if d == last:
            return d, c, "C", "time"
    return None


def finish(rows, side, name=""):
    """rows: list of dicts with i, j, ei, ep, ek, xi, xp, xk (+ optional w, legs). Adds costs, borrow, dates."""
    if not rows:
        return pd.DataFrame(columns=["i", "j", "ei", "xi", "ep", "xp", "ek", "xk", "gross", "net", "date", "hold", "w"])
    t = pd.DataFrame(rows)
    if "w" not in t:
        t["w"] = 1.0
    t["gross"] = side * (t.xp / t.ep - 1)
    days = np.maximum((dates[t.xi.to_numpy()] - dates[t.ei.to_numpy()]).days.to_numpy(), 1)
    borrow = BORROW * days / 365 if side == -1 else 0.0
    t["net"] = t.gross - cost(t.ep) - cost(t.xp) - borrow
    t["date"] = dates[t.i.to_numpy()]
    t["hold"] = (t.xi - t.ei).clip(lower=1)
    t["side"] = side
    return t


def book(signals, side, make):
    """signals: bool (T, N) or list of (i, j). make(i, j) -> row dict or None (not filled / dropped).
    One position per symbol: a signal while the previous trade is open (i <= its exit row) is skipped."""
    if isinstance(signals, np.ndarray):
        ii, jj = np.nonzero(signals)
        order = np.lexsort((ii, jj))
        pairs = zip(ii[order], jj[order])
    else:
        pairs = sorted(signals, key=lambda x: (x[1], x[0]))
    rows = []
    busy = {}
    for i, j in pairs:
        if i <= busy.get(j, -1) or i >= T - 1:
            continue
        r = make(int(i), int(j))
        if r is None:
            continue
        busy[j] = r["xi"]
        rows.append(r)
    return finish(rows, side)


_bench = {}


def bench(t):
    """Mean gross long return of the eligible stocks (signal-day eligibility) over the same entry/exit prices."""
    out = np.full(len(t), np.nan)
    keys = list(zip(t.ek, t.i, t.ei, t.xk, t.xi))
    for n, key in enumerate(keys):
        if key not in _bench:
            ek, i, ei, xk, xi = key
            e = ELIG[i]
            ep = Cx[ei, e] if ek == "C" else Ox[ei, e]
            xp = Ox[xi, e] if xk == "O" else Cx[xi, e]
            r = xp / ep - 1
            _bench[key] = float(np.nanmean(r)) if np.isfinite(r).any() else np.nan
        out[n] = _bench[key]
    return out


# ------------------------------------------------------------------------------------------------ statistics
def clust_t(x, blk):
    x = np.asarray(x, float)
    if len(x) < 3:
        return np.nan
    mu = x.mean()
    g = pd.DataFrame({"b": blk, "r": x}).groupby("b")["r"].agg(["sum", "size"])
    if len(g) < 2:
        return np.nan
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(x)
    return mu / se if se > 0 else np.nan


def summ(t):
    if t is None or not len(t):
        return {"n": 0}
    w = t.w.to_numpy(float)
    x = t.net.to_numpy(float) * w
    hold = max(1, int(np.median(t.hold)))
    blk = t.i.to_numpy() // max(1, 2 * hold) if hold > 1 else t.i.to_numpy()
    tt = clust_t(x, blk)
    d = {"n": int(len(t)), "sessions": int(t.i.nunique()), "exp_bps": round(x.sum() / w.sum() * 1e4, 2),
         "t": round(tt, 2) if np.isfinite(tt) else None, "win": round(float((t.net > 0).mean()), 3),
         "gross_bps": round(float((t.gross * w).sum() / w.sum()) * 1e4, 2), "avg_hold": round(float(t.hold.mean()), 2),
         "sum_pl": round(float(x.sum()), 4)}
    if "excess" in t and t.excess.notna().any():
        d["excess_bps"] = round(float(np.nansum(t.excess * w) / w[t.excess.notna().to_numpy()].sum()) * 1e4, 2)
    return d


def extra_stats(t):
    """Walk-forward month share, ex-best-day, busiest-day share (open history, 2016+)."""
    if not len(t):
        return {}
    x = t.net * t.w
    m = x.groupby(t.date.dt.to_period("M")).mean()
    byday = x.groupby(t.date).sum()
    best = byday.idxmax()
    rest = t[t.date != best]
    cnt = t.groupby("date").size()
    return {"wf_share": round(float((m > 0).mean()), 3), "wf_months": int(len(m)),
            "ex_best_bps": round(float((rest.net * rest.w).sum() / rest.w.sum()) * 1e4, 2) if len(rest) else None,
            "busiest_share": round(float(cnt.max() / len(t)), 4), "busiest_day": str(cnt.idxmax().date())}


RESULTS: list[dict] = []
TRADES: dict[str, pd.DataFrame] = {}


def score(cid, fam, side, desc, t, params, stock=True, keep=False):
    """Long-format rows (config x split / regime / year) appended to RESULTS."""
    rec = {"id": cid, "family": fam, "side": "long" if side == 1 else ("short" if side == -1 else "pair"),
           "desc": desc, **{f"p_{k}": v for k, v in params.items()}}
    if t is None or not len(t):
        RESULTS.append({**rec, "split": "all_open", "n": 0})
        return t
    t = t.copy()
    if stock and side in (1, -1):
        t["excess"] = t.gross - side * bench(t)
    d = t.date
    parts = {k: t[(d >= a) & (d <= b)] for k, (a, b) in SPLITS.items()}
    parts["trainvalid1"] = t[d <= "2024-10-31"]
    parts["all_open"] = t
    mc = d.dt.to_period("M").map(month_class).to_numpy()
    yc = d.dt.year.map(year_class).to_numpy()
    for k in ("up", "flat", "down"):
        parts[f"month_{k}"] = t[mc == k]
        parts[f"year_{k}"] = t[yc == k]
    for y, g in t.groupby(d.dt.year):
        parts[f"y{y}"] = g
    for k, g in parts.items():
        row = {**rec, "split": k, **summ(g)}
        if k == "all_open":
            row.update(extra_stats(g))
        RESULTS.append(row)
    if keep:
        TRADES[cid] = t
    return t


def save_trades(path):
    if TRADES:
        pd.concat([v.assign(cid=k) for k, v in TRADES.items()], ignore_index=True).to_parquet(path)


__all__ = ["t_required"]
