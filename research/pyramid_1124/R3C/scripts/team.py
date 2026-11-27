import json, numpy as np, pandas as pd, sys
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/R3C")
import rescore as RS
R = RS.reg()
out = {}
BK = ["L3-fromopen", "RW3-FD", "RW5-FD", "NM-ETF-late-dip"]
for m in ("res", "cal"):
    bk = {}
    for s in BK:
        _, b = RS.score_sets(R[s]["sets"], R[s]["rules"], R[s]["etb"]); bk[s] = b[m]
    for h in ("check", "T2"):
        book = pd.concat([bk[s][h] for s in BK]).groupby("date").r.sum().reindex(RS.SES[h], fill_value=0.0)
        w10 = book.nsmallest(10).index
        for c in ("L2:C4a", "G:NM-ETF+TT1", "L2:C1a", "L3:A3", "L3:A3t", "NM-RWN4", "CWT09-g10", "NM-ETF-late-dip", "S:GEN-261023-06", "G:B3+TT1"):
            _, b = RS.score_sets(R[c]["sets"], R[c]["rules"], R[c]["etb"])
            dr = b[m][h].groupby("date").r.sum().reindex(RS.SES[h], fill_value=0.0)
            out[f"{m}|{h}|{c}"] = dict(corr=round(float(np.corrcoef(dr, book)[0, 1]), 3), r_w10=round(float(dr.reindex(w10).sum()), 2),
                                       book_w10=round(float(book.reindex(w10).sum()), 1))
            print(m, h, c, out[f"{m}|{h}|{c}"], flush=True)
json.dump(out, open("team.json", "w"), indent=1)
