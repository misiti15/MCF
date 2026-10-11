"""Markdown tables for NOTES section 2 -> tables.md. Educational only - not financial advice."""
import numpy as np
import pandas as pd
from common import HERE

R = pd.read_csv(HERE / "gate_results.csv")
out = []
b = R[R.cond == "BASE"].set_index("list")
c = R[R.cond.str[:1].isin(["F", "N", "Z"])].copy()
c["delta"] = c["exp"] - c["base_exp"]
out.append("| list | base n | base exp R (t) | up / down | WF | best condition (n >= 150, by exp) | n kept | exp after (t) | up / down | WF | train / valid delta | passes bar |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for nm in b.index:
    x = b.loc[nm]
    cc = c[(c.list == nm) & (c.n >= 150)].sort_values("exp", ascending=False)
    if len(cc):
        y = cc.iloc[0]
        best = (f"{y.cond} | {int(y.n)} | {y.exp:+.3f} ({y.t}) | {y.up:+.3f} / {y.down:+.3f} | {y.wf} | "
                f"{y.train - y.base_train:+.3f} / {y.valid - y.base_valid:+.3f} | {'yes' if y.passes_bar else 'no'}")
    else:
        best = "- | - | - | - | - | - | no"
    out.append(f"| {nm} | {int(x.n)} | {x.exp:+.3f} ({x.t}) | {x.up:+.3f} / {x.down:+.3f} | {x.wf} | {best} |")
out.append("")
P = pd.read_csv(HERE / "gate_pooled.csv")
out.append("| condition | side | kept n | kept exp | blocked n | blocked exp | diff (t) | lists improved train / valid / both (of 48) |")
out.append("|---|---|---|---|---|---|---|---|")
for _, r in P.iterrows():
    out.append(f"| {r.cond} | {r.side} | {r.kept_n} | {r.kept_exp:+.4f} | {r.blocked_n} | {r.blocked_exp:+.4f} | {r['diff']:+.4f} ({r.diff_t}) | "
               f"{r.lists_improved_train} / {r.lists_improved_valid} / {r.lists_improved_both} |")
z = c[c.cond.str.startswith("Z")].groupby("cond")["delta"].agg(["mean", lambda s: int((s > 0).sum())])
out.append("")
out.append(z.to_string())
(HERE / "data" / "tables.md").write_text("\n".join(out))
print("\n".join(out))
