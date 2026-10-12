"""BDI 2026-10-12: index confirmation for the package-B long lists (Study A, 800 configs) and a same-side crowding cap
on the Testing-2 long book (Study B, 3 configs). Pre-declared in PLAN.md. Open history only (the rule-19 locked block
is never loaded). Educational only - not financial advice.

    python research/bdi/bdi1012/score.py      -> results_a.csv, results_b.csv
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TB = ROOT / "research" / "bdi" / "cwt" / "test_b"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(TB))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from score import cname, grid  # noqa: E402  (test_b grid; numba kernels unused)

TRAIN_END = "2025-12-31"
EXTRA_N = 1052 + 912 + 800
FILTERS = ["X1_spy_fo", "X2_spy_vwap", "X3_qqq_fo", "X4_qqq_vwap", "X5_notlow"]


def index_state() -> pd.DataFrame:
    p = HERE / "data" / "index_state.parquet"
    if p.exists():
        return pd.read_parquet(p)
    out = []
    for m in lib.months():
        df = lib.load_month(m, columns=["symbol", "date", "tod", "fromOpen", "vwapDistPct", "dist_lod_atr"])
        out.append(df[df.symbol.isin(["SPY", "QQQ"])])
    x = pd.concat(out)
    x["date"] = x["date"].astype(str)
    w = x.pivot_table(index=["date", "tod"], columns="symbol", values=["fromOpen", "vwapDistPct", "dist_lod_atr"])
    w.columns = [f"{s}_{v}" for v, s in w.columns]
    w = w.reset_index()
    w.to_parquet(p, index=False)
    return w


def tstat(r, day):
    if len(r) < 2:
        return 0.0
    mu = r.mean()
    g = pd.DataFrame({"d": day, "r": r}).groupby("d")["r"].agg(["sum", "size"])
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)
    return float(mu / se) if se > 0 else 0.0


def split_stats(dd, r):
    o = {}
    for nm, m in (("tr", dd <= TRAIN_END), ("va", dd > TRAIN_END), ("all", np.ones(len(dd), bool))):
        o[f"{nm}_n"] = int(m.sum())
        o[f"{nm}_exp"] = round(float(r[m].mean()), 4) if m.any() else np.nan
        o[f"{nm}_t"] = round(tstat(r[m], dd[m]), 2) if m.sum() > 1 else np.nan
    return o


def full_gates(dd, r, reg, N):
    tr = pd.DataFrame({"date": pd.to_datetime(dd).date, "r": r})
    sm = gates.summary(tr)
    rg = gates.regime_split(tr, reg)
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    v, fails = gates.verdict(sm, rg, wf, N)
    S = tr.groupby("date")["r"].size()
    return {"up_exp": rg["up"].get("exp_r"), "down_exp": rg["down"].get("exp_r"), "regime_pass": rg["pass"],
            "wf": wf["share_positive"], "ex_best_day": sm["ex_best_day"], "maxday": round(float(S.max() / len(r)), 4),
            "t_req": gates.t_required(N), "verdict": v, "fails": "; ".join(fails)}


def main():
    G = grid()
    z = np.load(TB / "data" / "trades.npz", allow_pickle=True)
    meta = json.load(open(TB / "data" / "baseline.json"))
    dates = np.array(meta["dates"])
    nlin = pd.read_csv(TB / "results.csv").groupby("fam")["N_lineage"].first().to_dict()
    reg = lib.regimes()
    ix = index_state().set_index(["date", "tod"])
    base_lists = [c for c in G if c["side"] == "long" and c["fam"] in ("B2", "B3", "B4", "B5")
                  and not (c["fam"] == "B2" and c["U"] != "all")]
    assert len(base_lists) == 160, len(base_lists)
    rows, T = [], {}
    for c in base_lists:
        k = c["id"]
        d = {f: z[f"{k}|{f}"] for f in ("day", "sym", "tod", "xtod", "r", "rh")}
        dd = dates[d["day"].astype(int)]
        key = pd.MultiIndex.from_arrays([dd, d["tod"].astype(int)])
        s = ix.reindex(key)
        have = s.notna().all(axis=1).to_numpy()
        masks = {"X1_spy_fo": s["SPY_fromOpen"].to_numpy() > 0, "X2_spy_vwap": s["SPY_vwapDistPct"].to_numpy() > 0,
                 "X3_qqq_fo": s["QQQ_fromOpen"].to_numpy() > 0, "X4_qqq_vwap": s["QQQ_vwapDistPct"].to_numpy() > 0,
                 "X5_notlow": (s["SPY_dist_lod_atr"].to_numpy() >= 0.10) & (s["QQQ_dist_lod_atr"].to_numpy() >= 0.10)}
        N = int(nlin[c["fam"]]) + EXTRA_N
        r, rh = d["r"].astype(float), d["rh"].astype(float)
        base = {"name": cname(c), "fam": c["fam"], "filter": "base", "N_lineage": N, "missing_ix": int((~have).sum())}
        rows.append(base | split_stats(dd, r) | full_gates(dd, r, reg, N) | {"hedged_exp": round(float(np.nanmean(rh)), 4)})
        T[c["id"]] = (c, dd, d)
        for f in FILTERS:
            m = masks[f] & have
            row = {"name": cname(c), "fam": c["fam"], "filter": f, "N_lineage": N, "missing_ix": int((~have).sum())}
            if m.sum() < 2:
                rows.append(row | {"all_n": int(m.sum()), "verdict": "retire"})
                continue
            row |= split_stats(dd[m], r[m]) | full_gates(dd[m], r[m], reg, N)
            row |= {"hedged_exp": round(float(np.nanmean(rh[m])), 4),
                    "dropped_exp": round(float(r[~m].mean()), 4) if (~m).any() else np.nan,
                    "base_exp": rows[-1 - FILTERS.index(f)]["all_exp"] if False else None}
            rows.append(row)
    A = pd.DataFrame(rows)
    b = A[A["filter"] == "base"].set_index("name")
    A["base_all_exp"] = A["name"].map(b["all_exp"])
    A["base_tr_exp"] = A["name"].map(b["tr_exp"])
    A["base_va_exp"] = A["name"].map(b["va_exp"])
    F = A[A["filter"] != "base"].copy()
    F["plateau"] = F.apply(lambda x: F[(F.name == x["name"]) & (F["filter"] != x["filter"])]["all_exp"].mean(), axis=1)
    A = A.merge(F[["name", "filter", "plateau"]], on=["name", "filter"], how="left")
    ok = A["filter"] != "base"
    A["primary_cand"] = ok & (A.tr_exp > 0) & (A.va_exp > 0) & (A.all_n >= 150) & (A.verdict == "keep") & (A.plateau > 0) \
        & (A.ex_best_day > 0) & (A.maxday <= 0.10) & (A.hedged_exp > 0) & (A.all_exp > A.base_all_exp)
    A["testing_near"] = ok & (A.all_exp > 0) & (A.tr_exp > 0) & (A.va_exp > 0) & (A.all_n >= 150) & (A.regime_pass == True) \
        & (A.wf >= 0.6) & (A.all_t >= 2.0) & (A.hedged_exp > 0)
    A["improves_tr_va"] = ok & (A.tr_exp > A.base_tr_exp) & (A.va_exp > A.base_va_exp)
    A.drop(columns=["base_exp"], errors="ignore").to_csv(HERE / "results_a.csv", index=False)

    # ---------------- Study B: crowding cap on the Testing-2 long book
    cfg = yaml.safe_load((ROOT / "config" / "account_testing2.yaml").read_text())
    srcs = []
    def walk(o):
        if isinstance(o, dict):
            if "testing2" in o and isinstance(o["testing2"], dict) and "source" in o["testing2"]:
                srcs.append(o["testing2"]["source"])
            for v in o.values():
                walk(v)
    walk(cfg)
    byname = {cname(c): c for c in G}
    book = [byname[s] for s in srcs if s in byname and byname[s]["side"] == "long"]
    parts = []
    for i, c in enumerate(book):
        k = c["id"]
        parts.append(pd.DataFrame({"date": dates[z[f"{k}|day"].astype(int)], "sym": z[f"{k}|sym"], "tod": z[f"{k}|tod"].astype(int),
                                   "xtod": z[f"{k}|xtod"].astype(int), "r": z[f"{k}|r"].astype(float), "pri": i}))
    bk = pd.concat(parts).sort_values(["date", "tod", "pri"], kind="mergesort").reset_index(drop=True)

    def run(cap):
        keep = np.zeros(len(bk), bool)
        for dt, g in bk.groupby("date", sort=False):
            open_ = []  # (xtod, sym)
            for i, tod, xt, sy in zip(g.index, g.tod.to_numpy(), g.xtod.to_numpy(), g.sym.to_numpy()):
                open_ = [(x, s) for x, s in open_ if x > tod]   # exits at or before this bar close are flat
                if any(s == sy for _, s in open_):
                    continue
                if cap is not None and len(open_) >= cap:
                    continue
                open_.append((xt, sy))
                keep[i] = True
        return keep

    base_keep = run(None)
    out = []
    rng = np.random.default_rng(1012)
    for cap in (None, 10, 20, 40):
        kp = run(cap)
        sel = bk[kp]
        row = {"cap": "none" if cap is None else cap, "book_lists": len(book)} | split_stats(sel.date.to_numpy(), sel.r.to_numpy())
        ds = sel.groupby("date")["r"].sum()
        row |= {"total_R": round(float(sel.r.sum()), 1), "worst5pct_day_R": round(float(ds.quantile(0.05)), 2),
                "worst_day_R": round(float(ds.min()), 2)}
        if cap is not None:
            # random-skip control: drop the same number of trades per session from the uncapped book, at random
            ub = bk[base_keep]
            need = ub.groupby("date").size() - sel.groupby("date").size().reindex(ub.date.unique(), fill_value=0)
            ctrl = {"tr": [], "va": [], "all": []}
            for _ in range(20):
                ix_keep = []
                for dt, g in ub.groupby("date", sort=False):
                    k = int(need.get(dt, 0))
                    idx = g.index.to_numpy()
                    ix_keep.append(rng.choice(idx, len(idx) - k, replace=False) if k > 0 else idx)
                cc = ub.loc[np.concatenate(ix_keep)]
                d2 = cc.date.to_numpy()
                ctrl["tr"].append(cc.r[d2 <= TRAIN_END].mean()); ctrl["va"].append(cc.r[d2 > TRAIN_END].mean()); ctrl["all"].append(cc.r.mean())
            row |= {f"ctrl_{k}_exp": round(float(np.mean(v)), 4) for k, v in ctrl.items()}
        out.append(row)
    B = pd.DataFrame(out)
    B.to_csv(HERE / "results_b.csv", index=False)
    print("book lists", [cname(c) for c in book])
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(B)
        print(A.groupby("filter")[["primary_cand", "testing_near", "improves_tr_va"]].sum())
        cols = ["name", "filter", "tr_n", "tr_exp", "tr_t", "va_n", "va_exp", "va_t", "all_n", "all_exp", "all_t", "up_exp",
                "down_exp", "wf", "hedged_exp", "base_all_exp", "plateau", "verdict"]
        print(A[ok].sort_values("all_t", ascending=False)[cols].head(25).to_string(index=False))


if __name__ == "__main__":
    main()
