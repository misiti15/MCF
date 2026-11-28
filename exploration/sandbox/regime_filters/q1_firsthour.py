"""Q1: does a bad start (closed R by T, scaled by L) predict a worse rest of day (avg R of lots entered after T)?
Usage: python q1_firsthour.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr
from common import load, dayt
S = sys.argv[1]; t = load(S); t = t[t.L.notna()]
rng = np.random.default_rng(11)
for T in [600, 630, 660]:
    rows = []
    for (a, d), g in t.groupby(["account", "date"]):
        X = g.r[g.xmin <= T].sum() / g.L.iloc[0]
        late = g[g.emin > T]
        if len(late) < 3:
            continue
        rows.append(dict(account=a, date=d, book=g.book.iloc[0], period=g.period.iloc[0], X=X, Xraw=g.r[g.xmin <= T].sum(),
                         early_n=(g.emin <= T).sum(), Y=late.r.mean(), Yn=len(late), Ytot=late.r.sum(), Ltot=g.r.sum()))
    D = pd.DataFrame(rows)
    print(f"\n=== T = {T//60}:{T%60:02d}  (first entries are at 09:50) ===")
    for (bk, pe), x in D.groupby(["book", "period"]):
        if len(x) < 8:
            continue
        rho, p = spearmanr(x.X, x.Y)
        q = x.X.quantile(0.2); m = (x.X <= q) & (x.X < 0); bad = x[m]; rest = x[~m]
        if len(bad) < 2: print(bk, pe, 'too few negative starts', len(bad)); continue
        # day-clustered difference: per date, mean Y bad minus mean Y rest (dates where both exist), plus lot-weighted
        wb = np.average(bad.Y, weights=bad.Yn); wr = np.average(rest.Y, weights=rest.Yn)
        # permutation of X labels within account (control for account level)
        diffs = []
        for _ in range(500):
            xs = x.copy(); xs["Xp"] = xs.groupby("account").X.transform(lambda s: s.sample(frac=1, random_state=int(rng.integers(1e9))).values)
            qq = xs.Xp.quantile(0.2); mm = (xs.Xp <= qq) & (xs.Xp < 0); b2 = xs[mm]; r2 = xs[~mm]
            diffs.append(np.average(b2.Y, weights=b2.Yn) - np.average(r2.Y, weights=r2.Yn))
        pct = 100 * np.mean(np.array(diffs) < (wb - wr))
        print(f"{bk:8s} {pe}: acct-days {len(x):3d} rho(X,Y) {rho:+.3f} (p {p:.3f}) | bottom-quintile neg start (X<={q:+.2f}, {len(bad)} days) late R/lot {wb:+.3f} "
              f"(n {bad.Yn.sum()}) vs rest {wr:+.3f} (n {rest.Yn.sum()}) diff {wb-wr:+.3f}, pct vs within-acct shuffle {pct:.0f}")
    D.to_csv(f"{S}/q1_T{T}.csv", index=False)
# by side: does the side's own bad start predict that side's later lots?
print("\n=== by side, T=10:30: side's closed R by 10:30 vs that side's later lots ===")
for side in ["long", "short"]:
    rows = []
    for (a, d), g in t[t.sidel == side].groupby(["account", "date"]):
        late = g[g.emin > 630]
        if len(late) < 3:
            continue
        rows.append(dict(book=g.book.iloc[0], period=g.period.iloc[0], X=g.r[g.xmin <= 630].sum() / g.L.iloc[0], Y=late.r.mean(), Yn=len(late)))
    D = pd.DataFrame(rows)
    for (bk, pe), x in D.groupby(["book", "period"]):
        if len(x) < 8:
            continue
        rho, p = spearmanr(x.X, x.Y); q = x.X.quantile(0.2)
        m = (x.X <= q) & (x.X < 0); b = x[m]; r = x[~m]
        if len(b) < 2: continue
        print(f"{side:5s} {bk:8s} {pe}: n {len(x):3d} rho {rho:+.3f} (p {p:.3f}) bottom-quintile late {np.average(b.Y, weights=b.Yn):+.3f} vs rest {np.average(r.Y, weights=r.Yn):+.3f}")
