# skeptic notes (current; runs 1-56 archived in roles/skeptic_log.md)

Educational only — not financial advice.

## State (2026-11-15, quiet Sunday)
- Checklist: research/SKEPTIC_CHECKLIST.md, 43 items (A look-ahead, B controls, C units/market, D data, E counting; 31-43 later).
  Lead's PROTOCOL: run it before posting a frozen plan.
- Guild standards I pushed that are now adopted: excess over matched controls, family try-counts, gross first, ex-market,
  shared-day permutation null, R next to ATR, pooled ratio estimator for binned units (#39), MDE printed beside every
  'closed' (#41), journal timing guard >= 16:30 (#40), early-close drop (#42), locked block guarded at request AND read (#43,
  research/guild_read.py).
- Owner decisions pending: RULE21-DB (decision-bar matching), PROMO2 (two-stage promotion), D3 replay records, COMPCAL card.
- Queue, Monday 11-16 after 16:30 ET: MOMSIDE -> SIZESTOP -> DIPTURN; FWDCAL fresh 11-16..11-17 after 11-17's close. 11-18: REPS3 + ICCSET (Scout).

## Pre-registered result audits (written 2026-11-15 before any of these is scored; I check exactly these)
FWDCAL fresh (rule 21): journal guard output printed (every account's last commit from the session, >= 10 min old, counts);
  exact-minute match >= 95% AND |avg R gap| <= 0.03 on the LR8 basis (both sides from 11-12); split live-quote vs pool-priced;
  CI on the gap; per-account rows; any account with match < 90% named. Optimistic gap (replay > live) is the failure that matters.
MOMSIDE: C1 gates exactly as PLAN (VALID ex-market t >= 2.91, TRAIN sign, >= 60% setups, best day < 50%, gross > 0); C3 beside C1
  (a C1 pass with C3 <= 0 = 'short-leg-driven, survivorship-suspect'); top-5 share; control's own avg R (#10); skip share by side;
  half-day drop count printed; MDE80 + at-bar; FWD reported, never a gate. If PASS: re-run the per-setup table myself from the
  posted CSV and check the excess is not one SPY-direction cell (up/down/quiet split).
SIZESTOP: conditioning effect t vs 2.66 AND > 0 in TRAIN and VALID; size-cut CTRL applied (stop effect = VAR - CTRL); name-day null
  95th pct; down-session sum >= 0; >= 60% families; w/o best day; give-up-then-recover vs random; stop-out shares; MDE.
  Red flag: stop effect positive but conditioning effect ~0 = unconditional widening (known), not the gap condition.
DIPTURN: tod >= 955 drop count; VALID t vs 3.57 and > null95; TRAIN sign; >= 60% setups; w/o best day; ATR per geometry beside R;
  SPY 09:50->close on condition days (if the 'edge' equals beta x that move, it is index, not selection); MDE at bar ~0.08R.
All four: count every config shown; check 'nothing above X; smaller unknown' wording on a close; rule-change context
  (ledger effective dates) for anything touching live trades.

## Learned (standing)
- On a losing book any 'trade less' rule scores; only excess over a same-share random control counts.
- Most 'edges' here were market direction or look-ahead; reproduce from my own fetch before believing.
- Day is the unit (ICC ~0.19, ~5 trade-equivalents per session); index tests have ~1 obs/day and exclude only large effects.
- Reused files carry their parent's filters (#38); journals hold only exited trades (#40); caches can hold extended hours (#42).

## Failed (mine, owned)
- Run 30 two-stage 'keeps most real edges' -> ~16%; run 33 exit model as FWDREP cause (wrong); run 41 entry drift as FWDCAL gap
  (was LR8); run 47 day-mean of bin means (false t 4.4, caught pre-post); run 50 an unverified number in a draft (removed).
  Rule: every number in a post comes from an out file.

## Next
- 11-15 19:50 UTC (run 58): verified the pre-registered items are printed in all four scorers at fa05e86f9; selftests clean here.
- 11-15 21:50 UTC (run 59): mirror.journal_guard passes silently if run 11-16 on the 11-16..11-17 window (future last day appended by trading_days; 11-17 then skipped). Asked for future-date refusal, per-day freshness, refuse-on-skip. Check the fix before 11-17.
- 11-15 23:50 UTC (run 60): reran --guard-selftest (7/7 + gap/skip asserts), read the wiring; SIGNED OFF for Tuesday. Hardening asked: past windows should require last commit >= 15:55 ET on the last window day.
- 11-16 01:50 UTC (run 61): past-window hardening verified (11/11 selftest). Scout fixed refresh.py the same way.
- 11-17 03:50 UTC (run 62): audited MOMSIDE / SIZESTOP / DIPTURN (all CLOSED, verdicts stand). Flags: MOMSIDE-LIVE window == lab FWD calendar (not independent); SIZESTOP net > gross = cost-per-R from fewer shares, asked for gross stop effect (also STOPW). Next: FWDCAL fresh after 11-17 16:30 ET.
- 11-17 05:50 UTC (run 63): Builder's gross split: widening = avoided stop-exit charges (gross t 0.98). Asked for the backtest's mean stop charge per stop in R vs live ~0.05R to size the live effect. Lead parked MOMSIDE-LIVE on my point. Next: FWDCAL fresh tonight.
- Monday: audit each result against the pre-registered list above, in order, as it lands.
