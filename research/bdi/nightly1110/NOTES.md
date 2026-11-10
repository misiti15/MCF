# Nightly learning loop, 2026-11-10 (Tuesday): 7 accounts (Primary, Testing 1, Testing 2, Graveyard, Gen, Explore 1, Live Lab)

*Educational only — not financial advice. These are live **paper** results from one session plus the record since start. They
describe what happened; they are not evidence that anything works. **Configurations tried tonight: 0** (no lab run; the
swarm backtest of step 4 was skipped: 2 new hypotheses, both exits that need a 2-year lab build first, and no setup is near a
gate). About 20 descriptive splits were looked at, so some will look strong by chance.*

**Costs are in.** R = journal `pnl_adj / $ risk`. Dollars are Alpaca where stated. What-ifs (latch-blocked signals, closing
open lots at the latch / at the flip) use SIP 1-minute closes and are **before extra costs**.

**Rule changes inside the windows quoted** (research/ledger.jsonl):
- Primary: MF2-FD / MF4-FD promoted 10-20, ST7-FD 10-26, ~$4,000 lot 10-28, −2R per-setup stop 10-29, L3 pair 10-30.
- All accounts: GX1 10-27; UNI1 (T2 top-500 pool) 11-04; ROLL1 (Explore 1 / Live Lab) 11-05.
- **11-09 / 11-10: EXPO1109 temporary moves** (GEN-261021-02 / -261019-03 / -261026-02 Gen → Testing 1, GEN-261022-07 /
  -261026-03 Gen → Testing 2). Reverted after this close (ledger 2026-11-10-expo1109-revert, effective 11-11, PR #173), so
  Testing totals include GEN results for 11-09 and 11-10 (today T1 GEN-261021-02 33 longs −11.8R / −$56.83).
- Compass display-only from 11-09. No Primary setup or exit rule changed on 11-10.

**Ops.** Trade run 42828419526 (dispatched 08:51 ET) handed over at ~14:37 ET to run 42886204930 (handover.py). Both
succeeded in all 7 jobs. The successor's `eod-start` job (PR #165) dispatched `eod.yml` at 15:58 ET (run 42900434533,
success); a `workflow_run` EOD (42900482343) also ran, harmlessly (one "EOD report" commit per branch). The first run's
`eod-start` correctly declined ("not after the close (1438 ET)").

**Market: V-day.** SPY +0.51% at 10:00 (high +0.56% 10:08), fell to −0.38% at 12:45, back across its open for good at 14:30
and closed +0.27% (QQQ +1.25% 10:01 → −0.82% 12:41 → +0.34%; IWM +0.28%).

## 1. Session close — all 7 clean
- Phase `closed`, 0 positions, `flatten_failed` [], `partial_lots` [], no data outages; job log "flatten complete: no MCF
  positions open" in all 7.
- journal = submitted = job-log "Trades": **99 / 127 / 147 / 629 / 280 / 7 / 5** (P / T1 / T2 / GY / Gen / Ex1 / LL); no
  duplicate rows across the hand-over (strategy + symbol + entry time).
- Primary broker (read-only GET): 0 positions, 0 open orders, equity $81,526.18 = status (last equity $81,635.58).
- **Latches survived the hand-over:** RW3 / RW5 / MF2 / MF4 latched 13:04–13:57 in the first run; the successor blocked
  ACGL (RW3), RBRK (MF2) and ICVT (×3) after 14:45. `setup_stopped` at the close: L3-rsi5hi-FD, MF2-FD, MF4-FD, RW3-FD, RW5-FD.
- Mid-session push rejects (Primary 11:27, Ex1 10:06, LL 11:03 ET) were retried; the final pushes landed.

## 1b. Coverage (`polls.py`, `polls_out.txt`)

| account | polls | vs 384 (T2) | longest gap |
|---|---|---|---|
| Testing 2 | 384 | 100% | 2.5 min |
| Testing 1 | 361 | 94% | 2.6 |
| Primary | 338 | **88%** | 2.5 (14:35, hand-over) |
| Explore 1 | 328 | 85% | 3.0 |
| Graveyard | 317 | 83% | 3.4 |
| Live Lab | 284 | 74% | 3.7 |
| Gen | 267 | 70% | **5.0 (14:50)** |

No gap over 5 min (Gen exactly 5.0 after the hand-over). Primary's poll count is below the usual 384 (cause not checked; its
longest gap stayed 2.5 min). Rejects: buying power Gen 146 / GY 115 (HK-GEN-BP, down from 437 / 173); price
crosscheck 4 (Gen); no "missed: triggered".

## 2. Autopsy (`autopsy.py` → scratch, `giveback.py`, `latchopen_out.txt`, `flip_out.txt`)

| account | trades | win% | R (costs) | journal $ | Alpaca (vs last equity) |
|---|---|---|---|---|---|
| Primary | 99 | 31% | **−31.25R** | −$162.88 | **−$109.40** |
| Testing 1 | 127 | 28% | −44.92R | −$484.11 | −$497.63 |
| Testing 2 | 147 | 46% | −27.11R | −$332.79 | −$324.73 |
| Graveyard | 629 | 72% | +67.90R | +$1,639.30 | +$1,716.24 |
| Gen | 280 | 43% | −59.88R | −$1,086.16 | −$957.84 |
| Explore 1 | 7 | 71% | +2.16R | +$10.15 | +$10.25 |
| Live Lab | 5 | 100% | +2.46R | +$53.18 | +$53.18 |

**Primary: 93 shorts −29.7R, 6 longs −1.6R.** Marked peak +$1,089 at 10:56 → trough −$346 at 15:53. Entries 10:00–10:59
made +6.8R (24 trades, 75% win); 11:00–13:59 −35.8R (67 trades, 18% win).
- Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` 18 trades **+6.26R / +$852.78** (10 targets). Its $ per R is
  high (COIN-class names), so the $ day was nearly flat while R was −31.
- Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` 22 **−12.53R**; Heavy Selling `RW3-…-FD` 17
  −8.83R; Early Sellers, Mid-High RSI `MF2-…-FD` 9 −6.37R; Strong Heat `MF4-…-FD` 20 −5.22R; L3-rsi5hi-FD 7 −2.98R;
  NS5 2 −1.34R; NS1 4 −0.24R.
- Bursts: MF4-FD 7 entries 10:45–11:00 (−0.41R, not the damage); RW5-FD 10 entries 12:15–12:30 (−5.18R).

**Pattern 1 — the latch stops new lots, not the open book.** Each latched setup hit −2.1 to −3.1R, then its lots already
open lost another −22.46R (43 lots). Closing them at the latch minute: −9.34R (**+13.1R**, all 5 setup-days better).
Across T1 / T2 / GY setups that crossed −2R: 19 of 26 setup-days better, 4 worse (all dip-buy longs), +48.5R in total.
→ backlog `nightly-1110-latch-closes-open-lots`.

**Pattern 2 — the midday flip.** The compass-learn standby flip ("SPY back across its open for 15 min after 12:00")
confirmed at 14:30. Shorts open at the flip: Primary 50 lots −23.97R vs −16.99R closed at the flip (+7.0R); T1 +17.5R,
T2 +24.5R, GY +12.8R. → backlog `nightly-1110-midday-flip-open-book-exit`.

**Pattern 3 — counter-index entries won** (L6): 100 trades +0.328R vs −0.103R for the rest (Primary 12 +0.672R vs 87
−0.452R) — the opposite of 11-09; evidence appended to `swing1103-L6-counter-index-entries`.

**Other accounts:** T1 Gap-Down Bounce Early Short `RW7-gapdn-bounce-early-short-FD` 57 −28.7R (55 lots open when it
crossed −2R; T1 has no latch); T2 `RW3S-gapdn-flowsell-short-FD` 61 −17.9R; GY longs +92.1R (three CWT14 failed-ORL-break long
variants +69.4R on 233) vs shorts −24.2R; Gen shorts −56.2R (`GEN-261020-10` 48 −43.0R).

## 5. Live-funds hold
Primary **−31.25R after costs, Alpaca −$109.40** → red, **streak 0**. Since Day 1 (10-23): 4 of 13 sessions green,
−81.89R, −$2,797.38 journal after costs.

## 6. Suggestions
- **DECISION RW3S-GY** (new): move Gap-Down Heavy-Selling Short, no RSI condition (all day) `RW3S-gapdn-flowsell-short-FD`
  Testing 2 → Graveyard. Since 11-03: 204 trades / 6 sessions (1 green), win 36.8% vs 52.3% break-even, −0.281R,
  −0.291R w/o its best day, day-t −1.88, last 4 −0.353R, −$867.78. The 11-06 verdict said Graveyard unless 11-09 was green;
  it was (+1.23R), then 11-10 −17.91R.
- No Testing setup is near the Primary bar (best: RW1-FD t 0.76, +0.036R w/o best day). DM-MF2 / DM-MF4 stay open and are
  folded into tonight's 18:33 TEAM-6 decision (not pre-empted here). Today: MF2-FD −6.37R (record 134 trades +0.055R,
  −0.197R w/o best day), MF4-FD −5.22R (158 −0.231R).
- Monitoring: M1 NS4-FD since the mark 16 trades −0.465R, 0 of 8 sessions green (lean drop); M2 GEN-261026-03 no trade
  (lean wait).

## 6b–6c shadows
- Watches: CWT14-pdl-p10-lowvol-long since 10-28 143 −0.204R (today 9 −0.70R); R2A long 136 −0.092R (today 26 −0.33R;
  scaled 17 +0.053 vs plain 9 −0.136), R2A short no trade; RW3S above.
- −2R latch: 28 Primary signals blocked (RW3 10, RW5 12, MF2 6) — what-if **−16.99R** before costs, so the latch saved
  ~+17R. Latch-by-category: Primary +16.99R raw / +22.85R excess; GY −41.78R raw (longs −33.2, shorts −8.6), 5-session GY
  ≈ +199.8R.
- BRAKE-1: triggered 11:19 (MF2-FD S); 49 family lots after it at half size → −31.25R actual vs −16.05R (+15.20R); running
  since 11-02 **+4.61R** (was −10.59R).
- REG2 session 5 (SPY +0.37% at 10:00 → keep shorts): kept 93 −0.319R vs dropped 6 −0.265R; kept-only −29.66R vs actual
  −31.25R (+1.59R). **5 sessions: kept 217 −0.396R vs dropped 83 +0.062R (t −3.25), kept-only −84.90R vs actual −79.74R
  (−5.16R); kept avg w/o best day −0.403R → fails both bars → FYI, parked.**
- LEASH shadow (forward day 1, seen at design): base +6.26R (18), K11 +3.88R (−2.39R), K12 +6.26R (0; no −1R latch hit).
- Compass cond: 11-10 already appended (+36 rows; 461 sessions, 1,090 cells); re-run idempotent, nothing to push.

## Files
`build.py fetch.py polls.py autopsy.py giveback.py today.py combined.py cands.py forward.py latchopen.py flip.py
add_backlog.py` (scratch inputs: journals / status / intraday / scorecards from the 7 data branches; SIP bars). Outputs:
`trades.csv`, `combined.csv`, `*_out.txt`, `forward.json`, `research/bdi/reg2_shadow.csv`,
`research/l3leash/shadow_scoreboard.csv`.
