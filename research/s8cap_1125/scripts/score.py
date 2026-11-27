"""S8-CAP scoring (PLAN.md metrics + pass bar). Educational only - not financial advice."""
import math
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(__file__).resolve().parent / "work"
SH = {4: ["L3-fromopen", "RW3", "RW5", "NM-ETF"], 9: ["L3-fromopen", "RW3", "RW5", "NM-ETF", "L3-lowdist", "L3-rsi5hi", "RW7", "RW6", "GEN-29-06"]}
CANDS = ["C6L", "C6N", "C8L", "C8N", "C10L", "C10N", "CSL", "CSN"]
OTHERS = ["K4N", "NOW"]


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if d >= "2025-10-01":
        return "CHECK"
    return "T2"


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if x.std() > 0 else float("nan")


rows, srows = [], []
for line in ("P4", "P9"):
    N = 4 if line == "P4" else 9
    for book in ("RAW", "NEUTRAL", "P10"):
        def ld(c):
            x = pd.read_parquet(W / f"day_{line}_{book}_{c}.parquet")
            x = x[x.scored].set_index("date")
            x["tot"] = x[[f"R{s}" for s in range(N)]].sum(1)
            x["lots"] = x[[f"N{s}" for s in range(N)]].sum(1)
            return x
        R = ld("REF")
        per = R.index.map(period)
        for c in CANDS + OTHERS:
            X = ld(c)
            d = X.tot - R.tot
            for p in ("FIT", "T2", "CHECK", "ALL"):
                m = (per == p) if p != "ALL" else np.ones(len(R), bool)
                n = int(m.sum())
                fires = sum(int((X[f"M{s}"][m] >= 0).sum()) for s in range(N))
                sv = lr = rp = 0.0; nb = nr = npos = 0
                for s in range(N):
                    f = (X[f"M{s}"] >= 0) & m
                    ds = X[f"R{s}"] - R[f"R{s}"]
                    bad = f & (R[f"R{s}"] <= -X[f"L{s}"] + 1e-9)
                    rec = f & ~bad
                    sv += ds[bad].sum(); lr += ds[rec].sum(); nb += int(bad.sum()); nr += int(rec.sum())
                    npos += int((rec & (R[f"R{s}"] > 0)).sum())
                rows.append(dict(line=line, book=book, cfg=c, period=p, n=n, dR=round(d[m].sum(), 1), dR_yr=round(d[m].sum() / n * 252, 1),
                                 t=round(tstat(d[m]), 2), R_ref=round(R.tot[m].sum(), 1), R=round(X.tot[m].sum(), 1),
                                 worst_ref=round(R.tot[m].min(), 1), worst=round(X.tot[m].min(), 1),
                                 w5_ref=round(R.tot[m].nsmallest(5).mean(), 1), w5=round(X.tot[m].nsmallest(5).mean(), 1),
                                 le6_ref=int((R.tot[m] <= -6).sum()), le6=int((X.tot[m] <= -6).sum()),
                                 cap_fires=fires, cap_fires_yr=round(fires / n * 252, 1), saved_bad=round(sv, 1), n_bad=nb,
                                 lost_rec=round(lr, 1), n_rec=nr, rec_pos=npos,
                                 acct_stops=int((X.stop_m[m] >= 0).sum()), acct_stops_ref=int((R.stop_m[m] >= 0).sum()),
                                 lots=int(X.lots[m].sum()), lots_ref=int(R.lots[m].sum()),
                                 X_med=round(X.X[m].median(), 1), L_med=round(np.nanmedian(X[[f"L{s}" for s in range(N)]][m].to_numpy()), 1) if c.startswith("C") else np.nan))
            for s in range(N):
                ds = X[f"R{s}"] - R[f"R{s}"]
                srows.append(dict(line=line, book=book, cfg=c, setup=SH[N][s], R_ref=round(R[f"R{s}"].sum(), 1), dR=round(ds.sum(), 1),
                                  better=int((ds > 1e-9).sum()), worse=int((ds < -1e-9).sum()), better_sum=round(ds[ds > 0].sum(), 1),
                                  worse_sum=round(ds[ds < 0].sum(), 1), fires=int((X[f"M{s}"] >= 0).sum()),
                                  fires_yr=round((X[f"M{s}"] >= 0).sum() / len(X) * 252, 1), L_med=round(X[f"L{s}"].median(), 1),
                                  **{f"dR_{p}": round(ds[per == p].sum(), 1) for p in ("FIT", "T2", "CHECK")}))
A = pd.DataFrame(rows); P = pd.DataFrame(srows)
A.to_csv(W.parent / "results.csv", index=False); P.to_csv(W.parent / "per_setup.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 500)
# pass bar
bar = []
for c in CANDS:
    r = {"cfg": c}
    ok = True
    for line in ("P4", "P9"):
        a = A[(A.line == line) & (A.cfg == c)]
        neu = a[a.book == "NEUTRAL"].set_index("period"); raw = a[a.book == "RAW"].set_index("period")
        c1 = all(neu.loc[p, "dR"] > 0 for p in ("FIT", "T2", "CHECK"))
        c2 = neu.loc["ALL", "t"] >= 2.0
        ps = P[(P.line == line) & (P.cfg == c) & (P.book == "NEUTRAL")]
        c3 = ps.dR.min() >= -10
        c4 = all(raw.loc[p, "worst"] >= raw.loc[p, "worst_ref"] - 1e-9 for p in ("FIT", "T2", "CHECK"))
        r.update({f"{line}_neuFIT": neu.loc["FIT", "dR"], f"{line}_neuT2": neu.loc["T2", "dR"], f"{line}_neuCHK": neu.loc["CHECK", "dR"],
                  f"{line}_t": neu.loc["ALL", "t"], f"{line}_minset": ps.dR.min(), f"{line}_c": "".join("1" if x else "0" for x in (c1, c2, c3, c4)),
                  f"{line}_neu_yr": neu.loc["ALL", "dR_yr"]})
        ok &= c1 and c2 and c3 and c4
    r["bench_pass"] = ok
    bar.append(r)
B = pd.DataFrame(bar); B.to_csv(W.parent / "bar_bench.csv", index=False)
print(B.to_string(index=False))
for book in ("RAW", "NEUTRAL", "P10"):
    print("=====", book)
    print(A[A.book == book].drop(columns=["book"]).to_string(index=False))
print(P[P.book == "NEUTRAL"].to_string(index=False))
print(P[P.book == "RAW"].to_string(index=False))
