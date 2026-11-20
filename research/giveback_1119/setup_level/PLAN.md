# Setup-level giveback causes and one targeted fix per setup — pre-registered plan

*Educational only — not financial advice.* Written 2026-11-20 before any fit or check score of this stage. Only the
per-setup lab trade counts and overall avg R were looked at before writing it. Research only: nothing is committed by
this stage, no setup, exit, config or ledger line is changed.

## Setups (15)
- Top 10 by live trades (run 1, all accounts, identical signals de-duplicated on (setup, symbol, entry minute)):
  CWT14-failbrk-orl-p05-long, CWT14-failbrk-orl-p05-lowvol-long, CWT14-failbrk-pdl-p05-long, CWT12-coil-k4-long,
  CWT14-failbrk-pdl-p10-long, heat_fade_short-FD, RW7-gapdn-bounce-early-short-FD, CWT14-failbrk-orl-p10-lowvol-long,
  CWT14-failbrk-orl-p10-long, CWT14-failbrk-pdl-p05-lowvol-long.
- Primary five (docs/live/assignments.json): L3-gap-slope-fromopen-FD (protected, W4-FRAME: scored, never proposed
  for Primary), NM-ETF-late-dip-di-long, RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD,
  ST7-rsi50dn-long-pm-t1s1-FD.
- heat_fade_short-FD and NM-ETF-late-dip-di-long have no bt_lab1104 list: live only.

## Data
- Lab: bt_lab1104 signal lists, ALL signals (refires kept), list R `r` (bt_all costs in, stop units). Locked block
  2024-11-01..2025-02-28 asserted absent. Fit = dates <= 2025-09-30, check = later (scored once).
- Live: giveback map live_paths (run 1, LR8 R), de-duplicated. Fit = first 17 sessions (10-06..10-28), check = 10-29..11-19.

## Candidate causes and fixes (entry-side; each is <= 2 changed parts, C3-WB)
Per setup, 8 candidate configs:
- A "crowd minute": skip every entry of the setup in a minute where that setup fires >= K signals (known at the bar
  close). K in {3, 5, 10}.
- B "late entry": no new entries at or after X. X in {13:30, 14:00, 14:30} (can't reach target before the 15:55 flatten).
- C "refire into a fade": C1 no 2nd+ entry in the same symbol the same day; C2 no re-entry in a symbol after that
  setup's earlier trade in it the same day closed at a loss (exit before the refire).
Configs = 8 x 15 = 120 (live-only setups use the live fit half). Descriptive diagnostic cells are counted too.

## Selection on fit (mechanical)
Per setup, a config is eligible if on fit it keeps >= 70% of trades and >= 90% of top-decile winners, its excess
over random removal (sum over dropped trades of (setup fit avg - r)) is > 0 with day-clustered t >= 2.0, and the excess
without its best day > 0. The eligible config with the largest fit excess is adopted (at most one per setup);
none eligible -> no fix (the setup is reported as such). A fixed setup is a NEW setup (tweaked copy) and would enter
through Testing, never replace the parent in place.

## Check (scored once) and pass rule
For each adopted fix on the check half (lab for 13 setups; live check half for the 2 live-only; live check half also
shown for all as a second readout): total R change, avg R change, excess over random removal (day-clustered t and the
percentile of 2,000 same-session random removals), avg R w/o best day, best-day share of the gain, plateau (neighbour
levels' excess sign on check, shown).
A fix PASSES only if all hold: total R and avg R improve after costs; avg R w/o best day not worse; best day < 50% of
the gain; and min(raw paired t, excess t) >= max(1.5, sqrt(2 ln N)), N = lineage configs = map 916 + time_in_trade
2,664 + day_lock 16 + targets 222 + outside_methods 814 + this stage's 120 configs + its descriptive cells.
The stage passes only if at least one setup passes AND more setups/families are better than worse on check.
Family = setup prefix (CWT14, CWT12, RW7, RW3, RW5, L3, ST7, heat, NM).

## Addendum A (written after the fit selection, before any check score)
Fit selection adopted **0 of 15** setups (0 of 84 testable fit cells reached excess t >= 2). Under the plan the check
half has nothing to score and the verdict is FAIL. Two secondary readouts are added; they count zero as evidence
and cannot change the verdict:
1. Fit-best on check: per setup, the keep-eligible config (>= 70% kept, >= 90% top decile kept) with the largest fit
   excess, scored once on the lab check half and on the live check half, to show whether fit directions persist.
2. Live descriptive table per setup (all 33 sessions): share and avg R of crowd-minute entries (>= 3 same-minute),
   entries at/after 14:00, refires (2nd+ entry same symbol same day), refires after a loss, and P(full stop | MFE >= 0.8).
Configs stay at 120 (the readouts re-use configs already counted).
