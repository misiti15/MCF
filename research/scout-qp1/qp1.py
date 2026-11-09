"""QP1 scorer (see PLAN.md, pre-registered). Usage: python qp1.py <bars_dir>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
DIR = sys.argv[1]; LK0, LK1, SPLIT = "2024-11-01", "2025-02-28", "2025-09-01"
SECT = "XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()
def load(s):
    b = pd.read_csv(f"{DIR}/{s}.csv"); b["t"] = pd.to_datetime(b.t, utc=True).dt.tz_convert("America/New_York")
    b["d"] = b.t.dt.strftime("%Y-%m-%d"); b = b[~((b.d >= LK0) & (b.d <= LK1))]
    b["m"] = b.t.dt.hour * 60 + b.t.dt.minute; return b
def day(b):
    g = b.groupby("d"); o = g.o.first(); first_m = g.m.first()
    e = b[b.m <= 595]; c955 = e.groupby("d").c.last(); n_e = e.groupby("d").size()
    D = pd.DataFrame({"o": o, "c": g.c.last(), "c955": c955, "n_e": n_e, "first_m": first_m, "n": g.size()})
    return D, e
S, se = day(load("SPY"))
S = S[(S.n >= 70) & (S.first_m == 570) & (S.n_e == 6)]
S["oc"] = (S.c / S.o - 1) * 100; S["fo10"] = (S.c955 / S.o - 1) * 100
x = se.merge(S[["o"]].rename(columns={"o": "so"}), left_on="d", right_index=True); x["side"] = np.sign(x.c - x.so)
S["cross"] = x.groupby("d").side.apply(lambda v: int((v.replace(0, np.nan).ffill().diff().fillna(0) != 0).sum()))
F = {}
for s in SECT + ["VXX"]:
    D, _ = day(load(s)); F[s] = (D.c955 / D.o - 1) * 100
F = pd.DataFrame(F).reindex(S.index)
S["disp"] = F[SECT].std(axis=1, skipna=True); S["vxx10"] = F["VXX"]
S["disp_ratio"] = S.disp / S.disp.shift(1).rolling(20, min_periods=15).mean()
S["quiet"] = S.oc.abs() <= 0.25
S = S.dropna(subset=["disp_ratio", "vxx10"]); S["split"] = np.where(S.index < SPLIT, "train", "valid")
tr = S[S.split == "train"]; d1 = tr.disp_ratio.quantile(1 / 3); v1 = tr.vxx10.quantile(1 / 3)
small = S.fo10.abs() <= 0.25
C = {"Q1 low disp_ratio & |fo10|<=0.25": (S.disp_ratio <= d1) & small,
     "Q2 low vxx10 & |fo10|<=0.25": (S.vxx10 <= v1) & small,
     "Q3 cross>=2 & |fo10|<=0.25": (S.cross >= 2) & small,
     "Q4 Q1 & Q2": (S.disp_ratio <= d1) & (S.vxx10 <= v1) & small}
print(f"sessions {len(S)} ({S.index.min()}..{S.index.max()}; locked block absent) train {len(tr)} / valid {len(S)-len(tr)}; "
      f"cuts (train): disp_ratio {d1:.3f}, vxx10 {v1:+.3f}%")
for s in ("train", "valid"):
    z = S[S.split == s]; print(f"  base {s}: quiet {z.quiet.mean():.1%}; |fo10|<=0.25 alone -> quiet {z.quiet[small[S.split==s]].mean():.1%} on {small[S.split==s].mean():.0%} of days")
R = []
for k, f in C.items():
    r = {"config": k}
    for s in ("train", "valid"):
        z = S[S.split == s]; fx = f[S.split == s]
        r[f"{s}_n"] = int(fx.sum()); r[f"{s}_share"] = round(fx.mean(), 3); r[f"{s}_quiet"] = round(z.quiet[fx].mean(), 3)
        r[f"{s}_lift"] = round((z.quiet[fx].mean() - z.quiet.mean()) * 100, 1)
        r[f"{s}_up"] = round((z.oc[fx] > 0.25).mean(), 3); r[f"{s}_dn"] = round((z.oc[fx] < -0.25).mean(), 3)
    r["PASS"] = all(r[f"{s}_lift"] >= 15 and r[f"{s}_share"] >= 0.10 for s in ("train", "valid")); R.append(r)
R = pd.DataFrame(R); pd.set_option("display.width", 250); print(R.to_string(index=False))
print("\ndescriptive (not a test): quiet share by quintile, all open days")
for col in ("disp_ratio", "vxx10", "cross"):
    q = pd.qcut(S[col].rank(method="first"), 5, labels=False)
    print(f"  {col}: " + " ".join(f"{S.quiet[q == i].mean():.0%}" for i in range(5)) +
          f"   |oc| mean by quintile: " + " ".join(f"{S.oc.abs()[q == i].mean():.2f}" for i in range(5)))
live = S[S.index >= "2026-10-06"]
print(f"\nlive window 2026-10-06.. ({len(live)} sessions): quiet {live.quiet.mean():.0%}; " +
      "; ".join(f"{k.split()[0]} flags {int(f[live.index].sum())} -> quiet {live.quiet[f[live.index]].mean():.0%}" for k, f in C.items()))
R.to_csv(f"{__import__("os").path.dirname(__import__("os").path.abspath(__file__))}/qp1_results.csv", index=False); S.to_csv(f"{__import__("os").path.dirname(__import__("os").path.abspath(__file__))}/qp1_days.csv")
print("Educational only - not financial advice.")
