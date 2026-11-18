# Guild results 2026-11-16 .. 2026-11-17

_Educational only — not financial advice._

Research files copied from branch `mcf-guild` (files < 200 kB; no data parquet, no caches). Each study was pre-registered (PLAN.md + reading table), pre-attacked by Skeptic, scored ONCE, and audited. Locked block 2024-11-01..2025-02-28 never read by these studies (see the 11-15 disclosure in PR #201: an old Observer index cache had read the block's SPY/QQQ/IWM path; purged, guards added). Source names per docs/GLOSSARY.md.

| Study | Source | Result | Bar | Verdict | Smallest effect it could see |
|---|---|---|---|---|---|
| MOMSIDE — skip trades against 12-1 / 6-1 momentum | 2-year backtest | VALID t 0.96; all of it one up-market cell; FWD 10-08..11-13 reverses (−723R, t −3.06) | BAR90 2.91 (family 187) | CLOSED | 0.025R / skipped trade |
| SIZESTOP — wider stops on big-gap days | 2-year backtest | conditioning C1 t 0.12, C2 t 0.65; not above widening on random name-days | — | CLOSED (known STOPW widening) | 0.002 / 0.004R / changed trade |
| Stop widening, gross vs net | 2-year backtest | net +0.0067R, gross +0.0015R (t 0.98); rest = avoided stop-exit charges (~0.089R/stop backtest vs ~0.09-0.10R Live) | — | descriptive | — |
| DIPTURN — owner's dip-then-turn morning (09:50 anchor) | 2-year backtest | long setups +0.009R t 0.92; short mirror −0.012R | BAR90 3.57 (family 2,611) | CLOSED | 0.045 / 0.069R / trade |
| HKS950 — same half-hour continuation | 2-year backtest (30-min bars) | L20 +1.82 bps t 2.18; net −10 bps; L40 sign fails | BAR90 2.46 (family 44) | CLOSED | ~2.7 bps / half-hour |
| HKS950 15:30 re-cut | 2-year backtest | 15:30-15:55 +9.91 bps t 4.45 (84% before 15:55); post hoc, TRAIN weak | — | descriptive → backlog lead (Shadow only) | — |
| BLKOUT — earnings blackout, trades inside vs outside | 2-year backtest | VALID gross −0.0034R t −0.46; negative in TRAIN/VALID/FWD; report-day BMO −0.064R (t −3.57) | — | CLOSED — owner policy stands | 0.021R / trade |
| FWDCAL fresh 11-16..11-17 — Session replay vs Live | Session replay vs Live | OFFICIAL rule 21 (score.py rule21()): FAIL, 3 / 10 pass (Testing B, Testing C, Gen); pooled pass carried by Graveyard | owner rule 21 | FAIL | — |

Configs this batch: MOMSIDE 4, SIZESTOP 2, DIPTURN 2, HKS950 2 (+ descriptive). Guild tally since 11-09: 77 tested, 174 configs / looks, 0 passes.

Rule changes inside the window (research/ledger.jsonl): RULE21-DB (11-17), TSZ1 testing sizing (11-17), shadow mode, Workbench copies (11-17), ROT1 spotlight (11-16), SPYEXIT on RW3-WB4 / RW5-WB4 (11-17), promotion hold (11-17).

Checklist (SKEPTIC_CHECKLIST.md) added #44 (selection tests: read the day-clustered t, a within-day shuffle null is too narrow) and #45.
