# LEAD20 — does leadership breadth at 10:30 raise rest-of-day continuation on SPY-up mornings? (FROZEN 2026-11-14 01:30 ET, before any fetch)
Educational only — not financial advice. Lead lead-20261114-0100-3 (up-day track: information beyond the index's own path).
Null to beat: Observer's OBS-UPDAY-NULL. SPY's return from the decision time to the close is ~0 in all 40 cells; at 10:30 the sign
so far calls the day 76% of the time.

## Data (Alpaca SIP 5-min bars, GET only; 2024-10-01..2026-11-13; locked block 2024-11-01..2025-02-28 never fetched)
SPY, QQQ, SPXL, TQQQ and LEADERS = the 20 largest S&P 500 weights as of Oct 2024 (fixed at the window start, so no hindsight
membership): AAPL MSFT NVDA AMZN META GOOGL GOOG BRK.B AVGO LLY TSLA JPM UNH XOM V MA PG JNJ COST HD.
TRAIN <= 2025-09-30 < VALID.

## Predictor (known at 10:30:00 ET, strict: uses bars closing at or before 10:30)
spy_up = SPY close of the 10:25 bar > SPY 09:30 open. L = share of LEADERS whose 10:25-bar close > their own 09:30 open.
## Rule (ONE config)
On spy_up days with L >= 0.70 (broad leadership): long at the open of the 10:30 bar, exit at the close of the 15:50 bar.
Instruments scored separately in their own prices: SPY, QQQ, SPXL, TQQQ.
Comparison (the null at the same decision time): all spy_up days. Value = mean rest-of-day return on rule days minus mean on
spy_up days with L < 0.70 (the complement), day-level Welch t. Also the rule days' own gross and net mean.
Costs (per share, own price): entry 1c + 1bp x 1.4 + 4.4bp spread, exit 1c + 1bp.

## Counting, bar, pass
Family: market-state gates 2,605 (includes breadth / compass) + 1 = 2,606 -> BAR90 3.57.
Pass (all of): SPY difference t >= 3.57 (full window); rule days' SPY GROSS mean > 0 and NET mean > 0; same sign in TRAIN and
VALID; SPXL net mean > 0; w/o best day > 0. Below the bar but positive in every split -> 'shadow-worthy, not a pass' for Lead.
Kill line: fails -> LEAD20 closed; no grid over the 0.70 threshold or the 10:30 time.
Reported (not gates): share of spy_up days with L >= 0.70; hit rate vs the 76% sign-so-far baseline; L < 0.50 days (narrow
leadership) as a mirror row; TQQQ/QQQ rows.

## RESULT (one look, 2026-11-14 02:10 ET) — FAIL, LEAD20 closed
`fetch.py` (24 symbols, 1.66M 5-min bars) -> `lead20.py` -> `lead20_out.txt`. 453 sessions; SPY up at 10:30 on 242 (53%);
broad leadership (L >= 0.70) on 72 of them (30%); narrow (L < 0.50) on 61.
- Hit (SPY closes above its open): broad days 82% vs all up-mornings 72%. Leadership improves the CALL of the day, but...
- ...rest-of-day return (10:30 open -> 15:55) on broad days: SPY +6.5bps gross (t 0.40), -0.6bps net; complement +0.3bps;
  difference +6.1bps (Welch t 0.37). QQQ +2.9 (t 0.14). SPXL +19.9 (t 0.40; net +12.0). TQQQ +10.4 (t 0.18).
- TRAIN diff +8.5bps (t 0.24), VALID +2.1bps (t 0.17). SPY without its best day: -6.1bps.
- Narrow-leadership mirror: SPY -2.3bps, SPXL -7.8bps (no usable fade either).
Reading: like the index's own sign-so-far (Observer's null), leadership breadth says what the day has ALREADY done, not what
is left. The 3x ETF only scales a ~0 continuation (SPXL t 0.40). Family market-state 2,606, closed.
