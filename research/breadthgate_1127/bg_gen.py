"""BREADTHGATE-1127: bench10 lots for 7 arena / reference setups (the non-Primary rows of the TOP-10 benchmark + ST7).
Wraps research/ultimate_1119/top10/bench10.py unchanged except SETUPS (same pattern as research/squeeze_1125/gen.py).
cwd = repo checkout. Usage: python bg_gen.py WORK sig1|walk1|t2. Locked block never read (bench10 filters + asserts).
Educational only - not financial advice."""
import sys
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B
B.SETUPS = [("L3-gap-slope-lowdist-FD", "account_testing.yaml", "testing"),
            ("L3-gap-slope-rsi5hi-FD", "account_testing.yaml", "testing"),
            ("RW6-ns2-up3-short-FD", "account_livelab.yaml", "livelab"),
            ("NM-RWN4-ns2-spyup05-notfri-short", "account_testingf.yaml", "testingf"),
            ("CWT14-failbrk-orl-p10-long-WB5", "account_testingd.yaml", "testingd"),
            ("CWT09-gapdn-vwaploss-g10-short", "account_testing.yaml", "testing"),
            ("ST7-rsi50dn-long-pm-t1s1-FD", "default.yaml", "primary")]
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
