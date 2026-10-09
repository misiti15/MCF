"""W3 daily study: scores the pre-declared grid in NOTES.md section 1 on data/daily_2016.parquet.

Single process, wide float64 arrays (~2.7k sessions x 1.2k symbols). The rule-19 locked block (2024-11-01..2025-02-28)
is NaN-ed out of every OUTCOME array before any return is computed, and trades touching it are dropped; features
(lookbacks) use the full price history. Outputs: results.csv, coverage_by_year.csv, trades_<id>.parquet for
candidates (git-ignored). Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import session_regimes, t_required  # noqa: E402

LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
SPLITS = {"train": ("2016-01-01", "2022-12-31"), "valid1": ("2023-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
BORROW = 0.03
FAM_N = {"F1": 34, "F2": 64, "F3": 12, "F4": 24, "F5": 28}

# ------------------------------------------------------------------------------------------------ data
raw = pd.read_parquet(HERE / "data" / "daily_2016.parquet")
meta = pd.read_csv(HERE / "assets_meta.csv")
etf = set(meta.loc[meta.is_etf, "symbol"])


def wide(col):
    return raw.pivot(index="date", columns="symbol", values=col).sort_index()


C = wide("close"); O = wide("open"); H = wide("high"); L = wide("low"); V = wide("volume")
dates = C.index
syms = C.columns.astype(str)
T, N = C.shape
print("matrix", T, N, flush=True)

# coverage by year (data description only)
cov = raw.assign(year=raw.date.dt.year).groupby("year").agg(rows=("close", "size"), symbols=("symbol", "nunique"),
                                                         sessions=("date", "nunique"))
cov.to_csv(HERE / "coverage_by_year.csv")

# ------------------------------------------------------------------------------------------------ features (full history)
def rsi(n):
    d = C.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, ignore_na=True).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False, ignore_na=True).mean()
    r = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    return r.where(dn > 0, 100.0).where(d.notna())


dv = (C * V)
adv20 = dv.rolling(20, min_periods=15).median()
nbars = C.notna().cumsum()
sma200 = C.rolling(200, min_periods=200).mean()
sma5 = C.rolling(5, min_periods=5).mean()
rsi2, rsi3 = rsi(2), rsi(3)
prevC = C.shift(1)
gap = O / prevC - 1
o2c = C / O - 1
rng = (H - L)
clv = ((C - L) / rng).where(rng > 0)
ret5 = C / C.shift(5) - 1
ret20 = C / C.shift(20) - 1
maxc252 = C.shift(1).rolling(252, min_periods=200).max()
maxh252 = H.shift(1).rolling(252, min_periods=200).max()
is_etf = np.array([s in etf for s in syms])
ELIG = ((C >= 5) & (adv20 >= 20e6)).to_numpy() & ~is_etf[None, :]
ELIG200 = ELIG & (nbars >= 200).to_numpy()
print("eligible per day median", np.median(ELIG.sum(1)), flush=True)

# ------------------------------------------------------------------------------------------------ outcome arrays (locked NaN-ed)
locked_rows = (dates >= LOCK_A) & (dates <= LOCK_B)
Cx = C.to_numpy(float).copy(); Ox = O.to_numpy(float).copy()
Cx[locked_rows] = np.nan; Ox[locked_rows] = np.nan
SMA5x = sma5.to_numpy(float)
didx = np.arange(T)
dser = pd.Series(dates)

# ------------------------------------------------------------------------------------------------ regimes
spy = C["SPY"].copy()
spy_lk = spy.where(~locked_rows)
mret = spy.resample("ME").last().pct_change()
mret.index = mret.index.to_period("M")
lk_m = {pd.Period(m, "M") for m in ["2024-11", "2024-12", "2025-01", "2025-02"]}
mret_open = mret[~mret.index.isin(lk_m)].dropna()
lo, hi = np.quantile(mret_open, [1 / 3, 2 / 3])
month_class = pd.Series(np.where(mret <= lo, "down", np.where(mret >= hi, "up", "flat")), index=mret.index)
month_class[mret.isna()] = "flat"
ylast = spy.groupby(spy.index.year).last()
yret = ylast / ylast.shift(1).fillna(spy.iloc[0]) - 1
year_class = pd.Series(np.where(yret > 0.10, "up", np.where(yret < 0, "down", "flat")), index=yret.index)
# day regime (gates.session_regimes) from eligible stocks outside the locked block
el = pd.DataFrame(ELIG & ~locked_rows[:, None], index=dates, columns=syms)
dd = pd.DataFrame({"date": np.repeat(dates.values, N), "open": Ox.ravel(), "close": Cx.ravel(), "e": el.to_numpy().ravel()})
dd = dd[dd.e & np.isfinite(dd.open) & np.isfinite(dd.close)]
dayreg = session_regimes(dd[["date", "open", "close"]])["regime"]
del dd
regime_info = {"month_cuts_pct": [round(lo * 100, 2), round(hi * 100, 2)],
               "year_class": {int(k): f"{v} ({yret[k]*100:+.1f}%)" for k, v in year_class.items()},
               "months": month_class[~month_class.index.isin(lk_m)].value_counts().to_dict()}
json.dump(regime_info, open(HERE / "regimes.json", "w"), indent=1)
print(regime_info, flush=True)

# ------------------------------------------------------------------------------------------------ trade engine
def cost(px):
    return 0.01 / px + 1e-4


def make_trades(sig, side, entry, exit_kind, k=None, cap=10, elig=ELIG):
    """sig: bool (T,N). entry 'C' (MOC on signal day i) or 'O' (MOO on i+1). exit_kind: 'ON' (open i+1),
    'K' (close i+k), 'SMA5' (first close beyond SMA5 after entry, cap at close i+cap). No re-entry while in a position."""
    s = np.asarray(sig, bool) & elig
    rows = []
    for j in range(N):
        idx = np.flatnonzero(s[:, j])
        if not len(idx):
            continue
        busy = -1
        cj, oj = Cx[:, j], Ox[:, j]
        for i in idx:
            if i <= busy:
                continue
            ei = i if entry == "C" else i + 1
            if ei >= T:
                continue
            ep = cj[i] if entry == "C" else oj[i + 1]
            if exit_kind == "ON":
                xi, xp, xk = i + 1, (oj[i + 1] if i + 1 < T else np.nan), "O"
            elif exit_kind == "K":
                xi = i + k
                if xi >= T:
                    continue
                xp, xk = cj[xi], "C"
            else:
                xi = min(i + cap, T - 1)
                start = ei if entry == "O" else i + 1
                sm = SMA5x[start:i + cap + 1, j]; cc = cj[start:i + cap + 1]
                hit = np.flatnonzero(cc > sm) if side == 1 else np.flatnonzero(cc < sm)
                if len(hit):
                    xi = start + hit[0]
                xp, xk = cj[xi], "C"
            if not (np.isfinite(ep) and np.isfinite(xp)) or ep <= 0:
                continue
            busy = i if exit_kind == "ON" else xi
            rows.append((i, j, ei, xi, ep, xp, xk))
    if not rows:
        return pd.DataFrame()
    t = pd.DataFrame(rows, columns=["i", "j", "ei", "xi", "ep", "xp", "xk"])
    t["entry"] = entry
    ed, xd = dates[t.ei.to_numpy()], dates[t.xi.to_numpy()]
    t = t[~((ed <= LOCK_B) & (xd >= LOCK_A))].copy()
    gross = side * (t.xp / t.ep - 1)
    days = (dates[t.xi.to_numpy()] - dates[t.ei.to_numpy()]).days.to_numpy()
    days = np.maximum(days, 1)
    borrow = np.where(side == -1, BORROW * days / 365, 0.0)
    t["gross"] = gross
    t["net"] = gross - cost(t.ep) - cost(t.xp) - borrow
    t["date"] = dates[t.i.to_numpy()]
    t["hold"] = (t.xi - t.ei).clip(lower=1) if exit_kind != "ON" else 1
    return t


_bench = {}


def bench(t):
    """Mean gross long return of all eligible stocks over the same entry/exit prices (entry type, i, xi, exit type)."""
    out = np.full(len(t), np.nan)
    for n, (key, g) in enumerate(t.groupby(["entry", "i", "xi", "xk"], sort=False)):
        if key not in _bench:
            en, i, xi, xk = key
            e = ELIG[i]
            ep = Cx[i, e] if en == "C" else Ox[i + 1, e]
            xp = Ox[xi, e] if xk == "O" else Cx[xi, e]
            r = xp / ep - 1
            _bench[key] = float(np.nanmean(r)) if np.isfinite(r).any() else np.nan
        out[t.index.get_indexer(g.index)] = _bench[key]
    return out


def clust_t(r, blk):
    r = np.asarray(r, float)
    if len(r) < 3:
        return np.nan, np.nan
    mu = r.mean()
    g = pd.DataFrame({"b": blk, "r": r}).groupby("b")["r"].agg(["sum", "size"])
    if len(g) < 2:
        return mu, np.nan
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)
    return mu, (mu / se if se > 0 else np.nan)


def summ(t, hold):
    if t is None or not len(t):
        return {"n": 0}
    blk = t.i.to_numpy() // max(1, 2 * hold) if hold > 1 else t.i.to_numpy()
    mu, tt = clust_t(t.net.to_numpy(), blk)
    d = {"n": int(len(t)), "sessions": int(t.i.nunique()), "exp_bps": round(mu * 1e4, 2),
         "t": round(tt, 2) if np.isfinite(tt) else None, "win": round(float((t.net > 0).mean()), 3),
         "gross_bps": round(t.gross.mean() * 1e4, 2), "per_session": round(len(t) / max(1, t.i.nunique()), 1),
         "avg_hold": round(float(t.hold.mean()), 2)}
    if "excess" in t and t.excess.notna().any():
        d["excess_bps"] = round(float(np.nanmean(t.excess)) * 1e4, 2)
    return d


RESULTS = []


def score(cid, fam, side, desc, t, hold, params, stock=True):
    rec = {"id": cid, "family": fam, "side": "long" if side == 1 else "short", "desc": desc, **params}
    if not len(t):
        RESULTS.append({**rec, "split": "all", "n": 0}); return
    if stock:
        t["excess"] = t.gross - side * bench(t)  # long: gross - bench; short: -(raw - bench)
    d = t.date
    parts = {k: t[(d >= a) & (d <= b)] for k, (a, b) in SPLITS.items()}
    parts["trainvalid1"] = t[d <= "2024-10-31"]
    parts["all_open"] = t
    mc = t.date.dt.to_period("M").map(month_class)
    yc = t.date.dt.year.map(year_class)
    for k in ("up", "flat", "down"):
        parts[f"month_{k}"] = t[mc.to_numpy() == k]
        parts[f"year_{k}"] = t[yc.to_numpy() == k]
    if hold <= 1:
        dr = t.date.map(dayreg)
        for k in ("up", "flat", "down"):
            parts[f"day_{k}"] = t[dr.to_numpy() == k]
    for y, g in t.groupby(t.date.dt.year):
        parts[f"y{y}"] = g
    for k, g in parts.items():
        RESULTS.append({**rec, "split": k, **summ(g, hold)})


# ------------------------------------------------------------------------------------------------ F1 overnight
def xs_decile(X, elig, top):
    A = np.where(elig, np.asarray(X, float), np.nan)
    q = np.nanquantile(A, 0.9 if top else 0.1, axis=1)[:, None]
    with np.errstate(invalid="ignore"):
        return (A >= q) if top else (A <= q)


def run_f1():
    cond = {"C0_all": np.ones((T, N), bool),
            "o2c_bot10": xs_decile(o2c, ELIG, False), "o2c_top10": xs_decile(o2c, ELIG, True),
            "clv_lt10": (clv < 0.1).to_numpy(), "clv_gt90": (clv > 0.9).to_numpy(),
            "rsi2_lt5": (rsi2 < 5).to_numpy(), "rsi2_gt95": (rsi2 > 95).to_numpy(),
            "gap_le-3": (gap <= -0.03).to_numpy(), "gap_ge+3": (gap >= 0.03).to_numpy()}
    wd = dates.dayofweek
    for k, nm in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
        cond[f"dow_{nm}"] = np.repeat((wd == k)[:, None], N, 1)
    ym = dates.to_period("M")
    last = np.r_[ym[1:] != ym[:-1], True]
    cond["tom_last"] = np.repeat(last[:, None], N, 1)
    for nm, s in cond.items():
        for side in (1, -1):
            t = make_trades(s, side, "C", "ON")
            score(f"F1_{nm}_{'L' if side == 1 else 'S'}", "F1", side, f"overnight MOC->MOO if {nm}", t, 1, {"cond": nm})
        print("F1", nm, flush=True)


# ------------------------------------------------------------------------------------------------ F2 Connors
def run_f2():
    above = (C > sma200).to_numpy(); below = (C < sma200).to_numpy()
    for side in (1, -1):
        for n, R in ((2, rsi2), (3, rsi3)):
            for thr in (5, 10):
                s = (above & (R < thr).to_numpy()) if side == 1 else (below & (R > 100 - thr).to_numpy())
                for entry in ("C", "O"):
                    for ex in ("K1", "K3", "K5", "SMA5"):
                        if ex == "SMA5":
                            t = make_trades(s, side, entry, "SMA5", elig=ELIG200); hold = 5
                        else:
                            k = int(ex[1]); t = make_trades(s, side, entry, "K", k=k, elig=ELIG200); hold = k
                        cid = f"F2_rsi{n}_{thr}_{entry}_{ex}_{'L' if side == 1 else 'S'}"
                        score(cid, "F2", side, f"Connors {'long >SMA200 RSI' if side == 1 else 'short <SMA200 RSI'}{n} "
                              f"{'<' if side == 1 else '>'}{thr if side == 1 else 100 - thr}, entry {entry}, exit {ex}",
                              t, hold, {"n_rsi": n, "thr": thr, "entry": entry, "exit": ex})
                print("F2", side, n, thr, flush=True)


# ------------------------------------------------------------------------------------------------ F3 momentum / 52wh
def run_f3():
    e2 = ELIG200
    sigs = {"52wh_new": (1, (C >= maxc252).to_numpy()), "52wh_2pct": (1, (C >= 0.98 * maxh252).to_numpy()),
            "mom20_top": (1, xs_decile(ret20, e2, True)), "mom20_bot": (-1, xs_decile(ret20, e2, False)),
            "rev5_bot": (1, xs_decile(ret5, e2, False)), "rev5_top": (-1, xs_decile(ret5, e2, True))}
    for nm, (side, s) in sigs.items():
        for k in (5, 20):
            t = make_trades(s, side, "C", "K", k=k, elig=e2)
            score(f"F3_{nm}_k{k}_{'L' if side == 1 else 'S'}", "F3", side, f"{nm}, MOC, hold {k}d", t, k,
                  {"cond": nm, "k": k})
        print("F3", nm, flush=True)


# ------------------------------------------------------------------------------------------------ F4 post-gap drift
def run_f4():
    for side in (1, -1):
        for g in (0.03, 0.06):
            base = (gap >= g).to_numpy() if side == 1 else (gap <= -g).to_numpy()
            for conf in ("any", "confirm"):
                s = base & ((o2c > 0).to_numpy() if side == 1 else (o2c < 0).to_numpy()) if conf == "confirm" else base
                for k in (1, 5, 10):
                    t = make_trades(s, side, "C", "K", k=k)
                    score(f"F4_g{int(g*100)}_{conf}_k{k}_{'L' if side == 1 else 'S'}", "F4", side,
                          f"gap {'+' if side == 1 else '-'}{int(g*100)}% {conf}, MOC, hold {k}d", t, k,
                          {"g": g, "conf": conf, "k": k})
        print("F4", side, flush=True)


# ------------------------------------------------------------------------------------------------ F5 calendar
def inst_trades(name, sig, entry_kind, exit_off, exit_kind):
    """Single-instrument (SPY/QQQ/IWM) or EW basket trades. entry at close of i (or open of i+1 not used),
    exit at close (or open) of i+exit_off."""
    rows = []
    for i in np.flatnonzero(sig):
        xi = i + exit_off
        if xi >= T:
            continue
        if name == "EW":
            e = ELIG[i]
            ep, xp = Cx[i, e], (Ox[xi, e] if exit_kind == "O" else Cx[xi, e])
            r = xp / ep - 1
            ok = np.isfinite(r)
            if not ok.any():
                continue
            gross = float(r[ok].mean()); c = float((cost(ep[ok]) + cost(xp[ok])).mean()); epm = float(np.nanmean(ep))
        else:
            j = list(syms).index(name)
            ep, xp = Cx[i, j], (Ox[xi, j] if exit_kind == "O" else Cx[xi, j])
            if not (np.isfinite(ep) and np.isfinite(xp)):
                continue
            gross = xp / ep - 1; c = cost(ep) + cost(xp); epm = ep
        rows.append((i, 0, i, xi, epm, np.nan, exit_kind, gross, gross - c))
    t = pd.DataFrame(rows, columns=["i", "j", "ei", "xi", "ep", "xp", "xk", "gross", "net"])
    if not len(t):
        return t
    ed, xd = dates[t.ei.to_numpy()], dates[t.xi.to_numpy()]
    t = t[~((ed <= LOCK_B) & (xd >= LOCK_A))].copy()
    t["date"] = dates[t.i.to_numpy()]; t["hold"] = max(1, exit_off); t["entry"] = "C"
    return t


def run_f5():
    ym = dates.to_period("M")
    pos_from_end = pd.Series(1, index=dates).groupby(ym).cumcount(ascending=False).to_numpy()  # 0 = last day
    tom = pos_from_end == 1  # 2nd-to-last trading day; exit 3rd trading day of next month = +4 sessions
    wd = dates.dayofweek
    for inst in ("SPY", "QQQ", "IWM", "EW"):
        t = inst_trades(inst, tom, "C", 4, "C")
        score(f"F5_TOM_{inst}", "F5", 1, f"{inst} turn of month (MOC -2 -> MOC +3)", t, 4, {"cond": "TOM", "inst": inst},
              stock=False)
        for k, nm in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
            nxt = np.r_[wd[1:] == k, False]  # hold close(i) -> close(i+1) where day i+1 is weekday k
            t = inst_trades(inst, nxt, "C", 1, "C")
            score(f"F5_DOW_{nm}_{inst}", "F5", 1, f"{inst} close-to-close ending {nm}", t, 1, {"cond": f"DOW_{nm}", "inst": inst},
                  stock=False)
        t = inst_trades(inst, np.ones(T, bool), "C", 1, "O")
        score(f"F5_ON_{inst}", "F5", 1, f"{inst} overnight every day", t, 1, {"cond": "ON", "inst": inst}, stock=False)
        print("F5", inst, flush=True)


if __name__ == "__main__":
    fams = sys.argv[1:] or ["F1", "F2", "F3", "F4", "F5"]
    for f in fams:
        globals()[f"run_{f.lower()}"]()
        pd.DataFrame(RESULTS).to_csv(HERE / f"raw_{f}.csv", index=False)
        RESULTS.clear()
