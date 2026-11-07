Educational only — not financial advice.

# ROTA1 — rolling Primary vs fixed Primary (owner 2026-11-06), study run 2026-11-07

Research only: no config, account, assignment or ledger change. Backtest numbers (2-year lab lists) and live numbers
(paper journals) are labelled separately (rule 7). The locked block 2024-11-01..2025-02-28 is never loaded.

**Result: FAIL — no rolling-book configuration reaches the bar (best t 2.36 vs 3.71, N = 975 pre-declared).
No Primary change is proposed. The light demotion-only rule also fails the bar (t 2.37) and is not proposed live.**

- **Persistence (2-year backtest): weak but real.** A setup's trailing score ranks its next 3/5/7 sessions with a mean
  Spearman rho of about +0.05..+0.12 (t 1.8..4.4) on TRAIN and on VALID; top-minus-bottom quintile spread +0.5..+1.7R
  per setup over the forward window. About half of it is an *activity* effect (quiet setups lose less R in a mostly
  losing lab set: 61 of 95 setups have negative capped avg R; total R vs trades/day corr -0.74); after controlling for
  trade count rho falls to +0.01..+0.09. **Live (paper, 24 sessions): no persistence** (rho ~0, 2-4 dates; only
  `worst` ranks, and only through activity).
- **Walk-forward:** the rolling book beats the static (today's Primary 10) book in 904 of 972 configs on both TRAIN and
  VALID (median +0.08 / +0.065 R per setup-session) — but day-clustered t tops out at **2.36**, the book itself is only
  ~flat (median -0.004R per setup-session), and the edge leans on GEN-* setups that were mined on this same history
  (removing them: 732 of 972 positive on both, FWD median -0.12R). Live (descriptive, 14 sessions) the rule
  *lost* to the static set by -0.30R per setup-session (t -1.7). vs Claude's Team: 2 sessions only, no verdict.
- **Light version (demotion only, 20-session flag):** +0.045 TRAIN / +0.052 VALID per setup-session vs static, t 2.37
  (h=5); about 2/3 of the gain is one setup (MF2-open-rsimidhi-flowsell-FD); it hurts the oversold longs NS1 / NS5.
  Live: -0.015R (t -0.6). Monday 11-09 it would bench **NS1-rsidip-rsi5pop-long** (live 15 trades, -0.131R, 38% green).

## Rule-change context in the windows (research/ledger.jsonl effective dates)
- *2-year backtest:* the lab lists run each setup's rule as configured on 11-04 over the whole history; no live
  rule change applies inside it (they are fixed rules, production costs, no account caps; capping here is ROTA1's own).
- *Live window 10-06..11-06:* per-lot stacking 10-13, refire B 10-14, twin cap + -2R setup stop 10-20, Testing setup
  stop off 10-23, GX1 clock 10-27, **Primary lot ~$4k 10-28, Primary -2R latch 10-29, CF (+BAR90) in Testing 10-30**,
  moves 10-30..11-04, **UNI1 top-500 pool in Testing 2 11-04, ROLL1 low-rep homes 11-05**. Live per-setup records
  therefore mix sizing / filter regimes; R per trade is used everywhere (sizing-neutral), the -2R latch is mimicked
  in the capping for all accounts.

## 1. Pre-declared plan (written and committed BEFORE any score was computed)

### Data
- **2-year backtest:** `research/history2y/data/bt_lab1104/sig_*.parquet` (BDI 1104 trade lists; production costs,
  stop first, 15:55 flatten; 95 setups with trades, all 10 current Primary setups covered). Sessions in the old holdouts
  (2026-04-01..06-30 and 2026-09-16..10-05) are **dropped from the series entirely** (never read, not even as
  look-back); the locked block is not in the files. Trailing windows simply span those gaps.
- Splits by the date being *scored* (forward window): **TRAIN** = 2024-10 + 2025-03..2025-12; **VALID** = 2026-01..03 +
  2026-07-01..09-15; **FWD** = 2026-10-06..11-04 (reported separately, not used to choose).
- **Live:** journals of all 7 accounts (run_id=1, closed trades), R = pnl_adj/(|entry-stop| x shares), pooled by setup
  name across accounts. 10-06..11-06, at most 24 sessions, so live windows are short (see below).
- **Setup-day series (both data sets, same rule):** per setup and session, one trade per symbol (first), the first
  **5** trades in entry order, and a **-2R per-setup daily latch** (no new entry once the day's cumulative R <= -2).
  Daily R = sum of those trades' R. This mimics Primary's one-position-per-symbol / slot limits and its 10-29 latch.
  A setup with no trade that day has daily R 0 and is not "active".

### Metrics on a trailing window of W sessions (W = long L or short 20)
- `wob` = avg R per trade without the best day = (sum R - best day's R) / (trades - best day's trades).
- `green` = share of active days with daily R > 0.
- `worst` = the worst daily R in the window.
- Qualify: >= **30** capped trades in the long window (>= 10 in the 20-session window for the persistence test).

### Step 1 — persistence
- Review dates every h sessions (h = 3 / 5 / 7, non-overlapping forward windows). At each date, for every qualified
  setup: metric on the trailing window (L = 60 and W = 20) vs forward = sum of daily R over the next h sessions.
- Report per metric (wob, green, worst, combo S1) x window x h: mean cross-sectional Spearman rho and the mean
  top-minus-bottom quintile spread of forward R, each with t over dates, on TRAIN, VALID (and FWD).
- Live: W = 10 sessions, h = 3 / 5, same statistics (few dates; descriptive only).

### Step 2 — walk-forward rolling book
- Scores (cross-sectional percentile ranks among qualified setups, each in 0..1):
  - **S1** = (rank wob + rank green + rank worst) / 3
  - **S2** = 0.5 rank wob + 0.25 rank green + 0.25 rank worst
  - **S3** = 0.7 x S1(long window) + 0.3 x S1(20-session window)
- Grid: review every **3 / 5 / 7** sessions x long window **L = 40 / 60 / 90** x score **S1 / S2 / S3** x margin
  **m = 0.05 / 0.10 / 0.20** (rank units) x max swaps **1 / 2** x book size **6 / 8 / 10** x short-window phase-out
  flag **off / on** = **972 configurations**. Bar: day-clustered t >= max(1.5, sqrt(2 ln 972)) = **3.71**.
- Mechanics: first review = top-k by score. Later reviews (after the close; the new book trades from the next
  session): a non-member is a challenger at a review if its score > weakest incumbent's score + m; it enters only
  if it was a challenger at **2 consecutive reviews**; at most `max swaps` per review, best challenger replaces
  weakest incumbent. Flag on: an incumbent whose 20-session window has avg R per trade < 0 **and** green < 0.40
  counts as weakest and is replaced by the best qualified non-member with no margin / streak needed (still within
  the swap cap).
- Book daily R = mean of member setups' daily R (equal risk per setup; R per setup-session), so books of different
  size compare.
- Baselines: **static** = today's 10 Primary setups, held throughout (note: chosen partly on this history, so it is
  in-sample favoured); **all** = equal-weight all qualified setups; **random** = random book of the same size
  re-drawn at each review (mean of 200 draws).
- Pass (all needed): (a) daily (rolling - static) difference has day-clustered t >= 3.71 on TRAIN+VALID; (b) the
  difference is positive on TRAIN and on VALID separately; (c) the chosen config sits on a plateau: its one-step
  neighbours (each knob moved one notch) are also positive on TRAIN and VALID, and their median t >= 1.5.
- Report per-setup effects for the chosen / best config: entries, exits, sessions held, R contributed vs static.
- **Light version** (reported whatever happens, 1 extra family of 3 x 1 = 3 configs): static book, demotion only —
  at each review (3 / 5 / 7) a member flagged by the 20-session rule (avg R/trade < 0 and green < 0.40) sits out
  (cash) until a later review clears it. Counted in N (total N = 975, bar still 3.71).

### Claude's Team
- The Team has only 2 sessions of picks (11-05 backfill, 11-06); it cannot be backtested. Compare on live only: the
  pooled live R per setup-session of the rule's picks (data through the prior session, live W = 10) vs the Team's
  picks vs the Primary set on 11-05 and 11-06. Descriptive, n = 2.

### Monday 11-09 pick
- If the rule passes: apply the chosen parameters to (i) the 2-year lists through 11-04 and (ii) live data through
  11-06 (live W = min(L, available)), and report both; Primary is judged on live (rule 21), so (ii) is the live view.
- If it fails: say so, and report what the light version flags for Monday.


## 2. Results (computed after the plan commit d606c339d)

### Configurations counted
| block | configs | role |
|---|---|---|
| walk-forward grid (pre-declared) | 972 | pass test |
| light demotion-only (pre-declared) | 3 | pass test |
| **N for the bar** | **975** | bar = max(1.5, sqrt(2 ln 975)) = **3.71** |
| post hoc: grid without GEN-* setups | 972 (+3 light, identical: no GEN in Primary) | sensitivity; with it N = 1,950, bar 3.89 |
| persistence cells (4 metrics x 2 windows x 3 h x 3 outcomes) + live (4 x 2 x 3) | 72 + 24 | descriptive, choose nothing |
| post hoc diagnostics: frozen-first-pick book, per-setup effects, live walk-forward (2), Team (2 days) | - | descriptive |

### Step 1 — persistence (combo score S1; full table for all metrics in `persist.csv`)
Forward = sum of capped daily R over the next h sessions; rho = mean cross-sectional Spearman over review dates
(t over dates in brackets); spread = top minus bottom quintile, R per setup over h sessions. The last two columns
were added after the first run when the activity confound showed up (forward R per trade; partial rho controlling
for trailing trade count).

| data | W | h | split | dates | rho (t) | spread R (t) | rho per-trade (t) | rho partial activity (t) |
|---|---|---|---|---|---|---|---|---|
| bt | 60 | 3 | TRAIN | 58 | +0.072 (3.7) | +0.60 (3.7) | +0.051 (2.5) | +0.026 (1.3) |
| bt | 60 | 3 | VALID | 38 | +0.085 (4.2) | +0.79 (3.7) | +0.075 (3.5) | +0.056 (3.0) |
| bt | 60 | 5 | TRAIN | 35 | +0.087 (4.3) | +0.95 (3.8) | +0.050 (2.3) | +0.023 (1.0) |
| bt | 60 | 5 | VALID | 23 | +0.106 (3.5) | +1.13 (3.1) | +0.080 (2.3) | +0.064 (2.4) |
| bt | 60 | 7 | TRAIN | 25 | +0.089 (3.1) | +1.21 (3.7) | +0.049 (1.8) | +0.014 (0.5) |
| bt | 60 | 7 | VALID | 17 | +0.125 (3.7) | +1.69 (3.1) | +0.086 (2.1) | +0.085 (2.8) |
| bt | 20 | 3 | TRAIN | 72 | +0.048 (3.4) | +0.52 (4.4) | +0.038 (2.4) | +0.025 (1.8) |
| bt | 20 | 3 | VALID | 38 | +0.080 (3.8) | +0.66 (3.4) | +0.083 (3.7) | +0.066 (3.1) |
| bt | 20 | 5 | TRAIN | 43 | +0.079 (4.4) | +0.80 (3.7) | +0.053 (2.9) | +0.048 (2.7) |
| bt | 20 | 5 | VALID | 23 | +0.079 (2.8) | +0.72 (2.0) | +0.067 (2.1) | +0.061 (2.2) |
| bt | 20 | 7 | TRAIN | 31 | +0.091 (4.0) | +1.03 (3.5) | +0.070 (3.0) | +0.058 (2.4) |
| bt | 20 | 7 | VALID | 16 | +0.063 (1.8) | +0.77 (1.6) | +0.042 (1.1) | +0.045 (1.3) |
| live | 10 | 3 | LIVE | 4 | -0.006 (-0.1) | +0.14 (0.8) | -0.093 (-1.5) | -0.032 (-0.6) |
| live | 10 | 5 | LIVE | 2 | +0.048 (-) | +0.40 (-) | -0.119 (-) | +0.019 (-) |

- By single metric: `worst` ranks best on raw forward R (rho +0.07..+0.15, t up to 9.6) but most of it is activity
  (partial rho +0.02..+0.07). `wob` (avg R without best day) alone is ~0 on TRAIN and +0.05..+0.10 on VALID;
  `green` sits in between. FWD (10-06..11-04, 2-7 dates) is positive for S1 / green / worst, ~0 or negative for wob.
- Caveat: every lab setup was built on this history (GEN-* most aggressively), so a stable cross-sectional quality
  ranking is partly in-sample; persistence here is an upper bound.

### Step 2 — walk-forward (2-year backtest; R per setup-session after costs; 144 TRAIN / 114 VALID / 22 FWD sessions)
Baselines (book R, not differences):

| book | TRAIN | VALID | FWD | t (TRAIN+VALID) |
|---|---|---|---|---|
| static = today's Primary 10 | -0.118 | -0.016 | -0.248 | -1.45 |
| all qualified setups, equal weight | -0.150 | -0.064 | -0.212 | -6.64 |
| random book (k 6-10, h 3-7; 200 draws) | -0.145..-0.153 | -0.057..-0.069 | -0.18..-0.22 | about -6.5 |

Grid (rolling minus static, R per setup-session):
- 904 of 972 positive in TRAIN and VALID; median +0.078 / +0.065 (FWD median +0.09). Day-clustered t on TRAIN+VALID:
  median 1.23, **max 2.36 (< 3.71): 0 configs pass.** The rolling book itself: median -0.004R, positive on both TRAIN
  and VALID in only 54 of 972 configs.
- Knob medians (diff t): L 40 / 60 / 90 = 1.08 / 1.17 / 1.47; score S1 / S2 / S3 = 1.19 / 1.35 / 1.18; m 0.05 /
  0.10 / 0.20 = 1.16 / 1.25 / 1.29; k 6 / 8 / 10 = 1.03 / 1.24 / 1.40; h, swaps and the short-window flag change
  little (1.20-1.30).
- **Plateau:** 139 configs are positive on both splits with all one-notch neighbours positive and neighbour median t
  >= 1.5 (`plateau.csv`). The plateau is L = 90 / S2 / m = 0.20 — at the **edge** of the grid (longest window, widest
  margin), i.e. the data prefer slow rotation drifting toward "hold the long-run best".
- Top configs (all fail the bar):

| h | L | score | m | swaps | k | flag | diff TRAIN | diff VALID | diff FWD | t TV | swaps made |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7 | 90 | S2 | 0.20 | 1 | 8 | off | +0.115 | +0.150 | +0.149 | 2.36 | 19 |
| 7 | 90 | S2 | 0.20 | 2 | 6 | off | +0.122 | +0.148 | +0.097 | 2.30 | 16 |
| 7 | 90 | S2 | 0.20 | 1 | 6 | off | +0.116 | +0.140 | +0.134 | 2.22 | 15 |
| 7 | 60 | S2 | 0.10 | 1 | 10 | on | +0.144 | +0.092 | +0.052 | 2.22 | 38 |
| 5 | 90 | S2 | 0.05 | 1 | 10 | off | +0.131 | +0.095 | +0.055 | 2.13 | 46 |

- **Representative plateau config** (h 5 = the owner's cadence, L 90, S2, m 0.20, 1 swap, k 8, flag off; all 10
  neighbours positive on both splits): diff +0.096 TRAIN / +0.110 VALID / +0.052 FWD, t 1.84; w/o best day +0.093
  (best day 9% of the gain, not a one-day result). 22 swaps in 20 months. **But vs the same book frozen at its first
  pick:** rolling - frozen = -0.007 TRAIN / +0.092 VALID / -0.035 FWD (t 1.46). On TRAIN the rotation itself adds
  nothing; the gain over static is mostly *which* setups were picked, not *rotating* them.
- **Per-setup effects (representative config, `effects_rep.csv`, `swaps_rep.csv`):** the book holds NM-AR-AM-gapdown-
  capitulation-long 98% of sessions (+0.170R per session held, +5.8 book-R), NS5 66% (+0.147), and a rotating set of
  GEN-* setups (19 of the 26 names it ever holds; 12 of those 19 negative while held, worst GEN-261028-02 -0.83R/session).
  It never holds MF2-FD (-14.1 R in static), L3 x2 (-7.7 / -7.1), MF4 x2 (-5.4 / -4.0) or RW3 (-1.7) — but it also
  never holds RW5 (+5.4 in static), and holds ST7 only 46% of sessions (+0.3 vs +5.2 in static). Today's Primary RW3/RW5/MF2 records are
  live-weighted; their 2-year lists are negative, which is most of why static loses here.
- **Without GEN-* setups (post hoc):** 732 of 972 positive on both splits, median diff +0.024 TRAIN / +0.147 VALID /
  **-0.116 FWD**, max t 2.58; representative config -0.023 TRAIN / +0.201 VALID / -0.094 FWD (t 1.37). Without the
  generator's in-sample picks the TRAIN edge nearly disappears.

### Light version (demotion only; static book, flagged member = 20-session avg R/trade < 0 and green < 40%, sits out)
| h | diff TRAIN (t) | diff VALID (t) | diff FWD | t TV |
|---|---|---|---|---|
| 3 | +0.040 (1.6) | +0.055 (1.5) | +0.082 | 2.22 |
| 5 | +0.045 (1.8) | +0.052 (1.5) | +0.013 | **2.37** |
| 7 | +0.034 (1.3) | +0.056 (1.5) | +0.035 | 2.02 |

Fails the bar (3.71), but is positive on TRAIN, VALID and FWD at every cadence, w/o best day +0.044 (best day 8%).
Per setup (h = 5, R in that setup's own units, `effects_light_h5.csv`) — 7 better, 3 worse:

| setup | share benched | R avoided TRAIN / VALID / FWD | R/session benched vs held |
|---|---|---|---|
| MF2-open-rsimidhi-flowsell-FD | 59% | +38.2 / +44.9 / +5.9 | -0.539 vs -0.449 |
| MF4-h40-open-flowsell-FD | 14% | +3.6 / +14.1 / 0 | -0.443 vs -0.152 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 12% | +0.6 / +14.8 / 0 | -0.441 vs -0.006 |
| MF4-h40-open-flowsell | 14% | +9.2 / +5.3 / 0 | -0.363 vs -0.107 |
| L3-gap-slope-fromopen-FD | 38% | +6.9 / +3.8 / -3.0 | -0.074 vs -0.360 |
| L3-gap-slope-rsi5hi-FD | 14% | +9.2 / -2.5 / 0 | -0.168 vs -0.292 |
| ST7-rsi50dn-long-pm-t1s1-FD | 7% | +1.0 / +0.3 / 0 | -0.066 vs +0.205 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 12% | +4.5 / **-11.4** / 0 | +0.197 vs +0.192 |
| NS1-rsidip-rsi5pop-long | 7% | **-2.0 / -3.3** / 0 | +0.265 vs +0.008 |
| NS5-sma50-flush-oversold-long | 11% | **-6.9 / -6.6** / 0 | +0.451 vs +0.121 |

About two thirds of the total gain is MF2-FD (a setup that loses on 2 years either way, so "benched" mostly means
"lost less"); the flag *hurts* the oversold longs (NS1 / NS5 rebound right after a bad stretch — mean reversion, the
opposite of persistence). Not targeted enough to pass the remedies rule as it stands.

### Live (paper, descriptive; `live_out.md`)
| run | sessions | rule R/setup-session | static Primary set | diff (t) |
|---|---|---|---|---|
| rolling S2, W=10, m 0.20, k 8, h 3 | 14 | -0.060 | +0.239 | -0.299 (-1.69) |
| same, h 5 | 14 | -0.054 | +0.239 | -0.293 (-1.63) |
| light, h 3 | 14 | +0.224 | +0.239 | -0.015 (-0.58) |
| light, h 5 | 14 | +0.222 | +0.239 | -0.017 (-1.73) |

The static set is today's Primary, itself chosen partly on this live record (hindsight in its favour).

**vs Claude's Team** (live R per setup-session of each group's setups that day; the rule picks 8 from live data
through the prior session):

| day | rule | Team (9 picks) | Primary set |
|---|---|---|---|
| 11-05 | +0.765 | +2.419 (backfill, picks made after the fact) | +0.588 |
| 11-06 | -0.848 | -0.104 | +0.834 |

Two sessions, one of them a hindsight backfill: no verdict either way.

### Step 3 — Monday 11-09
The rolling book **fails**, so no parameters are proposed and nothing changes. For information only:
- **Light rule on live (20 sessions through 11-06):** flags **NS1-rsidip-rsi5pop-long** only (15 trades, avg -0.131R,
  green 38%, worst -1.10R) → it would sit out Monday. Caution: NS1 / NS5 are exactly where the light rule's 2-year
  record is worst (they rebound after a flag).
- The same flag on the 2-year lists through 11-04 would bench L3-gap-slope-fromopen-FD, L3-gap-slope-rsi5hi-FD and
  MF2-open-rsimidhi-flowsell-FD instead — live and lab disagree (MF2-FD is +0.316R live over its last 53 trades,
  -0.445R/trade in its lab list over the same 20-session span), another reason not to automate this yet.
- Shadow S2 ranking on live (qualify >= 30 trades; members always ranked): weakest Primary = NS1 (0.53), L3-fromopen
  (0.59), NS5 (0.69); top non-members RW1-gapdn-bounce-flowsell-short-FD (0.80), CWT09-gapdn-bounce-g5-lowerhalf-short
  (0.74), heat_fade_long (0.73). With m = 0.20 and a 2-review streak, no challenger would enter on Monday anyway.

### What would help next (optimism, honestly scoped)
- The one consistent signal is **slow** ranking (90-session window, S2 = avg-R-w/o-best-day led, wide margin): it
  beats today's static set on every split in the backtest. As a Team variant in forward shadow (not live), it costs
  nothing and builds the live record the bar needs.
- A **targeted** demotion flag: exclude mean-reverting families (oversold dip longs) from the flag, or require the
  lab list to agree with live before benching; re-test per setup.
- Persistence must be re-tested on live once there are ~60 sessions; at 24 sessions the live test has 2-4 dates.

### Files
`build.py` (setup-day series), `common.py`, `persist.py` → `persist.csv`, `wf.py` → `wf_grid.csv`, `baselines.csv`
(+ `_nogen`), `plateau.py` → `plateau.csv`, `effects.py` → `effects_rep.csv`, `swaps_rep.csv`,
`effects_light_h5.csv`, `live.py` → `live_out.md`. Scratch inputs (journal copies, R matrices) are not committed;
rebuild with `git show origin/<branch>:journal.db > <scratch>/<branch>.db` then `python research/rota1/build.py <scratch>`.
