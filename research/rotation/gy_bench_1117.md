# GY-BENCH — Graveyard bench + guests, sessions 2026-11-18 → 2026-11-24 (built Tue 2026-11-17 after the close)

*Educational only — not financial advice. Paper accounts. R after costs = `pnl_adj / (|entry − stop| × shares)`; live journals (`origin/mcf-data-*:journal.db`, paper runs, closed trades) through the 11-17 close.*

Owner 2026-11-16 ~22:30 ET: *"pause any setup in Graveyard with over 150 trades for 5 sessions and use that space for further testing of generated setups with no action yet, or testing setups with low exposure. We'd have to figure out how to maintain the stats but too much unneeded trading is going on in the graveyard."*

## Mechanism (new: `mcf/rotation.py`)
No session-rotation bench existed in code, so two date-scoped per-setup keys were added, resolved for the session date when the config loads (runner, frozen snapshot, assignments, reports all agree):
- `benched: {from, until, reason}` — the setup sits out every session in the window and comes back by itself the session after `until`; block, rules and record untouched. The frozen snapshot (`state/setups/<date>.json`) logs it under `rotation.benched` and lists it as not enabled, so a benched session is no live session, no traded session and no per-session row (playing-time counts live sessions from the snapshot).
- `guest: {from, until, home}` in the Graveyard + `benched: {..., away: graveyard}` on the home block — the setup runs in the Graveyard only inside the window (one home per session) and goes home by itself on 2026-11-25. `tests/test_rotation.py` checks every guest/away pair matches.
- Guests keep their home account's limits: per-setup `max_stop_cost_r` (0.15R for Testing D/E/F homes, none for Setup Generator homes) and `max_setup_daily_loss_r: null` (no per-setup daily stop at home) override the Graveyard's account values for them only (`mcf/execution/risk.py`).

## 1. Benched: 18 Graveyard setups with > 150 live trades while in the Graveyard
Count used: closed live (paper-run) trades in the Graveyard journal only (`mcf-data-graveyard`), 10-21 → 11-17 close; trades from earlier accounts not counted. Next below the line: MF3-open-flowsell-rsi5hi-FD 148, NS3-failed-vwap-reclaim-short-FD 146, CWT09-gapdn-bounce-g5-lowerhalf-short 146 (stay on). The 18 took 7,664 of the Graveyard's 9,153 trades (84%) and ~570 of ~695 trades per session over 11-12..11-17.

| setup | GY trades | GY sessions | trades/session | avg R | avg R w/o best day | total R |
|---|---|---|---|---|---|---|
| `CWT14-failbrk-orl-p05-long` | 1027 | 20 | 51.4 | -0.081 | -0.114 | -82.7 |
| `CWT14-failbrk-orl-p05-lowvol-long` | 954 | 20 | 47.7 | -0.099 | -0.144 | -94.2 |
| `CWT14-failbrk-orl-p10-lowvol-long` | 639 | 20 | 31.9 | -0.062 | -0.093 | -39.3 |
| `CWT14-failbrk-orl-p10-long` | 618 | 20 | 30.9 | -0.102 | -0.131 | -63.0 |
| `CWT12-coil-k4-long` | 545 | 14 | 38.9 | -0.169 | -0.205 | -92.2 |
| `heat_fade_short-FD` | 496 | 19 | 26.1 | -0.120 | -0.194 | -59.5 |
| `CWT14-failbrk-pdh-p05-lowvol-short` | 417 | 19 | 21.9 | -0.141 | -0.165 | -58.6 |
| `CWT14-failbrk-pdl-p05-long` | 402 | 13 | 30.9 | -0.248 | -0.299 | -99.6 |
| `CWT14-failbrk-pdh-p10-short` | 369 | 18 | 20.5 | -0.181 | -0.213 | -66.7 |
| `CWT14-failbrk-pdl-p05-lowvol-long` | 332 | 13 | 25.5 | -0.189 | -0.255 | -62.7 |
| `RW2-exhaustion-noon-adv150-short-FD` | 321 | 20 | 16.1 | -0.286 | -0.351 | -91.7 |
| `ST2-slope20up-long-am-t05s1-FD` | 267 | 19 | 14.1 | -0.067 | -0.146 | -18.0 |
| `heat_fade_short` | 254 | 18 | 14.1 | -0.189 | -0.324 | -48.0 |
| `LIQ-orl-sweep-open15-s25-long` | 248 | 20 | 12.4 | -0.214 | -0.305 | -53.2 |
| `NS2-sma50break-overbought-short-FD` | 216 | 19 | 11.4 | +0.116 | -0.114 | +25.1 |
| `CWT14-failbrk-pdh-p10-lowvol-short` | 213 | 19 | 11.2 | -0.177 | -0.200 | -37.7 |
| `CWT12-coil-k6-long` | 181 | 15 | 12.1 | -0.136 | -0.251 | -24.6 |
| `heat_fade_long-FD` | 165 | 20 | 8.2 | -0.349 | -0.397 | -57.6 |

One-big-day check: NS2-sma50break-overbought-short-FD is the only positive record (+0.116R) and its best session is 165% of its total R (`1 day`, w/o best day −0.114R); every other benched record is negative with and without its best day. Nothing is retired; all 18 return 2026-11-25.

## 2. Guests: 20 setups into the Graveyard (4 a + 16 b)
- **(a)** Setup Generator setups with no live trade yet: the 4 GEN setups with 0 trades in every account (3 in Setup Generator, 1 in Testing E). Three of them are 'dormant' (≤ 1 live signal); they are cheap to host and the owner asked for them by name.
- **(b)** testing-arena setups (Testing A-F + Setup Generator, the ROT1 arena) by fewest traded sessions, then fewest trades (ties: most live signals). Left out: every Workbench copy (incl. today's 15 WB copies and NM-ETF-late-dip-di-long-WB4), the dormant index/breadth-gated IDX/LD longs and GEN-POD1022-02 (ROT1 dormant rule: more room cannot help a setup that does not signal), and CWT04-backside-lh-a25-short (kept apart from its sibling vwaptest-a25, as ROT1 did). Twins stay in separate accounts: no guest has a twin (name ± `-FD`, twin_group) in the Graveyard; GEN-261023-09's Workbench copy stays in Testing B.
- **Batch size** from projected concurrent lots: since the 300-slot / ~$460-lot regime (11-12) the Graveyard peaked at 300 lots (full) on 3 of 4 sessions; the 14 setups that keep running peaked at 26-112 lots (worst 112 on 11-13). Budget: projected Graveyard peak ≤ 200 lots (2/3 of 300 slots; ~$92k of the ~$150k buying power at 1.6×). Guests were added in rank order with each one's worst observed session peak: 20 guests = 59 lots → 112 + 59 = 171 ≤ 200; the next one, NM-RWN4-ns2-spyup05-notfri-short (peak 30), would make 201, so the batch stops at 20. Projected guest trades ≈ 46/session vs ~570/session benched.

| # | group | setup | home | traded sessions | trades | live signals | trades/session | peak lots |
|---|---|---|---|---|---|---|---|---|
| 1 | a | `GEN-261026-09-BBpctle0p3-SMA20slopege0p46-FromPCATRge0p45-LATE-BRvwgt0p6-t05s05-long` | Testing E | 0 | 0 | 3 | 0.0 | 0 |
| 2 | a | `GEN-261020-02-RSIslopelem19-BarRngATRge0p14-BuyPressge0p17-LATE-BRvwgt0p7-t05s1-short` | Setup Generator | 0 | 0 | 1 | 0.0 | 0 |
| 3 | a | `GEN-261021-08-RSI2le0-Ret15mATRge0p16-ATRdge3p6-LUNCH-QQQgt0p6-holdtr-long` | Setup Generator | 0 | 0 | 0 | 0.0 | 0 |
| 4 | a | `GEN-POD1022-01-thrasher-breadth-thrust-stocks-holdtr-long` | Setup Generator | 0 | 0 | 0 | 0.0 | 0 |
| 5 | b | `CWT04-backside-vwaptest-a25-short` | Testing D | 0 | 0 | 2 | 0.0 | 0 |
| 6 | b | `GEN-261023-01-VWAPxUp-VWAPatrge0p33-LAM-SPYgt0p5-t05s05-short` | Testing D | 1 | 1 | 12 | 1.0 | 1 |
| 7 | b | `GEN-261023-05-NewLOD-SMA20dlem0p94-ORLdistlem0p24-PM-BRopgt0p65-hold-long` | Testing E | 1 | 1 | 10 | 1.0 | 1 |
| 8 | b | `GEN-261021-10-MACDhge0p079-VWAPbarslem7-OPEN-QQQup-t1s05-long` | Testing E | 1 | 2 | 7 | 2.0 | 1 |
| 9 | b | `GEN-261029-10-RSIslopege19-Ret5mlem0p21-EMAdiffge0p29-OPEN-BRvwgt0p5-t1s1-short` | Testing D | 1 | 2 | 3 | 2.0 | 2 |
| 10 | b | `GEN-261028-03-EMAdChgge0p15-VWAPxUp-Since950ATRlem0p43-LUNCH-SPYgt0p25-hold-long` | Testing D | 1 | 3 | 47 | 3.0 | 3 |
| 11 | b | `GEN-261028-10-BarRngATRge0p18-Flow3lem0p54-FromPCATRge0p28-PM-SPYgt0p5-hold-long` | Testing E | 1 | 4 | 58 | 4.0 | 4 |
| 12 | b | `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short` | Testing E | 1 | 10 | 28 | 10.0 | 10 |
| 13 | b | `GEN-261023-02-Ret15mATRlem0p068-EMAdChgge0p028-ATRdge6-PM-BRopgt0p65-hold-long` | Setup Generator | 2 | 2 | 29 | 1.0 | 1 |
| 14 | b | `NM-RWR1-exh150-gapdn-spyup-pm-short` | Testing D | 2 | 2 | 4 | 1.0 | 1 |
| 15 | b | `GEN-261022-02-ORBfailUp-EMAdChglem0p094-ADX7ge57-LATE-BRvwgt0p7-t05s1-long` | Setup Generator | 2 | 3 | 25 | 1.5 | 2 |
| 16 | b | `LIQ-pdl-sweep-open15-vwap-long` | Testing E | 2 | 3 | 3 | 1.5 | 1 |
| 17 | b | `GEN-261021-03-RSI5le34-Ret15mATRge0p12-DayRngVsPrevge1p2-LUNCH-SPYltm0p25-t05s1-short` | Testing E | 2 | 4 | 5 | 2.0 | 3 |
| 18 | b | `GEN-261028-06-RSI5le13-VWAPatrlem0p15-DayRngVsPrevle0p34-MID-BRoplt0p35-hold-short` | Testing D | 2 | 8 | 11 | 4.0 | 7 |
| 19 | b | `GEN-261029-05-BearDiv-RSI14ge78-Compress6le0p091-AM-BRopgt0p5-t05s05-long` | Testing F | 2 | 9 | 11 | 4.5 | 8 |
| 20 | b | `GEN-261021-01-BearDiv-RVolDayle0p47-BarsSinceHODle0-LAM-SPYltm0p25-t1s1-short` | Testing E | 2 | 15 | 24 | 7.5 | 14 |

## 3. Stats
- Guests' trades stay on their own setup record (leaderboard merges by setup id; account tag Graveyard for 11-18..11-24, home again from 11-25). They are not Graveyard-origin: no `graveyard` tag, `assignments.json` marks them `guest`, `no_leaderboard` ignores a Graveyard guest coming home, and the dashboard's Graveyard filter skips them.
- Graveyard account totals in the daily post exclude the guests' P/L and trades for their window (labelled adjustment, original kept as `pnl_unadjusted`); Alpaca equity itself includes them.
- The benched setups stay assigned to the Graveyard (`assignments.json` `benched` window), keep their leaderboard rows, and add no traded sessions while benched.

## Rule / config changes inside the window (owner rule 2026-11-02)
- **11-18** this bench + guests; Record live quotes (ops, no trading change).
- **11-19 close** ROT1 block 1 ends (11-16..11-19). 12 guests are ROT1 block-1 spotlight setups (Testing D/E); block 2 must treat all 16 testing guests as away until 11-24.
- Guests trade in the Graveyard on Graveyard sizing (0.25% risk, slot ~$460 at 1.6× / 300 slots; Testing D/E/F: 0.125%, ~$500 slots — the slot binds in both, so lots are about the same size), per-setup cap 75 (home 100 / Gen 150), twin block on (no twins present); cost filter and per-setup daily stop are their home rules (above). GEN guests from the Setup Generator move from ~$540 to ~$460 lots.
- Graveyard-origin setups: rules unchanged; the guests are appended after them in `setup_order` so their priority is unchanged.

Ledger: `2026-11-18-gy-bench`, `2026-11-18-gy-bench-guests`. Educational only — not financial advice.
