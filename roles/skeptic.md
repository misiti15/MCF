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
- 11-17 07:50 UTC (run 64): stop charge parity (0.089 vs 0.09-0.10R) closes the thread. FWDCAL tier lines: asked Builder to call mcf.research.effective.tier (min 3 days / 30 entries; bias > 0.01 = optimistic). Flagged to Lead: effective.tier gives 0.2 to < 3 days even at 90% match, and lets bias -0.03 into 0.35 (owner text says +/-0.01).
- 11-17 09:50 UTC (run 65): Builder now calls effective.tier (one source). Lead takes bias-bound to owner PR, 2-day 0.2 as a question. Pre-attacked Observer's blackout look: silent no-blackout fallback, busday/report-time, event-day costs understated (x3 only at |gap|>=20%), same-week control, measured NBBO spread ratio.
- 11-17 11:50 UTC (run 66): BLKOUT pre-score bug: offsets on trade-date sessions skip the block (report 10-30 vs trade 03-03 = k~2) and block-dated reports dropped (late-Oct trades -> 'outside'); plus report-window edges; asked amendment + gap selftest; Builder to hold --run.
- 11-17 13:50 UTC (run 67): BLKOUT Amendment 1 signed off (selftest 4 cases ok; edge logic sound). Minor: half days removed from calendar -> off-by-one next to them.
- 11-17 15:50 UTC (run 68): Observer did BLKOUT 1b (half days in calendar). HKS950 pre-attack: family N 3 too narrow (>= 42 with ex30 cross-sectional, BAR90 2.46), drop 15:30 slot (close auction vs 15:55 flat), snapshot-universe survivorship, RTH check, cost realism; convince = VALID gross above bar + TRAIN + >= 8/11 slots + > null95.
- 11-17 17:50 UTC (run 69): HKS950 NOT re-signed: code at 90e686aa1 still BAR 1.35 / N 3, keeps 15:30 slot, no 8/11 or null95 gate, no per-slot break-even, no RTH assert. Re-sign when amended + selftest posted.
- 11-17 19:50 UTC (run 70): HKS950 Amendment 2 re-signed (selftest 5 cases ok). Tonight: FWDCAL -> BLKOUT -> FAMC; HKS950 (Scout). Audit all against pre-registered tables.
- 11-17 21:50 UTC (run 71): owner adopted RULE21-DB 11-17 (decision bar, gap-1.645SE<=0, replay_cal/score.py rule21): asked FWDCAL to print the official verdict from that source beside the pre-registered exact-minute one. Window context: SPYEXIT (RW3/RW5-WB4), TSZ1 3-share floor, 17 WB copies + ROT1, KILL-FLAT adopted closes.
- 11-17 23:50 UTC (run 72): FWDCAL fresh2 printed only exact-minute; official rule21() (decision bar) missing -> asked. My proxy estimate: 3/10 pass (B, Gen, C), pooled fail 0.932. HKS950 CLOSED; checklist #44 (persistent-selection nulls). BLKOUT ~0 (protective BMO k=0 cell, 1 of 18).
- 11-18 01:50 UTC (run 73): OFFICIAL rule21: 3/10 pass (my per-account estimate exact; my pooled FAIL was wrong: official 0.951 PASS). Pooled pass is Graveyard-carried; arena+On Deck gap +0.036R optimistic. Checklist #45. HKS950 15:30 re-cut: 84% before 15:55 (post hoc, 1 of 12 slots).
- 11-18 03:50 UTC (run 74): PR #223 notes checked (table right). Asked: qualify 'locked block never read' (11-15 disclosure); dashboard JS tier() duplicates effective.py (consistent now; add a node cross-test). Builder automated OFFICIAL + pooled ex-Graveyard / arena lines in every FWDCAL audit.
- 11-18 05:50 UTC (run 75): Lead fixed PR notes (#225). A2 side candidate (yesterday 15:30-15:55 sign): voted 'none yet' (same-slot persistence != next-morning; reversal prior; overnight news); if run, must beat today's 09:30-09:50 side. FAMC guards: add journal-final check.
- 11-18 07:50 UTC (run 76): FAMC journal-final guard in (shared guard_decide). A1: side line must use the full in-play denominator at 09:50, not the hindsight mover set (#20).
- 11-18 09:50 UTC (run 77): A1 fetch clean (guard, RTH-bounded requests, no half days); A1 measure should end at 15:55 (Live flat), not the close.
- 11-18 11:50 UTC (run 78): A1 not signed: extreme times 1-min (217/253 off 5-min grid) -> left_to_extreme silently 0; asked fix + off-grid selftest; minors after950 label, ETF regex 'Trust'. Checklist #46.
- 11-18 13:50 UTC (run 79): A1 Amendment 1 signed off (selftest ok). Asked print of missing-extreme-bar count. Tonight: FAMC NVDA, REPS3+ICCSET, A1, final shortlist.
- Monday: audit each result against the pre-registered list above, in order, as it lands.
