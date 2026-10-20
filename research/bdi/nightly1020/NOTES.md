# Nightly learning loop, analysis part: 2026-10-20 (Primary, Testing 1, Testing 2 = Graveyard, Setup Generator)

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live record (rule 7). They describe what happened; they are not evidence that anything works. **No backtest was run tonight (0 configurations)**, and neither the locked block (2024-11-01..2025-02-28) nor any holdout was touched. No config, setup or exit was changed. About 40 descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin, cluster, latency per account; 2 skip reasons × 4 accounts). None is gated, so a few will look strong by chance.*

**Costs are in.** P/L is the journal `pnl_adj`. avgR = `pnl_adj / $ risk`; the journal's `r_multiple` is quoted as "R(j)" (what the dashboard shows). What-if R for blocked signals is the runner's own what-if run (run 2) less the production cost model (`config/default.yaml`: $0.01/sh + 1 bps per side, none on target exits, +$0.02/sh on stops). Intraday curves mark open lots at the previous 1-min SIP close less 1 bps + $0.01/sh (giveback1019 method).

**Inputs.** `journal.db`, `status.json`, `reports/2026-10-20.csv`, `reports/scorecard.json`, `intraday/2026-10-20.jsonl` from `origin/mcf-data` (Primary), `mcf-data-testing` (T1), `mcf-data-testing2` (T2), `mcf-data-gen` (GEN); `docs/live/assignments.json` (state 2026-10-20 16:06 ET); SIP 1-min bars for 363 symbols incl. SPY/QQQ/IWM (Alpaca market data, read-only, kept in scratch). All four journals are complete today (submitted signals = trade rows; totals match the EOD reports).

**Scripts** (run as `python <script> <scratch>`; copied from `nightly1019/`): `fetch.py` (bars, incl. what-if symbols), `build.py` → `trades.csv`, `autopsy.py` → `autopsy_out.txt`, `giveback.py` → `giveback_out.txt`, `daily_peak.csv`, `giveback_attr.csv`, `tables.py` → `tables_out.md` (per-setup tables), **new** `caps.py` → `caps_out.txt` (twin cap / per-setup loss limit), **new** `combined.py` → `combined.csv`, `combined_out.txt` (cross-account record per setup).

**Market: an up day led by small caps.** SPY +0.41% (low −0.21% 09:45, high +0.84% 10:30), QQQ +0.31% (−0.68% 09:45, +1.05% 10:30), IWM **+1.57%** (high +1.98% 11:02). A V off the 09:45 low into 10:30–11:00, a dip to 11:30, then a flat-to-up afternoon. The mostly-short Primary book fought the tape all day.

## Failures first

1. **Primary closed negative after costs again: −$46.13** (journal −$29.61). Streak 0 (section 3). The live-funds hold stays.
2. **The per-setup −2R limit overshoots.** It checks realized R only. Every tripped setup ended well past −2R (−2.06R to −8.88R) because lots already open at the trip kept losing (section 1b). In T1 the signals it blocked were net **positive** (+18.87R in the what-if).
3. **Setup Generator −$74.63** on 6 trades: one hold-to-close setup (GEN-261020-07) was +$305 marked at 10:58 and closed −$90.
4. **Testing 2 still rejects brackets:** 22 orders "take_profit.limit_price must be ≤/≥ base_price ± 0.01" (CWT14 pdl/pdh), 132 such rejects on earlier days. Housekeeping H-1.
5. **Testing 1 "not shortable/ETB": 296 skips**, 246 of them L3-gap-slope-fromopen-FD re-firing on 49 hard-to-borrow names. Noise in the skip counts (H-2).
6. **What worked as built:** the fixed live scale-out completed twice in T2 (BITO, COIN on CWT14-pdl-p05-long, both `scaled+target`), no failures, the 2/day cap held. No flatten failures, no data outages in any account.

## 1. Headline per account (real trades, run 1)

| account | trades | win% | avgR (costs) | R(j) | P/L journal | P/L after costs | stop / target / flatten | marked peak → close (costs in) | runner peak / trough |
|---|---|---|---|---|---|---|---|---|---|
| Primary | 70 | 54.3% | −0.052 | −0.030 | −$29.61 | **−$46.13** | 19 / 12 / 39 | +$58 at 14:45 → −$46 | +$81.84 (14:44) / −$91.31 (13:54) |
| Testing 1 | 266 | 60.2% | +0.089 | +0.102 | +$718.51 | **+$692.09** | 53 / 85 / 128 | +$912 at 14:45 → +$692 (trough −$363 at 10:58) | +$1,035.92 (14:42) / −$320.48 (10:55) |
| Testing 2 (Graveyard) | 142 | 76.1% | +0.207 | +0.223 | +$292.42 | **+$281.38** | 26 / 102 / 12 (+2 scaled+target) | +$297 at 14:45 → +$281 | +$313.87 (14:43) |
| Setup Generator | 6 | 33.3% | −0.090 | −0.084 | −$72.23 | **−$74.63** | 1 / 1 / 4 | +$321 at 10:58 → −$75 | +$332.45 (10:20) / −$84.98 (15:38) |

(The marked Primary trough of −$164 at 15:52 is a thin last-minute bar artefact; the runner's −$91 at 13:54 is the better trough.)

**Best / worst setups today (after costs):**

| account | best | worst |
|---|---|---|
| Primary | NS1-rsidip +$41.27 (2); MF2-FD +$13.22 (2, +1.78R); RW3-FD +$6.44 | NS5 −$42.32 (3, 0%); MF3-FD −$30.66 (20, 50%); MF1 −$22.91 (7, 14%); RW5-FD −$12.91 |
| Testing 1 | **L3-gap-slope-fromopen-FD +$654.97 (80 shorts, 78%, +0.42R)**; L3-lowdist-FD +$172.11 (11); heat_fade_long-FD +$85.38 (14, 86%) | NS1-FD −$76.21 (11); orb20_a −$48.73 (3, 0%); heat_fade_short-FD −$34.30; MF3-FD −$30.45; MF1-FD −$26.64 |
| Testing 2 | CWT14-pdl-p05-long +$148.66 (38, 95%); pdl-p10-long +$132.97 (25, 96%); pdl-p05-lowvol +$55.00 | RW2-FD −$70.04 (15, 33%); CWT14-pdh-p05-lowvol-short −$24.66; orl-p05(-lowvol) −$24 each (4, 0%) |
| GEN | GEN-261019-01 FCX +$15.40 | GEN-261020-07 hold-long −$90.03 (5) |

T1's day is one setup on one theme: L3-fromopen-FD shorted 25 crypto-miner / small-cap names up to 5 times each. **Without today it is −0.174R over 48 trades** (L3-lowdist-FD −0.078R over 19). Both are on tonight's graveyard list; today does not change that.

### 1a. Intraday peak vs close (giveback1019 attribution, `giveback_out.txt`)

| account | giveback | open winners at peak | entered after peak | late flatten ≥ 15:50 | side | main contributors |
|---|---|---|---|---|---|---|
| Primary | $104 | **−$93** (27 flattened −$35, 2 stopped −$67) | −$1 | −$46 (39 lots) | shorts −$98 | NS4 CIFR short stopped −$58 (was +$21 at the peak), RW5-FD ARWR −$14, NS3-FD RIG ×3 −$26 |
| Testing 1 | $220 | **−$202** (78 flattened −$221, 8 targets +$24) | −$2 | **−$215 (128 lots)** | shorts −$212 | L3-fromopen-FD −$133 (37 lots marked +$449 at the peak, closed +$316), RW6G1-FD −$21, RW6-FD −$14 |
| Testing 2 | $16 | −$13 | −$6 | −$13 | | CWT13-z05-short −$10 |
| GEN | $395 | −$395 (4 flattened −$252, 1 stop −$144) | 0 | −$252 | longs | all GEN-261020-07 |

**In plain words:** nothing was lost by late entries today (the peak was at 14:45). The give-back is open short winners handed back into the final-hour lift (SPY +0.11% from 14:45) and flattened at 15:55. That is the pattern in `nightly-1014-fd-short-late-giveback` (idea) and `bdi1016-rw7-late-exit` (idea); today adds T1 −$215 and Primary −$46 of late-flatten give-back as support. No new item.

### 1b. Did the twin cap and the per-setup loss limit fire? (`caps_out.txt`)

**Twin cap ("twin held": X and X-FD may not both hold a symbol):**

| account | blocked | what-if of the blocked signals (costs in) | blocked setup ← holder |
|---|---|---|---|
| Primary | 4 | 4 trades, 75% win, **+0.40R (≈ +$5)** | MF4-h40 base ← MF4-FD |
| Testing 1 | 30 (29 priced) | 29 trades, 28% win, **−14.59R (≈ −$162 avoided)** | MF3 base −6.0R and MF5 base −5.1R ← their -FD twins; NS2 base −2.3R; heat_fade_short-FD +1.8R ← heat_fade_short |
| Testing 2 / GEN | 0 | | |

The cap helped on day 1 (net ≈ +$157 across accounts). It supports `gb-1019-twin-setup-exposure`, which is now live.

**Per-setup daily loss limit (−2R net, T1/T2/GEN; not Primary):**

| account | setups tripped | blocked | what-if of blocked (costs in) |
|---|---|---|---|
| Testing 1 | 6 | 75 (73 priced) | 66% win, **+18.87R (≈ +$209 forgone)**; MF1-FD +14.49R (21), NS2-FD +2.20R (24), RW5-FD +1.51R, heat_fade_short-FD +0.92R, MF5-FD +0.41R, MF3-FD −0.66R |
| Testing 2 | 4 | 14 | 43% win, **−4.86R (≈ −$39 avoided)**; CWT14-orl-p05 −2.18R, orl-p05-lowvol −1.59R, pdh-p10-lowvol −1.07R |
| GEN | 0 | 0 | |

| setup (account) | tripped | realized R(j) at trip | lots open at trip → result | final live R (costs) |
|---|---|---|---|---|
| MF1-945-flowsell-vwapup-FD (T1) | 10:40 | −2.99 (5) | 3 → −2.92R | −6.63R |
| MF3-open-flowsell-rsi5hi-FD (T1) | 10:40 | −2.58 (4) | 4 → −3.54R | −6.27R |
| NS2-sma50break-overbought-short-FD (T1) | 10:45 | −2.03 (2) | 0 | −2.19R |
| RW5-heat30-…-short-FD (T1) | 11:00 | −2.27 (2) | 0 | −2.38R |
| MF5-flowsell-vwapup-rsi5hi-FD (T1) | 11:05 | −2.35 (4) | 6 → −1.61R | −4.14R |
| heat_fade_short-FD (T1) | 14:15 | −3.09 (3) | 9 → −3.36R | −6.54R |
| CWT14-failbrk-orl-p05-long (T2) | 11:30 | −3.96 (3) | 1 → −1.11R | −5.65R |
| CWT14-failbrk-orl-p05-lowvol-long (T2) | 11:30 | −3.98 (3) | 1 → −1.13R | −5.68R |
| RW2-exhaustion-noon-adv150-short-FD (T2) | 13:25 | −7.46 (12) | 3 → −0.60R | −8.88R |
| CWT14-failbrk-pdh-p10-lowvol-short (T2) | 14:35 | −2.04 (3) | 0 | −2.06R |

- **Overshoot:** the limit is realized-only, and lots opened in clusters (3–9 per setup) keep running after the trip. RW2-FD opened 6 lots 10:12–10:17 while its realized R was still about −0.2R and lost −7.5R before it tripped.
- **Timing:** the T1 trips at 10:40–11:05 came at the morning low of the short books, just before the 11:00–11:30 index dip. The blocked MF1-FD shorts then won (+14.5R).
- One day, opposite signs in T1 and T2. Proposed as **`nightly-1020-setup-loss-limit-open-risk`** (risk; count open-lot risk; also score "no limit" and a per-poll lot cap). No change to the live rule.

## 2. Winner/loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 484 trades)

| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | winner give-back (MFE − R) | time to MFE, winners / losers | entry slip |
|---|---|---|---|---|---|---|
| Primary | 8 of 32, −$95.96 | **13 of 32** | 0.69 / 0.24 | 0.19R | 56 / 17 min | 2.5 bps |
| Testing 1 | 40 of 106, −$322.64 | 25 | 0.76 / 0.32 | 0.11R | 71 / 16 min | 6.1 bps |
| Testing 2 | 21 of 34, −$135.45 | 6 | 0.49 / 0.15 | 0.08R | 10 / 3 min | 5.9 bps |
| GEN | 0 of 4 | **4 of 4** | 0.93 / 0.57 | 0.22R | 149 / 28 min | **25.4 bps** |

Per setup, compact (full tables in `tables_out.md`):
- **Primary.**
  - MF3-FD (20 trades, −0.16R): 10 losers, 3 had reached ≥ 0.5R, and 10 twin-type entries (same symbol + side with another setup ≤ 3 min).
  - MF1 (7, 14% win): 5 of 6 losers had reached ≥ 0.5R (winner MFE 2.80R). It shorts the open flush and is stopped on the rebound.
  - NS5 (3 longs, 0%): 2 never worked.
  - NS4 (11, 73% win, −$0.44): wins small, CIFR −$36.55 stopped late.
  - Winners MF2-FD, NS1, RW3-FD, MF4-FD had no never-worked losers.
- **Testing 1.**
  - L3-fromopen-FD (80): 6 of 18 losers never worked; 52 lots were flattened at 15:55.
  - NS1-FD (11, 36%): 6 of 7 losers never worked (dip-buy longs on the 09:45 low).
  - heat_fade_short-FD (12, 17%): 5 of 10 losers never worked.
  - The MF family's -FD copies (MF1/MF3/MF5-FD) all lost and all tripped the limit.
- **Testing 2.**
  - CWT14 pdl longs won 95–96% on an up day (MAE of the few losers 0.3–0.4R).
  - CWT14 orl longs lost 0/8 before the limit.
  - RW2-FD (15 shorts, 33%) shorted morning strength on an up day.
- **GEN.** GEN-261020-07 (hold-long): all 5 reached ≥ 1.10R (median 1.30R), and 4 ended ≤ 0 at the close. The 25 bps average slip comes from small caps (RDW 59 bps, NTSK 34 bps). Proposed as **`nightly-1020-gen-hold-mfe-giveback`**: ask the generator lab to report a 1R target/trail next to the hold exit. Proposal only; no GEN setup is changed.
- **No other new pattern.**
  - Late-flatten give-back of shorts supports existing ideas (section 1a).
  - Shorts on a strong-IWM day lines up with the live split-tape gate (QQQ +0.26% vs IWM +1.63% at 15:30, spread −1.37, not blocking) and `bdi1016-dayclass-late-decision`.

Proposals: `research/bdi/nightly1020/backlog_proposals.jsonl` (2 lines, status idea, tag nightly-1020, 0 configs). **Nothing was appended to `research/backlog.jsonl`.**

## 3. Live-funds hold: Primary positive-day streak

| | 10-06 | 10-07 | 10-08 | 10-09 | 10-12 | 10-13 | 10-14 | 10-15 | 10-16 | 10-19 | 10-20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| after costs | −127.73 | −264.73 | −140.80 | −254.09 | **+115.77** | −101.67 | **+60.35** | −926.53 | −14.41 | −63.92 | **−46.13** |

- **Today: negative** (−$46.13 after costs, −$29.61 journal). **Consecutive positive Primary sessions: 0.**
- 2 of 11 sessions have been positive after costs; the longest streak is 1.
- Since start: 420 trades, 44.3% win, R(j) −0.139, **−$1,763.89 after costs**.
- **The hold stays.**

## 4. Promotion / demotion suggestions (owner decides; `combined_out.txt`)

**Method.** One row per setup, merged by name across all four accounts as the dashboard does.
- Columns: trades, sessions, win rate, break-even win rate (from the setup's own avg win / loss in R), avg R after costs, t (per trade on R(j), as the dashboard shows) and day-clustered t (rule 4), last-4-session avg R (10-15..10-20), and backtest R (`scorecard._expected`; "(base)" = the non-FD version's).
- Excluded from suggestions:
  - Setups already moving tonight.
  - The owner's standing answers: MF4 keep, MF1 leave, MF3 & MF5 demoted, MF2-FD/MF4-FD/NS3-FD promoted.
- Caveat: T1's 10-19 journal still misses 132 trades.

| setup (now) | trades | sessions | win | BE win | avgR | t / t_day | last-4 R (n) | backtest R | suggestion |
|---|---|---|---|---|---|---|---|---|---|
| MF3-open-flowsell-rsi5hi-FD (Primary) | 90 | 7 | 51.1% | 57.4% | −0.135 | −1.10 / −1.00 | −0.246 (71) | −0.034 (base) | **N1: demote to T1** |
| RW6G1-ns2-up3-vwap2sd-short (Primary) | 3 | 1 | 0% | — | −1.069 | — | −1.069 (3) | none | **N2: demote to T1** (its -FD copy: 15 trades, 33% vs BE 54%, −0.316R, t_day −1.45; sibling RW6-FD goes to the graveyard tonight) |
| NS5-sma50-flush-oversold-long-FD (T1) | 25 | 6 | 36.0% | 76.1% | −0.464 | −3.58 / −1.51 | −0.597 (19) | +0.002 (base) | **N3: T1 → Graveyard** with ST4-FD and RW6G1-FD |
| ST4-emadn-long-am-t1s05-FD (T1) | 11 | 5 | 18.2% | 41.1% | −0.699 | −1.77 / −1.35 | −0.656 (4) | none | N3 |
| RW6G1-ns2-up3-vwap2sd-short-FD (T1) | 15 | 6 | 33.3% | 53.9% | −0.316 | −1.46 / −1.45 | −0.546 (9) | none | N3 |
| CWT14-failbrk-orl longs ×4 (T2 = Graveyard) | 1,084 | 7 | 54–62% | 69–71% | −0.172 to −0.268 (family −0.208) | t_day −2.58 to −4.71 (family −4.0; 0 of 7 days positive) | −0.21 to −0.33 | −0.09 each | **N4: retire?** −$1,667 combined. They have only 7 Graveyard sessions, and retiring needs the owner prompt (rule 20) |

**Watch, not suggested:**
- MF2-open-rsimidhi-flowsell base (Primary): 4 trades, all stops, −1.21R, last traded 10-14; too few.
- NS5 base (Primary): 17 trades, +0.036R, t_day 0.12, last-4 −0.319R (8), today −$42.
- MF5-FD (T1): 41 trades, −0.209R, t_day −1.30; it tripped the limit today.

**Promotions: none suggested.**
- The best T1 candidates are small: NS4-pm-vwap-reclaim-FD (11 trades, +0.361R, t_day 1.98, 8 of them today) and ST7-rsi50dn-long-pm-FD (11, +0.532R, t_day 1.60, +0.256R without its best day). Both are short of a sample.
- No T2 setup is positive with a positive backtest. CWT14-pdl-p10-lowvol-long is +0.060R over 94 trades, t_day 0.70, backtest −0.095.

**Setup Generator → Testing/Primary: none.** No GEN setup has more than 5 trades. The only positive one with ≥ 3 trades is GEN-261019-10 (4 trades, +0.257R, one day).

## Housekeeping items (no strategy change)

| id | item |
|---|---|
| H-1 | Testing 2: 22 bracket rejects today ("take_profit.limit_price must be ≤ base_price − 0.01" or "≥ base_price + 0.01"; CWT14 pdl/pdh), and 132 on earlier days. The target is already through the base price at submit. Re-anchor the target or skip with a clear reason. |
| H-2 | Testing 1: L3-gap-slope-fromopen-FD re-fires on hard-to-borrow names every poll (246 "not shortable/ETB" skips on 49 symbols), which inflates the skip counts. Remember ETB per symbol per day. |
| H-3 | Marked-curve tool: thin bars at 15:52 give a false Primary trough (−$164 marked against the runner's −$91). Use the runner snapshot for troughs after 15:50. |

Educational only — not financial advice.
