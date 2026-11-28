# shorts_autopsy bench pre-registration (written 2026-11-27 ~23:55 ET, before any bench score is read)

Educational only — not financial advice.

Motivation (live, non-Graveyard, 10-23..11-27, LR8; exploration/sandbox/shorts_autopsy/live_autopsy*_out.txt):
gap-down short family is −0.012 R/trade without 11-25 but −0.20 on SPY gap ≥ +0.5% days (6 sessions); 11-25 (SPY gap −2.2%,
then +2.4% rally) cost the family −1,216R; non-gap-down shorts entered before 12:00 lose −0.17..−0.19 (ex 11-25), after 12:00 they are ≥ 0.

Engine: bench10 candidate lots (research/ultimate_1119/top10/bench10.py, unchanged, via gen_shorts.py) for 8 short setups:
gap-down family = L3-gap-slope-fromopen-FD, L3-gap-slope-lowdist-FD, L3-gap-slope-rsi5hi-FD, RW3, RW5, CWT09; other = RW6-ns2-up3, NM-RWN4.
Costs LIVE-L (primshorts_1126 cells_live.json) on every short; entry ≥ $5; ETB rate ≥ 0.9. Candidate level (no cap/latch):
the rules are day/time skips, so the book caps would only matter on crowded days (caveat stated in the report).
Windows: T2 2023-01-03..2024-09-13 and CHECK 2025-10-01..2026-11-04 are the scored splits; FIT descriptive. Locked block never read.

Configs (4, counted): 
- R1 GD-SPYUP: skip gap-down-family shorts on days SPY gaps ≥ +0.5% (open vs prior close).
- R2 SPYDN: skip every short on days SPY gaps ≤ −0.5%.
- R3 AM-OTHER: skip non-gap-down shorts entered before 12:00 ET.
- R4 R1+R2 combined.

Pass bar (each config, each of CHECK and T2): dR/session > 0; day-clustered t of the removed lots' daily R ≥ 2.0 (sign: removed lots lose);
≥ 95th percentile against 1,000 matched random removals (R1/R2/R4: the same number of random whole days, same family scope;
R3: the same number of random lots from the same setups); best-day share of the gain < 50%; more setups improve than worsen.
Also reported: worst-5 days, red days per month, avg R w/o best day.

## Addendum A (2026-11-28 ~00:05 ET, after the CHECK/FIT part of R1-R4 was seen, before T2 and before any cap number)
Live motivation: on 11-25 the testing accounts held 1,528 gap-down-family short lots from ~15 near-identical L3/RW clones (−1,216R).
Configs (3, counted): C5 / C10 / C20 = at most K open gap-down-family short lots at once across all 6 gap-down setups pooled
(one account holding all clones; first-come by entry minute, then symbol; a lot frees its slot at its exit minute).
Control: the same number of lots removed at random from the gap-down family, days kept (1,000 draws); also the
exposure-matched constant cut. Same pass bar as above, plus worst-5 days must improve on both splits. Candidate level, LIVE-L.

## Addendum B (2026-11-28 ~00:15 ET, after R1-R4 and C5-C20 scores were seen (all fail); before any dedupe number)
Config (1, counted): D1 = across the 6 gap-down setups pooled, keep only the first lot per symbol per day (any setup, any refire);
later lots in the same name that day are dropped. Control: same number of random family lots removed (1,000 draws) and the
exposure-matched constant cut. Same pass bar (both CHECK and T2: dR > 0, t ≥ 2, ≥ 95th pct, best-day share < 50%).
Builds on l3refire_1127 (repeats within L3 only, 0/7) — this is the cross-clone version.
