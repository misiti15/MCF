"""Forward tallies 2026-11-06 for the swing-autopsy shadows not already tallied by nightly1106 (which did L1 / L2 / L3 /
L6, FLOW1, latch1103 category shadow): swing1104-L7, swing1104-L8, gate1-checkpoint-gate (+ comp15-w60-early readings),
burst1-openloss-latch3 (first forward session), swing1105-L9 (qualifying check), fb1-flush-chase-shadow (needs the 11-06
frames), burst2-* and swing1106-L10 (in-sample on 11-06; forward from 11-09). Journals run 1, all 7 accounts, R =
pnl_adj / $ risk. Same rules as research/bdi/1105/forward_l78.py / forward_gate1.py.
Usage: python forward_1106.py <scratch mh1106>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"; D = "2026-11-06"
T = pd.read_csv(HERE.parent / "nightly1106" / "trades.csv"); T = T[T.run_id == 1].copy()
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
# GATE1 checkpoints + comp15 W60 readings
cl = B.pivot_table(index=B.index, columns="symbol", values="close"); op = B.pivot_table(index=B.index, columns="symbol", values="open").iloc[0]
br = (cl.ffill() > op).mean(axis=1)
def votes(t):
    v = [np.sign(spy_fo.asof(t)), np.sign(spy_c.asof(t) - spy_vw.asof(t)), np.sign(br.asof(t) - 0.5)]
    s3 = [np.sign(spy_fo.asof(t)), np.sign(q.asof(t)), np.sign(iw.asof(t))]; v.append(s3[0] if len(set(s3)) == 1 else 0)
    return int(sum(v))
st = {}; lines = []
for cp in pd.date_range(f"{D} 11:00", f"{D} 15:30", freq="30min", tz=TZ):
    t = cp - pd.Timedelta("1min")
    up = spy_fo.asof(t) >= 0.15 and spy_c.asof(t) > spy_vw.asof(t) and br.asof(t) >= 0.5 and (q.asof(t) > 0 or iw.asof(t) > 0)
    dn = spy_fo.asof(t) <= -0.15 and spy_c.asof(t) < spy_vw.asof(t) and br.asof(t) <= 0.5 and (q.asof(t) < 0 or iw.asof(t) < 0)
    st[cp] = "UP" if up else "DOWN" if dn else "MIXED"
    lines.append(f"{cp:%H:%M} {st[cp]} (SPY {spy_fo.asof(t):+.2f}%, {'>' if spy_c.asof(t) > spy_vw.asof(t) else '<'}VWAP, breadth {br.asof(t):.2f}, QQQ {q.asof(t):+.2f}, IWM {iw.asof(t):+.2f})")
print("GATE1 states: " + "; ".join(lines))
A = pd.read_csv(HERE.parent / "gate1" / "shadow_rule_setup_states.csv"); allow = {r.setup: set(str(r.allowed).split(",")) for _, r in A.iterrows()}
cps = sorted(st); state = lambda t: (lambda k: st[k[-1]] if k else None)([c for c in cps if c <= t])
T["state"] = T.nt.map(state)
g = T[T.strategy.isin(allow) & T.state.notna()].copy(); g["drop"] = [s not in allow[k] for k, s in zip(g.strategy, g.state)]
d_, k_ = g[g["drop"]], g[~g["drop"]]
row("gate1-checkpoint-gate", len(g), None, f"states {'/'.join(sorted(set(st.values())))}; dropped {len(d_)} entries {d_.radj.sum():+.2f}R (avg {d_.radj.mean() if len(d_) else float('nan'):+.3f}), kept {len(k_)} {k_.radj.sum():+.2f}R -> gated - ungated {-d_.radj.sum():+.2f}R (" + "; ".join(f"{a} {-x.radj.sum():+.1f}" for a, x in d_.groupby('acct')) + ")")
w = []
marks = list(pd.date_range(f"{D} 09:45", f"{D} 15:45", freq="15min", tz=TZ)); V = {m: votes(m - pd.Timedelta("1min")) for m in marks}
first = None
for i, m in enumerate(marks):
    last60 = [x for x in marks[max(0, i - 4):i + 1]]
    fo_s = {np.sign(spy_fo.asof(x - pd.Timedelta("1min"))) for x in last60}
    conf = abs(V[m]) >= 4 and len(fo_s) == 1 and len(last60) >= 2
    if conf and first is None: first = (m, np.sign(V[m]))
    w.append(f"{m:%H:%M} {V[m]:+d}{'c' if conf else ''}")
flips = sum(1 for a_, b_ in zip(marks, marks[1:]) if np.sign(V[a_]) * np.sign(V[b_]) < 0)
row("comp15-w60-early", 1, None, (f"first confirmed {first[0]:%H:%M} {'UP' if first[1] > 0 else 'DOWN'}" if first else "never confirmed") + f"; side flips {flips}; readings " + " ".join(w))
# burst1-openloss-latch3 (Primary + Graveyard): realised + 5-min MTM per setup at each entry; latch at <= -3R
PX = {s: g_.close for s, g_ in B.groupby("symbol")}
def mtm(r, t):
    p = PX.get(r.symbol)
    if p is None: return 0.0
    t5 = t.floor("5min"); x = p[(p.index < t5)]
    return 0.0 if x.empty else float((x.iloc[-1] - r.entry) * r.side * r.shares / r.risk_d)
res = []
for a in ("p", "gy"):
    for s, g_ in T[T.acct == a].sort_values("nt").groupby("strategy"):
        lat = None
        for _, r in g_.iterrows():
            prior = g_[g_.nt < r.nt]
            if lat is None and len(prior):
                closed = prior[prior.et <= r.nt]; op_ = prior[prior.et > r.nt]
                v = closed.radj.sum() + sum(mtm(x, r.nt) for _, x in op_.iterrows())
                if v <= -3: lat = r.nt
            if lat is not None: res.append(dict(acct=a, setup=s, latch=lat, R=r.radj))
X = pd.DataFrame(res)
if len(X):
    by = X.groupby(["acct", "setup"]).agg(t=("latch", "first"), n=("R", "size"), R=("R", "sum"))
    row("burst1-openloss-latch3", len(X), X.R.mean(), "shadow-latched setup-days " + str(len(by)) + "; blocked taken entries " +
        "; ".join(f"{a}:{s[:28]} {r.t:%H:%M} {r.n} {r.R:+.1f}R" for (a, s), r in by.iterrows()) + f"; shadow - live = {-X.R.sum():+.2f}R (taken entries only; live-latch-blocked what-ifs not re-priced)")
else:
    row("burst1-openloss-latch3", 0, None, "no setup reached -3R open + closed before a later entry")
# L9
s10 = spy_fo.asof(pd.Timestamp(f"{D} 09:59", tz=TZ))
row("swing1105-L9", 0, None, f"not qualifying (SPY {s10:+.2f}% at 09:59)")
pd.DataFrame(OUT).to_csv(HERE / "forward_1106.csv", index=False)
print("Educational only - not financial advice.")
