"""bdi1104: append tonight's backlog entries (idempotent by id). Usage: python research/bdi/1104/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-04 (research/bdi/1104/NOTES.md)"
NEW = [
 {"id": "qr1-1104-opening-range-trend-day-flag", "title": "QR1/QR2 (QDAY): SPY 09:30-10:00 range / 20-session mean daily range as an ex-ante day-type flag; counter-index entries only on narrow-open days",
  "category": "setup", "status": "parked", "configs_tried": 4, "module": "research/bdi/1104/qr1.py;research/bdi/1104/qr2.py",
  "hypothesis": "QD1 left the QDAY search needing an ex-ante quiet-day predictor (>= +15 points over the quiet-close base). The opening half hour's range relative to recent daily ranges may tell range days from trend days at 10:00.",
  "tags": ["bdi1104", "bdi", "qday", "quiet-day", "both-sides", "index", "setup"],
  "notes": "Tested 2026-11-04 (SPY 1-min 431 open sessions; 2-year trade lists of 95 lab setups; locked block absent). QR1 3 configs, 0 pass: low OR ratio & flat 10:00 +17.6 pts train / +5.5 valid; high OR -6.9 / -9.6; flat & prior quiet -19.2 / +14.3. Descriptive: quiet-close share by OR quintile 40/40/41/24/20% - a WIDE open flags a trend day (usable as a sizing input, SIZE1), a narrow one does not flag a quiet day. QR2 (counter-index entries >= 10:05 on narrow-open days, 1 config): n 137,302 -0.059R, excess +0.007R t 0.40 - fails; wide-open control -0.058R; quiet days +0.11R either way. Educational only - not financial advice."},
 {"id": "swing1104-L7-strong-qqq-short-guard", "title": "Swing lead L7: skip lab shorts when QQQ is >= +0.75% from its open at entry",
  "category": "filter", "status": "parked", "configs_tried": 1, "module": "research/bdi/1104/leads_bt.py",
  "hypothesis": "11-04 Primary gave back 16.4R after 12:16 re-loading shorts into QQQ's second leg; T2 / Gen shorts lost into QQQ +1.3..+1.9% in the morning; 11-03 the short book lost while SPY climbed.",
  "tags": ["bdi1104", "bdi", "swing", "filter", "index", "qday"],
  "notes": "2 years, 47 short lab setups: class A n 77,766 raw -0.017R vs B -0.067R, excess +0.031R (train -0.003 / valid +0.052, t 1.03) - fails (wrong sign); keeps 83% of trades / 79% of top-decile winners. Up days A -0.060 vs B -0.258R: shorting on up days is the loss, not the QQQ bar. Forward bar in research/bdi/swings/hypotheses.jsonl. Educational only - not financial advice."},
 {"id": "swing1104-L8-failbrk-long-iwm-down-guard", "title": "Swing lead L8: skip CWT14 failed-breakdown longs when IWM is <= -0.50% from its open at entry",
  "category": "filter", "status": "parked", "configs_tried": 1, "module": "research/bdi/1104/leads_bt.py", "parent": "nightly-1104-pdl-longs-smallcap-rotation",
  "hypothesis": "11-04 T2 CWT14-pdl-p10 pair -15.6R and GY CWT14-orl-p05 -24R while IWM fell to -1.01% (11:27); T2 11-03 pdl-p10 losses in the morning dip.",
  "tags": ["bdi1104", "bdi", "swing", "filter", "small-cap"],
  "notes": "2 years, 8 CWT14 failbrk long setups: class A n 130,363 raw -0.088R vs B -0.093R, excess +0.004R (t 0.27) - fails; keeps 77% of trades / 74% of top-decile winners (filter-creep bar missed). The pool itself is -0.092R/trade on 2 years. Educational only - not financial advice."},
 {"id": "gybp-1104-graveyard-cap12-replay", "title": "GY-BP replay (owner 11-03): Graveyard per-setup cap 25 -> 12 to spread buying power",
  "category": "risk", "status": "parked", "configs_tried": 2, "module": "research/bdi/1104/gybp.py",
  "hypothesis": "A lower per-setup cap frees buying power so later setups still get turns (playing time).",
  "tags": ["bdi1104", "bdi", "graveyard", "playing-time", "buying-power", "queue"],
  "notes": "Journal replay 10-21..11-04 (11 sessions): cap 12 drops 850 lots (-118.4R), funds 53 of 101 BP rejects (+6.1R) but only 1 setup without a live trade that session; net +124.5R comes from trading fewer lots of a -0.132R book (dropped -0.139R vs kept -0.130R: not selective). Cap 18 +34.3R, 0 new setups. Pre-registered question (>= 5 new setups get turns) fails. Educational only - not financial advice."},
 {"id": "mh-1104-group-gapup-fade-open", "title": "Move Hunt: opening group gap-up fade (>= 3 same-industry names gap >= +1.5% with rsi5 >= 90 at 09:35-09:45 -> short the group)",
  "category": "setup", "status": "idea", "configs_tried": 0, "module": None,
  "hypothesis": "11-04: 11 of the 25 biggest short moves were banks (COF, SYF, C, ALLY, HBAN, USB, KEY, PNC, PNFP, RF, FITB) that gapped +1.6..+3.1% with rsi5 88-100 and faded 1.6-3.0 ATR from 09:35-09:45; the book was long KEY / HBAN (-6.5R). Banks also moved together on 11-03.",
  "tags": ["bdi1104", "move-hunt", "open", "group", "short", "setup"],
  "test_needed": "Needs the 09:35-09:45 open frame (research timeofday open frame; the history2y frames start at 09:50) and an industry map; costs in, BAR90, locked block excluded.",
  "notes": "Not tested 2026-11-04 (open frame not rebuilt). Distinct from MH4 / COMBO1 (peer-laggard catch-up): this is the leaders' own fade. Educational only - not financial advice."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
n = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-04", "source": SRC, "variant": None}); e.setdefault("parent", None); rows.append(e); n += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(n, "added;", len(rows), "entries")
