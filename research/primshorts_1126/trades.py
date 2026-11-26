"""PRIMSHORTS-1126: bench10 trade paths (unchanged engine, research/ultimate_1119/top10/bench10.py) for Primary's 3 shorts
and the 2 PSHADOW shorts, each with its live config block (home account). Re-score only (cost fix) - no new configs.
Usage (repo root): python research/primshorts_1126/trades.py WORK {sig1|walk1|t2} [nmetf]
(nmetf = NM-ETF-late-dip-di-long only, Primary's long leg, needed for the book replay; unchanged config)
Locked block 2024-11-01..2025-02-28 never read (bench10 guards). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("L3-gap-slope-rsi5hi-FD", "account_testing.yaml", "testing"),
            ("RW6-ns2-up3-short-FD", "account_livelab.yaml", "livelab")]
if len(sys.argv) > 3 and sys.argv[3] == "nmetf":
    B.SETUPS = [("NM-ETF-late-dip-di-long", "default.yaml", "primary")]

if __name__ == "__main__":
    W, stage = Path(sys.argv[1]), sys.argv[2]
    W.mkdir(parents=True, exist_ok=True)
    if stage == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(2) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif stage == "walk1":
        B.walk1(W)
    elif stage == "t2" and len(sys.argv) > 3 and sys.argv[3] == "nmetf":
        # NM-ETF trades only its module's ETF list: build T2 frames for those symbols only (same t2_job)
        import json
        import pandas as pd
        m = B.load_mod("nmetf", "research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py")
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet") if p.stem in m.SYMBOLS)
        out, st = [], {}
        with Pool(2) as p:
            for sym, s_, o in p.imap_unordered(B.t2_job, syms):
                st[s_] = st.get(s_, 0) + 1
                if o is not None and len(o):
                    out.append(o)
        pd.concat(out, ignore_index=True).to_parquet(W / "trades_t2.parquet")
        json.dump({"symbols": len(syms), "status": st}, open(W / "t2_status.json", "w"))
        print(sum(len(o) for o in out), "T2 signals", st)
    elif stage == "t2":
        B.t2(W)
