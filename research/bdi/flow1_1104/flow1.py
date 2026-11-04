"""FLOW1 (owner 11-04): the book as a sensor. Scores PLAN.md on a trade table.
Usage: python flow1.py live <scratch>   (expects <scratch>/j_<acct>.db and <scratch>/spy1.pkl; SPY 1-min SIP bars)
Writes results_live.csv, picture_live.csv, regress_live.csv, out_live.txt here. Educational only - not financial advice."""
import itertools, math, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
TS = [615, 630, 645, 660]          # minutes since midnight: 10:15, 10:30, 10:45, 11:00
KS, MS, RULES = [3, 5], ["sumR", "win"], ["filter", "scale"]
N_TOTAL = 96; BAR = max(1.5, math.sqrt(2 * math.log(N_TOTAL)))
ACCTS = ["primary", "testing", "testing2", "graveyard", "gen"]


def mins(s):
    t = pd.to_datetime(s, utc=True, format="mixed").dt.tz_convert("America/New_York")
    return t.dt.hour * 60 + t.dt.minute + t.dt.second / 60


def load_live(S):
    out = []
    for a in ACCTS:
        c = sqlite3.connect(Path(S) / f"j_{a}.db")
        t = pd.read_sql("select date, side, entry_time, exit_time, entry, stop, shares, pnl_adj, pnl from trades "
                        "where run_id = 1 and date >= '2026-10-06' and date <= '2026-11-03' and exit_time is not null "
                        "and entry_time is not null", c)
        risk = (t.entry - t.stop).abs() * t.shares
        t["r"] = t.pnl_adj.fillna(t.pnl) / risk
        t = t[np.isfinite(t.r) & (risk > 0)].copy()
        t["ent"], t["ext"], t["acct"] = mins(t.entry_time), mins(t.exit_time), a
        out.append(t[["acct", "date", "side", "ent", "ext", "r"]])
    return pd.concat(out, ignore_index=True)


def spy_ctx(spy):
    spy = spy.copy(); spy["date"] = spy.index.strftime("%Y-%m-%d"); spy["m"] = spy.index.hour * 60 + spy.index.minute
    tp = (spy.h + spy.l + spy.c) / 3; spy["pv"] = tp * spy.v
    rows = []
    for d, g in spy.groupby("date"):
        o = g.o.iloc[0]; oc = g.c.iloc[-1] / o - 1 if g.m.iloc[-1] >= 955 else np.nan
        for T in TS:
            h = g[g.m < T]            # bars that closed by T (bar start < T)
            if not len(h):
                continue
            rows.append(dict(date=d, T=T, spy_fo=h.c.iloc[-1] / o - 1, spy_vw=h.c.iloc[-1] / (h.pv.sum() / h.v.sum()) - 1,
                             spy_oc=oc))
    return pd.DataFrame(rows)


def signals(t, T):
    e = t[t.ext <= T]
    g = e.groupby(["date", "side"]).r
    return pd.DataFrame({"n": g.size(), "sumR": g.sum(), "win": g.apply(lambda x: (x > 0).mean())}).reset_index()


def state(sig, k, m):
    conf = sig["sumR"] > 0 if m == "sumR" else sig["win"] > 0.5
    return np.where(sig.n < k, 0, np.where(conf, 1, -1))


def later(t, T, ctx):
    L = t[t.ent > T].copy()
    sg = signals(t, T)
    L = L.merge(sg, on=["date", "side"], how="left").fillna({"n": 0, "sumR": 0.0, "win": np.nan})
    c = ctx[ctx["T"] == T]
    L = L.merge(c, on="date", how="left")
    L["x_spy"] = L.side * L.spy_fo; L["x_vw"] = L.side * L.spy_vw
    return L


def dstats(dd):
    """dd: per-day delta series (all days of the book, zeros included)."""
    n = len(dd); mu = dd.mean(); sd = dd.std(ddof=1) if n > 1 else np.nan
    best = dd.idxmax() if n else None; tot = dd.sum()
    return dict(days=n, delta=round(tot, 2), t=round(mu / (sd / math.sqrt(n)), 2) if sd and sd > 0 else np.nan,
                delta_wo_best=round(tot - dd.max(), 2), best_share=round(dd.max() / tot, 2) if tot > 0 else np.nan)


def weights(L, k, m, rule):
    st = state(L, k, m)
    if rule == "filter":
        return np.where(st == -1, 0.0, 1.0), st
    return np.where(st == 1, 1.5, np.where(st == -1, 0.5, 1.0)), st


def score(L, w, days):
    dd = (L.r * (w - 1)).groupby(L.date).sum().reindex(days, fill_value=0.0)
    s = dstats(dd)
    kept, drop = L[w > 0], L[w == 0]
    # excess (rule 6): delta scored against the book's own window mean R of later trades (same side), so a filter that
    # only "helps" by trading less in a losing book scores ~0
    mu = L.groupby("side").r.transform("mean")
    xd = ((L.r - mu) * (w - 1)).groupby(L.date).sum().reindex(days, fill_value=0.0); xs_ = dstats(xd)
    s.update(excess=xs_["delta"], excess_t=xs_["t"])
    s.update(n_later=len(L), base_R=round(L.r.sum(), 2), base_avg=round(L.r.mean(), 4),
             kept_avg=round(kept.r.mean(), 4) if len(kept) else np.nan, n_drop=len(drop),
             drop_avg=round(drop.r.mean(), 4) if len(drop) else np.nan)
    return s


def ols_cl(y, X, g):
    X = np.column_stack([np.ones(len(y)), X]); XtX = np.linalg.pinv(X.T @ X); b = XtX @ X.T @ y; e = y - X @ b
    meat = np.zeros((X.shape[1],) * 2)
    for gi in np.unique(g):
        s = X[g == gi].T @ e[g == gi]; meat += np.outer(s, s)
    G = len(np.unique(g)); c = G / (G - 1) * (len(y) - 1) / (len(y) - X.shape[1])
    V = c * XtX @ meat @ XtX; return b, b / np.sqrt(np.diag(V))


def run(t, ctx, book, P):
    days = sorted(t.date.unique()); res, reg, pic = [], [], []
    for T in TS:
        L = later(t, T, ctx)
        for k, m, rule in itertools.product(KS, MS, RULES):
            w, st = weights(L, k, m, rule)
            s = score(L, w, days)
            for side, nm in ((1, "long"), (-1, "short")):
                mk = (L.side == side).to_numpy(); s2 = score(L[mk], w[mk], days)
                s[f"{nm}_delta"], s[f"{nm}_t"] = s2["delta"], s2["t"]
            # day-type split (diagnostic): delta by SPY open->close type
            dt = np.where(L.spy_oc > .0025, "up", np.where(L.spy_oc < -.0025, "down", "quiet"))
            for ty in ("up", "down", "quiet"):
                mk = dt == ty; s[f"dt_{ty}"] = round(float((L.r[mk] * (w[mk] - 1)).sum()), 2)
            # conditioning on side-aligned SPY move at T
            b = np.where(L.x_spy > .0025, "with", np.where(L.x_spy < -.0025, "against", "flat"))
            for ty in ("with", "flat", "against"):
                mk = b == ty; s[f"spy_{ty}"] = round(float((L.r[mk] * (w[mk] - 1)).sum()), 2)
            # on top of the SPY rule: among trades the SPY rule keeps (x_spy >= 0)
            ks = (L.x_spy >= 0).to_numpy(); s["on_spy_delta"] = round(float((L.r[ks] * (w[ks] - 1)).sum()), 2)
            s["on_spy_t"] = dstats((L.r[ks] * (w[ks] - 1)).groupby(L.date[ks]).sum().reindex(days, fill_value=0.0))["t"]
            s.update(book=book, T=T, k=k, m=m, rule=rule, n_conf=int((st == 1).sum()), n_contra=int((st == -1).sum()))
            res.append(s)
        # controls (SPY / VWAP filters)
        for nm, x in (("SPYrule", L.x_spy), ("VWAPrule", L.x_vw)):
            w = np.where(x >= 0, 1.0, 0.0); w = np.where(np.isnan(x), 1.0, w)
            s = score(L, w, days); s.update(book=book, T=T, k=0, m="-", rule=nm); res.append(s)
        # regressions: later-trade R on book signal and SPY
        for k in KS:
            Lk = L[L.n >= k].dropna(subset=["x_spy", "x_vw"])
            if Lk.date.nunique() < 5:
                continue
            y = Lk.r.clip(-5, 5).to_numpy(); g = Lk.date.to_numpy()
            xb = np.sign(Lk.sumR).to_numpy(); xr = Lk.sumR.clip(-10, 10).to_numpy() / np.maximum(Lk.n.to_numpy(), 1)
            for lab, X in (("book_sign", xb[:, None]), ("book_avgR", xr[:, None]), ("spy_only", Lk[["x_spy", "x_vw"]].to_numpy() * 100),
                           ("book_sign+spy", np.column_stack([xb, Lk.x_spy.to_numpy() * 100, Lk.x_vw.to_numpy() * 100])),
                           ("book_avgR+spy", np.column_stack([xr, Lk.x_spy.to_numpy() * 100, Lk.x_vw.to_numpy() * 100]))):
                b_, t_ = ols_cl(y, X, g)
                reg.append(dict(book=book, T=T, k=k, model=lab, n=len(y), days=len(np.unique(g)),
                                **{f"b{i}": round(v, 4) for i, v in enumerate(b_)}, **{f"t{i}": round(v, 2) for i, v in enumerate(t_)}))
            # does the book sign just restate SPY? correlation of book sign with side-aligned SPY at T (per day-side)
            ds = Lk.groupby(["date", "side"]).agg(sb=("sumR", "first"), xs=("x_spy", "first")).reset_index()
            reg.append(dict(book=book, T=T, k=k, model="corr(book sumR sign, side*SPY fo)", n=len(ds),
                            b0=round(np.corrcoef(np.sign(ds["sb"].to_numpy(float)), ds["xs"].to_numpy(float))[0, 1], 3) if len(ds) > 2 else np.nan))
    # simple picture: T=10:30, first k closes green/red
    for k in KS:
        e = t[t.ext <= 630].sort_values("ext")
        fk = e.groupby(["date", "side"]).head(k).groupby(["date", "side"]).r.agg(["size", "sum"]).reset_index()
        fk = fk[fk["size"] >= k]
        L = t[t.ent > 630].merge(fk, on=["date", "side"])
        for side, nm in ((1, "long"), (-1, "short")):
            for col, lab in ((L["sum"] > 0, "green"), (L["sum"] <= 0, "red")):
                x = L[(L.side == side) & col]
                pic.append(dict(book=book, k=k, side=nm, first_k=lab, days=x.date.nunique(), trades=len(x),
                                win=round((x.r > 0).mean(), 3) if len(x) else np.nan, avgR=round(x.r.mean(), 4) if len(x) else np.nan,
                                avgR_wo_best_day=round(x[x.date != x.groupby("date").r.sum().idxmax()].r.mean(), 4) if x.date.nunique() > 1 else np.nan))
        # days with no qualifying first-k (baseline)
    return res, reg, pic


if __name__ == "__main__":
    mode, S = sys.argv[1], Path(sys.argv[2])
    assert mode == "live"
    T_ = load_live(S); ctx = spy_ctx(pd.read_pickle(S / "spy1.pkl"))
    out = open(HERE / "out_live.txt", "w")
    R, G, Pc = [], [], []
    for book, tt in (("primary", T_[T_.acct == "primary"]), ("merged", T_)):
        print(book, len(tt), tt.date.nunique(), "days", file=out)
        a, b, c = run(tt, ctx, book, print); R += a; G += b; Pc += c
    R, G, Pc = pd.DataFrame(R), pd.DataFrame(G), pd.DataFrame(Pc)
    R.to_csv(HERE / "results_live.csv", index=False); G.to_csv(HERE / "regress_live.csv", index=False)
    Pc.to_csv(HERE / "picture_live.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(f"bar t >= {BAR:.2f} (N={N_TOTAL})", file=out)
    print(Pc.to_string(index=False), file=out)
    print(R[["book", "T", "k", "m", "rule", "days", "n_later", "base_avg", "delta", "t", "excess", "excess_t", "delta_wo_best", "best_share",
             "long_delta", "short_delta", "kept_avg", "drop_avg", "n_drop", "on_spy_delta", "on_spy_t", "spy_with", "spy_flat",
             "spy_against", "dt_up", "dt_down", "dt_quiet"]].to_string(index=False), file=out)
    print(G.to_string(index=False), file=out)
    out.close(); print(open(HERE / "out_live.txt").read())
