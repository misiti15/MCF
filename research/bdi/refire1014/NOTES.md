# refire1014: same-setup refire on the two-year history

*Educational only - not financial advice. Lab results on the open two-year history only; nothing here is a paper or
live result. Paper, backtest and live results are labelled separately (rule 7).*

Owner (2026-10-14): "If each setup has multiple opportunities in a day, unless it's specifically designed to only fire
during certain windows, let them go in as much as possible."

**Section 1 (pre-declaration) was written on 2026-10-14 before any configuration of this study was scored.**
Results go in section 2 and may not change section 1.

## 1. Pre-declaration

### 1.1 What is measured
`LabStrategy` (mcf/strategies/setups.py) fires a lab setup on the FIRST qualifying 5-minute decision bar of a
symbol-day. The new opt-in mode `refire` emits a signal on every qualifying decision bar inside the setup's window,
except that a signal blocks the next `refire_cooldown` decision bars of that setup on that symbol
(`refire_select`, shared by the live code and this scan). Live, same-setup re-entry on a new signal bar is already on
(`live.same_setup_reentry: true`, lot cap 3 per symbol), so refire is what would add trades.

Variants per setup (4 configurations per setup, all counted):
- `first`: first qualifying bar per symbol-day (current behaviour).
- `cd1`, `cd3`, `cd6`: refire with cooldown 1 / 3 / 6 decision bars (next signal no earlier than 10 / 20 / 35
  minutes after the previous one on a continuous qualifying run).

For each refire variant the trades split into the first signal of the symbol-day (identical to `first`) and the
**extras** (2nd+ signals). Reported per setup: n, trades/day, exp R after costs, day-clustered t for `first`, for each
variant in total, and for its extras alone; extras exp minus first exp.

### 1.2 Setups
Every enabled `type: lab` setup of the three accounts, configs as merged by `mcf.config` (config/default.yaml for
Primary; plus config/account_testing.yaml for Testing; plus config/account_testing2.yaml for Testing 2), each with its
module, YAML window and min_adv. A setup that runs in two accounts with the same module/window/min_adv is scored once.

### 1.3 Data, fills, costs
- Two-year lab frames `research/history2y/data/frames` via `research/history2y/lib.py`, open months only. The rule-19
  locked block (2024-11-01..2025-02-28) is never loaded; `MCF_HIST_ALLOW_LOCKED` is never set.
- Population: point-in-time adv20 >= the setup's min_adv, daily ATR > 0, decision bars (bar close) inside the setup
  window and inside 09:50-15:00 (as `LabStrategy.generate`).
- Fixed geometries (t1s1 / t05s1 / t1s05): the frames' per-bar lab outcome (entry at the decision-bar close,
  R = 0.25 x daily ATR, target/stop, flat 15:55) converted to production R with `gates.prod_r` and time-of-day entry
  costs (`gates.tod_cost_mult`) - the lab engine of stack1009 / RESCORE / swarm1013 B0.
- Testing 2 CWT modules and the Testing 1 LIQ modules are run on the frame plus the 09:35-09:45 rows from
  `research/bdi/cwt/test_b/data/headtail.parquet` (as research/bdi/cwt/live/verify.py), so their opening-range
  logic sees the open. LIQ rows also get the derived fromOpen / prior-day distances / ATR on those rows.
- Structural exits (GEOM "S": CWT09 x3, LIQ x2): simulated here on the 5-minute path (frame rows to 15:00, then the
  15:05-15:55 rows of headtail.parquet): stop first inside a bar, a bar whose open (proxy: prior close) is through the
  stop fills at that open, optional target as a limit, else flat at the 15:55 close. R = structural risk
  |entry - stop|. Costs: entry 1c + 1 bps x tod multiplier; target free; stop 1c + 1 bps + 2c; timed 1c + 1 bps.
  LIQ-pdl's live management (be_at_r / time stop) is NOT modelled (stated).
- RW6G1 (Primary and -FD): its VWAP +2 SD guard needs volume, which the frames do not carry. The guard is computed
  with the module's own `vwap_band_block` on 5-minute bars rebuilt from the SIP 1-minute cache (`data/cache_hist`)
  for the symbol-days where its base qualifies, locked block dropped on read (as swarm1013/backtest/bars.py).
- Portfolio limits (max positions, lot cap 3, same-side rule, daily loss stop) are NOT applied: these are setup-level
  lab numbers. Extras that overlap an open lot of the same setup would count toward the lot cap live.
- Survivorship caveat (rule 19): today's universe applied to the past.

### 1.4 Verdict per setup (fixed before scoring)
- **design-off** (refire stays off whatever the numbers; numbers still reported): setups built around one event or an
  opening window: MF1-MF4 Primary versions (MarcoFlow "open" / "945-1030" stacks, windows ending 10:30-11:00),
  CWT09 x4 (one gap-day bounce/VWAP-loss trade, stop at the 09:30-10:30 high), LIQ x2 (one sweep-and-reclaim of the
  opening range / prior-day low), CWT12 coil x2 (coil under the opening high, 09:50-11:30). No ORB, open-gap or
  fixed-time 15:30 setup is a `type: lab` setup (those are classic strategies, untouched by `refire`).
- For every other setup, per cooldown c in {1, 3, 6}:
  - **benefit** at c: extras n >= 30, extras exp R > 0 after costs, and extras exp R >= first exp R
    ("not worse than the first ones").
  - Recommended flag: refire on with the SMALLEST c that is a benefit (the owner wants as many entries as the data
    allow); otherwise off.
  - **neutral**: no c is a benefit, but some c has extras exp > 0 (positive but below the first signals, or n < 30).
  - **worse**: extras exp <= 0 at every c (with n >= 30 at some c), or no extras at all = no change.
- These are lab point estimates. Many setups have first-signal expectancy near zero (most Testing setups did not pass
  the gates); "not worse than the first ones" is not an edge claim. Total configurations: 4 per unique setup
  (reported in section 2). No holdout is scored.

## 2. Results

(filled in after the scan)
