Educational only — not financial advice

# U9 Execution leaks: short borrow skips and target/stop rejects — results (2026-11-18, research only, market hours)

**Headline: the ETB skips cost no R. The real leak is entries sent when the price has already passed the target or
the stop.** Over 32 sessions MCF journaled 9,237 `not shortable/ETB` skips (5,986 unique account/day/setup/symbol,
443 names). That is the biggest skip reason, but it does not take a slot or the "next candidate". The borrow check
runs before every position and trade cap and each symbol is checked separately, so the setup already moves on to the
next name. The 09:08 pre-open flags matched every live skip (0 intraday flips seen). The fix is housekeeping:
fewer journal lines and fewer broker lookups, with **no change in R or reps**.

The leak that does cost R: entries whose quote was already at or through the target or the stop. 226 brackets
were rejected by the broker (no trade, R 0). Another **115 filled and lost -65.3R** (96 at the target, -8.5R;
19 at the stop, -56.9R). A quote check before the order removes them. Re-pricing the rejected ones (B2, re-anchor)
**fails** (check sessions -0.48R/trade, t -3.96).

Nothing was changed or deployed. The code is a patch file (`fix.patch`, with tests: 9 new, full suite green). It
needs the owner's yes after hours.

Configurations scored: **4** (W1 ETB as-if, B1 target-at-quote, B1 stop-at-quote, B2 re-anchor). Bar
t ≥ max(1.5, sqrt(2 ln 4)) = **1.67**. Pre-registration: PLAN.md (commit 435a4161c, before any R). Fit = sessions
≤ 10-22, check = sessions ≥ 10-23. Data: live journals of all 10 accounts (signals + trades, as journaled),
1-minute raw SIP bars (GET only), borrow snapshots (09:08 on 11-04 / 11-05, plus one GET at 13:15 ET today). R after
costs (LR8). The locked block was not read.

## 1. What leaks (counts, 2026-10-06..11-18)

| Account | ETB skip rows | unique | short submits (unique) | ETB-blocked share | broker take-profit rejects | broker stop rejects | insufficient BP rejects |
|---|---|---|---|---|---|---|---|
| Primary | 2,544 | 719 | 993 | 42% | 0 | 0 | 0 |
| On Deck | 2,431 | 1,302 | 2,816 | 32% | 5 | 7 | 0 |
| Testing A | 1,153 | 977 | 1,742 | 36% | 165 | 13 | 0 |
| Testing B | 163 | 158 | 134 | 54% | 0 | 0 | 0 |
| Testing C | 126 | 116 | 122 | 49% | 3 | 0 | 0 |
| Testing D / E / F | 51 / 80 / 75 | 51 / 79 / 74 | 120 / 199 / 306 | 30 / 28 / 20% | 2 / 1 / 2 | 0 / 0 / 1 | 0 |
| Gen | 551 | 550 | 1,387 | 28% | 10 | 21 | 1,215 |
| Graveyard | 2,063 | 1,960 | 3,614 | 35% | 38 | 2 | 709 |

ETB skips are 20.5% of all skip/reject rows, and they are growing (≈ 650/day in 11-16..11-18 against ≈ 100/day in
mid-October). The names repeat: UVIX, MUU, SNDQ, MSTU, SOXS, NBIZ, KORU, GDXU, AAOZ, LITZ, mostly leveraged or
inverse ETPs and new listings. The setups hit hardest are CWT09 gap-down shorts (78-93% of their short signals
blocked), the L3 family (62-81%) and NM1 (93%). Insufficient-buying-power rejects (Gen/Graveyard) come from
account sizing. They are out of scope here (sizing guardrail): counted, not studied.

## 2. ETB: does a skip cost a trade? (Q2, Q3, W1)

- **No slot is taken (mechanism).** In `PaperRunner._enter` the borrow test comes before `risk.check`. A skipped
  short never counts toward trades/day, positions or a setup's sleeve. Each symbol is evaluated separately on every
  poll. In 955 of the 4,456 polls with an ETB skip, the same setup submitted another name in that same poll. The
  only possible displacement is a top-N rvol rank cap (orb/orb20/vwap_pullback): 8 skips in 32 sessions
  (orb20_a, traded engine R +0.005). Bound ≈ 0R.
- **Flags are stable intraday.** On 11-04 / 11-05, none of the 114 / 130 skipped names was ETB at 09:08, and none
  of the 308 / 330 traded short names was non-ETB. On 11-18 at 13:15 ET, 0 of 46 skipped names had become ETB and
  0 of 219 traded names had become non-ETB. A pre-open list gives exactly today's decisions. The hourly refresh in
  the patch is only a safety net.
- **W1: what the blocked names would have done (R that cannot be recovered on Alpaca).** 5,817 first skips per
  account/day/setup/symbol, simplified engine (signal stop/target, flat 15:55, LR8):

| Set | n | avg R | total | t | random entries, same names |
|---|---|---|---|---|---|
| ETB-blocked, as if borrowable | 5,817 | **-0.086** | -501R | -5.52 | -0.154 |
| Same setups' traded shorts (same engine) | 10,784 | -0.108 | | | -0.105 |
| Same traded shorts, live journal R | 10,784 | -0.119 | | | |

  Overall the blocked names are slightly better than the traded ones (+0.02R/trade) but negative: **being blocked
  avoided about -500R** in this simplified engine. Per setup (45 setups with ≥ 20 skips): blocked names were better
  in 22 and worse in 23 (median difference -0.002R). Only 4 pass "as-if avg > 0, t ≥ 1.5, w/o best day > 0":
  L3-gap-slope-rsi5hi-FD (+0.077, t 2.75, w/o best +0.042, best day 51%), MF3-open-flowsell-rsi5hi-FD,
  RW3-gapdn-rsi5pop-flowsell-short-FD, NS3-failed-vwap-reclaim-short. For the last three, random entries on the
  same names score about as well (+0.21 / +0.24 / +0.23), so the gain comes from the names drifting, not from the
  setup's timing.
- **Protected setup L3-gap-slope-fromopen-FD:** 76% of its short signals are blocked. The blocked names score
  +0.055 as if borrowable (t 1.26; w/o best day -0.014; best day = 121% of the total) against +0.223 engine /
  +0.236 live on the names it traded. The borrow block is not hurting its live record. Its research record
  (which includes these names) understates live.

Full table: `u9_w1_etb_by_setup.csv`.

## 3. Target / stop already passed (W2, B1)

| Config | Sessions | n | Effect | t | w/o best day / best-day share | vs random |
|---|---|---|---|---|---|---|
| B2 re-anchor rejected brackets (shift stop + target to the broker price) | fit | 168 | +0.033R/trade | 0.59 | -0.023 / 155% | +0.015 |
| | **check** | 55 | **-0.483R/trade, -26.6R** | **-3.96** | -0.606 | -0.255 |
| B1 skip when fill-side quote is at/through the target (R gain = live R of the fills removed) | fit | 45 | +3.15R | 1.52 | | |
| | **check** | 51 | **+5.32R (+0.104/trade)** | **2.32** | best day 61% (`1 day`) | |
| | all | 96 | +8.47R, 23 days | | +5.24R w/o best day, share 38% | |
| B1 skip when exit-side quote is at/through the stop | fit | 11 | +37.0R | 5.76 | | |
| | **check** | 8 | **+19.9R** | **8.24** | | |
| | all | 19 | +56.9R, 9 days | | +30.7R w/o best day, share 46% | |

- **Per setup.** B2 helps 11 setups (+10.9R) and hurts 14 (-31.9R): FAIL. B1-target helps 15 setups (+8.98R),
  hurts 4 (-0.50R). B1-stop helps 11 (+56.9R), hurts none. Mostly CWT14 failbrk (orl/pdl/pdh), plus CWT09
  vwaploss, heat_fade and MF1. Files: `u9_w2_target_by_setup.csv`, `u9_b1_quote_target_by_setup.csv`,
  `u9_b1_quote_stop_by_setup.csv`.
- **Mechanism.** Both cases are fixed by construction. If the fill-side quote is already through the target, the
  take-profit fills at once for at most 1 cent of upside. If the exit-side quote is at the stop, the trade is
  stopped out at once. R is measured on the fill-to-stop distance, so the stop-case R is large per trade (-3.0R
  average) while the dollar loss is small.
- **Research-vs-live gap.** A bar-close engine credits the 223 rejected brackets with **+0.42R each (+94R)**,
  mostly CWT14 orl/pdl (targets ~0.4R from the signal close). Live cannot get these. CWT14 research records are
  overstated by that amount (no new CWT14 variant is proposed).

## 4. The fix (fix.patch — not applied, not committed to the code tree)

- **(a) U9-ETB, `shorts.borrow_prefetch` / `borrow_refresh_min: 60`.** `AlpacaBroker.load_borrow()` makes one
  read-only GET /v2/assets and fills the `can_short` cache for every listed symbol. Unlisted names keep the
  per-symbol GET; a failed load leaves the per-symbol path in place, with 3 tries and no exception.
  `PaperRunner._refresh_borrow` runs at the first entry poll and then every hour. A short-only setup journals a
  non-ETB name once per day and then draws no further signals there (`_borrow_blocked`). Both-sided setups keep
  today's path, journaled once per day. Same trades as today.
- **(b) U9-TGT, `live.skip_passed_at_quote`.** In `_realism`, after the live quote and after the existing spread
  and cost checks (so their reasons keep priority), the entry is skipped with `target passed at quote` or `stop
  passed at quote`, and no order is sent. The shadow book uses the same check.
- **Tests.** `tests/test_u9_execleaks.py` has 9 tests: bulk load and cache, refresh and failure, short-only
  blocking, once-per-day journaling, long/short target and stop quote checks, flags off = today, config defaults.
  Full suite in the scratch worktree with the patch applied: **771 passed, 1 skipped, 0 failed**.

## 5. Expected gains (31 sessions measured, costs in)

| Decision code | Change | Expected R | Reps | Notes |
|---|---|---|---|---|
| **U9-ETB-YES** (after hours) | patch (a) | **0R** (mechanism + Q2/Q3) | 0 | ≈ 300-650 fewer journal rows and up to ≈ 640 fewer per-symbol broker GETs per session in the entry path. Cleaner playing-time / capture stats |
| **U9-TGT-YES** (after hours) | patch (b) | **+0.27R/session** target part (+8.5R / 31), **+1.8R/session** stop part (+56.9R / 31, inflated in R units by tiny fill risk) | -3.7 fills/session, all with no upside | 226 broker rejects become clean skips (R unchanged) |
| **U9-TGT-B2-NO** | re-anchor rejected brackets | -0.48R/trade on check | | FAIL |
| **U9-RES** (research note for C3-MECH) | ETB-only short universe in backtest / generator / promotion screens | — | — | blocked names are mixed per setup (22 better / 23 worse). L3-fromopen research understates live; CWT14 bar-close credit +94R that live cannot get |

Limits: the simplified engine has no trailing or time stops and no scale-outs. It fills the stop at the stop
price unless the bar opens through it. B1's gains are in-sample removals of trades with zero upside by
construction, not a forecast of setup behaviour. Two borrow snapshots and one intraday read are a short base for
"no flips". The promotion hold is unaffected: this changes execution only, not any setup's lineup.
