"""LPB loosening grid, bench10 'normal way' (LR8 costs, 1-min exits, testing book). Educational only."""
import itertools, json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, "/home/user/MCF")
import bench10 as B
from mcf.research.arena.indicators import compute
W = Path(sys.argv[1]); W.mkdir(exist_ok=True)
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + [f"2026-{m:02d}" for m in range(1, 12)]
assert not set(MONTHS) & B.LOCKED_MONTHS
COLS = ["symbol", "date", "tod", "close", "high", "low", "fromOpen", "gap", "atr_d", "vwapDistPct", "macdPct",
        "dist_hod_atr", "dist_lod_atr", "emaDiff", "momentum", "adv20"]
# grid (pre-registered): window start x macd_hist x ret3_atr x ADV floor; breadth > 0.5 and window end 15:00 fixed
WLO = [1400, 1330]; MH = [0.12, 0.08, 0.04]; RA = [-0.069, -0.04, -0.02]; ADV = [20e6, 10e6, 5e6]
GRID = list(itertools.product(WLO, MH, RA, ADV))
f32 = lambda v: float(np.float32(v))

def cand_job(m):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    f = lib.load_month(m, columns=COLS, context=True)
    f["symbol"] = f["symbol"].astype(str); f["date"] = f["date"].astype(str)
    B.no_locked(f.date.unique())
    x = compute(f, names=["macd_hist", "ret3_atr"], context=False)
    f["mh"] = x["macd_hist"].to_numpy(np.float32).astype(float)
    f["ra"] = x["ret3_atr"].to_numpy(np.float32).astype(float)
    tod = f.tod.to_numpy()
    with np.errstate(invalid="ignore"):
        ok = ((tod >= min(WLO)) & (tod <= 1500) & (f.breadth.to_numpy(float) > 0.5) & (f.mh >= f32(min(MH)))
              & (f.ra <= f32(max(RA))) & (f.adv20.fillna(0) >= min(ADV)) & (f.atr_d > 0))
    c = f.loc[ok, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "breadth", "mh", "ra"]].copy()
    c["entry"] = c.close; R = 0.25 * c.atr_d
    c["stop"] = c.entry - R; c["tgt"] = c.entry + 0.5 * R; c["risk"] = R; c["side"] = 1
    c = c.drop(columns=["close"]).reset_index(drop=True)
    c.to_parquet(W / f"cand_{m}.parquet")
    return m, len(c), f.date.nunique()

def walk_job(a):
    sym, T = a
    return B.walk_trades(T, B.hist_bars(sym))

if __name__ == "__main__":
    st = sys.argv[2]
    if st == "cand":
        ms = [m for m in MONTHS if not (W / f"cand_{m}.parquet").exists()]
        with Pool(2) as p:
            for r in p.imap_unordered(cand_job, ms): print(r, flush=True)
    elif st == "walk":
        C = pd.concat([pd.read_parquet(W / f"cand_{m}.parquet") for m in MONTHS], ignore_index=True)
        B.no_locked(C.date.unique())
        jobs = [(s, g) for s, g in C.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
        with Pool(3) as p:
            out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
        a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
        C = C.join(a); C.to_parquet(W / "cand_walked.parquet")
        print(len(C), "cands;", int((C.kind.isna() | (C.kind < 0)).sum()), "no 1-min path")
