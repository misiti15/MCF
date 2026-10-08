"""AUDIT: why the lab frame has ~3x more heat_fade_long / gapdn entries than the production code path.
Educational only - not financial advice."""
import pickle
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "research/oct7/innovation"); sys.path.insert(0, "research/heat/candidates")
import bdlib as B, regime_5  # noqa: E402
C = pickle.load(open("research/oct7/audit/data/C.pkl", "rb"))
df = B.load("train")
for nm, m, w in (("hfl_base", regime_5.score(df) >= regime_5.LONG_AT, (1105, 1330)),
                 ("gapdn", (df.gap.to_numpy() <= -0.88) & (df.fromOpen.to_numpy() > 0), (1300, 1430))):
    tod = df.tod.to_numpy()
    idx = B._first_idx(df, np.asarray(m) & (tod >= w[0]) & (tod <= w[1]) & np.isfinite(df[f"r_{'long' if nm=='hfl_base' else 'short'}_t1s1"].to_numpy()))
    lab = pd.DataFrame({"symbol": df.symbol.astype(str).to_numpy()[idx], "date": df.date.astype(str).to_numpy()[idx], "tod": tod[idx],
                        "gap": df.gap.to_numpy()[idx]})
    P = C[(C.setup == nm) & (C.split == "train")]
    ks = set(P.symbol + "|" + P.date)
    lab["in_prod"] = (lab.symbol + "|" + lab.date).isin(ks)
    syms_prod = set(C.symbol)
    print(nm, "lab n", len(lab), "prod n", len(P), "lab in prod", lab.in_prod.sum(), "lab symbols", lab.symbol.nunique(),
          "lab symbols never in any prod setup", len(set(lab.symbol) - syms_prod), "cache symbols in lab frame", df.symbol.nunique())
    notp = lab[~lab.in_prod]
    print("  lab-only by gap sign", (notp.gap > 0).mean().round(2), " lab-only tod top", notp.tod.value_counts().head(3).to_dict())
    print("  prod not in lab", len(ks - set(lab.symbol + "|" + lab.date)))
