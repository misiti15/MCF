Educational only — not financial advice
# Longs 11-25 autopsy (research only, 2026-11-26)
Data: `footrace.live_trades()` logic (LR8-cost R, identical signals once) + journal entry times; SPY 1-min Alpaca SIP (cache ends 11-04). SPY 11-25: open 703.19, low −1.10%, ~−0.5% at 11:30, turn ~11:56, last bar +1.93%. Longs +256.4R / 850 trades; shorts −1,483.2R / 1,928.
**11-25 longs by phase:** pre-turn (<11:56) +141.6R, 301 tr, avg +0.47, 79% win, SPY at entry −0.35% | turn (11:56–12:30) +113.9R, 139 tr, avg +0.82, 86% win, SPY +0.27% | post-turn +0.9R, 410 tr, avg 0.00, 52% win, SPY +1.56%.
30-min buckets (R / n / SPY at entry): 09:30 +14.5/12/−0.44 · 10:00 −11.0/88/−0.12 · 10:30 +92.9/122/−0.36 · 11:00 +44.1/62/−0.59 · 11:30 +4.0/27/−0.49 · 12:00 +111.1/129/+0.32 · 12:30 +15.8/42/+0.99 · 13:00 +2.9/158/+1.29 · 13:30 −8.1/81 · 14:00 −5.2/69 · 14:30 −2.2/57 · 15:00 −2.2/3.
→ Answer: hot from the morning dip through the turn (10:30–12:30 = +264R); entries after 12:30, into the rally, were flat. Neither "morning" nor "afternoon" alone: the edge was buying weakness before/at the reversal.
**Top long setups 11-25** (R / trades / avg / entry span): GEN-261023-07 Lunch Choppy RSI Turn Buy, testing2 +90.8/48/+1.89/12:00–13:52 · GEN-261022-01 Morning Failed-Break Buy (wild), graveyard +81.0/35/+2.31/10:21–10:51 · GEN-261027-10 Lunch Selling-Flush Buy (ext), testingd +57.7/98/+0.59/12:16–14:02 · GEN-261019-04 Midday Oversold Buy, gen +29.1/30/+0.97/11:06–11:53 · GEN-261027-05 Midday Volume Buy (volatile), graveyard +23.5/62/+0.38/12:00–13:01 · CWT14-failbrk-pdl-p10-lowvol-long-WB3, testingf +12.4/63/+0.20 · CWT14-failbrk-orl-p05-long, graveyard +10.0/98/+0.10 · GEN-261020-07 Morning RSI Surge Buy, graveyard +9.6/21 · IDX1-qqq100-0955-TQQQ-hold, explore1 +8.4/1 · GEN-POD1022-02 Breadth Thrust ETFs, gen +8.2/2.
**Concentrated, not broad:** 33 of 49 long setups positive, but top 3 = 90% of long R (top 10 = 129%); Graveyard = +124R of 256. Without best symbol: +246R (not one-ticker). One-day caveat: over 10-23..11-25 GEN-261023-07 totals +69.1R (so −21.7R on its other 9 days), GEN-261022-01 −20.2R (−101R outside 11-25), GEN-261027-10 +25.3R (−32R outside).
**Shorts 11-25 (contrast):** pre −360.6R (435 tr, avg −0.83, 11% win) | turn −449.5R (416, avg −1.08, 1% win) | post −673.2R (1,077, avg −0.63). Worst buckets 11:30–13:30 (−1,261R); 14:00+ ≈ flat. Broad: 53 of 58 short setups lost; top 10 losers = 78%, 7 of them the L3 gap-down fade family (L3-gap-slope-rsi5hi-FD testing −219R/311, its WB5 livelab −171R, fromopen-FD-WB4 testing2 −150R, lowdist-FD testing −145R, ...).
## Pattern check, live window 10-23..11-25 (24 sessions, longs)
Day types (SPY last vs open): up ≥ +0.3% 8 days, down ≤ −0.3% 9, flat 7; V-days (low ≤ −0.4% then close > open) 3 = 11-10, 11-24, 11-25.
| Long avg R (R, days) | pre <11:56 | 11:56–12:30 | post 12:30 |
|---|---|---|---|
| up (8) | +0.01 (+17.6R) | +0.21 (+83.9R) | −0.15 (−180.7R) |
| flat (7) | −0.11 (−326.2R) | −0.10 (−21.9R) | +0.08 (+64.8R) |
| down (9) | −0.36 (−1,449R) | −0.42 (−232.6R) | −0.30 (−399.8R) |
| V-days (3) | +0.14 (+143.1R) | +0.53 (+129.2R) | −0.05 (−39.1R) |
| non-V (21) | −0.21 (−1,901R) | −0.32 (−299.8R) | −0.19 (−476.7R) |
V-days without 11-25 (2 days): AM (<12:00) +1.1R/723 tr (avg 0.00), PM −24.3R/510 (avg −0.05); 11-10 PM +45R, 11-24 PM −69R. Longs were net positive on only 6 of 24 days (10-23, 11-09, 11-10, 11-11, 11-13, 11-25).
**Verdict:** 11-25 is close to unique. "Long afternoons after a morning dip" does not recur: V-day PMs are ≈ 0 outside 11-25, and post-12:30 longs lose on up and V days. The faint recurring signal is the midday turn window on up/V days (avg +0.21 / +0.53), n = 8 and 3 days, mostly 11-25 — a hypothesis for the backlog, not evidence. Down days (9) are where long R is lost, at every hour.
Rule changes in window (research/ledger.jsonl, 161 entries effective 10-23..11-23, none on 11-24/25): Primary size 4k→5k + 2R setup daily stop (10-28/29); testing cost filter (10-30); Explore 1/Live Lab low-rep homes (11-05); Testing D/E/F + full universe, LR8 cost basis, sizing caps, account halt 300 (11-12); rotations/WB variants (11-16..11-20); brake-burst (11-23). The setup mix and account count changed mid-window, so day cells are not like-for-like.
Configurations tried: 1 (fixed buckets/phases as asked; no tuning).
