# BDI 2026-10-15: every trade on a gap-down reversal day; index dip-bounce from the prior close (owner idea)

*Educational only - not financial advice.*

- Section 1 is one live **paper** session (rule 7), so it is a diagnosis, not evidence.
- Sections B and C are backtests on the open history (2024-09-16..2026-10-07, without the locked block), with
  production costs in.
- The rule-19 locked block (2024-11-01..2025-02-28) was never loaded:
  - Part B filters it out inside the parquet reader.
  - Part C uses the history2y loader, which refuses it. `MCF_HIST_ALLOW_LOCKED` was never set.
- `PLAN.md` was written before any configuration was scored.

**Configurations scored tonight: 99** (B 80, C1 9, C2 10).
- **0 meet a research bar.**
- One Part B row passes the pre-declared "at least as good as the open-based version" rule: GL QQQ 0.5/09:55 TRAIL on
  TQQQ. It is weak (see B).
- The owner's SPY prior-close idea does **not** pass.

## vs yesterday (2026-10-14)
| | 10-14 | 10-15 | why |
|---|---|---|---|
| Primary (journal) | +$63.53 | **-$861.83** (48 trades, 47 shorts) | Gap-down reversal: SPY -0.44% gap, low 09:57, close +0.72% vs the open. NS2 took 42 shorts, -$788.87, now flagged below backtest (52 trades, -0.500R) |
| Testing 1 | +$65.21 (restated) | **-$1,673.02** (halted 11:10) | Shorts -$1,767.66 (207 trades, 18% wins), longs +$94.64 |
| Testing 2 | -$785.74 (broker -$1,160.46) | **-$1,097.71** (broker -$1,276.34) | CWT09-g5 shorts -$683.07; CWT14 PDL longs positive |
| BDI | 480 configs, 0 pass | 99 configs, 0 research-bar pass, 1 weak comparison pass | |

Shorts lost -$3,927.94 across the three accounts. 10-14 and 10-13 favoured the shorts; today did not. The system did
not change; the direction of the day did.

## 1. Every trade (806: Primary 48, T1 225, T2 533). Rule values, path, what-ifs, opposite side, loss type
`analyse_1015.py` is `bdi1014/analyse_1014.py` re-dated, using the nightly's `trades.csv` and SIP bars. Per-trade
output is in `trades_analysis_1015.csv`, per-setup in `per_setup_1015.csv`. The method is unchanged: 1-minute path,
stop-first, costs in. The base re-simulation correlates with the journal at 0.941 (P), 0.957 (T1) and 0.919 (T2).

| acct | journal R | base | BE@0.5R | trail 0.5R | t 0.5R | t 1R | hold 15:55 | SAR | re-entry | opposite 1R/1R |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary | -0.563 | -0.611 | -0.531 | -0.576 | -0.536 | -0.621 | -0.838 | **-0.260** | -0.677 | +0.444 |
| T1 | -0.641 | -0.691 | -0.597 | -0.599 | -0.568 | -0.780 | -0.819 | **-0.426** | -0.961 | +0.426 |
| T2 | -0.143 | -0.221 | -0.225 | -0.229 | -0.133 | -0.152 | +0.132 | -0.194 | -0.253 | -0.114 |

**Exits**
- No exit overlay rescues a wrong-direction day. Breakeven at 0.5R and a 0.5R target cut the loss by only 0.05-0.12R.
- Holding to 15:55 is worst for Primary and T1, and best for T2 (+0.132; its longs ran with the index).

**Stop-and-reverse**
- The SAR leg adds +0.48R per stop on Primary (35 stops) and +0.36R on T1 (166 stops): the shorts were stopped and the
  index kept rising.
- This is the 10-14 lesson mirrored: SAR follows the day's direction. History (bdi1014, 480 configs) showed no edge of
  its own.

**Re-entry** after a stop, same side: -0.63R (P, 5), -1.79R (T1, 34), -0.39R (T2, 44). Refire on T1: 5 trades,
-1.10R.

**Rule values at entry, NS2 (P and T1)**
| | fromOpen | VWAP | RSI5 | QQQ fromOpen |
|---|---|---|---|---|
| Losers | +3.6..3.8% | +2.7..2.9% | 91-92 | +0.6..0.7% |
| Winners | +2.8..3.2% | | 89-90 | same |

The distributions overlap. No entry value separates the two groups beyond noise.

**Opposite side, with a hindsight check.**
- The pointer (QQQ fromOpen >= 0.25% against the trade, with the stock beyond its VWAP) was set on 275 trades. For
  those, the opposite-side R is +0.656 against -0.234 when it is not set.
- On 10-14 the same pointer was noise (-0.062 against -0.042).
- Its causal version was tested on history in C2 and fails.
- So the "opposite side would have won" reading is hindsight from the day's direction.

**Loss types** (438 losers, merged into `patterns.csv` by date, idempotent):

| account | wrong_side_big_swing | never_worked | small MFE then failed | gave_back | stopped_then_reversed | late_hold |
|---|---|---|---|---|---|---|
| Primary (38) | **24** | 2 | 5 | 6 | 1 | 0 |
| T1 (176) | **70** | 30 | 36 | 22 | 13 | 5 |
| T2 (224) | 30 | **59** | 55 | 38 | 40 | 2 |

## 2. Recurring patterns turned into rules (54 setup x loss-type pairs on 3+ days, including today)
| pattern (days) | testable rule (known at entry) | status |
|---|---|---|
| Short books wrong_side_after_big_swing (today: P 24, T1 70) | no new short while SPY fromOpen >= 0.25 / 0.50% | **tested, failed** (C2, 10 configs). The nightly's cluster skip and gap-reclaim veto also failed (10 configs) |
| RW2-FD never_worked (4 days) | fromOpen >= F or RSI5 >= R | **tested, failed** (C1, 9 configs). Closed |
| heat_fade_short(-FD) never_worked / small MFE / gave_back (4-5 days) | not testable in the lab frames (heat type) | under rule-20 review (ex-primary below backtest); a heat-frame harness is queued |
| L3-gap-slope-fromopen-FD wrong_side (3 days, new); 732 refire signals | cap refires per symbol-day | queued (`nightly-1015-l3-fromopen-refire-cap`) |
| LIQ-orl late_hold (3 days, new) | per-setup late exit | queued (it made +$77 today) |
| CWT14 all variants (4 of 4 T2 sessions) | SAR | lineage closed 10-14. The setups are -0.09R on history, so they go to the rule-20 review |

## B. Index dip-bounce from the PRIOR CLOSE (owner idea). 80 configurations. Not as good on SPY
`pcdip.py`, pre-declared in `PLAN.md` Part B.
- Same production class, fills and costs as `idxdip1015`.
- The open-based setups were re-run in the same harness. Parity holds: IDX5 +0.512 (14), IDX2 +0.777 (5), IDX3 +0.468
  (7), IDX1 trail +0.003 / hold +0.148 (8), all equal to `pick3x_results.csv`.
- DEV is 359 sessions. Lineage **1,214**, so the bar is **t >= 3.77. Not met by any row; the best t is 1.55.**

**Failures first: the owner's SPY version** (3x pick, TRAIL; n / mean R / t):
| prior-close row | PC | mapped open-based | extra gap days only | control, all days |
|---|---|---|---|---|
| SPY 0.5% by 09:45 | 50 / +0.065 / 0.41 | IDX5 14 / +0.512 / 1.00 | 44 / +0.013 | -0.097 |
| SPY 0.5% by 09:55 | 60 / +0.091 / 0.64 | none | - | -0.097 |
| SPY 0.75% by 09:45 and 09:55 (same 34 trades) | 34 / +0.165 / 0.81 | IDX2 5 / +0.777; IDX3 7 / +0.468 | 32 / +0.106 | -0.097 |
| SPY 1.0% by 09:45 | 21 / +0.421 / 1.45 (HOLD +0.522 / 1.55) | none | 21 / +0.421 | -0.097 |

- Measuring from the prior close trades 3-7 times as often.
- The extra days are mostly gap-down sessions and add only +0.01..+0.11R. The mean R per trade falls below the
  open-based setups.
- The 1.0% row looks best, but it has no open-based counterpart, so it was not eligible under the plan. It is queued
  for forward sessions only.
  - Down sessions -0.72R (5), up sessions +1.08R (13).
  - H1 +0.72R, H2 +0.15R.
- QQQ PC rows run -0.04..+0.11R.
- **The trigger is not selective.** 32 of 50 SPY triggers (and 26 of 43 GL-QQQ triggers) come on the first eligible
  bar (09:49).
- **On 2026-10-15** (out of sample, `today1015_out.txt`):
  - PC SPY 0.5 fired at 09:49 on SPXL and was **stopped at 09:55, -1.04R**. That is before the 09:57 low the owner saw.
  - PC SPY 0.75 and 1.0 did not fire (the low was -0.67% vs the prior close).
  - So this rule would not have caught the owner's bounce. A trigger that waits for a new low inside the window is
    queued (`bdi1015-idxdip-late-low-trigger`).

**Gap-down + early low (GL), 32 configs.**
- SPY g 0.5: +0.218R (26, t 0.87). That is below IDX5 and IDX3 TRAIL. SPY g 0.3 is negative.
- **QQQ g 0.5 by 09:55 on TQQQ, TRAIL: +0.160R, n 43, t 0.89, ex-best +0.079.** It is the only row that passes the
  pre-declared rule:
  - Mean R and t are at or above IDX1 TRAIL (+0.003, t 0.01).
  - The 42 extra days give +0.086R.
  - It beats the all-days control (-0.149R).
  - Plateau: g 0.3 is +0.024R.
  - Holdout, scored once: **n 10, +0.007R.**
- Same days at a random time: +0.137R. The gap-day condition carries the result, not the trigger.
- It **fails the rule-19 regime gate**: down -0.65R (14), flat -0.13R (11), up +0.96R (18). It is fading: H1 +0.621R,
  H2 +0.001R, 2026Q1 -0.11R, 2026Q3 -0.22R.
- 10-15: it fired at 10:01 and made +1.81R (IDX1 did not fire).

## C. Pattern rules on history. 19 configurations, 0 pass
`crules.py`, pre-declared in `PLAN.md` Part C. The inputs are the nightly1015 first-signal hits, with production and
time-of-day costs. Results are in `crules_results.csv`.

**C1 RW2-FD extension floor** (9 configs, bar 2.10):
- 6 of the 9 are no-ops: RW2's own rules already imply the floor (baseline -0.059R, n 22,187).
- The three RSI5 >= 95 versions lower the expectancy (-0.004..-0.006R).
- Live 10-15 contradicts the 10-14 split: extended entries -0.373R (51) against the rest -0.158R (9). **Closed.**

**C2 index-up short veto** (SPY fromOpen >= 0.25 / 0.50%, 5 setups, 10 configs, bar 2.45):
- 0 pass.
- The veto lowers expectancy in 7 of 10, and lowers it in up sessions in 10 of 10 (-0.05..-0.26R). It delays the
  first signal to a later, worse bar.
- NS2's first signals taken while SPY is up >= 0.25% are its *better* half (+0.065R, n 1,587).
- No rule known at entry has yet separated reversal-day shorts (4 rules, 20 configs, nightly and BDI).

## Proposed changes for 2026-10-16 (exact text in `PROPOSED_CONFIG.md`; nothing applied)
1. **Testing 1, optional:** `IDX6-qqq-gapdn050-earlylow-0955-TQQQ-trail`.
   - Class `index_dip_bounce`, with new options `dip_ref: prior_close`, `gap_min_pct: 0.5` and
     `below_open_pct: 0.10`.
   - It needs a code change in `index_dip.py`, `DayContext.peer_prev_close`, the backtester and the runner. That is
     described, not made, because another agent is editing the runner.
   - The evidence is weak (regime gate fails, fading, holdout +0.007R). It is the owner's call.
2. **Primary, owner decision:** review `NS2-sma50break-overbought-short` under its scorecard flag.
   - If the owner demotes it, it goes to Testing 1 with a `former_primary` marker, as NS3 did.
   - History is flat (+0.004R, t 0.07) and fails the regime gate.
3. Nothing else. Nothing met the Primary bar.

## Backlog (`add_backlog.py`; `research/BACKLOG.md` regenerated, 408 entries)
| id | status | configs |
|---|---|---|
| `bdi1015-idxdip-prior-close` | failed | 48 |
| `bdi1015-idxdip-gapdn-earlylow` | idea (IDX6 proposed for a forward test) | 32 |
| `bdi1015-idxdip-pc-spy100` | idea (forward sessions only) | 0 (scored inside the 48) |
| `bdi1015-idxdip-late-low-trigger` | idea | 0 |
| `bdi1015-short-index-up-veto` | failed | 10 |
| `bdi1014-rw2-extension-floor` | idea -> **failed** | 9 |

## Queued
1. The late-low trigger rework for the idxdip lineage (count it in 1,214).
2. A heat-frame harness, so that heat_fade_short(-FD) patterns can be tested.
3. A LIQ-orl per-setup late exit.
4. The L3-fromopen refire cap.
5. An owner rule-20 review pack for the CWT14 and CWT09 Testing 2 setups.

## Files
- `PLAN.md`.
- `analyse_1015.py`, which writes `trades_analysis_1015.csv` and `per_setup_1015.csv` and merges into `patterns.csv`.
- `pcdip.py`, which writes `pcdip_results.csv`, `pcdip_trades_dev.csv`, `pcdip_open_trades_dev.csv` and
  `pcdip_counts.json`.
- `today1015.py` with `fetch_prev.py`, which write `today1015_out.txt`.
- `crules.py`, which writes `crules_results.csv`.
- `add_backlog.py`.
- `PROPOSED_CONFIG.md`.
