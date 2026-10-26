"""1b coverage check, 2026-10-26: polls per account, longest gap, missed decision bars (OPS-POLL first post-fix session).
Usage: python polls.py <scratch> <repo>  (extracts polls/<date>/ of each data branch into <scratch>/polls/<branch>/)
Expected polls = Primary's count (1-min fetches 09:40-15:55). Educational only - not financial advice."""
import sys, subprocess, json
from pathlib import Path
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/ops")
from mcf.execution.runner import read_poll_log
from pollspeed1022_missed import missed, BRANCHES
S = Path(sys.argv[1]); REPO = sys.argv[2]; D = "2026-10-26"
out = {}
for acct, b in BRANCHES.items():
    d = S / "polls" / b / D; d.mkdir(parents=True, exist_ok=True)
    for l in subprocess.run(["git", "-C", REPO, "ls-tree", "--name-only", f"origin/{b}", f"polls/{D}/"], capture_output=True, text=True).stdout.split():
        (d / Path(l).name).write_bytes(subprocess.run(["git", "-C", REPO, "show", f"origin/{b}:{l}"], capture_output=True).stdout)
    recs = read_poll_log(str(S / "polls" / b), D)
    import pandas as pd
    t = pd.to_datetime([r["t"] for r in recs])
    gaps = (t[1:] - t[:-1]).total_seconds() / 60 if len(t) > 1 else []
    i = int(gaps.argmax()) if len(gaps) else 0
    m = missed(recs)
    out[acct] = dict(polls=len(recs), first=str(t[0].time()), last=str(t[-1].time()), max_gap_min=round(float(gaps.max()), 1),
                     max_gap_at=str(t[i].time()), gaps_over_5=int((gaps > 5).sum()), median_ms=sorted(r.get("ms", 0) for r in recs)[len(recs) // 2],
                     **{k: v for k, v in m.items() if k != "polls"})
ref = out["primary"]["polls"]
for a, v in out.items():
    v["pct_of_primary"] = round(100 * v["polls"] / ref, 1)
txt = json.dumps(out, indent=1)
open(Path(__file__).resolve().parent / "polls_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
