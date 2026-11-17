# SPY dip accumulation in leveraged S&P ETFs — PLAN (written 2026-11-17, before any scoring)

*Educational only — not financial advice. Research only: no config, account, setup or live-code change.*

Owner idea 2026-11-17: when the S&P dips, buy a small slice (0.25-0.5% of the account) of a leveraged S&P ETF
(read "SPY-L / SPY-X" as SPXL or UPRO at 3x and SSO at 2x) and hold long term, to stay ahead of the S&P; further dips
after a buy are fine. Separately, an intraday version (buy the dip, sell by the close) if it works.

## Data (fixed before scoring)
- **Daily:** Alpaca SIP 1Day, `adjustment=all` (split + dividend adjusted, i.e. a total-return proxy; ETF prices are
  already net of the expense ratio and financing), SPY / SPXL / UPRO / SSO / BIL, 2016-01-04 .. 2026-11-16 (the earliest
  Alpaca serves; 2026-11-17 is a partial session and is dropped). `scripts/download_daily.py`. **All three leveraged
  ETFs existed for the whole window, so every Part A number is real ETF data; nothing is simulated.** A daily-rebalanced
  3x / 2x SPY simulation (minus 0.91% / 0.89% a year expense and SOFR-like financing from BIL) is built only as a
  tracking check against the real series. Pre-2016 (2008) is not reachable from this session (no data host other than
  Alpaca is allowed) — stated as a gap, not filled with guesses.
- **Minute:** `data/cache_hist/1Min/{SPY,SPXL,UPRO,SSO}.parquet` (SIP 1-minute RTH bars, 2024-09-16 .. 2026-11-04).
- **Locked block 2024-11-01..2025-02-28 is dropped at load (daily and minute) and never read.** Because nothing may
  straddle it, every simulation runs in two separate segments with no position carried across:
  **SEG-A 2016-01-04 .. 2024-10-31** (daily only; ~8.8 years incl. 2018 Q4, 2020 crash, 2022 bear) and
  **SEG-B 2025-03-03 .. 2026-11-16** (daily; minute to 2026-11-04; incl. the April 2025 crash). The first session of
  SEG-B has no previous close inside the window and cannot trigger; weekly rules need one full week first.

## Part A — accumulation (long hold)
**Trigger families** (one buy per session at most; repeat buys on consecutive dip days are allowed):
- Daily data (SEG-A and SEG-B):
  - `gap`: today's open <= previous close x (1 - x). Buy at the open.
  - `dayclose`: today's close <= previous close x (1 - x) (daily proxy for "afternoon drop"; decision and fill at the
    close — slightly optimistic, the minute version checks it). Buy at the close.
  - `wkclose`: today's close <= last week's final close x (1 - x). Buy at the close.
  - `wkhigh`: today's close <= last week's highest high x (1 - x). Buy at the close.
- Minute data (SEG-B only, ~1.7 years; previous close = previous session's 15:59 bar close):
  - `m_gap`: 09:30 bar open <= prev close x (1 - x); buy at the 09:30 bar close.
  - `m_1015` / `m_1030`: SPY close of the bar starting 10:14 / 10:29 <= prev close x (1 - x); buy at that close.
  - `m_pm1530`: SPY close of the bar starting 15:29 <= prev close x (1 - x); buy at that close (the realistic
    "afternoon drop").
- x in {0.5, 0.75, 1.0}%.
**Buy:** fixed dollars c x E0 per trigger, E0 = $100,000, c in {0.25%, 0.5%} ($250 / $500), instrument in
{SPXL, UPRO, SSO}. Costs per side: $0.01/share + 1 bp of notional (the long-hold book's cost model), fractional
shares. Cash earns BIL (T-bills); a buy is skipped (and counted) when cash runs out.
**Exits:** `hold` (to segment end); `tp15` / `tp30` (sell that tranche at the first close >= +15% / +30% over its
entry); `n60` / `n250` (sell after 60 / 250 sessions). Proceeds go back to cash.
**Configurations:** daily 4 families x 3 x x 3 instruments x 5 exits x 2 sizes = 360; minute 4 x 3 x 3 x 5 x 2 = 360.
**N_A = 720.** (Size only changes the account-level view; return on deployed capital is identical — counted anyway.)

**Benchmarks (same dollars):**
1. `sched`: the same number of buys n on a fixed schedule, one every k = floor(sessions / n) sessions, same
   instrument, same fill type (open for `gap` rules, close otherwise); averaged over every start offset 0..k-1, and
   the share of offsets the dip rule beats.
2. `rand`: the same n buys on random distinct sessions in the segment, 1,000 draws (seed 1117); mean and the rule's
   percentile.
3. `spy_same`: SPY instead of the leveraged ETF on the same dip dates, same dollars.
4. `spy_bh`: account level — $100,000 in SPY on the first session, held. (Also: the rule's account vs the `spy_same`
   account, both with idle cash in BIL.)
**Metrics:** XIRR on deployed capital (money-weighted, terminal value marked at the segment's last close after exit
costs), terminal multiple on dollars deployed, account CAGR / max drawdown / longest time underwater (sessions below
the prior equity high), position-level max drawdown of the open ETF value vs its cost basis, average cash share
(cash drag), buys skipped for lack of cash, and leverage decay: ETF return minus L x SPY return over 20 / 60 / 250
sessions (all start dates) and for the rule's own tranches.
**Choice (pre-declared):** within each family, the finalist is the `hold` row with the highest SEG-A excess XIRR over
`rand` (ties -> lower x, then SPXL). Daily finalists are scored on SEG-B once, as is. Exit variants are reported
against `hold` for the finalists. Minute families have only SEG-B: descriptive, compared to their daily twin.
**One-big-period check:** the finalists recomputed with buys in 2020-02-19..2020-12-31 removed (rule and benchmarks
alike), with 2022 removed, and (SEG-B) with April 2025 removed; plus each calendar year's share of the excess dollars
over `rand`.
**Verdict rule:** "stays ahead" only if the finalist beats `sched` mean and `rand` mean on SEG-A **and** SEG-B, beats
`rand` in >= 80% of draws on SEG-A, and the sign survives the one-big-period removals. Beating SPY (`spy_same`,
`spy_bh`) is reported separately with drawdowns — leverage alone can beat SPY in a rising market, which is not a dip
edge.

## Part B — intraday (buy the dip, out by 15:55)
Minute data 2024-09-16 .. 2026-11-04 minus the locked block. TRAIN = to 2025-12-31, VALID = 2026. One trade per
session per config. No decision before 09:50 (owner rule 2026-11-14).
- **Families** (SPY vs previous close, prev close = previous session's 15:59 bar close):
  `gap0950` (09:30 open <= prev close x (1 - x); enter at the close of the bar starting 09:49),
  `d1015` / `d1030` (SPY close <= prev close x (1 - x) at the bar starting 10:14 / 10:29; enter there),
  `pm1430` (same test at the bar starting 14:29; enter there),
  `wk1015` (SPY at the 10:14 bar close <= last week's final close x (1 - x); enter there). x in {0.5, 0.75, 1.0}%.
- **Instruments:** SPXL, UPRO, SSO. **Exits:** `c1555` (no stop, exit the 15:54 bar close), `lowstop` (stop 5 bp
  under the ETF's own low since 09:30, else 15:55), `atrstop` (stop 1 x the ETF's daily ATR(14) under entry, else
  15:55; ATR from the prior 14 sessions within 30 calendar days, none straddling the locked block).
  R unit = the stop distance (`lowstop`, `atrstop`) and 1 x daily ATR for `c1555`. Stops fill at the stop or the
  bar open if it gaps through.
- **Costs (LR8 live model, config/default.yaml):** entry 1 bp; market exit max($0.01, 1 bp); stop exit
  max($0.02, 4 bp) extra; SEC 20.60/$1M of sells from 2026-04-04, TAF $0.000166 / $0.000195 per share sold (2025 /
  2026), CAT $0.00005 per share per side.
- **Configurations:** 5 x 3 x 3 x 3 = **N_B = 135**; bar = max(1.5, sqrt(2 ln 135)) = **3.13** (Testing bar 0.9x =
  2.82).
- **Nulls:** (i) the same days, same instrument and exit, 20 random entry bars 09:50-14:30 (seed 1117) — the
  drop_rebound_1116 style test; (ii) the same entry minute on every session (unconditional).
- **Pass (pre-declared):** avg R after costs > 0 in TRAIN and VALID, w/o best day > 0, beats both nulls, and day t >=
  3.13 (or >= 2.82 for the Testing bar). Overlap with the live IDX2/3/5 (SPY down from **today's open**, 09:45/09:55)
  and LD6/LD8 (SPY dip from the open + breadth turn) trigger days is reported as a day-level Jaccard.

## Outputs
`NOTES.md` (method, failures first), `RESULTS.md` (tables), `results_partA.csv`, `results_partB.csv`,
`equity_segA.png` / `equity_segB.png`. Scripts in `scripts/`.
