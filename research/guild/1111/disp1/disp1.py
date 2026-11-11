"""DISP1 scorer — frozen plan research/disp1/PLAN.md (one look). Educational only - not financial advice.
    python -I disp1.py <hodsep data dir with m5.csv.gz, daily.csv.gz>"""
import sys, numpy as np, pandas as pd
D = sys.argv[1]
ETF = "XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()
m = pd.read_csv(f"{D}/m5.csv.gz")
m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
m = m[(m.hm >= 930) & (m.hm <= 1555)]
dates = sorted(m.date.unique()); FORM, TEST = dates[:10], dates[10:]
print(f"sessions {len(dates)}: formation {FORM[0]}..{FORM[-1]}, test {TEST[0]}..{TEST[-1]} ({len(TEST)})")
# --- sector assignment on formation only (10:00-15:30 bars) ---
f = m[m.date.isin(FORM)].sort_values(["symbol", "t"]).copy()
f["r"] = f.groupby(["symbol", "date"]).c.pct_change()
f = f[(f.hm >= 1000) & (f.hm <= 1530)]
W = f.pivot_table(index=["date", "hm"], columns="symbol", values="r")
E = W[ETF]; names = [s for s in W.columns if s not in ETF + ["SPY"]]
C = pd.DataFrame({e: W[names].corrwith(E[e]) for e in ETF})
sec = C.idxmax(axis=1)[C.max(axis=1) >= 0.40]
print(f"names {len(names)}, assigned a sector (corr >= 0.40): {len(sec)}; per sector: {sec.value_counts().to_dict()}")
# --- ATR% from daily, days < D only ---
d = pd.read_csv(f"{D}/daily.csv.gz"); d["date"] = d.t.str[:10]; d = d.sort_values(["symbol", "date"])
pc = d.groupby("symbol").c.shift(1)
d["tr"] = np.maximum(d.h, pc) - np.minimum(d.l, pc)
d["atrp"] = (d.groupby("symbol").tr.transform(lambda x: x.rolling(14).mean().shift(1)) / pc)
A = d.set_index(["symbol", "date"]).atrp
# --- key prices per symbol-day ---
def at(hm, col):
    x = m[m.hm == hm].set_index(["symbol", "date"])[col]; return x
P = pd.DataFrame({"o930": at(930, "o"), "c945": at(945, "c"), "o950": at(950, "o"), "c1550": at(1550, "c")}).dropna()
P = P.reset_index(); P = P[P.date.isin(TEST)]
P["r20"] = P.c945 / P.o930 - 1; P["ret"] = P.c1550 / P.o950 - 1
X = P.set_index(["symbol", "date"])
funnel = {}
rows = []
for date in TEST:
    for e in ETF:
        if (e, date) not in X.index: continue
        er20, eret = X.loc[(e, date), "r20"], X.loc[(e, date), "ret"]
        spy = X.loc[("SPY", date), "ret"]
        mem = [s for s in sec.index[sec == e] if (s, date) in X.index]
        for s in mem:
            r = X.loc[(s, date)]; a = A.get((s, date), np.nan)
            if not (a > 0) or r.o950 < 5: continue
            rel = (r.r20 - er20) / a
            if abs(rel) < 0.5: continue
            sg = np.sign(rel)
            cost = (0.01 + r.o950 * (2.1e-4 + 4.4e-4)) / r.o950 + (0.01 + r.c1550 * 1e-4) / r.c1550 + 4e-4
            rows.append(dict(date=date, sym=s, etf=e, flat=abs(er20) <= 0.002, s=sg, rel=rel,
                             c_sec=sg * (r.ret - eret) / a, c_spy=sg * (r.ret - spy) / a, cost=cost / a))
R = pd.DataFrame(rows)
# split requirement: at least one event on each side in that sector-day
sides = R.groupby(["date", "etf"]).s.agg(lambda x: (x > 0).any() and (x < 0).any()).rename("split")
R = R.merge(sides, left_on=["date", "etf"], right_index=True)
EV, CT = R[R.flat & R.split], R[~R.flat & R.split]
print(f"member events |rel|>=0.5: {len(R)}; flat-sector & split: {len(EV)} on {EV.date.nunique()} days; control (non-flat, split): {len(CT)}")
def tclu(df, col):
    g = df.groupby("date")[col].mean()
    return g.mean(), (g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 1 else np.nan), len(g)
def wob(df, col, sgn):
    g = df.groupby("date")[col].sum() * sgn; b = g.idxmax(); r = df[df.date != b]
    return sgn * r[col].mean()
def report(df, tag):
    mu, t, nd = tclu(df, "c_sec"); ms, ts, _ = tclu(df, "c_spy")
    print(f"{tag}: n {len(df)}, days {nd}, c_sec {mu:+.3f} ATR (t {t:+.2f}), c_spy {ms:+.3f} (t {ts:+.2f}), "
          f"cost {df.cost.mean():.3f} ATR, follow net {df.c_sec.mean()-df.cost.mean():+.3f}, fade net {-df.c_sec.mean()-df.cost.mean():+.3f}")
    return mu, t, ms, ts
mu, t, ms, ts = report(EV, "EVENTS (flat sector)")
report(CT, "control (non-flat sector)")
for sg, nm in ((1, "up-split members (s=+1)"), (-1, "down-split members (s=-1)")): report(EV[EV.s == sg], f"  {nm}")
print("per sector events:", EV.etf.value_counts().to_dict())
dirn = 1 if mu > 0 else -1
net = dirn * EV.c_sec.mean() - EV.cost.mean()
w = wob(EV, "c_sec", dirn)
legs = [np.sign(EV[EV.s == g].c_sec.mean()) == dirn for g in (1, -1)]
p1 = abs(t) >= 2.71 and net > 0
p2 = np.sign(w) == dirn and np.sign(ms) == dirn and abs(ts) >= 2
p3 = all(legs)
print(f"\nDIRECTION {'follow' if dirn>0 else 'fade'}: net {net:+.3f} ATR/trade, w/o best day {w:+.3f}; legs same sign {legs}")
print(f"PASS 1 (|t|>=2.71 & net>0): {p1}; PASS 2: {p2}; PASS 3: {p3} -> {'PASS' if p1 and p2 and p3 else 'FAIL - DISP1 closed'}")
print("configs 2, family 94, BAR90 2.71. Educational only - not financial advice.")
