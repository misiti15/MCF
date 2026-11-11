"""nightly1111: add 11-11 evidence to two existing backlog ideas (no new id; status unchanged).
Usage: python research/bdi/nightly1111/add_backlog.py   Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[2] / "backlog.jsonl"
EV = {
 "nightly-1110-latch-closes-open-lots": ("11-11 (2nd data point, nightly1111/latchgross_out.txt, live gross-R latch basis): Primary L3-gap-slope-fromopen-FD 13:57, "
   "RW5-FD 14:25, RW3-FD 15:20 latched with 30 lots open; those lots finished -20.86R vs -9.84R marked at the latch minute -> -11.02R lost AFTER the latch "
   "(RW5 -8.19R on 19 lots, RW3 -2.47R, L3 -0.36R; 3 of 3 better if closed), while SPY was flat from each latch to the close (-0.03..-0.29%). "
   "T1 +8.55R, T2 +9.37R, GY +39.68R if closed; 24 setup-days better, 3 worse (GY CWT12-coil-k6-long -15.6R, CWT14-failbrk-orl-p05-lowvol-long -9.5R, "
   "heat_fade_long-FD 0.0: dip-buy longs again). Pattern holds 2 of 2 sessions: fade shorts better closed, dip-buy longs worse."),
 "ecg1-1109-early-compass-momentum-short-gate": ("11-11: compass W60 UP-confirmed from 11:30 (SPY +0.31% -> +0.74% 13:45); Primary shorts entered at/after 11:30: "
   "30 trades -21.33R after costs (of the day's -26.63R); T2 31 -3.04R - nightly1111."),
}
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
for r in rows:
    if r["id"] in EV and "nightly1111" not in (r.get("notes") or "") and "11-11 (2nd" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + " | " + EV[r["id"]]
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(len(rows), "rows")
