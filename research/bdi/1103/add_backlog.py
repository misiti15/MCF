"""bdi1103: append tonight's backlog entries (idempotent by id) and add the 2-year results to the swing1103 lead items.
Usage: python research/bdi/1103/add_backlog.py     Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-03 (research/bdi/1103/NOTES.md)"
NEW = [
 {"id": "combo1-1103-open-scan-laggard-fade", "title": "COMBO1 (owner): top-500 universe + 09:35 mover scan + MH4 peer-laggard catch-up + fade-timing entry at 09:40-09:50, raw or SPY-hedged to 10:30",
  "category": "setup", "status": "parked", "configs_tried": 9, "module": "research/bdi/1103/combo1.py",
  "hypothesis": "The week's small positives (smaller universe cuts cost per R, the 09:35 scan finds movers, laggards of a moving peer group catch up, reversal timing is the book's only positive line) combine into one opening setup that clears costs.",
  "tags": ["bdi1103", "bdi", "setup", "combo1", "move-hunt", "open", "group", "qday", "hedged"],
  "notes": "Tested 2026-11-03 on the timeofday open frame (2 years, locked block absent and dropped from the peer/beta tables, blackout removed, production costs + tod multiplier; hedge leg costed): 9 configs (side x fade on/off x t1s1 / h1030 SPY-hedged + two-sided book). 0 pass BAR90 (2.22 at N 21 tonight), 0 pass the light lane gate. Best absolute: short-fade-t1s1 +0.068R t 0.87 (train -0.065 / valid +0.134), 1.9/day; the hedged two-sided book -0.092R. Day-matched excess is positive in 8 of 9 (+0.03..+0.18R, short-fade-t1s1 t 2.46, long-any-h1030H t 1.81): the group again tells which names move, not enough to pay costs. Day types: no config positive on up, down AND quiet days. Scan proxy = 09:35 volumeRatio (opening $ volume / adv20 not in the frame). Educational only - not financial advice."},
 {"id": "qd1-1103-quiet-so-far-index-fade", "title": "QD1 (QDAY): on days SPY's range so far is small (<= 0.6 / 0.8 SPY ATR), fade moves from the open >= 0.3 / 0.5 ATR, both sides, 10:30-14:30, index ETFs or top-500 names",
  "category": "setup", "status": "parked", "configs_tried": 8, "module": "research/bdi/1103/qd1.py",
  "hypothesis": "Counter-index entries make +0.27R on (hindsight) quiet days; if 'quiet so far' is knowable intraday, a two-sided extension fade earns it.",
  "tags": ["bdi1103", "bdi", "setup", "qday", "quiet-day", "both-sides"],
  "notes": "Tested 2026-11-03 on the 2-year lab frames (locked block absent): 8 configs, 0 pass (all negative: IDX -0.10..-0.13R, STK -0.076..-0.081R, t -2.1..-6.9). 'Quiet so far' barely predicts a quiet close (37% / 35% vs 33% base). Index fades win on quiet days (+0.19..+0.33R) and lose on up (-0.28..-0.33) and down (-0.16..-0.25) days: the quiet-day edge is the hindsight label. Do not re-test without an ex-ante quiet-day predictor that beats the base rate by >= 15 points. Educational only - not financial advice."},
 {"id": "swing1103-L6-counter-index-entries", "title": "Counter-index entries: shorts entered with SPY >= +0.25% from the open (longs with SPY <= -0.25%) beat the same setups' other entries",
  "category": "filter", "status": "parked", "configs_tried": 1, "module": "research/bdi/swings/leads_bt.py",
  "hypothesis": "Live 11-02 (+0.314R, n 86) and 11-03 (+0.357R, n 177) shorts entered while SPY was up made money; the book swings with -net beta x SPY (Primary / T1 / Gen swings 11-03).",
  "tags": ["bdi1103", "bdi", "swing", "qday", "index"],
  "notes": "2 years, 21 lab setups, setup-adjusted: counter n 28,320, excess +0.003R (train +0.010 / valid -0.001, t 0.1) - fails. By day type: quiet +0.305R, down +0.009R, up -0.082R (quiet is hindsight; QD1 shows it is not knowable intraday). Shadow-forward logged in research/bdi/swings/forward.csv. Educational only - not financial advice."},
]
NOTES = {
 "swing1103-L1-ns5-vol-etp-beta": " bdi1103 2y backtest (1 config, 60-session daily beta proxy, all long lab setups since NS5 has 8 vol-ETP trades): class beta <= -1.5 n 434 -0.066R vs others -0.044R (A-B -0.022R, t -0.53), corr(day R, SPY o-c) -0.31 -> fails the pre-registered bar. The class is a pure direction bet (down days +0.49R, quiet +0.20R, up -0.30R). Status parked; forward shadow in research/bdi/swings/hypotheses.jsonl.",
 "swing1103-L2-rotation-turn-short-timing": " bdi1103 2y backtest (1 config, 1-min QQQ/IWM, 134 trigger days of 433): tagged family shorts n 854 -0.118R vs same-day others -0.11R, paired diff +0.030R t 0.47 -> fails. Tagged down days +0.34R, up -0.22R. Status parked; forward shadow running.",
 "swing1103-L3-upmorning-delay-family-shorts": " bdi1103 full rule incl. the IWM leg (1 config, 67 qualifying days): before -0.078R (n 828) vs after -0.104R (n 411), paired diff -0.079R t -1.01 -> fails again (after is worse). Forward shadow running.",
 "swing1103-L4-net-beta-cap": " bdi1103: recurring swing type confirmed across accounts on 11-03 - Primary (-32R per +1% SPY at 11:15) and T1 (-34R) swung with SPY both ways; Generator (+94R per +1% SPY at 14:57) lost -40R to market in 13:34-14:57 (SPY +0.54 -> +0.09%). Merged here; L6 (counter-index) was the testable side and failed on 2 years.",
}
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] in NOTES and "bdi1103" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + NOTES[r["id"]]
        if r["id"] in ("swing1103-L1-ns5-vol-etp-beta", "swing1103-L2-rotation-turn-short-timing"):
            r["status"] = "parked"; r["configs_tried"] = int(r.get("configs_tried") or 0) + 1
        if r["id"] == "swing1103-L3-upmorning-delay-family-shorts":
            r["configs_tried"] = int(r.get("configs_tried") or 0) + 1
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-03", "source": SRC, "variant": None}); e.setdefault("parent", None); rows.append(e)
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "entries")
