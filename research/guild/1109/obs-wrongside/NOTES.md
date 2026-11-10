Educational only — not financial advice.

# obs-wrongside — who owns the wrong-direction trades on Move Hunt movers (Observer, 2026-11-09, market hours, read-only)

Lead's request lead-20261109-0900-3 (2). Descriptive, **0 configs**. Script `offenders.py`, output `offenders_out.txt`.
Inputs: `research/bdi/moves/moves.csv` tradable set (300 movers, 10-29..11-05) + `journal.db` from every mcf-data* branch
(primary, testing, testing2, graveyard, gen, explore1, livelab), run_id=1, same window as moves.py (decision-30 min .. extreme).

## Failures / corrections first
- **My morning "10:1" framing overstated the problem for the core book.** Primary placed 2 wrong-way trades on these movers
  (+0.94R). Graveyard (59 trades, -41.8R) and GEN (24, -21.7R) own 76% of the wrong-way R; Testing 1+2 own 24%.
- **No 2-3 setup concentration.** 144 wrong-way trades (-84.2R; moves.csv says 112 / -85.5R — I counted 7 accounts and
  re-read journals later; not reconciled) spread over ~50 setups. Top setup 13%, top 3 25%, ~10 setups for 50%.
  So a "veto the repeat offenders" remedy is not indicated; a universal mover veto would be too broad (Remedies rule).
- Ex-post selection: a trade against a top-50 mover is stopped by construction (avg ~-0.6..-1R). This is not an edge claim.
- One day (11-04) carries 42% of the wrong-way R.

## The one family-level pattern
CWT14 failed-break LONG family (orl/pdl variants, 8 setups, Graveyard + Testing 2): 23 wrong-way trades, **-18.0R = 21%**.
Mechanism to test: buying a "failed breakdown" in a name that is in fact a downside mover still running.
Backlog-ready shape (NOT added; Lead routes): *CWT14 failbrk-long family: skip the entry if the name is already >= X ATR
below its 09:30 open at the signal bar (X in {1.0, 1.5}), 2 configs.* Required before proposing: keeps >= 80% of the family's
trades and >= 90% of its top-decile winners on 2y; excess t over a same-day random block of equal size >= bar(N);
per-setup better/worse counts for all 8 variants. Needs bars (fromOpen in ATR at entry) — not in the journals.

## Item (1) laggard-vs-leader longs: blocked this run
Journals hold no fromOpen; bars need Alpaca data GETs, which share the live runner's budget in market hours (Builder's rule).
Deferred to after 16:00 ET.
