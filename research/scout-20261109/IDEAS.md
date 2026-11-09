# Scout ideas, 2026-11-09 (run 1)

*Educational only — not financial advice. Ideas only: 0 trade configs scored here. The one measurement behind them
is QP1 (research/scout-qp1, 4 configs, 0 pass). Rules below are pre-declarations for the Builder; grids are counted.*

## Why these three
- **Quiet days can't be called at 10:00 from tape structure.** QD1 (8) + QR1 (3) + QP1 (4) = 15 predictor configs,
  best lift +10..+12 pts vs the +15 bar. QP1's most stable one: SPY crossing its open >= 2 times by 09:55
  (+10.2 / +10.6 pts TRAIN / VALID). Sector dispersion at 10:00 (stdev of 11 SPDR sectors' % from open / its 20-day
  mean) predicts the **size** of the day in both splits: low tercile |SPY o-c| 0.55% vs 0.76-0.83% TRAIN, 0.39% vs
  0.49-0.51% VALID. Usable for sizing, not as a quiet/not-quiet label.
- **On quiet days the big movers are earnings names.** Move Hunt quiet days in the library (10-29, 11-03; 2 days, descriptive):
  86% of long and 94% of short top movers are earnings-blackout names, vs ~60% on other days. The tradable quiet-day
  movers that remain are mostly sympathy peers (BUG / RBRK cyber, J / CACI gov-IT). So a quiet-day book either trades
  event names or trades something that doesn't depend on the index.

## SC1 — Event-day gap-and-hold (LONG first; short mirror)  [new; touches the gap family but gated by an event proxy + hold test]
- **Universe:** lab names, adv20 >= $60M. **Event proxy (no calendar needed):** |gap| >= G and 09:30-09:55 volume >= 4x
  the name's mean 09:30-09:55 volume over the prior 20 sessions. Live, tag known earnings days separately.
- **Long:** gap >= +G. At check time T (bar close): close > session open, close > session VWAP, and close >= prior close
  + 0.5 x gap (still holds half the gap). Enter next bar open. Stop = low of day so far − 0.05 ATR_d; skip if the stop
  is > 0.6 ATR_d away. Exit 15:55; after +1R trail to the lowest low of the last 6 five-minute bars.
- **Short mirror:** gap <= −G, below open and VWAP, holds >= half the gap down; stop = HOD so far + 0.05 ATR_d.
- **Grid (8):** G {4%, 6%} x T {10:00, 10:30} x side {long, short}.
- **Why:** an event gap that holds its open for 30-60 min shows informed, persistent demand (intraday onset of
  post-event drift; er-react-gap found gap-and-go continues and faded gaps reverse at daily horizon). Intraday event-day
  entries were never tested on 2y because there is no historical calendar (sw-w5-earnings-history) — the volume proxy
  sidesteps that. Long-side fit for P3.
- **Controls:** same gaps that fail the hold test; random entry time on the same names/days; report up/flat/down days.
- **Caveat:** live trading blacks out earnings names (+-4 days) — passing this would be an owner decision to exempt one setup.

## SC2 — Cross-asset driver -> equity laggard catch-up (both sides, independent of the index day)  [new family]
- **Drivers -> followers (lab symbols only):** USO/UCO -> XLE XOP XOM CVX COP OXY DVN EOG APA FANG HAL SLB EQT AR RRC;
  GLD/SLV -> GDX GDXJ NEM AEM GFI KGC WPM PAAS AU FNV AG CDE RGLD; IBIT -> MSTR COIN MARA RIOT CLSK HUT CIFR WULF HOOD.
- **Signal at a 5-min bar close, 10:00-15:00:** driver's 15-min return z >= Z (vs stdev of its 15-min returns over the
  prior 20 sessions, same clock window) and driver on the same side of its VWAP. Follower: beta to driver (5-min returns,
  prior 20 sessions) >= 0.5; follower's own 15-min return < L x beta x driver return (laggard). Enter follower in the
  driver's direction at next bar open. Stop 0.25 ATR_d; target 1R; time exit after H minutes.
- **Grid (12):** Z {1.5, 2.0, 2.5} x L {0.3, 0.5} x H {30, 60}. Report raw and SPY-beta-hedged (MH4 showed raw P/L can
  hide a real excess when entries carry the day's direction; a commodity driver should carry less of it).
- **Why:** slow information diffusion from commodity/crypto tapes to equities (industry lead-lag literature; equity
  traders under-watch other asset tapes). Move Hunt 11-04 had an oil cluster at 10:30-10:50 (UCO/BNO/USO/PDBC short,
  SCO long — Wednesday 10:30 EIA report time) and 11-05 a gold-miner turn. Day-type neutral by design.
- **Slice to report (not an extra config):** Wednesday 10:30-11:00 EIA window for the oil group.

## SC3 — Sector dispersion as a size dial (QDAY, builds on QP1; sizing before filters per the charter)
- **Rule:** at 10:00, disp_ratio = stdev of the 11 SPDR sectors' % from open (09:55 close) / its prior-20-session mean.
  Low = <= 0.76 (QP1 TRAIN tercile). For entries at or after 10:00: counter-index / fade setups 1.0x size on low days,
  0.5x otherwise; held-side / trend setups (GATE2 family) 0.5x on low days, 1.0x otherwise.
- **Test (2 configs):** re-weight the 2y lab trade lists (research/history2y/data/bt_lab1104) per setup; report avg R per
  $ risk before/after, avg R w/o best day, and per setup how many improve vs get worse and by how much (Remedies rule).
- **Why:** low dispersion = smaller SPY day in both splits (above); fades need a small day, trend entries need a big one.
