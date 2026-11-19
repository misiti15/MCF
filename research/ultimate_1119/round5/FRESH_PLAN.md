Educational only — not financial advice

# Round 5 — FRESH-window plan (pre-registered before any fresh data exists)

Written 2026-11-19 (UTC ~10:00) by the lead consultant of the "ultimate setup" job. Research only: no setup, exit, YAML,
account or ledger change. When this file was written, `/home/user/MCF/data/cache_fresh/` did not exist. No bar, frame
or signal from 2023-01-03..2024-09-13 had been downloaded or read by this job (FREEZE_CORE.json records
`fresh_data_exists_at_freeze: false`).

## 0. Why a fresh window
Rounds 1-4 tried 35 candidates (cumulative N ~1,000 configs) and none beat the benchmark. Two narrow edges held up out of
sample:
- **leg E**, the WB4 late-afternoon ETF dip;
- **leg M**, the one-bar RSI(14) collapse in very liquid stocks.

Both match the two benchmark setups that are positive on the check half (NM-ETF-late-dip and ST7-FD). The 2025-10..2026-11
check half has now informed the design of E and M (ULT-12/13/22/23/32), so it can no longer judge them. A window nobody
has looked at is required.

## 1. Windows (fixed)
| Name | Dates | Sessions | Use |
|---|---|---|---|
| WARM-UP | 2022-10-03..2022-12-30 | ~62 | feature warm-up only (adv20, daily ATR, RSI, DI). Never scored |
| **FRESH** | **2023-01-03..2024-09-13** | **427** | scored **once** per frozen rule |
| FRESH-1 (descriptive) | 2023-01-03..2023-12-29 | 250 | split report only |
| FRESH-2 (descriptive) | 2024-01-02..2024-09-13 | 177 | split report only |
| 2-year cache, open history | 2024-09-16..2026-11-04 minus the locked block | — | already used (FIT / CHECK of rounds 1-4) |
| **LOCKED** | **2024-11-01..2025-02-28** | — | **never read** |

- The download stops at 2024-09-14T00:00Z. Every fresh frame, trade list and 1-minute load asserts `date <= 2024-09-13`
  and `date >= 2022-10-03`. `MCF_HIST_ALLOW_LOCKED` is never set.
- **Session calendar.** The frozen `modules/ULT-28.py` NYSE_HOLIDAYS list starts in 2024. The fresh harness adds the
  2022-2023 NYSE holidays: 2022-11-24, 2022-12-26, 2023-01-02, 2023-01-16, 2023-02-20, 2023-04-07, 2023-05-29,
  2023-06-19, 2023-07-04, 2023-09-04, 2023-11-23, 2023-12-25. It then cross-checks the calendar against the SPY bar
  dates; any mismatch aborts the run.
- **Half days** (2023-07-03, 2023-11-24, 2024-07-03) are kept, as in the 2-year history. They produce no 14:00-15:00
  rows.
- "/session" and "R/session" divide by all 427 FRESH sessions.

## 2. Pipeline (same as rounds 2-4; only paths and the date range may change)
1. **Download.** Same logic as `research/history2y/download.py` (SIP feed, `adjustment=split`, RTH only, BarStore format).
   - Output: `/home/user/MCF/data/cache_fresh/1Min/<SYM>.parquet` (outside git).
   - Range 2022-10-03..2024-09-14T00:00Z.
   - SPY and QQQ are downloaded first. Keys are read from the environment and never logged.
2. **Frames.** Per symbol, `build_frames.one_chunk` logic: `daily_table` → adv20 (prior 20 sessions, min 5), then
   `setup_lab.build(resample 5min)`, merging adv20 on date.
   - Rows: bar closes 09:50-15:00.
   - Forward columns (`win_*`, `r_long*`, `r_short*`, `*heat*`) are dropped and asserted absent, as `ULT-32/bt.py` does.
3. **Context.** `spy_fo` and `qqq_fo` are each the ETF's own fromOpen at that bar close, the same definition as
   `mcf.strategies.lab_context.context_from_frames`.
   - Breadth columns are **not** built: the fresh universe is a subset of the lab list, so lab breadth cannot be
     reproduced.
   - None of the frozen rules R1-R6 reads breadth (asserted). Hunt candidates may not use it either (sec. 4).
4. **Streaming (disk ~4.4 GB free).** For each symbol:
   - download → frame → every frozen rule's superset rows (with flags);
   - walk those rows on 1-minute bars: the round-4 chassis (`ULT-28/bt.py` walk/walk_job/cost_R) and the benchmark walk
     (`benchmark/bench.py` walk1);
   - walk the random-control rows for the same symbol;
   - then delete the bars, unless the symbol is in `symbols_retained.txt`.

   Only signal and walk rows are kept (a few MB). A disk guard stops the run if free space falls below 1.0 GB.
   Cross-symbol steps run only after the stream ends, on the stored rows: one lot per symbol, refire chain, day cap 30,
   ADV ordering.
5. **Overrides allowed in the fresh harness** (thin wrapper `round5/fresh_bt.py`). It imports the frozen files and may
   change only:
   - DATA / CACHE paths;
   - the half definitions (FRESH, FRESH-1, FRESH-2);
   - the date range in `blackout_set()`: 2022-10-03..2024-10-31 instead of 2024-08-01..2026-12-31, with the same ±4
     sessions on report date and reaction day;
   - the holiday list (above);
   - the frame source (streamed frames instead of `lib.load_month`);
   - the removal of the 5-minute headtail cross-check column in bench.py (no headtail file exists for 2023-24).

   **No threshold, window, exit, cost, refire, cap or universe parameter may change.**
   - Before scoring, `fresh_bt.py` re-hashes every file in `FREEZE_CORE.json` (and `FREEZE_HUNT.json`) and aborts on any
     mismatch.
   - It also refuses to run unless this file's sha256 matches `FRESH_PLAN.sha256`.
6. **Parity check (before scoring; uses only already-open data).** Run `fresh_bt.py` on one open 2-year month
   (2025-10, from data/cache_hist).
   - It must reproduce ULT-32 32e's trades for that month and the benchmark's ST7-FD / NM-ETF trades for that month
     (symbol, date, tod, R within 1e-6).
   - Any difference is fixed in the harness, never in a rule, before the first fresh byte is downloaded.
7. **Costs (always in).**
   - LR8 research basis: entry 1c + 1 bp × time-of-day multiplier; exit 1c + 1 bp except target (limit) fills; +2c on
     stops.
   - The benchmark pipeline also applies its ×3 extended tier.
   - Shorts (hunt only; R1-R6 are long) pay the round-4 borrow estimate: 1.2 bp of entry notional (3 bp under $20). On
     reaction days it is 5 bp (8 bp under $20), with the ×1.5 reaction-day surcharge before 10:30.
   - Shorts are limited to today's easy-to-borrow list (a bias that favours shorts).
8. **Statistics.** `ULT-23/bt.py` `stats()` / `sub_halves()`:
   - avg R, avg R w/o best day, best-day share (`1 day` tag at >= 50%);
   - total R, R/session, worst day and worst day / trade-session;
   - day-clustered t, SPY up/flat/down (±0.30% open→close);
   - median hold, exit mix;
   - FRESH-1 / FRESH-2;
   - random control: same symbol-sessions, side, exit and leg window, with a random decision bar (seed 1119). Signal
     minus random is the read that is neutral to survivorship.

## 3. Frozen rules scored on FRESH (R1-R6)
Code, reference files and sha256 are in `round5/FREEZE_CORE.json` (git HEAD 97a93a56b799…, frozen 2026-11-19T09:57Z),
with copies in `round5/frozen/`. Key hashes (first 16 hex):
- `modules/ULT-32.py` 548796c8a7d4081a
- `modules/ULT-32_symbols.json` 5d200e9a54f1b96b
- `round4/ULT-32/bt.py` ec32b6439d25449a
- `round4/ULT-28/bt.py` c960a487de50f58f
- `round3/ULT-23/bt.py` c3d625f1f8119297
- `modules/ULT-28.py` 85f8e5277716d9b9
- `modules/ULT-23.py` effc5534986c105c
- `round4/data/earnings_yf.parquet` b80cdc46f4508312
- `benchmark/bench.py` 8943cb33f8d29f63
- `benchmark/stats.py` e3625dfafaa69ccd
- ST7-FD module f2750193891fe2bf
- NM-ETF module 6c47c7ec8c7723ed
- `config/default.yaml` ea4723767bc1092c
- `mcf/research/arena/indicators.py` bf2dc920b7726249
- `mcf/research/setup_lab.py` bd260b4979acf7e9
- `mcf/research/gates.py` 6af8a7afc69aec88
- `mcf/strategies/setups.py` a3afeab8d3f527f2

### R1 BOOK-EM = ULT-32 config 32e, exactly as coded and scored
`book(S, cfg={"adv": 500e6, "rmax": 30.0, "d_on": False}, cap=30, blackout=True)` in `round4/ULT-32/bt.py`. The
superset rows come from `month_job` (features from `modules/ULT-32.py: features(f, adv_md=500e6)`, then
`leg_mask(r, "E")` and `leg_mask(r, "M", rmax=35.0)`). The book then filters M to rsi <= 30.
- **Intake (both legs):**
  - price >= $10, |gap| < 20%, atr_d > 0, spy_fo present;
  - cost_r = ((1c + 1 bp) × tod mult + 1c + 1 bp + 2c) / (0.25 × atr_d);
  - universal long filter: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0.
- **Leg E (WB4 exact, long):**
  - symbols = W ∩ lab = 100 ETFs. The 24 W names not in the lab cache were never scored, so they stay out;
  - adv20 >= $95M, cost_r <= 0.10, bar close 14:00-15:00;
  - ret3 <= -0.75%, di_diff7 >= -5, ret12 >= -1.0%, atr_d_pct >= 3.5967583179473883;
  - exit t05s1 (+0.5u target / -1u stop, R per u, u = 0.25 × atr_d).
- **Leg M (RSI collapse, liquid stocks, long):**
  - symbols = STOCKS minus FUNDS, adv20 >= $500M (point in time), price >= $20, cost_r <= 0.08, bar close 10:15-15:00;
  - RSI14 of the bar exactly 5 min earlier >= 50 AND RSI14 now <= 30;
  - fromOpen <= -min(1.0%, 0.30 × atr_d%); buyPressure > 0;
  - earnings blackout: report date or reaction day within ±4 sessions;
  - exit t1s1 (+1u / -1u).
- **Chassis:**
  - entry at the OPEN of the 1-minute bar that starts at the decision-bar close; brackets around the decision close;
  - stop first, then target; stop gap-through at the worse of open/stop; target at the limit with no exit cost;
  - +2c on stops; 45-min time exit; flat by 15:50 (the 15:49 minute);
  - one lot per symbol across legs; refire >= 30 min after the exit; max 2 per symbol-session; day cap 30, ordered by
    (date, tod, adv20 desc).
- Long only, so no borrow fee applies.

### R2 leg E alone, R3 leg M alone
These are the R1 trades split by leg. The legs use disjoint universes (ETFs vs non-fund stocks), so this equals running
each leg alone unless the day cap binds. The uncapped count is reported to show that it does not.

### R4 ST7-FD and R5 NM-ETF-late-dip (benchmark pipeline, as in benchmark/BENCHMARK.md)
`bench.py` logic:
- live module + `config/default.yaml` entry (min_adv $95M on point-in-time adv20; window [950,1500] / [1400,1500]);
- refire chain `mcf.strategies.setups.refire_select` per the YAML;
- entry = decision-bar close, R = 0.25 × atr_d;
- 1-minute walk (stop first, then target, gap-through), flat 15:55; LR8 costs with the ×3 extended tier.

ST7-FD runs on every downloaded symbol (the lab list with max adv20 >= $95M). NM-ETF uses its module SYMBOLS ∩
downloaded (= W ∩ lab, 100).

### R6 ST7-base on the round-4 chassis
`dissect_configs()["ST7-base"]`: fam st7, all 4 layers, 09:50-15:00, adv20 >= $95M, exit T. This gives a like-for-like
comparison with R1-R3 on the same chassis. WB4-base on the chassis is the same rule as leg E (R2), so it is not scored
again.

### Check-half reference (2025-10-01..2026-11-04, 276 sessions; already seen, so these are reference figures, not evidence)
| Rule | /session | avg R | w/o best day | best-day share | R/session | t | Fit avg R |
|---|---|---|---|---|---|---|---|
| R1 BOOK-EM (32e) | 1.24 | +0.115 | +0.099 | 15% | +0.142 | 3.29 | +0.188 |
| R2 leg E | 0.82 | +0.110 | +0.096 | — | +0.090 | 2.87 | +0.219 |
| R3 leg M | 0.42 | +0.124 | +0.084 | — | +0.052 | 1.80 | -0.051 |
| R4 ST7-FD (bench) | 3.13 | +0.084 | +0.073 | 13% | +0.262 | — | -0.132 |
| R5 NM-ETF-late-dip (bench) | 0.95 | +0.052 | +0.039 | 28% | +0.049 | — | +0.269 |
| R6 ST7-base (chassis) | 2.23 | +0.094 | +0.078 | 18% | +0.209 | 2.41 | -0.143 |

Caveats on these references:
- The R1 check figure comes from the ULT-32 check plateau, read after the single score, which is why it is check-informed.
- Leg M was negative on fit (31 trades). Leg M at ADV >= $1B was positive in both halves (ULT-23), but $500M is the frozen
  parameter.

## 4. Volume-track slot: up to 6 new narrow-edge candidates (H1..H6)
The hunt stage may freeze **at most 6** candidates on the open 2-year data (FIT and/or CHECK) before any fresh byte is
downloaded. Each candidate must:
1. be a module + parameter set scored through the same round-4 chassis (or the benchmark pipeline), with LR8 costs and
   the borrow estimate on shorts;
2. take entries from 09:50, be flat by 15:50, and have a median hold of 5-45 min;
3. trade long, short or both, on any symbols in `symbols_download_all.txt`;
4. use only point-in-time features from the symbol's own bars plus SPY/QQQ/context-ETF frames; no breadth, no
   cross-sectional ranks over the lab universe, no future earnings data (scheduled dates are allowed);
5. be **positive on the 2025-10..2026-11 check half** (avg R > 0 and w/o best day > 0 after costs), and report fit too;
6. report its configuration count; this is added to the job's cumulative N (996-1,012 before round 5);
7. be written into `round5/FREEZE_HUNT.json` before the download starts. The entry holds the name, module path + sha256,
   exact parameters, universe, side, exits, check-half figures and the hunt's config count. A matching table goes in
   `round5/HUNT_FREEZE.md`. The FREEZE_HUNT timestamp must be earlier than the first fresh file's mtime (asserted).

Candidates not frozen by then are not scored on FRESH. A hunt slot may stay empty; we never force weak setups. A hunt
candidate may be added to the book only as its own leg (BOOK-EM+H) if that combination is itself one of the ≤ 6 frozen
rules.

### 4-V. Volume-track entries (H5V hunt), appended 2026-11-19T10:13Z, before any fresh byte existed
Source: `round5/hunt_volume/` (PLAN.md, RESULTS.md, H5V.py, hunt.py, test_module.py) and the freeze file
`round5/hunt_volume/FREEZE_VOLUME.json` (sha256 of the module, the backtest and every dependency, plus the exact rules).
`/home/user/MCF/data/cache_fresh` did not exist at freeze (asserted). The lead merges these two entries into
`round5/FREEZE_HUNT.json`. The hunt deliberately did not create that file, because its existence unlocks the download
while other tracks may still be freezing.

- **Hunt:** 7 legs, 40 configs, FIT pick by total R, CHECK scored once.
- **Keep rule:** check avg R > 0 and w/o best day > 0, at most 6.
- **Result:** 2 kept, 5 dropped (F, S, C, V, Q).

| Id | Rule (module `round5/hunt_volume/H5V.py`, sha256 1aba95f091c37af6…, frozen P) | Side / exit | Check /session | Check avg R | w/o best day | best-day share | t | Fit avg R (w/o best) |
|---|---|---|---|---|---|---|---|---|
| H-V1 | leg X, the WB4 mirror. W list, adv20 >= $95M, 14:00-15:00; ret3 >= +0.75%, di_diff7 <= +5, ret12 <= +1.0%, atr_d_pct >= 3.5968; cost_r <= 0.10; easy-to-borrow only | short / t05s1 | 0.58 | +0.105 | +0.078 | 32% | 1.77 | +0.095 (+0.048; 55% **1 day**) |
| H-V2 | leg K, one-bar shock snap. EQB ETFs adv20 >= $300M, 10:15-15:00; 5-min return <= -0.2 x atr_d%, vol_climax >= 2; cost_r <= 0.10; SPY long filter | long / t1s1 | 1.00 | +0.187 | +0.095 | **54% (1 day)** | 1.46 | +0.116 (-0.008; 106% **1 day**) |

**How both are run.** Both use the round-4 chassis (ULT-28 walk + LR8 cost_R, R per u = 0.25 x atr_d, 45-min time
exit, flat by 15:50). Shorts pay the 1.2 bp borrow (3 bp under $20). Selection follows `hunt.py select()`: one lot per
symbol, max 2 per symbol-session, refire >= 30 min after the exit, day cap 30. The fresh overrides allowed are those of
sec. 2.5.

**Warnings.**
- **H-V2 is lumpy.** The top two check days (2026-06-17, 2025-10-29) carry 90% of its check total R, and without them
  its avg R is +0.022.
- **H-V1 and H-V2 move together.** Their daily R correlation is 0.43, and they share their best check day with each
  other and with leg E.
- **H-V1 is concentrated.** SOXL, NUGT and TECL make up 66% of its check trades.

**Effect on M and N.** With R1-R6 plus H-V1 and H-V2, M = 8 and the t bar is 2.039 (if no other track adds rules).
Cumulative N goes up by 40, to 1,036 (up to 1,052).

**This edit changes the sha256 of this file.** `FRESH_PLAN.sha256` was left unchanged on purpose. The lead re-hashes
once every track's slot is in, and until then `download_fresh.py` refuses to run (a safe failure).

## 5. FRESH pass bar (pre-registered)
**M** = the number of rules scored on FRESH = 6 (R1-R6) + the number of frozen hunt rules (0-6). M is fixed when
FREEZE_HUNT.json is written. The benchmark rules count too, so the bar is conservative.

| M | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|
| t bar = max(1.5, sqrt(2 ln M)) | 1.893 | 1.973 | 2.039 | 2.096 | 2.146 | 2.190 | 2.229 |

A book (or single rule, R1-R3 and H*) **BEATS** only if all of these hold on FRESH (2023-01-03..2024-09-13, 427
sessions, costs in):
1. avg R > **+0.0836**;
2. avg R w/o best day > **+0.0734**;
3. total R/session > **0**;
4. day-clustered t >= **max(1.5, sqrt(2 ln M))**;
5. it was **positive on the 2025-10..2026-11 check half** (avg R > 0 there). R1, R2 and R3 are (+0.115 / +0.110 /
   +0.124).

**Always reported next to the bar (not pass conditions):**
- trades/session, compared with ST7-FD;
- R/session, compared with ST7-FD's on FRESH and with its check figure (+0.262);
- worst day / trade-session (the round 1-4 bar was >= -2.152);
- best-day share with the `1 day` tag;
- FRESH-1 / FRESH-2;
- SPY up / flat / down;
- signal minus random;
- whether the rule beats ST7-FD's own FRESH avg R.

**How to read the result:**
- BEATS → a backlog screening pass (RESEARCH_RULES 15-17). It is not a promotion and needs the job's deploy rule and the
  owner's yes.
- A fresh avg R below the bar, or a sign flip between FRESH-1 and FRESH-2, is reported as a failure. No re-tuning on
  FRESH is allowed.
- Any later variant needs a new untouched window.

**Single score.** Each rule's FRESH result is written once to `round5/fresh_once.json` with a UTC time stamp.
- If a harness bug is found after scoring, the fix touches only the harness, never a rule.
- Both runs are reported, with the reason.

## 6. Symbol universe (taken from the lab list; `round5/universe_fresh.json`)
| Group | Count | Rule |
|---|---|---|
| W ∩ lab (legs E, NM-ETF) | 100 | exact WB4 list; 24 W names not in the lab cache (BULZ, DDM, DOG, DPST, DUST, DXD, ERX, FAS, FAZ, FNGU, IVV, JNUG, LABU, RSP, SH, SPLG, SRTY, TAN, TECS, TWM, URTY, UWM, VOO, VTI) were never scored and stay out |
| Context ETFs | 23 | SPY QQQ IWM DIA, 11 sector SPDRs, SMH KRE XBI XOP XRT ITB IBB SOXX (all inside the lab list) |
| Leg-M candidates (non-fund stocks) | the 996 STOCKS in the download list | eligibility = point-in-time fresh adv20 >= $500M. For reference: 682 had max 2-year adv20 >= $250M and 384 had >= $500M |
| ST7-FD / ST7-base universe | 1,201 | lab names with max 2-year adv20 >= $95M (25 lab names never reached $95M in 2024-26 and are skipped) |
| **Download total** | **1,201** | `symbols_download_all.txt` (includes all of the above) |
| Retained on disk after scoring | 484 | W ∩ lab + context ETFs + stocks with max 2-year adv20 >= $500M (`symbols_retained.txt`); the rest are streamed and deleted |

Disk estimate: ~3 MB per symbol for 23 months of 1-minute bars. That is ~1.5 GB retained. Free space should stay well above
the 1.0 GB guard. Thresholds come from the 2-year daily table with the locked rows dropped.

**Survivorship and other biases (all favour the candidates, especially longs):**
- The lab list is today's 1,226 names. Names delisted, acquired or failed before 2026 are missing (e.g. 2023 bank
  failures).
- Bars are fetched by today's ticker without `asof`, so renamed tickers lose their pre-rename history. A coverage file
  lists symbols with < 50% session coverage.
- The ETB flag is as of today; the borrow fee is a flat estimate.
- The earnings dates (yfinance) cover 941 / 959 symbols in 2023 / 2024.

Signal minus random is reported as the survivorship-neutral read.

## 7. Order of work and guards
1. **Done before this file:**
   - `FREEZE_CORE.json` (+ `frozen/` copies);
   - `universe_fresh.json`, `symbols_download_all.txt`, `symbols_retained.txt`;
   - `FRESH_PLAN.sha256` (written right after this file).
2. **Hunt stage:** freezes H1..H6 → `FREEZE_HUNT.json` + `HUNT_FREEZE.md` (fixes M and the t bar).
3. **Harness:**
   - `fresh_bt.py` with the parity check on 2025-10 (open data);
   - hash checks (`FREEZE_CORE`, `FREEZE_HUNT`, `FRESH_PLAN.sha256`);
   - the assert that no fresh file exists yet.
4. **Download + stream** (one pass, all frozen rules) → signal/walk rows under `/home/user/MCF/data/cache_fresh/` (outside
   git). Temp files are deleted.
5. **Score once** → `round5/fresh_once.json`, `round5/FRESH_RESULTS.md` (every rule, M, cumulative N, all bars).
6. Only the Deploy stage commits, and only if the job's deploy rule is met.

## 8. Configurations
- Before round 5: cumulative N = 996 (up to 1,012).
- Round 5 adds the hunt's configs and M fresh scorings. The fresh t bar uses M because FRESH is a new holdout scored once
  per frozen rule. The cumulative N is still reported.

## 9. Rule-change context
- Every figure here and on FRESH is a backtest on 1-minute bars with one fixed rule set: LR8 costs, the round-4 chassis
  or the benchmark pipeline, today's live parameters.
- No live-account window is quoted, so no `research/ledger.jsonl` change falls inside these figures.
- WB4 went live 2026-11-17 (Testing E), ST7-FD was promoted 2026-10-26 and NM-ETF runs in Primary. All of that is after
  every window used here.
- The 2026-11-19 ledger entries (process bundle, usage1 plan, tweaked copies) are process only.

Educational only — not financial advice.
