"""squeeze_1125: bench10 lots for the 4 Primary setups (P4). Wraps bench10 unchanged
except SETUPS. cwd = repo checkout. Usage: python gen.py WORK sig1|walk1|t2. Educational only - not financial advice."""
import sys
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B
B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("NM-ETF-late-dip-di-long", "default.yaml", "primary")]
if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(3) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif st == "walk1":
        B.walk1(W)
    elif st == "t2":
        B.t2(W)
    elif st == "inv":
        for x in B.inventory(): print(x)
