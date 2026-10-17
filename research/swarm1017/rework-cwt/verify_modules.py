"""Module parity: modules/*.py mask on the live-like frame (build.month_frame) -> first hit in the window per symbol-day
vs the scan's trades (verify.trades) on 4 open months. Educational only - not financial advice."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402

MODS = {"NM1-cwt09-g10-vwaploss-fodn-slopeup-short": ((1030, 1500), 1e6, ("A7", "g10-T1", "short", "t1s1", "fo<0", "slope>0")),
        "NM2-cwt05-flush-m125-v3-continuation-short": ((1130, 1300), 95e6, ("B5", "m1.25-v3", "short", "so05", "", ""))}
scr = sys.argv[1]
sys.argv = [sys.argv[0], scr]
_sp = importlib.util.spec_from_file_location("rcverify", HERE / "verify.py")
VF = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(VF)  # (re-runs the verify pass once; cheap)

out = {}
for name, (w, adv, (fam, vid, side, ex, f1, f2)) in MODS.items():
    spec = importlib.util.spec_from_file_location(name, HERE / "modules" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    row = pd.Series({"fam": fam, "vid": vid, "side": side, "exit": ex, "win": f"{w[0]}-{w[1]}", "pick": "first", "f1": f1, "f2": f2})
    ref = VF.trades(row)
    got = []
    for m in ("2025-04", "2025-10", "2026-03", "2026-07"):
        f, P, _ = B.month_frame(m)
        P = P.merge(f[["symbol", "date", "tod", "sma20_slope_pct", "adv20"]], on=["symbol", "date", "tod"], how="left")
        P["adv20"] = P.groupby(["symbol", "date"])["adv20"].transform("max")
        P = P[P.adv20 >= adv].reset_index(drop=True)
        msk = np.asarray(mod.mask(P), bool) & (P.tod.to_numpy() >= w[0]) & (P.tod.to_numpy() <= w[1])
        h = P.loc[msk, ["symbol", "date", "tod"]].drop_duplicates(["symbol", "date"], keep="first")
        got.append(h)
    g = pd.concat(got)
    ms = {str(pd.Timestamp(m + "-01"))[:7] for m in ("2025-04", "2025-10", "2026-03", "2026-07")}
    rr = ref[pd.to_datetime(ref["date"]).dt.strftime("%Y-%m").isin(ms)]
    a = set(zip(g.symbol, g.date.astype(str), g.tod.astype(int)))
    b = set(zip(rr.symbol, rr.date.astype(str), rr.tod.astype(int)))
    out[name] = {"module_hits": len(a), "scan_trades": len(b), "both": len(a & b), "only_module": len(a - b), "only_scan": len(b - a),
                 "note": "module hits include earnings-blackout days (the live runner blocks them); scan trades exclude them"}
    print(name, out[name], flush=True)
json.dump(out, open(HERE / "verify_modules.json", "w"), indent=1)
