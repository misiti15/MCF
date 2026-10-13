"""Primary MF/NS/RW6G1 4-session review (2026-10-08, 09, 12, 13), journal real trades (run 1). Educational only."""
import sys, json, sqlite3, pandas as pd
S = sys.argv[1]
DAYS = ["2026-10-08", "2026-10-09", "2026-10-12", "2026-10-13"]
SET = ["MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell", "MF3-open-flowsell-rsi5hi", "MF4-h40-open-flowsell",
       "MF5-flowsell-vwapup-rsi5hi", "NS1-rsidip-rsi5pop-long", "NS2-sma50break-overbought-short", "NS3-failed-vwap-reclaim-short",
       "NS4-pm-vwap-reclaim-oversold-short", "NS5-sma50-flush-oversold-long", "RW6G1-ns2-up3-vwap2sd-short"]
val = json.load(open("/home/user/MCF/config/validation.json"))["setups"]
sc = {r["setup"]: r for r in json.load(open(f"{S}/p/reports/scorecard.json"))["setups"]}
t = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(f"{S}/p/journal.db"))
t = t[t.date.isin(DAYS)]
t1 = pd.read_sql("select * from trades where run_id=1 and date in ('2026-10-12','2026-10-13')", sqlite3.connect(f"{S}/t1/journal.db"))
rows = []
for s in SET:
    g = t[t.strategy == s]; v = val.get(s, {})
    f = t1[t1.strategy == s + "-FD"]
    rows.append(dict(setup=s, n=len(g), win=round(100 * (g.pnl > 0).mean()) if len(g) else None,
                     avgR=round(g.r_multiple.mean(), 3) if len(g) else None, pnl=round(g.pnl.sum(), 2),
                     **{d[5:]: round(g[g.date == d].pnl.sum(), 2) if (g.date == d).any() else None for d in DAYS},
                     exp_aprjun=v.get("apr_jun_exp_r"), exp_2y=v.get("two_year_exp_r"), exp_scorecard=sc.get(s, {}).get("expected_r"),
                     verdict=sc.get(s, {}).get("verdict"), fd_n=len(f), fd_avgR=round(f.r_multiple.mean(), 3) if len(f) else None,
                     fd_pnl=round(f.pnl.sum(), 2)))
o = pd.DataFrame(rows); o.to_csv("mfns_4session.csv", index=False)
pd.set_option("display.width", 250); print(o.to_string())
print("primary by day:", t.groupby("date").pnl.agg(["size", "sum"]).round(2).to_dict())
print("MF/NS/RW6G1 total", len(t[t.strategy.isin(SET)]), round(t[t.strategy.isin(SET)].pnl.sum(), 2))
