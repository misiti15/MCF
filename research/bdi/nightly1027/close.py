"""Session-close check, 2026-10-27, for all 5 accounts (no broker access: status.json, journal.db, EOD report, scorecard,
intraday snapshots and the new poll-input log polls/<date>/ on each data branch).
Usage: python close.py <scratch> <repo>   Educational only - not financial advice."""
import sys, json, sqlite3, subprocess, gzip, io
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); REPO = sys.argv[2]; D = "2026-10-27"
BR = dict(p="mcf-data", t1="mcf-data-testing", t2="mcf-data-testing2", gy="mcf-data-graveyard", gen="mcf-data-gen")
git = lambda *a: subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout
rows = []
for a, b in BR.items():
    st = json.load(open(S / a / "status.json")); h = st["health"]; td = st["today"]
    c = sqlite3.connect(S / a / "journal.db")
    jt = c.execute("select count(*) from trades where date=? and run_id=1", (D,)).fetchone()[0]
    jo = c.execute("select count(*) from trades where date=? and run_id=1 and exit is null", (D,)).fetchone()[0]
    sub = c.execute("select count(*) from signals where day=? and run_id=1 and status='submitted'", (D,)).fetchone()[0]
    rep = pd.read_csv(S / a / "reports" / f"{D}.csv")
    sc = json.load(open(S / a / "reports" / "scorecard.json"))
    log = git("log", "--format=%ci %s", f"origin/{b}", "--since=2026-10-27T13:00:00Z")
    done = [l for l in log.splitlines() if "done" in l or "EOD report" in l]
    pl = git("ls-tree", "-r", "-l", f"origin/{b}", f"polls/{D}").splitlines()
    nbytes = sum(int(l.split()[3]) for l in pl)
    # poll-log content: rows (bars) in the first and last file
    def nrows(path):
        raw = subprocess.run(["git", "-C", REPO, "show", f"origin/{b}:{path}"], capture_output=True).stdout
        return sum(1 for _ in gzip.open(io.BytesIO(raw), "rt"))
    first, last = pl[0].split()[-1], pl[-1].split()[-1]
    sig_polls = c.execute("select count(distinct substr(ts,1,16)) from signals where day=? and run_id=1", (D,)).fetchone()[0]
    rows.append(dict(acct=a, phase=st["phase"], positions=len(st["positions"]), open_pos=td.get("open_positions"),
                     flatten_failed=h["flatten_failed"], partial=h["partial_lots"], outages=h["data_outages"], polls=h["polls"],
                     last_bar=h["last_bar"], journal=jt, journal_open=jo, submitted=sub, report=len(rep), status_trades=td["trades"],
                     pnl_adj_status=td["pnl_adj"], pnl_adj_report=round(rep.pnl_adj.sum(), 2) if "pnl_adj" in rep else None,
                     scorecard_asof=sc.get("asof") or sc.get("generated") or "?", pushes=" | ".join(done[:4]),
                     poll_files=len(pl), poll_bytes=nbytes, poll_first=first.split("/")[-1], poll_last=last.split("/")[-1],
                     poll_rows_first=nrows(first), poll_rows_last=nrows(last)))
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 200)
R = pd.DataFrame(rows)
txt = R.T.to_string()
open(Path(__file__).resolve().parent / "close_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
