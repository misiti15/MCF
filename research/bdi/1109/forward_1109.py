"""Forward tallies 2026-11-09 for the swing-autopsy shadows not already tallied by nightly1109 (which did L1 / L2 / L3 / L6,
gate1, comp15, burst1-openloss-latch3, latch1103 category, REG2): swing1104-L7, swing1104-L8, burst2-openloss-latch4 (forward
day 1, all 7 accounts), burst2-flush-gate-short (forward day 1), swing1106-L10 (forward day 1), swing1105-L9 (qualifying check).
fb1 in fb1_live.py, mh1106-p1 in mh_p1_live.py, ECG1 in ecg1.py. Journals run 1, all 7 accounts, R = pnl_adj / $ risk.
Usage: python forward_1109.py <scratch mh1109>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"; D = "2026-11-09"
T = pd.read_csv(HERE.parent / "nightly1109" / "trades.csv"); T = T[T.run_id == 1].copy()
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
T["risk_d"] = (T.entry - T.stop).abs() * T.shares
B = pd.read_parquet(S / f"cov/days/{D}/bars.parquet"); B.index = pd.to_datetime(B.index, utc=True).tz_convert(TZ)
def ser(s):
    g = B[B.symbol == s]; tp = (g.high + g.low + g.close) / 3; vw = (tp * g.volume).cumsum() / g.volume.cumsum()
    return (g.close / g.open.iloc[0] - 1) * 100, g.close, vw
spy_fo, spy_c, spy_vw = ser("SPY"); q, qc, _ = ser("QQQ"); iw, _, _ = ser("IWM")
OUT = []
def row(h, n, r, note, ins=False): OUT.append(dict(date=D, hyp=h, n=int(n), avgR=None if r is None or r != r else round(float(r), 4), note=note, in_sample=ins)); print(h, "|", n, "|", r, "|", note)
# L7 / L8 (asof = last 1-min bar at or before the fill minute, as forward_l78.py)
T["q"] = T.nt.dt.floor("min").map(lambda t: q.asof(t)); T["i"] = T.nt.dt.floor("min").map(lambda t: iw.asof(t))
sh = T[T.side == -1]; a = sh[sh.q >= 0.75]; b = sh[(sh.q < 0.75) & sh.strategy.isin(a.strategy)]
row("L7", len(a), a.radj.mean() if len(a) else None,
    f"class A shorts with QQQ >= +0.75% (max {q.max():+.2f}% {q.idxmax():%H:%M}); same-setup B n {len(b)} avg {b.radj.mean() if len(b) else float('nan'):+.3f}; A - B {(a.radj.mean() - b.radj.mean()) if len(a) and len(b) else float('nan'):+.3f}")
fb = T[T.strategy.str.match(r"CWT14-failbrk-.*-long$")]; a8, b8 = fb[fb.i <= -0.5], fb[fb.i > -0.5]
row("L8", len(a8), a8.radj.mean() if len(a8) else None,
    f"IWM min {iw.min():+.2f}% -> class A {len(a8)}; class B n {len(b8)} avg {b8.radj.mean():+.3f} (" + "; ".join(f"{k} {len(g)} {g.radj.mean():+.3f}" for k, g in b8.groupby('acct')) + ")")
# gate1 / comp15 / burst1 / L1-L3 / L6 tallied by nightly1109 (not redone)
# burst2-openloss-latch4 (all 7 accounts): realised + 5-min MTM per setup at each entry; latch at <= -4R
PX = {s: g_.close for s, g_ in B.groupby("symbol")}
def mtm(r, t):
    p = PX.get(r.symbol)
    if p is None: return 0.0
    t5 = t.floor("5min"); x = p[(p.index < t5)]
    return 0.0 if x.empty else float((x.iloc[-1] - r.entry) * r.side * r.shares / r.risk_d)
res = []
for a in ("p", "t1", "t2", "gy", "gen", "ex1", "ll"):
    for s, g_ in T[T.acct == a].sort_values("nt").groupby("strategy"):
        lat = None
        for _, r in g_.iterrows():
            prior = g_[g_.nt < r.nt]
            if lat is None and len(prior):
                closed = prior[prior.et <= r.nt]; op_ = prior[prior.et > r.nt]
                v = closed.radj.sum() + sum(mtm(x, r.nt) for _, x in op_.iterrows())
                if v <= -4: lat = r.nt
            if lat is not None: res.append(dict(acct=a, setup=s, latch=lat, R=r.radj))
X = pd.DataFrame(res)
if len(X):
    by = X.groupby(["acct", "setup"]).agg(t=("latch", "first"), n=("R", "size"), R=("R", "sum"))
    row("burst2-openloss-latch4", len(X), X.R.mean(), "shadow-latched setup-days " + str(len(by)) + "; blocked taken entries " +
        "; ".join(f"{a}:{s[:28]} {r.t:%H:%M} {r.n} {r.R:+.1f}R" for (a, s), r in by.iterrows()) + f"; shadow - live = {-X.R.sum():+.2f}R (taken entries only; live-latch-blocked what-ifs not re-priced)")
else:
    row("burst2-openloss-latch4", 0, None, "no setup reached -4R open + closed before a later entry")
# L9
s10 = spy_fo.asof(pd.Timestamp(f"{D} 09:59", tz=TZ))
row("swing1105-L9", 0, None, f"not qualifying (SPY {s10:+.2f}% at 09:59)")
# burst2-flush-gate-short + swing1106-L10: per (acct, setup, side) count prior same-side entries within 15 min; QQQ 30-min return
qc30 = (qc / qc.shift(30) - 1) * 100
T["q30"] = T.nt.dt.floor("min").map(lambda t: qc30.asof(t - pd.Timedelta("1min")))
T = T.sort_values("nt"); T["k15"] = 0
for _, g_ in T.groupby(["acct", "strategy", "side"]):
    ts = g_.nt.tolist()
    T.loc[g_.index, "k15"] = [sum(1 for u in ts[:i] if t_ - u <= pd.Timedelta("15min")) for i, t_ in enumerate(ts)]
fg = T[(T.side == -1) & (T.k15 >= 2) & (T.q30 <= -0.4)]
row("burst2-flush-gate-short", len(fg), fg.radj.mean() if len(fg) else None, f"blocked {len(fg)} shorts {fg.radj.sum():+.2f}R -> gate gain {-fg.radj.sum():+.2f}R (QQQ 30-min min {qc30.min():+.2f}%); " + "; ".join(f"{a} {len(x)} {-x.radj.sum():+.1f}" for a, x in fg.groupby('acct')))
A10 = T[(T.k15 >= 2) & (((T.side == -1) & (T.q30 <= -0.4)) | ((T.side == 1) & (T.q30 >= 0.4)))].copy()
def scalp(r):
    p = B[B.symbol == r.symbol]; p = p[(p.index > r.nt.floor("min")) & (p.index < pd.Timestamp(f"{D} 15:55", tz=TZ))]
    Ru = abs(r.entry - r.stop); tg = r.entry + r.side * 0.5 * Ru; cost = r.r_multiple - r.radj
    for h, l in zip(p.high, p.low):
        if (l <= r.stop) if r.side == 1 else (h >= r.stop): return -1.0 - cost
        if (h >= tg) if r.side == 1 else (l <= tg): return 0.5 - cost
    return ((p.close.iloc[-1] - r.entry) * r.side / Ru if len(p) else 0.0) - cost
A10["sc"] = [scalp(r) for r in A10.itertuples()] if len(A10) else []
row("swing1106-L10", len(A10), A10.radj.mean() if len(A10) else None, (f"class A {len(A10)} (long {(A10.side == 1).sum()}, short {(A10.side == -1).sum()}): live {A10.radj.sum():+.2f}R vs +0.5R scalp {A10.sc.sum():+.2f}R -> scalp - live {A10.sc.sum() - A10.radj.sum():+.2f}R; " + "; ".join(f"{a} {len(x)} {x.sc.sum() - x.radj.sum():+.1f}" for a, x in A10.groupby('acct'))) if len(A10) else f"no class A (QQQ 30-min range {qc30.min():+.2f}..{qc30.max():+.2f}%)")
pd.DataFrame(OUT).to_csv(HERE / "forward_1109.csv", index=False)
print("Educational only - not financial advice.")
