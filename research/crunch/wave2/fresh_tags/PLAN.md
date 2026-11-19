Educational only — not financial advice

# Wave 2 "fresh_tags" (WAVE1 §7 items 3, 4, 6) — pre-registered plan

Written 2026-11-19 after the close, **before any scoring**. Research and proposals only: no config, runtime, ledger,
assignments or setup change; no final decision without the owner. Locked block 2024-11-01..2025-02-28 never read
(`research/history2y/lib.py` refuses it; no `MCF_HIST_ALLOW_LOCKED`). 2023-24 bars (`cache_fresh`) not used.

**Configurations counted: 3** (item 4 only; items 3 and 6 add none). Bar for item 4: max(1.5, √(2 ln 3)) = **1.50**
(day-clustered t). Item 4 is a separate source with **SRCV1 weight 0**: it can only inform, never pass a rule.

## Item 3 — fresh-session check of the frozen TAGS1 rules (0 new configs; report, don't decide)
- Rules exactly as frozen in `research/tags1/rules.json` (2026-11-18): FLAT25, STACK1_L3X, MFGAP (the four W4 watch
  tags are tabulated too, no comment). Tagger: `research/tags1/tags1.py` `build()` unchanged.
- Data: every account journal at the 11-19 close (`origin/mcf-data*`), session 2026-11-19 (first fresh session;
  11-20 has not happened yet). Live = run kind `paper` only (run 1); shadow = run kind `shadow`; **what-if rows (run kind
  `whatif`) are excluded** — `tags1.decisions()` labels every non-shadow run "live", which would pull what-if rows into
  the score; checked and reported as a housekeeping finding, not changed here.
- Bars: 11-19 1-minute + daily bars of the traded names + SPY from Alpaca SIP (GET only, keys from the environment,
  never printed), deleted after use.
- R = booked pnl_adj / (|entry − stop| × shares) (LR8 is the booked basis from 11-12). Account R = LR8 $ ÷ (0.25% ×
  equity), equities as in wave2/packet.
- Reported per rule: would-skip count, their R and account R, per setup (better / worse if skipped), Primary vs all
  accounts (de-duplicated setup|symbol|date|entry minute for "all" scope), live and shadow separately.
  **No verdict, no t, no random-removal percentile** — `score.py` stays sealed until 20 sessions (on/after 12-17).

## Item 4 — 2-year single-config scores (3 configs, weight 0)
Source: the 2-year lab frames (`research/history2y`, 5-minute features + lab exit outcomes, context `spy_fo`), open
months only, **sessions 2024-10-01..2026-10-05** (everything before the live record the three rules were found on,
10-06..11-18; the locked block is not in the frames). Deviation from WAVE1 §7 ("2-year live-code replay"): the replay
(`research/replay2y`) ran only 7 sessions and kept no trade files, so it cannot score a rule; the lab is used instead.
Trades: the live module mask & live config window/min_adv (& L3 prefilter), first qualifying bar per symbol-day
(`gates.lab_trades`), module GEOM, **production cost R** (`gates.prod_r` with time-of-day entry costs — the lab's cost
model; LR8 needs live fills and is not available for lab trades). No ETB/shortable or refire/stacking modelled.
1. **FLAT25 on the current Primary five** (L3-gap-slope-fromopen-FD, NM-ETF-late-dip-di-long,
   RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, ST7-rsi50dn-long-pm-t1s1-FD): skip
   a trade when |spy_fo at its entry bar| < 0.25 (%).
2. **MFGAP on the MF family** (MF1-945-flowsell-vwapup-FD, MF2-open-rsimidhi-flowsell-FD, MF3-open-flowsell-rsi5hi-FD,
   MF4-h40-open-flowsell-FD, MF5-flowsell-vwapup-rsi5hi-FD; all short): skip when the stock's gap ≥ +2.0%.
3. **W7 SPY-up-day profile of RW3/RW5** (the two -FD setups): trade R on SPY-up sessions (SPY close > open, daily bar)
   vs SPY-down sessions. Hindsight day label — a profile, not a rule. "Replicates" = up-day avg R below down-day avg R
   with day-clustered t ≥ 1.50 on the per-session difference measure (Welch t on per-session avg R, up vs down).

For 1 and 2: skip gain = −ΣR of skipped trades; random-removal percentile (same count, same setups' pool, 2,000
draws, seed 1119); day-clustered t of the per-session skip gain over all sessions with a trade of the scope; gain
w/o best day and best-day share; per-setup better / worse (count and R); halves (2024-10..2025-09 vs 2025-10..2026-10-05)
sign check. "Supports" = t ≥ 1.50 AND random percentile ≥ 95 AND same sign in both halves AND best-day share < 50%.

## Item 6 — correlation recheck (0 new configs)
Pairs: L3-gap-slope-fromopen-FD vs RW3-gapdn-rsi5pop-flowsell-short-FD; L3-gap-slope-rsi5hi-FD vs NS1-rsidip-rsi5pop-long
(and its -FD copy pooled under NS1). Series: per-session sum of trade R (LR8, `cost_r_lr8`) and of account R; live run 1,
2026-10-06..2026-11-19. Views: **Primary-only** and **pooled** (all accounts, exact setup names + plain copies, WB copies
excluded, identical signals setup|symbol|date|minute counted once). Two day sets each: (a) days both traded,
(b) union of traded days with 0 on a no-trade day. Pearson and Spearman, n days. Also the pooled correlation split into
same-account vs cross-account pairs to show what drives the pooled figure.

Rule changes inside the windows (ledger) are listed in RESULTS.md.
