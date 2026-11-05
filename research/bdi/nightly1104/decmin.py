"""Decision-minute coverage and the run 190 (41455594297) -> standby 195 (41507490469) handover gap, 2026-11-04 (needs polls.py run first).
A 5-minute decision minute = a poll whose expected bar index exp % 5 == 0 (exp 0..380 -> 77 per session).
Usage: python decmin.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-n1104"); sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-n1104/research/ops")
from mcf.execution.runner import read_poll_log
from pollspeed1022_missed import BRANCHES
S = Path(sys.argv[1]); D = "2026-11-04"; out = []
for acct, b in BRANCHES.items():
    r = read_poll_log(str(S / "polls" / b), D)
    exps = {x["exp"] for x in r}
    dec = set(range(0, 381, 5)); miss = sorted(dec - exps)
    t = pd.to_datetime([x["t"] for x in r], format="%H:%M:%S")
    g = (t[1:] - t[:-1]).total_seconds() / 60
    # handover (run 190 job end -> standby 195, ~14:31 ET): the longest gap that starts 14:26-14:36
    w = [(t[i], t[i + 1], g[i]) for i in range(len(g)) if "14:26" <= t[i].strftime("%H:%M") <= "14:36"]
    h = max(w, key=lambda z: z[2]) if w else None
    out.append(dict(acct=acct, polls=len(r), pct_of_384=round(100 * len(r) / 384, 1), decision_polled=f"{len(dec) - len(miss)}/{len(dec)}",
                    decision_missed=",".join(f"{9 + (30 + m) // 60:02d}:{(30 + m) % 60:02d}" for m in miss) or "-",
                    handover=f"{h[0].strftime('%H:%M:%S')} -> {h[1].strftime('%H:%M:%S')} ({h[2]:.1f} min)" if h else "-",
                    exp_mod5=pd.Series([x["exp"] % 5 for x in r]).value_counts().sort_index().to_dict()))
txt = pd.DataFrame(out).to_string(index=False)
open(Path(__file__).resolve().parent / "decmin_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
