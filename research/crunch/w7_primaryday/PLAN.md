# W7-primaryday — pre-registered plan (written 2026-11-18 ~17:40 ET, before any rule was scored)

Educational only — not financial advice. Research only: no config, runtime or setup change.

## Data
- Primary journal (`mcf-data:journal.db`), live run (run_id 1) only, R = pnl_adj / (|entry - stop| x shares), costs in (LR8 since 11-12).
- Windows: **FIT** 10-23..11-05 (10 sessions), **CHECK** 11-06..11-18 (9 sessions), plus an **EARLY** out-of-window replication 10-06..10-22 (Primary, older lineup; before the twin block for 10-06..10-19, before the -2R latch).
- Market context: Alpaca SIP 5-min SPY bars and daily bars of traded names (GET only). Locked block never read.
- Two books: (a) **as traded** (all lineups); (b) **current five** (L3-gap-slope-fromopen-FD, NM-ETF-late-dip-di-long, RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, ST7-rsi50dn-long-pm-t1s1-FD) = their Primary trades only.

## Descriptive step (no rule chosen from it except where marked)
Per-session decomposition: setup, side vs SPY, entry hour, 5-min entry clusters, same-symbol stacking, open same-side count, prior loss on the symbol, realised peak/giveback, squeeze (SPY moving against a short after entry).

## Rules (all point-in-time, remove entries only, fixed parameters, chosen by mechanism before scoring)
Simulation walks entries in time order; a removed entry never opens, so it does not count toward later caps; the Primary -2R per-setup latch (from 10-29) is re-applied on the simulated realised R so removals can move the latch either way. Freed slots are NOT refilled (skipped signals' outcomes are not used) — stated as a limit.
1. **SYM1** symbol loss limit: after any Primary lot on a symbol closes at a loss, no new Primary entry on that symbol that day (any setup, either side).
2. **STACK1** one open lot per symbol across all Primary setups (blocks a new lot while any Primary lot on that symbol is open). Twin block already covers X/X-FD; this extends to cross-setup.
3. **CLU3** entry-cluster de-dup: at most 3 new Primary entries per 5-min decision bar account-wide (first by signal time).
4. **CLU5** same with 5.
5. **CORR2** correlated-name cap: no new lot if 2 or more same-side Primary lots are open in names whose trailing 40-session daily-return correlation with it is >= 0.60 (computed with closes up to the prior session only).
6. **SECT3** sector cap: no new lot if 3 or more same-side lots are open in the same sector (research/rework/web_families/sector_map.json; unmapped names never blocked; coverage reported).
7. **TOD-FH** first-hour budget: at most 6 new Primary entries before 10:30 ET per session (time-of-day risk budget; not a realised-R brake).
8. **FLAT25** (hypothesis that came from the descriptive step on the full window, so FIT/CHECK are NOT clean for it; its only clean test is EARLY): skip entries when |SPY from today's open| < 0.25% at the entry.

Configurations: 8 rules x 2 books = **16**. Bar: t >= max(1.5, sqrt(2 ln 16)) = **2.35** on the paired per-session difference (rule minus baseline), whole window; plus same sign in FIT and CHECK; plus EARLY not negative.

## Reported for every rule
Total dR, FIT/CHECK dR, EARLY dR, paired t, green-day % (before/after), median day, worst day, days <= -10R, per setup improve/worsen counts with R, avg R w/o best day and best-day share of the rule's per-day effect, trades removed. Rule changes in the window from research/ledger.jsonl are listed.

## Guardrails
Not retested: giveback locks, halts, short caps, equity-curve gating, latch levels, re-entry pause, spike filters, morning-only L3, shared latches, RW3+RW5 open-lot caps, compass gate. L3-gap-slope-fromopen-FD is protected: any rule that costs it R is reported as such and can only be proposed with an L3 exemption scored separately (exemption variants count as extra configs).
