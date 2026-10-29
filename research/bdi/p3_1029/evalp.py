"""p3_1029 step 3b: portfolio simulation of Primary's 8 setups (parent) and every pre-declared config (PLAN.md) on the
open two-year signals from bt.py. Usage: python evalp.py <scratch> <iteration 1|2|3> [best-of-family json for 2/3]
Appends to results.csv and counts.json. Educational only - not financial advice."""
import json
import math
import os
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

S = Path(sys.argv[1]); IT = int(sys.argv[2]); OUT = Path(__file__).resolve().parent
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
TRAIN_END = pd.Timestamp("2025-12-31").date()
CFG = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())
ORDER = {s: i for i, s in enumerate(CFG["live"]["setup_order"])}
PRIOR_N = 8   # sat1024-late-profit-lock 6 + nightly-1027-flatten-1545 2 (PLAN.md)

sig = pd.concat([pd.read_parquet(f) for f in sorted((S / "p3bt").glob("sig_*.parquet"))], ignore_index=True)
d = pd.to_datetime(sig.date).dt.date
assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked row"
sig["date"] = d.astype(str)
lk = pd.read_csv(ROOT / "research/bdi/indexlink/linkage.csv", usecols=["symbol", "sector_etf"])
sig["sector"] = sig.symbol.map(dict(zip(lk.symbol, lk.sector_etf))).fillna("?")
sig["prio"] = sig.setup.map(ORDER).fillna(99)
sig["tie"] = [zlib.crc32(f"{a}|{b}|{c}".encode()) for a, b, c in zip(sig.symbol, sig.date, sig.setup)]
sig = sig.sort_values(["date", "tod", "prio", "tie"]).reset_index(drop=True)
reg = lib.regimes()
reg["date"] = pd.to_datetime(reg["date"]).dt.date.astype(str) if "date" in reg else reg.index.astype(str)
SESS = sorted(reg["date"].unique())
REG = dict(zip(reg["date"], reg["regime"]))


def simulate(cfg):
    """cfg: dict(exit=variant, longs_only_exit=bool, min_rps, max_cost, lots, sym_day, sector_cap, poll_cap)."""
    v = cfg.get("exit", "base")
    r = sig[f"r_{v}"].to_numpy(float); x = sig[f"x_{v}"].to_numpy(float)
    if cfg.get("longs_only_exit"):
        lo = sig.side.to_numpy() == 1
        r = np.where(lo, r, sig.r_base.to_numpy(float)); x = np.where(lo, x, sig.x_base.to_numpy(float))
    keep = np.ones(len(sig), bool)
    if cfg.get("min_rps"):
        keep &= sig.R_ps.to_numpy() >= cfg["min_rps"]
    if cfg.get("max_cost"):
        keep &= sig.cost_stop_r.to_numpy() <= cfg["max_cost"]
    lots, symday, seccap, pollcap = cfg.get("lots", 3), cfg.get("sym_day"), cfg.get("sector_cap"), cfg.get("poll_cap")
    take = np.zeros(len(sig), bool)
    D, T, SY, SD, ST, SE = (sig[k].to_numpy() for k in ("date", "tod", "symbol", "side", "setup", "sector"))
    cur = None; openl = []; seen = set(); polln = {}
    for i in range(len(sig)):
        if D[i] != cur:
            cur, openl, seen, polln = D[i], [], set(), {}
        if not keep[i]:
            continue
        t = T[i]
        openl = [o for o in openl if o[0] > t]
        same = [o for o in openl if o[1] == SY[i]]
        if any(o[2] != SD[i] for o in same) or len(same) >= lots:
            continue
        if sum(1 for o in openl if o[3] == ST[i]) >= 30 or len(openl) >= 77:
            continue
        if symday and SY[i] in seen:
            continue
        if seccap and SE[i] != "?" and sum(1 for o in openl if o[4] == SE[i] and o[2] == SD[i]) >= seccap:
            continue
        if pollcap and polln.get(t, 0) >= pollcap:
            continue
        take[i] = True; seen.add(SY[i]); polln[t] = polln.get(t, 0) + 1
        openl.append((x[i], SY[i], SD[i], ST[i], SE[i]))
    return pd.DataFrame({"date": D[take], "setup": ST[take], "side": SD[take], "r": r[take]})


def gate_rate(day):
    s = pd.Series(day).reindex(SESS, fill_value=0.0).to_numpy()
    w = np.lib.stride_tricks.sliding_window_view(s, 10)
    net = w.sum(1)
    return float((((w > 0).sum(1) >= 7) & (net > 0) & (w.max(1) <= 0.5 * net)).mean())


def score(tr, name, par_day=None):
    s = gates.summary(tr)
    day = tr.groupby("date").r.sum()
    sp = np.where(tr.date.to_numpy() <= str(TRAIN_END), "train", "valid")
    row = dict(config=name, n=s["n"], days=s["days"], avgR=s["exp_r"], shrunk=round(s["exp_r"] * s["n"] / (s["n"] + 20), 4), t=s["t"],
               ex_best=s["ex_best_day"], best_share=round(day.max() / day.sum(), 3) if day.sum() > 0 else None,
               green=round(float((pd.Series(day).reindex(SESS, fill_value=0) > 0).mean()), 3), gate10=round(gate_rate(day), 3),
               totR=round(tr.r.sum(), 1))
    for k in ("train", "valid"):
        g = tr[sp == k]; q = gates.summary(g)
        row[f"{k}_avgR"] = q["exp_r"]; row[f"{k}_t"] = q["t"]; row[f"{k}_shrunk"] = round(q["exp_r"] * q["n"] / (q["n"] + 20), 4); row[f"{k}_n"] = q["n"]
    rg = tr.date.map(REG)
    for k in ("up", "down"):
        row[f"{k}_avgR"] = round(tr.r[rg == k].mean(), 4)
    if par_day is not None:
        dd = day.reindex(SESS, fill_value=0) - par_day.reindex(SESS, fill_value=0)
        se = dd.std(ddof=1) / math.sqrt(len(dd))
        row["delta_day"] = round(dd.mean(), 4); row["delta_t"] = round(dd.mean() / se, 2) if se > 0 else None
        tri = np.array([x <= str(TRAIN_END) for x in dd.index])
        row["delta_train"] = round(dd[tri].mean(), 4); row["delta_valid"] = round(dd[~tri].mean(), 4)
        rr = pd.Series([REG.get(x) for x in dd.index], index=dd.index)
        row["delta_up"] = round(dd[rr == "up"].mean(), 4); row["delta_down"] = round(dd[rr == "down"].mean(), 4)
    return row, day


ITER1 = {"A1_rps010": dict(min_rps=0.10), "A2_rps015": dict(min_rps=0.15), "A3_cost015": dict(max_cost=0.15),
         "B1_lots1": dict(lots=1), "B2_symday1": dict(sym_day=True), "B3_sector2": dict(sector_cap=2), "B4_poll3": dict(poll_cap=3),
         "C1_f1545": dict(exit="f1545"), "C2_f1530": dict(exit="f1530"), "C3_t1500_050": dict(exit="t1500_050"),
         "C4_f1545_longs": dict(exit="f1545", longs_only_exit=True)}
NEIGH = {"A1_rps010": {"A_rps005": dict(min_rps=0.05), "A_rps008": dict(min_rps=0.08), "A_rps012": dict(min_rps=0.12), "A_rps020": dict(min_rps=0.20)},
         "A2_rps015": {"A_rps008": dict(min_rps=0.08), "A_rps012": dict(min_rps=0.12), "A_rps020": dict(min_rps=0.20), "A_rps025": dict(min_rps=0.25)},
         "A3_cost015": {"A_cost008": dict(max_cost=0.08), "A_cost010": dict(max_cost=0.10), "A_cost020": dict(max_cost=0.20), "A_cost025": dict(max_cost=0.25)},
         "B": {"B_lots2": dict(lots=2), "B_poll2": dict(poll_cap=2), "B_poll5": dict(poll_cap=5), "B_sector1": dict(sector_cap=1), "B_sector3": dict(sector_cap=3)},
         "C": {"C_f1540": dict(exit="f1540"), "C_f1550": dict(exit="f1550"), "C_t1500_025": dict(exit="t1500_025"), "C_t1500_075": dict(exit="t1500_075")}}

if __name__ == "__main__":
    cnt_f = OUT / "counts.json"
    counts = json.loads(cnt_f.read_text()) if cnt_f.exists() else {"prior_related": PRIOR_N, "iterations": {}}
    par, par_day = score(simulate({}), "PARENT")
    rows = [par]
    if IT == 1:
        grid = ITER1
    else:
        best = json.loads(Path(sys.argv[3]).read_text())   # {"A": cfgname, "B": cfgname, "C": cfgname} (+ "cfg" dicts for it 3)
        if IT == 2:
            grid = {}
            grid.update(NEIGH[best["A"]])
            bB = {"B1_lots1": ["B_lots2", "B_sector1", "B_poll2", "B_symday"], "B2_symday1": ["B_lots2", "B_poll2", "B_poll5", "B_sector1"],
                  "B3_sector2": ["B_sector1", "B_sector3", "B_lots2", "B_poll2"], "B4_poll3": ["B_poll2", "B_poll5", "B_sector1", "B_lots2"]}[best["B"]]
            grid.update({k: NEIGH["B"][k] for k in bB if k in NEIGH["B"]})
            grid.update(NEIGH["C"])
        else:
            c = best["cfg"]
            grid = {"AB": {**c["A"], **c["B"]}, "AC": {**c["A"], **c["C"]}, "BC": {**c["B"], **c["C"]}, "ABC": {**c["A"], **c["B"], **c["C"]}}
    for name, cfg in grid.items():
        row, _ = score(simulate(cfg), f"it{IT}:{name}", par_day)
        row["cfg"] = json.dumps(cfg)
        rows.append(row)
    counts["iterations"][str(IT)] = len(grid)
    N = counts["prior_related"] + sum(counts["iterations"].values())
    counts["N"] = N; counts["bar"] = round(max(1.5, math.sqrt(2 * math.log(N))), 3)
    cnt_f.write_text(json.dumps(counts, indent=1))
    df = pd.DataFrame(rows)
    df["bar"] = counts["bar"]
    df["pass_bar"] = (df.get("delta_t", pd.Series(np.nan)) >= counts["bar"]) & (df.get("delta_train", 0) > 0) & (df.get("delta_valid", 0) > 0) \
        & (df.get("delta_up", 0) > 0) & (df.get("delta_down", 0) > 0) & (df.train_shrunk >= par["train_shrunk"]) & (df.valid_shrunk >= par["valid_shrunk"])
    f = OUT / "results.csv"
    old = pd.read_csv(f) if f.exists() and IT > 1 else None
    df = df if old is None else pd.concat([old, df[df.config != "PARENT"]], ignore_index=True)
    df.to_csv(f, index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(f"N {N}, bar {counts['bar']}")
    cols = ["config", "n", "avgR", "shrunk", "t", "train_avgR", "valid_avgR", "up_avgR", "down_avgR", "ex_best", "green", "gate10", "totR",
            "delta_day", "delta_t", "delta_train", "delta_valid", "delta_up", "delta_down", "pass_bar"]
    print(df[[c for c in cols if c in df]].to_string(index=False))
    # per-setup parent table (iteration 1 only)
    if IT == 1:
        tr = simulate({})
        print(tr.groupby("setup").r.agg(["size", "mean", "sum"]).round(3).to_string())
        sp = np.where(tr.date <= str(TRAIN_END), "train", "valid")
        print(tr.groupby(sp).r.agg(["size", "mean"]).round(3).to_string())
