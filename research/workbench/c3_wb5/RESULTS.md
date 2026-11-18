Educational only — not financial advice

# C3-WB5 — the five pre-registered tunes, split check on later sessions (2026-11-18 after the close)

Owner yes on C3-WB5 and C3-WB, 2026-11-18. Each tune is the single pre-registered config of
research/consultant_p3/RESULTS.md #7 (<= 2 changes); nothing was chosen or tuned here. **Configurations tried: 6**
(item 3 has two parents). Promotion hold unchanged; a pass becomes a testing copy only.

**Data.** Live journals (run_id 1) of all ten mcf-data* branches, sessions 10-06..11-18 (11-18 is the only session no
consultant study had seen), R = pnl_adj / initial risk (after costs, LR8 from 11-12). Symbol-days traded by one setup in
two accounts keep the account with more trades. Gates/exits use SIP 1-minute and daily bars fetched GET-only from Alpaca
market data (split-adjusted), measured on the last completed 1-minute bar before the decision (no look-ahead). Locked
block 2024-11-01..2025-02-28 never touched. Code: code/wb5_data.py, code/wb5_eval.py; numbers: results.json.

**Split (C3-WB rule 3).** Per parent: fit = first ceil(D/2) traded sessions, check = the later sessions. Verdict on
check only: the copy meets or exceeds the parent's avg R (within 0.01R or >= 95%) and is not worse on avg R w/o best day
or worst day by more than 0.02R / 10%. The 2-year backtest leg of the C3-WB rule was NOT run tonight (time); the paired
shadow A/B (40+ trades, 5+ sessions) is the final pass for any deployed copy.

**Rule changes inside the window (research/ledger.jsonl):** 10-20 twin block; 10-22/23 testing latch off; 10-28 Primary
sizing; 10-29 -2R latch + BAR90; 11-11 TEAM-6; 11-12 LR8 after-cost R + Testing D/E/F; 11-16 ROT1; 11-17 TSZ1 half-size +
promotion hold; 11-18 GY-BENCH, SRCV1. R is per unit of risk, so the sizing changes do not distort it; LR8 changes net R.

| # | Tune (pre-registered) | Parent check n / avg / w/o best / worst day | Copy check n / avg / w/o best / worst day | Check verdict | Deployed |
|---|---|---|---|---|---|
| 1 | CWT09-gapdn-vwaploss-g10 → gap <= -15% + signal-bar close below the day open | 10 / -0.047 / -0.120 / -1.04R | **1** / +1.022 / – / +1.02R | numeric PASS on ONE trade | **No** — one check trade is no evidence; a gate on a proven parent (+0.228R, w/o best day +0.150) is outside C3-WB rule 1 and on the guardrail list; it already has WB1 (below-open). Flagged for the owner |
| 2 | NS3-failed-vwap-reclaim-short → 09:50-10:30 + SPY and QQQ up on the day | 34 / -0.234 / -0.292 / -4.36R | 7 / -0.215 / -0.697 / -3.22R | FAIL (w/o best day) | No |
| 3a | MF2-open-rsimidhi-flowsell-FD + NM-MF3 gate (QQQ below its open, no gap up) | 125 / -0.565 / -0.587 / -25.01R | 47 / -0.393 / -0.449 / -6.54R | relative PASS, copy still losing | **No** — losing parent with 185 trades: C3-WB rule 1 (no tunes/copies) and EXIT100 moved it to the Graveyard tonight |
| 3b | MF4-h40-open-flowsell-FD + NM-MF3 gate | 152 / -0.392 / -0.433 / -17.09R | 47 / -0.261 / -0.349 / -11.31R | relative PASS, copy still losing | **No** — same as 3a (214 trades, EXIT100) |
| 4 | GEN-261027-08 one exit change: 1R target (W7-TUNE27-08) | 37 / +0.047 / -0.256 / -4.87R | 37 / +0.011 / -0.284 / -3.68R | FAIL (avg R, w/o best day) | No |
| 5 | L3-gap-slope-rsi5hi-FD refire off (first entry per symbol-day) | 81 / +0.031 / -0.248 / -2.98R | 66 / +0.078 / -0.183 / -2.50R | **PASS** | **Yes** — L3-gap-slope-rsi5hi-FD-WB5 in Testing C (livelab), top of its order, from session 2026-11-19 (parent On Deck, WB4 Testing B: twins apart) |

Fit halves (for the record, not the verdict): 1 parent +0.425 (14) / copy +0.525 (3); 2 -0.188 (47) / -0.281 (21);
3a +0.663 (60) / +0.855 (38); 3b +0.068 (62) / +0.308 (21); 4 +0.170 (41) / +0.553 (41); 5 +0.175 (77) / +0.169 (67).
Item 4 shows the in-sample trap C3-WB names: the 1R target tripled fit R and lost on check.

Per-setup effect (Remedies rule): of 6 parents scored, the tune improved check avg R for 5 (1, 2, 3a, 3b, 5 — item 1 on
one trade) and worsened it for 1 (item 4, -0.036R/trade); avg R w/o best day improved for 3 (3a, 3b, 5), worsened for 2
(2: -0.405; 4: -0.028). Only item 5 clears every part of the rule with a usable check sample.

11-18 alone (unseen by every earlier study): 1 parent +0.49R (2) / copy +1.02R (1); 2 -1.07R (10) / -0.27R (2);
3a -4.93R (6) / -4.65R (4); 3b +1.49R (12) / +2.06R (6); 4 -4.87R (14) / -3.68R (14); 5 +1.19R (6) / +0.77R (5).

Caveats: check halves are 3-14 sessions; one day moves any result. Item 4's exit walk is conservative (live exit cost
left in; target only when traded through by max(1c, 0.03%)). Item 1's gap uses the daily open vs prior close.
