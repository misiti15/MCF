"""Render the W2-promodemo tables from SCORES.csv. Usage: python tables.py <SCORES.csv>. Educational only."""
import sys, pandas as pd, numpy as np
R = pd.read_csv(sys.argv[1]); R["name"] = R.name.str.split(" — ").str[0]
def f(x, d=2, pct=False, sign=True):
    if pd.isna(x): return "n/a"
    return f"{x*100:.0f}%" if pct else (f"{x:+.{d}f}" if sign else f"{x:.{d}f}")
def share(x): return "n/a (total ≤ 0)" if pd.isna(x) else (f"{x*100:.0f}% `1 day`" if x >= 0.5 else f"{x*100:.0f}%")
def row(x, p="", corr="corr_primary", extra=()):
    return ("| " + " | ".join([f"{x['name']} (`{x.setup}`)", x.account + (" (guest)" if x.tag == "GY-BENCH guest" else ""),
            str(int(x[p+"n"]) if not pd.isna(x[p+"n"]) else 0), f"{int(x[p+'sessions']) if not pd.isna(x[p+'sessions']) else 0}/{int(x.active_days)}",
            f(x[p+"totR"], 1), f(x[p+"avgR"], 3), f(x[p+"wo_best"], 3), share(x[p+"best_share"]), f(x[p+"green_pct"], pct=True),
            f(x[p+"last5R"], 1), f(x.get(p+"fit_avg"), 3) + " / " + f(x.get(p+"check_avg"), 3), f(x[corr], 2)] + [e(x) for e in extra]) + " |")
H = "| Setup | Account | Trades | Traded / active sessions | Total R | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to Primary |"
S = "|---|---|---|---|---|---|---|---|---|---|---|---|"
out = []
P = R[R.acct == "primary"]
out += ["### (a) Primary — record since current admission", H.replace("Corr to Primary", "Corr to rest of Primary") + " Admitted | -10R demotion? |", S + "---|---|"]
for _, x in P.iterrows(): out.append(row(x, corr="corr_rest_primary", extra=(lambda x: x.prim_since, lambda x: "yes" if x.demote10 else "no")))
OD = R[R.acct == "testing"].copy()
out += ["", "### (b) On Deck — record outside Primary (dedup), C3-BAR2 as proposed", H + " C3-BAR2 fails | Since On Deck admission (n / R) |", S + "---|---|"]
for _, x in OD.sort_values("totR", ascending=False).iterrows():
    out.append(row(x, extra=(lambda x: x.bar2_fails or "PASS", lambda x: f"{int(x.cur_n) if not pd.isna(x.cur_n) else 0} / {f(x.cur_totR,1)}")))
A = R[~R.acct.isin(["primary", "testing", "graveyard"])]
c = A[(A.n >= 10) & ((A.wo_best > 0) | ((A.totR > 5) & (A.t >= 1.5)))].sort_values("wo_best", ascending=False)
out += ["", "### (c) Arena → On Deck — closest to C3-BAR2 (n ≥ 10 and avg R w/o best day > 0, or total > +5R with t ≥ 1.5)", H + " C3-BAR2 fails | t |", S + "---|---|"]
for _, x in c.iterrows(): out.append(row(x, extra=(lambda x: x.bar2_fails or "PASS", lambda x: f(x.t, 2))))
E = R[R.exit100].sort_values("totR")
out += ["", "### (d) Arena → Graveyard — meets C3-EXIT100 (≥ 100 trades, ≥ 15 active days, avg ≤ −0.05, w/o best day ≤ 0)", H + " Current account n / avg |", S + "---|"]
for _, x in E.iterrows(): out.append(row(x, extra=(lambda x: f"{int(x.cur_n) if not pd.isna(x.cur_n) else 0} / {f(x.cur_avgR,3)}",)))
out.append(f"\nEXIT100 total: {len(E)} setups, {E.n.sum():.0f} trades, {E.totR.sum():+.1f}R.")
W = A[(A.n >= 50) & (A.avgR <= -0.05) & (A.wo_best <= 0) & ~A.exit100].sort_values("totR")
out += ["", "### (d2) Not yet EXIT100 (n 50-99 or < 15 active days) but on the same path — watch, no proposal", H, S]
for _, x in W.iterrows(): out.append(row(x))
G = R[R.acct == "graveyard"].copy()
out += ["", "### (e) Graveyard → arena (GY-LIFE graduation: ≥ 15 Graveyard days, ≥ 30 Graveyard trades, whole w/o best day > 0, best day < 50%)",
        "| Setup | Status | Whole n / sessions | Whole avg R | Whole w/o best | Whole best share | GY n / days | GY avg R | GY w/o best | GY best share | GY last-5 R | Corr to Primary | Graduates? |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for _, x in G.sort_values("gy_wo_best", ascending=False).iterrows():
    out.append(f"| {x['name']} (`{x.setup}`) | {x.tag if isinstance(x.tag, str) else 'active'} | {0 if pd.isna(x.all_n) else int(x.all_n)} / {0 if pd.isna(x.all_sessions) else int(x.all_sessions)} | {f(x.all_avgR,3)} | {f(x.all_wo_best,3)} | {share(x.all_best_share)} | "
               f"{int(x.gy_n) if not pd.isna(x.gy_n) else 0} / {int(x.gy_sessions) if not pd.isna(x.gy_sessions) else 0} | {f(x.gy_avgR,3)} | {f(x.gy_wo_best,3)} | "
               f"{share(x.gy_best_share)} | {f(x.gy_last5R,1)} | {f(x.corr_primary,2)} | {'yes' if x.gy_grad else 'no'} |")
print("\n".join(out))
