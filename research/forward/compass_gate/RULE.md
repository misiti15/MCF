# Compass Gate: FROZEN 2026-11-19 (forward shadow only)

*Educational only. Not financial advice. This is research only. It places no orders, changes no config, sends nothing to the runner, and no account runs it.*

Owner, 2026-11-19: "Do want the shadow test" (Primary -14.4R on 11-19: ST7-FD longs and L3-FD inverse-ETF shorts went against
a Compass DOWN reading). This file states the rule as it stands. It is not tuned. If anything below changes, that is a new rule with a new freeze date and a new forward count. **No
stacking cap is part of this rule (the owner wants stacking kept).** Configurations tried: **1** (this rule). No variant was
scored or selected.

## 1. Compass reading ("confirmed")

- Source: the live Market Compass, the **W60** reading (`w60` column) in `origin/mcf-data-compass:compass/<date>.csv`, written by
  `mcf/report/compass_live.py`. **Confirmed** means `w60` is `UP-confirmed` or `DOWN-confirmed`: votes |v| >= 4 (SPY
  from-open sign, SPY vs VWAP, 200-name breadth vs 0.5, SPY/QQQ/IWM agreement, 60-min persistence), with persistence
  and at least 2 marks. 09:45 alone can never confirm.
- Marks run every 15 minutes, 09:45 to 15:45 (25 marks). A mark labelled T uses only bars that started before T.
- **Gaps:** the live job missed marks on some days (11-16, 11-17 and 11-19 have 1 or 2 recorded rows). A missing mark is recomputed with
  the same `compass_live.compute()` on the stored day pack (Release `bars-<YYYY-MM>`, `1min-<date>.parquet`). After
  16:15 ET only, read-only Alpaca market data can fill it (`--alpaca`). Recorded rows always win. Where both exist they are
  cross-checked (backfill: 0 mismatches in 150 marks). A session counts only when all 25 marks are present.
- **Lag:** a mark T acts on entries at or after **T + 2 min**. This is conservative: the live job needs the bar that closes at T, plus
  one poll.

## 2. Exposure direction of a trade

exposure = side (+1 long / -1 short) x beta sign of the instrument:

| class | beta sign | members (frozen) |
|---|---|---|
| long_beta | +1 | every stock and every ETF/ETP not listed below (index, sector, country, leveraged long, single-stock long, crypto ETPs such as ETHA / IBIT) |
| inverse | -1 | the `INVERSE` set in `shadow.py`: index and sector inverse ETFs (SH SDS SPXU SPXS SPDN PSQ QID SQQQ DOG DXD SDOW RWM TWM TZA SRTY SOXS TECS FAZ LABD ERY DUST JDST GDXD YANG FNGD ...), single-stock inverse ETFs (AAPD AMZD MSFD PLTD PLTZ NVD NVDQ NVDS NVDD TSDD TSLQ TSLZ MSTZ AMDD DAMD MUD MUZ SNDQ BMNZ LITZ SKDD SKHZ AVS ...), crypto inverse (BITI SBIT ETHD), BTAL |
| long_vol | -1 | VXX UVXY VIXY UVIX VIXM VXZ |
| neutral | 0 (never gated) | gold / silver / oil / natgas / broad commodity, treasury and bond, managed-futures and currency ETPs (`NEUTRAL` in `shadow.py`, e.g. GLD SLV USO UNG BOIL TLT TMF EDV DBMF UUP) |

The members were chosen by prospectus knowledge and checked on 11-13 and 11-17 1-minute data. Every listed inverse name has a
negative 1-minute return correlation with its underlying or with SPY (for example DAMD/AMD -0.95, MUZ/MU -0.94, SNDQ/SNDK -0.97, BMNZ/BMNR -0.77).
A later addition is allowed only for a symbol that is inverse or long-volatility by prospectus. Each addition is dated in this file and is never
made because of results. So a long in SQQQ is short-market. A short in SQQQ or SPXS is **long-market**, which is why L3's 11-19
shorts count as long-market bets.

## 3. Gate

- Each session starts with no gate side. The first confirmed reading sets the side. The side changes only when a confirmed reading
  appears on the **other** side (a flip). A leaning or mixed reading never clears it.
- While the side is DOWN, a NEW entry with exposure +1 is **blocked**. While the side is UP, a NEW entry with exposure -1 is
  **blocked**. Neutral instruments, entries before the gate is set, and exits of open lots are never affected.
- Blocked trades score 0 R in the gated total. Their realised R is the cost they would have avoided (or the gain they would have
  lost). Second-order effects are **not** modelled: a blocked loser cannot trip the -2R latch, freed capital and slots, other
  setups that would then have filled. The R figures understate nothing and add nothing.

## 4. Data and R

- Trades: every account journal (`git show origin/<data branch>:journal.db`: primary, testing, testing2, testingd/e/f, gen,
  graveyard, livelab, explore1). Runs of kind `whatif` / `shadow` are excluded, so BASE1 shadow rows are excluded too. Only closed trades are scored.
- R = pnl_adj / (|entry - stop| x shares). pnl_adj includes the LR8 live cost model (from 2026-11-12; before that it is the
  earlier slippage allowance, see the ledger). Costs are always in. The family is the setup prefix (`mcf.research.shadow_calib.family_of`).
- The locked block 2024-11-01 to 2025-02-28 is never read.

## 5. Pass bar (fixed now, scored once)

The forward window is sessions from **2026-11-20** onward. The 11-06 to 11-19 backfill was seen before this freeze, is
reported only, and never counts. The rule is scored once, at the first nightly run with **>= 15 complete forward sessions and >= 40 blocked
trades** (or at 40 sessions, whatever the count). PASS needs **all** of the following:

1. Blocked trades' avg R < 0, **and** trade-level t <= -1.5, **and** session-level t (per-session blocked-R sums)
   <= -1.5. Trades within one session are not independent, and the session t is the honest one.
2. Gated total R > ungated total R, for all accounts pooled **and** for Primary alone.
3. One-big-day check: the session where blocking saved the most accounts for < 50% of the total saved R, and the avg blocked R
   without that session is still < 0.
4. Per family (all accounts pooled): more families improve than get worse, and the R lost by the worse families is <= 1/3 of
   the R saved by the better ones. Per-setup better/worse counts are always reported (`--score`: setups_better /
   setups_worse, by_family, by_account).

All met: write it up as a **DECISION for the owner**. It is still never enabled automatically, it goes in the ledger, and it is not changed during market
hours. Any check missed: retire the rule. It is logged and not re-tuned on the same forward data.

## 6. Backfill (seen data, reported only: 2026-11-06 .. 2026-11-18, 9 complete sessions; 11-19 pending)

A Compass side was confirmed on all 9 sessions, mostly at the 10:00 mark. So the gate covers most of almost every day.

- All accounts: 11,765 closed trades, of which **4,344 would have been blocked**. Blocked avg **-0.030 R**. The trade-level t is -2.40, but the **session-level t is
  -0.34**. Blocked total -128.4 R (ungated -1,147.8 R, gated -1,019.4 R).
- Per session, blocked R: 11-06 -5.5, 11-09 -178.0, 11-10 +38.5, 11-11 +27.7, 11-12 +165.4, 11-13 +125.9, 11-16 -210.4, 11-17
  -73.7, 11-18 -18.3. The best session (11-16) accounts for **164%** of the saved R. **Without it the blocked trades average +0.023 R**, which means
  the gate would have cost R. This is a one-big-day record.
- Primary: 238 of 446 trades blocked, blocked total -27.9 R, so Primary would have gone from -44.4 R ungated to -16.5 R gated. That figure is carried by
  11-06 / 11-09 / 11-11 (MF2 -21.7 R, MF4 -25.1 R, RW5 -9.5 R, RW3 -5.1 R blocked) and is offset by **L3 +32.5 R blocked** (L3's
  counter-Compass trades were mostly winners: 11-12 alone had 120 L3 blocked trades across accounts, +61.4 R) and ST7 +1.4 R.
- Families: 25 better, 22 worse. Worse families lose 216.0 R and better families save 344.4 R. Setups: 101 better, 98 worse.
- If this had been the scored window, it would **FAIL** checks 1 (session t), 3 (one big day) and 4 (families).
- Rule-change context inside the window (research/ledger.jsonl): Primary ran TEAM-6 from 11-11 (open-ended from 11-16). On 11-12 came LR3
  (latch and halt count R after costs), LR8 (live cost model in pnl_adj), Testing per-setup cap 10 -> 30, Gen and Graveyard
  sizing and caps, and the account halt raised to 300 R outside Primary. On 11-17 came TSZ1 (Testing half-size lots, 2x slots, cap 100) and the Workbench copies
  L3-*-WB4 and ST7-WB1 in Testing A/B/C/F, plus RW3/RW5 WB4 swaps. 11-19: NS5 moved Primary -> On Deck, C3 epoch/BASE1, U9-TGT, DQ-P4. So
  per-account R before and after 11-12 / 11-17 is not like-for-like. R stays comparable but dollars do not.

## Running it

    python research/forward/compass_gate/shadow.py --date YYYY-MM-DD [--alpaca]   # idempotent per date (upsert)
    python research/forward/compass_gate/shadow.py --backfill                     # every session with Compass marks
    python research/forward/compass_gate/shadow.py --score [--start 2026-11-20]   # tally + pass-bar status

Nightly (after 16:15 ET, preferably after store-bars at about 16:40 ET):

    python research/forward/compass_gate/shadow.py --date $(TZ=America/New_York date +%F) --alpaca --score

`forward.csv` has one row per closed live trade: date, account, setup, family, trade_id, symbol, side, inst_class, exposure, entry/exit
ET, gate_side and gate_since at entry, last W60 at entry, blocked (1/0; blank = marks incomplete), R. `days.csv` has one row per
session: mark counts (recorded / recomputed / mismatches), first confirm, gate timeline, blocked count and R, status.
Day packs are cached in `.cache/packs/` (git-ignored).
