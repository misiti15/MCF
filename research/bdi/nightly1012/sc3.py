import sys, json, sqlite3, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
S = sys.argv[1]
out = []
for a, days in (("p", ["2026-10-08", "2026-10-09", "2026-10-12"]), ("t1", ["2026-10-09", "2026-10-12"]), ("t2", ["2026-10-12"])):
    c = sqlite3.connect(f"{S}/{a}/journal.db")
    T = pd.read_sql(f"select date, strategy, r_multiple, pnl from trades where run_id=1 and date in ({','.join(repr(d) for d in days)})", c)
    sc = json.load(open(f"{S}/{a}/scorecard.json"))
    lb = {r["setup"]: r for r in sc["leaderboard"]}
    st = {r["setup"]: r for r in sc["setups"]}
    for s, g in T.groupby("strategy"):
        row = {"acct": a, "setup": s, "n": len(g), "win%": round(100 * (g.pnl > 0).mean()), "avgR": round(g.r_multiple.mean(), 3), "totR": round(g.r_multiple.sum(), 2), "pnl": round(g.pnl.sum(), 2)}
        for d in days: row[d[5:]] = round(g[g.date == d].pnl.sum(), 1) if (g.date == d).any() else None
        row["exp_r(bt)"] = st.get(s, {}).get("expected_r", lb.get(s, {}).get("expected_r"))
        row["verdict"] = st.get(s, {}).get("verdict", "")
        row["live_now"] = s in json.load(open(f"{S}/{a}/status.json"))["rules"]["strategies"]
        out.append(row)
    tot = T.groupby("date").agg(n=("pnl", "size"), pnl=("pnl", "sum"), avgR=("r_multiple", "mean")).round(3)
    print(a, tot.to_dict("index"))
O = pd.DataFrame(out).sort_values(["acct", "pnl"])
O.to_csv(f"{S}/scorecard3.csv", index=False)
print(O.to_string(index=False))
