# S6 long-hold account: management and research agenda (pre-declared 2026-10-12)

*Educational only - not financial advice. Paper account. This file is written **before** any of the ideas below is
scored. It may change only by dated amendments at the bottom. Backtests, the backtest replay and paper results are
always labelled separately (rule 7).*

Owner (2026-10-12): a dedicated Alpaca paper account for `S6_mom12_1rev_N20_W`, "tightly monitored and managed",
with ongoing research into how to handle it. The account went live on 2026-10-12 with an initial market-on-close
portfolio from the 2026-10-09 signal. The lead decided this and the owner waived the two-week dry run. After that it
runs the weekly MOO schedule in `research/longhold/DESIGN.md`.

## 1. What runs, and what is frozen
- Strategy: `mcf/longhold/signals.py` (parity-tested against `study.py`: a frozen slice in
  `tests/test_longhold_runner.py`, and the full 2016-2026 file in `make_parity_fixture.py --full`, 3 of 3 dates
  exact). Config: `config/longhold.yaml`. Both are frozen per session. Changes only outside 09:30-16:00 ET, with a
  ledger entry (rules 9-11).
- Runner: `mcf/longhold/runner.py`, workflow `.github/workflows/longhold.yml`, state branch `mcf-data-longhold`
  (`longhold/`), order ids `mcl-`.
- **Nothing in this agenda changes the live book until it passes the gates in section 3 and is approved.** Every idea
  goes into `research/backlog.jsonl` first (rule 16) with `parent: "lh-mom-revfilter"`.

## 2. Monitoring (what "tightly monitored" means; thresholds in `config/longhold.yaml`)
| signal | where | threshold / action |
|---|---|---|
| daily mark: equity, cash, day P/L, vs SPY, vs EW universe, vs backtest replay | `marks.csv`, status card | - |
| tracking difference (paper day return - replay day return) | `marks.csv: te`, `te_20d` | \|day\| > 1 % or \|20-session sum\| > 3 % -> warn; review whole-share drag, fills, data |
| drawdown from the high-water mark | `marks.csv: drawdown` | -15 % warn; -25 % no new orders (holdings kept; owner decides) |
| slippage vs the official auction print | `fills.csv` | mean \|slippage\| > 25 bps on a rebalance -> warn; compare with the model cost 1c + 1 bps |
| turnover | `marks.csv: turnover` vs `model_turnover` | backtest ~16x/yr one-way; persistent excess -> investigate |
| missed rebalance / data-sanity skip / order rejects / unfilled OPG | `status.json: alerts`, `events.jsonl` | warn; an unfilled OPG order is retried once as DAY (-r) |
| manual kill switch | `longhold/HALT` on the state branch | no orders at all while present |
| weekly report (Saturday) | `longhold/reports/weekly-<date>.html` | equity vs SPY / EW / replay, costs, holdings, events |

Review points: after 6 weekly rebalances (tracking and costs only), after 6 months (drawdown and tracking vs the
replay). Judge on tracking and drawdown, not on months of return (DESIGN.md 9). Expect 35-55 % vol and -30..-45 %
drawdowns. The backtest's CAGR is an upper bound (survivorship).

## 3. How every idea below is tested (fixed now)
- **Lineage.** S6 used its one look at the clean locked block 2024-11..2025-02 (look 1, 2026-10-10). Every overlay or
  variant below is a **new lineage** (child of `lh-mom-revfilter`). It gets its own pre-declared grid, its own
  try-count, and its own first look at the locked block. The bar rises with each look (rule 18: t >= 1.0 / 1.5 / 2.0
  / 2.5). The locked block has already been looked at by S6, so a pass there is weaker evidence than S6's was. Each
  write-up states that.
- **Data and splits.** These are the same as the longhold study: daily bars 2016-2026 and train 2017-20, valid
  2021-24.10, valid2 2025.03+. The locked block is zeroed in every simulation (`study.py` convention).
  Survivorship-cohort reruns and the top-300 large-cap rerun are reported.
- **Costs always in:** 1c/share + 1 bps per side at the open (study). Overlays that trade ETFs (hedges, BIL) pay the
  same. A 2x-cost diagnostic is reported. Once the account has fills, the measured auction slippage from `fills.csv`
  replaces the model cost in a second diagnostic.
- **Gates.** The idea must improve S6, not just pass:
  (a) longhold Tier A on the overlaid book (active vs EW > 0 in all three splits; monthly active t on train+valid >=
  `max(3.05, sqrt(2 ln N_lineage))`; active > 0 in SPY-up and SPY-down months);
  (b) higher active return than S6 in all three splits, **or**, for risk overlays, max drawdown at least 5 points
  shallower in train+valid **and** Sharpe not lower in any split;
  (c) a plateau: the neighbouring parameter values are also positive;
  (d) walk-forward share >= 60 % (rule 19);
  (e) then one locked look.
- Every configuration counts toward N (rule 3/4). Failures are reported first, with their numbers (rule 13).
- Forward check: once one is approved, it runs as a separate replay line in the status first, never by replacing S6
  in the book without the owner's decision.

## 4. Agenda (priority order)
| # | idea | grid (pre-declared size) | why | notes |
|---|---|---|---|---|
| M1 | **Rebalance band** | relative band {0, 10, 25, 50 %} on held names (4) | cuts turnover (16x/yr) and cost drag 1.3 %/yr | backlog `lh-band-diag` (DESIGN 4); a diagnostic before any live band; band = 0 until then |
| M2 | **Rebalance frequency** | W, biweekly, M; signal day Fri vs Thu (4) | monthly sibling t 2.98 "near"; fewer trades | the M sibling is already scored, so only the new cells count |
| M3 | **Names count** | N in {15, 20, 30} (N10/N50 already scored) (2 new) | concentration vs diversification; whole-share drag at small equity | neighbours of S6 in the study: N10 / N50 W are "near" |
| M4 | **Sector / industry cap** | max names per GICS sector {3, 4, 5}; per industry {2, 3} (5) | S6 is often concentrated (2022 energy, 2026 semis/storage: AAOI, AXTI, STX, WDC, SNDK, MU, TER ...) | needs a sector map (Alpaca asset attributes or a static file); point-in-time caveat |
| M5 | **Volatility targeting of the book** | target {20, 30, 40 %} ann., 63-day realised, weekly, rest in BIL (3) | vol is 33-56 %; the study's V overlays were on other bases, not S6 | the study's `vol_overlay` code exists; the sat1010 G7 "vol-scaling to EW" failed (below) |
| M6 | **Per-name inverse-vol weights** | 1/vol63 vs equal weight within the top 20, cap 12 % (1) | high-vol names dominate the risk | a weighting change, not a filter |
| M7 | **Cash buffer** | {0, 2, 5 %} in BIL (2 new) | funds MOO gap-ups without margin; lowers vol slightly | live already keeps 0.25 % (weekly) / 1 % (init) for funding |
| M8 | **Partial hedge** | short SPY or QQQ at {25, 50 %} of beta-adjusted exposure, weekly (4) | S6 beta 1.3-2.2; isolates the active return | paper account is long-only by policy: needs the owner's OK to short ETFs; borrow 3 %/yr |
| M9 | **Earnings-proximity exclusion** | skip / defer names with earnings within {3, 5} sessions of the open (2) | momentum names gap on earnings | needs point-in-time earnings dates (`mcf/data/earnings.py` covers recent years only); the sat1010 dip strategies got worse with it (not S6) |
| M10 | **Crash protection via momentum-factor volatility, held in cash/BIL (not EW)** | MOMVOL pct > {0.8, 0.9} -> 50 % BIL (2) | Daniel-Moskowitz | **mostly already tested and failed**, see 5; only the to-BIL partial version remains untested, and it is low priority |
| M11 | **Execution** | MOO vs VWAP-of-first-30-min vs prior-close limit (live A/B is not possible on one book; backtest only) (2) | measured slippage decides | after 6 rebalances of `fills.csv` |

Total pre-declared so far: 31 configurations across M1-M11. Each block is a separate lineage with its own N. The sum
is reported, so the multiple testing across blocks is visible.

## 5. Already tested on S6 and failed (do not re-run as new)
- **CWT C8/C9 overlays on S6** (`research/bdi/cwt/test_c/NOTES.md` 2.4; 7 configs): SPY > SMA200 to cash, SPY > SMA10,
  follow-through state, two closes < SMA20, Kidd 8/21 EMA exit, Keltner 3-ATR target, and the equity-curve governor
  (20 weeks). **Every one lowers S6's active return in all three splits** (-3..-58 %/yr). The governor and regime
  gates cut drawdown (-30..-33 % vs -44 %), but the Sharpe falls in most splits. None passes.
- **sat1010 momentum crash guards** (`research/bdi/saturday1010/rework/NOTES.md` 1.6 / 2.1; 18 configs on the monthly
  sibling S6M and S1W): SPY200 -> EW / BIL, true range, VIX percentile, momentum-factor vol percentile 0.7/0.8/0.9,
  bear state, vol scaling toward EW. All 18 fail and every one lowers the active t. Only to-BIL cuts drawdown, and at a
  large cost to return. Retired for these parents.
- So **regime timing and trend exits on S6 are a known dead end** here. The agenda leans to construction (M1-M4,
  M6), sizing (M5, M7) and execution (M11), where the evidence is not yet in.

## 6. Owner-facing rules for managing the book
- The book is never dumped by an automatic rule. A drawdown halt stops new orders only. Selling everything is the
  owner's call (`HALT` stops all orders; a manual liquidation is a separate, explicit request).
- The weekly signal runs whether or not the owner looks. A skipped rebalance (data, risk, halt) is reported, not
  silently retried with guessed data.
- Any change to signals, config or runner logic that changes trades = a strategy change (rules 9-11, 16). Monitoring,
  reports and dashboards = housekeeping (rule 15).

## Amendments (dated)
- (none)
