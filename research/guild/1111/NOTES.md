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

## Evening 11-11 (owner REGSW and live-reps tasks)
**Failures first:**
- **GAP-U re-test** (reporting only; Phase 1 code + Skeptic's fixes, `regsw_rebreak/`): with ONE day permutation shared by all setups, GAP-U-OFF no longer beats its random 95th percentile — VALID +4,538R vs +4,905 (Phase 1 +4,616 vs +3,904), FWD +991 vs +1,102; ETB off the same; IDX3-P and SPYO-P also below. SPY o→c flat on gap days (+0.08% / +0.02%). Phase 1's 'beats random' came from the per-setup null.
- **REGSW-2** (owner item 2; 4 switches, N 103, BAR90 2.74; `regsw2/`): 0 of 4 on an 11-setup winning base (TRAIN gross > 0 and live net > 0). GAP-U under the shared null everywhere; checkpoint / W60 / SPY-from-open switches turn negative vs random (VALID t −2.31 / −2.78 / −3.42) — trades against the market state did better on this short-heavy base (unregistered; Skeptic: check ex-market and on the full base first).
- **COILGAP** (owner item 3; 1 look): coil longs off on SPY gap ≤ −0.25% → ex-market z −0.01, closed (second coil shape after COILAM).
- **DISP1, minute-10 exit, CONFIRM, BOTHDAYS, NEWSMID plan, horizon ladder** — see the board; all closed or descriptive.
**Live reps (owner top priority):** owner memo `obs-reps/MEMO.md`. Setup-day is the unit (ICC ~0.19; ~4.8 effective trades per session). Levers ranked by new setup-days: more setups live is the only one that scales; Gen halt / buying power small and unproven; filters protective. No verdict rule beats the 69% base rate. Promotion luck (`skeptic-20261111/promo_luck*`): ~11% of zero-edge setups flagged in 20 sessions. FWDCAL (mirror-live replay, `fwdcal/`) result pending.
**FAMC** forward session 1 (11-11): 2 events, rule − control +0.611R; no alarm (one session).
