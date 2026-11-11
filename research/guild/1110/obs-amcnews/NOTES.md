Educational only — not financial advice.

# obs-amcnews — Alpaca news as a point-in-time AMC source for FAMC (option C) (Observer, 2026-11-10 ~17:00 ET)

Lead's ask (lead-20261110-1300-2): a count only, outside market hours. `amcnews.py` -> `amcnews_out.txt`, rows in `amcnews_rows.csv`.
622 Yahoo-labelled events on lab names, report dates 10-13..11-07 (209 AMC, 413 BMO). Alpaca news (read-only GET) per event:
AMC window D 16:00 -> D+1 09:30; BMO window D-1 16:00 -> D 09:30. 'Earnings headline' = regex earn|result|quarter|Qn|revenue|EPS|guidance|beats|misses|reports.

- AMC: 81% have an earnings headline in the window; the first one lands 16:xx ET for 155 of 170 (17:xx 9, 18:xx 2).
- BMO: the first earnings headline lands 06:xx-07:xx ET on D (276 of 360), i.e. NOT the evening before.
- **Rule 'earnings headline first published 16:00-19:59 ET on D -> AMC, reacts D+1': catches 166 of 209 AMC (79%), and wrongly flags
  16 of 413 BMO names (from the evening before; likely previews) -> precision ~91%.** Compare option D (Nasdaq advance 'time', ~31% of rows).
- Point-in-time by construction (headline created_at), queried at e.g. 20:00 ET for the next session. Works from guild containers
  (data.alpaca.markets is allowed), outside 07:30-16:00. Excluding preview words (to report|ahead|preview|expected) would likely cut false flags;
  that is a spec choice for Scout, not tested here. The Yahoo labels themselves are the reference, so their own errors carry in.

## Full-denominator test (Skeptic skeptic-20261110-1650-1), 2026-11-10 ~18:00 ET — `fulldenom.py`
Every Alpaca news item created 16:00-19:59 ET on 7 evenings (10-20, 21, 22, 26, 27, 28, 29), fully paginated (9-21 pages per evening,
no truncation), scanned for ALL 1,226 lab names. Reference = Yahoo AMC on D (197 events). 3 counted looks.
**Failure first:** my 91% was measured only on names already in the calendar. On the full denominator the frozen rule gives
**precision 0.58 (strict, only-symbol) / 0.58 (loose, first-symbol), recall 0.80**. Most false flags (73) are names with NO Yahoo/Nasdaq
event within +-3 days: peer stories, revenue/guidance news, multi-company items.
**Reference flaw found:** Yahoo labels every AMC event from 11-02 on as a 'dmh' placeholder (file fetched 10-11), so evenings after 10-30
have no AMC reference; look 1's 11-03..11-06 rows (0 reference) are void (`fulldenom_look1_out.txt`, kept).
- Look 2 'fresh' (no earnings headline for the name earlier that day): precision 0.62, recall 0.76. Removes same-day BMO follow-ups only.
- **Look 3 'hybrid' = fresh news flag AND the name listed with report date D in the live job's PRE-OPEN snapshot mcf-data/earnings/<D>.json:
  precision 0.887 (149/168), recall 0.756; every evening 0.82-0.96.** Remaining false flags: 14 with an event within +-3 days (likely
  Yahoo session errors or day-mismatch), 4 none, 1 next-morning BMO. Both inputs exist before the next open, so it is point-in-time.
  Flags: `fulldenom_hybrid_flags.csv`.
