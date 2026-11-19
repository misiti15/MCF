# Guild results 2026-11-18 — live reps, setup-day correlation, missed-move gap

_Educational only — not financial advice._

Files copied from branch `mcf-guild` (< 200 kB each). Live = Alpaca paper journals (run kind paper; Shadow run 3 excluded). Locked block never read by these studies.

## REPS3 — did the 11-12 restructure deliver the forecast live reps? (Live, 11-12..11-18, 5 sessions, journals final)
| Reading | Realized setup-days / wk | Forecast (frozen 11-11) |
|---|---|---|
| All setups that signalled | 545 | 482.8 (+13%) |
| Forecast setups, matched by setup id, any account | 521 | 482.8 (+8%) |
| Same, eligibility-adjusted (18 GY-BENCH benched pairs out; guests counted) | 521 | 465.1 (+12%) |
| Non-forecast setups (Workbench copies) | +24 | — |
| Pre-TSZ1 (11-12..11-16) / post (11-17..11-18) | 527 / 573 (forecast setups 513) | — |

- Gen halt skips and buying-power skips: 66 / 60 per session → 0 / 0.
- TSZ1 (11-17) added no setup-days to existing setups; the post-11-17 uplift is the new Workbench copies.
- Market context: SPY daily high-low range averaged 1.46% in the window vs 1.23% in the forecast's 10-20..11-10 baseline. A busier tape lifts signal rates, so part of the uplift is the market, not the restructure.
- Per-account rows are not like-for-like (46 setups moved/split; ROT1 moved 65 Gen setups).
- Rule changes in the window: 56 ledger entries (listed in reps3_1118_out.txt), incl. TSZ1, RULE21-DB, Workbench copies, ROT1, GY-BENCH, promotion hold.

## ICCSET — how correlated are trades within one setup-day? (Live, LR8 basis, all trades)
Median ICC 0.201 (to 11-11) → 0.223 (to 11-16) → 0.219 (to 11-18); TSZ1 does not move it. Shorts 0.27 vs longs 0.17; heat/exhaustion/RW3/RW5 shorts highest (0.44-0.52). A setup-day ≈ 1 / 0.22 effective trades at high counts, so the setup-day stays the evidence unit.

## A1 — where are the big moves Live misses? (descriptive, 0 configs; 11 sessions of the Move Hunt catalogue, non-blackout)
- At T0 = max(decision, 09:50), 77% of each missed move is still ahead (1.17 daily ATR mean, measured to 15:55); 99% of extremes come after T0. Most of that is selection: for a driftless path the extreme falls after 09:50 85% of the time, and these names were picked for their full-day move.
- What survives: ~4.5 non-ETF moves a day with ≥ 1 ATR left where no setup fired or Live traded outside the move. **The gap is foresight (which name, which side), not timing.**
- Shortlist (shortlist/FINAL.md): 1) a setup search on that pool, only once a new SIDE input exists (all known side inputs are closed; SIDEHUNT opened); 2) A-WT guard parked; 3) live-reps ranking input for the spotlight rotation (descriptive).

## FAMC earnings Shadow (journal-only; nothing trades)
3 sessions scored (11-11, 11-12, 11-18), 3 unscorable. Raw net per session +0.372, −0.641, +0.220R. Mean ex-market delta +0.129R; **without its best session (11-11, 66% of the positive delta) −0.112R.** K_edge 0.663 = no evidence either way; ~40-60 scored sessions needed.
