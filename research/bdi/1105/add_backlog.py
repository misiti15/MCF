"""bdi1105: append tonight's backlog entries (idempotent by id). Usage: python research/bdi/1105/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-05 (research/bdi/1105/NOTES.md)"
NEW = [
 {"id": "fb1-1105-sell-bounce-not-flush", "title": "FB1: sell the bounce, not the flush - guard lab shorts entered within 0.15 ATR of the session low (stock / QQQ), mirror for longs at the HOD, and a bounce-sold boost (RW3 trait)",
  "category": "filter", "status": "parked", "configs_tried": 4, "module": "research/bdi/1105/fb1.py", "parent": "burst1",
  "hypothesis": "BURST1: MF4 / MF2 / RW3S / GEN-261022-09 shorted 11:00-11:10 at the QQQ low and were stopped together in the +1.4% bounce; RW3 waited for an RSI(5) pop and sold the bounce (+16.5R).",
  "tags": ["bdi1105", "bdi", "burst", "filter", "short", "both-sides"],
  "notes": "2 years (95 lab setups, 1.17M trades, costs in, locked block absent), 4 configs, 0 pass (bar 1.89 for 6 tonight): FB1-S class A (13.8% of shorts) excess +0.013R t 1.03 (train +0.023 / valid +0.009); FB1-I (QQQ at its low & <= -0.5%) +0.005R t 0.27; FB1-L +0.000R; FB1-B bounce-sold +0.003R t 0.17. Distance from the low carries no information on its own across families (11 helped / 13 harmed). Day-type split: index-flush shorts lose on quiet (-0.134 ex) and up (-0.200 ex) days, win on down days (+0.061) - hindsight, not usable at entry. Educational only - not financial advice."},
 {"id": "swing1105-L9-deep-down-morning-long-veto", "title": "Swing lead L9: skip lab long entries at/after 10:00 on days SPY <= -1.00% from its open at 10:00",
  "category": "filter", "status": "parked", "configs_tried": 1, "module": "research/bdi/1105/l9_bt.py",
  "hypothesis": "11-05 (SPY -1.48% at 10:00, -4.2% o-c): every account's longs lost (GY -122R, T2 -60R, Gen -62R, Ex1 -17R).",
  "tags": ["bdi1105", "bdi", "swing", "filter", "long", "qday"],
  "notes": "2 years: only 2 qualifying open-month days (both rebounded, SPY o-c mean +0.24%); class A n 2,801 excess +0.229R (wrong sign) t 1.09 - fails, not powered. Forward shadow in research/bdi/swings/hypotheses.jsonl (needs >= 3 qualifying days). Educational only - not financial advice."},
 {"id": "mh-1105-gapup-vs-falling-tape-0950", "title": "Move Hunt precursor: short names that gapped >= +0.8% and are below their open at 09:50 while SPY <= -0.50% from open",
  "category": "setup", "status": "parked", "configs_tried": 1, "module": "research/bdi/1105/mh_p1.py", "parent": "mh-1104-group-gapup-fade-open",
  "hypothesis": "Move Hunt 11-04 / 11-05: gap-up banks faded against a weak tape (11-05 C, JPM, MS, BNY, WFC, BLK, STT, PNC, HBAN, KEY, AMP 1.7-2.7 ATR from 09:50 to 10:53).",
  "tags": ["bdi1105", "move-hunt", "open", "short", "setup", "banks"],
  "notes": "2 years (lab label r_short_t1s1, $0.01/share costs): n 1,766 on only 9 days, avg -0.046R (t -0.34) - fails; excess over same-day 09:50 shorts +0.183R (t 2.19) and down days +0.099R, but quiet -0.63 / up -0.62R; TRAIN +0.173 / VALID -0.184. Relative edge on a crash morning only. Educational only - not financial advice."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}; n = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-05", "source": SRC, "variant": None}); e.setdefault("parent", None); rows.append(e); n += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(n, "added;", len(rows), "entries")
