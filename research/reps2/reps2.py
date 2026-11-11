"""REPS2 - setup-days per SLOT (descriptive, 0 configs; follows REPS1b's 'more setups live is the lever that scales').
Per live setup (10-20..11-10, 7 accounts): live setup-day rate = sessions with >= 1 submitted signal / active sessions
(active = first..last session the setup logged any signal, so the rate is an upper bound for setups added mid-window).
Related to the lab rate (research/bdi/playingtime/expected_rates.json, trades/day, 5 busiest days out) by
p_day = 1 - exp(-a x lab_per_day), a fitted by least squares on setups with both. Gives setup-days/week a slot yields.
    python -I reps2.py <signals.csv.gz> <MCF root>          Educational only - not financial advice."""
import sys, json, numpy as np, pandas as pd
S = pd.read_csv(sys.argv[1]); ROOT = sys.argv[2]
days = sorted(S.day.unique()); di = {d: i for i, d in enumerate(days)}
g = S.groupby("strategy")
R = pd.DataFrame({"first": g.day.min(), "last": g.day.max(),
                  "sub_days": S[S.status == "submitted"].groupby("strategy").day.nunique(),
                  "sig_days": g.day.nunique(), "acct": g.acct.agg(lambda a: "/".join(sorted(set(x.replace("mcf-data-", "").replace("mcf-data", "primary") for x in a))))})
R["sub_days"] = R.sub_days.fillna(0)
R["active"] = R["first"].map(di).rsub(R["last"].map(di)) + 1
R["p_day"] = R.sub_days / R.active; R["sig_p"] = R.sig_days / R.active
lab = {k: v["per_day"] for k, v in json.load(open(f"{ROOT}/research/bdi/playingtime/expected_rates.json"))["setups"].items()}
R["lab_per_day"] = R.index.map(lab)
F = R.dropna(subset=["lab_per_day"]); F = F[F.active >= 5]
grid = np.linspace(0.001, 2, 2000); sse = [((F.p_day - (1 - np.exp(-a * F.lab_per_day))) ** 2).sum() for a in grid]
a = grid[int(np.argmin(sse))]
print(f"setups with live signals: {len(R)}; with a lab rate and >= 5 active sessions: {len(F)}; fitted a = {a:.3f} "
      f"(p_day = 1 - exp(-a x lab trades/day)); corr(p_day, fit) {np.corrcoef(F.p_day, 1 - np.exp(-a * F.lab_per_day))[0, 1]:.2f}")
print("slot yield (setup-days/week) by lab trades/day: " + ", ".join(f"{x}/day -> {5 * (1 - np.exp(-a * x)):.1f}" for x in (0.1, 0.3, 1, 3, 10)))
A = R[R.active >= 5]
print(f"\nlive setups with >= 5 active sessions: {len(A)}; setup-days/week per slot: median {5 * A.p_day.median():.2f}, "
      f"mean {5 * A.p_day.mean():.2f}; slots yielding < 1/week: {int((A.p_day < 0.2).sum())}; >= 3/week: {int((A.p_day >= 0.6).sum())}")
A = A.assign(acct1=A.acct.str.split("/").str[0])
print("\nby account (setups, median setup-days/week per slot, total setup-days/week):")
for ac, x in A.groupby("acct1"):
    print(f"   {ac:10s} {len(x):3d}  median {5 * x.p_day.median():.2f}  total {5 * x.p_day.sum():.1f}")
print(f"\nsignal days vs submitted days (how much of a slot's yield blocks take away): median sig_p {A.sig_p.median():.2f} vs p_day {A.p_day.median():.2f}")
pd.set_option("display.width", 200)
cols = ["acct", "active", "sig_days", "sub_days", "p_day", "lab_per_day"]
print("\nlowest-yield slots (p_day < 0.2, >= 8 active sessions), by account:")
print(A[(A.p_day < 0.2) & (A.active >= 8)].sort_values(["acct", "p_day"])[cols].round(2).to_string())
R.to_csv("reps2_setups.csv")
print("Educational only - not financial advice.")
