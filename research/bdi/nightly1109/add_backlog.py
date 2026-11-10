"""nightly1109: append tonight's backlog hypotheses (idempotent by id; status idea) and add 11-09 evidence to
swing1103-L6-counter-index-entries. Usage: python research/bdi/nightly1109/add_backlog.py   Educational only - not financial advice."""
import json
from pathlib import Path
B = Path("/home/user/MCF/research/backlog.jsonl")
SRC = "nightly learning loop 2026-11-09 (research/bdi/nightly1109/NOTES.md, mf1109_out.txt)"
NEW = [
 {"id": "nightly-1109-mf-short-broad-etf-skip", "category": "setup", "configs": 2,
  "title": "MF family shorts: skip unleveraged (diversified / factor) ETFs",
  "hypothesis": "11-09: 12 of MF4-FD's 17 Primary shorts were broad or factor ETFs (AVLV, JEPI, QUAL, SPYV, IWN, FNDX, DIA, IWD, IWS, VTV, SPYM, AVUV); 16 of 17 stopped (-17.1R) on a trend-up day. A flow-sell signal on a diversified ETF is an index short. 2y (MF1109 A): skipping unleveraged ETFs helps all 6 MF short setups (VALID +398R, 6 better / 0 worse) but kept avg R stays negative and VALID day-clustered t 1.80 < bar 2.64; lab rows after 10-05 +20R.",
  "test_needed": "Rework on the MF lineage: ETF list from holdings count (not name match), per-setup cut, combine with B (UP-confirmed); plateau; rule-18 look count (MF lineage 33).",
  "tags": ["nightly1109", "setup", "mf", "etf", "remedy"]},
 {"id": "nightly-1109-mf-short-upconfirmed-gate", "category": "filter", "configs": 2,
  "title": "MF family shorts: no new short while the index tape is UP-confirmed (W60 proxy, from 10:00)",
  "hypothesis": "11-09: the live compass was UP-confirmed at 10:00 and never flipped; MF4-FD shorted 17 times 10:20-10:51 (-17.1R). GATE1 starts at 11:00 and does not list MF4-FD, so it would have dropped nothing on Primary. 2y (MF1109 B, proxy without breadth: SPY >= +0.15% & above VWAP & QQQ, IWM up, 60-min persistence): VALID +420R, t 2.51 (B2 no persistence 2.56) < bar 2.64, all 6 setups better, but lab rows after 10-05 -123R (t -1.46) - the October tape punished it.",
  "test_needed": "Add breadth to the proxy (true W60), forward on journals 10-06.., combine with the ETF skip; per setup / family report; owner decision only after a pass.",
  "tags": ["nightly1109", "filter", "compass", "mf", "regime"]},
 {"id": "nightly-1109-gen-index-gated-short-trend-day", "category": "setup", "configs": 0,
  "title": "Generated shorts gated on 'SPY > +x% from open' fade a trend-up day",
  "hypothesis": "11-09 Gen: GEN-261029-08 (RSI14 >= 65, SPYgt0p5, hold) 50 shorts -38.9R / -$810.70; GEN-261022-08 (SPYgt0p25, holdtr) 28 -18.1R; Gen shorts -63.2R vs longs +5.9R; Graveyard shorts -136.0R vs longs +59.5R. The generator's index gate admits shorts exactly when the index is strong; on UP-confirmed days with no midday reversal they lose together.",
  "test_needed": "Generator lab lists: index-gated shorts split by W60 state at entry (UP-confirmed vs other) and by day type; regime split; owner consent needed for any change to GEN setups (rule 20).",
  "tags": ["nightly1109", "setup", "generator", "regime"]},
]
EVID = ("11-09 (strong up day, SPY +1.44%, compass UP-confirmed 10:00): counter-index entries lost - 430 trades avg -0.516R vs 536 "
        "others +0.122R (Primary 35 shorts -0.531R, GY 256 -0.531R, Gen 104 -0.608R); opposite of 11-06 (+0.082 vs -0.073) - nightly1109.")
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] == "swing1103-L6-counter-index-entries" and "nightly1109" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + " | " + EVID
for e in NEW:
    if e["id"] in have: continue
    rows.append({"id": e["id"], "title": e["title"], "added": "2026-11-09", "source": SRC, "category": e["category"],
                 "hypothesis": e["hypothesis"], "module": None, "variant": None, "status": "idea", "configs_tried": e["configs"],
                 "tags": e["tags"], "test_needed": e["test_needed"],
                 "notes": ("MF1109 2y screen 2026-11-09: 0 of 4 configs pass (bar 2.64); see research/bdi/nightly1109/mf1109_out.txt. " if e["configs"] else "Not run 2026-11-09. ")
                          + "Educational only - not financial advice."})
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "rows")
