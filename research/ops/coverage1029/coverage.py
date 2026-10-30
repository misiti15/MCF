"""Poll coverage of Primary for a session, from the live poll log (polls/<day>/*.jsonl.gz on origin/mcf-data, read with
mcf.execution.runner.read_poll_log) plus universe.csv / earnings/<day>.json / status.json.
Reports: universe and tiers, earnings exclusions (by report date, and among ADV >= $95M names), watchlist size, symbols
with bars per poll, poll count and gaps, and whether every 5-minute lab decision minute (bucket 4th minute 09:49..14:59)
was polled. Usage: python coverage.py <scratch> <day> [...]   (inputs from fetch.py)  -> <scratch>/out/cov_<day>.json
Educational only - not financial advice."""
import json, sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/user/MCF")
from mcf.execution.runner import read_poll_log

S = Path(sys.argv[1])
uni = pd.read_csv(S / "p" / "universe.csv")
for D in sys.argv[2:]:
    r = read_poll_log(str(S / "p" / "polls"), D)
    out = {"day": D, "polls": len(r)}
    if not r:
        print(D, "no poll log"); continue
    t = pd.to_datetime([f"{D} {x['t']}" for x in r])
    gaps = pd.Series(t).diff().dt.total_seconds()
    sess = [x for x in r if "09:35" <= x["t"] <= "15:55"]
    out.update(first=r[0]["t"], last=r[-1]["t"], watchlist=sorted({x["n"] for x in r}),
               max_gap_s=float(gaps.max()), gaps_over_90s=int((gaps > 90).sum()),
               got_min=min(x["got"] for x in sess), got_median=float(pd.Series([x["got"] for x in sess]).median()),
               fresh_median=float(pd.Series([x["fresh"] for x in sess]).median()),
               none_max=max(x["none_n"] for x in sess), none_last=r[-1]["none"][:10],
               poll_s_median=float(pd.Series([x["ms"] for x in sess]).median() / 1000))
    # decision minutes: bucket 4th minute 09:49 .. 14:59; polled when a poll's last completed minute (lm) equals it
    lms = {x["lm"] for x in r}
    dm = [f"{h:02d}:{m:02d}" for h in range(9, 15) for m in range(4, 60, 5) if "09:49" <= f"{h:02d}:{m:02d}" <= "14:59"]
    out["decision_minutes"] = len(dm); out["decision_minutes_polled"] = sum(m in lms for m in dm)
    out["decision_minutes_missed"] = [m for m in dm if m not in lms]
    ep = S / "p" / "earnings" / f"{D}.json"
    if ep.exists():
        eb = json.loads(ep.read_text())
        es = set(eb["symbols"])
        out["earnings"] = {"excluded": len(es), "source": eb.get("source"), "complete": eb.get("complete"),
                           "window_days": eb.get("days"),
                           "by_report_date": dict(sorted(Counter(min(v) for v in eb["symbols"].values()).items()))}
        if D == sys.argv[2] or D == "2026-10-29":
            big = set(uni.loc[uni.adv >= 95e6, "symbol"])
            out["earnings"].update(universe=len(uni), universe_tiers=uni.tier.value_counts().to_dict(),
                                   adv95_names=len(big), adv95_excluded=len(big & es),
                                   extended_excluded=int(uni[uni.symbol.isin(es)].tier.eq("extended").sum()),
                                   watchlist_tiers=uni[~uni.symbol.isin(es)].tier.value_counts().to_dict())
    (S / "out").mkdir(exist_ok=True)
    (S / "out" / f"cov_{D}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "none_last"}))
