# Nightly learning loop, 2026-10-29 (Thursday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **1 configuration family was replayed
tonight** (15:45 vs 15:55 flatten on all live trades, the same replay as 10-27 / 10-28 with one more session). No
backtest, no locked block, no holdout. No config, setup or exit was changed. About 30 descriptive splits were looked at
(setup, side, hour, exit, poll, lot, twin, cluster / burst size, latency, peak-to-close attribution, NS3-family repeats,
re-arm after −2R, one-big-day per candidate), so some will look strong by chance.*

**Reused, not redone:** Primary's red day is fully analysed in `research/bdi/primary1029/NOTES.md` (−11.3R, short book
on a breadth-up day, stacking WDAY / NTSK, IOVA re-entry; ST-P; 68 configurations, brake proposal). Primary signal
parity is in `research/ops/coverage1029.md` (35 / 35). This note covers the close, coverage and the other four accounts.

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`. The Day 5 message-board post and the job-log
review show P/L **before** costs (Primary −$385.14); after costs it is −$411.08.

**Scripts** = nightly1028's with the date set to 10-29 (`fetch.py`, `build.py`, `close.py`, `polls.py`, `decmin.py`,
`autopsy.py`, `tables.py`, `giveback.py`, `combined.py`, `rearm.py`, `ns3fam.py`, `flat1545.py`), plus `burst.py`
(same-setup same-poll bursts, all accounts since 10-06) and `onebig.py` (one-big-day detail for the candidates and the
monitor marks). `<scratch>` holds each account's journal.db / status.json / reports / intraday from the data branches
and `bars/` (SIP 1-min, 682 symbols). Run as `python <script> <scratch>` (`close.py` / `polls.py` also take the repo path;
`tables.py > tables_out.md`).

**Market: index flat, small caps up then faded.** SPY +0.09% (high +0.25% 11:34, low −0.28% 13:54); QQQ −0.17% (low
−0.69% 09:35, high +0.21% 11:33, −0.51% at 14:00); IWM +0.56% (high +1.00% 11:34). primary1029 classes it an "up"
session for the universe (median stock +0.48%, 68% up).

**Rules effective today:** ST-P (Primary −2R latched per-setup stop) day 1; K4-2 move (CWT12-coil-k4-long now in the
Graveyard, 52 trades there today).

## Failures first

1. **No broken session.** Closed clean in all 5 accounts: phase `closed`, 0 positions, `flatten_failed` [], no partial
   lots, no data outages; journal trades = EOD report rows = `status.today.trades` = job-log "Trades" (16 / 174 / 204 /
   401 / 217); job-log P/L = journal before-cost P/L (P −385.14, T1 276.68, T2 269.90, GY −188.35, Gen −3,709.59);
   "flatten complete: no MCF positions open" in the Gen standby log; EOD report + scorecard 19:57-19:58 UTC (scorecard
   as of 15:57-15:58 ET). Broker positions are not reachable from here (no broker keys); journal = report = status = job
   log is the proxy.
2. **Gen: 8 submitted entries have no trade row (new HK-RECON case).** 225 submitted signals vs 217 trades; the 8 orders
   are still `submitted` in the journal's orders table (all other accounts: submitted = trades). They are the 10:00-10:45
   entries TRV ×2, LITE, EVRG, TMF, USFD (GEN-261023-03 / GEN-261026-05 shorts) and AKAM, EQX (GEN-261020-07 longs). All are
   "hold" / "holdtr" geometries, closed by the 15:55 flatten, whose stop legs answered "order pending cancel" in the
   flatten log, so most likely the reconcile could not pair the flatten close to these lots. The reconcile looks back 7
   days for open orders, so tomorrow's run should book them (as on 10-28 for T2's Z / SLN). **Gen's −$3,927.73 is
   therefore missing up to 8 trades** (the 10:45 burst may be 47, not 45). Housekeeping row HK-RECON-GEN.
3. **Gen lost −$3,927.73 after costs (−$3,709.59 before), its worst day by far** (previous worst −$568 on 10-22). 217
   trades (2.6× 10-28), 21% win, −0.627R. One setup, one poll: **GEN-261020-07 (breadth > 0.7 AM long) took 45 longs at
   10:45, 2 winners, −43.3R, −$1,699** as IWM faded from its 11:34 high. Gen's marked P/L peaked at +$278 (11:34) and
   fell all afternoon (−$1,142 12:31, −$3,169 14:01). Sizing is unchanged (median $1,905 notional / $24.8 risk per lot).
   → backlog `nightly-1029-burst20-one-bet`.
4. **Handover #169 → standby #175 (~14:35-14:39 ET) was clean this time: no gap > 5 min, no decision minute missed.**
   #169 (workflow_dispatch, 08:52 ET) hit the 6-h limit; its jobs ended 14:36:51-14:38:50 ET; #175's jobs started
   14:36:54-14:38:52 and checkout took ~5 s (10-28: 42-78 s). Trade steps began 14:37:33 (T1), 14:38:40 (GY), 14:38:41
   (T2), 14:39:00 (P), 14:39:29 (Gen). Poll gaps: Primary 1.8 min (14:37:16 → 14:39:02), T1 2.4, T2 3.5, GY 3.5, **Gen 4.3**
   (14:35:14 → 14:39:32). The residual is the old job: it stopped polling ~1.5-3.5 min before its job ended. OPS-HANDOVER
   stays open on that part only.
5. **Poll coverage still under 90% in the 3 slow accounts** (of 384 1-min polls 09:30-15:54): Primary 384, T1 384,
   **T2 316 (82%), GY 310 (81%), Gen 264 (69%)** (10-28: 268 / 315 / 227). Every 5-minute decision minute (77/77) was
   polled in all 5; the slow accounts skip bucket minutes 1-2 (Gen exp%5 = 1 / 2 only 14 / 27 times), which only
   non-lab setups use (OPS-POLL).
6. **Broker rejects 8, crosscheck 0, "missed: triggered" 0** (all journaled as signal reasons): Graveyard 5 take-profit
   already through the base price + 2 "insufficient buying power"; Testing 2 1 stop_loss on the wrong side of the base
   price (H-1 / HK-1). No quote errors.

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`, `decmin_out.txt`)

| account | polls | % of 384 | decision minutes | longest gap | handover gap | trades (journal = report = status = log) |
|---|---|---|---|---|---|---|
| Primary | 384 | 100% | 77 / 77 | 1.8 min (handover) | 1.8 min | 16 |
| Testing 1 | 384 | 100% | 77 / 77 | 2.4 min (handover) | 2.4 min | 174 |
| Testing 2 | 316 | **82%** | 77 / 77 | 3.5 min (handover) | 3.5 min | 204 |
| Graveyard | 310 | **81%** | 77 / 77 | 3.5 min (handover) | 3.5 min | 401 |
| Gen | 264 | **69%** | 77 / 77 | 4.3 min (handover) | 4.3 min | 217 (+8 submitted, not booked) |

## 1. Headline per account (real trades)

| account | trades | win% | avgR (costs) | **P/L after costs** (before) | stop / target / flatten | marked peak → close |
|---|---|---|---|---|---|---|
| Primary | 16 | 25% | −0.706 | **−$411.08** (−$385.14) | 12 / 4 / 0 | +$20 (13:21) → −$411 (see primary1029) |
| Testing 1 | 174 | 56% | −0.001 | **+$250.12** (+$276.68) | 56 / 94 / 22 | trough −$140 (12:00) → peak +$475 (13:53) → +$250 |
| Testing 2 | 204 | 67% | +0.034 | **+$245.96** (+$269.90) | 62 / 126 / 16 | trough −$276 (10:50) → peak +$285 (15:26) → +$246 |
| Graveyard | 401 | 61% | −0.047 | **−$300.63** (−$188.35) | 119 / 219 / 63 | +$124 (10:53) → trough −$679 (12:01) → −$301 |
| Gen | 217 | 21% | −0.627 | **−$3,927.73** (−$3,709.59) | 138 / 16 / 63 | +$278 (11:34) → −$3,928 |

Total after costs **−$4,143.36** (Gen 95% of it). By side (R / $): T1 shorts +9.5R / +$375, longs −9.7R / −$124; T2 shorts
+5.2R / +$255, longs +1.8R / −$9; GY shorts −12.5R / −$205, longs −6.4R / −$96; **Gen longs −95.0R / −$3,344**, shorts
−41.0R / −$584; Primary shorts −9.8R / −$353. Unlike Primary, the Testing shorts made money on the same session.

**Primary live-funds hold: closed RED.** −$411.08 after costs (−$385.14 before) → positive-day streak **reset to 0**
(it was 3: 10-26, 10-27, 10-28). Since Day 1 (10-23): 3 of 5 sessions positive, **−$135.86** after costs (−$79.78
before). Since start: 6 of 18 positive, −$1,157.22. M2 (8 of the last 10 green): 4 of 10. Nothing changes; lifting the
hold is the owner's call.

### 1a. Intraday peak vs close (`giveback_out.txt`)
- **Testing 1:** −$140 at 12:00 → +$475 at 13:53 → +$250. L3-gap-slope-fromopen-FD did it: 38 trades, 71% win, +0.39R,
  +$360.75 (an 11-entry short burst at 11:35 +7.4R); exhaustion_short / -FD +$66. Peak → close −$225: 27 entries after
  the peak −$116, 22 late flattens −$115.
- **Testing 2:** −$276 at 10:50 → +$285 at 15:26 → +$246. exhaustion_short-FD 15 trades 87% win +$119.19,
  L3-gap-slope-rsi5hi-FD 15 trades 93% win +$115.85, NM-AR-AM-gapdown-capitulation-long 8 trades +$40.51.
- **Graveyard:** +$124 at 10:53 → −$679 at 12:01 → −$301. CWT09-gapdn-bounce-g5-lowerhalf-short −$115 (−$326 marked
  peak → close), CWT12-coil-k4-long −$111 (52 trades, first Graveyard day), CWT14-orl-p10-long −$107; the −2R latch and
  the per-setup cap blocked 134 + 108 signals worth −21.4R / −31.5R (what-if).
- **Gen:** see failure 3. Worst setups: GEN-261020-07 −$1,720.86 (46 trades, 4% win), GEN-261027-10 (FlowShift LUNCH
  long) −$678.49 (18, 11%), GEN-261027-05 (VolRatio MID long) −$362.55 (14), GEN-261022-07 (Z12 AM short) −$186.10. 24 of
  83 Gen setups traded; 1 of 24 positive (GEN-261023-04 +$2.54).

## 2. Winner / loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE / MAE for all 1,012 trades)

- **Losers "never worked" again:** 248 losers never reached +0.2R (P 3 / T1 38 / T2 30 / GY 88 / Gen 89), −$4,180
  together; losers' median MFE 0.16-0.23R in the four non-Primary accounts. Winners peak late (median 38-81 min),
  losers early (6-15 min); winners give back little (median 0.06-0.09R, Gen 0.18R).
- **Bursts are one bet** (`burst_out.txt`, all accounts 10-06..10-29): same-setup same-poll entries of 20+ average
  Gen −0.963R (45), Graveyard −0.311R (116), Testing 2 −0.416R (257), Testing 1 −0.079R (183), against −0.058..−0.122R for
  single entries. All bursts of ≥ 10: 108 bursts, 1,694 trades, −0.211R, −357.7R; 40 bursts positive; the best burst is 8%
  of the positive R; without 10-29 −0.204R. Three cluster caps already failed on two years (sat1024 3/5 per bar on RW,
  nightly-1026 coil ≥ 10, nightly-1015 short clusters), so the new item pools all lab setups at a rare threshold (20+)
  and must beat a uniform size cut. → backlog `nightly-1029-burst20-one-bet` (risk).
- **NS3 family** (`ns3fam_out.txt`): +1.9R today (T1 RW4-FD 2 / 2 +$23.49; T2 NS3-FD no trade). Since 10-06: 280 family
  shorts, 35% win, −0.230R, −$1,902. The 10-28 item (`nightly-1028-ns3-family-one-bet`) stands; nothing new.
- **Testing accounts after −2R** (`rearm_out.txt`; per-setup stop off there since 10-23): 10 setup-days kept trading
  after −2R today, 33 entries −10.3R; since 10-20 56 events, 360 entries, −78.6R.
- **15:45 flatten** (`flat1545_out.txt`, 1,926 lots since 10-06): +48.9R vs the 15:55 flatten, 14 of 18 days better,
  t_day 1.66; **today +20.9R is 43% of the gain** (longs +23.5R, shorts +25.4R overall). Already in the backlog
  (nightly-1027-flatten-1545); no new item.
- **Checked, no new pattern:** twins (T2 52 twin entries, no order), latency terciles, lot number, refires (T1 29).

## 3. Backlog (1 new, status idea)
- `nightly-1029-burst20-one-bet` (risk; any lab setup firing on ≥ 20 symbols in one poll = one index bet: first N or a
  shared 5-10R; related failures listed in the item).
No swarm tonight: 1 new idea (< 3) and no setup is near a gate (bar90_1029: 0 candidates clear BAR90 under live
conditions).

## 4. Suggestions (`combined_out.txt`, `onebig_out.txt`; all accounts merged, 18 sessions, costs in; yardstick research/ops/primary_bar.md)

- **DECISION BRAKE-1 (from primary1029, owner pending):** Primary short-family brake: after 3 RW3-FD / RW5-FD / MF2-FD /
  MF4 / MF4-FD stops in a day, new family lots at half size. Live replay 10-29 −11.3R → −8.5R, record +84.0R → +85.8R;
  2-year vs an equal uniform size cut train t −0.36 / valid t +2.0, sibling failed the locked block, the other 4 accounts
  show no persistence. **Recommendation: no, run it as a shadow line for 20 sessions.** Reply "BRAKE-1 yes" / "BRAKE-1
  no". Added open to docs/live/decisions.json.
- **No promotion is ready.** Closest: Gap-Down Recovery Fade (all day) (`L3-gap-slope-fromopen-FD`, Testing 1) 245
  trades / 13 sessions, 61.2% win vs 49.0% needed, +0.174R, **w/o best day +0.055R (10-20 = 79%, `1 day`)**, **w/o its
  best two days (10-20, 10-29) −0.045R**, t_day 1.04, last 4 +0.250R, +$938.40, 2-year −0.017R (swarm15_1029). It now
  passes every Primary-bar line except that two big days carry it; Friday review (10-30), no decision tonight.
  `L3-gap-slope-rsi5hi-FD` (T2) 76 trades +0.173R, w/o best day +0.089R (61%, 1 day), w/o best two −0.014R.
- **Demotion watch unchanged** (WATCH-NS3, MF3-FD / MF5-FD) for Friday; nothing new tonight. Gen setups are not on the
  promotion path, but GEN-261020-07 is now 64 trades / 3 sessions, 15.6% win vs 38.0% needed, −0.587R, −$1,199 (FYI).

### 4a. Monitor marks (docs/live/monitor.json)
- **CWT14-failbrk-pdl-p05-long** (Testing 1; owner demo mark 10-29 → Graveyard): today 57 trades −10.25R, −$99.47.
  Record 675 / 14, 61.9% vs 66.3% needed, −0.085R, w/o best day −0.117R. Full evaluation by the 17:20 ET task.
- **CWT14-failbrk-pdl-p05-lowvol-long** (Testing 2; demo mark 10-29): today 49 trades −4.71R, −$61.70. Record 433 / 14,
  60.3% vs 66.8%, −0.115R, w/o best day −0.142R. 17:20 ET task.
- **CWT14-failbrk-pdl-p10-long** (Testing 2; demo mark 10-29): today 35 trades +1.22R, −$10.67. Record 384 / 14, 66.1% vs
  65.8%, −0.023R, w/o best day −0.069R. 17:20 ET task.
- **Afternoon VWAP Reclaim Fade (all day)** (`NS4-pm-vwap-reclaim-oversold-short-FD`, Testing 1 → Primary, promo mark
  10-27): today 6 trades −0.66R (+$18.72); since the mark 7 trades −1.71R. Record 25 / 9, 56% vs 43% needed, +0.236R, w/o
  best day +0.063R (10-22, 79%, **1 day**), w/o best two −0.046R. **Lean: wait.**
- **Generated NewLOD, Flow3lem0p37 LUNCH short** (`GEN-261026-03-...-holdtr-short`, Gen → Testing 1, promo mark 10-27):
  today 1 trade −1.12R (−$11.22). Record 12 / 3 sessions, 58% vs 33% needed, +0.509R, **w/o best day −0.009R** (10-27,
  101%, **1 day**). **Lean: wait.**

### 4b. Watch: CWT14-failbrk-pdl-p10-lowvol-long (Primary → Testing 2 from 10-28)
Since the move: 2 sessions, 38 trades, 61% win, −4.63R (−0.122R), −$41.10 (today 31 trades −0.58R, −$19.12). Record 210 /
14, 68.1% vs 66.6% needed, +0.002R, w/o best day −0.027R (10-20, **1 day**), 2-year −0.095R.

## 5. ST-P day 1 (from primary1029, not re-run)
ST-P fired twice: RW5-FD at 13:59 (−2.27R) and MF4-FD at 14:30 (−2.86R). It blocked 4 entries (SPG MF4 −1.10R, FUTU RW5
−1.06R, JETS MF4 +0.26R, UNP MF4 −0.51R), saving about 2.41R (~$60): the day was −11.3R instead of about −13.7R. Both
latches tripped after most of the damage (NTSK's RW5 lot was entered before RW5's latch). On two years ST-P is the one
tested rule with real value. No decision item.

Educational only — not financial advice.
