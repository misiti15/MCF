# Part A - Primary setups with a big live loss (paper live; 2-year as-run backtest)
Selected (live P/L since start <= $-100 or 10-20+10-21 <= $-100): L3-gap-slope-fromopen-FD, NS3-failed-vwap-reclaim-short-FD, RW6G1-ns2-up3-vwap2sd-short

## L3-gap-slope-fromopen-FD
- Live Primary (paper): {'trades': 5, 'sessions': 1, 'win_pct': 0.0, 'breakeven_win_pct': None, 'avg_r': -1.149, 't': None, 'pnl_adj': -176.93, 'sum_r': -5.75, 'last4_avg_r': -1.149, 'last4_pnl': -176.93, 'first': '2026-10-21', 'last': '2026-10-21'}
- Live all accounts merged (paper): {'trades': 133, 'sessions': 7, 'win_pct': 61.7, 'breakeven_win_pct': 52.3, 'avg_r': 0.147, 't': 0.7, 'pnl_adj': 350.18, 'sum_r': 19.5, 'last4_avg_r': 0.332, 'last4_pnl': 522.08, 'first': '2026-10-13', 'last': '2026-10-21'}
- Live Primary by day: 2026-10-21 Choppy 5 trades -5.7R $-177
- 2-year as-run: n 25124, avg R -0.030 (t -0.62); train -0.032 / valid -0.029
- By regime (avg R, n): Bull -0.051 (12229); Bear +0.078 (3505); Choppy -0.066 (3834); Quiet -0.027 (5466)
- Worst live Primary day -5.7R. On 2 years, 101 setup-days were that bad or worse (24.05 per 100 sessions; percentile 25.6% of its traded days); regimes {"Bull": 40, "Quiet": 36, "Choppy": 16, "Bear": 8}.
- Days <= -5R: 105 ({"Bull": 42, "Quiet": 38, "Choppy": 16, "Bear": 8}); <= -10R: 74 ({"Bull": 30, "Quiet": 25, "Choppy": 12, "Bear": 6}).
- Clustering: bottom-decile day (<= -22.6R) base rate 0.10, after a bottom-decile day 0.05; longest run 2.
- By regime, setup-days: {"Bear": {"days": 72, "sum_R": 272.4, "avg_day_R": 3.78}, "Bull": {"days": 88, "sum_R": -621.8, "avg_day_R": -7.07}, "Choppy": {"days": 67, "sum_R": -251.8, "avg_day_R": -3.76}, "Quiet": {"days": 163, "sum_R": -146.3, "avg_day_R": -0.9}}

## NS3-failed-vwap-reclaim-short-FD
- Live Primary (paper): {'trades': 32, 'sessions': 2, 'win_pct': 15.6, 'breakeven_win_pct': 55.9, 'avg_r': -0.374, 't': -4.19, 'pnl_adj': -484.71, 'sum_r': -11.97, 'last4_avg_r': -0.374, 'last4_pnl': -484.71, 'first': '2026-10-20', 'last': '2026-10-21'}
- Live all accounts merged (paper): {'trades': 84, 'sessions': 7, 'win_pct': 39.3, 'breakeven_win_pct': 43.6, 'avg_r': -0.058, 't': -0.35, 'pnl_adj': -358.95, 'sum_r': -4.9, 'last4_avg_r': -0.036, 'last4_pnl': -337.74, 'first': '2026-10-12', 'last': '2026-10-21'}
- Live Primary by day: 2026-10-20 Choppy 6 trades -0.2R $-3; 2026-10-21 Choppy 26 trades -11.7R $-482
- 2-year as-run: n 16955, avg R -0.015 (t -0.63); train -0.004 / valid -0.021
- By regime (avg R, n): Bull -0.154 (2511); Bear +0.067 (5584); Choppy -0.067 (2806); Quiet -0.008 (6013)
- Worst live Primary day -11.7R. On 2 years, 51 setup-days were that bad or worse (12.11 per 100 sessions; percentile 12.0% of its traded days); regimes {"Choppy": 14, "Bull": 13, "Quiet": 13, "Bear": 11}.
- Days <= -5R: 112 ({"Quiet": 44, "Bull": 32, "Choppy": 21, "Bear": 15}); <= -10R: 59 ({"Quiet": 16, "Choppy": 15, "Bull": 15, "Bear": 13}).
- Clustering: bottom-decile day (<= -13.1R) base rate 0.10, after a bottom-decile day 0.14; longest run 2.
- By regime, setup-days: {"Bear": {"days": 81, "sum_R": 374.5, "avg_day_R": 4.62}, "Bull": {"days": 90, "sum_R": -386.3, "avg_day_R": -4.29}, "Choppy": {"days": 72, "sum_R": -188.0, "avg_day_R": -2.61}, "Quiet": {"days": 177, "sum_R": -46.7, "avg_day_R": -0.26}}

## RW6G1-ns2-up3-vwap2sd-short
- Live Primary (paper): {'trades': 3, 'sessions': 1, 'win_pct': 0.0, 'breakeven_win_pct': None, 'avg_r': -1.069, 't': None, 'pnl_adj': -102.18, 'sum_r': -3.21, 'last4_avg_r': -1.069, 'last4_pnl': -102.18, 'first': '2026-10-15', 'last': '2026-10-15'}
- Live all accounts merged (paper): {'trades': 3, 'sessions': 1, 'win_pct': 0.0, 'breakeven_win_pct': None, 'avg_r': -1.069, 't': None, 'pnl_adj': -102.18, 'sum_r': -3.21, 'last4_avg_r': -1.069, 'last4_pnl': -102.18, 'first': '2026-10-15', 'last': '2026-10-15'}
- Live Primary by day: 2026-10-15 Bull 3 trades -3.2R $-102
- **No 2-year backtest** (not covered by the frame scan).
