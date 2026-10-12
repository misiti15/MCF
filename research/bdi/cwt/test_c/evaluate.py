"""Apply the gates of NOTES.md 1.4 to raw_daily.csv + raw_intraday.csv -> results.csv (long) + gates.csv (one row per
configuration). Educational only - not financial advice."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LINEAGE = {"C1": 143, "C2": 32, "C3": 8, "C4": 20, "C5": 7, "C6": 4, "C7": 10, "C8": 15, "C9": 42}
PLAN_N = {"C1": 28, "C2": 20, "C3": 8, "C4": 12, "C5": 7, "C6": 4, "C7": 10, "C8": 12, "C9": 16}
BASE = {"C1": "C1_L_rsi3_15_none_L2_sma5", "C2": "C2_M10_B10_w8_sma10", "C3": "C3_sma20_close_2nd_sma20",
        "C4": "C4_N50_none_don20"}


def t_req(n):
    return max(1.5, math.sqrt(2 * math.log(n)))


_raws = [HERE / f for f in ("raw_daily.csv", "raw_intraday.csv") if (HERE / f).exists()]   # deleted after merging
raw = pd.concat([pd.read_csv(p) for p in _raws], ignore_index=True) if _raws else pd.read_csv(HERE / "results.csv")
raw.to_csv(HERE / "results.csv", index=False)
cfg = raw[~raw.family.astype(str).str.endswith("_inst") & raw.family.notna()].drop_duplicates("id").set_index("id")
P = raw.pivot_table(index="id", columns="split", values=["n", "exp_bps", "t", "excess_bps"], aggfunc="first", dropna=False)
ALL = raw[raw.split == "all_open"].drop_duplicates("id").set_index("id")


def g(cid, c, s):
    try:
        v = P.loc[cid, (c, s)]
        return float(v) if pd.notna(v) else np.nan
    except KeyError:
        return np.nan


STEPS = {"C1": {"sig": ["rsi3_15", "rsi2_5"], "R": ["none", "spy200"], "L": [0.02, 0.03, 0.05], "exit": ["sma5", "open"]},
         "C2": {"M": [0.1, 0.2], "B": [10, 20], "w": [0.08, 0.12], "X": ["sma10", "sma20"], "or": [5, 30]},
         "C3": {"k": [20, 50], "entry": ["close", "stop"], "exit": ["2nd_sma20", "k10"]},
         "C4": {"N": [50, 252], "vol": ["none", "v15"], "exit": ["don20", "don50", "bracket"]},
         "C6": {"anchor": ["earn", "h252"], "exit": ["avwap", "k10"]},
         "C7": {"Nd": [3, 4, 5], "exit": ["upclose", "k5"]}}


def nz(v):
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return "" if pd.isna(v) else str(v)


def neighbours(cid):
    m = cfg.loc[cid]
    fam = m.family
    if fam not in STEPS:
        return None
    pcols = [c for c in cfg.columns if c.startswith("p_")]
    same = cfg[(cfg.family == fam) & (cfg.side == m.side)]
    same = same[same.get("p_intraday", pd.Series(np.nan, index=same.index)).map(nz) == nz(m.get("p_intraday", np.nan))]
    if fam == "C7":   # streak / day3 / day5 are separate sub-families
        same = same[same.index.str.split("_").str[1].str[:5] == cid.split("_")[1][:5]]
    out = []
    for p, vals in STEPS[fam].items():
        if f"p_{p}" not in cfg or nz(m.get(f"p_{p}")) == "":
            continue
        vs = [nz(v) for v in vals]
        if nz(m[f"p_{p}"]) not in vs:
            continue
        i = vs.index(nz(m[f"p_{p}"]))
        for jx in (i - 1, i + 1):
            if not 0 <= jx < len(vs):
                continue
            cand = same
            for q in pcols:
                want = vs[jx] if q == f"p_{p}" else nz(m[q])
                cand = cand[cand[q].map(nz) == want]
            out += [x for x in cand.index if x != cid]
    return out


rows = []
for cid, m in cfg.iterrows():
    fam = m.family
    intr = nz(m.get("p_intraday", np.nan)) == "1"
    stock = fam not in ("C5", "C7") and not cid.startswith("C5")
    minn = 20 if fam in ("C5", "C7") else 100
    a = ALL.loc[cid] if cid in ALL.index else None
    r = {"id": cid, "family": fam, "side": m.side, "desc": m.desc, "intraday": intr, "N_plan": PLAN_N[fam],
         "N_lineage": LINEAGE[fam], "t_bar": round(t_req(LINEAGE[fam]), 2), "t_bar_round": round(t_req(1058), 2)}
    for s in ("train", "valid1", "valid2", "trainvalid1", "all_open", "month_up", "month_flat", "month_down",
              "y2018", "y2022", "session_up", "session_down"):
        r[f"{s}_n"] = g(cid, "n", s); r[f"{s}_exp"] = g(cid, "exp_bps", s); r[f"{s}_t"] = g(cid, "t", s)
    for s in ("train", "valid1", "valid2", "all_open"):
        r[f"{s}_excess"] = g(cid, "excess_bps", s)
    for k in ("wf_share", "wf_months", "ex_best_bps", "busiest_share", "busiest_day"):
        r[k] = a[k] if a is not None and k in a else np.nan
    fails = []
    if intr:
        if not (r["all_open_n"] >= 150):
            fails.append(f"n {r['all_open_n']:.0f} < 150")
        if not (r["all_open_exp"] > 0):
            fails.append("exp<=0")
        if not ((r["all_open_t"] or 0) >= r["t_bar"]):
            fails.append(f"t {r['all_open_t']} < {r['t_bar']}")
        for k in ("up", "down"):
            if not (r[f"session_{k}_exp"] > 0 and r[f"session_{k}_n"] >= 30):
                fails.append(f"session_{k} fail")
        fails.append("no train split (two-year history only)")
    else:
        for s in ("train", "valid1", "valid2"):
            if not (r[f"{s}_exp"] > 0):
                fails.append(f"{s} exp<=0")
            if not (r[f"{s}_n"] >= minn):
                fails.append(f"{s} n<{minn}")
        if not ((r["trainvalid1_t"] if np.isfinite(r["trainvalid1_t"]) else 0) >= r["t_bar"]):
            fails.append(f"t {r['trainvalid1_t']} < {r['t_bar']}")
        if not ((r["valid1_t"] if np.isfinite(r["valid1_t"]) else 0) >= 1.5):
            fails.append("valid1 t<1.5")
        if stock and not (r["train_excess"] > 0 and r["valid1_excess"] > 0):
            fails.append("excess<=0")
        for k in ("up", "down"):
            if not (r[f"month_{k}_exp"] > 0 and r[f"month_{k}_n"] >= 30):
                fails.append(f"month_{k} fail")
    nb = neighbours(cid)
    if nb is not None:
        vals = [g(x, "exp_bps", "all_open" if intr else "trainvalid1") for x in nb]
        r["plateau"] = round(float(np.nanmean(vals)), 2) if vals and np.isfinite(vals).any() else np.nan
        r["neighbours"] = ";".join(nb)
        if not (r["plateau"] > 0):
            fails.append("plateau<=0")
    if not (r["wf_share"] >= 0.6):
        fails.append(f"wf {r['wf_share']}")
    if not (r["ex_best_bps"] > 0):
        fails.append("ex-best<=0")
    if not (r["busiest_share"] <= 0.10):
        fails.append(f"busiest {r['busiest_share']}")
    if not (r["all_open_n"] >= 150):
        fails.append("n<150")
    if fam in ("C8", "C9"):
        b = BASE[m.p_base]
        r["base"] = b
        for s in ("train", "valid1", "valid2"):
            r[f"d_{s}_exp"] = r[f"{s}_exp"] - g(b, "exp_bps", s)
        r["d_t_trainvalid1"] = r["trainvalid1_t"] - g(b, "t", "trainvalid1")
        r["d_sum_pl_all"] = (ALL.loc[cid, "sum_pl"] - ALL.loc[b, "sum_pl"]) if cid in ALL.index else np.nan
        r["improves"] = bool(all(r[f"d_{s}_exp"] > 0 for s in ("train", "valid1", "valid2")) and r["d_t_trainvalid1"] > 0)
        if not r["improves"]:
            fails.append("does not improve base")
    all3 = (not intr) and all(r[f"{s}_exp"] > 0 for s in ("train", "valid1", "valid2"))
    r["verdict"] = "candidate" if not fails else ("near" if all3 else "fail")
    r["fails"] = "; ".join(fails)
    rows.append(r)
G = pd.DataFrame(rows).sort_values(["family", "verdict", "id"])
G.to_csv(HERE / "gates.csv", index=False)
print("configs", len(G), G.groupby(["family", "verdict"]).size().unstack(fill_value=0).to_string())
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 300)
cols = ["id", "train_n", "train_exp", "valid1_exp", "valid2_exp", "trainvalid1_t", "t_bar", "valid1_t", "train_excess",
        "valid1_excess", "valid2_excess", "month_up_exp", "month_down_exp", "y2018_exp", "y2022_exp", "plateau", "wf_share",
        "verdict"]
print(G[cols].round(1).to_string(index=False))
