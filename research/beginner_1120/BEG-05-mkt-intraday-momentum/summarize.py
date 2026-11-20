"""T1 combined stats (fit + check booked trades) for a variant, appended to results.json. Educational only."""
import json, sys
import pandas as pd
import run as R
import bench10 as B
name = sys.argv[1]
bk = pd.concat([pd.read_parquet(R.WORK / f"bk_{name}_{p}.parquet") for p in ("fit", "check")], ignore_index=True)
spy = B.spy_t1(); spy = spy[spy.index <= R.T1_LAST]
n = int(pd.Series(B.half(spy.index)).isin(["fit", "check"]).sum())
st = B.stats(bk, n, spy)
res = json.loads((R.HERE / "results.json").read_text()); res[f"{name}_t1comb"] = st
(R.HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: st[k] for k in ("trades", "sessions", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r_per_session", "t_day_clustered")}))
