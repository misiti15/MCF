"""Journal refresh with Skeptic's timing guard (skeptic-20261115-0150-1; Lead lead-20261114-2100-1), for REPS3 / ICCSET scoring.
For each account branch: fetch, take journal.db from origin/<branch>, and ASSERT its last commit (a) is ON OR AFTER the given
session date (ET) - a later commit means the session is closed and final - and, when it is ON the session day, (b) was made at
or after the exchange close - 5 min (15:55 ET, or 12:55 on half days; a midday push or dead EOD job is not final; Skeptic skeptic-20261115-2350-1) and (c) is >= 10 minutes old.
Refuses a session date after today (ET) (Skeptic's FWDCAL hole, skeptic-20261115-2150-1). score.py must then be given the same
session as --end, so later (possibly partial) sessions are never counted. Prints per-account last-commit time and that session's trade count.
Refuses (exit 1) if any account fails, unless --allow-stale. Read-only: never pushes; writes only into <out dir>.
    python3 -I refresh.py <MCF repo> <out dir> <session YYYY-MM-DD> [--allow-stale]     |  python3 -I refresh.py x x --selftest        Educational only - not financial advice."""
import sys, os, subprocess, sqlite3, datetime as dt
from zoneinfo import ZoneInfo
REPO, OUT, SESSION = sys.argv[1], sys.argv[2], sys.argv[3]; ALLOW = "--allow-stale" in sys.argv
BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-explore1", "mcf-data-livelab", "mcf-data-testingd",
      "mcf-data-testinge", "mcf-data-testingf", "mcf-data-gen", "mcf-data-graveyard"]
ET = ZoneInfo("America/New_York"); now = dt.datetime.now(dt.timezone.utc); bad = []
def flat_hm(session):
    """the EOD-final threshold = exchange close - 5 min, from live's own calendar (MCF mcf/execution/market_calendar.py; one source,
    Skeptic skeptic-20261127-0155-1): 15:55 normally, 12:55 on NYSE half days (2026-11-27, 2026-12-24). No network (use_http=False)."""
    sys.path.insert(0, os.environ.get("MCF_REPO", "/home/user/MCF"))
    from mcf.execution.market_calendar import session_close
    c = session_close(session, use_http=False); m = c.hour * 60 + c.minute - 5
    return (m // 60) * 100 + m % 60
def check(commit_local_date, session, age_min, today, commit_hm=1600):
    """returns '' if final, else the failure reason (unit-tested in --selftest). commit_hm = last commit time ET as HHMM."""
    if session > today: return "session is in the future"
    if commit_local_date < session: return "date"
    if commit_local_date == session and commit_hm < flat_hm(session): return "pre-close commit"   # a midday push is not the EOD journal
    if commit_local_date == session and age_min < 10: return "age"
    return ""
if SESSION == "--selftest":
    T = "2026-11-18"
    assert check("2026-11-18", "2026-11-19", 50, T) == "session is in the future"
    assert check("2026-11-17", "2026-11-18", 600, T) == "date"
    assert check("2026-11-18", "2026-11-18", 5, T) == "age"
    assert check("2026-11-18", "2026-11-18", 30, T) == ""
    assert check("2026-11-19", "2026-11-18", 1, "2026-11-19") == ""          # later commit: the session is final
    assert check("2026-11-18", "2026-11-18", 300, T, 1100) == "pre-close commit"   # dead EOD job / midday push
    assert check("2026-11-18", "2026-11-18", 30, T, 1556) == ""
    assert flat_hm("2026-11-18") == 1555 and flat_hm("2026-11-27") == 1255 and flat_hm("2026-12-24") == 1255
    assert check("2026-11-27", "2026-11-27", 30, "2026-11-27", 1302) == ""            # half day: 13:02 commit is final
    assert check("2026-11-27", "2026-11-27", 300, "2026-11-27", 1230) == "pre-close commit"
    print("selftest ok"); sys.exit(0)
os.makedirs(OUT, exist_ok=True)
g = lambda *a: subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
for b in BR:
    if g("fetch", "-q", "origin", b).returncode != 0:
        print(f"{b:20s} branch not found (skipped)"); continue
    ts = g("log", "-1", "--format=%cI", f"origin/{b}", "--", "journal.db").stdout.strip()
    if not ts: print(f"{b:20s} no journal.db"); continue
    t = dt.datetime.fromisoformat(ts); age = (now - t).total_seconds() / 60; local = t.astimezone(ET)
    why = check(local.strftime("%Y-%m-%d"), SESSION, age, now.astimezone(ET).strftime("%Y-%m-%d"), local.hour * 100 + local.minute)
    data = subprocess.run(["git", "-C", REPO, "show", f"origin/{b}:journal.db"], capture_output=True).stdout
    p = f"{OUT}/{b}.db"; open(p, "wb").write(data)
    n = sqlite3.connect(p).execute("select count(*) from trades where date = ?", (SESSION,)).fetchone()[0]
    flag = "" if not why else f"  <-- FAIL ({why})"
    print(f"{b:20s} last journal commit {local:%Y-%m-%d %H:%M} ET ({age:5.0f} min ago)  trades on {SESSION}: {n}{flag}")
    if flag: bad.append(b)
if bad and not ALLOW:
    print(f"REFUSED: {len(bad)} account(s) not final for {SESSION}: {bad}. Re-run later (after 16:30 ET).", file=sys.stderr); sys.exit(1)
print("journals ready" + (" (stale accounts allowed)" if bad else "") + ". Educational only - not financial advice.")
