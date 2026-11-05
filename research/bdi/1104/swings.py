"""BDI 2026-11-04 step 0b: swing autopsy for every intraday account (Primary first), generalising
research/bdi/swing1103 (Primary, to 13:20) to the full session and all five accounts.

Curve: per lot, open mark = (1-min close - fill) x side x shares / $risk (no costs) while open, realized = journal
pnl_adj / $risk (costs in) from the exit minute. Total R = sum over lots ($ likewise).
Swings: zig-zag on the 1-min total-R curve with reversal threshold 25% of the day's R range (max - min); every leg
is listed; the largest leg (and the leg into / out of the trough) is decomposed.
Decomposition of a leg [t0, t1] (parts sum exactly to the leg):
  market   beta_s x SPY 1-min return, summed over minutes the lot is open (beta = 5-min-return beta to SPY,
           2026-09-22..11-03, SIP)
  mismatch group part: gamma_s x (ETF return - beta_ETF x SPY return), ETF = the sector ETF whose residual best
           correlates with the stock's residual (same window); for ETF trades their own residual. "The setup's names'
           group moved against the setup's side on this day."
  entries  the fill-to-close of the entry minute + the stock-specific part of the first 5 minutes after the fill
  stock    the remaining stock-specific part, incl. exit fills and costs (realized pnl_adj minus the last mark)
Top 5 names = cross-cut of the same leg. Writes swings_out.txt, timeline_<acct>.csv (5-min).
Usage: python swings.py <scratch>    Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(HERE.parent / "nightly1104" / "trades.csv")
T = T[T.run_id == 1].copy()
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
T["risk_d"] = (T.entry - T.stop).abs() * T.shares
B1 = pd.read_parquet(S / "cov/days/2026-11-04/bars.parquet")
idx = pd.date_range("2026-11-04 09:30", "2026-11-04 15:59", freq="1min", tz=TZ)
def px(s):
    g = B1[B1.symbol == s]
    if len(g) == 0:
        f = S / "bars" / f"{s}.parquet"
        if not f.exists(): return None
        g = pd.read_parquet(f); g.index = pd.to_datetime(g.index, utc=True).tz_convert(TZ)
    return g.close.reindex(idx).ffill().bfill()
ETF = ["XLK", "SMH", "XLF", "XLE", "XLI", "XLV", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "KRE", "IGV", "XBI", "IWM"]
B5 = pd.read_parquet(S / "mh/2026-11-04/bars5.parquet"); B5 = B5[B5.index < pd.Timestamp("2026-11-04", tz=TZ)]
R5 = B5.pivot_table(index=B5.index, columns="symbol", values="close").pct_change(fill_method=None)
R5 = R5[R5.index.normalize() == R5.index.normalize()]  # keep
first = R5.index.to_series().groupby(R5.index.date).transform("min") == R5.index.to_series(); R5[first.values] = np.nan  # no overnight
sp = R5["SPY"]
def fit(s):
    if s not in R5: return 1.0, "SPY", 0.0
    x = pd.concat([R5[s], sp], axis=1).dropna(); b = np.cov(x.iloc[:, 0], x.iloc[:, 1])[0, 1] / x.iloc[:, 1].var()
    res = x.iloc[:, 0] - b * x.iloc[:, 1]; best, bc, bg = "SPY", -1, 0.0
    for e in ETF:
        if e not in R5: continue
        y = pd.concat([R5[e], sp], axis=1).reindex(x.index).dropna(); be = np.cov(y.iloc[:, 0], y.iloc[:, 1])[0, 1] / y.iloc[:, 1].var()
        er = (y.iloc[:, 0] - be * y.iloc[:, 1]).reindex(res.index)
        c = res.corr(er)
        if c > bc: best, bc, bg = e, c, np.cov(res.dropna().reindex(er.dropna().index).fillna(0), er.dropna().reindex(res.dropna().index).fillna(0))[0, 1] / max(er.var(), 1e-12)
    if s in ETF: best, bg = s, 1.0
    return b, best, (bg if bc > 0.2 else 0.0)
PX = {s: px(s) for s in set(T.symbol) | set(ETF) | {"SPY", "QQQ"}}
PX = {k: v for k, v in PX.items() if v is not None}
BETA = {}
for s in set(T.symbol) | set(ETF):
    BETA[s] = fit(s)
rs = PX["SPY"].pct_change().fillna(0).to_numpy()
NM = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Generator"}
P = []
def pr(*a): P.append(" ".join(str(x) for x in a))
spy_fo = (PX["SPY"] / PX["SPY"].iloc[0] - 1) * 100; qqq_fo = (PX["QQQ"] / PX["QQQ"].iloc[0] - 1) * 100
pr("SPY o-c +0.48% (UP day, SPY above open at 10:00 +0.55%; QQQ +1.34% at 10:00, high +1.89% 10:15, close +0.50%; IWM -0.06%, low -1.01% 11:27). Betas 5-min 09-22..11-03.")
for a in ("p", "t1", "t2", "gy", "gen"):
    t = T[T.acct == a].reset_index(drop=True); n = len(idx); L = len(t)
    V = np.zeros((L, n)); VD = np.zeros((L, n)); comp = np.zeros((4, L, n))     # market, mismatch, entries, stock (per-minute increments)
    openm = np.zeros((L, n), bool)
    for i, r in t.iterrows():
        p = PX.get(r.symbol)
        if p is None or r.risk_d <= 0: continue
        sd, sh, rk = int(r.side), float(r.shares), float(r.risk_d)
        b, e, g = BETA.get(r.symbol, (1.0, "SPY", 0.0)); pe = PX.get(e, PX["SPY"]); be = BETA.get(e, (1.0,))[0] if e in BETA else 1.0
        re_ = pe.pct_change().fillna(0).to_numpy(); pv = p.to_numpy(); rr = np.r_[0, np.diff(pv) / pv[:-1]]
        i0 = idx.searchsorted(r.nt.floor("min")); i1 = idx.searchsorted(r.et.floor("min")) if pd.notna(r.et) else n - 1
        i1 = min(max(i1, i0), n - 1)
        mark = (pv - r.entry) * sd * sh / rk
        V[i, i0:i1] = mark[i0:i1]; V[i, i1:] = r.radj; VD[i, i0:i1] = mark[i0:i1] * rk; VD[i, i1:] = r.pnl_adj; openm[i, i0:i1] = True
        # increments
        inc = np.diff(np.r_[0, V[i]])
        comp[2, i, i0] += inc[i0]                                      # fill -> entry-minute close
        for m in range(i0 + 1, i1):
            dp = (pv[m] - pv[m - 1]) * sd * sh / rk; base = pv[m - 1] * sd * sh / rk
            mk = b * rs[m] * base; gp = g * (re_[m] - be * rs[m]) * base; st = dp - mk - gp
            comp[0, i, m] += mk; comp[1, i, m] += gp
            comp[2 if m <= i0 + 5 else 3, i, m] += st
        if i1 > i0: comp[3, i, i1] += inc[i1]                          # exit fill + costs
        elif i1 == i0: comp[2, i, i0] += 0
    tot = V.sum(0); totd = VD.sum(0)
    assert np.allclose(comp.sum(0).sum(0).cumsum(), tot, atol=1e-6), a
    # 5-min timeline
    rows = []
    for m in range(19, n, 5):   # from 09:49
        o = openm[:, m]; side = t.side.to_numpy()
        nb = sum(int(t.side[i]) * t.shares[i] * PX[t.symbol[i]].iloc[m] * BETA.get(t.symbol[i], (1,))[0] * 0.01 / t.risk_d[i] for i in np.flatnonzero(o) if t.symbol[i] in PX)
        nbd = sum(int(t.side[i]) * t.shares[i] * PX[t.symbol[i]].iloc[m] * BETA.get(t.symbol[i], (1,))[0] for i in np.flatnonzero(o) if t.symbol[i] in PX)
        rows.append(dict(et=f"{idx[m]:%H:%M}", open_R=round(V[o, m].sum(), 2), realized_R=round(V[~o, m].sum(), 2), total_R=round(tot[m], 2), total_usd=round(totd[m]),
                         spy=round(spy_fo.iloc[m], 2), qqq=round(qqq_fo.iloc[m], 2), longs=int((o & (side == 1)).sum()), shorts=int((o & (side == -1)).sum()),
                         beta_R_per_1pct=round(nb, 1), beta_usd=round(nbd)))
    TL = pd.DataFrame(rows); TL.to_csv(HERE / f"timeline_{a}.csv", index=False)
    # zig-zag swings on the 1-min curve from 09:50
    c = tot[20:]; rng = c.max() - c.min(); th = 0.25 * rng
    piv = [0]; hi = lo = 0; tr_ = 0
    for k in range(1, len(c)):
        if c[k] > c[hi]: hi = k
        if c[k] < c[lo]: lo = k
        if tr_ >= 0 and c[hi] - c[k] >= th and hi > piv[-1] - (0 if tr_ else 1):
            if hi != piv[-1]: piv.append(hi)
            tr_ = -1; lo = k
        elif tr_ <= 0 and c[k] - c[lo] >= th and lo >= piv[-1]:
            if lo != piv[-1]: piv.append(lo)
            tr_ = 1; hi = k
    last = len(c) - 1
    if last != piv[-1]: piv.append(last)
    piv = [p + 20 for p in piv]
    pk, tr = int(np.argmax(tot[20:]) + 20), int(np.argmin(tot[20:]) + 20)
    nt_ = t.groupby("side").size().to_dict()
    pr(f"\n#### {NM[a]}: {L} lots (long {nt_.get(1, 0)}, short {nt_.get(-1, 0)}); close {tot[-1]:+.2f}R / ${totd[-1]:+.0f}; peak {tot[pk]:+.2f}R ({idx[pk]:%H:%M}), trough {tot[tr]:+.2f}R ({idx[tr]:%H:%M}); range {rng:.2f}R, swing threshold {th:.2f}R")
    legs = [(piv[k], piv[k + 1]) for k in range(len(piv) - 1)]
    pr("   legs: " + "; ".join(f"{idx[x]:%H:%M}->{idx[y]:%H:%M} {tot[y] - tot[x]:+.2f}R (${totd[y] - totd[x]:+.0f}, SPY {spy_fo.iloc[x]:+.2f}->{spy_fo.iloc[y]:+.2f}%)" for x, y in legs))
    big = sorted(legs, key=lambda l: -abs(tot[l[1]] - tot[l[0]]))[:2]
    for x, y in sorted(big):
        sl = slice(x + 1, y + 1); parts = comp[:, :, sl].sum(2)          # 4 x L
        sw = tot[y] - tot[x]; P4 = parts.sum(1)
        pr(f"   SWING {idx[x]:%H:%M}->{idx[y]:%H:%M}: {sw:+.2f}R (${totd[y] - totd[x]:+.0f}) = market {P4[0]:+.2f} + setup-day mismatch {P4[1]:+.2f} + bad entries {P4[2]:+.2f} + stock-specific {P4[3]:+.2f} (check {P4.sum():+.2f})")
        lr = pd.DataFrame({"sym": t.symbol, "setup": t.strategy, "side": t.side, "R": parts.sum(0)})
        top = lr.groupby(["sym", "setup"]).R.sum().sort_values(key=lambda s: -s.abs() * np.sign(sw)).head(5) if False else lr.groupby(["sym", "setup"]).R.sum()
        top = top.sort_values(ascending=sw < 0).head(5)
        pr("     top 5 names: " + "; ".join(f"{s} `{st}` {v:+.2f}R" for (s, st), v in top.items()) + f" (together {top.sum():+.2f}R)")
        bs = lr.groupby("setup").R.sum().sort_values(ascending=sw < 0)
        pr("     by setup: " + "; ".join(f"`{k}` {v:+.2f}" for k, v in bs.head(4).items()))
        ent = t[(t.nt >= idx[x]) & (t.nt <= idx[y])]
        pr(f"     entries inside the leg: {len(ent)} (long {(ent.side == 1).sum()}, short {(ent.side == -1).sum()}), their final avg R {ent.radj.mean():+.3f}; "
           f"longs/shorts open at start {int((openm[:, x] & (t.side.to_numpy() == 1)).sum())}/{int((openm[:, x] & (t.side.to_numpy() == -1)).sum())}, net beta {TL.iloc[max(0, (x - 19) // 5)].beta_R_per_1pct:+.1f}R per +1% SPY")
pr("\nEducational only - not financial advice.")
(HERE / "swings_out.txt").write_text("\n".join(P) + "\n"); print("\n".join(P))
