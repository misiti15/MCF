"""top5_1026: rebuild gates1021's live-shaped signal cache (scratch) for only the 4 short setups scored tonight.
Same code as research/bdi/gates1021/scripts/scan.py (month_job, peer_map, spy_prev), restricted setup list, and it does
not rewrite gates1021/setups_scored.csv. Locked block never loaded (gates1021 common/lib assert).
Educational only - not financial advice.

    G21SCR=$SCRATCH/g1026 python research/bdi/top5_1026/build_cache.py 3
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gates1021" / "scripts"))
import scan  # noqa: E402
from common import SCR, lib  # noqa: E402

TARGETS = ("NS3-failed-vwap-reclaim-short-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD",
           "L3-gap-slope-rsi5hi-FD")


def main():
    (SCR / "sig").mkdir(exist_ok=True)
    (SCR / "ctrl").mkdir(exist_ok=True)
    us = scan.unique_setups()
    keep = []
    for r in us.to_dict("records"):
        hit = [t for t in TARGETS if t in r["names"].split(",")]
        if hit:
            r["setup"] = hit[0]
            keep.append(r)
    assert sorted(r["setup"] for r in keep) == sorted(TARGETS), [r["setup"] for r in keep]
    for r in keep:
        print({k: r[k] for k in ("setup", "names", "window", "min_adv", "refire", "cooldown", "geom", "side")})
    d = lib.daily()
    spy = d[d["symbol"] == "SPY"].sort_values("date")
    dd = pd.to_datetime(spy["date"])
    prev = spy["close"].pct_change() * 100
    prev[(dd.diff().dt.days > 5).to_numpy()] = np.nan
    pd.DataFrame({"date": spy["date"].to_numpy(), "spy_prev": prev.to_numpy()}).to_parquet(SCR / "spy_prev.parquet")
    pm = scan.peer_map()
    json.dump(pm, open(SCR / "peers.json", "w"))
    months = lib.months()
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as p:
        for r in p.imap_unordered(scan.month_job, [(m, keep, pm) for m in months]):
            print(r, flush=True)


if __name__ == "__main__":
    main()
