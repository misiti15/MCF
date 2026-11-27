"""R3B: run bench10 stages (unchanged code) for the top-10 setups that lack lab paths in earlier teams' work dirs.
Usage (cwd inbox): python run10.py WORK stage. Educational only - not financial advice."""
import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.path.insert(0, "research/ultimate_1119/top10")
import bench10 as B
WANT = {"CWT14-failbrk-orl-p10-long-WB5", "CWT09-gapdn-vwaploss-g10-short", "NM-RWN4-ns2-spyup05-notfri-short",
        "NM-ETF-late-dip-di-long"}
B.SETUPS = [s for s in B.SETUPS if s[0] in WANT]
W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True); stage = sys.argv[2]
if stage == "sig1":
    from multiprocessing import Pool
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
    with Pool(3) as p:
        for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
            print(r, flush=True)
elif stage == "walk1":
    B.walk1(W)
elif stage == "t2":
    B.t2(W)
