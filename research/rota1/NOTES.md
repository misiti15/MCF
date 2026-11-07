Educational only — not financial advice.

# ROTA1 — rolling Primary vs fixed Primary (owner 2026-11-06), study run 2026-11-07

Research only: no config, account, assignment or ledger change. Backtest numbers (2-year lab lists) and live numbers
(paper journals) are labelled separately (rule 7). The locked block 2024-11-01..2025-02-28 is never loaded.

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
