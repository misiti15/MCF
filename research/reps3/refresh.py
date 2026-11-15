"""Journal refresh with Skeptic's timing guard (skeptic-20261115-0150-1; Lead lead-20261114-2100-1), for REPS3 / ICCSET scoring.
For each account branch: fetch, take journal.db from origin/<branch>, and ASSERT its last commit (a) is from the given session date
(ET) and (b) is >= 10 minutes old at run time. Prints per-account last-commit time and that session's trade count.
Refuses (exit 1) if any account fails, unless --allow-stale. Read-only: never pushes; writes only into <out dir>.
    python3 -I refresh.py <MCF repo> <out dir> <session YYYY-MM-DD> [--allow-stale]        Educational only - not financial advice."""
import sys, os, subprocess, sqlite3, datetime as dt
from zoneinfo import ZoneInfo
REPO, OUT, SESSION = sys.argv[1], sys.argv[2], sys.argv[3]; ALLOW = "--allow-stale" in sys.argv
BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-explore1", "mcf-data-livelab", "mcf-data-testingd",
      "mcf-data-testinge", "mcf-data-testingf", "mcf-data-gen", "mcf-data-graveyard"]
ET = ZoneInfo("America/New_York"); now = dt.datetime.now(dt.timezone.utc); os.makedirs(OUT, exist_ok=True); bad = []
g = lambda *a: subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
for b in BR:
    if g("fetch", "-q", "origin", b).returncode != 0:
        print(f"{b:20s} branch not found (skipped)"); continue
    ts = g("log", "-1", "--format=%cI", f"origin/{b}", "--", "journal.db").stdout.strip()
    if not ts: print(f"{b:20s} no journal.db"); continue
    t = dt.datetime.fromisoformat(ts); age = (now - t).total_seconds() / 60; local = t.astimezone(ET)
    ok_date = local.strftime("%Y-%m-%d") == SESSION; ok_age = age >= 10
    data = subprocess.run(["git", "-C", REPO, "show", f"origin/{b}:journal.db"], capture_output=True).stdout
    p = f"{OUT}/{b}.db"; open(p, "wb").write(data)
    n = sqlite3.connect(p).execute("select count(*) from trades where date = ?", (SESSION,)).fetchone()[0]
    flag = "" if (ok_date and ok_age) else "  <-- FAIL (" + ("date " if not ok_date else "") + ("age" if not ok_age else "") + ")"
    print(f"{b:20s} last journal commit {local:%Y-%m-%d %H:%M} ET ({age:5.0f} min ago)  trades on {SESSION}: {n}{flag}")
    if flag: bad.append(b)
if bad and not ALLOW:
    print(f"REFUSED: {len(bad)} account(s) not final for {SESSION}: {bad}. Re-run later (after 16:30 ET).", file=sys.stderr); sys.exit(1)
print("journals ready" + (" (stale accounts allowed)" if bad else "") + ". Educational only - not financial advice.")
