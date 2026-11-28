# RW3/RW5 1.25x profit target: re-check under today's rules (RW-TGT125)

Educational only — not financial advice.

Track (c), overnight 2026-11-27/28. Research only: no config, setup, exit or runtime change. The locked block
2024-11-01..2025-02-28 was never read (bench10 asserts on every load). Alpaca was used for GET only (1-minute bars).
Pre-registration: `exploration/sandbox/rw_target/PREREG.md`, committed (746264f59f) before any bench score from this track.

## Verdict: it does not hold. No config draft.

The "only exit change that ever passed" (WAVE2 Y1: +0.044 R/trade, t 2.58, 6 of 6 weeks up) **does not survive today's
cost model on the two-year bench**. It fails the pre-registered bar on both scored splits:

| Split (RW3 + RW5, LIVE-L costs, 11-20 rounding) | lots | parent → 1.25x avg R | Δ R/lot | day t | sign-flip p | gain on best day | weeks up |
|---|---|---|---|---|---|---|---|
| **CHECK** 2025-10..2026-11 | 7,309 | −0.104 → −0.097 | **+0.007** | 1.47 | 0.14 | 17% | 36 / 58 |
| **T2** 2023-01..2024-09 | 3,876 | −0.160 → −0.158 | **+0.003** | 0.42 | 0.68 | 36% | 54 / 89 |
| FIT 2024-10, 2025-03..09 (descriptive) | 4,045 | −0.155 → −0.163 | **−0.008** | −0.97 | 0.35 | — (loss) | 12 / 36 |

Pass needed t ≥ 2.0 and p < 0.05 on BOTH CHECK and T2. Both miss by a wide margin. The bench effect is about one sixth of
the original +0.044.

**Per setup (Remedies rule)**

| setup | CHECK Δ (t) | T2 Δ (t) | FIT Δ (t) | better / worse lots (CHECK) |
|---|---|---|---|---|
| RW3-gapdn-rsi5pop-flowsell-short-FD | +0.011 (1.90) | +0.005 (0.62) | **−0.016 (−1.55)** | 1,104 / 270 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | +0.002 (0.40) | +0.001 (0.08) | +0.001 (0.08) | 899 / 278 |

RW5 gets nothing anywhere. RW3 is mildly positive on CHECK and T2 but negative on FIT. No setup is hurt by more than 0.02R
on a scored split.

**One-big-day check.** Avg R without the best day, parent → 1.25x: CHECK −0.112 → −0.106; T2 −0.165 → −0.163;
FIT −0.166 → −0.175. Both arms lose after costs in every split. The target size does not change that.

**Primary book view** (cap 30, −2R latch on realized R): CHECK +0.17 R/day (t 1.21), T2 +0.05 R/day (t 0.76),
FIT −0.17 R/day (t −0.98). The latch effect was the caveat in the original study. It does not rescue the result.

## Why the original pass and the bench disagree

- **Mechanism, the same in both.** About 75% of lots that hit the 1.0R target go on to 1.25x and gain +0.25R each. The rest
  give it back. On the bench, 22% are flattened at 15:55 (−0.45 to −0.58R each) and **3.5% turn from target into a full
  stop (−2.0R each)**. In the original 27 live sessions, no trade went from target to stop.
- **Tape dependence.** On the bench, Δ per lot is +0.027 (CHECK) / +0.052 (T2) on SPY-down days, about 0 on flat days and
  −0.02 to −0.03 on SPY-up days. The original window (10-12..11-17) was mostly a falling tape (SPY 773 → 690). The 1.25x
  target is a bet that the fade keeps running into the close, so it pays in down tapes and costs in up tapes.
- **Costs.** On the LR8 bench basis Δ is smaller still (CHECK +0.004, T2 +0.001). Cost model choice is not what kills it.
- **Parity.** The unrounded arms reproduce tonight's shorts_autopsy T1 numbers exactly (same 7,309 / 4,045 lots, CHECK
  +0.0072, FIT −0.0073). New here: T2 (+0.005 unrounded, +0.003 rounded), per-setup splits, the book view and the live
  what-if. Rounding moves Δ by under 0.002R.

## Live what-if (Primary journal, 10-23..11-27, 326 trades, Alpaca 1-minute SIP replay)

| cut | n | live avg R (LR8) → with 1.25x | Δ R/trade | day t | sign-flip p | gain on best day |
|---|---|---|---|---|---|---|
| RW3 + RW5, all | 326 | −0.058 → −0.029 | +0.029 | 2.06 | 0.04 | 37% (11-05) |
| RW3 | 166 | −0.046 → −0.009 | +0.037 | 1.71 | 0.10 | 52% (`1 day`) |
| RW5 | 160 | −0.071 → −0.051 | +0.020 | 1.60 | 0.13 | 30% |
| 10-23..11-17 (**inside** the original study's window) | 229 | | +0.040 | 2.33 | | |
| **11-18..11-27 (new sessions only)** | 97 | | **+0.001** | 0.03 | | |

- The live result looks positive, but 70% of these trades fall inside the window where the idea was found.
- On the 97 trades after that window, the 1.25x target added nothing (+0.1R in total). The last week was −2.1R (11-23 −1.2R,
  11-25 −1.5R, both rally days).
- Avg R without the best day, live → 1.25x: −0.122 → −0.103. Still negative.
- Replay check: the parent arm lands within 0.10R of the journal on 81% of trades (mean +0.04R high). Two split-adjusted bar
  days (BITO) were rescaled. Of the 96 parent-target trades, 72 reach 1.25x, 23 are flattened and 1 goes to a stop.

## Does a rule change since then already overlap it? No.

- **11-20 stop / take-profit rounding:** moves a 1.25x limit by under 1c. Modelled on both arms (Δ shift < 0.002R).
- **FOOTRACE-EXIT (11-20):** an arena demotion rule, not a trade exit. No overlap.
- **SPYEXIT engine / giveback exits (11-17):** used only on the RW3-WB4 / RW5-WB4 copies. The Primary parents have no
  SPY or giveback exit (`scale_out_r: null`, t1s1). The giveback_1119 work parked the target classes. No overlap.
- **AV50 / ETF-STOP50 (effective 11-30):** NM-ETF-late-dip only. No overlap.
- **Not modelled:** the U9-TGT quote skip (11-19), which skips fewer entries with a farther target (small), and the
  Remedy-Q 12:30-cutoff testing copies (11-23), which are not the parents.
- **Gate if ever revisited:** PROT-27 (t1s1 default; beat it per setup with costs in over ≥ 15 Testing sessions) and
  PROT-07 (Primary core seats, epoch rule).

**Rule changes inside the windows used (research/ledger.jsonl).** Live 10-23..11-27: 10-28 Primary sizing ×2; 10-29 Primary
−2R latch; 11-11 TEAM-6; 11-12 LR8 cost model (earlier rows re-costed by cost_r_lr8); 11-17 TSZ1 (testing only);
11-19 C3-EPOCH / U9-TGT; 11-20 rounding / FOOTRACE-EXIT; 11-23 BRAKE-BURST, ST7 out, Remedy-Q copies; 11-27 half day
(flatten 12:55, modelled). The bench uses one rule set throughout, with no live rule changes.

## Configurations

- **Counted: 1.** The WAVE2 Y1 config re-checked, scored on CHECK / T2 (FIT descriptive) plus the live what-if.
- **Descriptive views of the same config: 3.** Unrounded, the LR8-bench basis and the Primary book.
- Cumulative N: about 9,373 → **about 9,374** (other tracks tonight not included).

## Recommendation

- **Do not adopt RW-TGT125.** Remove "the only exit change that ever passed" from the open list. Under today's costs it is
  +0.003 to +0.007 R/lot, not significant on two years of held-out data. It is regime-dependent (wins on down days, loses
  on up days), and it adds nothing on live sessions after its discovery window.
- PROPOSALS P3, the nightly shadow, can be **dropped or kept as zero-cost information only**. On this evidence the expected
  gain is about 0, and a 20-session shadow cannot resolve a +0.005R effect (it would need several thousand trades).
- Looking for what can be salvaged: the one consistent signal is the SPY-day split. A larger target pays on SPY-down days
  (+0.03 to +0.05 R/lot on CHECK and T2). It is not a setup-specific tweak. If anything follows, it belongs in the backlog
  as a pre-registered "market-state-dependent target" idea, tested on the whole gap-down family with a random control.
  The target would be extended only after SPY has been below its open at the time the parent target is hit, since that is
  known in real time.

## Files

- `exploration/sandbox/rw_target/`: PREREG.md, bench_rwtgt.py (bench10 wrapper, 4 arms per signal), bench_score.py with
  bench_score_out.txt and bench_rows.csv, live_rwtgt.py (journal load / Alpaca bars / replay), live_score.py with
  live_score_out.txt.
- Original study: research/crunch/wave2/exits/ (PLAN.md, RESULTS.md) and research/crunch/WAVE2.md.
- Earlier partial re-check: exploration/findings/shorts_autopsy.md (T1).
