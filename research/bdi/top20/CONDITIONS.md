# Top-20 setups: when they thrive and when they struggle (running table)

*Educational only - not financial advice.*

- **Top 20** = the dashboard leaderboard order (shrunk avg R = avgR x n / (n + 20), all live records since start,
  Primary + Testing 1 + Testing 2 + Graveyard, GEN-* and S6 out, >= 20 trades, setups enabled somewhere now).
- **Live** = paper trades (rule 7), a diagnosis rather than evidence. "2y" = backtest of the live-shaped signal on the
  open two-year history (TRAIN + VALID, costs in, locked block never loaded).
- "Thrives / struggles" uses **point-in-time conditions only**: SPY vs its open at 10:00 or at entry (+/-0.10% bands),
  time of day, gap, ADV, price, ATR%, stock / ETF / leveraged ETF, side. Day type (SPY up / down / quiet open-to-close,
  +/-0.25%) is hindsight. It is shown in the notes but never used as a condition.
- **No strangling filters.** A condition is only proposed as a filter if skipping it keeps >= 70% of trades and >= 90% of
  top-decile winners. Otherwise it is a sizing or "on deck" idea.
- **Rotation:** all 20 are read live every run. 5-8 are done "deep" (live + 2y) each night, and the full 20 are deep at
  least once a week. Check the `depth` column before choosing tonight's deep set.
- Each night's files: `research/bdi/top20/` (scripts plus live_* / hist_* outputs) and `research/bdi/top5_<date>/NOTES.md`.

| date | rank | setup (acct now) | n live | depth | thrives when | struggles when | note |
|---|---|---|---|---|---|---|---|
| 2026-11-03 | 1 | MF2-open-rsimidhi-flowsell-FD (P) | 67 | deep | gap-down names (gap <= -1%) while SPY is below its open at entry (live +0.99R, n 38) | SPY flat at entry (live -0.46R, n 9); 2y: SPY below its open at 10:00 (-0.11R) and price < $20 (-0.21R) | 63% of total R on 10-22, ex-market +0.29R of +0.70R; 2y -0.058R (up sessions -0.19R): a down-tape bet |
| 2026-11-03 | 2 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (P) | 121 | deep | 10:30-13:00 with SPY below its open at entry (live +0.56R, n 54; 2y -0.004R vs -0.117R above) | SPY above its open at entry (live +0.23R; 2y -0.117R, TRAIN and VALID) and 09:50-10:30 (live -0.57R, n 6) | half size when SPY is above its open: on deck (sizing_check) |
| 2026-11-03 | 3 | RW3-gapdn-rsi5pop-flowsell-short-FD (P) | 93 | deep | SPY below its open at entry (live +0.61R, n 51) | SPY above its open at entry (live -0.04R, n 29, 54% of losing R; 2y -0.103R) | 71% of total R on 10-22; ex-market +0.14R |
| 2026-11-03 | 4 | L3-gap-slope-fromopen-FD (P+T1) | 250 | deep | SPY above its open at 10:00 (live +0.37R, n 90; 2y +0.018R vs -0.017R parent) | SPY below its open at 10:00 (live -0.33R, n 35; 2y -0.126R, TRAIN -0.19 / VALID -0.03) | live after 13:00 -0.82 / -0.25R, but 2y's best slice is 14:00+ (+0.14R), so they disagree; 74% of R on 10-20 |
| 2026-11-03 | 5 | NM-MF3-qqqdn-gapdn-FD (T2) | 24 | deep | ETFs, 11:30-13:00 (live +0.74R, n 17) | single stocks (live -0.09R, n 15) | 4 sessions; the record is one day (199% of total R on 10-22); 2y -0.004R |
| 2026-11-03 | 6 | L3-gap-slope-rsi5hi-FD (P+T2) | 81 | deep | SPY flat or above its open at 10:00 (live +0.27 / +0.16R) | SPY below its open at 10:00 (live -0.47R, n 11, 34% of losing R; 2y -0.100R vs -0.047R) | 2y 14:00+ +0.067R |
| 2026-11-03 | 7 | NS4-pm-vwap-reclaim-oversold-short-FD (T1) | 26 | deep | ATR% >= 5 (live +0.58R, n 17; 2y +0.001R vs -0.060R parent) | ATR% 2-3.5 (live -1.05R, n 6; 2y -0.133R, both splits) | 91% of total R on 10-22; skipping ATR% 2-3.5 keeps 77% live / 73% 2y, but 2y still -0.033R |
| 2026-11-03 | 8 | NS5-sma50-flush-oversold-long (P) | 24 | deep | price $20-50 (live +0.75R, n 8); 2y gap +1..+3% (+0.10R) | SPY above its open at 10:00 (live -0.56R, n 5; 2y -0.23R in TRAIN, +0.11R in VALID, mixed) | live-only signal; 2y TRAIN -0.17 / VALID +0.16R |
| 2026-11-03 | 9 | MF4-h40-open-flowsell-FD (P) | 80 | live | SPY below its open at entry (live +0.33R, n 22) | SPY flat at entry (live -0.31R, n 16) | 2y in top5_1102: -0.10R |
| 2026-11-03 | 10 | L3-gap-slope-lowdist-FD (T1) | 59 | deep (top5) | 2y: SPY flat at 10:00 (+0.089R, both splits); live 10:30-11:30 (+0.48R, n 17) | 11:30-13:00 (live -0.23R, n 31, 72% of losing R); 2y price < $20 (-0.29R) | 2y loses 10:30-11:30 (-0.31R), so live and 2y disagree; 329% of total R on 10-20 |
| 2026-11-03 | 11 | RW1-gapdn-bounce-flowsell-short-FD (T2) | 83 | deep (top5) | ETFs (live +0.43R, n 22), SPY below its open at entry (+0.22R) | SPY flat at entry (live -0.40R, n 17); 2y does not confirm (G17 no gain) | ex-market -0.11R |
| 2026-11-03 | 12 | MF4-h40-open-flowsell (P) | 22 | live | SPY below its open at entry (+0.33R, n 9) | ATR% 2-3.5 (-0.22R, n 8) | thin |
| 2026-11-03 | 13 | RW7-gapdn-bounce-early-short-FD (T1) | 338 | live | ADV >= $1B (+0.21R, n 61), ETFs (+0.20R, n 63) | SPY flat at entry (-0.14R, n 83) | ex-market -0.105R |
| 2026-11-03 | 14 | ST7-rsi50dn-long-pm-t1s1-FD (P) | 23 (26 on dashboard) | deep (top5) | SPY below its open at entry (live +0.17R, n 11); 2y SPY flat or below at 10:00 (+0.08 / +0.11R) | SPY above its open (live -0.28R, n 8; 2y at 10:00 -0.11R, both splits); live 13:00-14:00 | 3 dashboard trades are missing from reports csv |
| 2026-11-03 | 15 | NS4-pm-vwap-reclaim-oversold-short (P+T2) | 29 | live | SPY below its open at entry (+0.44R, n 9) | flat gap -1..+1% (-0.35R, n 14); ATR% 2-3.5 (61% of losing R) | |
| 2026-11-03 | 16 | MF3-open-flowsell-rsi5hi (P+T1) | 44 | live | SPY above its open at 10:00 (+0.36R, n 12) | 09:50-10:30 (-0.36R, n 17) | 523% of total R on 11-03 |
| 2026-11-03 | 17 | CWT14-failbrk-pdl-p10-lowvol-long (P+T2) | 243 | live | price $20-50 (+0.13R, n 74) | ATR% 3.5-5 (-0.19R, n 55) | total < 0 |
| 2026-11-03 | 18 | RW3S-gapdn-flowsell-short-FD (T2) | 24 | deep (top5) | 10:30-11:30 (live +0.42R, n 10) | 09:50-10:30 (live -0.70R, n 9) | 1 session; 2y says the opposite (<= 10:30 -0.040R vs -0.060R later) |
| 2026-11-03 | 19 | CWT14-failbrk-pdl-p10-long (T2) | 442 | live | SPY above its open at 10:00 (+0.19R, n 99) | SPY below its open at 10:00 (-0.17R, n 175, 51% of losing R); ADV >= $1B (-0.20R) | total < 0 |
| 2026-11-03 | 20 | exhaustion_short (T1) | 77 | live | ATR% 3.5-5 (+0.27R, n 17), SPY flat at 10:00 (+0.14R) | SPY below its open at 10:00 (-0.31R, n 24) | total < 0 |
