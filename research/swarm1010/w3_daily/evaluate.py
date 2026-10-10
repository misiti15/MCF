"""Apply the pre-declared gates (NOTES.md 1.7) to raw_F*.csv -> results.csv (long format) + gates.csv (one row per config).
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from mcf.research.gates import t_required  # noqa: E402

FAM_N = {"F1": 30, "F2": 64, "F3": 12, "F4": 24, "F5": 28}
_raws = sorted(HERE.glob("raw_F*.csv"))  # written by study.py; deleted after merging into results.csv
raw = pd.concat([pd.read_csv(p) for p in _raws], ignore_index=True) if _raws else pd.read_csv(HERE / "results.csv")
for c in ("excess_bps",):
    if c not in raw:
        raw[c] = np.nan
raw.to_csv(HERE / "results.csv", index=False)
P = raw.pivot_table(index="id", columns="split", values=["n", "exp_bps", "t", "excess_bps", "gross_bps", "per_session"],
                    aggfunc="first", dropna=False)
meta = raw.drop_duplicates("id").set_index("id")


def g(cid, col, split):
    try:
        v = P.loc[cid, (col, split)]
        return float(v) if pd.notna(v) else np.nan
    except KeyError:
        return np.nan


def neighbours(cid):
    m = meta.loc[cid]
    fam = m.family
    same = meta[(meta.family == fam) & (meta.side == m.side)]
    out = []
    if fam == "F2":
        steps = {"n_rsi": [2, 3], "thr": [5, 10], "entry": ["C", "O"], "exit": ["K1", "K3", "K5", "SMA5"]}
    elif fam == "F3":
        steps = {"k": [5, 20]}
        same = same[same.cond == m.cond]
    elif fam == "F4":
        steps = {"g": [0.03, 0.06], "conf": ["any", "confirm"], "k": [1, 5, 10]}
    else:
        return None
    def nz(v):
        try:
            return f"{float(v):g}"
        except (TypeError, ValueError):
            return str(v)

    for p, vals in steps.items():
        vs = [nz(v) for v in vals]
        i = vs.index(nz(m[p]))
        for j in (i - 1, i + 1):
            if 0 <= j < len(vals):
                cand = same
                for q in steps:
                    want = vs[j] if q == p else nz(m[q])
                    cand = cand[cand[q].map(nz) == want]
                out += list(cand.index)
    return out


rows = []
for cid, m in meta.iterrows():
    fam = m.family
    minn = 20 if fam == "F5" else 100
    r = {"id": cid, "family": fam, "side": m.side, "desc": m.desc, "N_family": FAM_N[fam], "t_req": t_required(FAM_N[fam])}
    for s in ("train", "valid1", "valid2", "trainvalid1", "month_up", "month_down", "year_down", "year_up"):
        r[f"{s}_n"] = g(cid, "n", s); r[f"{s}_exp"] = g(cid, "exp_bps", s); r[f"{s}_t"] = g(cid, "t", s)
    r["train_excess"] = g(cid, "excess_bps", "train"); r["valid1_excess"] = g(cid, "excess_bps", "valid1")
    r["valid2_excess"] = g(cid, "excess_bps", "valid2"); r["per_session_v2"] = g(cid, "per_session", "valid2")
    fails = []
    for s in ("train", "valid1", "valid2"):
        if not (r[f"{s}_exp"] > 0):
            fails.append(f"{s} exp<=0")
        if not (r[f"{s}_n"] >= minn):
            fails.append(f"{s} n<{minn}")
    if not ((r["trainvalid1_t"] or 0) >= r["t_req"]):
        fails.append(f"t {r['trainvalid1_t']} < {r['t_req']}")
    if not ((r["valid1_t"] or 0) >= 1.5):
        fails.append("valid1 t<1.5")
    if m.side == "long" and fam != "F5" and not (r["train_excess"] > 0 and r["valid1_excess"] > 0):
        fails.append("excess<=0")
    for k in ("up", "down"):
        if not (r[f"month_{k}_exp"] > 0 and r[f"month_{k}_n"] >= 30):
            fails.append(f"month_{k} fail")
    nb = neighbours(cid)
    if nb is not None:
        vals = [g(x, "exp_bps", "trainvalid1") for x in nb]
        r["plateau"] = round(float(np.nanmean(vals)), 2) if vals else np.nan
        if not (r["plateau"] > 0):
            fails.append("plateau<=0")
    else:
        r["plateau"] = None
    all3 = all(r[f"{s}_exp"] > 0 for s in ("train", "valid1", "valid2"))
    r["verdict"] = "candidate" if not fails else ("near" if all3 else "fail")
    r["fails"] = "; ".join(fails)
    rows.append(r)
G = pd.DataFrame(rows).sort_values(["verdict", "family", "id"])
G.to_csv(HERE / "gates.csv", index=False)
print(G.verdict.value_counts().to_dict(), "configs", len(G))
cols = ["id", "train_exp", "valid1_exp", "valid2_exp", "trainvalid1_t", "valid1_t", "train_excess", "valid1_excess",
        "month_up_exp", "month_down_exp", "year_down_exp", "plateau", "per_session_v2", "fails"]
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
for v in ("candidate", "near"):
    print(f"--- {v}"); print(G[G.verdict == v][cols].round(2).to_string(index=False))
