# latch_1103: which kinds of setups does the per-setup −2R latch help?

*Educational only — not financial advice.* Backtests (2 years, costs in) and live **paper** results (rule 7) are
labelled separately. Research only: nothing in config/, mcf/, the setups, exits, docs/live or the ledger was changed.
Categories and the decision rule were fixed in `PLAN.md` before any result was computed (commit 3f93bcb26). Two
amendments, both made before any latch delta on the full history was read: account caps (3 lots/symbol, 30 open per
setup) and the excess-delta control. Locked block 2024-11-01..2025-02-28 never read.

**Configurations: 41 cells × 3 levels = 123 (bar t ≥ 3.10); with the 147 pairwise contrasts N = 270 (bar 3.35).**

## Failures first
- **No categorical split passes.** No point-in-time category has the latch helping on one side and hurting on the
  other in TRAIN *and* VALID, so the pre-registered decision rule is not met. No DECISION card; FYI and forward shadow.
- **The key mechanism fails.** Same-day outcomes do cluster (lag-1 autocorrelation of trade R > 0 for 117 of 118
  setups, median +0.225). But after two *realised* losses the next trade loses no more often than usual
  (P(loss | 2L) − P(loss): median +0.2 pp, IQR −5.2..+2.8 pp). By the time the latch fires, the cluster has mostly
  played out: the stops come together and then the day turns.
  - "excess > +5 pp" setups: excess delta +303R (t 1.81) on TRAIN, then −49R (t −0.73) on VALID.
  - The rho split is degenerate, because rho ≤ 0 holds for only 1 setup (1 latched day).
- **On 2 years, nearly the whole saving comes from the setups losing, not from the latch's timing.** At −2R the latch
  saves +16,811R on TRAIN (t 10.6) and +6,593R on VALID (t 7.3) over 121 setups. But 72% of the setups have negative
  average R after costs (median −0.058R). Blocking trades of a losing setup saves R at any time of day.
  - The **excess delta** removes that effect: it scores the blocked trades against the setup's own average. It is
    −363R (t −0.27) on TRAIN and −409R (t −0.48) on VALID, i.e. about zero.
  - It is near zero in every point-in-time cell: |t| ≤ 1.81 on TRAIN, and no cell holds the same sign at |t| ≥ 1 on
    VALID.
- **Per-setup cherry-picking does not carry over either.** Take the setups the latch hurt on TRAIN. On VALID the
  latch moves them +17.8R (t 0.19), and their excess is −15R. That is noise, not a reversal.

## Results by category (−2R; TRAIN / VALID raw delta, then the excess delta; full tables in results.csv)
- **Side.** Long: +9,150 / +4,435R, excess −302 / −273. Short: +7,661 / +2,157R, excess −61 / −136. No split.
- **Family.**
  - Raw delta is positive for CWT, MF, RW, NS and L3, because they lose on 2 years.
  - GEN: +8.5 / −217R (t 0.08 / −1.73). At −1.5R and −3R it is negative in both halves (−38 / −207, −71 / −200), but
    its TRAIN t is only −0.26 / −0.60. "Style other" is mostly GEN.
  - Excess for every family is within ±1.5 t.
- **Entry style.**
  - Reclaim: +10,774 / +5,174R. This is CWT14 failbrk, which fires heavily and loses.
  - Fade: +3,654 / +923R. Breakout: +2,357 / +705R.
  - Excess for all three: −242..+66R.
- **Frequency.** Low-frequency setups (< 2 trades per active day) almost never reach −2R (1 latched day on TRAIN). The
  latch only matters for high-frequency setups.
- **Exit geometry.**
  - t1s05 (target > stop): excess +61 / +166R (t 0.21 / 1.00).
  - Win rate < 45%: excess +34 / +192R (t 0.13 / 1.22).
  - These lean the right way but are far below the bar.
- **Time window.** Open-only setups: +30 / −29R (≈ 0, 88 latched days). Full-day setups carry everything.
- **SPY vs open at the latch time (point-in-time).**
  - Market against the setup's side: excess −301 / −203R.
  - Market with the side: −62 / −206R.
  - So nothing.
- **Session type (hindsight, diagnostic only).** This is the one clear separator, and it cannot be known when the
  latch fires.
  - Trend sessions: excess +2,299R (t 2.33) / +775R (t 1.67).
  - Quiet sessions: −2,490R (t −4.36) / −1,014R (t −2.04).
  - Latched before a reversal (SPY's sign vs its open flips by the close): −1,712R / −1,719R (t −2.26 / −3.68).
  - The owner's picture is right in hindsight: the latch saves on trend days and costs on quiet or reversal days.
    But no point-in-time proxy tested here separates them.
- Levels −1.5R and −3R give the same picture.

## Live (paper, 10-06..11-03, 1,211 setup-days, 5 accounts; off = taken + what-ifs of latch-skipped signals)
- **Overall at −2R:** +467R saved (t 2.45, 270 latched days), but excess +10R (t 0.07).
- **By account:** Primary +31.2R (excess −6.6), T1 +88, T2 +147, GY +182, Gen +19.
- **Primary reproduction:** 11-02 the latch saved +17.8R (owner's figure 16.8R). 11-03 it cost −6.9R (owner's
  −8.19R). These numbers use the journals' r_multiple, without the fill-realism adjustment.
- **Long vs short:**
  - Longs: +413R (t 2.76, excess +96, t 0.86), mostly CWT longs in GY/T2.
  - Shorts: +54R (t 0.35).
  - **MF and RW, Primary's core shorts, are hurt live:** −25R and −46R (t −0.54 / −0.88). On 2 years they are helped
    (they lose there).
  - So the sign flips between backtest and live, at n = 30 / 31 latched days, and is not significant.
- **Rule changes inside the live window** (research/ledger.jsonl):
  - Per-setup daily stop on in T1 / T2 / Gen / GY from 10-19/20, non-latching (re-armed after a winner) until 10-22.
  - LL-LATCH (latched) from 10-23.
  - ST-A: off in T1 / T2 / Gen from 10-23. Graveyard has had it on since it opened on 10-21.
  - ST-P: Primary on from 10-29.
  - Primary size ~$4k from 10-28. GX1 5-minute clock from 10-27. CF cost filter in T1 / T2 from 10-30.
  - Many setup moves: 10-20 to 10-22, 10-26, 10-30, 11-02, 11-03.
  - The what-if sequences give every latch level the same trades, so these changes move the sample, not the
    comparison.

## Verdict and what is parked
- **No categorical split holds.** On 2 years the latch "helps" every kind of losing setup equally. Its timing adds
  nothing beyond trading less (excess ≈ 0), and live is consistent with that.
- Whether to keep the latch on Primary is a question about Primary's setups' expectancy, not about their category.
  The latch costs where a setup is genuinely positive (live MF / RW) and saves where it is negative.
- **Forward shadow:** `research/bdi/swings/hypotheses.jsonl` id `latch1103-category-shadow`. Each night it tallies,
  for each account and pre-registered category, latch on (−1.5 / −2 / −3R) vs off, raw and excess.

## Limits
- **Coverage:** 124 of 204 enabled setups (121 traded). Not covered: hold / holdtr / S exits (57), classic (14),
  heat (4), index allow-lists (5).
- **Fidelity:** base exits only (no scale-out or trail). Account-level slots and buying power are not modelled. Each
  setup is simulated on its own.
- **In-sample selection:** VALID overlaps the period many of these setups were selected on.

Files: `PLAN.md`, `bt_all.py` (trade lists with exit times), `latch.py`, `analyze.py`, `live.py`, `results.csv`,
`splits.csv`, `live_cells.csv`, `setup_props.csv`, `setups.csv`, `counts.json`, `out.txt`.
