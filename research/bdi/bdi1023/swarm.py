"""bdi1023 swarm (PLAN.md, pre-declared): backlog nightly-1023-wide-stop-pct-risk on the two-year history.
A/B skip wide-stop-% entries, C/D down-size them; per book (Primary / Testing 1 / Testing 2). 21 configs, gates1021's
cached live-shaped signal tables (costs in). The locked block 2024-11-01..2025-02-28 is never read (no_locked asserts in
load_sig). No holdout scored.  Usage: python swarm.py > swarm_out.txt     Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gates1021" / "scripts"))
from load import load_sig  # noqa: E402
from part_b import evaluate  # noqa: E402
from mcf.research.gates import GEOMK  # noqa: E402

U = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv").set_index("setup")
BOOKS = {"primary": "primary", "testing1": "testing", "testing2": "testing2"}
N_GATE = 718 + 196 + 340 + 36 + 12
BAR_GATE = round(math.sqrt(2 * math.log(N_GATE)), 2)
BAR_SIZE = round(max(1.5, math.sqrt(2 * math.log(9))), 2)

sig = load_sig(list(U.index))
sig["geom"] = sig["setup"].map(U["geom"])
sig["side"] = sig["setup"].map(U["side"])
dn = sig["geom"].map(lambda g: GEOMK[g][1])
sig["stop_pct"] = dn * 0.25 * sig["atr_d"] / sig["close"] * 100
sig["ctrl"] = np.nan
for (s, g), ix in sig.groupby(["side", "geom"]).groups.items():
    sig.loc[ix, "ctrl"] = sig.loc[ix, f"c_{s}_{g}"]
sig = sig[np.isfinite(sig["stop_pct"]) & (sig["stop_pct"] > 0)]
p75 = sig[sig.split == "train"].groupby("setup")["stop_pct"].quantile(0.75)


def day_t(D: pd.Series) -> tuple[float, float]:
    D = D.astype(float)
    if len(D) < 2 or D.std(ddof=1) == 0:
        return float("nan"), float("nan")
    return float(D.mean()), float(D.mean() / (D.std(ddof=1) / math.sqrt(len(D))))


def size_eval(s: pd.DataFrame, w: np.ndarray) -> dict:
    base = s["r"] * s["stop_pct"]
    var = base * w
    out = {}
    d = pd.DataFrame({"date": s["date"], "split": s["split"], "regime": s["regime"], "b": base, "v": var})
    for sp in ("train", "valid", "all"):
        x = d if sp == "all" else d[d.split == sp]
        g = x.groupby("date")[["b", "v"]].sum()
        D = g["v"] - g["b"]
        out[f"{sp}_n"] = len(x)
        out[f"{sp}_avgR"] = round(float(s.loc[x.index, "r"].mean()), 4)
        out[f"{sp}_base_usd_per_trade"] = round(float(x["b"].mean()), 5)   # slot % units
        out[f"{sp}_var_usd_per_trade"] = round(float(x["v"].mean()), 5)
        out[f"{sp}_delta_per_trade"] = round(float(D.sum() / max(1, len(x))), 5)
        out[f"{sp}_delta_t"] = round(day_t(D)[1], 2)
        if sp == "all":
            out["all_delta_ex_best_day"] = round(float((D.sum() - D.max()) / max(1, len(x))), 5)
    for reg in ("up", "flat", "down"):
        x = d[d.regime == reg]
        out[f"{reg}_delta_per_trade"] = round(float((x["v"] - x["b"]).sum() / max(1, len(x))), 5)
    out["mean_weight"] = round(float(np.mean(w)), 3)
    return out


rows, desc = [], []
for book, acct in BOOKS.items():
    sts = [st for st in U.index if acct in U.loc[st, "accounts"].split(",")]
    s = sig[sig["setup"].isin(sts)].sort_values(["date", "tod", "setup", "symbol"]).reset_index(drop=True)
    sp = s["stop_pct"].to_numpy(float)
    # descriptive: quintiles of stop % (edges from train)
    edges = np.quantile(sp[s.split.to_numpy() == "train"], [0.2, 0.4, 0.6, 0.8])
    s["q"] = np.digitize(sp, edges)
    t = s.pivot_table(index="q", columns="split", values="r", aggfunc=["mean", "size"]).round(3)
    t["stop_pct_med"] = s.groupby("q")["stop_pct"].median().round(2)
    desc.append((book, edges.round(2), t))
    gates = {f"A{x}": sp > x for x in (1.5, 2.0, 2.5)}
    gates["B-p75"] = sp > s["setup"].map(p75).to_numpy(float)
    for g, blk in gates.items():
        e = evaluate(s, blk, "ctrl")
        kept = 1 - blk.mean()
        ok = (e["train_gated_exp"] or -1) > 0 and (e["valid_gated_exp"] or -1) > 0 \
            and (e["train_delta"] or -1) > 0 and (e["valid_delta"] or -1) > 0 \
            and e["train_delta"] > e["train_ctrl_delta"] and e["valid_delta"] > e["valid_ctrl_delta"] \
            and (e["up_delta"] or -1) >= 0 and (e["down_delta"] or -1) >= 0 \
            and (e["all_delta_t"] or 0) >= BAR_GATE and kept >= 0.75
        rows.append(dict(part="AB", book=book, cfg=g, kept_pct=round(100 * kept, 1), passes=bool(ok), **e))
    med = float(np.median(sp[s.split.to_numpy() == "train"]))
    sizes = {f"C{x}": np.minimum(sp, x) / sp for x in (1.0, 2.0)}
    sizes["D-eq"] = med / sp
    for g, w in sizes.items():
        e = size_eval(s, w)
        ok = e["train_delta_per_trade"] > 0 and e["valid_delta_per_trade"] > 0 and e["up_delta_per_trade"] >= 0 \
            and e["down_delta_per_trade"] >= 0 and (e["all_delta_t"] or 0) >= BAR_SIZE and e["all_delta_ex_best_day"] > 0
        rows.append(dict(part="CD", book=book, cfg=g, kept_pct=100.0, passes=bool(ok), **e))
    # per setup: top train-quartile vs rest (descriptive)
    for st, x in s.groupby("setup"):
        hi = x["stop_pct"] > p75.get(st, np.inf)
        for spl in ("train", "valid"):
            m = x.split == spl
            desc_row = dict(book=book, setup=st, split=spl, n=int(m.sum()), n_hi=int((m & hi).sum()),
                            r_hi=round(float(x.loc[m & hi, "r"].mean()), 3) if (m & hi).any() else None,
                            r_rest=round(float(x.loc[m & ~hi, "r"].mean()), 3) if (m & ~hi).any() else None)
            rows.append(dict(part="setup-desc", **desc_row))

R = pd.DataFrame(rows)
R.to_csv(HERE / "results.csv", index=False)
cfg = R[R.part.isin(["AB", "CD"])]
(HERE / "counts.json").write_text(json.dumps({"configs": len(cfg), "gate_lineage_N": N_GATE, "bar_gate": BAR_GATE,
                                              "size_lineage_N": 9, "bar_size": BAR_SIZE,
                                              "passes": int(cfg.passes.sum()), "locked_block_read": False}, indent=1))
pd.set_option("display.width", 260)
print(f"configs {len(cfg)}, passes {int(cfg.passes.sum())}; bars gate {BAR_GATE} (N {N_GATE}), size {BAR_SIZE} (N 9)")
print("\n== A/B skip gates")
print(cfg[cfg.part == "AB"][["book", "cfg", "kept_pct", "train_parent_exp", "train_gated_exp", "train_in_state_exp",
                             "valid_parent_exp", "valid_gated_exp", "valid_in_state_exp", "train_delta", "valid_delta",
                             "train_ctrl_delta", "valid_ctrl_delta", "up_delta", "down_delta", "all_delta_t",
                             "passes"]].to_string(index=False))
print("\n== C/D sizing (slot-% units: R x weight x stop %)")
print(cfg[cfg.part == "CD"][["book", "cfg", "mean_weight", "train_avgR", "valid_avgR", "train_base_usd_per_trade",
                             "train_var_usd_per_trade", "valid_base_usd_per_trade", "valid_var_usd_per_trade",
                             "train_delta_per_trade", "valid_delta_per_trade", "up_delta_per_trade",
                             "down_delta_per_trade", "all_delta_t", "all_delta_ex_best_day", "passes"]].to_string(index=False))
print("\n== descriptive: avg R after costs by stop-% quintile (train edges)")
for b, e, t in desc:
    print(f"-- {b}: edges {list(e)}")
    print(t.to_string())
sd = R[R.part == "setup-desc"]
w = sd.pivot_table(index=["book", "setup"], columns="split", values=["r_hi", "r_rest", "n_hi"])
w["worse_both"] = (w[("r_hi", "train")] < w[("r_rest", "train")]) & (w[("r_hi", "valid")] < w[("r_rest", "valid")])
print("\n== per setup: top train-quartile stop % vs rest (descriptive)")
print(w.round(3).to_string())
print(f"\nsetups where wide-stop is worse in both splits: {int(w.worse_both.sum())} of {len(w)}")
print("\nEducational only - not financial advice.")
