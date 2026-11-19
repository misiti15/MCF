Educational only — not financial advice

# Round 5 summary: fresh-window test NOT RUN yet, so nothing deployed (2026-11-19)

## In plain words
- Rounds 1-4 tried 35 candidate setups (about 1,000 configurations). None beat our current best setup (ST7-FD,
  +0.084R per trade after costs, +0.073R without its best day).
- Two narrow ideas did hold up on the check data: a late-afternoon dip-buy in a fixed list of ETFs ("leg E", about
  +0.10R) and a buy after a one-bar RSI collapse in very liquid stocks ("leg M", about +0.12R). Both look a lot like the
  two setups we already run (NM-ETF-late-dip and ST7-FD).
- Those ideas were partly designed using the check data, so a fair test needs data nobody has looked at. We set aside
  2023-01-03..2024-09-13 (427 sessions) for that, and each frozen rule gets exactly one score on it.
- **That score has not happened yet.** The plan has safety checks that must pass in a fixed order before any fresh data
  is downloaded. Three of them are not done, so the scorer stopped on purpose and read nothing. That was the right call:
  scoring now would have used up the one clean test without the safeguards in place.
- The one-score-per-rule budget is still unused for all 8 rules. Nothing was downloaded. The locked block
  2024-11-01..2025-02-28 was not touched.
- **Nothing was deployed.** The deploy rule needs a fresh-window BEAT that the skeptic upholds, and there are no fresh
  results at all.

## Every row (all 8 rules waiting for their single fresh score)
Check-half (2025-10-01..2026-11-04) figures are reference only. That data has been seen, so it is not evidence.

| Rule | What it is | Check trades/session | Check avg R | Check w/o best day | Best-day share | Fresh result |
|---|---|---|---|---|---|---|
| R1 BOOK-EM | ULT-32 config 32e (leg E + leg M) | 1.24 | +0.115 | +0.099 | 15% | not scored |
| R2 leg E | WB4 late-afternoon ETF dip, long | 0.82 | +0.110 | +0.096 | n/a | not scored |
| R3 leg M | one-bar RSI collapse, ADV >= $500M, long | 0.42 | +0.124 | +0.084 | n/a | not scored |
| R4 ST7-FD | benchmark, the current best | 3.13 | +0.084 | +0.073 | 13% | not scored |
| R5 NM-ETF-late-dip | benchmark | 0.95 | +0.052 | +0.039 | 28% | not scored |
| R6 ST7-base | ST7 on the round-4 chassis | 2.23 | +0.094 | +0.078 | 18% | not scored |
| H-V1 | leg X, WB4 mirror, short (borrow fee in) | 0.58 | +0.105 | +0.078 | 32% | not scored |
| H-V2 | leg K, one-bar shock snap in ETFs, long | 1.00 | +0.187 | +0.095 | **54% (1 day)** | not scored |

H-V2's check record leans on one or two big days: its top two days carry 90% of its check R. H-V1 and H-V2 move
together (daily R correlation 0.43), and H-V1 is concentrated in SOXL, NUGT and TECL (66% of its trades).

Fresh pass bar (pre-registered, FRESH_PLAN sec. 5): avg R > +0.0836, avg R w/o best day > +0.0734, R/session > 0,
day-clustered t >= 2.039 (M = 8), and positive on the check half.

## Why it is blocked (checked independently by the skeptic, read-only)
1. `FREEZE_HUNT.json` and `HUNT_FREEZE.md` are missing (FRESH_PLAN sec. 4.7 / 7.2), so M and the t bar are not formally
   fixed. With 8 rules, M = 8 and the bar is t >= 2.039.
2. `FRESH_PLAN.md` no longer matches `FRESH_PLAN.sha256` (now e52de481…, recorded b54e69c5…). Section 4-V was appended
   at 10:13Z, after the hash was taken at 09:59Z, and nobody re-hashed. `download_fresh.py` correctly refuses to run.
   The re-hash needs a dated note, plus a check that the append changed nothing in sections 1-4.
3. The `fresh_bt.py` harness does not exist, so the 2025-10 parity check has not run (sec. 2.5 / 2.6).
4. Because of 1-3, there are no fresh bars, and `/home/user/MCF/data/cache_fresh/` does not exist.

What passed: all 31 FREEZE_CORE files match their hashes, and all 8 FREEZE_VOLUME files match theirs. The scorer had
said "14"; the manifest lists 8 files plus 6 deps, and FRESH_RESULTS.md now says 8. Both freezes record that no fresh
data existed when they were made.

## Next steps, in order
1. Write FREEZE_HUNT.json and HUNT_FREEZE.md.
2. Re-hash FRESH_PLAN.md, with a note on the 4-V append.
3. Build fresh_bt.py and pass the 2025-10 parity check.
4. Run download_fresh.py, then verify_fresh.py.
5. Score each rule once.

Things the eventual scoring must handle (skeptic carry-forward):
- Survivorship: the symbol list is today's, so names delisted in 2023-24 are missing. This likely flatters R3/R4 more
  than the ETF legs, and the effect needs an estimate.
- Compute ADV >= $500M point-in-time from fresh bars.
- Check earnings-date coverage before 2024-09.
- Charge the borrow fee on H-V1 shorts.
- Report w/o-best-day, best-day share and day-clustered t for every rule.
- De-duplicate R2/R3 against R4/R5, which overlap by design.

## Configurations counted
No configurations were tried at this stage. Cumulative N stays at **1,036 (up to 1,052)**: 996 (up to 1,012) before
round 5, plus the round-5 volume hunt.

## Honest read
We have not yet learned whether anything beats ST7-FD. Round 5 is not a fail. It is an untaken test with the
safeguards intact. The candidates that look best on the check half (R1 BOOK-EM, R2 leg E) are close relatives of
setups we already run. Even if they pass, they would add modest volume (about 1.2 trades per session) at an edge
similar to what we have, not a step change. The known biases (today's symbol list, a flat borrow fee) all favour the
candidates, so expect fresh numbers to come in lower than the check figures. Following "don't force weak setups",
nothing goes live until a fresh, skeptic-upheld BEAT exists.

## Rule-change context
All figures are backtests on 1-minute bars with one fixed rule set (LR8 costs, next-minute-open fill, borrow fee for
shorts). No live-account window is quoted, so no `research/ledger.jsonl` rule change is mixed into them. For
reference: WB4 went live 2026-11-17 (Testing E), ST7-FD was promoted 2026-10-26, and NM-ETF runs in Primary. All of
these dates fall after every backtest window used here. The 2026-11-19 ledger entries are process-only. No ledger entry
was added for round 5, because nothing was deployed.

## Deployment
None. No setup, YAML, account, display name, assignments file or ledger entry was changed.

Educational only — not financial advice.
