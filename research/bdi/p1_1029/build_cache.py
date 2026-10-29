"""p1_1029: rebuild gates1021's live-shaped signal cache (scratch) for the setups this study scores (live long book,
the three Primary short families, and the fade / momentum books for the vol switch). Same code path as
research/bdi/top5_1028/build_cache.py (gates1021 scan.month_job: live module mask, window, ADV, refire chain,
production R with the extended tier x3, same-minute random control). Locked block never loaded (gates1021 common/lib
assert; lib.months() is open months only). Educational only - not financial advice.

    G21SCR=$SCRATCH/p1/g python research/bdi/p1_1029/build_cache.py 2
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

TARGETS = (
    # Primary
    "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell", "MF4-h40-open-flowsell-FD", "NS1-rsidip-rsi5pop-long",
    "NS5-sma50-flush-oversold-long", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
    "ST7-rsi50dn-long-pm-t1s1-FD",
    # Testing 1 / 2 covered
    "L3-gap-slope-fromopen-FD", "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD", "MF3-open-flowsell-rsi5hi-FD",
    "NS1-rsidip-rsi5pop-long-FD", "NS3-failed-vwap-reclaim-short-FD", "NS5-sma50-flush-oversold-long-FD",
    "RW4-ns3-adv150-short-FD", "RW7-gapdn-bounce-early-short-FD", "RW1-gapdn-bounce-flowsell-short-FD",
    "ST4-emadn-long-am-t1s05-FD", "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD", "ST8-volspikedn-long-pm-t1s1-FD",
    "exhaustion_short-FD", "LD1-ns1-breadthup-t05s1-long", "LD3-st2-idxturn-t05s1-long", "LD4-st4-breadthup-t1s05-long",
    "LD5-st2-breadthup-t05s1-long", "NM-AR-AM-gapdown-capitulation-long", "NM-HL-T75-pm-long",
)


def main():
    (SCR / "sig").mkdir(exist_ok=True)
    (SCR / "ctrl").mkdir(exist_ok=True)
    us = scan.unique_setups()
    keep, seen = [], set()
    for r in us.to_dict("records"):
        hit = [t for t in TARGETS if t in r["names"].split(",") and t not in seen]
        if hit:
            r["setup"] = hit[0]
            seen.add(hit[0])
            keep.append(r)
    missing = sorted(set(TARGETS) - seen)
    print("missing (not covered / deduped):", missing)
    for r in keep:
        print({k: r[k] for k in ("setup", "names", "window", "min_adv", "refire", "cooldown", "geom", "side")})
    json.dump([{k: (list(v) if isinstance(v, tuple) else v) for k, v in r.items()} for r in keep],
              open(SCR / "setups.json", "w"), default=str)
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
