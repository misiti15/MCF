"""Q4: replay every real trade 10-06..16 on SIP 1-min bars under exit/entry variants.
Bars from the minute after the entry fill to 15:55. Stop checked before target in the same bar (conservative).
Costs: each trade's own journal cost (pnl - pnl_adj, in R) is subtracted from every variant that trades it.
Live data, descriptive; variants are counted as configurations but not gated. Educational only - not financial advice."""
from load import *
T = trades(); T = T[T.R1 > 0].copy()
DAYS = sorted(T.date.unique())
def sim(up, dn, cl, tgt, stop=-1.0, tmax=None, be=None, scale=None, trail=None):
    st = stop; half = None; peak = 0.0
    n = len(cl)
    for i in range(n):
        if tmax is not None and i >= tmax:
            r = cl[i - 1] if i else 0.0
            return r if half is None else 0.5 * half + 0.5 * r
        if dn[i] <= st:
            r = st
            return r if half is None else 0.5 * half + 0.5 * r
        if scale is not None and half is None and up[i] >= scale:
            half = scale; st = max(st, 0.0)
        if tgt is not None and up[i] >= tgt:
            return tgt if half is None else 0.5 * half + 0.5 * tgt
        if be is not None and up[i] >= be: st = max(st, 0.0)
        if trail is not None:
            peak = max(peak, up[i]); st = max(st, peak - trail)
    r = cl[-1] if n else 0.0
    return r if half is None else 0.5 * half + 0.5 * r
V = {"sim_base": dict(), "stop0.5": dict(stop=-0.5), "stop0.75": dict(stop=-0.75), "time30": dict(tmax=30), "time60": dict(tmax=60),
     "time120": dict(tmax=120), "be@0.5": dict(be=0.5), "scale@0.5+BE": dict(scale=0.5), "no_target_hold": dict(notgt=True),
     "target2x": dict(t2=True), "trail1R": dict(notgt=True, trail=1.0), "opposite[HINDSIGHT]": dict(opp=True)}
rows = []
for d in DAYS:
    B = bars(d); B = B[(B.ts.dt.time >= pd.Timestamp("09:30").time()) & (B.ts.dt.time <= pd.Timestamp("15:55").time())]
    spy = B[B.symbol == "SPY"].set_index("ts"); spy_o = spy.open.iloc[0]
    G = {s: g.set_index("ts") for s, g in B.groupby("symbol")}
    for r in T[T.date == d].itertuples():
        g = G.get(r.symbol)
        if g is None: continue
        m = r.nt.floor("1min")
        w = g[g.index > m]
        if w.empty: continue
        s = r.side
        up = ((w.high - r.entry) / r.R1 if s == 1 else (r.entry - w.low) / r.R1).values
        dn = ((w.low - r.entry) / r.R1 if s == 1 else (r.entry - w.high) / r.R1).values
        cl = (s * (w.close - r.entry) / r.R1).values
        tgt = None if pd.isna(r.target) else s * (r.target - r.entry) / r.R1
        sp = spy[spy.index <= m]
        spy_now = 100 * (sp.close.iloc[-1] / spy_o - 1) if len(sp) else 0.0
        o = dict(id=r.id, acct=r.acct, date=d, strategy=r.strategy, side=s, actual=r.r_multiple, cost=r.cost_r, spy_at_entry=spy_now, tgt=tgt,
                 hour=r.nt.hour, mfe=up.max(), mae=dn.min())
        for k, kw in V.items():
            kw = dict(kw)
            if kw.pop("opp", False):
                o[k] = sim(-dn, -up, -cl, tgt); continue
            t2 = kw.pop("t2", False); notgt = kw.pop("notgt", False)
            tt = None if notgt else (None if tgt is None else (2 * tgt if t2 else tgt))
            o[k] = sim(up, dn, cl, tt, **kw)
        rows.append(o)
    print(d, len(rows), flush=True)
R = pd.DataFrame(rows); R.to_csv(S / "rework.csv", index=False)
