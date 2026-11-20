"""Day-level profit lock on live account-days (PLAN.md). Usage: python sim_live.py live_paths.parquet bars.parquet OUTDIR
Writes days.csv (config x account-day) and lots.csv (config x changed lot). Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
P = pd.read_parquet(sys.argv[1]); B = pd.read_parquet(sys.argv[2]); OUT = sys.argv[3]
M0, NM = 570, 390
GRID = [(X, Y, A) for X in (5.0, 8.0) for Y in (0.3, 0.5) for A in ("A1block", "A2tighten", "A3half", "A4flatten")]
G = {}
for (day, sym), g in B.groupby(["day", "symbol"]):
    a = np.full((4, NM), np.nan, dtype=np.float64); i = g.m.to_numpy() - M0; ok = (i >= 0) & (i < NM)
    for k, col in enumerate("ohlc"): a[k, i[ok]] = g[col].to_numpy()[ok]
    a[3] = pd.Series(a[3]).ffill().bfill().to_numpy()
    a[0] = np.where(np.isnan(a[0]), a[3], a[0]); G[(day, sym)] = a
del B
P = P[P.m_out.notna()].copy()
P["i0"] = (P.m_in - M0).clip(0, NM - 1).astype(int); P["i1"] = (P.m_out - M0).clip(0, NM - 1).astype(int)
P["rps"] = (P.entry - P.stop).abs()
sp = P.spread_bps.fillna(5.0)
P["xc"] = (sp / 2e4 * P.entry + 0.01 + 1e-4 * P.entry) / P.rps   # extra early-exit cost in R
def act(L, g, t, A):
    """lot deltas of action A taken at minute index t on one account-day. Returns (list of (r, kind, d), dom, n_open)."""
    opn = [(r, a) for r, a in L if r.i0 <= t < r.i1]
    nl = sum(r.side > 0 for r, a in opn); ns = len(opn) - nl
    if nl != ns: dom = 1 if nl > ns else -1
    else:
        prior = g[g.i0 <= t]; dom = int(prior.sort_values("m_in").side.iloc[-1]) if len(prior) else 1
    out = []
    for r, a in L:
        d = 0.0; kind = None
        if r.i0 > t and (A == "A4flatten" or (A == "A1block" and r.side == dom)):
            d = -r.R; kind = "blocked"
        elif r.i0 <= t < r.i1 and a is not None and A in ("A2tighten", "A3half", "A4flatten"):
            if A in ("A3half", "A4flatten"):
                px = a[0, t + 1]; full = r.side * (px - r.exit) / r.rps - r.xc
                d = full if A == "A4flatten" else 0.5 * full; kind = "exit"
            else:
                m = r.side * (a[3, t] - r.entry) / r.rps
                if m > 0:
                    lock = r.entry + r.side * 0.5 * m * r.rps
                    for j in range(t + 1, r.i1 + 1):
                        if r.side > 0 and a[2, j] <= lock:
                            px = min(a[0, j], lock); d = (px - r.exit) / r.rps - r.xc; kind = "lock"; break
                        if r.side < 0 and a[1, j] >= lock:
                            px = max(a[0, j], lock); d = (r.exit - px) / r.rps - r.xc; kind = "lock"; break
        if kind: out.append((r, kind, d))
    return out, dom, len(opn)

DAY = {}
for (acc, day), g in P.groupby(["account", "date"]):
    real = np.zeros(NM); unr = np.zeros(NM); L = []
    for r in g.itertuples():
        a = G.get((day, r.symbol))
        real[r.i1:] += r.R
        ok = a is not None and r.rps > 0
        if ok and r.i1 > r.i0: unr[r.i0:r.i1] += r.side * (a[3, r.i0:r.i1] - r.entry) / r.rps
        L.append((r, a if ok else None))
    DAY[(acc, day)] = (g, L, real + unr, float(real[-1]))
days, lots = [], []
for X, Y, A in GRID:
    fired = {}
    for (acc, day), (g, L, mtm, base) in DAY.items():
        pk = np.maximum.accumulate(mtm); hit = np.where((pk >= X) & (mtm <= pk * (1 - Y)))[0]
        if len(hit) and hit[0] < NM - 1: fired[(acc, day)] = int(hit[0])
    for (acc, day), (g, L, mtm, base) in DAY.items():
        rec = dict(account=acc, date=day, X=X, Y=Y, A=A, base=base, n=len(g), fired=False, new=base, n_new=len(g))
        if (acc, day) in fired:
            t = fired[(acc, day)]; pk = np.maximum.accumulate(mtm)
            out, dom, no = act(L, g, t, A)
            for r, kind, d in out:
                lots.append(dict(account=acc, date=day, X=X, Y=Y, A=A, strategy=r.strategy, family=r.family, side=r.side, kind=kind, R=r.R, d=d))
            # time-matched placebo: same action, same clock minute, on this account's non-fired days
            pl = [sum(d for _, _, d in act(L2, g2, t, A)[0]) for (a2, d2), (g2, L2, _, _) in DAY.items() if a2 == acc and (a2, d2) not in fired]
            rec.update(fired=True, t=t + M0, peak_at_fire=float(pk[t]), mtm_at_fire=float(mtm[t]), dom=dom, open_n=no,
                       runner=bool(mtm[t + 1:].max() > pk[t]), new=base + sum(d for _, _, d in out),
                       n_new=len(g) - sum(k == "blocked" for _, k, _ in out), placebo=float(np.mean(pl)) if pl else np.nan, placebo_n=len(pl))
        days.append(rec)
pd.DataFrame(days).to_csv(f"{OUT}/days.csv", index=False); pd.DataFrame(lots).to_csv(f"{OUT}/lots.csv", index=False)
print("account-days", len(DAY), "changed lots", len(lots))
