"""T1 combined (fit + check) stats from the saved books. Educational only - not financial advice."""
import json, sys
import pandas as pd
import run as Rn
B = Rn.B
res = json.loads((Rn.HERE / "results.json").read_text())
for v in sys.argv[1:]:
    bk = pd.concat([pd.read_parquet(Rn.WORK / f"bk_{v}_{p}.parquet") for p in ("fit", "check")], ignore_index=True)
    nf, spy = Rn.n_sessions("fit"); nc, _ = Rn.n_sessions("check")
    st = B.stats(bk, nf + nc, spy)
    res[f"{v}_t1comb"] = st
    print(v, {k: st[k] for k in ("trades", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r_per_session", "t_day_clustered")})
(Rn.HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
