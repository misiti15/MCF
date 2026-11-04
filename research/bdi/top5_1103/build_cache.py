"""top5_1103: rebuild gates1021's live-shaped signal cache (scratch; /dev/shm tonight, disk full) for the 5 top-5 setups
and the 8 top-20 in-depth setups (research/bdi/top20) scored tonight.
Same code as research/bdi/gates1021/scripts/scan.py (month_job, peer_map, spy_prev), restricted setup list, and it does
not rewrite gates1021/setups_scored.csv. Locked block never loaded (gates1021 common/lib assert).
Educational only - not financial advice.

    G21SCR=/dev/shm/t5_1103/g python research/bdi/top5_1103/build_cache.py 2
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

TOP5 = ("exhaustion_short-FD", "RW3S-gapdn-flowsell-short-FD", "RW1-gapdn-bounce-flowsell-short-FD",
        "L3-gap-slope-lowdist-FD", "ST7-rsi50dn-long-pm-t1s1-FD")
TOP20 = ("MF2-open-rsimidhi-flowsell-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
         "L3-gap-slope-fromopen-FD", "NM-MF3-qqqdn-gapdn-FD", "L3-gap-slope-rsi5hi-FD",
         "NS4-pm-vwap-reclaim-oversold-short-FD", "NS5-sma50-flush-oversold-long")
TARGETS = TOP5 + TOP20


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
