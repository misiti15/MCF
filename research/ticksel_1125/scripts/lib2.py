"""TICKSEL helpers. Educational only - not financial advice."""
import numpy as np, pandas as pd
QTRAITS = ["adv20", "atrp", "beta", "gap", "ret1", "ret5", "rvol1"]
PRICE_CUTS = [0, 10, 20, 50, 100, np.inf]

def ct(r, d):
    r = np.asarray(r, float); d = np.asarray(d)
    if len(r) < 3: return np.nan
    m = r.mean(); e = pd.Series(r - m).groupby(d).sum()
    se = np.sqrt((e ** 2).sum()) / len(r)
    return m / se if se > 0 else np.nan

def diff_t(r, ind, d):
    """cluster(date)-robust t of b in r = a + b*ind."""
    r = np.asarray(r, float); ind = np.asarray(ind, float); d = np.asarray(d)
    if ind.sum() < 3 or (1 - ind).sum() < 3: return np.nan, np.nan
    X = np.c_[np.ones_like(r), ind]
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ r
    e = r - X @ b
    g = pd.DataFrame(X * e[:, None]).groupby(d).sum().to_numpy()
    V = XtXi @ (g.T @ g) @ XtXi
    return b[1], b[1] / np.sqrt(V[1, 1])

def wobd(r, d):
    s = pd.Series(np.asarray(r, float)).groupby(np.asarray(d)).sum()
    tot = s.sum(); n = len(r)
    if n < 2: return np.nan, np.nan
    best = s.idxmax()
    nb = n - int((np.asarray(d) == best).sum())
    w = (tot - s.max()) / nb if nb else np.nan
    share = s.max() / tot if tot > 0 else np.nan
    return w, share

def cuts_for(F, trait, q=5):
    v = F[trait].dropna()
    return list(np.unique(np.quantile(v, np.linspace(0, 1, q + 1)[1:-1])))

def bucket(df, trait, cuts):
    if trait == "price":
        return pd.cut(df.entry, PRICE_CUTS, right=False, labels=["<10", "10-20", "20-50", "50-100", ">=100"]).astype(str)
    if trait in ("sector",):
        return df.sector.astype(str)
    if trait == "etf":
        return np.where(df.etf.fillna(False), "ETF", "stock")
    if trait == "levinv":
        return np.where(df.levinv.fillna(False), "lev/inv", "plain")
    if trait == "etb":
        return np.where(df.etb.isna(), "na", np.where(df.etb >= 0.999, "etb=1", "etb<1"))
    if trait == "spread":
        b = np.digitize(df.spread.to_numpy(float), cuts)
        return np.where(df.spread.isna(), "na", "S" + pd.Series(b + 1).astype(str).to_numpy())
    v = df[trait].to_numpy(float)
    b = np.digitize(v, cuts)
    return np.where(np.isnan(v), "na", "Q" + pd.Series(b + 1).astype(str).to_numpy())

def summ(r, d):
    r = np.asarray(r, float)
    w, sh = wobd(r, d)
    return dict(n=len(r), avg=r.mean() if len(r) else np.nan, tot=r.sum(), wobd=w, best_share=sh, t=ct(r, d),
                days=len(np.unique(d)))
