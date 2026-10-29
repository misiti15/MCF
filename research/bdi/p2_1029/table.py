"""Per-setup summary table for NOTES.md from diag_table.csv + results.csv. Best variant = highest day-clustered t among
grid configs that raise trades/month >= 25% (all configs if none does). Educational only - not financial advice."""
import pandas as pd
D = pd.read_csv("diag_table.csv"); R = pd.read_csv("results.csv")
P = R[R.config == "P"].set_index("setup"); c = R[R.config != "P"]
for s in D.setup:
    g = c[c.setup == s]; f = g[g.trades_month_change >= 25]
    b = (f if len(f) else g).sort_values("t", ascending=False).iloc[0]; d = D[D.setup == s].iloc[0]
    print(f"| {s} | {d.acct} | {d.tier} | {d.sessions} | {d.live_trades} ({d.live_per_sess}) | {d.live_sigdays_per_sess} | "
          f"{d.bt_per_day} | {d.live_over_bt} | {d.binding} | {b.config} | {P.loc[s, 'per_month']} → {b.per_month} "
          f"({b.trades_month_change:+.0f}%) | {P.loc[s, 'avgR']:+.3f} → {b.avgR:+.3f} | {b.t:.2f} | {b.failed} |")
