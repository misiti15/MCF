"""Broker position qty (status.json snapshots, from the broker positions call) vs journal open-lot shares at the same time.
Every status commit of 2026-10-14. Educational only."""
import subprocess, json, sys, pandas as pd
acct, branch = sys.argv[1], sys.argv[2]
T = pd.read_csv("trades.csv"); T = T[T.acct == acct].copy()
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
log = subprocess.run(["git", "-C", "/home/user/MCF", "log", "--format=%h", "--since=2026-10-14T13:30:00Z", "origin/" + branch, "--", "status.json"],
                     capture_output=True, text=True).stdout.split()
out = []
for h in reversed(log):
    d = json.loads(subprocess.run(["git", "-C", "/home/user/MCF", "show", h + ":status.json"], capture_output=True, text=True).stdout)
    if d.get("session_date") != "2026-10-14" or d.get("phase") != "trading":
        continue
    ts = pd.Timestamp(d["asof"]).tz_convert("America/New_York")
    broker = {p["symbol"]: float(p["qty"]) for p in d["positions"]}
    o = T[(T.nt <= ts) & (T.et > ts)]
    jr = (o.side * o.shares).groupby(o.symbol).sum().to_dict()
    for s in set(broker) | set(jr):
        b, j = broker.get(s, 0.0), float(jr.get(s, 0))
        if abs(b - j) > 1e-6:
            out.append(dict(snap=d["asof_et"], ts=ts, symbol=s, broker=b, journal=j))
o = pd.DataFrame(out)
print(acct, "snapshots with a mismatch:", o["snap"].nunique() if len(o) else 0, "rows:", len(o))
if len(o):
    # mismatches that persist >= 2 consecutive snapshots (fill-timing noise is 1 snapshot: status and fills are seconds apart)
    g = o.groupby("symbol").agg(first=("snap", "min"), last=("snap", "max"), n=("snap", "size"), broker=("broker", "first"), journal=("journal", "first"))
    print(g[g.n >= 2].to_string())
    o.to_csv(f"qtycheck_{acct}.csv", index=False)
