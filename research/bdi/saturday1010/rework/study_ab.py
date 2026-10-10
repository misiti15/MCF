"""Saturday 2026-10-10 rework, lineages A (Connors dip buy) and B (weekly reversal basket): the grid pre-declared in
NOTES.md 1.4/1.5, gated per 1.7. Reuses the W3 engine (study.py executed as a prefix with its file writes disabled;
the locked block 2024-11-01..2025-02-28 is NaN-ed from every outcome array exactly as in W3, and no new data file
contains it). Writes results_ab.csv (config x split) and gates_ab.csv. Educational only - not financial advice.
    python research/bdi/saturday1010/rework/study_ab.py
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = HERE / "data"
W3 = ROOT / "research" / "swarm1010" / "w3_daily"
sys.path.insert(0, str(ROOT))
assert os.environ.get("MCF_HIST_ALLOW_LOCKED") is None
from mcf.research.gates import t_required, walk_forward  # noqa: E402

# ---------------------------------------------------------------------------------------------- W3 engine (no writes)
src = (W3 / "study.py").read_text().split('if __name__ == "__main__":')[0]
assert 'LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")' in src
src = src.replace('cov.to_csv(HERE / "coverage_by_year.csv")', "pass")
src = src.replace('json.dump(regime_info, open(HERE / "regimes.json", "w"), indent=1)', "pass")
S: dict = {"__name__": "w3study", "__file__": str(W3 / "study.py")}
exec(compile(src, str(W3 / "study.py"), "exec"), S)
dates, syms, T, N = S["dates"], S["syms"], S["T"], S["N"]
C = S["C"]
LOCK_A, LOCK_B = S["LOCK_A"], S["LOCK_B"]
locked_rows = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))
ELIG200 = S["ELIG200"]
LK = ["2024-11", "2024-12", "2025-01", "2025-02"]
D19 = np.asarray(dates >= "2019-01-02")

# ---------------------------------------------------------------------------------------------- new features
def _no_locked(df, col="date"):
    d = pd.to_datetime(df[col])
    assert not ((d >= LOCK_A) & (d <= LOCK_B)).any(), "locked rows in a feature file"
    return df


vix = _no_locked(pd.read_parquet(DATA / "cboe_vol_indices.parquet"))
vw = vix.pivot(index="date", columns="index", values="close").sort_index()
vw.index = pd.to_datetime(vw.index)
TR_s = (vw["VIX"] / vw["VIX3M"])
VIXP_s = vw["VIX"].dropna().rolling(252, min_periods=200).apply(lambda x: (x <= x[-1]).mean(), raw=True)
TR = TR_s.reindex(dates).to_numpy()            # NaN on a stock session with no VIX row -> filter false
VIXP = VIXP_s.reindex(dates).to_numpy()

ty = _no_locked(pd.read_parquet(DATA / "treasury_yields.parquet", columns=["date", "t10y2y"]))
CURVE = ty.set_index(pd.to_datetime(ty.date))["t10y2y"].sort_index().reindex(dates).ffill(limit=5).to_numpy()

spy = C["SPY"]
SPY200 = (spy > spy.rolling(200, min_periods=200).mean()).to_numpy()

# FINRA short-volume ratio, 20 available sessions
uni = set(syms)
parts = []
for y in range(2019, 2027):
    f = _no_locked(pd.read_parquet(DATA / f"finra_shvol_{y}.parquet", columns=["date", "symbol", "shortvolume", "totalvolume"]))
    f = f[f.symbol.isin(uni) & (f.totalvolume > 0)]
    parts.append(pd.DataFrame({"date": pd.to_datetime(f.date), "symbol": f.symbol.astype(str),
                               "r": (f.shortvolume / f.totalvolume).astype("float32")}))
fin = pd.concat(parts, ignore_index=True)
del parts
fin = fin.drop_duplicates(["date", "symbol"])
svr = fin.pivot(index="date", columns="symbol", values="r").sort_index()
del fin
svr20 = svr.rolling(20, min_periods=10).mean().reindex(index=dates, columns=syms)
SVR20 = svr20.to_numpy(float)
del svr, svr20

# earnings sessions
ec = _no_locked(pd.read_parquet(DATA / "earnings_cal.parquet", columns=["date", "symbol"]))
ec = ec[ec.symbol.isin(uni)]
pos = np.searchsorted(dates.values, pd.to_datetime(ec.date).values.astype(dates.values.dtype))
EARN = np.zeros((T, N), np.int32)
colix = {s: k for k, s in enumerate(syms)}
ok = pos < T
EARN[pos[ok], [colix[s] for s in ec.symbol[ok]]] = 1
CS = np.vstack([np.zeros((1, N), np.int64), EARN.cumsum(0)])  # CS[i+1] = sum EARN[0..i]


def earn_in(lo, hi):
    """bool (T,N): an earnings session in [i+lo, i+hi] (clipped to the sample)."""
    i = np.arange(T)
    a = np.clip(i + lo, 0, T); b = np.clip(i + hi + 1, 0, T)
    return (CS[b] - CS[a]) > 0


def lag1(x):
    out = np.empty_like(x)
    out[0] = np.nan if x.dtype.kind == "f" else False
    out[1:] = x[:-1]
    return out


def xs_top(X, elig, q):
    """True where X is in the top q share of the day's eligible names (NaN -> False)."""
    A = np.where(elig, X, np.nan)
    out = np.zeros((T, N), bool)
    for i in range(T):
        a = A[i]
        if np.isfinite(a).sum() >= 20:
            out[i] = a >= np.nanquantile(a, 1 - q)
    return out


# ---------------------------------------------------------------------------------------------- filters
def filters(lineage):
    """name -> (row mask (T,) or matrix (T,N) of allowed signals, uses_2019_data)."""
    lagged = lineage == "B"
    tr = lag1(TR) if lagged else TR
    vp = lag1(VIXP) if lagged else VIXP
    sv = lag1(SVR20) if lagged else SVR20
    hold_hi = 10 if lineage == "A" else None
    with np.errstate(invalid="ignore"):
        F = {f"TR{int(th*100)}": ((tr >= th), False) for th in (0.90, 0.95, 1.00, 1.05)}
        F.update({f"VP{int(p*100)}": ((vp >= p), False) for p in (0.3, 0.5, 0.7)})
    for q in (10, 20, 33):
        F[f"SV{q}"] = (~xs_top(sv, ELIG200, q / 100), True)
    F["SPY200"] = (SPY200, False)
    with np.errstate(invalid="ignore"):
        F["Y1"] = (CURVE > 0, False)
    F["_E"] = hold_hi  # placeholder, earnings built per base (needs k)
    return F


def earn_filters(lineage, k):
    if lineage == "A":
        return {"E1": ~earn_in(1, 10), "E2": ~earn_in(-3, 10)}
    return {"E1": ~earn_in(0, k), "E2": ~earn_in(-3, k)}


def as_mat(m):
    m = np.asarray(m, bool)
    return np.repeat(m[:, None], N, 1) if m.ndim == 1 else m


# ---------------------------------------------------------------------------------------------- scoring
ROWS = []
GROWS = []


def summ(t, hold):
    return S["summ"](t, hold)


def score_cfg(cid, lineage, base, filt, t, hold, uses19):
    side = 1
    t = t.copy()
    t["excess"] = t.gross - S["bench"](t)
    d = t.date
    sp = {"train": ("2016-01-01", "2022-12-31"), "train19": ("2019-01-01", "2022-12-31"),
          "valid1": ("2023-01-01", "2024-10-31"), "valid2": ("2025-03-01", "2026-12-31")}
    parts_ = {k: t[(d >= a) & (d <= b)] for k, (a, b) in sp.items()}
    parts_["trainvalid1"] = t[d <= "2024-10-31"]
    parts_["trainvalid19"] = t[(d >= "2019-01-01") & (d <= "2024-10-31")]
    parts_["all_open"] = t
    mc = t.date.dt.to_period("M").map(S["month_class"])
    for k in ("up", "flat", "down"):
        parts_[f"month_{k}"] = t[mc.to_numpy() == k]
    yc = t.date.dt.year.map(S["year_class"])
    parts_["year_down"] = t[yc.to_numpy() == "down"]
    for y, g in t.groupby(t.date.dt.year):
        parts_[f"y{y}"] = g
    rec = {"id": cid, "lineage": lineage, "base": base, "filter": filt, "uses2019": uses19}
    out = {}
    for k, g in parts_.items():
        s = summ(g, hold) if len(g) else {"n": 0}
        ROWS.append({**rec, "split": k, **s})
        out[k] = s
    wf = walk_forward(pd.DataFrame({"date": t.date, "r": t.net}), exclude_months=LK)
    out["wf"] = wf["share_positive"]
    out["wf_folds"] = wf["n_folds"]
    return out


def run_lineage(lineage):
    if lineage == "A":
        above = (C > S["sma200"]).to_numpy()
        bases = {"b35": above & (S["rsi3"] < 5).to_numpy(), "b310": above & (S["rsi3"] < 10).to_numpy(),
                 "b25": above & (S["rsi2"] < 5).to_numpy()}
        hold = 5

        def trades(sig, base):
            return S["make_trades"](sig, 1, "O", "SMA5", elig=ELIG200)
    else:
        sig5 = S["xs_decile"](S["ret5"], ELIG200, False)
        bases = {"k20": sig5, "k10": sig5}

        def trades(sig, base):
            k = int(base[1:])
            return S["make_trades"](sig, 1, "C", "K", k=k, elig=ELIG200)
    F = filters(lineage)
    F.pop("_E")
    res = {}
    for b, sig in bases.items():
        hold = 5 if lineage == "A" else int(b[1:])
        k = None if lineage == "A" else int(b[1:])
        EF = earn_filters(lineage, k)
        # controls (parent, not counted): full sample and 2019+ sample
        t0 = trades(sig, b)
        res[(b, "BASE")] = score_cfg(f"{lineage}_{b}_BASE", lineage, b, "BASE", t0, hold, False)
        res[(b, "BASE19")] = score_cfg(f"{lineage}_{b}_BASE19", lineage, b, "BASE19", t0[t0.date >= "2019-01-02"], hold, True)
        allf = {**{k_: v for k_, v in F.items()}, **{k_: (v, True) for k_, v in EF.items()}}
        for fn, (m, u19) in allf.items():
            s = sig & as_mat(m)
            if u19:
                s = s & D19[:, None]
            t = trades(s, b)
            res[(b, fn)] = score_cfg(f"{lineage}_{b}_{fn}", lineage, b, fn, t, hold, u19)
            print(lineage, b, fn, res[(b, fn)]["trainvalid1"].get("n"), res[(b, fn)]["trainvalid1"].get("exp_bps"),
                  res[(b, fn)]["trainvalid1"].get("t"), flush=True)
        if b in ("b35", "k20"):
            combos = [("TR95", "E2"), ("TR95", "SV20"), ("TR95", "SPY200"), ("VP50", "E2"), ("VP50", "SV20"),
                      ("VP50", "SPY200"), ("TR95", "E2", "SV20")]
            for cb in combos:
                m = np.ones((T, N), bool); u19 = False
                for fn in cb:
                    mm, uu = allf[fn]
                    m &= as_mat(mm); u19 |= uu
                s = sig & m
                if u19:
                    s = s & D19[:, None]
                fn = "+".join(cb)
                t = trades(s, b)
                res[(b, fn)] = score_cfg(f"{lineage}_{b}_{fn}", lineage, b, fn, t, hold, u19)
                print(lineage, b, fn, res[(b, fn)]["trainvalid1"].get("n"), flush=True)
            if lineage == "A":
                nos = (S["rsi3"] < 5).to_numpy()
                for fn, s in (("noSMA200", nos), ("noSMA200+TR95", nos & as_mat(allf["TR95"][0]))):
                    t = trades(s, b)
                    res[(b, fn)] = score_cfg(f"{lineage}_{b}_{fn}", lineage, b, fn, t, hold, False)
                    print(lineage, b, fn, res[(b, fn)]["trainvalid1"].get("n"), flush=True)
    return res


# ---------------------------------------------------------------------------------------------- gates (NOTES 1.7)
LINEAGE_N = {"A": 115, "B": 47}
ORDERED = {"TR": ["TR90", "TR95", "TR100", "TR105"], "VP": ["VP30", "VP50", "VP70"], "SV": ["SV10", "SV20", "SV33"],
           "E": ["E1", "E2"]}
BASE_NB = {"A": {"b35": ["b310", "b25"], "b310": ["b35"], "b25": ["b35"]}, "B": {"k20": ["k10"], "k10": ["k20"]}}
COUNTED = lambda f: f not in ("BASE", "BASE19")  # noqa: E731


def neighbours(lineage, b, f):
    out = []
    if "+" in f:
        return [(b, x) for x in f.split("+")]
    if f.startswith("noSMA200"):
        return [(b, "BASE")] if f == "noSMA200" else [(b, "noSMA200"), (b, "TR95")]
    for seq in ORDERED.values():
        if f in seq:
            i = seq.index(f)
            out += [(b, seq[j]) for j in (i - 1, i + 1) if 0 <= j < len(seq)]
    out += [(nb, f) for nb in BASE_NB[lineage][b]]
    return out


def gate(lineage, res):
    treq = t_required(LINEAGE_N[lineage])
    rows = []
    for (b, f), r in res.items():
        u19 = any(x in f for x in ("SV", "E1", "E2")) or f == "BASE19"
        tr_key, tv_key = ("train19", "trainvalid19") if u19 else ("train", "trainvalid1")
        g = lambda k, c: (r.get(k) or {}).get(c)  # noqa: E731
        fails = []
        for s in (tr_key, "valid1", "valid2"):
            if not ((g(s, "exp_bps") or -1) > 0):
                fails.append(f"{s} exp<=0")
            if not ((g(s, "n") or 0) >= 100):
                fails.append(f"{s} n<100")
        if not ((g(tv_key, "t") or 0) >= treq):
            fails.append(f"t {g(tv_key, 't')} < {treq}")
        if not ((g("valid1", "t") or 0) >= 1.5):
            fails.append("valid1 t<1.5")
        if not ((g(tr_key, "excess_bps") or -1) > 0 and (g("valid1", "excess_bps") or -1) > 0):
            fails.append("excess<=0")
        for k in ("up", "down"):
            if not ((g(f"month_{k}", "exp_bps") or -1) > 0 and (g(f"month_{k}", "n") or 0) >= 30):
                fails.append(f"month_{k} fail")
        nb = [x for x in neighbours(lineage, b, f) if x in res] if COUNTED(f) else []
        pl = float(np.nanmean([(res[x].get("trainvalid1") or {}).get("exp_bps", np.nan) for x in nb])) if nb else np.nan
        if COUNTED(f) and not (pl > 0):
            fails.append("plateau<=0")
        if not ((r.get("wf") or 0) >= 0.6):
            fails.append(f"wf {r.get('wf')} < 0.6")
        all3 = all((g(s, "exp_bps") or -1) > 0 for s in (tr_key, "valid1", "valid2"))
        verdict = ("control" if not COUNTED(f) else "candidate" if not fails else "near" if all3 else "fail")
        rows.append({"id": f"{lineage}_{b}_{f}", "lineage": lineage, "base": b, "filter": f, "uses2019": u19,
                     "N_lineage": LINEAGE_N[lineage], "t_req": treq, "verdict": verdict,
                     "train_split": tr_key,
                     **{f"{s}_{c}": g(s, c) for s in ("train", "train19", "valid1", "valid2",
                                                       "trainvalid1", "trainvalid19", "month_up", "month_down",
                                                       "year_down") for c in ("n", "exp_bps", "t", "excess_bps")},
                     "wf_share": r.get("wf"), "wf_folds": r.get("wf_folds"), "plateau_bps": round(pl, 2) if nb else None,
                     "neighbours": ";".join(f"{x[0]}_{x[1]}" for x in nb), "fails": "; ".join(fails)})
    return rows


if __name__ == "__main__":
    allrows = []
    for L in ("A", "B"):
        res = run_lineage(L)
        allrows += gate(L, res)
        pd.DataFrame(ROWS).to_csv(HERE / "results_ab.csv", index=False)
        pd.DataFrame(allrows).to_csv(HERE / "gates_ab.csv", index=False)
    G = pd.DataFrame(allrows)
    print(G.groupby(["lineage", "verdict"]).size())
