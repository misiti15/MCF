"""OPENDRIVE_1127: live entry slippage (journals, read-only git show) by minute of day -> early-entry surcharge base E.
Educational only - not financial advice."""
import subprocess, sqlite3, tempfile, pandas as pd, numpy as np, os
BR = ["mcf-data","mcf-data-testing","mcf-data-testing2","mcf-data-gen","mcf-data-graveyard","mcf-data-livelab","mcf-data-explore1","mcf-data-testingd","mcf-data-testinge","mcf-data-testingf"]
P=[]
for br in BR:
    raw = subprocess.run(["git","-C","/home/user/MCF","show",f"origin/{br}:journal.db"],capture_output=True).stdout
    if not raw: print("no",br); continue
    with tempfile.NamedTemporaryFile(suffix=".db",dir=".") as f:
        f.write(raw); f.flush(); del raw
        con=sqlite3.connect(f.name)
        x=pd.read_sql("SELECT date, entry_time, signal_time, side, entry, slip_bps FROM trades WHERE entry_time IS NOT NULL",con)
        con.close()
    x["acct"]=br; P.append(x)
t = pd.concat(P); print("live entries", len(t))
# --- summary: entry slip by minute-of-day (signed bps, positive = cost) ---
t["et"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["m"] = t.et.dt.hour * 60 + t.et.dt.minute
t = t[t.slip_bps.notna() & (t.slip_bps.abs() < 200)]
print("earliest live entry minute (ET, minutes after midnight):", int(t.m.min()), "entries before 09:49:", int((t.m < 589).sum()))
for a, b in ((589, 600), (600, 630), (630, 720), (720, 960)):
    s = t[(t.m >= a) & (t.m < b)].slip_bps
    print(f"{a//60:02d}:{a%60:02d}-{b//60:02d}:{b%60:02d} n {len(s)} mean {s.mean():.2f} bp (se {s.sem():.2f}) median {s.median():.2f} mean|.| {s.abs().mean():.1f}")
s = t[(t.m >= 589) & (t.m < 600)].slip_bps
print("E (09:49-09:59 mean signed slip + 1 bp fees) =", round(float(s.mean()) + 1.0, 2), "bp")
