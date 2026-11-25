Educational only — not financial advice

# Project Pyramid — Team S: the two best shorts (2026-11-24)

Research only. Pre-registration hashed before scoring (scratchpad/pyramid/S/PREREG.txt, sha256 5b8914c1…214d): 9 configs + 4 diagnostics = 13 scorings. Lab: bench10 conventions (T1_fit 2024-10 + 2025-03..09, 170 sessions; T1_check 2025-10..2026-11-04, 276; T2 2023-01..2024-09, 427), testing-arena rules, LR8 + borrow, 1-min exits; ETB-only (≥ 90% of 33 snapshots). Live: 10 journals 10-06..11-24, deduped, LR8. Locked block never read. Did not repeat ULT-01/04/08/09 or GAPDEF A/B/C. Nothing reaches TIER A.

## Picks
| Blade | Setup | Tier | Live (ETB) | Lab | Notes |
|---|---|---|---|---|---|
| G (gap-down) | L3-gap-slope-fromopen-FD, latch −2 kept | B | 346 tr / 25 sess, +0.255R, w/o best day +0.216R (34%), win 67.9% vs BE 51.4%, t 3.1; +8.7R on the book's 10 worst days | check −0.077 (fails the −0.046 standard); 2023-24 −0.012; beats random by ~+0.29R | Best live short by far; already in Primary — keep as is. Latch −2 vs none is a coin-flip (live +3R; lab mixed). Non-ETB L3 trades made −11.5R live (mild hindsight). |
| N (non-gap) | GEN-261029-06 Late Quiet-Day Short (QQQ down, 14:00–15:00) | B (`1 day`) | 285 tr / 12 sess, +0.107R, w/o best day +0.039R (11-20 = 69%), t 1.34; corr with Primary book .16, with L3 .05 | meets the standard in fit (−0.042), check (−0.008) and 2023-24 (−0.019, out-of-sample); beats random by +0.12–0.14R | Only candidate meeting the lab standard in both halves; failure mode = late SPY rally (−0.68 on SPY-up check days). Forward-test to > 20 sessions. |
| Runner-up | GEN-261023-06 Late-AM Pop Fade (SPY down) | B / watch | 26 tr / 6 sess, +1.03R, w/o best day +0.478R; corr with gap-down family −0.12; +17R on the family's 8 worst days | 2023-24 −0.404 (40 tr, only clean OOS) — fails; 0.44–0.75 tr/session | Best diversifier, but in-sample only and low volume. |
| Failed | G4: first-minute-VWAP gap with L3's own threshold | FAIL | removed 33 trades averaging +0.373R → −12.3R | — | Closes the last GAPDEF salvage for L3. |
| Failed | ST5-pdbrkup-short-mid-t05s1-FD | FAIL | 29 tr, +0.207R | check −0.073 vs random +0.005 | — |

The two blades are diversified from each other: daily-R correlation +0.05 live, +0.08 lab.

## Next steps (backlog, not run)
- GEN-261029-06: pre-registered "SPY not rallying since 14:00" guard for its up-day failure mode.
- GEN-261023-06: keep forward-testing to ≥ 20 sessions.

Rule changes in the live window: 10-20/10-23/10-29 latch rules; 10-28 Primary sizing; 10-30 testing cost filter, L3-fromopen re-promoted; 11-12 LR8, Testing D/E/F; 11-16 ROT1 (GEN-261029-06 to Testing D — its volume jumped then); 11-17 TSZ1; 11-20 ult1119 admissions; pending 11-27 PRIM-ADD2.
