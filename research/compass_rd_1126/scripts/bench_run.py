"""COMPASS-RD-1126: bench10 trade paths (unchanged engine) for 8 condition-dependent setups. Stages sig1|walk1|t2|inv.
Locked block never read (bench10 guards). Educational only - not financial advice."""
import sys, yaml
from multiprocessing import Pool
from pathlib import Path
import pandas as pd
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa
WANT = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
        "NM-ETF-late-dip-di-long", "RW7-gapdn-bounce-early-short-FD", "CWT09-gapdn-bounce-g5-lowerhalf-short", "MF3-open-flowsell-rsi5hi-FD",
        "CWT14-failbrk-pdh-p10-short"]
FILES = ["default.yaml", "account_testing.yaml", "account_testinge.yaml", "account_testingd.yaml", "account_livelab.yaml", "account_testing2.yaml", "account_graveyard.yaml", "account_testingf.yaml"]
S = []
for w in WANT:
    for f in FILES:
        st = (yaml.safe_load((ROOT / "config" / f).read_text()).get("strategies") or {}).get(w)
        if st and st.get("module"):
            S.append((w, f, "primary" if f == "default.yaml" else "testing")); break
    else:
        print("no module block", w)
B.SETUPS = S
if __name__ == "__main__":
    W, stage = Path(sys.argv[2]), sys.argv[3]
    W.mkdir(parents=True, exist_ok=True)
    if stage == "inv":
        for x in B.inventory(): print(x)
    elif stage == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(1) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif stage == "walk1":
        B.walk1(W)
    elif stage == "t2":
        import json
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
        out, st = [], {}
        with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 2, maxtasksperchild=40) as p:
            for sym, s_, o in p.imap_unordered(B.t2_job, syms):
                st[s_] = st.get(s_, 0) + 1
                if o is not None and len(o):
                    out.append(o)
        T = pd.concat(out, ignore_index=True)
        T.to_parquet(W / "trades_t2.parquet")
        json.dump({"symbols": len(syms), "status": st}, open(W / "t2_status.json", "w"))
        print(len(T), "T2 signals", st, T.groupby("setup").size().to_dict())
