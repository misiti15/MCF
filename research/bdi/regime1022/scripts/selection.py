"""regime1022 Part C (iii): the selection rule applied to every live setup (covered or not) -> selection.csv and a
markdown table for NOTES.md. Educational only - not financial advice."""
from __future__ import annotations

import json

import pandas as pd
import yaml

from rc import HERE, ROOT

CRIT = ["S1", "S2", "S3", "S4", "S5", "S6"]


def main():
    names = yaml.safe_load((ROOT / "config" / "setup_names.yaml").read_text())
    used = pd.read_csv(HERE / "setups_used.csv")
    C = pd.read_csv(HERE / "classes.csv")
    G = pd.read_csv(HERE / "gates_c.csv")
    G = G[~G["reference_only"]]
    G["n_ok"] = G[CRIT].sum(axis=1)
    lv = pd.read_csv(HERE / "live_by_regime.csv")
    acc_lbl = {"primary": "P", "testing": "T1", "testing2": "T2", "graveyard": "GY"}
    rows = []
    for setup, g in used.groupby("setup", sort=False):
        accts = "+".join(acc_lbl[a] for a in g["account"])
        disp = (names.get(setup) or {}).get("name", setup)
        c = C[C["names"].str.split(",").apply(lambda x: setup in x)]
        live = lv[lv["strategy"] == setup]
        live_s = "; ".join(f"{r.regime} {int(r.trades)} / {r.avg_r:+.2f}" for r in live.itertuples())
        if c.empty:
            rows.append({"setup": setup, "name": disp, "accounts": accts, "class": "not scored",
                         "why": g["why_not"].iloc[0], "live_by_regime": live_s, "verdict": "not scored (no frame outcome)"})
            continue
        c = c.iloc[0]
        gg = G[G["skey"] == c["skey"]].sort_values(["n_ok", "all_delta_t"], ascending=False).iloc[0]
        br = json.loads(c["by_regime"])
        fails = [k for k in CRIT if not gg[k]]
        if gg["pass"]:
            verdict = f"gate {gg['gate']} qualifies"
        elif c["class"] == "all-weather":
            verdict = "keep as-is; never gate (all-weather)"
        elif c["train_avg_r"] > 0 and c["valid_avg_r"] > 0:
            verdict = "keep as-is; profitable in both periods, no gate"
        elif c["train_avg_r"] < 0 and c["valid_avg_r"] < 0:
            verdict = "no gate qualifies; loses net on 2 years in both periods"
        else:
            verdict = "no gate qualifies; mixed (one period positive)"
        rows.append({"setup": setup, "name": disp, "accounts": accts, "class": c["class"], "best": c["best"],
                     "worst": c["worst"], "n": int(c["n"]), "avg_r": round(c["avg_r"], 3),
                     "train_avg_r": round(c["train_avg_r"], 3), "valid_avg_r": round(c["valid_avg_r"], 3),
                     **{f"{k}_avg_r": (round(v["avg_r"], 3) if v["avg_r"] is not None else None) for k, v in br.items()},
                     "S1_split_real": bool(c["S1"]), "best_gate": gg["gate"], "best_gate_t": gg["all_delta_t"],
                     "best_gate_fails": ",".join(fails), "live_by_regime": live_s, "verdict": verdict})
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "selection.csv", index=False)
    md = ["| setup (id) | acct | class | best / worst | 2-yr avg R (train / valid) | Bull / Bear / Choppy / Quiet avg R | best gate (t; fails) | verdict |",
          "|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        if r._4 == "not scored":
            md.append(f"| {r.name} ({r.setup}) | {r.accounts} | not scored | – | – | – | – | {r.why} |")
            continue
        md.append(f"| {r.name} ({r.setup}) | {r.accounts} | {r._4} | {r.best} / {r.worst} | {r.avg_r:+.3f} "
                  f"({r.train_avg_r:+.3f} / {r.valid_avg_r:+.3f}) | {r.Bull_avg_r:+.3f} / {r.Bear_avg_r:+.3f} / "
                  f"{r.Choppy_avg_r:+.3f} / {r.Quiet_avg_r:+.3f} | {r.best_gate} ({r.best_gate_t:.2f}; "
                  f"{r.best_gate_fails or 'none'}) | {r.verdict} |")
    (HERE / "selection_table.md").write_text("\n".join(md) + "\n")
    print(df["verdict"].value_counts())
    print(df["class"].value_counts())


if __name__ == "__main__":
    main()
