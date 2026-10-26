# Exposure and trade counts: do we need more paper accounts? (2026-10-26)

*Educational only — not financial advice. Research only: nothing that trades was changed. Numbers are live paper
journals (`git show origin/<branch>:journal.db`, `setups/<day>.json`, `status.json`), read by
`research/ops/exposure1026/exposure.py` (output `research/ops/exposure1026/results.json`). Every trade carries the
usual cost model; this note only counts trades, it does not judge any setup's R.*

## Answer first

- **Caps are not the bottleneck, and neither is the number of accounts. Rare signals are.** In the last 5 sessions
  the slot / per-setup / trades-per-day caps blocked **0 signals** in Primary, Testing 1, Testing 2 and Gen. The only
  real cap losses were in the **Graveyard**, whose caps are set low on purpose (25 per setup: 210 signals in 4
  sessions, 171 of them on its first day; plus its per-setup −2R stop: 522).
- **The slow setups are slow because they hardly fire.** Of the 85 live setups with 0–2 live trades in their
  current account, **67 have never journaled a signal there** (Testing 1: 7 of 11, Testing 2: 12 of 19, Gen: 47 of
  53). Their other signals were lost to borrow (ETB), spread, or the split-tape gate. Caps blocked none of them. More
  accounts give these setups no extra reps.
- **What an extra account could recover:** signals lost because another setup held the symbol (lot cap of 3 / twin /
  opposite side). Over 5 sessions that was **~38/day in Testing 1** (49 lot-cap on 10-26 alone), ~5/day in Testing 2
  and ~7/day in Primary. Almost all of it is in busy setups that already have 30+ trades.
- **Recommendation: `EXP wait`.** Run one week (10-27..10-31) with GX1 (clock gate) and GX2 (Gen caps). Then
  re-check the triggers in section 6. A Testing 3 split would add ~20–40 trades/day, mostly to setups that already
  have 30+ trades. A second Generator account adds nothing until Gen itself runs out of room: today it peaked at 23
  open positions against a 200 cap.

## 1. Per account, last 5 sessions (10-20, 21, 22, 23, 26)

"Trades" = journaled paper entries (= submitted orders; every submitted signal became a trade row).
"Caps" = slots full + per-setup cap + trades/day cap. "−2R" = the per-setup daily loss stop (Testing 1/2 and Gen
turned it off on 10-22 evening, owner ST-A; Graveyard keeps it). "Held" = symbol held by another lot / lot cap (3) /
twin / opposite side, with the lot-cap part in brackets. "ETB" = not shortable. Peak gross = the largest sum of
entry × shares open at one moment.

| account | day | signals | trades | caps | −2R | held (lot cap) | ETB | spread/quote | peak open / slots | peak gross |
|---|---|---|---|---|---|---|---|---|---|---|
| **Primary** (160 slots, 100/setup) | 10-20 | 88 | 70 | 0 | – | 5 (1) | 2 | 11 | 41 / 160 | $76k |
| | 10-21 | 115 | 46 | 0 | – | 3 (2) | 49 | 17 | 30 | $56k |
| | 10-22 | 196 | 126 | 0 | – | 21 (15) | 20 | 28 | **82** | $147k |
| | 10-23 | 48 | 32 | 0 | – | 3 (0) | 3 | 10 | 12 | $22k |
| | 10-26 * | 28 | 22 | 0 | – | 1 (0) | 1 | 4 | 9 | $17k |
| **Testing 1** (400 slots, 150/setup) | 10-20 | 825 | 266 | 0 | 75 | 112 (76) | 296 | 69 | **148** / 400 | $129k |
| | 10-21 | 360 | 199 | 0 | 9 | 9 (1) | 21 | 46 | 90 | $79k |
| | 10-22 | 365 | 113 | 0 | 175 | 7 (0) | 17 | 49 | 28 | $25k |
| | 10-23 | 202 | 131 | 0 | – | 9 (5) | 23 | 26 | 46 | $40k |
| | 10-26 * | 305 | 136 | 0 | – | 55 (49) | 92 | 9 | 72 | $64k |
| **Testing 2** (400 slots, 50/setup) | 10-20 | 259 | 142 | 0 | 14 | 4 (4) | 13 | 62 | 42 / 400 | $36k |
| | 10-21 | 151 | 91 | 0 | 1 | 1 (0) | 36 | 18 | 33 | $29k |
| | 10-22 | 257 | 138 | 0 | 59 | 6 (0) | 23 | 25 | 60 | $51k |
| | 10-23 | 220 | 147 | 0 | – | 11 (7) | 28 | 33 | 39 | $34k |
| | 10-26 * | 167 | 136 | 0 | – | 3 (0) | 17 | 11 | **88** | $77k |
| **Graveyard** (200 slots, 25/setup, −2R on) | 10-21 | 714 | 347 | **171** | 62 | 49 (19) | 25 | 60 | **135** / 200 | **$247k** |
| | 10-22 | 710 | 281 | 28 | **233** | 36 (7) | 40 | 91 | 85 | $153k |
| | 10-23 | 584 | 274 | 9 | 186 | 24 (8) | 20 | 67 | 113 | $204k |
| | 10-26 * | 313 | 193 | 2 | 41 | 25 (5) | 27 | 25 | 108 | $193k |
| **Gen** (80 slots / 16 per setup to 10-23; 200 / 48 from 10-26) | 10-20 | 10 | 6 | 0 | – | 0 | 0 | 4 | 5 / 80 | $24k |
| | 10-21 | 16 | 13 | 0 | – | 0 | 3 | 0 | 10 | $47k |
| | 10-22 | 7 | 4 | 0 | – | 0 | 0 | 3 | 3 | $14k |
| | 10-23 | 59 | 51 | 0 | – | 1 | 1 | 6 | **44** | **$207k** |
| | 10-26 ** | 28 | 24 | 0 | – | 0 | 0 | 4 | 23 / 200 | $43k |

\* 10-26: GitHub missed the schedule, so every account's first signal was ~10:40 ET instead of 09:50.
\*\* Gen also crashed (numba) and traded only from 12:02 ET (first signal 12:10).
Testing 1 on 10-21/23/26 also lost 73 / 13 / 9 signals to the split-tape short gate (not a cap).
Graveyard went live 10-21. Gen's 10-20..22 were before the poll fix (genexposure1025).

**Buying power.** Equity is ~$96–101k in each account. Peak gross was **$247k (2.5× equity) in the Graveyard on
10-21**, $207k in Gen on 10-23 (80-slot sizing, ~$4.7k a slot), and $147k or less everywhere else. No journal has a
buying-power reject. One limit to watch: by the slot rule each account's full-slot notional is equity ×
`buying_power_multiple`. That is 3.2× = ~$309k for Primary and 3.8× = ~$380k for the other four, above the ~$321k
intraday buying power quoted in `config/default.yaml`. It cannot bind until ~85% of the slots are full, which no
account has come close to.

### Per-setup cap, closest calls
Testing 2 `CWT12-coil-k4-long` reached **49 of its 50** open on 10-26. Graveyard `CWT14-failbrk-orl-p05-long` sat
at 25 / 25 on 10-21. Primary's highest was 24 / 100, Testing 1's 66 / 150, Gen's 18 / 48 on 10-26 (above the old 16).

## 2. Trades per day: 5-session average, the 10-26 late start scaled, then GX1

**Late-start scaling.** On 10-20..23, this share of each account's submitted signals came before the time it started
on 10-26: Primary 20%, Testing 1 44%, Testing 2 40%, Graveyard 48% (before 10:40), and Gen 66% (before 12:10, from
only 92 signals). A full 10-26 ≈ the 10-26 count ÷ (1 − that share). This is rough, for three reasons. Lab setups
only act on the latest bar, so missed morning signals are lost, not caught up later. Some setups refire later and
partly make up for it. And the share comes from 4 days.

| account | trades/day, 5-session average (actual) | with 10-26 scaled to a full day | GX1 replay uplift (from 10-27) | expected trades/day with GX1 |
|---|---|---|---|---|
| Primary | 59 | 60 (10-26: 22 → ~28) | +57% | **~95** |
| Testing 1 | 169 | 191 (10-26: 136 → ~245) | +39% | **~265** |
| Testing 2 | 131 | 149 (10-26: 136 → ~227) | +51% | **~225** |
| Graveyard (4 sessions) | 274 | 319 (10-26: 193 → ~373) | +20% | **~380** |
| Gen | 20 (10-23 + 10-26 only: 51 and ~71 → ~61) | – | +26% | **~75** (GX5: ~150 signals/day expected before caps → up to ~125) |
| **All five** | **~650** | **~780** | | **~1,040** |

GX1 uplifts are from `gx1clockgate1026.md` (replays of 10-19..23). They give extra reps, not better trades: there,
the added trades averaged −0.002 R (Primary), +0.065 (T1), +0.016 (T2), −0.184 (Graveyard) and −0.018 (Gen), with
costs in. The replay also displaced trades the old gate took (Graveyard 188, Testing 2 123), so in the Graveyard
GX1 shows up mostly as caps binding sooner.

**Peak open with GX1** (rough: peak × (1 + uplift)): Primary on a 10-22-type day ~130 / 160, the closest any
account gets. Testing 1 ~205 / 400, Testing 2 ~135 / 400, Graveyard ~160 / 200 (its 25-per-setup cap and −2R stop
bind first), Gen ~60 / 200. Testing 2's `CWT12-coil-k4-long` will hit its 50 cap.

### GX2 (Gen caps 80 → 200 slots, 16 → 48 per setup, live 10-26)
Today GX2 changed little. Gen peaked at 23 open. Only one setup went past 16 open
(`GEN-261020-05-…-LUNCH-…-long`, 18 trades, 18 open at once), so under the old caps 2 of today's 24 trades would
have been blocked. GX2's real effects:
1. Slots are smaller: ~$1.9k instead of ~$4.75k, so peak gross fell to $43k from $207k on 10-23.
2. Headroom: on a 10-23-type day with GX1 and the 10–20 setups added per generator run, Gen would have filled the
   old 80 / 16.
3. The 10-26 window was 12:02–15:50, about a third of a session. Scaled, today is ~71 trades, in line with 10-23's 51.
   It is too early to say whether GX5's ~150 signals/day shows up.

## 3. Per setup: live trades so far and pace to 30

Counts are trades in the setup's **current** account only. Trades from before a move are not added. Pace =
trades in the last 5 sessions ÷ sessions it was enabled there. Setups with 30+ trades: Primary 4 of 12,
Testing 1 10 of 33, Testing 2 3 of 45, Graveyard 11 of 22, Gen 0 of 63.

**0–2 live trades (85 setups):**
- **Primary (1):** `ST7-rsi50dn-long-pm-t1s1-FD` (0, live 1 session, no signal yet).
- **Testing 1 (11):** `MF1-945-flowsell-vwapup` 0, `RW6G1-ns2-up3-vwap2sd-short` 0 (non-FD twin), `IDX1-qqq100-0955-TQQQ-trail`
  0, `IDX1-qqq100-0955-TQQQ-hold` 0, `IDX2-spy075-0945-3x-trail` 0, `IDX3-spy075-0955-3x-trail` 0,
  `IDX5-spy050-0945-3x-trail` 0, `ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD` 0, `LIQ-pdl-sweep-open15-vwap-long` 1,
  `ST3-rsi5up-short-pm-t1s1-FD` 1, `ST5-pdbrkup-short-mid-t05s1-FD` 2. Their signals over all time: 28 (split-tape gate 10, ETB 6,
  symbol held 5, taken 4, spread 2, rejected 1).
- **Testing 2 (19):** all 8 `LD1..LD8` breadth/index-turn longs 0, `NM-RWR1-exh150-gapdn-spyup-pm-short` 0,
  `NM-AMS-N1-quiet-morning-short` 0, `NS3V1-am-widestop-short` 0, `MF5-flowsell-vwapup-rsi5hi` 0,
  `CWT04-backside-lh-a25-short` 0, `CWT04-backside-vwaptest-a25-short` 0, `CWT04-backside-lh-a15-short` 1,
  `NM-PM-gapdn-above-pdh-rvol-short` 1, `NM-RWN3-ns3-spyup-early-short` 2, `NM-RWR3-ns3-qqqup-early-short` 2,
  `NM1-cwt09-g10-vwaploss-short` 2. Their signals over all time: 27 (ETB 9, taken 8, spread 5, held 4, −2R 1).
- **Graveyard (1):** `CWT09-gapdn-vwaploss-g5-short` 1 (live 1 session). Next slowest: `ST1-ordn-long-pm-t05s1-FD`
  3 trades (36 sessions to 30).
- **Gen (53 of 63):** 47 have never signalled live (including all 10 GEN-261026 setups added today, 3 GEN-POD1022
  setups, and every GEN-261019/20/21 setup except the ones listed below).

**Slowest setups that do trade (sessions to 30 at the current pace):**

| sessions to 30 | setups |
|---|---|
| 100+ | T1 `ST3-rsi5up-short-pm-t1s1-FD` (145), T1 `ST5-pdbrkup-short-mid` (140), T1 `ST6-volspikeup-short-mid` (130); T2 `NM-PM-gapdn-above-pdh-rvol-short` (145); Gen `GEN-261019-01` (145), `GEN-261019-03` (135) |
| 40–100 | Primary `NS1-rsidip-rsi5pop-long` (55); T1 `ST4-emadn-long-am` (45), `MF3-open-flowsell-rsi5hi` (40); T2 `NM1-cwt09-g10-vwaploss-short` (70), `CWT09-gapdn-vwaploss-g10-short` (65), `NM-HL-T75-pm-long` (55), `CWT05-flush-m075-v3-long` (50), `CWT04-backside-vwaptest-a15-short` (40); Gen `GEN-261022-08` / `-10` (87), `GEN-261020-04` (70), `GEN-261023-07` (58), `GEN-261019-04` / `GEN-261020-08` (45) |
| 20–40 | Primary `NS5-sma50-flush-oversold-long` (20); T1 `ST8-volspikedn-long-pm` (37); T2 `NM-ETF-late-dip-di-long` (31), `NS5-…-FD` (26), `NM-RWR4-…-short` (25); Graveyard `ST1-ordn-long-pm` (36), `CWT09-gapdn-vwaploss-g5-short` (29); Gen `GEN-261021-09` (36) |
| no pace (0 trades in their last 5 sessions but some before) | Primary `MF2-open-rsimidhi-flowsell` (4), `MF4-h40-open-flowsell` (21); T2 `NM-RWN5-…` (5), `CWT13-vwapstretch-z075-long` (8), `CWT05-flush-m05-v5-long` (4), `CWT05-flush-m075-v5-long` (3) |

None of these lost a signal to slots or a per-setup cap in the 5 sessions. GX1 helps them by about the account's
uplift (+20–57%), which takes a 145-session setup to ~95–120: still months.

## 4. Where the lost signals go (5 sessions, all accounts)

| reason | signals | would another account recover them? |
|---|---|---|
| Not shortable (ETB) | ~760 | No: same broker borrow list in every account |
| Spread / quote / size (realism) | ~680 | No: same tape |
| Per-setup −2R stop (now Graveyard only) | ~855 (522 Graveyard; T1/T2 333 before ST-A) | No: a rule, not a capacity limit |
| Graveyard 25-per-setup cap | 210 | Yes, or a cap change (owner set it low on purpose) |
| Symbol held / lot cap / twin | ~380 (T1 192, Graveyard 134, Primary 33, T2 25) | **Partly**: only when the crowding setups sit in different accounts |
| Split-tape short gate (T1) | 95 | No: a rule |
| Slots full, trades/day cap (any account) | **0** | – |

## 5. Would a 6th / 7th paper account add reps?

**Testing 3 (split the Testing setups further).** Testing 1 = Testing 2 for promotion, so a Testing 3 would have
the same weight; the split itself is a move, never a copy (promotion = move). It recovers the cross-setup symbol
crowding between whatever moves out and whatever stays. That is at most Testing 1's ~38/day and Testing 2's ~5/day,
call it **+20–40 trades/day**. The gain goes to the busy setups that crowd each other: `L3-gap-slope-fromopen-FD`,
`CWT14-failbrk-pdl-p05-long`, `RW7-gapdn-bounce-early-short-FD`, `CWT12-coil-k6-long`, all already past 30 trades.
The slow setups gain ~0 (section 3). A Testing 3 adds real reps only if it gets **new setups** that cannot fit
elsewhere. Today they all fit: Testing 1/2 use ≤ 148 of 400 slots.

**Second Generator account (Gen 2).** Gen has 63 setups and adds ~10 per generator run. It peaked at 44 open
(10-23, 80-slot era) and 23 today against 200 slots / 48 per setup, with no cap losses ever. A Gen 2 adds reps only
once Gen is full, roughly when its peak open passes ~160 or setup-cap losses appear. At ~75 trades/day expected with
GX1, that is not close. It would also need a routing rule in the generator (which account each new GEN setup goes to).

**A 6th account could add reps the day the account caps bind.** Right now that is only the Graveyard. Its caps are
deliberately half of Testing 2's, so the fix there is a cap choice, not an account.

### If the owner wants one anyway, what it needs
- **Owner:** one new Alpaca **paper** account, with its key pair added as repository secrets in the existing
  pattern: `ALPACA_TESTING3_API_KEY` / `ALPACA_TESTING3_SECRET_KEY`, or `ALPACA_GEN2_API_KEY` /
  `ALPACA_GEN2_SECRET_KEY`. Market data stays on the primary SIP keys. Also: the list of setups to move (or "Claude
  proposes, owner approves"), and its caps (default: same as Testing 1/2).
- **Claude (one PR, outside market hours, setup-freeze applies):**
  - `.github/workflows/trade.yml`: matrix entry, concurrency group, order prefix (`mt3-` / `mg2-`), state branch
    (`mcf-data-testing3` / `mcf-data-gen2`), key mapping, skipped-while-unset check.
  - The same in `watchdog.yml` and `eod.yml`.
  - `config/account_testing3.yaml` (or `account_gen2.yaml` with `strategies_exclusive`).
  - The account lists in `mcf/execution/session_guard.py`, `mcf/replay/{store,export,harness}.py` and
    `mcf/report/{assignments,playing_time,daily_post}.py`.
  - Dashboard `docs/live/index.html` + `report.html`.
  - Tests, `docs/OPERATIONS.md`, and a regenerated `docs/live/assignments.json`.
  - Moved setups switched off where they came from, with ledger lines.
  - Gen 2 only: a generator routing rule.
- **Costs / load:** the same cost model and per-trade risk as Testing 1/2 (costs always in). It adds one more ~6-hour
  Actions job a day and one more poller of ~3,700 symbols on the shared SIP keys. Check data-API headroom before
  adding it.

## 6. Re-check after a week of GX1 + GX2 (10-27..10-31): triggers for a new account

Add an account (or raise a cap) if any of these show up:

1. Any account's peak open above **80% of its slots** on 2+ days. The most likely is Primary at ~130 / 160.
2. **Slots-full or per-setup-cap losses above 5% of an account's signals.** Graveyard is excluded, because its low
   caps are deliberate.
3. **Peak gross above ~$300k** in any account, or any buying-power reject.
4. Symbol-held / lot-cap losses above **~50/day** in Testing 1 or 2, which would favour Testing 3.
5. Gen peak open above **~160 / 200**, or Gen setup-cap losses, which would favour Gen 2.

Script: `python research/ops/exposure1026/exposure.py` (edit `DAYS`).

*Educational only — not financial advice.*
