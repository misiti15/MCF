Educational only — not financial advice.

# Root cause 2026-11-19 — dimension: CONDITIONS (market state at entry)

Research only. No config, setup, exit or order change. Scripts and intermediate data: `cond_work/` next to this file
(compass.py, feats.py, gates.py, tab.py, gates.csv). Alpaca data GETs made: 4 (1 for today's 1-min bars, 3 for SPY/QQQ/IWM 11-05..11-18).
Locked block 2024-11-01..2025-02-28 never read (asserted on every load). Costs in: live R = pnl_adj / (|entry-stop| x shares);
lab R = bt_lab1104 production-cost R (research/history2y/data/bt_lab1104). Lab L3 is capped at 3 lots per symbol-day to
look like live (lab refires are otherwise uncapped). Live = every `paper` trade in all 9 account journals (2026-10-06..11-19).

**Configurations tried: 5 gate configs (G1-G5), each scored on TRAIN / VALID / FWD (lab) and LIVE.** Plus 6 descriptive
cuts (compass alignment, SPY from-open, SPY last 30 min, SPY range so far, rest-of-day, SPY move after entry) — no
selection was made from these.

**Rule-change context (research/ledger.jsonl) for the live window:** ST7-FD promoted Testing 1 -> Primary 2026-10-25;
L3 first Primary session 10-21, demoted 10-22, re-promoted 10-30 (earlier live trades are Testing 1); Primary position size
~$5k then ~$4k on 10-27; Primary per-setup daily stop -2R (latched) from 10-28 (it latched both setups today); 11-09
generator temp moves (not these setups). Live figures below mix Testing 1 and Primary periods of each setup.

## What happened at ~11:50 (SPY/QQQ 1-min, Alpaca)
- SPY fell from -0.12% (10:00) to -1.38% (10:40) from its open. ST7's 7 longs (ASML, ETHA, FTEC, MUU, SMH, TER, TECL)
  were bought at 10:45-10:46 in a small bounce (SPY -1.31%, last 30 min -0.70..-0.75%). All are Nasdaq/semis beta.
- SPY bounced to -1.03..-1.16% by 11:15-11:45. L3 shorted SPXS/SQQQ (inverse ETFs) 6 times 11:16-11:46 — **shorting an
  inverse ETF is a long-market bet**. So all 14 losing positions were the same trade: long Nasdaq/S&P beta.
- 11:49-12:05 a sharp leg down: **SPY -1.03% -> -2.66%, QQQ -1.23% -> -3.53% in ~16 minutes** (QQQ 663.7 -> 647.2,
  volume 2-4x). SQQQ +4.0% -> +11.4%. L3's 6 stops hit 11:51-11:52; ST7's stops 11:53-12:18. Stops are 0.25 x daily ATR
  (t1s1), so a 1.6% index leg is several stops deep on 3x ETFs and semis.
- Compass (W60): recorded CSV for today has only the 09:45 row; the owner/dashboard mark is DOWN-confirmed at 11:15. A
  breadth-free proxy (81% agreement with the real W60 on history) reads DOWN-confirmed already at the 10:45 mark. So
  ST7's 10:45 entries were at/just after confirmation and **all 6 L3 inverse-ETF shorts came after DOWN was confirmed**.
- Did the compass "know" the 11:50 drop? No: on 2 years, after a DOWN-confirmed reading SPY's next 60 minutes went down
  only **48.9%** of the time (UP-confirmed: 53.7%; n 5,501 marks) — a coin flip, matching COMPASS-LEARN.

## Whole record: R by market state at entry (both setups)
Market side = trade side, flipped for inverse ETFs (beta to SPY < -0.3 on 2-year daily returns).

| | ST7 LIVE (58) | ST7 LAB (1,114) | L3 LIVE (403) | L3 LAB capped (14,128) |
|---|---|---|---|---|
| all | -0.059 (w/o best day -0.139) | +0.036 (w/o best +0.028, best 24%) | +0.202 (w/o best +0.148, best day 41%) | -0.066 |
| compass AGAINST (confirmed opposite) | +0.002 (25) | **+0.123 (333)** | **+0.306 (187)** | -0.012 (7,272) |
| compass aligned | -1.07 (1) | -0.008 (195) | +0.227 (63) | -0.155 (1,148) |
| unconfirmed | -0.076 (32) | +0.002 (586) | +0.064 (153) | -0.117 (5,708) |
| SPY last 30 min against <= -0.5% | -0.821 (9, 3 days) | **+0.542 (64)** | +0.635 (21) | +0.069 (2,030) |
| SPY from open against <= -1.0% | -0.399 (17, 6 days) | +0.147 (46) | +0.586 (38) | +0.097 (3,265) |
| SPY moved against >0.5% after entry (not knowable) | -0.700 (13) | -0.928 (72) | -0.89 (2) | -1.024 (1,164) |
| SPY moved with >0.2% after entry (not knowable) | +0.44 (9) | +0.45 (299) | +0.62 (144) | +0.65 (3,867) |
| rest of day against >0.5% (day type, not knowable) | +0.02 (10) | -0.536 (135) | -1.057 (8) | -0.560 (2,129) |

- **Correlation of R with the SPY move after entry (in the trade's market direction): ST7 live 0.41, lab 0.41; L3 live
  0.40, lab 0.42.** Both setups are, to a large degree, market-direction trades after entry: the market path decides a big
  share of every outcome.
- **But no point-in-time state at entry separates the bad entries on the whole record.** The "counter-compass" state that
  looks guilty today is ST7's *best* lab bucket and L3's *best* live bucket — both setups are counter-moves (dip buy;
  fade of a gap-down recovery) and naturally fire against the tape. Falling-knife entries (SPY -0.5% in the last 30 min)
  are ST7's best lab bucket (+0.542R, 64 trades) even though its 9 live ones lost (3 days). Vol (SPY range so far) gives
  no monotone pattern.
- Live ST7 is a 58-trade record at -0.059R/trade (w/o best day -0.139R); it is not a "100% win" setup. Live L3 is the
  strong one (+0.202R, 403 trades, best day 41% of R).

## Gates tested (point-in-time; effect per setup across all 95 lab setups and all live setups)
Delta = R of removed trades with the sign flipped (positive = the gate helps). Lab capped 3 lots/symbol-day.

| gate | split | setups affected | improve / worse | gained / lost R | removed avg R | ST7 | L3 |
|---|---|---|---|---|---|---|---|
| G1 block counter-compass entries | TRAIN | 92 | 59 / 33 | +16,364 / -1,515 | -0.099 (rest -0.073) | -5.0 | -131.4 |
| | VALID | 94 | 49 / 45 | +6,749 / -1,123 | -0.043 (rest -0.068) | -32.1 | +134.5 |
| | FWD | 85 | 57 / 28 | +1,497 / -376 | -0.081 (rest -0.072) | -4.0 | +85.7 |
| | LIVE | 132 | 89 / 43 | +820 / -244 | -0.090 (rest -0.129) | -0.1 | **-57.2** |
| G2 falling-knife (SPY 30m against <= -0.5%) | TRAIN/VALID/FWD/LIVE | 87/82/38/81 | 45/42, 44/38, 20/18, 44/37 | net -856 / +464 / -7 / +62 | ~0 | -16.0/-18.7/0/+7.4 | -191/+51/+1/-13 |
| G3 SPY from-open against <= -1.0% | TRAIN/VALID/FWD/LIVE | 86/80/35/93 | 53/33, 41/39, 17/18, 64/29 | net -163 / +132 / -92 / +261 | ~0 | +6.9/-13.5/-0.2/+6.8 | -290/-25/0/-22 |
| G4 no shorts of inverse ETFs | TRAIN | 46 | 29 / 17 | +404 / -148 | -0.051 (other shorts -0.078) | 0 | +13.3 |
| | VALID | 46 | 21 / 25 | +347 / -148 | -0.041 (other shorts -0.046) | 0 | +31.6 |
| | FWD | 43 | 41 / 2 | +267 / -4 | -0.377 (other shorts -0.071) | 0 | +6.3 |
| | LIVE | 41 | 29 / 12 | +71 / -12 | -0.351 (other shorts -0.081) | 0 | +10.0 (15 trades) |
| G5 G4 only while DOWN-confirmed | TRAIN/VALID/FWD/LIVE | 41/42/26/18 | 21/20, 18/24, 17/9, 12/6 | net +75 / +78 / +69 / +23 | -0.03/-0.05/-0.43/-0.45 | 0 | +6.2/+6.1/+2.6/+6.5 |

Reading the table honestly:
- **G1 (compass gate) fails.** Its big lab "net" only means "trade a losing lab book less": the removed trades are no worse
  than the kept ones (VALID -0.043 vs -0.068, LIVE -0.090 vs -0.129). It hurts ST7 in every split and costs L3 -57R live.
  It would have removed all 14 of today's losers (+15R today) but is not a remedy on the whole record.
- **G2 / G3 (SPY-move gates) fail**: removed trades average ~0R, nets flip sign across splits, ST7 and L3 mixed.
- **G4 / G5 (inverse-ETF shorts) is the one targeted candidate, with weak support.** It fixes a specific failure mode:
  a short setup quietly taking long-market exposure (and stacking with the long setups). In TRAIN/VALID inverse-ETF shorts
  were about as good as other shorts (no edge loss, no edge either; VALID 21 setups better / 25 worse); in FWD and LIVE
  they were much worse (-0.38 / -0.35R vs -0.07 / -0.08R; worst day only 22% of the loss). For L3 it helps in all four
  splits (+13 / +32 / +6 / +10R); it never touches ST7. Today it would have kept L3 out of the 6 SPXS/SQQQ shorts
  (-6.49R, 45% of the day). Its evidence is mostly the last 6 weeks, so treat as a backlog candidate, not proven.

## Verdict for this dimension
- Market condition is the **outcome driver** of today: a 1.6% index leg down at 11:49-12:05 hit 14 positions that were
  all long Nasdaq/S&P beta (ST7's 7+1 longs and L3's 6 inverse-ETF shorts). Size: essentially all of -15.2R of the two
  setups moved with that leg.
- Market condition **as knowable at entry is not a root cause that a gate can fix**: no point-in-time state (compass,
  SPY from open, SPY last 30 min, range) separates winners from losers on the whole record, the compass does not predict
  the next 60 minutes (48.9%), and the counter-compass state is where both setups earn best.
- The part of "conditions" that is fixable is structural, not a market read: **L3's inverse-ETF shorts convert it into a
  long-market setup** (6 of 6 lost today, -6.49R; 15 live trades -0.669R on 3 days). That is a symbol-class rule, which
  also lowers hidden same-direction exposure across setups.
- Underestimate rather than overestimate: today's compass state comes from an owner mark plus a proxy; live samples per
  bucket are small (ST7 9-25 trades in its key buckets, 3-9 days).

Remedies (all research only, none applied; market hours):
1. G4 "short setups do not short inverse ETFs" (or G5, only while DOWN-confirmed) -> backlog candidate with a locked
   check; tested above: L3 +13/+32/+6/+10R; across setups TRAIN 29 better / 17 worse, VALID 21 / 25, FWD 41 / 2, LIVE 29 / 12.
2. Do NOT add a compass or SPY-move entry gate to ST7 / L3: tested, hurts ST7 in every split and L3 live (-57R).
3. Untested: count inverse-ETF longs/shorts as market exposure in any cross-setup exposure check (hand-off to the
   stacking/exposure dimension).

Educational only — not financial advice.
