"""Re-run the broker-vs-journal quantity check for an earlier session on the RESTATED journal (journal.db as of 10-15 EOD).
Every status.json commit of that session; prints symbols whose mismatch persists >= 3 snapshots. Educational only."""
import subprocess, json, sys, sqlite3, pandas as pd
S, acct, branch, day = sys.argv[1:5]
T = pd.read_sql(f"select * from trades where run_id=1 and date='{day}'", sqlite3.connect(f"{S}/{acct}/journal.db"))
for c in ("entry_time", "exit_time"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed")
G = ["git", "-C", "/home/user/MCF"]
log = subprocess.run(G + ["log", "--format=%h", f"--since={day}T13:00:00Z", f"--until={day}T21:00:00Z", "origin/" + branch, "--", "status.json"],
                     capture_output=True, text=True).stdout.split()
out = []
for h in reversed(log):
    d = json.loads(subprocess.run(G + ["show", h + ":status.json"], capture_output=True, text=True).stdout)
    if d.get("session_date") != day or d.get("phase") != "trading":
        continue
    ts = pd.Timestamp(d["asof"])
    broker = {p["symbol"]: float(p["qty"]) for p in d["positions"]}
    o = T[(T.entry_time <= ts) & (T.exit_time > ts)]
    jr = (o.side * o.shares).groupby(o.symbol).sum().to_dict()
    for s in set(broker) | set(jr):
        b, j = broker.get(s, 0.0), float(jr.get(s, 0))
        if abs(b - j) > 1e-6:
            out.append(dict(snap=d["asof_et"], symbol=s, broker=b, journal=j))
o = pd.DataFrame(out)
print(acct, day, "snapshots:", len(log), "mismatch rows:", len(o))
if len(o):
    g = o.groupby("symbol").agg(first=("snap", "min"), last=("snap", "max"), n=("snap", "size"), broker=("broker", "last"), journal=("journal", "last"))
    print(g[g.n >= 3].to_string())
