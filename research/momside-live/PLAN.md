# MOMSIDE-LIVE — frozen companion check on LIVE trades (Observer, 2026-11-14 ~09:50 ET, before any outcome is read)

Purpose: Builder's MOMSIDE (research/momside/PLAN.md) scores the 2-year LAB trades once. This is a secondary, descriptive
check on LIVE paper trades with the same tags, run ONLY AFTER Builder posts the lab result, so it cannot shape the lab
plan. It cannot pass anything on its own (28 sessions); it can only flag 'live disagrees with lab'.

Frozen definitions (no tuning after this commit):
- Trades: run_id 1, all 10 accounts, entries 2026-10-06..2026-11-13 (window fixed now; later sessions excluded).
- R = raw R (r_multiple = pnl / risk), the basis that is identical on both sides of LR8 (OBS-LR8). Costs reported
  separately with LR8 recompute; gross first.
- 12-1 momentum per name and trade date: close(prior session - 21 trading days) / close(prior session - 252) - 1, from
  Alpaca daily SIP split-adjusted bars fetched after 16:00; names with < 253 prior sessions = untagged.
- Deciles: across the lab universe (research/lab_symbols.txt) on each trade date. Aligned = long in deciles 8-10 or
  short in deciles 1-3; counter = long in 1-3 or short in 8-10; else neutral.
- Score: within each setup-day, aligned trades' mean raw R minus the mean of a random same-count draw from that
  setup-day's non-aligned trades (1,000 draws); pooled over setup-days with >= 1 aligned and >= 1 other trade.
  Day-clustered t, best-day share, per-setup better/worse (setups with >= 5 eligible setup-days).
- Ex-market: subtract side x (SPY return over the hold) x the setup's live beta (OLS of R on side x SPY-hold return,
  per setup, from the same window); reported beside raw.
- Survivorship: none in live (names traded live existed then); report the share of live-traded names missing from the
  lab universe (lab survivorship proxy).
Reading rule (fixed): 'agrees with lab' if the sign of the live aligned-minus-random excess matches the lab's and |t| >= 1;
'disagrees' if opposite sign with |t| >= 1; else 'uninformative'. No pass/fail; no setup/config changes.
Family: 0 new configs (same tags as MOMSIDE; a check, not a candidate). Educational only — not financial advice.

## Amendment 1 (2026-11-14 ~11:50 ET, before any live outcome is read): adopt Builder's frozen MOMSIDE definitions verbatim
- 12-1: close(D_-21) / close(D_-252) - 1, sessions strictly before D (D_-1 = prior close), NaN with < 253 prior sessions;
  locked-block restart rule applies (it never binds for live dates 10-06..11-13: their lookback starts ~2025-10).
- Deciles across research/lab_symbols.txt names with a valid mom on D.
- Configs as research/momside/PLAN.md: C1 skip longs in deciles 1-3 / shorts in 8-10 (primary); C2 1-2 / 9-10; C3 longs-only
  leg of C1; C4 = Builder's dated 6-1 amendment, adopted verbatim when it is committed (not run before it exists).
- Score (replaces my aligned-minus-random draw): per setup-day, delta = -sum(R of skipped trades), control = (k/n) x setup-day
  total R, excess = delta - control, summed per day, day-clustered t; per-setup excess per trade (setups with >= 10 skipped);
  best-day share; kept and control avg R printed. Raw R (r_multiple) gross first; ex-market = raw - beta_setup x side x SPY move
  over the hold (beta per setup by OLS on ALL live trades in the window); LR8-recomputed net beside.
- Reading rule unchanged: agrees / disagrees (|t| >= 1, sign vs Builder's VALID C1) / uninformative. Still 0 configs.

## Amendment 2 (2026-11-14 ~13:50 ET, before any live outcome is read)
- C4 adopted verbatim from Builder's Amendment 1 (4c8a8487c): 6-1 = close(D_-21) / close(D_-126) - 1, < 127 prior sessions -> NaN,
  counter = long in deciles 1-3 or short in 8-10. Reported like C2/C3.
- Scope follows Builder's PRIMARY input (Lead lead-20261114-1300-1): if Builder scores the full-day lists, the live primary is all
  entry times; if Builder keeps trades_tagged, the live primary is entries at or after 12:00 (Skeptic), all hours descriptive.
  Set by --scope {all,pm} at run time to match Builder's posted scope; both are printed either way.

## Amendment 3 (2026-11-14 ~15:50 ET, before any live outcome is read)
- Builder's Amendment 2 (58a8384e8) scores the full-day lab lists -> live primary scope = ALL entry times (pm descriptive).
- Reporting only (Skeptic skeptic-20261114-1450-1): print the top-5 setups' share of the live excess beside better/worse.
- Outcome-free coverage run now (--coverage): daily closes fetched (Saturday), trades tagged; prints counts only (tagged
  share, skipped counts per config, setup-days with a skip). R is never loaded in this mode.

## Amendment 4 (2026-11-15 ~03:50 ET, before any live outcome is read): MDE column (guild standard, checklist #41)
Each summary line also prints MDE80 = 2.8 x SE of the per-day excess (and per skipped trade); a 'disagrees/uninformative'
reading is worded 'nothing above MDE80; smaller unknown'. No other change.

## Pre-registered reading (2026-11-15 ~13:50 ET, before any live outcome is read; no gate, it fixes how results are read)
| Lab C1 (Builder) | Live C1 (this) | Reading / next step |
|---|---|---|
| PASS | agrees (same sign, |t| >= 1) | Live supports the lab: the owner gets both; arena-only field test is the next step (never On Deck / Primary first). |
| PASS | uninformative (|t| < 1) | Lab stands alone; say live has ~29 sessions (MDE printed); no extra weight either way. |
| PASS | disagrees (opposite sign, |t| >= 1) | Flag to Lead before any owner note: lab-live gap on the same tags; check survivorship (C3) and the 2026 regime first. |
| CLOSED | agrees / uninformative | Closed; print live MDE ('nothing above X; smaller unknown'). |
| CLOSED | disagrees with a positive live effect | Closed stands (one-look rule); live is a 29-session lead only, logged, no re-score. |
Also printed regardless: C1 by side (short-leg vs long-leg share of the excess), C3 beside C1, top-5 setups' share, per-setup
better/worse, and the live window's rule-change context (11-12 restructure c64d75df0, LR8 from 11-12 - raw R is basis-stable).

## PARKED (Lead lead-20261116-2300-3, 2026-11-16 23:00 ET) — never run
MOMSIDE lab CLOSED (C1 VALID t 0.96 vs 2.91; an up-day cell; FWD 10-08..11-13 reverses, t -3.06). This live window
(10-06..11-13) is the same calendar as lab FWD (Skeptic skeptic-20261117-0350-1), so it would not be independent and would
only be a second look at a closed idea. Not run; no live outcome was ever read. Plan and scorer stay as the record.
