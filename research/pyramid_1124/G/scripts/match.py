import sys, numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import bench10 as B
T = pd.read_parquet("p2_live_trades.parquet")
l3 = B.add_r(pd.read_parquet("../L3/work/trades_t1.parquet")); l3["date"] = l3.date.astype(str)
l1 = B.add_r(pd.read_parquet("../L1/trades_check.parquet")); l1["date"] = l1.date.astype(str); l1["ctrl"] = 0
l3 = pd.concat([l3[l3.cfg == "A1"], l1[l1.cfg == "L3-gap-slope-fromopen-FD"]])
for fam, cfg in (("L3-fromopen", "L3-gap-slope-fromopen-FD"), ("GEN-261027-01", "A1")):
    e = l3[(l3.cfg == cfg) & ((l3.ctrl == 0) if cfg == "A1" else True)]
    lv = T[(T.fam == fam) & (T.date <= "2026-11-04") & T.bar_time.notna()].copy()
    lv["dec"] = ((lv.bar_time // 100) * 60 + lv.bar_time % 100 + 1).astype(int)
    lv["dec"] = (lv.dec // 60) * 100 + lv.dec % 60
    m = lv.merge(e[["symbol", "date", "tod", "entry", "stop", "risk", "r", "r_gross", "kind", "xt"]], on=["symbol", "date"], suffixes=("", "_e"))
    if not len(m): continue
    m["dt"] = ((m.tod // 100) * 60 + m.tod % 100) - ((m.dec // 100) * 60 + m.dec % 100)
    m["adt"] = m.dt.abs()
    best = m.sort_values("adt").drop_duplicates("k")
    print("==", fam, "live trades in window", len(lv), "with engine signal same symbol-day", best.k.nunique())
    print(" |dt| minutes dist:", best.adt.describe()[["50%", "mean"]].round(1).to_dict(), "exact same bar:", (best.adt == 0).mean().round(3))
    best["px_diff_R"] = (best.ref_price - best.entry_e) / best.risk
    best["risk_ratio"] = (best.ref_price - best.stop).abs() / best.risk
    for lab, x in (("same bar", best[best.adt == 0]), ("diff bar", best[best.adt > 0]), ("all", best)):
        print(f" {lab}: n {len(x)} live R {x.r.mean():.3f}  live-replay {x.fill_eng_net.mean():.3f}  engine R {x.r_e.mean():.3f}  "
              f"ref-vs-engine-entry (R) med {x.px_diff_R.median():.3f}  risk ratio live/engine med {x.risk_ratio.median():.3f}")
    # same bar: why different outcomes
    sb = best[best.adt == 0]
    if len(sb):
        print(sb[["symbol", "date", "dec", "tod", "ref_price", "entry_e", "stop", "stop_e", "target", "r", "fill_eng_net", "r_e", "xt", "exit_reason"]].head(25).to_string())
    # engine signals per live symbol-day, their tod vs live
    print(" engine signals per live symday:", m.groupby("k").size().describe()[["50%", "mean"]].to_dict())
    
