# Oct-7 finalists: audit (key: audit, 2026-10-08)

*Educational only — not financial advice. Everything here is a backtest on train (2026-07-15..08-25, 30 sessions) and valid (08-26..09-15, 14 sessions). The locked data (09-16..10-05 and data/cache_q2) was never read: every bar load uses `end="2026-09-16"`, and no `MCF_*_ALLOW_*` variable was set. The live days 10-06 and 10-07 were not used as evidence.*

## Verdict: 0 of 8 finalists confirmed for a holdout look

| finalist | verdict | main reason (production costs) |
|---|---|---|
| hfl_deep4 | REJECTED | Reproduces exactly, but as a change to heat_fade_long it lowers train $ (Δ −$158, t −0.29). The valid gain is not significant (Δ +$175, t 0.64, ex-best-day −$17). Every threshold from −3% to −6% lowers train $. |
| BD-hfl-nearPDL | REJECTED | The lab numbers are on a population about 3× larger than production. At production (min_adv 125M): valid +0.037R/trade, $ t 0.58, best day 86% of the total. Δ vs current heat_fade_long: t 0.18 (train) and 0.71 (valid). |
| BD-gapdn-reclaim | REJECTED | Positive at production, but its own failed parent explains most of it. Shorting every gap-down name at 13:00 makes +0.078R (train) and +0.166R (valid); that P1-gap family scored −0.049R and −0.061R on the locked holdouts. The reclaim layer adds only +0.024R (t 0.98) / +0.050R (t 1.96). 84% of train $ came from the first 2 of 6 weeks. It is one correlated cross-section bet (90% of entries at 13:00, up to 107 concurrent shorts). |
| BD-gapdn-reclaim-rsi3 | REJECTED | Same issues as BD-gapdn-reclaim. The RSI(3) layer adds nothing (production valid +0.212R vs +0.233R without it). |
| NM1 heat_fade_short 2% stop cap | REJECTED (confirms FAILED) | Valid ΔR0 +0.002 (gate +0.03). The 1.5% neighbour is −0.031R0 / −$233 on valid. |
| NM2 heat_fade_long flat 15:30 | REJECTED (confirms FAILED) | Valid ΔR0 +0.002, t 0.08, Δ$ −39. The 15:00 neighbour is −0.048R0 on valid. |
| NM3 exhaustion_short give-back 0.5R→0 | REJECTED (confirms FAILED) | Valid ΔR0 −0.004. The (0.5, 0.25) neighbour is −0.0065 on train. |
| NM4 intraday_momentum scale-out ⅓ at 0.5R | REJECTED (confirms FAILED) | Valid ΔR0 −0.014, t −1.16. |

**Checks run by this audit: 40 in total.**
- 6 production signal runs.
- 4 deep-drop thresholds.
- 7 gapdn neighbours and 3 baselines.
- 2 nearPDL neighbours.
- 12 exit re-runs.
- 6 portfolio allocations.

These are checks, not a search. Nothing was tuned.

## Engine issue found (housekeeping, affects the live heat and lab setups too)
**What happens:**
- `HeatStrategy.eligible` and `LabStrategy.eligible` return False unless `len(ctx.bars) % 5 == 0`.
- In a backtest, a full-day context is only evaluated when `n == 390`.
- SIP 1-minute bars are missing for minutes with no trades. So **every heat and lab backtest, including the live setups' and the autopsy and exits studies', only sees symbol-days with all 390 bars.**

**How much is excluded.** Share of symbol-days with all 390 bars, in a 120-symbol sample:

| day $ volume | share with all 390 bars |
|---|---|
| $95–200M | 26% |
| $200–500M | 43% |
| > $500M | 92% |

- **Example:** BD-gapdn-reclaim takes 2,576 trades on full-bar days, against 5,670 when every name is evaluated. A direct re-implementation matches all 2,576 full-bar trades to the cent.
- **Live behaviour differs.** The runner evaluates `eligible` on the running bar count, so names with missing minutes are scanned at irregular times. The live population of heat_fade_* and exhaustion_short is therefore not the population that was backtested.
- **Suggested fix:**
  - Gate on the clock time of the last bar, not on the bar count. In the backtest, evaluate every day.
  - The backtest fix is housekeeping. The live gating change alters which trades are taken, so it goes through the backlog.

## Reproduction
- **Lab frame** (`lab_repro.py`): BD-gapdn-reclaim, BD-gapdn-reclaim-rsi3, BD-hfl-nearPDL and the regime_5 parent reproduce the innovation numbers exactly. For example, gapdn train n 4512, +0.0658R, t 1.26; valid n 2365, +0.1957R, t 1.20.
- **Production path** (`collect.py`, then `analyse.py` and `portfolio.py`):
  - Entries come from `build_strategies` with HeatStrategy/LabStrategy `.signals()`, and fills from `engine.simulate`.
  - Config costs: 1c/share + 1 bps per side, +2c on stops, 3c/share on the extended tier. Next-minute entry, stop-first.
  - Sizing is the allocator rule: min($250 / risk per share, slot $1,930 / price).
  - Portfolio runs use `Backtester.allocate` together with the live setups' trades (the exits Lab base, 0 mismatches vs `engine.simulate`).
- **hfl_base matches the autopsy base exactly:** 497 train / 116 valid trades, $6.95 / $0.80 per trade.
- **The production entries are an exact subset of the lab entries.** The lab frame holds all 1,225 cache names with no ADV, price or ATR% filter, and no full-bar condition.
  - heat_fade_long: 1,595 lab entries → 497 in production.
  - gapdn: 4,512 lab entries → 1,735 in production.
- **Look-ahead:** none found.
  - gap, fromOpen, dist_pdl_atr (from ctx.prev_low), the heat components and the prior-day ATR are all known at the 5-minute bar close.
  - The entry is the next 1-minute open.
  - The deep4 first-hit rule is causal live: the first hit cannot change later.
  - All entries are at or after 11:05 (hfl) or 13:00 (gapdn).

## hfl_deep4 (filter on heat_fade_long)

| | train | valid |
|---|---|---|
| kept trades | 205 | 33 |
| $/trade (base) | $16.09 ($6.95) | $8.12 ($0.80) |
| R/trade (base) | +0.274 (+0.109) | +0.295 (−0.025) |
| day-clustered t, daily $ | 1.79 | 1.48 |
| day-clustered t, daily mean R | 0.04 | 2.20 |
| random-subset p | 0.000 | 0.019 |
| Δ $ vs current heat_fade_long (t) | **−158 (−0.29)** | +175 (0.64) |
| portfolio Δ $ (t, ex-best) | −147 (−0.28, −344) | +173 (0.64, −17) |

- **Neighbours, Δ $ vs base (train / valid):**

  | threshold | train | valid |
  |---|---|---|
  | −3% | −173 | +152 |
  | −5% | −816 | +94 |
  | −6% | −1,105 | −2 |

  The per-trade figure rises, but the system total does not, at any threshold.
- **Why that matters:** slots do not bind (160 slots), so dropped trades are not replaced by better ones.
- **Further caveats:** the threshold family was chosen after a bucket table that included valid (the autopsy says so). The valid kept-set t of 1.48 is already below the 1.5 that look 2 needs.

## BD-hfl-nearPDL

| | train | valid |
|---|---|---|
| production, min_adv 125M: n | 347 | 80 |
| R/trade | +0.177 | +0.037 |
| day-clustered t, $ / mean R | 1.98 / 0.99 | **0.58** / 1.89 |
| ex-best-day $, best-day share | +$2,178, 39% | +$28, **86%** |
| as deployed with min_adv 95M | +0.172R | −0.005R |
| Δ vs current heat_fade_long | +$125 (t 0.18) | +$109 (t 0.71) |

- **Neighbours:**
  - PDL < 0: valid +0.027R, t$ 0.59.
  - PDL < 0.5: valid +0.038R, t$ 0.49, ex-best negative.
- **Overlap:** 427 of 427 trades fall on heat_fade_long symbol-days; 395 have the identical entry; 193 are also deep4 trades.

## BD-gapdn-reclaim

**Production, full-bar days:**

| split | n | R/trade | $/trade | t (daily $) | t (daily mean R) | ex-best $ | best day |
|---|---|---|---|---|---|---|---|
| train | 1,735 | +0.120 | $4.51 | 1.47 | 2.61 | +$4,208 | 46% |
| valid | 841 | +0.233 | $4.66 | 1.56 | 0.97 | +$2,555 | 35% |

**All names (how live would behave):**

| split | n | R/trade | t (daily $) | t (daily mean R) |
|---|---|---|---|---|
| train | 3,783 | +0.099 | 1.44 | 1.92 |
| valid | 1,887 | +0.224 | 1.88 | 1.57 |

**Plateau:** every neighbour is positive on both splits. Train / valid R:

| neighbour | train | valid |
|---|---|---|
| gap 0.5 | +0.077 | +0.178 |
| gap 1.66 | +0.116 | +0.285 |
| window 12:30–14:30 | +0.034 | +0.107 |
| window 13:30–14:30 | +0.101 | +0.187 |
| window 13:00–14:00 | +0.097 | +0.224 |
| window 13:00–15:00 | +0.102 | +0.225 |

**Baselines (rule 6):**

| baseline | train | valid |
|---|---|---|
| short every name at the first window bar | −0.036R | +0.012R |
| fromOpen > 0 without the gap layer | −0.021R | +0.054R |
| **short every gap ≤ −0.88% name at 13:00** (the P1-gap parent, failed holdout look 1) | **+0.078R (t$ 1.36)** | **+0.166R (t 1.66)** |
| same-time edge vs all names (all-names version) | +0.109R, t 3.07 | +0.150R, t 1.77 |

**The reclaim layer's own increment over the gap-down parent** (day-mean R): train +0.024 (t 0.98), valid +0.050 (t 1.96).

**Concentration:**
- ISO weeks 29–30 carry $6,566 of the $7,821 train total.
- Median 46 trades a day, maximum 227. 89.5% of entries are at 13:00.
- 122 of the symbol-days overlap exhaustion_short.

**Portfolio impact:**

| version | train Δ $ (t) | valid Δ $ (t) | other effects |
|---|---|---|---|
| uncapped | +$3,873 (1.09) | +$3,563 (1.59) | up to 107 concurrent new shorts; crowds out 52 exhaustion_short trades (−$877 on train); worst valid day −$1,113 |
| capped at 20 a day | +$1,801 (1.95) | +$868 (1.30) | — |

**Why REJECTED:**
- The parent family already failed both holdouts, and the layer that is new is worth less than the parent's holdout shortfall.
- Another look leaks more of the holdout for little expected value.
- If the lead still wants to score it, it should be the 20-a-day capped form, as deployed, with the parent comparison reported next to it.

## Exit near-misses (NM1–NM4)
`exits_repro.py` re-ran each rule on its own setup only. The exits study applied the % caps to all setups at once. Numbers are in original-R units at fixed slot dollars, which avoids the R-unit trap. Train numbers match within the allocation interaction:
- NM1 train +0.0256 (t 2.09), against +0.028 / 2.28 reported.
- The others match to the reported digits.

All four fail on valid, and their neighbours are not on a plateau.

## Files
- `collect.py`, `collect2.py` (pass 2 adds the neighbours and baselines), `mods/` (nearPDL neighbours)
- `analyse.py`, `portfolio.py`, `score2.py`, `lab_repro.py`, `lab_vs_prod.py`, `exits_repro.py`
- Outputs: `standalone.json`, `portfolio.json`, `score2.json`, `exits_repro.json`. Raw candidates are in `data/` (gitignored).
