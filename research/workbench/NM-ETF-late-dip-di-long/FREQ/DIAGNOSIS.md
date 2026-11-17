# FREQ diagnosis: why Late-Day ETF Dip Buy (`NM-ETF-late-dip-di-long`) trades only ~1.1 times per session
Mechanic, 2026-11-17 (owner request 2026-11-16 ~22:15 ET: "everything looks great, we just need it to be more active").
Research files only: no config change, nothing deployed. Educational only — not financial advice.

**Rule changes inside the windows used here (research/ledger.jsonl):** GX1 lab clock gate from 2026-10-27 (before it, lab
setups were evaluated only when the 1-minute bar count was a multiple of 5); ST-P per-setup -2R latch in Primary from 10-29;
CF cost filter (stop-exit cost > 0.15R skipped) in Testing accounts from 10-30; ROLL1 move Testing 2 -> Live Lab (Testing C)
from 11-05; TEAM-6 move Live Lab -> Primary from 11-11; LR3 / LR8 cost-based R in Primary from 11-12; TSZ1 testing half-size
lots from 11-17 (R comparable). The setup's live record spans all of these: 10-19..11-04 Testing 2, 11-05..11-10 Testing C,
11-11..11-16 Primary.

## Q1. Blocked signals — is another setup stopping it?
Sources: every account journal (signals + trades, run_id 1; run_id 2 = the runner's own what-if of skipped signals), the
frozen `setups/<day>.json` (active every session 10-19..11-16), the poll logs (`polls/<day>/*.jsonl.gz`, from 10-22), and
the replay of the live sessions (this job's engine, which reproduces every one of the 27 live signals).

| | Count (21 sessions) | Per session |
|---|---|---|
| Signals the replay finds (isolated, no caps) | 32 | 1.52 |
| Live signals logged | 27 | 1.29 |
| Live trades | 23 | 1.10 |
| Logged but skipped | 4 (15% of logged) | |
| Never logged (silent) | 5 | |

| Signal | Cause | What-if R gross / after costs (replay, LR8) | Journal what-if (run 2, gross) |
|---|---|---|---|
| GDXU 2026-10-28 14:55 | spread 34 bps > 30 max (Testing 2) | +2.42 / +2.39 | +0.75 |
| LABD 2026-11-02 14:55 | Testing cost filter CF: stop-exit cost 0.24R > 0.15R | −0.20 / −0.39 | −0.37 |
| SOXL 2026-11-05 14:30 | **opposite side held**: `CWT09-gapdn-vwaploss-g10-short` "Gap-Down VWAP Loss Short (10% gap)" was short SOXL (Testing C) | +0.61 / +0.60 | +0.50 |
| GDXU 2026-11-10 14:00 | spread 34 bps > 30 max (Testing C) | +0.39 / +0.38 | +0.47 |
| GDXU 2026-10-20 14:25 | silent: pre-GX1 clock gate (no poll log that day) | −0.82 / −0.84 | — |
| SOXS 2026-10-20 15:00 | silent: the 15:00 bucket was never evaluated (last signal of ANY setup 14:51) | +0.34 / +0.28 | — |
| GDXU 2026-10-22 14:05 | silent: pre-GX1 clock gate (GDXU 4 missing minute bars; no 14:05 evaluation for any setup) | +0.20 / +0.18 | — |
| LABU 2026-10-22 14:40 | silent: pre-GX1 clock gate (LABU ~80 missing minute bars) | +0.55 / +0.54 | — |
| LABU 2026-10-28 15:00 | silent: data (LABU minute bars late / missing 14:42-15:05 in the poll log) | +0.16 / +0.15 | — |

Totals: skipped 4 = +3.22R gross / +2.99R after costs (replay; the GDXU 10-28 fill sits close to the stop, so its R is
large; the runner's own what-if says +1.35R gross for the four). Silent 5 = +0.43 / +0.30R.
**None of these were caused by** max positions, slots, buying power, the per-setup cap (30), the -2R latch, the window or
a twin group. In Primary (11-11..11-16) 5 of 5 signals traded, 0 blocked.

**Another setup:** once — `CWT09-gapdn-vwaploss-g10-short` (Gap-Down VWAP Loss Short (10% gap)) in Testing C; it is now in
On Deck, not with this setup. Cross-check against Primary's journal: on 11-10 (the setup was still in Testing C)
`L3-gap-slope-rsi5hi-FD` and `L3-gap-slope-fromopen-FD` were short SOXL at 14:26, so in Primary that SOXL dip (+0.51R)
would have been skipped "opposite side held". Across the 32 replay signals that is 1 in Primary (3%) and 2 in the
accounts it actually ran in. Primary setups held these ETFs during 14:00-15:00 on 41 lot-windows since 10-19, mostly
shorts (RW5 14, RW3 6, L3-fromopen 5, MF2-FD 5, L3-rsi5hi 4) — a real but small source.
**Proposed fix: none now.** An account cannot hold the same symbol long and short, so the only remedies are priority
(would block the short instead) or a reserved symbol — both are owner decisions with no evidence they pay; at ~3% of
signals it is not where the frequency is. The GX1 fix (10-27) already removed 4 of the 5 silent misses. The spread skips
are GDXU only (a thin 3x ETN, ~34 bps); the filter is doing its job (2 what-ifs, both green, too few to argue).

## Q2. Universe — which ETFs, and would more help?
The list is the module's own `SYMBOLS` (124 index / sector / leveraged ETFs, swarm 2026-10-17, `symbols: module` in the
YAML). The real narrowing is the **ATR >= 3.6% of price** sensor: only 37 of the 124 have a median ATR above it, so the
setup is in practice a 3x-ETF / gold-miner setup. 2-year trades per ETF (parent): SOXS 76, SOXL 62, GDXU 47, TECL 31,
LABU 30, TNA 22, TQQQ 21, TZA 18, LABD 17, SQQQ 17, NUGT 15, DUST 14; 80 of 124 ETFs traded at least once. Live signals:
SOXL 7, SOXS 5, TECL 3, GDXU 2, LABD 2, SQQQ 2, TZA 2, GDXJ / TNA / QLD / TQQQ 1 (27).
Note: 24 of the 124 (FAS, FAZ, ERX, DUST, JNUG, TECS, LABU, FNGU, SRTY, URTY, ...) were missing from the old 1,226-symbol
cache, so the first Workbench pass scored the parent on 104 ETFs. This job fetched them (read-only SIP, locked block never
fetched): the complete parent has 561 2-year trades (+0.117R) vs 480 (+0.125R) before. All numbers here use the complete
parent.

Wider sets, each added alone (2-year avg R / trades per session; parent +0.117 / 1.30):
- 1x equity ETFs (81: sector, industry, country, size/style, ADV >= $95M): +0.110 / 1.35 — barely adds (ATR too low).
- Leveraged index / sector not in the list (ADV >= $95M: only KORU, TMF): +0.110 / 1.40; with ADV >= $40M (+USD, NAIL,
  YINN, TMV, GDXD, ZSL, ETHU): +0.083 / 2.27, worst day −13.4R.
- Single-stock leveraged ETFs (NVDL, TSLL, MUU, AMDL, MSTU, ...): +0.037 / 2.52 — the mechanism does not transfer.
- Commodity ETFs: +0.092 / 1.52. Crypto ETFs: +0.106 / 1.40. VIX ETPs excluded (contango decay, different mechanism).
- Large-cap stocks (ADV >= $1B): +0.038 / 3.41, worst day −35R — does not transfer.
- ADV floor $50M on the same list (adds NUGT, URTY, ... days): +0.117 / 1.68, total R 65.6 -> 85.0, but the 2-year worst day
  −8.97R (12% worse) and the replay gain only +16%.
Twins: the other index-dip setups (IDX1 / LD2 / LD6 / LD8, TQQQ / SPXL) trade 09:50-10:30 only — no overlap with 14:00-15:00.
**Verdict on Q2: more tickers alone does not do it** — every wider set dilutes avg R and worsens the worst day, because
the extra names all sell off together on the same late-day drops.

## Q3. Rules that limit frequency
- **One entry per symbol per day (refire false)** — the parent ignores every later dip on SOXL/SOXS after the first.
  Live refire (cooldown 1 bar, stacking under max_lots 3) alone: 2-year 1.30 -> 1.48 / session, +0.129R, total +82.8R, but
  the replay avg R drops (+0.271) and w/o best day fails.
- **DI(7) >= 0** — DI >= −5: 1.64 / session but avg +0.097, worst day −12.0R; no DI: 4.5 / session at +0.048R.
- **15-min dip <= −0.80%** — −0.70: 1.72 / session at +0.082R; −0.60 / −0.50: worse.
- **ATR >= 3.6%** — 3.0 / 2.5% add almost nothing (low-ATR ETFs rarely dip 0.8% in 15 min).
- **Window 14:00** — from 13:30: +0.031R (the 13:30-14:00 dips lose); from 13:45: +0.090R. The end cannot move past 15:00
  (LabStrategy caps bar closes at 15:00). 15:00-bar entries are already weak (parent −0.196R on 36).
- **The key interaction:** the loosened parts fail alone because the extra dips include "falling-hour" dips (60-min return
  below −1%) — the same failure mode WB1 found. Adding a mild falling-hour guard (ret12 >= −1.0%, much looser than WB1's
  +0.5%) lets DI −5, dip −0.75% and refire add trades without the losers: that is WB4.
- Cluster caps (at most N entries per bar) cut the worst days but also the April-2025 rebound clusters: total R falls (fail).
