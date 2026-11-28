"""shorts_autopsy: bench10 candidate lots for the 7 short setups in bench10's list (Primary trio + RW6, NM-RWN4, CWT09,
L3-lowdist, L3-rsi5hi). Wraps bench10 unchanged except SETUPS (same pattern as research/squeeze_1125/gen.py).
cwd = repo checkout. Usage: python gen_shorts.py WORK sig1|walk1|t2. Locked block never read (bench10 asserts).
Educational only - not financial advice."""
import sys
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B
B.SETUPS = [s for s in B.SETUPS if s[0] in (
    "L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
    "RW6-ns2-up3-short-FD", "NM-RWN4-ns2-spyup05-notfri-short", "CWT09-gapdn-vwaploss-g10-short",
    "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD")]
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
