"""shorts_autopsy: re-check of the settled RW3/RW5 1.25x target (outsider_1120 Y1, +0.044R, t 2.58) under LIVE-L costs on T1
(CHECK + FIT), bench10 walk_trades unchanged with target moved from 1.0R to 1.25R. Candidate level. Usage (cwd repo):
python rw_t125.py WORK. Educational only - not financial advice."""
import sys, json
from pathlib import Path
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "research/ultimate_1119/top10"); sys.path.insert(0, "research/primshorts_1126")
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
W = Path(sys.argv[1]); RW = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
def job(a):
    s, g = a
    if not (B.CACHE / f"{s}.parquet").exists(): return []
    b = B.hist_bars(s); return B.walk_trades(g, b)
if __name__ == "__main__":
    t = pd.read_parquet(W / "trades_t1.parquet"); t = t[t.setup.isin(RW)].copy(); t["date"] = t.date.astype(str)
    t = t[~((t.date >= "2024-11-01") & (t.date <= "2025-02-28"))]
    base = t.copy()
    t["tgt"] = t.entry + t.side * 1.25 * t.risk
    t = t.drop(columns=["px", "kind", "xt"])
    with Pool(3) as p:
        res = [r for rr in p.imap_unordered(job, list(t.groupby("symbol")), chunksize=8) for r in rr]
    a = pd.DataFrame(res, columns=["i", "px", "kind", "xt"]).set_index("i"); t = t.join(a)
    etb = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/S/etb_rate.parquet").rate
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    out = {}
    for lab, z in (("t1.00", base), ("t1.25", t)):
        z = B.add_r(z); z = z[(z.entry >= 5) & z.symbol.map(etb).fillna(0).ge(0.9)].copy()
        kd = np.where(z.kind == 2, "target", np.where(z.kind == 1, "stop", "market"))
        z["r"] = z.r_gross - CL.predict_R(cells, z.entry.to_numpy(), z.risk.to_numpy(), kd)
        z["per"] = np.where(z.date >= "2025-10-01", "CHECK", np.where((z.date >= "2025-03-01") | (z.date.str[:7] == "2024-10"), "FIT", "none"))
        out[lab] = z.set_index(["setup", "symbol", "date", "tod"])[["r", "per"]]
    m = out["t1.00"].join(out["t1.25"].r.rename("r125"), how="inner").reset_index()
    m["d"] = m.r125 - m.r; m["wk"] = pd.to_datetime(m.date).dt.to_period("W")
    for per in ("CHECK", "FIT"):
        for s in RW + ["both"]:
            z = m[(m.per == per) & ((m.setup == s) | (s == "both"))]
            dd = z.groupby("date").d.mean(); tt = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
            wk = z.groupby("wk").d.sum(); best = z.groupby("date").d.sum()
            print(f"{per} {s[:3] if s!='both' else 'both'}: n {len(z)} avgR 1.00 {z.r.mean():+.3f} -> 1.25 {z.r125.mean():+.3f}  d {z.d.mean():+.4f} (day t {tt:.2f}); "
                  f"weeks up {(wk > 0).sum()}/{len(wk)}; best-day share {best.max()/best.sum() if best.sum()>0 else float('nan'):.2f}")
