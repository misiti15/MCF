# Nightly learning loop, analysis part: 2026-10-21 (Primary, Testing 1, Testing 2, Graveyard, Setup Generator)

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live record (rule 7). They describe what happened; they are not evidence that anything works. **No backtest was run tonight (0 configurations)**, and neither the locked block (2024-11-01..2025-02-28) nor any holdout was touched. No config, setup or exit was changed. About 50 descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin, cluster, latency for 5 accounts; 3 skip reasons). None is gated, so a few will look strong by chance.*

**Costs are in.** P/L is the journal `pnl_adj`. avgR = `pnl_adj / $ risk`. The journal's `r_multiple` is quoted as "R(j)". What-if R for blocked signals is the runner's own what-if run (run 2) less the production cost model (as nightly1020).

**Inputs.**
- `journal.db`, `status.json`, `reports/2026-10-21.csv`, `reports/scorecard.json`, `intraday/2026-10-21.jsonl` from these branches:
  - `origin/mcf-data` (Primary, p)
  - `mcf-data-testing` (T1)
  - `mcf-data-testing2` (T2)
  - `mcf-data-graveyard` (GY, first session)
  - `mcf-data-gen` (GEN)
- SIP 1-min bars for 493 symbols (Alpaca market data, read-only, kept in scratch).

**Scripts** were copied from `nightly1020/` with the date set to 10-21 and the Graveyard added. Run each as `python <script> <scratch>`:
- `fetch.py`
- `build.py` → `trades.csv`
- `autopsy.py` → `autopsy_out.txt`
- `giveback.py` → `giveback_out.txt`, `daily_peak.csv`, `giveback_attr.csv`
- `tables.py` → `tables_out.md`
- `caps.py` → `caps_out.txt`
- `combined.py` → `combined.csv`, `combined_out.txt`

The LL-1.5 monitor reuses `research/bdi/ll1020/replay.py`, which now has 10-21 and the Graveyard added.

**Market: a flat, choppy day; large caps up and small caps down.**
- SPY +0.25%: low −0.36% at 10:12, high +0.42% at 14:16, dip to +0.05% at 15:00.
- QQQ +0.42%: high +0.80% at 13:20.
- IWM −0.14%: low −0.56% at 15:11.
- Large caps rallied 11:00–13:30 while short books were open. The split-tape gate was active in Testing 1 from 11:00.

## Failures first

1. **Primary closed −$626.57 after costs**, its second-worst day (journal −$592.95). The positive-day streak is 0 and the live-funds hold stays.
   - The marked P/L was +$90 at 12:28 and fell to −$753 at 14:43.
   - Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD) lost −$481.78 (26 trades, 12% win).
   - Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD) lost −$176.93 (5 of 5 stopped).
   - Both are already analysed in `research/bdi/gates1021/NOTES.md`, which was not redone here. In short: stacked lots on the same names (FTNT, CIFR, SKHY ×3), then a 13:00–14:00 squeeze in crypto miners. As run live over 2 years, both lose: NS3-FD −0.015R/trade (n 16,955), L3-fromopen-FD −0.031R (n 25,124).
2. **Every account but GEN closed red.**
   - T1 −$547.68.
   - Graveyard −$747.09: heat_fade_short-FD alone lost −$460.88.
   - T2 −$14.85.
3. **The per-setup −2R stop overshot again** (realized-only, as on 10-20). Lots that were open when a setup tripped:
   - T1 CWT14-failbrk-pdh-p05-lowvol-short: 28 lots open at 10:40, −16.0R after the trip.
   - T1 CWT14-failbrk-pdh-p10-short: 14 open at 11:35, −12.2R.
   - GY heat_fade_short-FD: 22 open at 11:50, −16.2R.

   This is evidence for `nightly-1020-setup-loss-limit-open-risk`, which is now in the backlog, and for OPEN_ITEMS LL-OPEN.
4. **Nothing broke** (apart from 7 bracket rejects, H-1). In all 5 accounts:
   - phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data outages;
   - journal trades = submitted signals = EOD report rows = `status.today.trades`;
   - EOD report and scorecard pushed (19:57–19:58 UTC).

   Not verifiable here: open orders at the broker, and GitHub Actions job logs (no access). The journal = report = status match is the proxy for "final push succeeded".

## 0. Session close, and today's new mechanics

| account | phase | positions | flatten_failed | polls | journal = report = status | EOD + scorecard |
|---|---|---|---|---|---|---|
| Primary | closed | 0 | [] | 48 | 46 = 46 = 46 | yes |
| Testing 1 | closed | 0 | [] | 49 | 199 = 199 = 199 | yes |
| Testing 2 | closed | 0 | [] | 51 | 91 = 91 = 91 | yes |
| Graveyard | closed | 0 | [] | 50 | 347 = 347 = 347 | yes (first scorecard, 1 session) |
| GEN | closed | 0 | [] | 47 | 13 = 13 = 13 | yes |

- **GY-1, the Graveyard's first session, was clean. The item is closed.**
  - The job ran 50 polls, and 714 signals gave 347 trades.
  - Order ids carry the `mgy-` prefix (e.g. `mgy-heat_fade_short-ASML-20261021-0949`).
  - It ended flat, and the push landed (`job 15:05 done`, then the EOD report).
- **Split-ticker copies (allocation 2026-10-20) were clean.**
  - Every trade and signal of MF5-flowsell-vwapup-rsi5hi, NS5-sma50-flush-oversold-long-FD, RW4-ns3-adv150-short-FD and exhaustion_short-FD stayed on its own half: T1 = crc32 half 0, T2 = half 1. That is 0 wrong-half rows in 53 signals and 34 trades.
  - No setup + symbol pair was traded in both testing accounts.
- **Twin cap ("twin held") worked.**
  - Primary: 1 block (MF4-h40 base ← MF4-FD), what-if +0.42R.
  - T1: 4 blocks (MF3 base), what-if +2.35R.
  - GY: 25 blocks, what-if **−5.20R**, so about $72 was avoided. 20 of them were heat_fade_short-FD signals while heat_fade_short held the name.
- **twin_group (LD-NS1 / LD-ST2 / LD-SPXL) could not be checked.** The LD1–LD8 longs and the M1 observation (NM-MF3-qqqdn-gapdn-FD) fired **no signals** today. Expected rates are 0.07–0.42/day each.
- **Testing 1's new scale-out cap (2/day) held.**
  - Exactly 2 scale-outs: XLC 09:49 and QID 09:54, both CWT14-failbrk-pdl-p05-long, both then `scaled+breakeven` (−$0.03, −$1.98).
  - 30 later pdl-p05-long trades and 13 pdh-p05-lowvol-short trades reached their trigger with no budget left. Logged as idea `nightly-1021-scaleout-cap-allocation`.
  - T2 also made 2 scale-outs (CWT12-coil-k4-long DT and ZSL).
- **The split-tape short gate in T1 blocked 73 shorts (11:00–14:59).** Their what-if was 48% win, **−8.49R** after costs (about $50 avoided). The largest piece was L3-gap-slope-lowdist-FD at −4.83R.

## 1. Headline per account (real trades, run 1)

| account | trades | win% | avgR (costs) | R(j) | P/L journal | P/L after costs | stop / target / flatten | marked peak → close | runner peak / trough |
|---|---|---|---|---|---|---|---|---|---|
| Primary | 46 | 30.4% | −0.321 | −0.301 | −$592.95 | **−$626.57** | 15 / 12 / 19 | +$90 (12:28) → −$627 (trough −$753 14:43) | +$104 (12:26) / −$694 (14:41) |
| Testing 1 | 199 | 45.7% | −0.273 | −0.241 | −$501.84 | **−$547.68** | 85 / 82 / 30 (+2 scaled) | +$50 (10:06) → −$548 | +$46 / −$521 (15:34) |
| Testing 2 | 91 | 57.1% | −0.012 | +0.005 | +$0.71 | **−$14.85** | 23 / 46 / 20 (+2 scaled) | +$91 (15:11) → −$15 (trough −$167 14:43) | +$97 / −$148 |
| Graveyard | 347 | 58.5% | −0.091 | −0.073 | −$656.79 | **−$747.09** | 108 / 193 / 46 | +$199 (10:41) → −$747 | +$247 / −$690 |
| GEN | 13 | 76.9% | +0.373 | +0.373 | +$419.85 | **+$419.61** | 1 / 4 / 8 | +$489 (15:11) → +$420 | +$507 / −$89 |

**Total after costs: −$1,516.58** (all 5 accounts).

**Best and worst setups (after costs):**
- **Primary.**
  - Best: CWT14-pdl-p10-lowvol-long +$33.35 (6 of 6 won, +0.51R); RW5-FD +$16.06; MF4-FD +$11.75.
  - Worst: NS3-FD −$481.78; L3-fromopen-FD −$176.93; RW3-FD −$24.68.
- **Testing 1.**
  - Best: CWT14-pdl-p05-long +$16.35 (40); MF3-FD +$15.79.
  - Worst: CWT14-pdh-p05-lowvol-short −$154.64 (44, 45%); CWT14-pdh-p10-short −$137.22 (42); NS3 base −$98.67 (9, 11%); RW4-FD −$94.82 (8, 0%).
- **Testing 2.**
  - Best: CWT09-g10 +$88.81 (1); CWT12-coil-k4 +$23.59.
  - Worst: RW4-FD −$72.04 (13, 23%); NM-AR-AM capitulation long −$41.33 (3, all stopped).
- **Graveyard.**
  - Best: CWT14-orl-p05-long +$73.30; heat_fade_long(-FD) +$71/+$72; MF1-FD +$61.07.
  - Worst: heat_fade_short-FD −$460.88 (25, 4%); RW2-FD −$189.16; heat_fade_short −$174.79; LIQ-orl-sweep −$117.96.
- **GEN.**
  - Best: GEN-261019-10 short +$267.26 (7, 86%); GEN-261019-04 long +$177.99 (2).
  - Worst: GEN-261020-05 hold-long −$40.39.

**The NS3 family took one bet across three accounts.** NS3-FD (Primary), NS3 (T1) and RW4-ns3-adv150-short-FD (T1 + T2) together lost **−25.1R** on 16 symbols. 14 of those symbols were traded in two or three accounts, mostly crypto miners (RIOT, CIFR, HUT, CLSK) plus SKHY. Read the family as one record, not three.

### 1a. Intraday peak vs close (`giveback_out.txt`)

| account | giveback | open winners at peak | entered after peak | late flatten ≥ 15:50 | main contributors |
|---|---|---|---|---|---|
| Primary | $717 | −$452 (6 stopped −$367) | −$56 | −$213 (19) | NS3-FD −$524, L3-fromopen-FD −$173 (gates1021) |
| Testing 1 | $597 | −$59 | **−$519 (146 entries after 10:06)** | −$104 | CWT14 pdh shorts −$316, NS3 −$101, RW4-FD −$95 |
| Testing 2 | $106 | −$84 (14 flattened) | 0 | −$89 | RW4-FD −$83 |
| Graveyard | $946 | −$216 | **−$671 (161)** | −$226 | heat_fade_short(-FD) −$705, RW2-FD −$166, LIQ-orl −$160 |
| GEN | $70 | −$121 (7 flattened) | 0 | −$96 | GEN-261019-10 short −$135 into the close |

**In plain words.** T1 and the Graveyard peaked early. Their losses are new short entries into a large-cap up-tape, not give-back. Primary's give-back was open NS3-FD and L3-FD shorts stopped in the 13:00–14:00 squeeze. The late-flatten give-back (T2, GEN) fits existing ideas `nightly-1014-fd-short-late-giveback` and `bdi1016-rw7-late-exit`, so nothing new was added.

### 1b. Per-setup −2R stop (`caps_out.txt`)

| setup (account) | tripped | realized R(j) at trip | lots open → result | day R | blocked → what-if |
|---|---|---|---|---|---|
| CWT14-failbrk-pdh-p05-lowvol-short (T1) | 10:40 | −2.73 (16) | 28 → −16.01R | −18.99R | 8 → −3.75R |
| CWT14-failbrk-pdh-p10-short (T1) | 11:35 | −2.74 (28) | 14 → −12.22R | −15.45R | 1 → +0.35R |
| CWT13-vwapstretch-z05-short (T2) | 14:10 | −2.11 (2) | 2 → −0.50R | −2.68R | 1 → +0.95R |
| RW2-exhaustion-noon-adv150-short-FD (GY) | 10:50 | −2.06 (2) | 6 → −4.25R | −6.55R | 25 → −4.32R |
| CWT14-failbrk-orl-p10-lowvol-long (GY) | 11:20 | −2.10 (23) | 13 → +2.94R | −3.00R | 2 → +0.86R (9 entries after the trip: realized R recovered above −2R) |
| heat_fade_short-FD (GY) | 11:50 | −2.81 (3) | 22 → −16.24R | −19.11R | 34 → **+6.84R** |
| LIQ-orl-sweep-open15-s25-long (GY) | 13:30 | −3.20 (3) | 14 → −5.88R | −9.19R | 1 → +0.11R |

The blocked signals netted −3.40R in T1, +0.95R in T2 and +3.49R in the Graveyard. So the stop roughly broke even on what it blocked. Its real failure is the open lots it cannot block.

## 2. Winner/loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 696 trades)

| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | winner give-back | time to MFE, winners / losers | entry slip | stacked lots (lot ≥ 2) |
|---|---|---|---|---|---|---|---|
| Primary | 8 of 32, −$193 | 12 | 0.60 / 0.16 | 0.06R | 28 / 25 min | 10.2 bps | 13, −$284 |
| Testing 1 | 43 of 108, −$367 | 21 | 0.55 / 0.28 | 0.09R | 18 / 9 min | 5.7 bps | 31 |
| Testing 2 | 24 of 39, −$233 | 7 | 0.63 / 0.25 | 0.09R | 32 / 7 min | 10.7 bps | 10 |
| Graveyard | 64 of 144, −$1,204 | 22 | 0.52 / 0.28 | 0.07R | 30 / 6 min | 4.2 bps | 120 |
| GEN | 1 of 3 | 1 | 0.74 / 0.40 | 0.12R | 116 / 72 min | 10.3 bps | 0 |

- **Primary.**
  - NS3-FD: 6 of 23 losers never worked and 7 reached ≥ 0.5R first. Winners took 190 min to MFE. Lots 2–3 lost −$284 in total (gates1021).
  - L3-fromopen-FD: all 5 stopped, MAE 1.11R, 2 had reached ≥ 0.5R.
  - The promoted CWT14-pdl-p10-lowvol-long won 6 of 6.
- **Testing 1.**
  - CWT14-pdh shorts (86 trades): 28 of 47 losers never worked, clusters of 8–9 per poll, MFE within 6–15 min. They shorted prior-day-high failures into a large-cap up-tape. This is the existing day-class idea `bdi1016-dayclass-gate-cwt14pdh` (evidence added here; no new item).
  - CWT12-coil-k6-long: 10 of 20 losers had reached ≥ 0.5R (winner MFE 1.83R).
- **Testing 2.** RW4-FD: 5 of 10 losers had reached ≥ 0.5R. NM-AR-AM capitulation long: 3 of 3 never worked.
- **Graveyard.**
  - heat_fade_short-FD: 13 of 24 losers never worked, with clusters of 7.
  - LIQ-orl-sweep: 8 of 14 never worked.
  - The 4 CWT14-orl longs entered the same names within 3 min 97 times. Keeping only the first entry per symbol per 15 min would have been worse today (−2.9R vs +1.9R), so no item.
- **GEN.** GEN-261019-10 PM short won 6 of 7, then gave back $135 from the 15:11 peak at the flatten.

**Backlog (status idea, 0 configurations; `backlog_proposals.jsonl`), appended to `research/backlog.jsonl`:**
- `nightly-1020-setup-loss-limit-open-risk`: carried over from last night's proposal, with the 10-21 overshoot added.
- `nightly-1020-gen-hold-mfe-giveback`: carried over unchanged.
- `nightly-1021-scaleout-cap-allocation`: new.

**Step 4 (swarm) is deferred.**
- The open-risk idea needs a replay with slot effects, which is already scheduled for the Saturday deep run on 10-24 (LL-OPEN).
- The scale-out idea is scored on live journals first.
- The GEN idea belongs to the generator lab.

## 3. Live-funds hold: Primary positive-day streak

| | 10-12 | 10-13 | 10-14 | 10-15 | 10-16 | 10-19 | 10-20 | 10-21 |
|---|---|---|---|---|---|---|---|---|
| after costs | **+115.77** | −101.67 | **+60.35** | −926.53 | −14.41 | −63.92 | −46.13 | **−626.57** |

- **Today: negative. Consecutive positive Primary sessions: 0.** 2 of 12 sessions have been positive, and the longest streak is 1.
- Since start: 466 trades, 42.9% win, **−$2,390.46 after costs**. **The hold stays.**

## 4. Promotion / demotion suggestions (owner decides; `combined_out.txt`)

**Method.** The same as nightly1020, across all 5 accounts, merged by setup name. "last-4" covers 10-16, 10-19, 10-20 and 10-21.
- Not suggested again: N2 and N3 (pending; numbers not materially changed), G1 (gates1021), and the standing answers.
- The watch list (PROMO-1021) is section 6b.

| setup | trades | sessions | win | BE win | avgR | t / t_day | last-4 R (n) | backtest R | suggestion |
|---|---|---|---|---|---|---|---|---|---|
| Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD), Primary | 84 (Primary-only 32 in 2 sessions: −11.97R, −$484.71) | 7 | 39.3% | 43.0% | −0.058 | −0.56 / −0.32 | −0.036 (69) | 2-yr as-run −0.015R (gates1021) | **N5: Primary → Testing 2** |
| Failed Prior-Day-High Break Short (0.05 ATR, low volume) [fill] (CWT14-failbrk-pdh-p05-lowvol-short), T1 | 232 | 8 | 57.8% | 68.2% | −0.173 | −2.98 / −1.89 | −0.191 (108) | −0.095 | **N6: → Graveyard** |
| Failed Prior-Day-High Break Short (0.1 ATR) [fill] (CWT14-failbrk-pdh-p10-short), T1 | 210 | 8 | 62.4% | 69.7% | −0.139 | −2.00 / −1.21 | −0.141 (98) | −0.096 | N6 |
| Failed Prior-Day-High Break Short (low volume) (CWT14-failbrk-pdh-p10-lowvol-short), T2 | 102 | 7 | 54.9% | 66.3% | −0.194 | −2.08 / −1.76 | −0.198 (40) | −0.089 | N6 |

- **N5.** Testing 2 rather than Testing 1, because Testing 1 already runs its base (NS3-failed-vwap-reclaim-short) and the allocator keeps a setup and its -FD apart. The family lost −25.1R across accounts today (section 1).
- **N6.** The three pdh shorts lost −$548 combined. All are under their break-even win rate, every backtest is negative, and on 10-21 they lost −36.2R.

**Promotions: none.**
- The best candidates are still small:
  - NS4-pm-vwap-reclaim-oversold-short-FD (T1): 11 trades, +0.361R, t_day 1.98, no trades today.
  - Generated: FlowShiftge0p42 PM short (GEN-261019-10-…-t1s1-short): 11 trades in 2 sessions, +0.358R, t_day 2.09.
- Primary keepers holding up: MF4-h40-open-flowsell-FD (41, +0.248R, t_day 2.00) and RW5-heat30-…-short-FD (49, +0.292R, t_day 1.57).

## 6b. Watch list (Primary-only since 2026-10-21; first review 2026-10-27)
- Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD): 5 trades, 0% win, −1.15R avg, −$176.93. The 2-yr as-run backtest is −0.031R/trade.
- Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] (CWT14-failbrk-pdl-p10-lowvol-long): 6 trades, 100% win, +0.51R avg, +$33.35. The backtest is −0.095R.

## 6c. LL-1.5 monitor (`research/bdi/ll1020/replay.py`, with 10-21 and the Graveyard added)

| 10-21 net R after costs | −2R (live) | −1.5R |
|---|---|---|
| Testing 1 | −54.38 | −54.81 |
| Testing 2 | −1.08 | −1.08 |
| GEN | +4.85 | +4.85 |
| Graveyard | −30.22 | −30.22 |
| **day** | **−80.83** | **−81.26** |

- **Since 10-21:** −1.5R is behind by 0.43R (1 of 3 sessions).
- **7-day base (10-12..10-20):** −1.5R ahead by +40.56R. Over 8 days that makes +40.13R.
- −1.5R blocked 1 more T1 signal than −2R. Both blocked 64 Graveyard signals.

## Housekeeping (no strategy change)
- H-2 (T1 "not shortable/ETB" noise) is smaller after L3-fromopen-FD left T1: 21 skips today, against 296 on 10-20.
- T2 still logs 36 ETB skips.
- H-1 (bracket rejects, "take_profit.limit_price must be <= / >= base_price ± 0.01") is still open: 7 today. 3 in T1 (CWT14 pdh shorts EW, HPQ ×2; the setups moved there with the reallocation) and 4 in T2 (CWT14 pdl longs RWM, TZA, SBUX ×2).

Educational only — not financial advice.
