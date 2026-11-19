# SIDEHUNT #2 step 0 — signed volume share 09:30-09:50 vs today's 09:30-09:50 side (outcome-free; 2026-11-18 ~21:45 ET)
Educational only — not financial advice. Lead lead-20261118-2100-2. 0 configs; no price after 09:50 was read.
Data: 5-min SIP bars 09:30-09:49 ET (fetch_open.py, #43 guard), the fixed 512-name list, 450 sessions (2-year history, locked block
absent). Feature built fresh and day-reset (Skeptic: the lab column buyPressure is NOT day-reset; at 09:50 it is mostly yesterday's
afternoon). Script step0.py, output step0_out.txt.

| set | sign agreement with the competitor | Spearman (pooled / median day) | discordant N | per day | n_eff | MDE at BAR90 2.74 |
|---|---|---|---|---|---|---|
| all names | 79.3% | +0.728 / +0.711 | 46,558 | 103.5 | 1,978 | 0.081R |
| in-play proxy (top quintile of 09:30-09:50 range / prior ATR14) | **87.6%** | +0.802 / +0.761 | 5,641 | 12.5 | 1,594 | **0.090R** |

MDE assumptions are STATED, not measured: a per-trade SD of 1.0R and ICC 0.22 (ICCSET 11-18). The in-play proxy is not
precursors.py's vol_exp.

**Reading: #2 is CLOSED as untestable here** (Lead's line: MDE > ~0.05R). In-play, the day-reset flow agrees with the competitor 88% of
the time, so it is mostly a relabel; the discordant cell is the whole test, and its MDE is 0.09R.
**Why a bigger universe would not rescue it:** day clustering caps n_eff near days / ICC, so the MDE floor is about
(2.74 + 0.84) x 1.0 x sqrt(0.22 / 450) = 0.079R however many names are added. Only more sessions (or a lower per-trade SD) lower it.
Method note for the guild: with ICC ~0.2, any 09:50 side test on ~450 days has an MDE floor near 0.08R per trade.
