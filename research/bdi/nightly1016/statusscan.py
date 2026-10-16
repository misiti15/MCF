"""Every status.json commit of a branch for one session: equity, broker positions, phase. Read-only (git). Educational only."""
import subprocess, json, sys, pandas as pd
branch, day, out = sys.argv[1], sys.argv[2], sys.argv[3]
G = ["git", "-C", "/home/user/MCF"]
log = subprocess.run(G + ["log", "--format=%h %cI", "--since=" + day + "T00:00:00Z", "origin/" + branch, "--", "status.json"],
                     capture_output=True, text=True).stdout.split("\n")
rows = []
for line in reversed([l for l in log if l]):
    h = line.split()[0]
    try:
        d = json.loads(subprocess.run(G + ["show", h + ":status.json"], capture_output=True, text=True).stdout)
    except Exception:
        continue
    rows.append(dict(commit=h, asof=d.get("asof"), asof_et=d.get("asof_et"), session=d.get("session_date"), phase=d.get("phase"),
                     equity=d.get("account", {}).get("equity"), today_pnl=d.get("today", {}).get("pnl"),
                     n_pos=len(d.get("positions") or []),
                     positions=json.dumps({p["symbol"]: float(p["qty"]) for p in d.get("positions") or []}),
                     polls=d.get("health", {}).get("polls"), gate=json.dumps(d.get("health", {}).get("split_tape_gate"))))
o = pd.DataFrame(rows); o.to_csv(out, index=False)
print(o[["asof_et", "session", "phase", "equity", "today_pnl", "n_pos", "polls"]].to_string())
