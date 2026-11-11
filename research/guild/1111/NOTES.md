# Research Guild — 2026-11-10 night / 11-11 early (research files from branch `mcf-guild`)

*Educational only — not financial advice.* Research only: nothing in config/, mcf/, docs/live or the trading path changed.
Owner summary of days 1-3: **`obs-synthesis/DAY1-3.md`** (Observer). Locked block never read.

## Failures first (since the 11-10 evening PR)
- **NEWSDIR** headline polarity (1 look, family N 145): +0.032 ATR, day-t 1.18 vs gap baseline +0.028 → closed (direction already in the gap).
- **UNGAP** unexplained gaps (1 look, gap family N ~6,285): drift with the gap +0.039 ATR (t 1.49) — opposite of the pre-registered fade → closed.
- **Cost-killed setups** (descriptive; 17 setups, 1,719 live trades): live paper cost 0.065R vs lab 0.192R; only 2 of 17 positive w/o best day, both post-10-30 shorts; RW7 then −28.7R on 11-10.
- **LIMEX** limit entry at the signal close (3 configs, family N 1,960): adversely selected — missed signals earn up to +0.217R, filled −0.062..−0.077R; net −185 / −803 / −1,115R (t −0.50 / −2.83 / −4.77) → closed.
- **WHATWORKS** (descriptive; 18,878 live trades, 194 setups): one setup×account clears positive after live costs + w/o best day + best day < 50% — RW1-gapdn-bounce-flowsell-short-FD (Testing 2, 75 trades, +0.211R); 11 near-misses all shorts carried by 11-04/05. 2-year lab join: every survivor negative on 2 years (−0.027..−0.087R) and a market-direction bet (SPY down days +0.08..+0.27R, up days −0.09..−0.32R).

## Open
- **CONFIRM** (stop entry at the trigger price; plan frozen, unscored; Skeptic amendments pending).
- **FAMC** journal-only forward shadow from 11-11; nightly calendar builder `obs-amcnews/build_famc_cal.py` (hybrid: precision 0.887, recall 0.756; pre-open + source asserts).

Rule-change context: the live window 10-06..11-10 holds many ledger changes (Owner CF cost filter Testing 1/2 from 10-30, UNI1 top-500 11-04, Graveyard moves 11-02/03, ROLL1 11-05, EXPO1109 11-09/10); live survivors' gains sit after 10-30 and overlap the 11-04/05 sell-off.
