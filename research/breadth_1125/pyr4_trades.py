"""BREADTH-1125 Part B: bench10 trade paths (unchanged engine) for Primary's 4 setups + GEN-261027-01.
Usage (from the repo root): python research/breadth_1125/pyr4_trades.py WORK BW {sig1|walk1|t2}
BW = build_breadth.py output dir; its pct_vwap feeds the 'breadth' context column of the 2023-24 frames (the lab frames
already carry 'breadth' for 2024-10..2026-11). Locked block never read (bench10 guards). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

GEN01 = "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"
B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("NM-ETF-late-dip-di-long", "default.yaml", "primary"),
            (GEN01, "account_testinge.yaml", "testinge")]


def init_t2(bw):
    c = pd.read_parquet(B.FRESH / "ctx.parquet")
    c["date"] = c["date"].astype(str)
    br = pd.read_parquet(Path(bw) / "breadth.parquet")
    br = br[br.src == "T2"][["date", "T", "pct_vwap"]].rename(columns={"T": "tod", "pct_vwap": "breadth"})
    B.WCTX["ctx"] = c.merge(br, on=["date", "tod"], how="left")


if __name__ == "__main__":
    W, BW, stage = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
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
    elif stage == "t2":
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
        out, st = [], {}
        with Pool(3, initializer=init_t2, initargs=(BW,)) as p:
            for sym, s, o in p.imap_unordered(B.t2_job, syms):
                st[s] = st.get(s, 0) + 1
                if o is not None and len(o):
                    out.append(o)
        T = pd.concat(out, ignore_index=True)
        T.to_parquet(W / "trades_t2.parquet")
        print(len(T), "T2 signals", st, T.groupby("setup").size().to_dict())
