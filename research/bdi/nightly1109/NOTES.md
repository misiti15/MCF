# Nightly learning loop, 2026-11-09 (Monday): 7 accounts (Primary, Testing 1, Testing 2, Graveyard, Gen, Explore 1, Live Lab)

*Educational only — not financial advice. These are live **paper** results from one session plus the record since start. They
describe what happened; they are not evidence that anything works. **Configurations tried tonight: 4** (MF1109, 2-year lab
lists, pre-registered in `mf1109.py`; the locked block was not read). About 25 descriptive splits were looked at, so some
will look strong by chance.*

**Costs are in.** R = journal `pnl_adj / $ risk`. Dollars are Alpaca where stated. What-ifs for latch-blocked signals use
SIP 1-minute bars and are **before costs**.

**Rule changes inside the windows quoted** (research/ledger.jsonl):
- Primary: MF2-FD / MF4-FD promoted 10-20, ST7-FD 10-26, ~$4,000 lot 10-28, −2R per-setup stop 10-29, L3 pair 10-30.
- All accounts: GX1 10-27; UNI1 (T2) 11-04; ROLL1 (Explore 1 / Live Lab) 11-05.
- **11-09: EXPO1109 temporary moves.** GEN-261021-02 / GEN-261019-03 / GEN-261026-02 moved Gen → Testing 1, and
  GEN-261022-07 / GEN-261026-03 moved Gen → Testing 2. They revert after the 11-10 close, so Testing totals include GEN
  results for 11-09 and 11-10.
- Live Market Compass recording started 11-09 (display only).
- No Primary setup or exit rule changed on 11-09.

**Ops.** GitHub's scheduler missed again: the session guard dispatched trade at 08:50 ET (run 42629015419) and
hunch/compass at 09:49. Trade self-handed-over at 14:39 to run 42684037967, and the latches were restored.

**Market: trend-up day.** SPY was +0.74% at 10:00, +1.26% at 11:00, high +1.82% at 15:15 and closed +1.44%. QQQ closed
+2.43% (high +3.0%) and IWM +1.81%. The live compass was UP-confirmed at 10:00 (W60) and at 10:30 (30-min), and GATE1 was UP
at every checkpoint from 11:00 to 15:00.

## Failures first
1. **The EOD report, scorecard and P/L reconcile had not run at 16:48 ET** in any of the 7 accounts.
   - The closing trade run was dispatched by `github-actions[bot]`, and GitHub does not fire `workflow_run` events for
     GITHUB_TOKEN runs. The 16:25 backup cron was missed as well.
   - I dispatched `eod.yml` (day 2026-11-09) at 21:49 UTC and all 7 jobs succeeded. Reports, scorecards and
     `pl_reconcile/2026-11-09.json` landed 21:49–21:50 UTC.
   - Housekeeping row HK-EOD-CHAIN is open.
2. **Testing 1 carries a short that MCF did not place** (DECISION T1X).
   - Cash minus equity was $1,629.48 at the 11-06 close and $1,761.60 at the 11-09 close. It was $0 at the 11-05 15:55 status.
   - The position is not in the journal, so the flatten never closes it.
   - 11-05 Alpaca −$1,526.68 vs journal +$58.05 (likely the same corporate-action booking as Primary's MTUM).
   - 11-09 Alpaca −$126.46 (reconcile) vs journal +$0.41.
   - The Testing 1 keys only exist in Actions. The read-only `account-check` run 21:52 shows equity $95,488.12, still moving
     after hours.
3. **Team final row missing from the scoreboard** (HK-TEAM-SB).
   - `team/2026-11-09.json` is closed (+2.54R), but `research/shadow_primary/scoreboard.csv` had no `closed` row.
   - I appended it from the stored report. The mcf-data-team branch still lacks it.
4. **Broken merge in docs/live/decisions.json on this branch.** Conflict markers from 3dfb1db6a had been committed, which made
   the file invalid JSON. Resolved as the union (DM-MF2 … RISK1 plus COMP-LIVE). Base `claude/intraday-trading-system-witis4`
   was fine.
5. **Buying-power rejects:** Gen 437 and Graveyard 173 (HK-GEN-BP). These entries are not in the record.

## 1. Session close (all 7 clean)
- Phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data outages.
- Job log "flatten complete: no MCF positions open" in all 7.
- journal = submitted = status = job-log "Trades": 36 / 65 / 53 / 512 / 293 / 4 / 3 (P / T1 / T2 / GY / Gen / Ex1 / LL).
- Final pushes "job 14:36–14:39 done" (20:55–20:58 UTC).
- Primary broker (read-only GET): 0 positions, 0 open orders, equity $81,638.08 (last equity $81,810.34).
- The other accounts' state shows cash = equity except Testing 1 (failure 2).

## 1b. Coverage (`polls.py`, `polls_out.txt`)

| account | polls | % of Primary | first / last | longest gap |
|---|---|---|---|---|
| Primary | 384 | 100% | 09:30:01 / 15:54 | 1.8 min |
| Testing 2 | 384 | 100% | 09:30:01 / 15:54 | 2.3 |
| Testing 1 | 349 | 90.9% | 09:30:01 / 15:54 | 3.0 |
| Live Lab | 315 | 82.0% | 09:30:01 / 15:54 | 3.5 |
| Explore 1 | 300 | 78.1% | 09:30:01 / 15:54 | 3.3 |
| Graveyard | 257 | 66.9% | 09:30:01 / 15:54 | 4.1 |
| Gen | 243 | 63.3% | 09:30:01 / 15:54 | 4.9 (14:45) |

- No gap is over 5 min.
- The 08:50 dispatch still polled from 09:30:01, and the 14:34–14:36 hand-over cost at most 4.1 min.
- Skips:
  - Primary: 163 ETB, 28 setup daily loss limit, 17 twin held, 11 spread.
  - T1: 113 split-tape short gate, 4 "missed: triggered".

## 2. Autopsy (`autopsy_out.txt`, `giveback_out.txt`)

| account | trades | win% | sum R (costs) | journal $ after costs | Alpaca (close-to-close) |
|---|---|---|---|---|---|
| Primary | 36 | 31% | **−18.10R** | −$197.36 | −$175.87 (−$172.26 vs last_equity) |
| Testing 1 | 65 | 57% | −1.69R | −$6.99 | −$136.93 (T1X position) |
| Testing 2 | 53 | 60% | −5.07R | −$69.30 | −$66.96 |
| Graveyard | 512 | 54% | −76.41R | −$653.05 | −$549.75 |
| Gen | 293 | 40% | −57.36R | −$1,137.94 | −$1,050.14 |
| Explore 1 | 4 | 75% | +0.60R | −$13.14 | low-rep home |
| Live Lab | 3 | 100% | +1.40R | +$47.11 | low-rep home |

**Primary: 35 shorts −18.58R, 1 long +0.47R.** Marked peak +$16 at 10:06, trough −$662 at 10:59, close −$197.

**MF4-FD (Early Sellers, Strong Heat (all day)): 17 shorts, −17.09R / −$203.23, 16 stopped.**
- Entries 10:20–10:51, all after the compass was UP-confirmed at 10:00.
- 12 of the 17 were broad or factor ETFs: AVLV, JEPI, QUAL, SPYV, IWN, FNDX, DIA, IWD, IWS, VTV, SPYM, AVUV.
- The rest were CNI, PNC, BAC and FNDE, plus MAGS (the one target).
- MFE was 0.0–0.4R and the stops hit 10:51–12:46. The tape kept rising, so this was one index short taken 17 times.

**L3-fromopen-FD (Gap-Down Slope From Open):**
- 10 trades −1.30R, but −$137 because COIN / USD carry about $100 per R.
- The 10:05 USD / COIN shorts stopped; the later COIN / BMNR lots won.
- It drove the 10:59 marked trough (−$487 open).

**Others:**
- MF2-FD 1 trade −1.20R.
- RW3-FD 2 trades +0.97R; RW5-FD 4 trades −0.44R (+$64); L3-rsi5hi +0.48R; NS1 +0.47R.

**Same failure family as 11-05 / 11-06 (MF shorts in a burst):**
- 11-05 / 11-06: the bursts came after the selling was already done.
- 11-09: the shorts went against a confirmed up tape with no flush at all.
- Cluster of ≥ 5 per poll: 12 trades, 0% win, −1.09R avg.

**Other accounts:**
- **Graveyard:** shorts −136.0R (n 256) vs longs +59.5R. heat_fade_short-FD −19.3R, MF3-FD −18.8R, MF5-FD −16.6R,
  RW2-FD −14.9R; CWT12 coil longs +27.1R.
- **Gen:** shorts −63.2R vs longs +5.9R.
  - GEN-261029-08 (SPYgt0p5, RSI ≥ 65) 50 shorts −38.9R; GEN-261022-08 28 shorts −18.1R.
  - GEN-261020-07 27 longs +9.2R / +$397.87 (best setup of the day).
- **Testing 1:** NS1-FD 22 trades +3.56R. The moved GEN-261021-02 had 29 longs −3.64R (22 entered at 09:50).
- **Testing 2:** NS4 −4.97R, NM-AR capitulation −4.23R, CWT14 pdl p10 +3.77R.

**Counter-index entries lost today** (L6 shadow): 430 trades at −0.516R vs +0.122R for the other entries. This is the
opposite of 11-06.

## 3. Backlog (+3, status idea; `add_backlog.py`)
- `nightly-1109-mf-short-broad-etf-skip`
- `nightly-1109-mf-short-upconfirmed-gate`
- `nightly-1109-gen-index-gated-short-trend-day`

L6 got the 11-09 evidence added.

## 4. MF1109 two-year screen (`mf1109.py`, `mf1109_out.txt`; 4 configs, 0 pass)
- **Data:** MF shorts in bt_lab1104, 45,744 trades over 6 setups. Base avg R is −0.127 (TRAIN) and −0.066 (VALID).
- **Bar:** day-clustered t ≥ 2.64 on VALID (MF lineage 33 looks).

| config | TRAIN Δ (t) | VALID Δ (t) | setups better / worse (VALID) | lab rows after 10-05 | result |
|---|---|---|---|---|---|
| A skip unleveraged ETFs | +1,043R (4.49) | +398R (1.80) | 6 / 0 | +20R | fail |
| A2 skip all ETFs | +1,080R (4.37) | +453R (1.88) | 5 / 1 | +7R | fail |
| B UP-confirmed proxy, 60-min persistence | +585R (2.26) | +420R (2.51) | 6 / 0 | **−123R (t −1.46)** | fail (near miss) |
| B2 UP-confirmed proxy, no persistence | +774R (2.21) | +496R (2.56) | 6 / 0 | −107R | fail |

- In every config the kept trades still average below zero (VALID −0.054..−0.062R). The filters remove bad trades but do not
  make the MF short family positive. That supports DM-MF4 / PV1 rather than a fix.
- The UP-confirmed gate would have removed all 17 MF4 shorts today (+17.1R), but it lost on the October lab rows.
- No DECISION; both ideas are in the backlog for rework.

## 5. Live-funds hold
- Primary is red after costs (−18.10R / −$197.36 journal / −$175.87 Alpaca), so the **streak is 0**.
- Since Day 1: 12 sessions, 4 green, −50.64R, −$2,634.50 journal after costs. The Alpaca figure excluding MTUM is
  −$2,387.69 (PL1109).
- Hold stays: not ready for live funds.

## 6. Promotion / demotion (the PV decision is pending after the 11-10 close; no duplicate decisions)
- **Out-of-sample day 1, naive journal subtraction.** This is not the Exposure Lab's as-live replay, and it ignores twins,
  latches and capacity.
  - PV0 (as is) −18.10R.
  - PV1 (MF2-FD, MF4-FD, MF4 base out) +0.19R.
  - PV2 (RW3-FD, RW5-FD, L3-fromopen-FD, ST7-FD, NS5; NM-ETF late dip not in Primary) −0.77R.
- **DM-MF4, Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD`:**
  - 138 trades, 52.9% win vs 67.4% break-even, −0.227R after costs, −0.281R w/o best day.
  - Last 4 sessions −0.648R (n 58), −$2,028.43 (P + T1).
  - Today 17 trades −17.09R.
- **DM-MF2, Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD`:**
  - 125 trades, +0.110R, −0.152R w/o best day (10-22, `1 day`).
  - Last 4 sessions −0.534R (n 58). Today 1 trade −1.20R.
- **Keepers today:** RW3-FD (123 trades +0.405R, last 4 +0.714R) and RW5-FD (133 trades +0.347R).
- No promotion candidate.

## 6a / 6b. Marks and watches
- **M1 NS4-FD (Testing 1):** since the mark 15 trades / 7 sessions, 0 green, −0.432R; today 3 trades −1.72R. The lean is drop.
- **M2 GEN-261026-03 (in Testing 2 for EXPO1109):** no trade today; since the mark 17 trades +0.406R, 1 of 2 green.
- **RW3S-FD:** green today (3 trades +1.23R), but 1 of 5 sessions green and 143 trades −0.275R. Its "Graveyard unless green"
  verdict is therefore technically met by today's green day; the owner calls it.
- CWT14 pdl p10-lowvol: since its move 134 trades −0.213R; today −0.12R.

## 6c. The −2R stop and latch shadows (`today_out.txt`, `forward_out.txt`, `openloss_out.txt`)
- **MF4-FD latch:** latched at 10:52, after its last entry (10:51), so it prevented 0 of the 17 losses.
- **L3-fromopen latch:** latched 10:56–11:02.
- **Blocked signals:** 28, what-if +0.36R before costs (MF4 5 at −0.5R, L3 23 at +0.86R). Deduped first per setup-symbol:
  10 at +2.5R. The latch cost a little today.
- **Latch-by-category shadow:** the Graveyard latch saved +23.4R raw (shorts +53.7, longs −30.3); 4-day Graveyard ≈ +241.6R
  saved. Primary −2.5R today.
- **burst1-openloss-latch3 shadow:** MF4-FD hit −4.86R open at 10:40 and would have blocked 3 entries (+1.66R). Primary
  shadow minus live +0.89R; Graveyard +10.56R (7 better / 2 worse).
- **BRAKE-1:** triggered 10:54; 6 family lots after it at half size: −0.27R today, running −10.59R.

## 6c3. REG2 shadow (session 4 of 5)
- REG1 day UP (SPY +0.78% at 10:00), so shorts are kept and the one long is dropped.
- Kept-only −18.58R vs actual −18.10R: diff −0.47R.
- 4-session diff −6.76R (−2.32, −4.24, +0.27, −0.47). Rows appended to research/bdi/reg2_shadow.csv.

## 6c4. Claude's Team (shadow)
- Final +2.54R / +$433.50 after costs (14 trades) vs Primary −18.10R.
- Per setup:

| setup | trades | R |
|---|---|---|
| GEN MACDh LATE long | 7 | +2.06 |
| RSI Collapse Dip Buy | 1 | +1.00 |
| Late-Day ETF Dip Buy | 2 | +0.99 |
| RW3-FD | 1 | −0.29 |
| RW5-FD | 3 | −1.22 |
| Gap-Down VWAP Loss | 0 | 0 |
| NS5 | 0 | 0 |

- Scoreboard row added (see failure 3).

## 6e. Forward shadows (`forward_gate1.py`, research/bdi/swings/hypotheses.jsonl)
- **gate1-checkpoint-gate:**
  - GATE1 (live compass) was UP at all 9 checkpoints. It dropped 29 entries worth −15.88R, so the gate gained +15.88R:
    Gen GEN-261026-10 longs 16 (−6.3R) and Graveyard shorts 13 (CWT13-z05 −5.8, NS3-FD −2.5, RW4-FD −1.3).
  - **It would have dropped nothing from Primary.** MF4-FD is not gate-listed, and its 17 shorts were all before the first
    checkpoint. L3-fromopen-FD and MF2-FD are allowed in UP. The 6 Primary entries after 11:00 were RW3-FD / RW5-FD.
  - Forward: 3 sessions, +18.05R total.
- **comp15-w60-early:** W60 first confirmed UP at 10:00 vs the 30-min compass at 10:30. 0 side flips, and it was correct
  (close +1.44%). Forward: 2 sessions.

## Daily post fix (PL1109, PR #164, merged)
`mcf/report/daily_post.py` image 1 changes:
- Dollars are now Alpaca equity close-to-close.
- An explicit `PL_ADJUSTMENTS` table covers Primary 11-05 (set to −$367.71, trading-only) and 11-06 (+$183.92, MTUM phantom
  marks). It shows as a labelled "Excluded" line.

The Day 12 images 1 / 3 / 4, post.txt and facts.txt were regenerated (the fresh 11-09 scorecard also corrects the streak
lines), and post.md / post.html were updated for Primary today / since Day 1.
