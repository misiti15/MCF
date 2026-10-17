"""Summarise rework.csv. Educational only - not financial advice."""
from load import *
R = pd.read_csv(S / "rework.csv")
VS = ["actual", "sim_base", "stop0.5", "stop0.75", "time30", "time60", "time120", "be@0.5", "scale@0.5+BE", "no_target_hold", "target2x", "trail1R", "opposite[HINDSIGHT]"]
for v in VS: R[v + "_c"] = R[v] - R.cost
R["wk"] = np.where(R.date.isin(LAST), "lastwk", "thiswk")
print("fidelity: corr(actual, sim_base)=%.2f, mean actual %.3f sim %.3f, same sign %.0f%%" % (R.actual.corr(R.sim_base), R.actual.mean(), R.sim_base.mean(), 100 * (np.sign(R.actual) == np.sign(R.sim_base)).mean()))
print("\n== exit variants, avg R after cost (n trades)")
t = R.groupby(["acct", "wk"])[[v + "_c" for v in VS]].mean().round(3); t.columns = VS
t["n"] = R.groupby(["acct", "wk"]).size(); print(t.T.to_string())
print("\nall pooled by day (avg R after cost):"); t = R.groupby("date")[[v + "_c" for v in VS]].mean().round(3); t.columns = VS; print(t.to_string())
print("\nvariant beats sim_base on how many of 9 days:")
for v in VS[2:]: print(f"  {v:22s}", int((R.groupby('date')[v + '_c'].mean() > R.groupby('date')['sim_base_c'].mean()).sum()))
# day-class filter at decision time (SPY % from open at entry minute)
print("\n== decision-time day-class skip (SPY from open at entry); kept-trade sum R after cost per account, base=all")
for a in ACC:
    q = R[R.acct == a]; base = q.sim_base_c.sum()
    out = [f"base {base:.1f} (n{len(q)})"]
    for x in (0.15, 0.3, 0.5):
        k = ~(((q.side == 1) & (q.spy_at_entry < -x)) | ((q.side == -1) & (q.spy_at_entry > x)))
        out.append(f"skip-against>{x}: {q[k].sim_base_c.sum():.1f} (n{k.sum()})")
    print(ACC[a], " | ".join(out))
print("\nlong vs short by SPY-at-entry bucket, all accounts (avg actual R after cost, n)")
R["spyb"] = pd.cut(R.spy_at_entry, [-9, -0.5, -0.15, 0.15, 0.5, 9])
print(R.groupby(["spyb", "side"]).actual_c.agg(["mean", "size"]).round(3).unstack().to_string())
print("\nby entry hour (avg actual R after cost, n)"); print(R.groupby("hour").actual_c.agg(["mean", "size"]).round(3).T.to_string())
print("\nnever worked (MFE<0.2R) share of losers:", round(((R.actual < 0) & (R.mfe < 0.2)).sum() / (R.actual < 0).sum(), 3),
      " losers that reached +0.5R first:", int(((R.actual < 0) & (R.mfe >= 0.5)).sum()), "of", int((R.actual < 0).sum()))
print("median MFE winners %.2f, losers MAE median %.2f" % (R[R.actual > 0].mfe.median(), R[R.actual < 0].mae.median()))
# per-setup: which variant best, and does it hold in both halves (first vs second half of each setup's trades by date)
print("\n== per setup (n>=30) best exit variant; sim_base vs best, and best also wins in both halves?")
rows = []
for s, g in R.groupby("strategy"):
    if len(g) < 30: continue
    g = g.sort_values("date"); h = len(g) // 2
    m = {v: g[v + "_c"].mean() for v in VS[1:-1]}
    b = max(m, key=m.get)
    both = (g.iloc[:h][b + "_c"].mean() > g.iloc[:h].sim_base_c.mean()) and (g.iloc[h:][b + "_c"].mean() > g.iloc[h:].sim_base_c.mean())
    rows.append((s, len(g), round(m["sim_base"], 3), b, round(m[b], 3), both, round(g["opposite[HINDSIGHT]_c"].mean(), 3)))
print(pd.DataFrame(rows, columns=["setup", "n", "base", "best", "best_R", "both_halves", "opp[H]"]).sort_values("best_R", ascending=False).to_string(index=False))
