"""Random-entry controls for one (variant, part); writes a small json to WORK/rnd. Educational only - not financial advice."""
import json, sys
import numpy as np
import run as R
v, part, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
st0, _ = R.score(v, part, save=False)
o = {"setup_avg_r": st0["avg_r"]}
for kind in ("side", "names"):
    vals = []
    for s in range(n):
        rng = np.random.default_rng(1000 + s)
        st, _ = R.score(v, part, save=False, rand_side=rng if kind == "side" else None, rand_names=rng if kind == "names" else None)
        vals.append(st.get("avg_r", np.nan))
    vals = np.array(vals, float)
    o[kind] = {"mean": round(float(np.nanmean(vals)), 4), "p05": round(float(np.nanpercentile(vals, 5)), 4),
               "p95": round(float(np.nanpercentile(vals, 95)), 4),
               "setup_pctile": round(float((vals < st0["avg_r"]).mean() * 100), 1), "n": n}
(R.WORK / "rnd" / f"{v}_{part}.json").write_text(json.dumps(o))
print(v, part, o)
