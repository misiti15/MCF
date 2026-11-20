Educational only — not financial advice

# owner1120/inverse — direction-correct inverse / leveraged handling, all setups (pre-registered)

Written 2026-11-20 before any scoring in this folder. Owner 11-19 ~21:50 ET: "make sure ... all setups buy and short the
correct tickers. I don't mind that inverses are in play, but they need to be done correctly" and "INV yes - as long as
it's not beneficial to short or buy an inverse. I don't want to rule these out completely unless you think we can afford
to." Research only: no config, setup, exit, order or runner change; nothing committed by this stage.

## Data and windows
- Live: run 1 (paper live), all 10 accounts, journals read from origin/mcf-data* (git show, data through 2026-11-19).
  Costs: mcf.costs.with_cost_r (LR8 basis for every row). Borrow: Alpaca charges borrow only on positions held
  overnight; every MCF trade is flat by 15:55, so intraday borrow fee = 0. The borrow cost that matters is availability
  (ETB list) and is already in the live record (ETB skips). Inverse/leveraged funds' daily-reset decay acts at the close
  only; intraday the fund tracks -L x the underlying's move from the prior close (path term < 1% of the move for moves
  < 3%); noted, not modelled, except the 0.02R haircut on synthetic inverse-buy rows (H2D below).
- Lab: research/rootcause_1119/sl_work/family_trades.parquet (118 enabled lab setups, first fire per symbol-day,
  production costs, 2024-10..2026-11). **Locked block 2024-11-01..2025-02-28 asserted absent, never read.**
  Fit half = dates < 2025-11-01; check half = dates >= 2025-11-01.
- Rule changes inside the live window are listed from research/ledger.jsonl in RESULTS.md.

## Product classes (frozen in shadow.py of this folder; INVERSE / LONG_VOL / NEUTRAL = research/forward/compass_gate)
inv_broad (broad-index inverse), inv_sector (sector / country / theme inverse incl. SARK, BTAL), inv_single
(single-stock inverse), inv_crypto (BITI SBIT ETHD), long_vol (VXX UVXY VIXY UVIX VIXM VXZ), lev_long (2x/3x long
funds, name-regex list frozen from data/universe.csv), neutral, stock/plain ETF. Each inverse fund has an underlying and
leverage (frozen map). Exposure sign = side x beta sign (inverse/long-vol = -1).
"Thesis match" = the trade's market exposure has the setup's side (a short setup ending up long the market = mismatch).

## Configurations (all counted, all reported)
| # | code | rule |
|---|---|---|
| 1 | H1 | short setups skip INVERSE U LONG_VOL (= Wave 2 INV-G1) |
| 2 | H1M | H1 + long setups skip them too (block everything) |
| 3 | H2 | DIRECTION-CORRECT. Each inverse trade is read as a trade on its underlying with the side flipped. Short X = long U: a short setup's thesis cannot be expressed -> skip. Long X = short U on a signal computed on X's own bars, which are the inverted, levered underlying -> kept (the signal is on the inverted underlying already). Plus the "inverse buy": when a short setup's short signal on an underlying U (that has an inverse fund in the universe) is not executed for a borrow / spread / cost reason, buy the inverse instead (R = the run-2 what-if R of the U short when one exists; else not counted). |
| 4 | H2D | diagnostic: H2 + a duplicate long-inverse for every EXECUTED short on an underlying (R = that short's R - 0.02R). Shows whether expressing index weakness twice adds anything. |
| 5 | H2S | "keep where beneficial": per setup, inverse/long-vol trades (either side) are kept only if that setup's own inverse trades in the FIT data had n >= 5 and avg R > 0; else blocked. Lab: fit = lab first half, check = lab second half. Live: fit = 10-06..11-05, check = 11-06..11-19 (and the lab second half where the setup is a lab setup). |
| 6-10 | H1-broad, H1-sector, H1-single, H1-crypto, H1-vol | H1 restricted to one product class (decomposition) |
| 11 | LEV-X | diagnostic: block lev_long trades on both sides (leveraged longs are direction-correct; is anything wrong there?) |

Scoring: paired on each setup's own trades (WB2: guarded = base minus removed plus added rows); per setup x account
(live), per setup (lab), per family; better / worse counts and sizes, largest worsening, avg R and avg R w/o best day
with best-day share, live with and without 11-19. "Can we afford to drop them": R and reps lost if blocked, per setup.

## Choice per setup (fixed now)
For each setup with inverse/long-vol trades: H1 for its short side unless H2S keeps it on fit AND check is >= 0;
its long side is kept (H2) unless both the live record and the lab check half are negative for that setup's inverse
longs with n >= 5 each (then blocked). Setups with no evidence default to H2 (shorts skip, longs keep).

## Shadow pass bar (fixed now; journal-only, forward from 2026-11-20)
>= 10 sessions; for the blocked inverse shorts: their net R < 0 (guard helps), >= 60% of affected setup x accounts not
worse, no setup worse by > 3R; for the kept inverse longs: net R >= 0 over the same sessions (else review the long side).
Locked holdout scored once only at a promotion decision.

Educational only — not financial advice.
