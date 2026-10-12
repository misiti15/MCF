import sys, sqlite3, json; import pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
S = sys.argv[1]
T = pd.read_csv(f"{S}/trades_all.csv")
for c in ("entry_time", "exit_time"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
grid = pd.date_range("2026-10-12 09:50", "2026-10-12 15:55", freq="5min", tz="America/New_York")
for a in ("p", "t1", "t2"):
    d = T[T.acct == a]
    op = [((d.entry_time <= g) & (d.exit_time > g)).sum() for g in grid]
    s = pd.Series(op, index=grid.strftime("%H:%M"))
    print(a, "max open", s.max(), "at", s.idxmax(), " 10:45:", s.get("10:45"), " 11:30:", s.get("11:30"), " 13:00:", s.get("13:00"))
    # open by strategy at peak
    g = grid[s.values.argmax()]
    print("  open by setup at peak:", d[(d.entry_time <= g) & (d.exit_time > g)].strategy.value_counts().head(8).to_dict())
    c = sqlite3.connect(f"{S}/{a}/journal.db")
    W = pd.read_sql("select strategy, side, r_multiple, meta, entry_time from trades where date='2026-10-12' and run_id=2", c)
    W["why"] = W.meta.str.extract(r"why=(.*)$")[0].str.replace(r"\d+", "#", regex=True)
    print("  what-if (skipped signals, simulated, no costs):"); print(W.groupby("why").r_multiple.agg(["size", "mean", "sum"]).round(3).to_string())
    if a == "t2":
        sg = pd.read_sql("select strategy, reason, ts from signals where day='2026-10-12' and status='skipped' and reason like 'max positions%'", c)
        print("  cap-skips by setup:", sg.strategy.value_counts().to_dict(), sg.ts.min()[11:16], sg.ts.max()[11:16])
        mp = W[W.why == "max positions for this setup"]
        print(mp.groupby("strategy").r_multiple.agg(["size", "mean"]).round(3).to_string())
        sk = pd.read_sql("select ts, status from signals where day='2026-10-12'", c); sk["m"] = sk.ts.str[11:16]
        print("  signals per 30m:", sk.assign(b=sk.m.str[:4].str.replace(r'(\d\d):(\d)', lambda m: m.group(0), regex=True)).groupby([sk.m.str[:2], "status"]).size().unstack(fill_value=0).to_string())
    # intraday attribution
    rows = [json.loads(l) for l in open(f"{S}/{a}/intraday.jsonl")]
    tot = pd.Series({r["t"]: r["total"] for r in rows})
    tot = tot[~tot.index.duplicated(keep="last")]
    green = tot[tot > 0]
    print(f"  intraday total: min {tot.min()} at {tot.idxmin()}, max {tot.max()} at {tot.idxmax()}, last {tot.iloc[-1]} at {tot.index[-1]}; green points {len(green)}/{len(tot)}",
          ("first green " + green.index[0] + " last green " + green.index[-1]) if len(green) else "never green")
    for key in (tot.idxmax(), tot.idxmin(), tot.index[-1]):
        r = [x for x in rows if x["t"] == key][-1]["by_setup"]
        top = sorted(r.items(), key=lambda kv: kv[1])
        print(f"   @{key}: worst", [(k, v) for k, v in top[:3]], " best", [(k, v) for k, v in top[-3:]])
    # green stretches
    segs = []; cur = None
    for k, v in tot.items():
        if v > 0 and cur is None: cur = k
        if v <= 0 and cur is not None: segs.append((cur, prev)); cur = None
        prev = k
    if cur: segs.append((cur, prev))
    print("  green stretches:", segs)
