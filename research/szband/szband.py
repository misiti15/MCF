"""SZBAND (PLAN.md, frozen 2026-11-10 15:20 ET): calibration of a prior-60-day size band for SPY moves from mark T.
    python szband.py <dir with SPY.csv from research/scout-qp1/fetch.py>       Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
LK0, LK1, S1, S2 = "2024-11-01", "2025-02-28", "2025-09-30", "2026-10-06"
b = pd.read_csv(f"{sys.argv[1]}/SPY.csv"); b["t"] = pd.to_datetime(b.t, utc=True).dt.tz_convert("America/New_York")
b["d"] = b.t.dt.strftime("%Y-%m-%d"); b = b[~((b.d >= LK0) & (b.d <= LK1))]
b["m"] = b.t.dt.hour * 60 + b.t.dt.minute
C = b.pivot_table(index="d", columns="m", values="c"); H = b.pivot_table(index="d", columns="m", values="h"); L = b.pivot_table(index="d", columns="m", values="l")
full = [m for m in range(570, 960, 5)]
C = C.reindex(columns=full); H = H.reindex(columns=full); L = L.reindex(columns=full)
ok = C.notna().all(axis=1); C, H, L = C[ok], H[ok], L[ok]
assert not ((C.index >= LK0) & (C.index <= LK1)).any()
days = list(C.index); print(f"sessions {len(days)} ({days[0]}..{days[-1]}), locked block absent")
end_of = lambda T: T - 5                                      # bar starting at T-5 ends at T
MARKS = list(range(585, 916, 15)); HZ = {"30m": 30, "60m": 60, "90m": 90, "close": None}
seg = pd.Series(np.cumsum([0] + [int((pd.Timestamp(days[i]) - pd.Timestamp(days[i - 1])).days > 5) for i in range(1, len(days))]), index=days)
rows = []
for T in MARKS:
    cT = C[end_of(T)]
    rng_so_far = (H.loc[:, :end_of(T)].max(axis=1) - L.loc[:, :end_of(T)].min(axis=1)) / C[570 - 0 if False else 570]   # range so far / 09:30 bar close
    for hz, h in HZ.items():
        if h is not None and T + h > 955: continue
        c2 = C[955] if h is None else C[end_of(T + h)]
        mv = (c2 / cT - 1).abs() * 100
        for i, d in enumerate(days):
            prior = [x for x in days[max(0, i - 60):i] if seg[x] == seg[d]]
            if len(prior) < 40: continue
            pm = mv[prior]; q50, q80 = float(pm.median()), float(pm.quantile(.8))
            rr = float(rng_so_far[prior].median())
            rows.append(dict(d=d, T=T, hz=hz, mv=float(mv[d]), q50=q50, q80=q80, volr=float(rng_so_far[d]) / rr if rr > 0 else np.nan))
X = pd.DataFrame(rows)
X["in80"] = X.mv <= X.q80; X["in50"] = X.mv <= X.q50
X["split"] = np.where(X.d <= S1, "TRAIN", np.where(X.d < S2, "VALID", "FWD"))
X["volt"] = X.groupby(["T", "hz"]).volr.transform(lambda v: pd.qcut(v.rank(method="first"), 3, labels=["low", "mid", "high"]))
def cov(g, col):
    dm = g.groupby("d")[col].mean(); return round(dm.mean(), 3), round(dm.std(ddof=1) / np.sqrt(len(dm)), 3), len(dm)
print("\ncoverage of the prior-60-day band (target: <= 80th pct 0.80, <= median 0.50); mean, day-clustered se, days")
for hz in HZ:
    for sp in ("TRAIN", "VALID", "FWD"):
        g = X[(X.hz == hz) & (X.split == sp)]
        if not len(g): continue
        a, sa, n = cov(g, "in80"); m, sm, _ = cov(g, "in50")
        vt = " ".join(f"{v}: {g[g.volt == v].in80.mean():.2f}" for v in ("low", "mid", "high"))
        print(f"  {hz:5s} {sp:5s} in80 {a:.3f} (se {sa:.3f})  in50 {m:.3f} (se {sm:.3f})  days {n} | in80 by today's vol tercile {vt}")
print("\nby mark (ALL splits, 60m): in80 " + " ".join(f"{T // 60:02d}:{T % 60:02d} {X[(X.hz == '60m') & (X['T'] == T)].in80.mean():.2f}" for T in MARKS if (X[(X.hz == '60m') & (X['T'] == T)]).size))
ex = X[(X.split == "FWD") & (X.hz == "60m")].groupby("T")[["q50", "q80"]].median()
print("\nexample band (FWD median, 60m, % of price): " + "; ".join(f"{T // 60:02d}:{T % 60:02d} med {r.q50:.2f}% / p80 {r.q80:.2f}%" for T, r in ex.iterrows()))
X.to_csv(f"{sys.argv[1]}/szband_rows.csv.gz", index=False)
print("Educational only - not financial advice.")
