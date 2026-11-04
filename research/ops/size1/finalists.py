"""SIZE1 finalists table (pre-registered list, PLAN.md) from results.csv. Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
H = Path(__file__).resolve().parent
r = pd.read_csv(H / "results.csv")
sel = {l.split(":")[0].split()[-1]: l for l in open(H / "selection.txt") if l.startswith("Book")}
out = []
for b in ("A", "B"):
    tr = r[(r.book == b) & (r.window == "TRAIN")]
    s1 = tr[tr.stage == 1]
    sel_name = sel[b].split("(ret/DD) ")[1].split(";")[0]
    fin = {"baseline": "0.25%/4x/FC", "TRAIN-selected": sel_name}
    for a in ("FC", "QS", "QX", "FAM"):
        x = s1[s1.config.str.endswith("/" + a)]; fin[f"best {a}"] = x.loc[x.rdd.idxmax(), "config"]
    for bp in (1, 2, 4):
        x = s1[s1.config.str.contains(f"/{bp}x/")]; fin[f"best {bp}x"] = x.loc[x.rdd.idxmax(), "config"]
    for c in tr[tr.stage == 2].config:
        fin[c] = c
    seen = set()
    for lab, c in fin.items():
        if c in seen:
            continue
        seen.add(c)
        row = {"book": b, "role": lab, "config": c}
        for w in ("TRAIN", "VALID", "LIVE"):
            m = r[(r.book == b) & (r.window == w) & (r.config == c)].iloc[0]
            for k in ("ret", "dd", "green", "avgR", "avgR_wob", "best_share", "trades", "t", "t_vs_base"):
                row[f"{w}_{k}"] = m[k]
        out.append(row)
f = pd.DataFrame(out)
f.to_csv(H / "finalists.csv", index=False, float_format="%.3f")
pd.set_option("display.width", 300)
for w in ("TRAIN", "VALID", "LIVE"):
    print(w); print(f[["book", "role", "config"] + [c for c in f.columns if c.startswith(w)]].rename(columns=lambda c: c.replace(w + "_", "")).round(2).to_string(index=False))
