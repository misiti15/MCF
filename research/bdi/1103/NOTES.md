# BDI 2026-11-03 (Tuesday): Move Hunt day 4, all-account swing autopsy, swing hypotheses file, COMBO1, QD1

*Educational only — not financial advice. Live numbers are **paper** results from one session (costs in: P/L = journal
`pnl_adj`, R = `pnl_adj / $ risk`). Two-year tests use the history2y lab frames / lab trade lists and the timeofday open
frame; **the locked block 2024-11-01..2025-02-28 is not in those directories and was dropped from the daily table before
any beta / peer / regime table was built (asserted). It was never read.** **21 configurations were tried tonight, all
reported below; 0 pass** (bar t ≥ max(1.5, √(2 ln 21)) = 2.47, BAR90 2.22). No config, setup, exit, ledger or docs/live
file was changed.*

Built on, not redone: nightly1103 (close / coverage / Primary WHY = RW5-FD, latch what-if, BRAKE-1, the 4-config swarm
U1-U3 / V1, backlog L1-L5) and swing1103/AUTOPSY.md (Primary 10:54 low, leads L1-L5).

**Day type today: QUIET.** SPY open-to-close +0.22% (|·| < 0.25%), above its open at 10:00 (+0.15%), high +0.58% at 13:34,
then faded to the close; QQQ +0.14%, IWM −0.01%. Every R figure for today below is therefore a quiet-day, SPY-above-open-
at-10:00 figure.

**Rule changes inside the windows quoted here** (research/ledger.jsonl): effective today 11-03 — MF3-FD (T1) and MF5-FD
(T2) moved to the Graveyard, SO-1A (R2A scale-out cap exempt, T2), RW3S added to Testing 2. From 11-04 (not in today's
numbers): DM-N3 (NS5-FD / ST4-FD / RW6G1-FD → Graveyard), UNI1 (Testing 2 top-500 pool). Primary records span ~$4k size
(10-28), the −2R per-setup latch (10-29) and the L3 pair promotion (10-30); Testing records span the cost filter CF
(10-30). Two-year results are rule-fixed backtests (no live rule change inside them).

## Today's win
**The Move Hunt's captured R turned positive: +4.13R on the day's 50 biggest tradable moves (yesterday −0.65R), and the
wrong-side loss fell to −4.0R from −16.0R — while Primary closed green on a quiet day (+$136.10, +11.33R).** Research win:
tonight measured that the book's large quiet-day edge for counter-index entries (+0.305R on 2 years) is a hindsight label —
"quiet so far" predicts a quiet close only 37% vs 33% base (QD1) — so the QDAY search can stop chasing intraday
quiet-day gates and needs an ex-ante quiet-day predictor first.

## 0a. Move Hunt (v1 definition unchanged; research/bdi/moves/; moves.csv +100 rows for 11-03)
Inputs: SIP 5-minute bars 10-14..11-03 (1,580 symbols), live priors + SIP 1-minute bars, the 5 journals; 1,207 liquid
names, 79,573 decision rows, 737 live trades.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | **1 / 50 (2%)** (WDAY long, GY) | +0.30 | 1, −0.35R | blackout 46 (33 on the event day: LDOS, DD, HSIC, ROKU, FOXA, MDGL, APTV, SYY …) |
| tradable (blackout removed) | **6 / 50 (12%)**: long 5/25, short 1/25 | **+4.13** | 12, **−4.00R** | traded outside the move 19, no setup 17, wrong side only 4, skipped 4 |

**vs 11-02: 22% (11/50), −0.65R, wrong side −16.01R; 10-30: 6%; 10-29: 26%.** Catches: GY CWT12-coil-k4 WDAY / DOCU / ENPH
longs (+0.30 / +0.37 / +0.53R), GY CWT14-failbrk-pdl-p05 (+lowvol) IWS (+0.24R), T2 R2A ADSK (+0.09R), Gen ORBfailDn +
T2 RW3S DG short (+2.60R). Primary caught none of the 50 (it traded the morning's leaders short, see 0b).

What was known at the decision point (only data available then):
- **Gap-down software reversed up at 09:50** (WDAY −1.2% gap, DOCU −2.3%, MANH −1.7%, TTAN −1.7%, CRM −1.7%, ADSK
  −0.4% / −3.0% from open; all below or at the prior-day low) — 6 of the 25 long movers, a group, at the same bar, the
  morning XLK leg (XLK +0.66 → +1.15% 10:54-11:03). Primary / T1 / T2 shorted gap-down names into that tape.
- **The open again:** 23 of 50 decision points at 09:35-09:45 (11-02 36, 10-30 33, 10-29 30).
- **Short side was thin and late** (decisions 10:45-14:10: KEY, RF, BNS, RY banks 10:45-10:55; PCAR, NDAQ, ADSK, BAH after
  13:35 into the SPY fade). 19 were "traded outside the move" (the names were traded, but not inside the window).
- **Skips:** MANH / BAH longs spread > max; ANF short spread vs stop; VFLO long rejected on buying power (Graveyard).
- **Recurring precursor test:** the group-reversal pattern (four Move Hunt days running) is the MH4 peer-laggard signal;
  tonight's COMBO1 is its combined test (step 3): the group again carries day-matched information (+0.03..+0.18R) but no
  form clears costs. No new precursor passes.

## 0b. Swing autopsy, every account (research/bdi/1103/swings.py → swings_out.txt, timeline_<acct>.csv, 5-min)
Method = swing1103 generalised to the full session: 1-min marked R per lot (open = mark, closed = pnl_adj / $risk);
zig-zag legs ≥ 25% of the day's R range; each leg split into **market** (beta × SPY), **setup-day mismatch** (the name's
sector-ETF residual), **bad entries** (fill + stock-specific first 5 min), **stock-specific** remainder (incl. exit fills
and costs); parts sum exactly to the leg (asserted). Betas = 5-min, 10-14..11-02.

**Primary** (43 lots, 41 short + 2 vol-ETP "longs" = short beta): trough −6.69R 10:53, peak +12.44R 15:37, close +11.33R.
Legs: 10:11→10:53 −7.04R (SPY +0.13 → +0.34%), 10:53→11:04 +6.59R, 11:14→12:36 **+10.87R** (SPY +0.43 → +0.26%),
12:36→13:35 −6.01R (SPY → +0.51%), 13:35→close **+11.46R** (SPY +0.51 → +0.19%).
- 11:14→12:36 +10.87R = market +4.23 + mismatch +2.35 + entries 0.00 + stock +4.29. Top 5: ISRG `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`
  +1.22, IWO `MF4-h40-open-flowsell-FD` +1.14, IWR (RW5) +0.96, HON (RW5) +0.81, DIA (RW5) +0.80 (together +4.93R).
- 13:35→close +11.46R = market +5.62 + mismatch +5.49 + entries −0.25 + stock +0.61. Top 5: VEA `MF2-open-rsimidhi-flowsell-FD`
  +1.93, VFLO (RW5) +1.85, AAOZ `L3-gap-slope-fromopen-FD` +1.02, KMI (RW5) +1.00, KMI `RW3-gapdn-rsi5pop-flowsell-short-FD` +1.00.
- Net beta −32R per +1% SPY at 11:15 (−$98k beta-$ on ~$95k), −13.5R at 13:35. **Cause in one line: an all-short book on a
  quiet day — it lost while SPY climbed to +0.51% and won both SPY fades; RW5 drove both recoveries (+6.7R / +6.9R).**
  The morning trough is in swing1103/AUTOPSY.md (market −3.18R, mismatch −1.05R of −6.47R).

**Testing 1** (49 lots, 40 short): same shape — trough −4.86R 10:59, peak +9.93R 15:03, close +6.35R. 11:15→12:37 +12.25R =
market +5.30 + mismatch +4.87 + entries −0.28 + stock +2.37 (ISRG `MF3-open-flowsell-rsi5hi` +1.19, ISRG `RW7-gapdn-bounce-early-short-FD`
+1.15, UPS (RW7) +1.13, IWO (MF3) +1.00, HON (MF3) +0.83); 12:37→13:34 −10.45R = market −5.47 + mismatch −3.50 + entries −0.40 +
stock −1.07 (ISRG RW7 −1.56, UVIX / UVXY `NS5-sma50-flush-oversold-long-FD` −1.25 / −1.18, MCO `MF5-flowsell-vwapup-rsi5hi`
−0.93, IWO MF3 −0.87). Net beta −34R per +1% at 11:15. Recovery after 13:34: RW7, MF3, MF5 on the SPY fade.

**Testing 2** (90 lots, 52 long / 38 short — the only balanced book): trough −9.96R 11:47, close at the peak +5.11R.
10:39→11:47 −9.75R = market +0.35 + mismatch +1.70 + **entries −2.14 + stock −9.66**: LEN `CWT14-failbrk-pdl-p10-lowvol-long`
/ `CWT14-failbrk-pdl-p10-long` −1.31 / −1.31 (same lot twice), SSNC `RW3S-gapdn-flowsell-short-FD` −1.04, HD (pdl-p10) −1.03,
C (pdl-p10) −0.92 — stock-specific, not the market (net beta +6R). 13:36→close +12.10R: RW3S +8.68R (CB, ITB, HON, KBWB),
MF5 +4.55R on the fade.

**Graveyard** (422 lots, 298 long): peak +5.95R 10:50 → trough −45.16R 12:50 → close −29.14R. 10:29→10:50 +24.55R
(mismatch +18.50: the opening failed-breakdown / coil longs' groups rallied) then **10:50→12:50 −51.11R = market −2.95 +
mismatch −18.83 + entries −6.29 + stock −23.04**: `CWT12-coil-k4-long` −15.94, `CWT12-coil-k6-long` −12.12,
`CWT14-failbrk-orl-p05-long` −10.81, `-lowvol-long` −9.69; top 5 XLV (coil-k6) −1.70, JD (orl-p05 ×2) −1.64 / −1.64,
AAL (orl-p05 ×2) −1.51 / −1.51. The peak is the minute the account ran out of buying power (59 rejects 10:50-11:20,
nightly); the give-back is the opening reversal longs' groups rolling over, not the index.

**Generator** (133 lots, 120 long): peak +0.32R 10:12, trough −35.12R 14:57, close −26.10R. **13:34→14:57 −31.67R = market
−40.03 + mismatch +1.36 + entries −1.15 + stock +8.15**; net beta **+94R per +1% SPY** (+$422k beta-$ at 14:59 — ~4× equity
long the index); 14:57→15:47 +22.79R as SPY bounced. Drivers: `GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long`
−9.06, `GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long` −7.88,
`GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long` −7.86.

**Recurring swing type (merged):** in Primary, T1 and Gen the swing is the account's net beta × SPY's quiet-day
oscillation (short books lose the climbs, the long Gen book loses the fade). This is backlog swing1103-L4 (net-beta cap);
its testable side tonight is L6. GY's and T2's swings are stock / group-specific (opening reversal longs giving back).

### Testable leads — research/bdi/swings/hypotheses.jsonl (new file; one pre-registered 2-year backtest each)
`research/bdi/swings/leads_bt.py` → leads_bt_out.txt. Train < 2025-09-01, valid after; R split by SPY day type and by SPY
vs open at 10:00. Forward shadow: `research/bdi/swings/forward.py <scratch> <day>` every later session → forward.csv and
the running n / avg R / t in hypotheses.jsonl (11-03 logged as in-sample, not counted).

| lead | rule (fixed before the test) | 2-year result | day types | verdict |
|---|---|---|---|---|
| L1 vol / inverse-ETP beta guard | long lab setups on beta ≤ −1.5 symbols ≥ 0.10R worse, day-R corr with SPY ≤ −0.5 | n 434 −0.066R vs −0.044R (−0.022R, t −0.53), corr −0.31 | down +0.49 / quiet +0.20 / up −0.30R | fail (a pure direction bet, not worse on average) |
| L2 rotation turn | QQQ new high 10:30-11:30, IWM ≥ +0.40% and ≥ 0.10% under its high ≥ 5 min → family shorts in non-tech next 30 min | 134 trigger days, n 854 −0.118R vs same-day others −0.11R (diff +0.030R, t 0.47) | down +0.34 / quiet −0.08 / up −0.22R | fail |
| L3 up-morning delay (full, incl. IWM) | SPY ≥ +0.15% & IWM ≥ +0.25% at 10:00: family shorts before the first SPY 5-min lower-low bar after 10:30 vs after | 67 days: before −0.078R (828), after −0.104R (411), diff −0.079R t −1.01 | after: up −0.21 / quiet +0.13 / down +0.15 | fail (after is worse) |
| L6 counter-index entries (new) | short with SPY ≥ +0.25% / long with SPY ≤ −0.25% at entry beat the setup's other entries ≥ 0.05R in train and valid, all day types | n 28,320, excess +0.003R (train +0.010 / valid −0.001, t 0.1) | **quiet +0.305R** / down +0.009 / up −0.082R | fail (quiet = hindsight) |

Forward seed 11-03 (in-sample): L1 4 NS5 vol-ETP longs −0.248R (no class-B NS5 trades); L2 no trigger; L3 not qualifying
(SPY +0.1455% at 10:00, just under +0.15%); L6 counter n 180 +0.366R vs others −0.177R. Decisions from leads: none
(nothing passed; a forward pass would become a Testing / Live Lab DECISION, never Primary).

## 0. Per-account session review (accounts.py → accounts_out.txt; peak / close from nightly1103 daily_peak.csv)
All R below is a QUIET-day, SPY-above-open-at-10:00 figure (one day type only today).

**Primary** — **+$136.10** after costs, 43 trades, 67% win vs 48% break-even, **+0.263R**; peak +$207 (15:39) → +$136
(give-back $70: 15 lots still open at the peak, mostly shorts, against the +0.06% SPY uptick into the close).
Best `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` 18 trades +9.8R (+$179), `L3-gap-slope-fromopen-FD` +1.0R (+$98); worst
`L3-gap-slope-rsi5hi-FD` −0.5R (−$94), `RW3-gapdn-rsi5pop-flowsell-short-FD` −1.4R (−$62, latched −2R at 10:47). Shorts
+0.289R (41), longs −0.251R (2, UVIX / UVXY). Skips: 103 not shortable (L3's inverse ETFs), 13 latch (what-if +8.19R missed,
nightly). Index-linked stacking: IWB ×2, IWR ×3, IWO, IWS, DIA, SPLV, VEA, VFLO shorts + UVIX / UVXY longs = one short-SPY bet
(13 same-symbol stack lots +4.0R). Edits: (1) none to rules from one green quiet day; (2) L1 forward tag on NS5 vol-ETP
longs (logged); (3) L4 / L6 shadow tags (logged).

**Testing 1** — **+$12.56**, 49 trades, 57% win vs 47%, +0.130R; peak +$70 (14:56) → +$13 (give-back $57: 31 open at the
peak, the 15:00-15:55 SPY bounce against a short book). Best `RW7-gapdn-bounce-early-short-FD` +5.5R (17 trades),
`MF3-open-flowsell-rsi5hi` +3.4R; worst `NS1-rsidip-rsi5pop-long-FD` −1.7R (4), `NS5-sma50-flush-oversold-long-FD` −0.5R.
Shorts +0.266R (40), longs −0.478R (9). Skips: cost filter 26, not shortable 12. Edits: NS5-FD leaves on 11-04 (DM-N3);
RW7-FD now 348 trades — still flat long-run (nightly 1102: +0.001R), no promotion case.

**Testing 2** — **+$40.64**, 90 trades, 67% vs 62%, +0.057R; closed at the peak (trough −$75 11:48). Best
`MF5-flowsell-vwapup-rsi5hi` +5.7R (10), R2A long 20 trades +0.3R (+$23); worst `RW3S-gapdn-flowsell-short-FD` 24 trades
−1.2R (−$39, day 1 in T2; it drove the 13:36-close leg with +8.7R after losing in the morning), CWT05-flush long −1.5R. Longs +0.007R (52), shorts +0.125R (38).
Skips: cost filter 37, not shortable 17. Stacking: LEN / C each held by two pdl-p10 sister setups (−$18 / −$11).
Edit: queue nothing new — the sister-setup stacking item (bdi-1102-underlying-exposure-cap) covers LEN / C.

**Graveyard** — **−$307.89**, 422 trades, 58% vs 63%, −0.069R; peak +$44 (09:58) → −$308 (380 after-peak entries; the
opening reversal longs gave back after 10:50, see 0b). Longs −0.133R (298, −$362), shorts +0.086R (124). Best
`MF3-open-flowsell-rsi5hi-FD` +5.6R (moved in today), `heat_fade_short-FD` +6.1R; worst `CWT12-coil-k4-long` −13.2R,
`CWT14-failbrk-orl-p05-lowvol-long` −12.3R. 59 buying-power rejects (GY-BP replay is queued; another session runs it).
Edit: none (data collection, rule 20).

**Generator** — **−$585.51**, 133 trades, 40% vs 58%, −0.196R; peak +$10 (10:13) → −$586 (132 after-peak entries; a
long-beta book into the SPY fade, market −40R in 13:34-14:57). Worst `GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long`
−9.0R (21; same setup −47.3R on 11-02), best `GEN-261027-02-NewLOD-RSI14le35-Gapge2-PM-SPYup-holdtr-long` +0.6R. Edit: none
new (GEN-261021-06 is the Generator's own retirement call; the beta stacking is L4).

## 1. Every trade, all accounts (trades_bdi.py → trades_bdi_out.txt, per_trade_1103.csv; patterns.csv +318 losers)
737 trades with SIP 1-minute paths; 318 losers. Exit what-ifs (sum R after costs; live / be05 / t1 / trail / hold / sar /
reenter / opp): Primary +11.3 / +7.6 / +15.2 / +11.5 / **+25.5** / +6.9 / +10.5 / −15.8; T1 +6.4 / +6.7 / +9.2 / +6.5 / +10.7 /
+4.0 / +5.8 / −9.4; T2 +5.1 / +6.7 / +5.8 / −0.2 / −3.4 / +2.1 / +8.4 / −6.8; GY −29.1 / **−10.6** / −54.8 / −38.8 / −84.0 /
−22.3 / −23.6 / +42.5; Gen −26.1 / −21.3 / −17.8 / −19.2 / −20.0 / −20.2 / −20.7 / +13.2. Per trade live −0.044R, opposite
+0.032R (se ~0.03). One day: hold won for the short books, breakeven-at-0.5R for GY's longs — no exit change from one day
(hold lost −129.8R in GY on 10-30).
- **Loss types:** small-MFE-then-failed 75 (−$1,277, GY 49), never-worked 70 (−$1,077), late hold 89 (−$707, Gen 33),
  gave-back-gains 46 (−$514), wrong-side-after-big-swing 25 (−$481), stopped-then-reversed 13.
- **Opposite side, hindsight check:** shorts entered while SPY was ≥ +0.25% up made **+0.357R live (n 177)** (11-02:
  +0.314R, n 86) — two days running, so it was tested on 2 years tonight as L6: no edge beyond the day type.
- **Give-back:** Primary $70 / T1 $57 (short books into the 15:00-15:55 bounce), GY $351 and Gen $595 (after-peak entries).
- **Correlated stacking:** Primary's index-ETF shorts + vol-ETP longs were one short-SPY bet (above); Gen's +$422k
  beta-$ long book is the same thing on the other side; GY 85 same-symbol stacks (187 lots −7.4R; COPX 3 lots −$52).

## 2. Patterns → rules
1. Book R = −net beta × SPY on quiet days (Primary, T1, Gen) → L4 (backlog) / L6 (tested, fails).
2. Gap-down software group reversal at 09:50 (Move Hunt) → the MH4 / COMBO1 group line (tested, fails absolute).
3. Opening reversal longs (CWT12 coil, CWT14 orl / pdl) peak by ~10:50 and give back (GY, 5+ days in patterns.csv:
   coil-k4 never-worked / small-MFE 5 days each) — Graveyard setups; no new rule (pdl / orl family exhausted this week).

## 3-4. New tested ideas (queue order: COMBO1 first; GY-BP left to the session already running it)
**COMBO1** (`combo1.py` → combo1_out.txt, combo1_results.csv; owner item, top of research/queue.jsonl). Top-500 by ADV × ATR%
→ 09:35 scan (top 150 by volumeRatio, declared proxy for opening $ volume / adv20) → MH4 peer laggard (P ≥ 0.40 ATR,
agree ≥ 0.7, own z < P/2) at 09:40-09:50 → optional fade-timing bar; exits t1s1 or to 10:30 SPY-hedged. 9 configs:

| config | n | /day | avg R | t | w/o best day | train / valid | up / down / quiet | day-matched excess (t) |
|---|---|---|---|---|---|---|---|---|
| long-any-t1s1 | 416 | 2.3 | −0.056 | −0.91 | −0.075 | −0.128 / −0.033 | +0.136 / −0.173 / −0.157 | +0.047 (0.80) |
| long-any-h1030H | 416 | 2.3 | −0.025 | −0.33 | −0.056 | −0.008 / −0.031 | −0.099 / +0.080 / −0.023 | +0.127 (1.81) |
| long-fade-t1s1 | 212 | 1.8 | −0.149 | −2.04 | −0.165 | −0.249 / −0.114 | +0.009 / −0.178 / −0.276 | −0.036 (−0.48) |
| long-fade-h1030H | 212 | 1.8 | −0.143 | −1.60 | −0.174 | −0.130 / −0.147 | −0.274 / +0.120 / −0.159 | +0.030 (0.35) |
| short-any-t1s1 | 439 | 2.7 | +0.031 | 0.49 | +0.014 (best day 56%) | −0.094 / +0.087 | −0.105 / +0.092 / +0.072 | +0.139 (2.35) |
| short-any-h1030H | 439 | 2.7 | −0.031 | −0.43 | −0.058 | −0.129 / +0.014 | +0.037 / −0.083 / −0.033 | +0.126 (1.62) |
| **short-fade-t1s1** | 228 | 1.9 | **+0.068** | 0.87 | +0.048 (best day 31%) | −0.065 / +0.134 | −0.040 / +0.206 / +0.041 | **+0.182 (2.46)** |
| short-fade-h1030H | 228 | 1.9 | −0.045 | −0.50 | −0.069 | −0.200 / +0.031 | +0.033 / −0.030 / −0.108 | +0.116 (1.22) |
| both-fade-h1030H (two-sided, hedged) | 440 | 2.3 | −0.092 | −1.35 | −0.119 | −0.170 / −0.059 | −0.136 / +0.029 / −0.133 | +0.074 (1.08) |

0 pass BAR90, 0 pass the light lane gate (train ≥ −0.02R fails in every config). By SPY vs open at 10:00 (proxy):
short-fade-t1s1 −0.022 above / +0.132 below. The group signal again beats a day-matched random entry (8 of 9 positive,
+0.18R at t 2.46 for short-fade) but the opening cost and the day's direction take it; the hedge does not rescue it.
(The script header printed N 17 / BAR90 2.14 while it ran; the final count is 21 / 2.22 — no verdict changes.) Train /
valid split for COMBO1 = MH4's (≤ 2025-09-30). Backlog `combo1-1103-open-scan-laggard-fade` (parked).

**QD1 — QDAY quiet-day / both-direction** (`qd1.py` → qd1_out.txt, qd1_results.csv). "Quiet so far" (SPY range ≤ 0.6 / 0.8
SPY ATR) × fade the symbol's move from the open ≥ 0.3 / 0.5 ATR, both sides, 10:30-14:30, index ETFs (SPY QQQ IWM DIA) or
top-500 names, t1s1. 8 configs, **all negative** (IDX −0.103..−0.131R, STK −0.076..−0.081R; t −2.1..−6.9). The gate barely
predicts the day type (flagged days end quiet 37% / 35% vs 33% base). Index fades: quiet +0.19..+0.33R, up −0.28..−0.33R,
down −0.16..−0.25R. Backlog `qd1-1103-quiet-so-far-index-fade` (parked): no re-test without an ex-ante quiet-day predictor
≥ 15 points over base.

**Configurations tonight: 21 (L1 1, L2 1, L3 1, L6 1, COMBO1 9, QD1 8); 0 pass.** No locked look spent. About 20
descriptive splits (accounts, sides, loss types, what-ifs, stacking, day types) were looked at as well.

## 5. Decisions
None. Nothing passed; no near-miss clears the lane gate (best: COMBO1 short-fade-t1s1, valid +0.134R t 1.51 but train
−0.065R). Avg R decides: no Live Lab candidate tonight.

Reproduce: `research/ops/coverage1029/fetch.py <scratch>/cov 2026-11-03` → `research/bdi/moves/fetch5.py` (start 10-14) →
`frames_today.py` → `moves.py <scratch> 2026-11-03`; journals via `git show origin/mcf-data*:journal.db`; SIP 1-min bars for
traded symbols (`research/bdi/nightly1103/fetch.py`) → `trades_bdi.py <scratch> 2026-11-03`, `accounts.py <scratch>`,
`swings.py <scratch>`; `python research/bdi/swings/leads_bt.py 21`; `research/bdi/swings/forward.py <scratch> 2026-11-03
--in-sample`; `python research/bdi/1103/combo1.py 21`; `python research/bdi/1103/qd1.py 21`; `add_backlog.py`;
`research/bdi/1028/merge_patterns.py research/bdi/1103/patterns_1103.csv`. Scratch deleted after the run.

Educational only — not financial advice.
