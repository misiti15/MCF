Educational only — not financial advice

# Wave 2 item 5 — WB2-NEXT exits: pre-registered plan (written 2026-11-19 22:11 UTC = 17:11 ET, before any variant was scored)

Research and proposals only. No config, setup, exit or runtime change. Locked block 2024-11-01..2025-02-28 not read
(live journals 10-06..11-17 and the 1-minute release packs `bars-2026-10/11` only; no 2-year data). Costs in (LR8 live
cost per trade kept; extra exit cost on every replayed stop / flatten / market exit).

## Family and setups (fixed by rule)
Gap-down short fades with fixed targets (the W5 Part D family). Eligible for exit tunes under C3-WB = parent with
>= 150 live trades, avg R after costs > 0 AND avg R w/o best day > 0 on the live record through 11-17, not protected
(L3-gap-slope-fromopen-FD excluded). By W5's figures that is **RW3-gapdn-rsi5pop-flowsell-short-FD,
RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, L3-gap-slope-rsi5hi-FD** (RW7: w/o best day < 0; RW1: avg < 0). If the
recomputed parent stats change eligibility, the rule (not the W5 list) decides, and that is reported.
Trades: run 1, all ten accounts, identical signals counted once (W5 loader), dates with a 1-minute pack (10-06..11-17).
11-18 / 11-19 have no pack and are out of the scored sample (reported).

## Classes (fixed parameters, nothing searched) — 3 classes x 3 setups = 9 configurations; bar t >= max(1.5, sqrt(2 ln 9)) = 2.10
- **Y1 target 1.25x**: target = signal price + side x 1.25 x |parent target - signal price|; stop unchanged.
  Signal price = entry / (1 + side x slip_bps / 1e4) (journal fill vs signal reference).
- **Y2 trail after +1R**: parent bracket until the lot first reaches MFE >= +1R (fill risk); from the NEXT bar the
  target is cancelled and a trailing stop sits at (best price since entry) - side x 0.5R; the initial stop stays as
  the floor. If the parent target lies inside +1R it fills first as in the parent (no change for that trade).
- **Y3 target from the fill**: target = fill + side x k x |fill - stop|, k = parent's |target - signal| / |stop -
  signal| (same reward:risk in fill terms); stop unchanged.
- All variants keep the parent's 15:55 flatten.

## Replay ("calibrated replay", W2 of WB2 for exits that go past the live exit)
- Each live trade is walked on 1-minute SIP bars from its entry minute (the entry bar's remaining range counts from
  the next full minute) to 15:55, once with the parent bracket (R_p) and once with the variant (R_v). Inside a bar:
  stop first; a limit target needs a 3 bp (min 1c) touch-through; trail stops pay max(1c, 1 bp) + 1c slippage like
  stops; the 15:55 flatten pays the same at the 15:55 bar open. Live per-trade cost in R ((pnl - pnl_adj)/risk) is
  subtracted from both arms. Prices are rescaled if the pack and the fill differ by > 3% (W5 rule).
- **Paired effect Δ = R_v - R_p** (same engine on both arms, so engine bias cancels).
- **Calibration** reported: share of trades where R_p is within 0.10R of live R and the exit type matches; mean R_p - R_live.
  Robustness: the same Δ on calibrated trades only (pre-registered; does not change the verdict rule).

## WB2 scoring and pass rule (as W5 Part D / PROTOCOL W3-W4)
Per setup day-clustered mean Δ and SE; DerSimonian-Laird pooled μ, SE = max(SE_RE, day-clustered family SE); sign-flip
on pooled daily sums (10,000 flips, seed 20261119); leave-one-week-out; empirical-Bayes shrunk per-setup Δ.
PASS (all): t >= 2.10; permutation p < 0.01; >= 75% of leave-one-week-out folds positive; shrunk Δ > 0 for >= 2 of 3
setups and none < -0.02R; family avg R w/o best day (variant) >= parent; best-day share of the gain < 50%.
Harm (t <= -2.10 or perm p < 0.01 negative) -> backlog "do not" note proposal.
Remedies rule: improve / worsen counts and R per setup for every class.

## Paired read-out of RW3-WB4 / RW5-WB4 SPY-since-entry exits (re-scoring of 2 configs already counted by UPDAY; 0 new)
- Counterfactual on the parent's own live trades (RW3 with spy_exit_pct 0.30, RW5 with 0.40; mcf/spy_exit.py rule: bar
  k-1 SPY close vs SPY close at the entry minute, exit at bar k open, before stop/target), earlier-exit-only on the live
  trade (W5 rule, extra exit cost), Δ = R_var - R_live. WB2 statistics with N = 2 (bar 1.5). Report only; no verdict
  beyond pass/fail/harm.
- Live descriptive: WB4 copies 11-17..11-19 matched to parent signals (symbol, date, signal within 5 min), R side by side.

## Reporting
Configs tried (9 new + 2 re-scored), per setup n / sessions / parent and variant avg R and w/o best day (share), Δ ± SE,
shrunk Δ, improve/worsen; rule changes inside the window from research/ledger.jsonl; 11-19 context (10 of 14 lots
>= +0.8R; no ST7/L3 lot at target) addressed descriptively (ST7 / L3-fromopen are outside the family and not tuned).
