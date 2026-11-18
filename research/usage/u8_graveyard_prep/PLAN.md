Educational only — not financial advice

# U8 — Graveyard revival prep (USAGE PLAN item 8) — pre-registration

Written 2026-11-18 ~13:10 ET (market hours: research only, no config/code/runtime change, no PR/merge). This plan was
written before any tune was scored. Only the per-setup headline record (n, avg R, avg R w/o best day per setup over the
whole live window) had been looked at when it was written.

Scope: the Graveyard's resident setups (config/account_graveyard.yaml `strategies`, minus the 20 GY-BENCH guests, which
are arena setups visiting 11-18..11-24 and go home by themselves). 34 residents. Nothing is deleted or switched (rule 20);
the evening Graveyard deep dive owns triage and the lifecycle rule; this item only ranks and pre-tests revival tunes and
writes CANDIDATES.md for it.

## Data
- Live journals (run_id 1 only; what-if run 2 and shadow run 3 are NOT used) of all ten `mcf-data*` state branches,
  sessions 2026-10-06..2026-11-17 (11-18 still open). A resident's record = its trades in every account under the same
  setup id (home account before the move + Graveyard), identical signals (setup, symbol, date, entry minute) counted once.
- R = pnl_adj / (|entry - stop| x shares) (after costs, LR8). Locked block 2024-11-01..2025-02-28 is not read (no 2-year
  data is used at all here — guardrail: no replay/2-year-only passes).
- Entry features from the live-session bar packs (release bars-2026-10 / bars-2026-11, 1-min, streamed one day at a time
  and deleted) and the 1day pack (only days strictly before the session): SPY return from 09:30 open to the entry minute,
  SPY gap, the stock's gap, the stock's return from its open to entry (signed by trade side), stock vs session VWAP at
  entry, and spread_bps from the order meta.
- Exits use the journal's mae_r / mfe_r: a target at +X R is hit iff mfe_r >= X (the trade was still open when it first
  touched X); a tighter stop at -s R is hit iff mae_r <= -s. Tuned R = new gross R - (gross R - after-cost R) of the
  original trade (same per-trade cost). Trades with no mae/mfe keep their R.

## Split
- FIT = sessions 2026-10-06..2026-10-30 (diagnosis and tune choice only).
- CHECK = sessions 2026-11-02..2026-11-17 (12 sessions, unseen for tune choice; verdict only).
- Rule changes inside the window (research/ledger.jsonl): 10-20 twin-symbol block; 10-21 Graveyard opens (per-setup -2R
  latch there from day one; Testing 1/2 latch off 10-22/23, -2R latch back 10-29); 10-27 slot cut; 10-29 BAR90;
  11-12 LR8 after-cost R and Graveyard REPV-11/12 (more, smaller slots); 11-16 ROT1; 11-17 KILL-FLAT / TSZ1. R is per unit
  of risk, so sizing does not move it; latches and slot counts change WHICH trades exist, and a gate cannot add back
  trades a latch or slot limit cut.

## Ranking (all 34 residents scored; top 10 eligible get a tune)
Excluded from tunes by guardrail: CWT12-* and CWT14-* (closed to new variants, 13 residents) — ranked for the record only.
Score (higher = better revival potential):
1. Positive w/o best day in any period (whole record, FIT, CHECK, Graveyard-only): +2 if any; +0.5 per positive period.
2. Mechanism (pre-assigned, falsifiable reason): 2 = clear (gap / failed-reclaim / overextension-from-VWAP / liquidity
   sweep); 1 = stated but generic (heat regime fades, flow sells, exhaustion, big-gainer fade, vwap stretch, flush);
   0 = template only (ST1/ST2/ST4 indicator templates).
3. Fixable in <= 2 changes: the FIT-half best tune from the menu below: +2 if its FIT avg R w/o best day > 0, else +1 if it
   lifts FIT avg R by >= 0.10R, else 0.
4. Low correlation with Primary: Pearson of the setup's daily R with Primary's journal daily R over shared sessions:
   +1 if |rho| < 0.2, 0 if < 0.4, -1 if >= 0.4 or a same-family sibling of a current Primary setup (RW3S vs RW3).
Ties: whole-record avg R w/o best day.

## Tune menu (identical for every setup; one change = one item; max 2 changes per tune — C3-WB)
Gates (keep only trades that satisfy):
- T1 entry < 10:30 ET; T2 entry < 11:30; T3 entry >= 11:30; T4 entry >= 13:00
- S1 SPY up from open at entry; S2 SPY down from open at entry
- G1 SPY gap > +0.2%; G2 SPY gap <= +0.2%
- K1 stock gap > 0; K2 stock gap < 0
- V1 stock above VWAP at entry; V2 stock below VWAP at entry
- M1 stock already moving with the trade from its open (side x return-from-open > 0); M2 against (< 0)
- C1 spread_bps <= 10 at entry
Exits:
- X1 target +0.5R; X2 target +1.0R (applied only where it is closer than the trade's own target)
- X3 stop at -0.7R
18 single changes. Tune choice on FIT: best single change by FIT avg R w/o best day (must keep >= 20 FIT trades and >= 25%
of the parent's FIT trades); a second change from the remaining 17 is added only if it lifts FIT avg R w/o best day by
another >= 0.03R and still keeps the trade floors. Every single and conditional pair tried counts as a configuration.

## Verdict on CHECK (pre-registered)
For each of the top-10 tunes, on the 12 CHECK sessions, with the parent re-scored on the identical CHECK trades:
- PASS (-> Testing-copy proposal, decision code U8-REV-<setup>; promotion hold stays, nothing deployed): tuned avg R > 0,
  tuned avg R w/o best day > 0, best-day share < 50%, improvement over the parent paired by day with
  t >= max(1.5, sqrt(2 ln N)) where N = all configurations counted in this item, and the tuned set beats >= 95% of
  random same-size subsets of the parent's CHECK trades (random-entry control for gates; exits are paired per trade).
- LEAD: tuned avg R > 0 and w/o best day > 0 and better than the parent on CHECK, but t below the bar -> watch item for the
  deep dive (keep collecting in the Graveyard), no proposal.
- FAIL otherwise.
Reported for every tuned setup: parent vs tuned n / avg R / avg R w/o best day / best-day share / total R on FIT and CHECK,
trades kept, t, random-subset percentile; and the count of tuned setups that improve / worsen on CHECK and by how much.

## Caveats known up front
Gates are scored on the trades that happened; a gated setup would free slots that other setups could use (not modelled).
Setups ranked partly on CHECK-period positivity have a selection bias in their absolute CHECK level; the paired
improvement is clean because the tune is chosen on FIT only. 12 CHECK sessions: one big day can carry a result.
