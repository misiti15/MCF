"""bdi1023 rework E (PLAN.md addendum, declared after A-D were scored): skip entries whose stop is < X % of price
(the stop-% version of gb-1019-noise-floor-stop), per book. 9 configs; gates1021 cached signal tables, costs in; the
locked block is never read (no_locked in load_sig); no holdout scored.  Usage: python swarm_e.py > swarm_e_out.txt
Educational only - not financial advice."""
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
from mcf.research import gates as G  # noqa: E402

U = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv").set_index("setup")
BOOKS = {"primary": "primary", "testing1": "testing", "testing2": "testing2"}
N = 1302 + 9
BAR = round(math.sqrt(2 * math.log(N)), 2)

sig = load_sig(list(U.index))
sig["geom"] = sig["setup"].map(U["geom"]); sig["side"] = sig["setup"].map(U["side"])
sig["stop_pct"] = sig["geom"].map(lambda g: G.GEOMK[g][1]) * 0.25 * sig["atr_d"] / sig["close"] * 100
sig["ctrl"] = np.nan
for (s, g), ix in sig.groupby(["side", "geom"]).groups.items():
    sig.loc[ix, "ctrl"] = sig.loc[ix, f"c_{s}_{g}"]
sig = sig[np.isfinite(sig["stop_pct"]) & (sig["stop_pct"] > 0)]

rows, per = [], []
for book, acct in BOOKS.items():
    sts = [st for st in U.index if acct in U.loc[st, "accounts"].split(",")]
    s = sig[sig["setup"].isin(sts)].sort_values(["date", "tod", "setup", "symbol"]).reset_index(drop=True)
    sp = s["stop_pct"].to_numpy(float)
    for x in (0.4, 0.5, 0.6):
        blk = sp < x
        e = evaluate(s, blk, "ctrl")
        kept = 1 - blk.mean()
        ok = (e["train_gated_exp"] or -1) > 0 and (e["valid_gated_exp"] or -1) > 0 \
            and (e["train_delta"] or -1) > 0 and (e["valid_delta"] or -1) > 0 \
            and e["train_delta"] > e["train_ctrl_delta"] and e["valid_delta"] > e["valid_ctrl_delta"] \
            and (e["up_delta"] or -1) >= 0 and (e["down_delta"] or -1) >= 0 \
            and (e["all_delta_t"] or 0) >= BAR and kept >= 0.75
        rows.append(dict(book=book, cfg=f"E{x}", kept_pct=round(100 * kept, 1), passes=bool(ok), **e))
        for st, y in s.assign(b=blk).groupby("setup"):
            r = {"book": book, "cfg": f"E{x}", "setup": st}
            for spl in ("train", "valid"):
                z = y[y.split == spl]
                k = z[~z.b]
                r[f"{spl}_n"], r[f"{spl}_kept"] = len(z), len(k)
                r[f"{spl}_parent"] = round(float(z.r.mean()), 4) if len(z) else None
                r[f"{spl}_gated"] = round(float(k.r.mean()), 4) if len(k) else None
                r[f"{spl}_gated_t"] = G.summary(k[["date", "r"]]).get("t") if len(k) > 1 else None
            per.append(r)
R = pd.DataFrame(rows); P = pd.DataFrame(per)
R.to_csv(HERE / "results_e.csv", index=False); P.to_csv(HERE / "results_e_setups.csv", index=False)
c = json.loads((HERE / "counts.json").read_text())
c.update({"configs_E": len(R), "configs_total": c["configs"] + len(R), "gate_lineage_N_after_E": N, "bar_E": BAR,
          "passes_E": int(R.passes.sum())})
(HERE / "counts.json").write_text(json.dumps(c, indent=1))
pd.set_option("display.width", 260)
print(f"E configs {len(R)}, passes {int(R.passes.sum())}, bar {BAR} (gate lineage N {N})")
print(R[["book", "cfg", "kept_pct", "train_parent_exp", "train_gated_exp", "train_in_state_exp", "valid_parent_exp",
         "valid_gated_exp", "valid_in_state_exp", "train_delta", "valid_delta", "train_ctrl_delta", "valid_ctrl_delta",
         "up_delta", "down_delta", "all_delta_t", "train_winners_blocked_pct", "gated_ex_best_day", "passes"]].to_string(index=False))
P["better_both"] = (P.train_gated >= P.train_parent) & (P.valid_gated >= P.valid_parent)
P["pos_both"] = (P.train_gated > 0) & (P.valid_gated > 0)
P["par_pos_both"] = (P.train_parent > 0) & (P.valid_parent > 0)
print("\n== per setup: gated >= parent in both splits / positive in both (gated vs parent)")
print(P.groupby(["book", "cfg"])[["better_both", "pos_both", "par_pos_both"]].sum().to_string())
q = P[(P.pos_both) & (P.train_kept >= 30) & (P.valid_kept >= 20)].sort_values("valid_gated", ascending=False)
print("\n== setups positive in both splits after the gate (>=30/20 kept)")
print(q.to_string(index=False))
print("\nEducational only - not financial advice.")
