Educational only — not financial advice

# Giveback investigation 2026-11-19: keeping gains after a spike

## Owner summary
1. Gains come back in three places: setups with far targets (2:1 / 2.5:1 targets that sit 1.2R+ from the fill), GEN "hold" setups with no target, and a book that leans one way when the market turns (11-19: Primary +8.7R at 11:40 to -19.6R at 13:40).
2. We tested 3,836 exit and lock rules across 5 groups on 2 years (1.1 million trades, costs in), checked live, and an independent skeptic re-scored the best one. **0 passed.** Time cuts, breakeven moves, trails, partial profits, closer targets, clock exits, SPY-turn exits and day-level profit locks all lost R on the check half.
3. Why: nothing in a trade's own price path says "get out now". Before costs a fading trade is a coin flip, and each early exit costs extra. On far-target setups the trades that reach 2R pay for the ones that turn around. Taking profit early lost 950-1,600R on exactly those setups.
4. The "flatten at +5R, 30% giveback" lock would have saved 11-19 (+19.9R). It would also have cost 40.8R on 11-12 and 24.0R on 11-16. Its gains, and those of the "block new entries" lock, come from trading less, not from the lock: a same-time control did as well.
5. Proposals: **GB-NOEXIT yes** (no new exit or lock rule), **GB-NOLOCK yes** (no day-level profit lock, Primary included), **GB-GENTRAIL yes** (research only: trail for GEN hold setups, the one untested pocket), **GB-BRAKE optional** (research only: exposure brake, scored against a control), **GB-BLPARK yes** (park 2 backlog exit ideas these tests cover), **GB-READ optional** (reporting wording). Nothing is applied until you reply.

## Scope and method
- **Live:** run 1 of all 10 journals, 10-06..11-19 (33 sessions), 28,097 de-duplicated trades, avg -0.151R on the LR8 cost basis. Minute paths come from read-only Alpaca 1-minute bars; bar MFE matches the journal's mfe_r (corr 0.95). Live results are descriptive only.
- **Lab:** bt_lab1104 first signals, 95 setups / 36 family-sides, 446 sessions, 1,106,391 trades. Fit = sessions up to 2025-09-30 (170), check = after (276), and the check half was scored once per stage. The locked block 2024-11-01..2025-02-28 was filtered at read and asserted absent in every stage.
- **Costs:** bt_all costs (lab) and LR8 (live), plus $0.01/share plus 1 bp extra on every rule-driven early exit.
- **Method:** WB2, meaning paired scoring on the parent's own signals, pooled by mechanism family. Each stage pre-registered PLAN.md before scoring and reports per-setup and per-family better/worse counts and sizes, plus avg R without the best day.
- **Configs counted:** time_in_trade 2,664, day_lock 16, outside_methods 814, targets 222, setup_level 120 = **3,836 scored configs**. With the map's 916 cells and setup_level's 520 descriptive cells the lineage N is **5,272**, so the multiple-testing bar is t >= 4.14.

| Stage | Folder | Verdict | Check-half headline |
|---|---|---|---|
| Map | map/ | descriptive | 0 of 916 "exit now" cells in both halves; 31 favour holding |
| Time-in-trade (A "never worked", B "worked then faded") | time_in_trade/ | FAIL | adopted RW1/RW3 short: -117.4R, t -1.58; book-wide A -126R, B -400R |
| Day-level profit lock (16 configs) | day_lock/ | FAIL | best A1 block +408R, t 2.60, but excess over the same-time control +139R (t 0.99), and -160R on fit |
| Outside methods (chandelier, scale-out, SPY turn, clock exit) | outside_methods/ | FAIL | adopted O3 +4.4R, t 0.03 (one day = 984% of the gain); book-wide O1-O4 -238 to -481R |
| Targets (partials, caps, no target) | targets/ | FAIL | 0 of 36 adopted; every book-wide config loses (-1,136 to -16,007R) |
| Setup-level entry fixes (crowd minute, late entry, refires) | setup_level/ | FAIL | 0 of 84 fit cells reach excess t +2 vs random removal |
| Skeptic (independent re-score) | (scratchpad) | all 5 FAILs stand | no look-ahead, no tuning on check; A1 re-score matched exactly |

## Where gains are given back, and why
1. **Not in "stalled" trades.** At every checkpoint from 5 to 120 minutes, holding beat exiting.
   - Even trades that reached +0.5R and fell back to entry are worth +0.03 to +0.22R more held than cut.
   - Most of that hold advantage is the cost of exiting (0.04-0.06 stop units). Before costs, the price is a coin flip from any state.
   - This matches L16 near-target breakeven (-0.007R/trade, 1 of 35 families better), the book-wide breakeven (kept off), W5 X1-X3 and the Wave 2 trail.
2. **Far targets (pocket 1): real, but it is the price of the 2:1 payoff.**
   - Of trades that touch +0.8R, about 5% end at a full stop on t1s1 setups and 28% on t1s05 setups. Live trades with targets more than 1.2R from the fill: 3,100 trades, -0.293R, 993R given back after +0.8R.
   - The setups with the biggest giveback are the same in lab and live: CWT09-gapdn-vwaploss-g5-short, MF1-945-flowsell-vwapup-FD, MF2-open-rsimidhi-flowsell-FD, CWT12-coil-k6-long.
   - Closer targets lose on exactly these four:

     | Setup | CAP 1.0R | Half off at +0.8R |
     |---|---|---|
     | CWT09-g5 | -187R | -118R |
     | MF1-945 | -561R | -319R |
     | MF2-open | -197R | -110R |
     | CWT12-k6 | -178R | -106R |

     Scale-out at +1D lost -92R (runner on the original stop) and -153R (runner at breakeven).
   - The 11-19 Primary targets (1.0-1.6R from the fill) belong to this geometry. Target-from-fill was parked in Wave 2 (Y3 +0.026R, t 1.58, later half negative), and live fill targets already sit closer than the signal ratio because slippage is mostly adverse.
3. **GEN hold setups (pocket 2): untested.**
   - Live: 3,406 trades, -0.231R; 25% of +0.8R trades end at a stop; 538R given back.
   - The lab has no GEN hold lists, so no 2-year test exists either way. This is the only open exit pocket.
4. **Market turns against a one-sided book: real, but mostly hindsight.**
   - Of the 83 account-days that peaked at +5R or more, 58% closed red; Primary had 15 such days, 7 red.
   - On the 70 big-giveback days: lots open at the peak gave back -1,268R (majority-side lots -1,029R), and entries after the peak gave back -933R (vs -881R at the accounts' normal rate).
   - Skeptic base rate: at random minutes the median majority side is already 77% of open lots (n 787), vs 83% at the peaks. Books are one-sided most of the time, not specially on giveback days.
   - "SPY against" (a stop after +0.8R happens 30% of the time when SPY moved against the trade vs 6% with it) is known only afterwards. As a real-time exit (O3, SPY turn) it failed: book-wide -238R, 9 families better / 18 worse.
5. **Not entry timing in the big setups.**
   - CWT14 and CWT12 give little back: only 6-12% of their trades reach +0.8R. They lose because they have no edge at the 0.5R target.
   - RW3 and RW5 crowd-minute entries are their best live trades.

## What works to keep gains (skeptic-upheld)
- **No exit or lock rule tested here keeps gains net of costs.** The skeptic upheld no positive result.
- Holding to the setup's own stop and target is the best of everything tested, and it gives every setup its full room to breathe.
- The day lock that did not cut runners (A1, +10R on 28 check-half days that kept running up) still has no edge beyond trading less late in the day: blocking all late entries does as well, and the excess over the control is negative in both halves.

## What does not work (do not re-propose without a new mechanism)

| Class | Best check result | Families / setups effect |
|---|---|---|
| Time cut "never worked" (A) / "faded" (B) | adopted -117.4R; book-wide A -126R (t -0.62), B -400R (t -2.35) | RW1 short -125.0R, RW3 short +7.6R; fit-bests applied anyway: 9 better (+138R) / 26 worse (-1,527R); RW7 below-entry cut -346R |
| Day lock: tighten (A2) / half off (A3) | A2 -64 to -103R; A3 -85 to -129R | sign flips from fit |
| Day lock: block (A1) / flatten (A4) | A1 +408R, but excess +139R (t 0.99), and -160R on fit; A4 excess -288R | A1: 27 families better (+466R) / 11 worse (-58R); gain is 85% Graveyard + Gen; Primary +13R |
| Chandelier ATR trail (O1) | -379R, t -4.9 | 0 better / 8 worse |
| Scale-out half at +0.5/+1.0D (O2) | -270R, t -3.5 | 1 / 4 |
| SPY-turn exit (O3) | -238R, t -2.5 | 9 / 18 |
| Clock exit 12-15h (O4) | -481R, t -2.3; flatten at 12:00 -8,753R on fit | 6 / 21; gap-down fades +536R fit becomes -3,138R check |
| Partials at +0.6/+0.8 | -4,247 / -3,527R, t -8.8 / -12.8 | 0 better / 27 worse |
| Target caps 1.0R / 1.5R | -1,623 / -1,136R | 0 / 8 |
| No target (EOD or 120 min) | -13,864 / -16,007R | 6 / 30 and 4 / 32 |
| Entry: crowd minute / late entry / refires | summed excess -26 to -1,509R | 0 of 84 cells at excess t +2 |

**One-big-day check.** The only gains were O3's +4.4R (best day 984% of the gain) and A1's +408R (best day 28%, but it fails the control). Every other result is negative.

## Proposals (ranked; nothing applied)

| Rank | Code | Recommend | What | Effect per setup | Conflicts with standing rules | Next step |
|---|---|---|---|---|---|---|
| 1 | **GB-NOEXIT** | Yes | Add no new trade-path exit (time cut, breakeven, trail, partial, target cap, clock or SPY-turn exit) in any account; record the 3,836 configs as tested and failed | none (no change); avoids losses like RW1 short -125R and MF1-945 -561R | none: keeps "setups need room to breathe"; leaves the -2R latch (kept 11-17) and the WB2 hold (11-18) untouched | none; finding line added to the backlog (gb-1119-exit-lineage-finding) |
| 2 | **GB-NOLOCK** | Yes | No day-level profit lock (block, tighten, half off or flatten after a +5R/+8R peak), Primary included, despite the 11-19 hindsight figure | none; the 11-19 flatten +19.9R is offset by 11-12 -40.8R and 11-16 -24.0R | overlaps the Primary -2R latch (10-29, kept 11-17) and R2 (no new daily stop, 10-22) | none |
| 3 | **GB-GENTRAIL** | Yes (research only) | Score a 1R target and a 1R-activated trail (giveback 50%) on GEN hold setups in the generator's own lab, on hold lists rebuilt for 2 years: 2 configs, WB2 paired, per-setup better/worse, costs in | target: GEN hold setups (live 3,406 trades, -0.231R, 538R given back after +0.8R); no live change; prior is against (every trail tested so far lost) | 10-19: no GEN setup changes without your consent (research only); PKT-FX / FOOTRACE-EXIT moves 7 GEN arena setups to the Graveyard; WB2 hold; any adoption = new copies (11-18) | research; if it passes, a 15-session journal-only shadow in Gen, then a decision outside market hours |
| 4 | **GB-BRAKE** | Optional (research only) | Test an exposure brake / net-beta cap (swing1103-L4) scored against a same-clock control on days without the trigger and against the 77% one-side base rate: <= 3 configs | target: majority-side lots on reversal days (-1,029R on 70 days); live trades blocked would be mostly late same-side entries | R2 "no new daily stop" (10-22); prior 0 of 44 (R2), 0 of 6 (sat1024 brake), 0 of 74 (REGSW), A1 control fail; -2R latch kept 11-17; Testing 1 sizing first; Primary only in the Friday epoch window; replay2y is only 79% calibrated (needs a calibrated book harness first) | research; if it passes, a journal-only would-block shadow for 15 sessions; Primary only at a Friday epoch window with your yes |
| 5 | **GB-BLPARK** | Yes | Park backlog exits xa-1105-hwm-giveback-exit (covered by the O1 chandelier, Wave 2 trail-after-1R and L16) and nightly-1014-fd-short-late-giveback (covered by O4 clock exits, 14:00/15:00 winners-only -481R) with this evidence; both return at the biweekly parked review | none (backlog only) | PARK1 (parked, not failed) | backlog status edit on your yes |
| 6 | **GB-READ** | Optional | Reporting wording: show "stopped after +0.8R" as the cost of the 2:1 payoff (next to the 2R-hit share), and add the base rate plus a "peak picked in hindsight" note to nightly peak-to-close FYIs | none (display only) | rule-change context (11-02) already applies | nightly brief template |

## FYI (no decision)
- **L3 afternoon.** In the lab, L3 entries at 13:30 or later average +0.173R (n 6,316), which runs against the live / W4 "L3 afternoon loses" lead. Do not act on that lead without more evidence.
- **ST7-FD** is the only top setup with a far-target-style giveback (27% of +0.8R trades end at a stop, n 58). ST7 is already with you (ST7-A / ST7-B).
- **Live replay of no target to the close** shows +493R over 33 days, but the lab rejects it (-13,864R; 6 better / 30 worse). It is market drift, not evidence.

## Rule / config changes inside the live window (research/ledger.jsonl)
Live figures above span these rule regimes and mix them:
- **10-16/17:** Testing 2 CWT14 scale-out, plus 4 more setups.
- **10-23:** per-setup latch; Testing setup stop off.
- **10-26:** Gen caps raised (GX2).
- **10-28:** Primary sizing changed twice.
- **10-29:** Primary -2R latch.
- **10-30:** Testing cost filter.
- **11-12:** LR1 / LR3 / LR8, plus Gen / Graveyard sizing (REPV).
- **11-17:** TSZ1 sizing; SPYEXIT engine and WB4 copies.
- **11-19:** C3 Epoch 1 (EXIT100, ROT, WB5, U9-TGT, U9-ETB, TAGS1).
- **After the window:** 11-20 broker stop rounding and FOOTRACE-EXIT.

## Caveats
- Live has 33 sessions, so it is descriptive only.
- The lab is first-signal-per-day and has no GEN hold lists.
- Exits fill at the decision bar's close. That biases slightly in favour of the rules, and they still lost.
- day_lock does not model freed slots or buying power being used by other entries.
- The skeptic did not audit the targets / outside_methods code line by line.

Files:
- Stage reports: map/, time_in_trade/, day_lock/, outside_methods/, targets/, setup_level/ (each has PLAN.md, RESULTS.md and code).
- Decisions: research/owner_inbox/2026-11-20.md and docs/live/decisions.json.

Educational only — not financial advice.
