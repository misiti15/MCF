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
