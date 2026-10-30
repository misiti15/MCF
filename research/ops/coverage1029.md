Educational only — not financial advice.

# Coverage and signal funnel audit: Primary, session 2026-10-29 (OPS-AUDIT / LAB-RATE-PARITY)

Owner question (2026-10-29): "Are we confident we are constantly searching the 3,000+ tickers with our setups? It seems
coincidental that sister setups all played into the same 3 stocks (WDAY, NTSK, IOVA)."

This is a read-only audit. No config, engine, setup, ledger or backlog file was changed, and nothing was committed. The inputs are the Primary state branch
`origin/mcf-data` (journal.db, status.json, universe.csv, polls/, setups/<d>.json, earnings/<d>.json), fetched after the
16:00 close (status phase `closed`), plus SIP 1-minute bars and live-identical priors (`mcf.data.priors.build_priors`) from
Alpaca market-data GETs. Scripts are in `research/ops/coverage1029/` (`fetch.py`, `coverage.py`, `funnel.py`, `live10.py`, `summary.py`).

## Answer

1. **Yes. Every symbol in the universe is evaluated by every Primary setup at every 5-minute decision bar, and today's live signals match an
   offline recompute 35 of 35** (0 missed, 0 extra). That recompute runs the live `LabStrategy` code, with its frame build, mask, window and
   first-hit / refire rules, on the full day's bars. The same holds for all three sessions since the GX1 clock gate went live (10-27..10-29):
   92 of 92 offline signals were taken live. There were 3 live extras: CORO is not in this study's symbol list, and XLE on 10-27 is a later bar revision.
2. **The same few names recur because the conditions select few names. This is not a bug or a data gap.** RW3 ⊂ RW5, and both
   overlap MF4-FD. All three need a bearish MarcoFlow heat of −20 to −40 together with heavy net selling. RW3 and RW5 add a gap-down
   and an RSI(5) pop above 80. A name that sells off hard with a bounce trips all of them on the same bars. Today the funnel was
   643 tradable names with ADV ≥ $95M → 274 gapped down → 114 with heat ≤ −30 → 33 also with buyPressure < −0.15 → **7 also with RSI5 > 80** (RW5).
   For RW3 the last step leaves **4** (IOVA, NTSK, QLYS, WDAY, all inside RW5's 7).
3. **Over 10 sessions the setups did not keep hitting the same 3 names.** Live Primary signalled **202 distinct symbols**: RW5 84 distinct
   in 87 symbol-days, RW3 63/68, MF4-FD 62/66, MF2-FD 44/46. No symbol repeated more than 3 times. Of the 195 sister-setup symbol-days,
   52 (27%) were hit by 2 or more sisters on the same day. That overlap is what nested rules produce.
4. **There was a real bug, but it is already fixed: before 2026-10-27 live caught only 56% of the signals its own code produces** (235 of 419,
   8 setups, 10-16..10-26). The old lab gate `len(bars) % 5 == 0` skipped every decision bar of a symbol that had missed any
   minute earlier in the day. On 10-26, **every** live lab signal had a bar count ≡ 0 mod 5, and every miss after the 10:39 start had ≢ 0,
   except one (SDS, MF4-FD 12:14, not explained). GX1 (`lab_decision_buckets`, commit 7b1be77e, merged after the 10-26 close) fixed it, and the
   capture rate has been 100% since then. **This matters for LAB-RATE-PARITY.** The live rates in p2_1029 (live/backtest 0.00–0.50) come mostly from
   sessions before 10-27, so they were too low by about 44%. Those ratios should be measured again on sessions from 10-27 on.
5. **The earnings blackout is the biggest remaining reason live sees fewer chances than the 2-year lab.** It works as coded: ±4 trading days =
   a 9-weekday window (today 10-23..11-04), Nasdaq calendar, `complete: true`. It is peak earnings season, so the blackout removes 1,490 of 4,664 universe names
   (32%) and **522 of 1,165 names with ADV ≥ $95M (45%)**. In the 3 sessions since GX1, the names it removed would have added **68 signals on
   top of the 92** for the 8 setups (+74%). Today the 4 sister shorts would have taken AXTI, SFM, IBRX, MHK, CF, INFY, MSGK, GLPI and NEU. Gap-down names
   are often earnings names. **The two-year frames (`research/history2y`) do not apply the blackout** (grep finds no earnings filter). So their
   trades-per-session include symbol-days that live can never trade, and the gap is largest in earnings season.
   The rule itself is an owner rule. Nothing is changed here.

## 1. Coverage (poll log, Primary)

| | 10-29 |
|---|---|
| Universe (universe.csv) | 4,664 (core 3,552 / extended 1,112) |
| Earnings-excluded | 1,490 (core 1,327 / extended 163). Report dates 10-23: 23, 10-26: 58, 10-27: 147, 10-28: 224, 10-29: 273, 10-30: 47, 11-02: 134, 11-03: 227, 11-04: 357 |
| Watchlist polled | 3,174 (+2 later; core 2,225 / extended 949) |
| Names the 8 setups can trade (ADV ≥ $95M, not blacked out) | 643 |
| Polls | 384, 09:30:01–15:54:12, longest gap 106 s, 1 gap > 90 s, median poll 6.7 s |
| Symbols with bars per poll (09:35–15:55) | median 3,170 of 3,174 (minimum 3,084, early); at most 90 with no bar yet (early, thin names) |
| 5-minute decision minutes polled (09:49..14:59) | 63 / 63 |
| Stale-data polls | 0 |

Extended-tier names (ADV $1–5M) stay only when they are in play (opening rvol ≥ 3). None of them can pass the $95M `min_adv` that all 8 Primary setups use,
so for Primary they are polled but never eligible. Earlier sessions: 10-22, 10-27 and 10-28 had all 63/63 decision minutes polled. 10-23 missed 10:44. 10-26 started at 10:39 (10 minutes missed).
No poll log exists for 10-20 or 10-21.

## 2. Funnel per setup, 2026-10-29

Symbols at each step. Every condition must hold on the **same** 5-minute bar, inside the setup's window, and the steps are cumulative. "alone" = symbols that met that one condition
at some bar in the window. Offline = the live code on the full day's bars. A symbol can have at most one signal per day, except under MF2-FD's refire.

| setup | ADV ≥ $95M | step 1 | step 2 | step 3 | step 4 | offline sig | live sig | matched | blackout names that would signal |
|---|---|---|---|---|---|---|---|---|---|
| RW5 | 643 | gap<0: 274 | heat≤−30: 114 | bp<−0.15: 33 | RSI5>80: **7** | 7 | 7 | 7 | AXTI, SFM |
| RW3 | 643 | gap<0: 274 | heat≤−20: 239 | bp<−0.35: 41 | RSI5>80: **4** | 4 | 4 | 4 | IBRX, MHK |
| MF2-FD (refire) | 643 | heat≤−30: 296 | RSI14 55–65: 35 | bp<−0.25: **5** | | 7 | 7 | 7 | CF, INFY, MSGK |
| MF4-FD | 643 | heat≤−40: 98 | bp<−0.25: **11** | | | 11 | 11 | 11 | GLPI, MHK, NEU |
| MF4 (to 11:00) | 643 | heat≤−40: 44 | bp<−0.25: 2 | before 11:00: **1** | | 1 | 1 | 1 | – |
| ST7 | 643 | fromOpen<−1%: 165 | RSI crosses below 50: 91 | RSI≤30: 4 | bp>0: **1** | 1 | 1 | 1 | TWLO |
| NS1 | 643 | fromOpen>+2%: 159 | RSI crosses below 40: 24 | RSI5≥80: **4** | 09:50–11:30: 4 | 4 | 4 | 4 | NXT, TW |
| NS5 | 643 | fromOpen<−2%: 55 | crosses below SMA50: 7 | RSI≤30: **0** | | 0 | 0 | 0 | PLTR |

Each condition alone is common (e.g. RW5: gap<0 274, heat≤−30 296, bp 618, RSI5>80 643). It is the **combination on one bar** that is rare. The binding step is
the last one, RSI5 > 80 while heat and selling are already extreme. Across the whole day, RW5 had only 8 qualifying symbol-bars.

What happened to the 35 live signals today: 16 submitted. The 19 skipped were 6 not shortable/ETB (GGLL, UVIX ×3, TZA, AAOX), 5 spread > 30 bps (FROG, KOD, QLYS ×2, WK),
3 spread too large a share of the stop distance (DEO, AZO ×2), 4 hit the setup's −2R daily loss limit (SPG, FUTU, JETS, UNP), and 1 twin held (MF4 on GMAB behind MF4-FD).
QLYS / WK / FUTU have old bar indices because those names had 30–50 minutes without a trade. The decision bar is still the latest bar.

## 3. Parity and distinct symbols, last 10 sessions (offline / live; * = not identical)

| setup | 10-16 | 10-19 | 10-20 | 10-21 | 10-22 | 10-23 | 10-26 | 10-27 | 10-28 | 10-29 | offline | live | matched | distinct offline symbols | + blackout signals |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RW5 | 9/3* | 8/3* | 20/8* | 7/4* | 52/33* | 12/9* | 4/1* | 8/9* | 10/10 | 7/7 | 137 | 87 | 85 | 124 | 37 |
| RW3 | 8/5* | 8/5* | 12/5* | 8/3* | 47/30* | 9/3* | 8/0* | 8/8 | 5/5 | 4/4 | 117 | 68 | 67 | 103 | 43 |
| MF2-FD | off | off | 4/2* | 3/1* | 49/30* | 2/2 | 4/3* | 8/8 | 1/1 | 7/7 | 78 | 54 | 54 | 61 | 17 |
| MF4-FD | off | off | 19/9* | 6/3* | 36/25* | 9/7* | 10/1* | 7/8* | 2/2 | 11/11 | 100 | 66 | 63 | 93 | 29 |
| ST7 | off | off | off | off | off | off | 0/0 | 1/1 | 2/2 | 1/1 | 4 | 4 | 4 | 4 | 5 |
| NS1 | 1/1 | 0/0 | 4/3* | 0/0 | 0/0 | 0/0 | 0/0 | 1/1 | 0/0 | 4/4 | 10 | 9 | 9 | 10 | 10 |
| NS5 | 6/5* | 1/1 | 3/3 | 0/0 | 1/1 | 0/0 | 0/0 | 0/0 | 3/3 | 0/0 | 14 | 13 | 13 | 14 | 6 |
| MF4 | 11/6* | 4/4 | 7/4* | 4/3* | 15/11* | 3/3 | 5/0* | 1/2* | 0/0 | 1/1 | 51 | 34 | 32 | 48 | 15 |

"off" = not enabled in Primary that day (freeze file). Before GX1 (10-16..10-26) the 8 setups had 419 offline signals, 240 live, 235 matched (56%).
After GX1 (10-27..10-29): 92 offline, 95 live, 92 matched (100%). Every miss before GX1 that was checked is a symbol whose bar count was not a multiple of 5 at
the decision bar. The full mismatch list is in `summary.py` output. The few extras before GX1 are VEA / OPCH / ESS (10-20) and live-only small names
from setups outside this list.

## Caveats

- The symbol list is today's universe with ADV ≥ $60M (1,532 names), applied to every day. A name with ADV ≥ $95M on an earlier day but now below $60M
  is missing (this is the CORO extra on 10-27). The ADV used for the gates is recomputed per day from priors, as live does.
- The offline bars are the bars as they stand after the close. A late SIP revision can create or remove a bar (XLE on 10-27).
- The universe tier, in-play filter and spread / borrow skips are taken from the journal, not simulated. No outcomes (R) are computed here.
- Follow-ups (housekeeping, not done here): (a) measure the LAB-RATE-PARITY live/backtest ratios again on sessions from 10-27 on only; (b) apply the live earnings
  blackout (`earnings_cal.parquet` on `research-data`) to the two-year frames before any rate comparison or low-tier verdict.

Reproduce: `python research/ops/coverage1029/fetch.py <scratch> <days...>`, then `funnel.py <scratch> <day>` for each day, `coverage.py <scratch> <days...>`,
`live10.py <scratch>` and `summary.py <scratch> 2026-10-29`.
