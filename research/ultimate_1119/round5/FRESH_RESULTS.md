Educational only — not financial advice

# Round 5: FRESH results. Every frozen rule was scored once, and none BEATS.

Scored 2026-11-19T11:12:10Z by the scorer stage (FRESH_PLAN sec. 7.5) with `fresh_bt.py score`. The single score is in
`round5/fresh_once.json`, and every trade is in `round5/fresh_trades.csv.gz`. This file replaces the earlier
"NOT SCORED" status.

## Window and guards
- **Window:** FRESH 2023-01-03..2024-09-13, 427 sessions. "/session" divides by all 427. The descriptive halves are
  FRESH-1 = 2023 (250 sessions) and FRESH-2 = 2024-01-02..2024-09-13 (177 sessions). The 2022-10-03..2022-12-30 warm-up
  was used for features only.
- **Costs are in:** LR8 costs, with the ×3 extended tier on R4/R5 and the borrow estimate on the H-V1 shorts.
- **Guards were re-verified right before scoring, and all passed:**
  - the FRESH_PLAN.md sha256 equals FRESH_PLAN.sha256 (6bc5fb4213079da3…);
  - FREEZE_CORE matches 31/31 and FREEZE_HUNT matches 16/16;
  - M = 8, the t bar is 2.039, and H3..H6 are empty;
  - FREEZE_HUNT (10:28:39Z) is earlier than every one of the 1,876 fresh files;
  - MCF_HIST_ALLOW_LOCKED is unset, and 2.80 GB of disk was free;
  - the parity PASS (10:37:18Z) still holds with the same pinned harness. The `fresh_bt.py` sha 189b138665c6e390… equals
    the stream's recorded harness sha.
- **Run once:** `fresh_once.json` did not exist before this run. The score code path had been exercised beforehand only
  on the 2025-10 parity rows (`score-dry`), not on fresh data.
- **Untouched:** no rule, threshold or harness file was edited. The locked block 2024-11-01..2025-02-28 was not read.

## Every rule on FRESH (costs in)
The pass bar (sec. 5) needs all five of: avg R > +0.0836, w/o best day > +0.0734, R/session > 0, day-clustered
t >= 2.039, and positive on the check half.

| Rule | Trades | /session | avg R | w/o best day | best-day share | R/session | worst day (/trade-session) | t | 2023 avg R | 2024 avg R | SPY up / flat / down avg R (n) | signal − random | BEATS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 BOOK-EM (32e) | 270 | 0.63 | −0.040 | −0.067 | n/a (total < 0) | −0.025 | −8.20 (−3.98) | −0.73 | −0.033 | −0.048 | −0.072 (81) / +0.000 (103) / −0.059 (86) | +0.021 | no |
| R2 leg E | 249 | 0.58 | −0.040 | −0.069 | n/a | −0.023 | −8.20 (−3.95) | −0.69 | −0.024 | −0.057 | −0.098 (76) / +0.030 (90) / −0.063 (83) | +0.027 | no |
| R3 leg M | 21 | 0.05 | −0.043 | −0.118 | n/a | −0.002 | −1.08 (−0.93) | −0.27 | −0.144 | +0.049 (flip) | +0.322 (5) / −0.204 (13) / +0.047 (3) | −0.044 | no |
| R4 ST7-FD (bench) | 481 | 1.13 | −0.016 | −0.039 | n/a | −0.018 | −13.96 (−6.94) | −0.25 | +0.008 | −0.046 (flip) | +0.309 (122) / −0.014 (191) / −0.253 (168) | +0.230 | no |
| R5 NM-ETF-late-dip (bench) | 256 | 0.60 | −0.044 | −0.063 | n/a | −0.026 | −8.21 (−3.82) | −0.69 | −0.038 | −0.052 | −0.166 (75) / −0.001 (74) / +0.012 (107) | +0.087 | no |
| R6 ST7-base (chassis) | 256 | 0.60 | −0.001 | −0.015 | n/a | −0.000 | −4.65 (−2.94) | −0.01 | +0.004 | −0.006 (flip) | +0.121 (88) / +0.050 (107) / −0.265 (61) | +0.164 | no |
| H-V1 leg X (short) | 88 | 0.21 | −0.141 | −0.193 | n/a | −0.029 | −3.33 (−2.24) | −1.38 | −0.194 | −0.107 | −0.245 (21) / −0.097 (26) / −0.115 (41) | −0.108 | no |
| H-V2 leg K (long) | 192 | 0.45 | +0.042 | +0.012 | **72% (1 day**, 2024-08-23) | +0.019 | −5.29 (−2.26) | +0.43 | +0.056 | +0.030 | +0.066 (62) / +0.251 (68) / −0.212 (62) | +0.159 | no |

Bar checks:
- No rule passes avg R, w/o best day or t.
- Only H-V2 has R/session > 0.
- All 8 were positive on the check half, so condition 5 holds for all of them.

Other figures:
- **Median hold (min):** R1 40.5, R2 37, R3 45, R4 75, R5 27, R6 45, H-V1 34, H-V2 25.5.
- **Win rate:** 46-58%.
- **Day cap:** it never bound. R1 had 270 trades both capped and uncapped, and H-V1 / H-V2 had the same counts either
  way. So R2 and R3 are exactly the legs run alone.
- **Earnings blackout:** R1 without the blackout had 280 trades, avg R −0.032 and w/o best day −0.057.
- **Random control:** the random draws were paired for every trade, except 5 missing for R4 and 1 for R6.

## Read
- **Nothing beats our current best setups on fresh data.** By the pre-registered bar, round 5 is a FAIL for all 8 rules.
  No re-tuning on FRESH is allowed, and any later variant needs a new untouched window.
- **The benchmark itself did not hold up in 2023-24.**
  - ST7-FD: avg R −0.016 and R/session −0.018, against +0.084 and +0.262 on the check half.
  - NM-ETF: −0.044.
  - So the window was hostile to these long mean-reversion setups as a group. Its losses are concentrated on SPY-down
    days: ST7-FD −0.253, R6 −0.265 and H-V2 −0.212.
  - No candidate beats ST7-FD's own FRESH avg R by a margin that matters. R6 (−0.001) and H-V2 (+0.042) are nominally
    above it, but both have t < 0.5.
- **Signal minus random is positive for 6 of 8 rules.** The largest are R4 +0.23, R6 +0.16 and H-V2 +0.16. The entry
  timing is better than a random bar in the same symbol-session, but not enough to clear costs. The exceptions are
  H-V1 (−0.108) and R3 (−0.044, n = 21).
- **The legs from rounds 1-4 did not carry over.**
  - Leg E (WB4 ETF dip), the strongest check-half leg, was −0.040 in both years.
  - Leg M had only 21 trades in 427 sessions, because few names met adv20 >= $500M point in time. The fresh median was
    121 names a day at >= $500M and 624 at >= $95M. Leg M flipped sign between the years.
- **H-V1** (the short mirror) was the worst rule at −0.141, below its random control.
- **H-V2 is the only rule positive in both years, but it is weak and lumpy.**
  - Without 2024-08-23 its avg R is +0.012, and that day is 72% of total R (the `1 day` tag).
  - t is 0.43.
  - Its check record was also carried by 1-2 days (54%). This does not support a promotion. At most it is a note for a
    future idea with its own new window.
- **Volume was lower in 2023-24.** Trades per session were well below the check half: R4 1.13 vs 3.13, and R6 0.60 vs
  2.23. Fewer names cleared the ADV and ATR gates in that window. That is consistent with the data, but the size of the
  gap is worth a look by the skeptic.

## Survivorship and other biases (all favour the candidates)
- The universe is today's list of 1,201 names. Names delisted, acquired or failed in 2023-24 are missing, for example
  the 2023 bank failures (SIVB, FRC, SBNY), which were long-dip traps.
- 54 symbols listed after the window returned empty, and 25 cover less than 50% of the fresh sessions.
- Tickers are fetched without `asof`, so renamed names lose their pre-rename history.
- The ETB flag is as of today, and the borrow fee is a flat estimate (it flatters H-V1).
- Earnings dates come from yfinance and are incomplete before 2024. That makes the blackout weaker in 2023 and is a mild
  risk for R1/R3.
- Every one of these biases pushes the long rules' FRESH numbers **up**, so the true figures are likely at or below
  those shown. Signal minus random is the read that is neutral to survivorship. It is positive but small next to costs.

## Configurations
- Round 5 adds 8 fresh scorings (M = 8, each scored once) to the hunt's 40 configs.
- Cumulative N is **1,044 (up to 1,060)**: 996 (up to 1,012) before round 5, plus 40 from the hunt, plus 8 fresh
  scorings.

## Rule-change context
- All figures are 1-minute backtests on one fixed rule set: LR8 costs, the round-4 chassis or the benchmark pipeline,
  and today's live parameters.
- No live-account window is quoted, so no `research/ledger.jsonl` change falls inside 2023-01-03..2024-09-13.
- WB4 went live 2026-11-17, ST7-FD was promoted 2026-10-26, and NM-ETF runs in Primary. All of that is after the window.

## Deployment
- None. The deploy rule needs a fresh-window BEAT, and there is none.
- No setup, YAML, account, assignments or ledger change was made.

Educational only — not financial advice.
