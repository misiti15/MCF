"""symbol-day overlap of finalists vs orb20_a (rebuilt as begdup/ovl.py), BEG-ORB stopOR (beg01w), gap-down trio and the
live top-10 books (top10w), T1 fit+check; plus Primary-proxy fit. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
W = S / "fp/open-drive"
src = open(S / "begdup/ovl.py").read().split("others = {")[0]
exec(src)          # defines orb20a (+ orb, gng, gcont) on T1 rows
others = {"orb20_a": orb20a, "orb20_a-WB3": orb20wb3, "gap_and_go(off)": gng}
live = pd.read_parquet(S / "top10w/booked_trades.parquet"); live = live[(live.test == "T1") & (live.half != "none")]
for s, g in live.groupby("setup"):
    others[s] = g
others["BEG-ORB-stopOR"] = pd.concat([pd.read_parquet(S / f"beg01w/booked_t1_stopOR_{h}.parquet") for h in ("fit", "check")])
def keys(df, side=False):
    return set(zip(df.symbol.astype(str), df.date.astype(str), df.side.astype(int))) if side else set(zip(df.symbol.astype(str), df.date.astype(str)))
res = {}
for c in sys.argv[1].split(","):
    B = pd.read_parquet(W / f"bk_{c}.parquet")
    kb, kbs = keys(B), keys(B, True)
    rows = {}
    for o, O in others.items():
        ko, kos = keys(O), keys(O, True)
        rows[o] = {"share_of_cand": round(len(kb & ko) / len(kb), 3), "same_side": round(len(kbs & kos) / len(kbs), 3),
                   "share_of_other": round(len(kb & ko) / max(1, len(ko)), 3)}
    res[c] = dict(sorted(rows.items(), key=lambda x: -x[1]["share_of_cand"])[:8])
    # Primary proxy = current Primary lineup's home-book backtest (top10w): L3-fromopen, RW3-FD, RW5-FD, NM-ETF, ST7-FD
    prim = live[live.setup.isin(["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
                                 "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long", "ST7-rsi50dn-long-pm-t1s1-FD"])]
    pdr = prim.groupby("date").r.sum()
    cdr = B.groupby("date").r.sum()
    days = sorted(set(pdr.index) | set(cdr.index))
    pdr, cdr = pdr.reindex(days).fillna(0), cdr.reindex(days).fillna(0)
    red = pdr < 0
    res[c]["_primary_fit"] = {"corr_daily": round(float(np.corrcoef(pdr, cdr)[0, 1]), 3),
                              "prim_red_days": int(red.sum()), "cand_R_on_prim_red_days_avg": round(float(cdr[red].mean()), 3),
                              "cand_R_on_prim_green_days_avg": round(float(cdr[~red].mean()), 3),
                              "prim_red_days_turned_green_by_cand_pct": round(float(((pdr + cdr)[red] > 0).mean()), 3),
                              "combined_green_pct": round(float((pdr + cdr > 0).mean()), 3), "prim_green_pct": round(float((pdr > 0).mean()), 3)}
json.dump(res, open(W / "overlap.json", "w"), indent=1)
print(json.dumps(res, indent=1))
