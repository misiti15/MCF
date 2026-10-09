# BDI autopsy: primary and Testing accounts, 2026-10-09

*Educational only — not financial advice. These are live **paper** results from one session. They are a diagnosis, not evidence (rule 7). Lab and history numbers are labelled separately below. No locked holdout was scored here.*

Inputs:
- the two trade exports (`origin/mcf-data:reports/2026-10-09.csv`, 70 rows; `origin/mcf-data-testing:reports/2026-10-09.csv`, 46 rows), read-only copies of each branch's `journal.db` and `setups/2026-10-09.json` (the frozen setup set of each account)
- SIP 1-minute bars fetched read-only (Alpaca market data only) for the 89 traded symbols plus SPY/QQQ/IWM, 2026-08-10..10-09, and for the 1,223 lab symbols on 10-08/10-09 (market breadth), in `data/cache/bdi1009/` (git-ignored; `fetch.py`)
- Alpaca news headlines for the traded symbols, 10-08 16:00 to 10-09 16:00 ET (`news.py`; keyword screen, routine "maintains / reiterates" notes and SPY macro headlines are not counted as material)

Scripts (this folder): `autopsy.py` (from the 10-08 version: same what-ifs, costs and loss-type precedence, both accounts, plus the regime1009 market context at entry) -> `trades.csv`; `summary.py`, `render.py` (tables); `tests.py` (history check of the heat_fade_short split) -> `tests_heat_split.csv`.

There are no stacking-bug artifacts today (one position per symbol, #13, held). All 115 lab/heat signals re-qualify on the live-equivalent recomputation (`mask_recomputed`); orb20_a is not a lab mask. 23 symbol/setup pairs were traded by both accounts (same signals).

## Failures first
- **Primary: the fourth red day in a row, and the worst so far in dollars.** 70 trades, 29 green (41.4%), average −0.168R, journal P/L **−$238.87** (cost-adjusted −$254.09). Since the start: 178 journal trades, −$742.
- **The loss is the opening window.** Entries before 10:30: 35 trades, −0.436R, **−$350.63**. Entries from 10:30: 35 trades, +0.099R, **+$111.76**.
- **heat_fade_short alone lost $226.75** on 31 trades (10 green, −0.37R), all entered 09:50–10:31; 15 of them in the first two minutes (09:50–09:51, −$68.31).
  - Every one of the 31 was a **gap-up name trading just below its open** (gap +0.07% to +16%; fromOpen −0.02% to −2.3%, 13 of them within 0.15% of the open: −$102.56). The market had no direction until 10:15: SPY −0.07% to 0.00% from the open, QQQ −0.4% to −0.56% (gap +0.67% being sold), universe breadth from the open 0.45–0.51. From 10:15 SPY and IWM rallied (SPY +0.41% at the 14:51 high) and the gap-up names went back above their opens.
  - On the 2-year history the setup's live window is +0.017R (n 14,433, t 0.68, up sessions −0.199 / down +0.154; RESCORE "rework"). Today was a flat session (universe median open-to-close +0.197%, just below the up cut of +0.212%), where the history gives +0.082R. Today's −0.37R is a bad draw on a setup with no proven edge, not a new failure mode.
- **NS3 / MF4 / MF3 opening shorts on big gap-up decliners never worked:** MXL (MF4, gap +3.2%, −2.9% from the open, −$39.11; MF3 in Testing −$21.33), FCEL (NS3, −$46.21 / Testing −$23.76), PURR (NS3, −$39.33 / −$17.64). None moved in the trade's favour (held MFE ≤ 0.0R).
- **Testing account: red but nearly flat.** 46 trades (first entry 10:01), 25 green (54%), −0.023R, **−$25.03** (cost-adjusted −$36.15). Its losses are the same signals as primary (NS3 −$39.89, MF3 −$22.23) plus ALHC (L3, bearish-outlook headline at 08:49, −$17.78) and ST2 (−$16.19).
- **Every live exit what-if is diagnosis only** (rule 7; the exit lineages failed on the history in EXIT_STUDY, the 10-07 autopsy and the 10-08 H3 test). Today none of the exit changes helps the primary book by more than +4R; stop-and-reverse (+5.9R vs base) only because heat_fade_short reversed.
- **Hindsight check:** the opposite side would have hit +1R first on 26 of 41 primary losers (1 of 29 winners) and 14 of 21 Testing losers (0 of 25 winners). The four counter-signal flags and the two market-context gates of today's regime study do not pick those trades out consistently (section below).
- **The 10-09 loop hypothesis "heat_fade_short open drain" fails as a fix on the history:** the full-day version (Testing from 10-12) is worse than the live window (−0.032R, n 75,136, t −2.22 vs +0.017R), and dropping the near-open entries (fromOpen > −0.15%) raises the live window only to +0.027R (t 1.03, still regime-dependent). See Tests.

## Versus yesterday (2026-10-08), primary
| | 10-08 (real trades) | 10-09 | change |
|---|---|---|---|
| trades | 39 | 70 | +31 |
| win rate | 41% | 41.4% | flat |
| avg R | −0.166 | −0.168 | flat |
| journal P/L | −$121.03 | −$238.87 | −$117.84 |
| worst setup | exhaustion_short −$105.68 (15 trades, 13:00–14:45) | heat_fade_short −$226.75 (31 trades, 09:50–10:31) | |
| best setup | NS2 +$33.3 | exhaustion_short +$106.87 (4/4) | |

- **Not better.** The book traded 31 more times at the same negative expectancy (−0.17R per trade on both days), so the dollar loss doubled. Testing traded for the first time (−$25.03).
- **Why:** a different setup and a different window lost each day: 10-08 exhaustion_short into an afternoon small-cap rally; 10-09 heat_fade_short into a directionless open that turned up. On 10-09 exhaustion_short won 4 of 4 (+$106.87): names up 7–12% from the open faded in the afternoon. That is the same setup the 10-08 report recommended retiring (2-year −0.010R). One day each way is noise around a setup with no proven edge; the history decides.
- **What is being tried next:** today's main study (Part B, `research/bdi/regime1009`) asked whether a market-regime signal known at entry can gate long/short setups. It cannot (1,052 configurations, no passer; summary below). Two new backlog items follow from it: volatility-aware sizing (what *is* predictable is the size of the rest-of-day move) and beta-hedged setups.

## Market context
- SPY: gap +0.30%, open to close +0.30%; low −0.14% at 09:48, high +0.41% at 14:51. QQQ: gap +0.67%, open to close −0.17%; low −0.56% at 10:11. IWM: gap +0.23%, open to close +0.26%; +0.60% at 14:51.
- Universe (1,223 lab symbols): median open-to-close **+0.197%** -> a **flat** session (cuts −0.226% / +0.212%). Breadth from the open: 0.49 at 09:50, 0.51 at 10:00, 0.46 at 10:30, 0.52 at 12:00, 0.60 at 14:00, 0.58 at 15:55.
- News: no market-moving macro event in the morning; UMich inflation expectations headline at 10:56 ("second-worst print ever"), Gulf oil shut-ins and diesel headlines midday.

## Market-context gate on today's trades (regime1009 G1-G4, computed at each entry)
| account | gate | allowed: n / P/L / avg R | blocked: n / P/L / avg R |
|---|---|---|---|
| primary | G1 breadth > 0.5 for longs, < 0.5 for shorts | 51 / −$234.94 / −0.184 | 19 / −$3.93 / −0.126 |
| primary | G2 breadth dead zone (≥ 0.60 / ≤ 0.40) | 0 | 70 / −$238.87 / −0.168 |
| primary | G3 SPY from the open > 0 / < 0 | 46 / −$233.19 / −0.224 | 24 / −$5.68 / −0.061 |
| primary | G4 SPY dead zone (±0.30%) | 0 | 70 |
| testing | G1 | 25 / −$47.55 / −0.061 | 21 / +$22.52 / +0.022 |
| testing | G2 | 1 / +$6.16 / +0.363 | 45 / −$31.19 / −0.032 |
| testing | G3 | 13 / +$26.96 / +0.312 | 33 / −$51.99 / −0.155 |
| testing | G4 | 1 / +$6.16 | 45 / −$31.19 |

- G1 would have *allowed* 28 of the 31 heat_fade_short entries: breadth was 0.46–0.49, just under 0.5. Only the dead-zone gates (G2/G4) would have stopped the opening cluster, because they stopped everything today: no bar reached breadth ≤ 0.40 or ≥ 0.60 before 14:00, and SPY did not reach ±0.30% from the open until the afternoon.
- G3 helped Testing (+0.31R allowed vs −0.16R blocked) and hurt primary (−0.22R allowed vs −0.06R blocked). On the 2-year history none of these gates passes (Part B), so neither day's result is evidence.

## Per-trade autopsy (116 trades: 70 primary, 46 Testing)
How to read the table (as 10-08):
- **R** = |entry − stop| as executed. **Rule values** recomputed as LabStrategy/HeatStrategy saw them (40 prior 5-minute bars + today's complete bars, prior-day ATR(14)). **brd / SPY fo** = universe breadth from the open (share of the 1,223 lab symbols above their open) and SPY's move from the open at the last complete minute before the signal.
- **MFE/MAE**: "held" from entry to exit; "day" from entry to 15:55. **What-ifs** net of production costs (1c + 1 bps per side, +2c on stops), 1-minute walk, stop first: BE0.5 (stop to breakeven at +0.5R, live target), trail (0.5R trail after +0.5R, no target), tp0.5 / tp1, hold 15:55 (live stop, no target), SAR (stop-and-reverse 1R/1R), re-entry (same side after a stop at the first 5-minute close back through the entry, 1R/1R), opposite 1R/1R.

### primary (70 trades)

| id | sym | setup | side | in-out (ET) | exit | r live | rule values at signal (recomputed) | brd / SPY fo at entry | held MFE / MAE (R) | t->MFE held / day (min) | day MFE | BE0.5 | trail | tp0.5 | tp1 | hold 15:55 | SAR | re-entry | opposite 1R/1R | loss type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 188 | ABVX | hfs | S | 09:50-11:34 | target | +0.83 | score -13.8, gap +1.35%, fromOpen -0.59%, rsi 70 | 0.46 / -0.06% | 0.97 / -0.81 | 104 / 116 | 1.80 | -0.11 | +0.24 | +0.47 | +0.97 | +1.32 | +0.80 | +0.80 | -1.13 (stop) | win |
| 162 | AFRM | hfs | S | 09:50-09:56 | stop | -1.06 | score -29.0, gap +1.09%, fromOpen -0.06%, rsi 78 | 0.46 / -0.06% | -0.35 / -1.17 | 1 / 1 | -0.35 | -1.06 | -1.06 | -1.06 | -1.06 | -1.06 | -0.10 | -2.13 | +0.96 (target) | never_worked |
| 186 | AKAM | hfs | S | 09:50-11:31 | stop | -1.05 | score -19.8, gap +1.46%, fromOpen -0.04%, rsi 76 | 0.46 / -0.06% | 0.44 / -1.05 | 12 / 12 | 0.44 | -1.04 | -1.04 | -1.04 | -1.04 | -1.04 | -0.06 | -2.08 | +0.97 (target) | small MFE then failed (0.15-0.5R) |
| 180 | APP | hfs | S | 09:50-11:08 | target | +0.90 | score -14.2, gap +0.54%, fromOpen -0.35%, rsi 69 | 0.46 / -0.06% | 1.07 / -0.56 | 78 / 341 | 1.30 | -0.03 | +0.06 | +0.48 | +0.98 | +0.60 | +0.87 | +0.87 | -1.03 (stop) | win |
| 195 | AVGO | hfs | S | 09:50-12:43 | target | +0.77 | score -20.4, gap +1.55%, fromOpen -0.38%, rsi 76 | 0.46 / -0.06% | 0.80 / -0.44 | 173 / 363 | 0.96 | -0.04 | +0.06 | +0.47 | +0.84 | +0.84 | +0.74 | +0.74 | -0.90 (time) | win |
| 167 | CRCL | hfs | S | 09:50-10:08 | stop | -1.00 | score -52.2, gap +1.58%, fromOpen -0.02%, rsi 84 | 0.46 / -0.06% | -0.06 / -1.10 | 1 / 1 | -0.06 | -1.04 | -1.04 | -1.04 | -1.04 | -1.04 | -0.06 | -2.07 | +0.98 (target) | never_worked |
| 169 | EGO | hfs | S | 09:50-10:23 | target | +1.16 | score -30.0, gap +2.77%, fromOpen -0.11%, rsi 86 | 0.46 / -0.06% | 1.23 / -0.45 | 33 / 165 | 1.53 | +1.08 | +0.89 | +0.43 | +0.93 | +0.42 | +1.08 | +1.08 | -1.13 (stop) | win |
| 203 | GE | hfs | S | 09:50-14:50 | stop | -1.01 | score -12.6, gap +0.20%, fromOpen -0.04%, rsi 53 | 0.46 / -0.06% | 2.46 / -1.18 | 49 / 49 | 2.46 | -0.09 | +0.88 | +0.42 | +0.92 | -1.09 | -1.32 | -1.06 | -1.28 (stop) | gave_back_gains |
| 163 | HUM | hfs | S | 09:51-09:55 | target | +0.21 | score -51.5, gap +16.31%, fromOpen -1.09%, rsi 89 | 0.49 / -0.04% | 0.36 / -0.78 | 4 / 72 | 2.28 | +0.17 | +0.09 | +0.48 | +0.98 | +1.97 | +0.17 | +0.17 | -1.02 (stop) | win |
| 170 | LITE | hfs | S | 09:51-10:23 | stop | -1.06 | score -13.4, gap +6.28%, fromOpen -2.34%, rsi 65 | 0.49 / -0.04% | 0.17 / -1.43 | 6 / 6 | 0.17 | -1.02 | -1.02 | -1.02 | -1.02 | -1.02 | -0.03 | -0.63 | +0.99 (target) | news_earnings |
| 164 | MDB | hfs | S | 09:51-09:54 | stop | -0.97 | score -14.7, gap +1.22%, fromOpen -0.47%, rsi 73 | 0.49 / -0.04% | 0.02 / -1.17 | 1 / 1 | 0.02 | -1.02 | -1.02 | -1.02 | -1.02 | -1.02 | -0.04 | -2.05 | +0.98 (target) | never_worked |
| 197 | RIO | hfs | S | 09:51-14:06 | stop | -1.05 | score -12.7, gap +0.94%, fromOpen -0.02%, rsi 79 | 0.49 / -0.04% | 0.90 / -1.01 | 30 / 30 | 0.90 | -0.12 | +0.28 | +0.42 | -1.13 | -1.13 | -1.29 | -1.16 | +0.92 (target) | gave_back_gains |
| 174 | SNDK | hfs | S | 09:51-10:42 | target | +0.81 | score -14.0, gap +1.48%, fromOpen -0.84%, rsi 63 | 0.49 / -0.04% | 0.83 / -0.27 | 51 / 349 | 1.70 | +0.80 | +0.55 | +0.49 | +0.99 | +1.43 | +0.80 | +0.80 | -1.01 (stop) | win |
| 177 | SPXL | hfs | S | 09:51-10:58 | stop | -1.02 | score -11.5, gap +0.79%, fromOpen -0.13%, rsi 70 | 0.49 / -0.04% | 0.12 / -1.04 | 11 / 11 | 0.12 | -1.05 | -1.05 | -1.05 | -1.05 | -1.05 | -0.09 | -2.10 | +0.96 (target) | never_worked |
| 165 | XME | hfs | S | 09:51-10:00 | stop | -1.12 | score -29.9, gap +1.25%, fromOpen -0.09%, rsi 82 | 0.49 / -0.04% | 0.07 / -1.05 | 3 / 3 | 0.07 | -1.16 | -1.16 | -1.16 | -1.16 | -1.16 | -2.35 | -2.30 | +0.91 (target) | never_worked |
| 210 | ACN | hfs | S | 09:55-15:55 | flatten | -0.20 | score -12.5, gap +0.07%, fromOpen -0.53%, rsi 60 | 0.48 / -0.07% | 0.59 / -0.40 | 13 / 13 | 0.59 | -0.03 | +0.06 | +0.48 | +0.16 | +0.16 | +0.16 | +0.16 | -0.20 (time) | gave_back_gains |
| 211 | CVNA | hfs | S | 09:55-15:55 | flatten | +0.55 | score -20.3, gap +1.22%, fromOpen -0.11%, rsi 65 | 0.48 / -0.07% | 1.01 / -0.69 | 351 / 351 | 1.01 | -0.10 | +0.13 | +0.45 | +0.95 | +0.45 | +0.45 | +0.45 | -1.09 (stop) | win |
| 166 | BAM | MF3 | S | 10:00-10:03 | target | +0.29 | heat -34, bp -0.61, vwap +0.35%, rsi5 83, rsi 83, fo +0.7%, gap +0.4% | 0.51 / -0.02% | 0.35 / -0.10 | 3 / 3 | 0.35 | +0.19 | -1.12 | -1.12 | -1.12 | -1.12 | +0.19 | +0.19 | +0.93 (target) | win |
| 184 | CRWD | hfs | S | 10:00-11:23 | stop | -1.02 | score -30.9, gap +1.90%, fromOpen -0.42%, rsi 61 | 0.51 / -0.02% | 0.38 / -1.02 | 6 / 6 | 0.38 | -1.03 | -1.03 | -1.03 | -1.03 | -1.03 | -0.05 | -2.06 | +0.98 (target) | small MFE then failed (0.15-0.5R) |
| 172 | ILF | MF1 | S | 10:01-10:35 | stop | -1.07 | heat -32, bp -0.59, vwap +0.19%, rsi5 100, rsi 76, fo -0.1%, gap +1.2% | 0.51 / -0.03% | 0.99 / -1.15 | 7 / 7 | 0.99 | -0.36 | +0.10 | +0.29 | -1.36 | -1.36 | -0.57 | -2.73 | +0.79 (target) | gave_back_gains |
| 171 | MXL | MF4 | S | 10:01-10:23 | stop | -1.12 | heat -53, bp -0.44, vwap -3.00%, rsi5 1, rsi 44, fo -2.9%, gap +3.2% | 0.51 / -0.03% | -0.00 / -1.07 | 1 / 1 | -0.00 | -1.03 | -1.03 | -1.03 | -1.03 | -1.03 | -0.06 | -2.07 | +0.98 (target) | never_worked |
| 183 | SPY | hfs | S | 10:01-11:19 | stop | -1.02 | score -13.8, gap +0.30%, fromOpen -0.02%, rsi 74 | 0.51 / -0.03% | 0.38 / -1.02 | 3 / 3 | 0.38 | -1.12 | -1.12 | -1.12 | -1.12 | -1.12 | -0.22 | -2.24 | +0.89 (target) | small MFE then failed (0.15-0.5R) |
| 206 | BE | hfs | S | 10:05-15:17 | stop | -1.02 | score -18.7, gap +1.14%, fromOpen -0.36%, rsi 64 | 0.45 / -0.08% | 0.50 / -1.02 | 6 / 6 | 0.50 | -1.02 | -1.02 | -1.02 | -1.02 | -1.02 | -1.33 | -0.66 | +0.99 (target) | small MFE then failed (0.15-0.5R) |
| 178 | COPX | hfs | S | 10:05-11:04 | stop | -1.00 | score -22.5, gap +3.45%, fromOpen -0.07%, rsi 83 | 0.45 / -0.08% | 0.39 / -1.00 | 17 / 17 | 0.39 | -1.09 | -1.09 | -1.09 | -1.09 | -1.09 | -0.80 | -2.20 | +0.94 (target) | small MFE then failed (0.15-0.5R) |
| 212 | GLD | hfs | S | 10:06-15:55 | flatten | -0.65 | score -33.2, gap +1.41%, fromOpen -0.07%, rsi 85 | 0.47 / -0.08% | 0.32 / -0.99 | 56 / 56 | 0.32 | -0.74 | -0.74 | -0.74 | -0.74 | -0.74 | -0.74 | -0.74 | +0.61 (time) | late_hold |
| 179 | HUT | hfs | S | 10:06-11:05 | stop | -1.02 | score -17.7, gap +2.35%, fromOpen -1.74%, rsi 51 | 0.47 / -0.08% | 0.49 / -1.00 | 34 / 34 | 0.49 | -1.03 | -1.03 | -1.03 | -1.03 | -1.03 | -0.05 | -2.06 | +0.98 (target) | news_earnings |
| 208 | FBTC | hfs | S | 10:10-15:50 | target | +0.99 | score -17.2, gap +1.42%, fromOpen -0.08%, rsi 82 | 0.46 / -0.03% | 0.99 / -0.79 | 326 / 328 | 1.01 | +0.93 | +0.33 | +0.43 | +0.93 | +0.75 | +0.93 | +0.93 | -1.11 (stop) | win |
| 213 | ETHA | hfs | S | 10:10-15:55 | flatten | +0.51 | score -11.6, gap +1.31%, fromOpen -0.31%, rsi 83 | 0.46 / -0.03% | 0.68 / -0.69 | 339 / 339 | 0.68 | -0.11 | -0.09 | +0.44 | +0.41 | +0.41 | +0.41 | +0.41 | -0.54 (time) | win |
| 168 | MSTR | hfs | S | 10:11-10:15 | stop | -1.01 | score -18.6, gap +1.88%, fromOpen -0.48%, rsi 60 | 0.48 / -0.03% | -0.20 / -1.44 | 1 / 265 | 0.15 | -1.04 | -1.04 | -1.04 | -1.04 | -1.04 | -0.06 | -0.07 | +0.97 (target) | never_worked |
| 214 | SNPS | hfs | S | 10:11-15:55 | flatten | -0.59 | score -13.1, gap +2.54%, fromOpen -0.58%, rsi 62 | 0.48 / -0.03% | 0.14 / -0.72 | 6 / 6 | 0.14 | -0.54 | -0.54 | -0.54 | -0.54 | -0.54 | -0.54 | -0.54 | +0.51 (time) | late_hold |
| 215 | HOOD | hfs | S | 10:16-15:55 | flatten | -0.19 | score -25.6, gap +1.91%, fromOpen -0.34%, rsi 60 | 0.50 / +0.00% | 0.60 / -0.89 | 186 / 186 | 0.60 | -0.07 | -0.06 | +0.45 | -0.38 | -0.38 | -0.38 | -0.38 | +0.29 (time) | news_earnings |
| 173 | PURR | NS3 | S | 10:21-10:35 | stop | -1.00 | heat 2, bp +0.12, vwap +0.12%, rsi5 64, rsi 41, fo -2.2%, gap +1.2% | 0.46 / +0.03% | -0.02 / -1.00 | 1 / 332 | 0.50 | -1.18 | -1.18 | -1.18 | -1.18 | -1.18 | -2.37 | -0.28 | +0.90 (target) | never_worked |
| 216 | CBRS | NS3 | S | 10:25-15:55 | flatten | +0.03 | heat -4, bp -0.16, vwap +0.33%, rsi5 74, rsi 36, fo -2.8%, gap +1.2% | 0.50 / +0.05% | 0.39 / -0.91 | 314 / 314 | 0.39 | +0.13 | +0.13 | +0.13 | +0.13 | +0.13 | +0.13 | +0.13 | -0.16 (time) | win |
| 175 | FCEL | NS3 | S | 10:26-10:51 | stop | -1.02 | heat -11, bp -0.19, vwap +0.23%, rsi5 56, rsi 54, fo -2.6%, gap +3.3% | 0.50 / +0.06% | -0.04 / -1.17 | 1 / 116 | 0.33 | -1.11 | -1.11 | -1.11 | -1.11 | -1.11 | -2.21 | -0.16 | +0.94 (target) | never_worked |
| 176 | JBL | hfs | S | 10:26-10:56 | stop | -1.04 | score -13.1, gap +1.29%, fromOpen -0.37%, rsi 69 | 0.50 / +0.06% | 0.54 / -1.04 | 15 / 15 | 0.54 | -0.03 | +0.01 | +0.48 | -1.03 | -1.03 | -2.08 | -1.30 | +0.98 (target) | gave_back_gains |
| 200 | CLS | hfs | S | 10:30-14:24 | stop | -1.02 | score -19.0, gap +3.01%, fromOpen -1.65%, rsi 61 | 0.46 / +0.04% | 0.41 / -1.04 | 12 / 12 | 0.41 | -1.02 | -1.02 | -1.02 | -1.02 | -1.02 | -1.77 | -0.37 | +0.98 (target) | small MFE then failed (0.15-0.5R) |
| 196 | KRMN | hfs | S | 10:31-12:43 | target | +0.83 | score -20.4, gap +3.38%, fromOpen -0.15%, rsi 76 | 0.46 / +0.05% | 0.84 / -0.60 | 130 / 130 | 0.84 | +0.78 | +0.26 | +0.45 | -0.18 | -0.18 | +0.78 | +0.78 | +0.09 (time) | win |
| 190 | Z | NS5 | L | 10:31-11:43 | target | +1.52 | heat -13, bp +0.31, vwap -0.67%, rsi5 31, rsi 26, fo -2.5%, gap +0.5% | 0.46 / +0.05% | 1.56 / -0.24 | 72 / 267 | 2.06 | -0.18 | +0.20 | +0.40 | +0.90 | +1.63 | +1.26 | +1.26 | -1.18 (stop) | win |
| 217 | CIFR | NS3 | S | 10:35-15:55 | flatten | -0.40 | heat -1, bp +0.12, vwap +0.15%, rsi5 58, rsi 39, fo -2.1%, gap +0.7% | 0.44 / +0.03% | 0.32 / -0.54 | 249 / 249 | 0.32 | -0.33 | -0.33 | -0.33 | -0.33 | -0.33 | -0.33 | -0.33 | +0.18 (time) | late_hold |
| 218 | MT | MF4 | S | 10:36-15:55 | flatten | -0.04 | heat -46, bp -0.49, vwap -0.25%, rsi5 44, rsi 81, fo -0.4%, gap +4.9% | 0.43 / +0.01% | 0.31 / -0.85 | 5 / 5 | 0.31 | -0.10 | -0.10 | -0.10 | -0.10 | -0.10 | -0.10 | -0.10 | -0.06 (time) | late_hold |
| 191 | NVTS | NS3 | S | 10:36-11:58 | target | +0.94 | heat 1, bp -0.22, vwap +0.07%, rsi5 79, rsi 45, fo -3.4%, gap +2.5% | 0.43 / +0.01% | 0.99 / -0.79 | 82 / 84 | 1.13 | +0.84 | +0.43 | +0.39 | +0.89 | +0.31 | +0.84 | +0.84 | -1.21 (stop) | win |
| 182 | SHLD | MF3 | S | 10:46-11:15 | stop | -1.09 | heat -31, bp -0.28, vwap +0.32%, rsi5 85, rsi 77, fo +0.4%, gap +0.1% | 0.46 / +0.03% | -0.05 / -1.09 | 3 / 3 | -0.05 | -1.32 | -1.32 | -1.32 | -1.32 | -1.32 | -0.74 | -2.06 | +0.85 (target) | never_worked |
| 219 | RAM | NS5 | L | 10:51-15:55 | flatten | +0.00 | heat -5, bp -0.15, vwap -1.81%, rsi5 32, rsi 27, fo -3.3%, gap +3.2% | 0.47 / +0.07% | 0.32 / -0.43 | 211 / 211 | 0.32 | -0.10 | -0.10 | -0.10 | -0.10 | -0.10 | -0.10 | -0.10 | -0.04 (time) | late_hold |
| 181 | TRP | MF3 | S | 10:51-11:10 | target | +0.51 | heat -32, bp -0.38, vwap +0.39%, rsi5 71, rsi 76, fo +1.0%, gap -0.4% | 0.47 / +0.07% | 0.52 / -0.10 | 17 / 80 | 1.19 | +0.41 | -0.10 | +0.42 | +0.92 | +0.27 | +0.41 | +0.41 | -1.17 (stop) | win |
| 220 | BTDR | NS3 | S | 10:55-15:55 | flatten | +0.35 | heat -6, bp +0.02, vwap +0.17%, rsi5 72, rsi 64, fo -2.3%, gap +2.4% | 0.47 / +0.11% | 0.72 / -0.17 | 280 / 280 | 0.72 | +0.26 | +0.26 | +0.39 | +0.26 | +0.26 | +0.26 | +0.26 | -0.48 (time) | win |
| 221 | SMTC | NS3 | S | 10:56-15:55 | flatten | -0.37 | heat -10, bp +0.06, vwap +0.09%, rsi5 69, rsi 52, fo -3.3%, gap +2.9% | 0.48 / +0.12% | 0.79 / -0.56 | 66 / 66 | 0.79 | -0.03 | +0.26 | +0.48 | -0.43 | -0.43 | -0.43 | -0.43 | +0.39 (time) | gave_back_gains |
| 192 | KVYO | NS5 | L | 11:06-12:14 | stop | -1.00 | heat 2, bp -0.23, vwap -1.53%, rsi5 0, rsi 22, fo -2.3%, gap +0.9% | 0.48 / +0.12% | 0.02 / -1.02 | 17 / 261 | 0.23 | -1.18 | -1.18 | -1.18 | -1.18 | -1.18 | -2.36 | -0.28 | +0.90 (target) | never_worked |
| 222 | GLXY | NS3 | S | 11:16-15:55 | flatten | -0.36 | heat -17, bp +0.27, vwap +0.05%, rsi5 36, rsi 50, fo -3.0%, gap +3.8% | 0.54 / +0.14% | 0.71 / -0.40 | 193 / 193 | 0.71 | -0.13 | +0.08 | +0.43 | -0.40 | -0.40 | -0.40 | -0.40 | +0.26 (time) | gave_back_gains |
| 193 | ON | hfl | L | 11:16-12:22 | stop | -1.01 | score 58.5, gap +2.29%, fromOpen -5.12%, rsi 22 | 0.54 / +0.14% | 0.24 / -1.01 | 8 / 254 | 0.55 | -1.06 | -1.06 | -1.06 | -1.06 | -1.06 | -2.11 | -0.09 | +0.96 (target) | wrong_side_after_big_swing |
| 185 | CAI | NS1 | L | 11:20-11:24 | target | +0.44 | heat 12, bp -0.17, vwap +0.36%, rsi5 97, rsi 39, fo +3.2%, gap +0.9% | 0.56 / +0.18% | 0.56 / 0.00 | 4 / 209 | 2.41 | +0.35 | +0.58 | +0.45 | +0.95 | +1.75 | +0.35 | +0.35 | -1.09 (stop) | win |
| 187 | GILD | NS1 | L | 11:20-11:32 | target | +0.48 | heat 1, bp -0.09, vwap +0.22%, rsi5 85, rsi 38, fo +2.1%, gap -0.6% | 0.56 / +0.18% | 0.55 / -0.13 | 12 / 139 | 2.60 | +0.43 | +0.49 | +0.44 | +0.94 | +2.10 | +0.43 | +0.43 | -1.08 (stop) | win |
| 189 | XBI | NS1 | L | 11:21-11:36 | target | +0.52 | heat 5, bp +0.37, vwap +0.30%, rsi5 93, rsi 35, fo +2.0%, gap +0.0% | 0.55 / +0.17% | 0.62 / -0.05 | 15 / 118 | 1.99 | +0.45 | +1.20 | +0.45 | +0.95 | +1.17 | +0.45 | +0.45 | -1.06 (stop) | win |
| 223 | AMT | orb | L | 11:30-15:55 | flatten | +0.16 | OR break, fromOpen +2.2%, rsi 67 | 0.55 / +0.11% | 0.34 / -0.80 | 255 / 255 | 0.34 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | -0.09 (time) | win |
| 202 | IONQ | NS5 | L | 11:31-14:46 | target | +0.86 | heat 4, bp -0.16, vwap -0.65%, rsi5 11, rsi 29, fo -2.1%, gap +1.4% | 0.55 / +0.12% | 0.94 / -0.03 | 195 / 197 | 1.35 | +0.82 | +1.06 | +0.46 | +0.96 | +1.06 | +0.82 | +0.82 | -1.07 (stop) | win |
| 199 | TXN | hfl | L | 12:01-14:21 | target | +1.33 | score 59.3, gap +0.86%, fromOpen -2.76%, rsi 20 | 0.52 / +0.09% | 1.36 / -0.48 | 138 / 141 | 1.58 | +1.27 | +1.02 | +0.45 | +0.95 | +0.82 | +1.27 | +1.27 | -1.06 (stop) | win |
| 224 | AXTI | hfl | L | 12:05-15:55 | flatten | -0.11 | score 57.8, gap +2.93%, fromOpen -7.07%, rsi 24 | 0.53 / +0.14% | 0.34 / -0.21 | 166 / 166 | 0.34 | -0.12 | -0.12 | -0.12 | -0.12 | -0.12 | -0.12 | -0.12 | +0.09 (time) | late_hold |
| 201 | MCHP | hfl | L | 12:06-14:24 | target | +0.79 | score 58.3, gap +1.01%, fromOpen -2.66%, rsi 18 | 0.52 / +0.16% | 0.85 / -0.78 | 138 / 204 | 1.48 | +0.73 | +0.31 | +0.46 | +0.96 | +1.10 | +0.73 | +0.73 | -1.07 (stop) | win |
| 225 | SITM | hfl | L | 12:06-15:55 | flatten | -0.03 | score 62.6, gap +1.70%, fromOpen -7.43%, rsi 10 | 0.52 / +0.16% | 0.33 / -0.85 | 150 / 150 | 0.33 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | +0.10 (time) | late_hold |
| 194 | NTR | hfl | L | 12:11-12:28 | stop | -1.07 | score 58.1, gap +0.13%, fromOpen -1.56%, rsi 18 | 0.52 / +0.16% | -0.05 / -1.28 | 8 / 8 | -0.05 | -1.09 | -1.09 | -1.09 | -1.09 | -1.09 | -0.15 | -2.18 | +0.94 (target) | never_worked |
| 226 | ARM | hfl | L | 12:15-15:55 | flatten | -0.12 | score 66.9, gap +1.70%, fromOpen -4.73%, rsi 17 | 0.53 / +0.18% | 0.26 / -0.26 | 178 / 178 | 0.26 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | +0.10 (time) | news_earnings |
| 227 | HLN | MF5 | S | 12:20-15:55 | flatten | -0.59 | heat -30, bp -0.27, vwap +0.09%, rsi5 80, rsi 67, fo +0.2%, gap +0.1% | 0.53 / +0.22% | -0.00 / -0.78 | 18 / 18 | -0.00 | -0.92 | -0.92 | -0.92 | -0.92 | -0.92 | -0.92 | -0.92 | +0.06 (time) | late_hold |
| 198 | FICO | hfl | L | 12:30-14:16 | stop | -1.04 | score 62.5, gap +1.48%, fromOpen -3.66%, rsi 21 | 0.53 / +0.23% | 0.09 / -1.05 | 20 / 20 | 0.09 | -1.01 | -1.01 | -1.01 | -1.01 | -1.01 | -0.02 | -2.03 | +0.99 (target) | wrong_side_after_big_swing |
| 228 | BTI | MF5 | S | 13:05-15:55 | flatten | -0.04 | heat -30, bp -0.59, vwap +0.10%, rsi5 89, rsi 79, fo +0.2%, gap -0.1% | 0.57 / +0.27% | 0.36 / -0.54 | 109 / 109 | 0.36 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.22 (time) | late_hold |
| 204 | CLF | exh | S | 13:10-14:49 | target | +0.87 | rsi5 92, sma20 +1.09%, bear_div 1, fromOpen +6.9% | 0.56 / +0.23% | 0.90 / -0.64 | 99 / 121 | 1.10 | +0.73 | +0.35 | +0.37 | +0.87 | +0.77 | +0.73 | +0.73 | -1.25 (stop) | win |
| 209 | IBRX | exh | S | 13:16-15:51 | target | +0.94 | rsi5 100, sma20 +1.19%, bear_div 1, fromOpen +7.4% | 0.56 / +0.22% | 0.99 / -0.66 | 155 / 158 | 1.22 | +0.82 | +0.07 | +0.38 | +0.88 | +0.98 | +0.82 | +0.82 | -1.23 (stop) | win |
| 229 | MTUM | MF5 | S | 13:17-15:55 | flatten | +0.34 | heat -49, bp -0.80, vwap +0.26%, rsi5 83, rsi 82, fo -0.1%, gap +0.9% | 0.56 / +0.22% | 0.57 / -0.55 | 114 / 114 | 0.57 | +0.40 | +0.40 | +0.42 | +0.40 | +0.40 | +0.40 | +0.40 | -0.56 (time) | win |
| 230 | IOVA | exh | S | 13:20-15:55 | flatten | +0.61 | rsi5 90, sma20 +1.57%, bear_div 1, fromOpen +10.8% | 0.57 / +0.20% | 0.81 / -0.65 | 154 / 154 | 0.81 | +0.55 | +0.55 | +0.41 | +0.55 | +0.55 | +0.55 | +0.55 | -0.72 (time) | win |
| 231 | JCI | MF5 | S | 13:21-15:55 | flatten | +0.54 | heat -38, bp -0.56, vwap +0.72%, rsi5 75, rsi 80, fo +1.9%, gap +0.6% | 0.57 / +0.21% | 0.76 / -0.29 | 144 / 144 | 0.76 | +0.49 | +0.49 | +0.44 | +0.49 | +0.49 | +0.49 | +0.49 | -0.62 (time) | win |
| 205 | BMO | MF5 | S | 13:25-15:12 | stop | -1.03 | heat -34, bp -0.31, vwap +0.43%, rsi5 91, rsi 78, fo -0.4%, gap +1.0% | 0.56 / +0.21% | 0.08 / -1.00 | 2 / 2 | 0.08 | -1.10 | -1.10 | -1.10 | -1.10 | -1.10 | -1.21 | -1.22 | +0.93 (target) | never_worked |
| 207 | FSLY | exh | S | 14:55-15:28 | target | +0.77 | rsi5 100, sma20 +1.05%, bear_div 1, fromOpen +11.9% | 0.60 / +0.33% | 0.95 / -0.14 | 33 / 57 | 1.41 | +0.73 | +1.20 | +0.46 | +0.96 | +1.20 | +0.73 | +0.73 | -1.07 (stop) | win |

### testing (46 trades)

| id | sym | setup | side | in-out (ET) | exit | r live | rule values at signal (recomputed) | brd / SPY fo at entry | held MFE / MAE (R) | t->MFE held / day (min) | day MFE | BE0.5 | trail | tp0.5 | tp1 | hold 15:55 | SAR | re-entry | opposite 1R/1R | loss type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 | PDBC | RW7 | S | 10:05-12:46 | target | +0.97 | heat -24, bp -0.25, vwap +0.16%, rsi5 77, rsi 58, fo +0.3%, gap -0.0% | 0.45 / -0.08% | 1.03 / -0.91 | 154 / 270 | 1.27 | +0.71 | +0.05 | +0.21 | +0.71 | +0.25 | +0.71 | +0.71 | -1.53 (stop) | win |
| 13 | BP | RW7 | S | 10:15-12:05 | target | +1.15 | heat -22, bp -0.26, vwap +0.31%, rsi5 58, rsi 64, fo +0.7%, gap -0.1% | 0.46 / -0.01% | 1.76 / -0.61 | 110 / 272 | 2.06 | +1.00 | +1.08 | +0.39 | +0.89 | +1.74 | +1.00 | +1.00 | -1.18 (stop) | win |
| 2 | MXL | MF3 | S | 10:20-10:36 | stop | -1.06 | heat -43, bp -0.32, vwap -1.19%, rsi5 92, rsi 54, fo -1.6%, gap +3.2% | 0.46 / +0.02% | -0.03 / -1.06 | 6 / 6 | -0.03 | -1.03 | -1.03 | -1.03 | -1.03 | -1.03 | -1.41 | -0.84 | +0.98 (target) | never_worked |
| 3 | PURR | NS3 | S | 10:20-10:35 | stop | -1.00 | heat 2, bp +0.12, vwap +0.12%, rsi5 64, rsi 41, fo -2.2%, gap +1.2% | 0.46 / +0.02% | 0.12 / -1.00 | 1 / 333 | 0.64 | -1.20 | -1.20 | -1.20 | -1.20 | -1.20 | -2.40 | -0.31 | +0.89 (target) | never_worked |
| 24 | ABNB | RW1 | S | 10:25-14:46 | stop | -1.01 | heat -22, bp -0.45, vwap +0.25%, rsi5 61, rsi 62, fo +1.0%, gap -0.2% | 0.50 / +0.05% | 0.17 / -1.11 | 32 / 32 | 0.17 | -1.05 | -1.05 | -1.05 | -1.05 | -1.05 | -1.21 | -0.99 | +0.97 (target) | small MFE then failed (0.15-0.5R) |
| 32 | CBRS | NS3 | S | 10:25-15:55 | flatten | +0.03 | heat -4, bp -0.16, vwap +0.33%, rsi5 74, rsi 36, fo -2.8%, gap +1.2% | 0.50 / +0.05% | 0.39 / -0.91 | 314 / 314 | 0.39 | +0.13 | +0.13 | +0.13 | +0.13 | +0.13 | +0.13 | +0.13 | -0.16 (time) | win |
| 1 | COHR | ST2 | L | 10:25-10:31 | target | +0.36 | heat -36, bp +0.04, vwap -2.42%, rsi5 64, rsi 56, fo -3.8%, gap +5.4% | 0.50 / +0.05% | 0.46 / -0.13 | 6 / 308 | 1.37 | +0.34 | -0.01 | +0.48 | +0.98 | +0.93 | +0.34 | +0.34 | -1.02 (stop) | win |
| 25 | CVX | RW1 | S | 10:25-14:46 | target | +0.84 | heat -22, bp -0.35, vwap +0.21%, rsi5 49, rsi 61, fo +0.8%, gap -0.2% | 0.50 / +0.05% | 1.16 / -0.92 | 261 / 262 | 1.17 | +0.79 | +0.60 | +0.45 | +0.95 | +0.94 | +0.79 | +0.79 | -1.07 (stop) | win |
| 4 | FCEL | NS3 | S | 10:25-10:51 | stop | -1.02 | heat -11, bp -0.19, vwap +0.23%, rsi5 56, rsi 54, fo -2.6%, gap +3.3% | 0.50 / +0.05% | -0.07 / -1.16 | 1 / 117 | 0.27 | -1.10 | -1.10 | -1.10 | -1.10 | -1.10 | -2.20 | -0.16 | +0.95 (target) | never_worked |
| 33 | SOXL | ST2 | L | 10:25-15:55 | flatten | -0.15 | heat -43, bp +0.12, vwap -1.35%, rsi5 38, rsi 52, fo -5.2%, gap +4.0% | 0.50 / +0.05% | 0.72 / -0.84 | 9 / 9 | 0.72 | -0.03 | +0.19 | +0.48 | -0.29 | -0.29 | -0.29 | -0.29 | +0.26 (time) | gave_back_gains |
| 11 | Z | NS5 | L | 10:31-11:43 | target | +0.91 | heat -13, bp +0.31, vwap -0.67%, rsi5 31, rsi 26, fo -2.5%, gap +0.5% | 0.46 / +0.05% | 0.94 / -0.42 | 72 / 267 | 1.32 | +0.71 | +0.30 | +0.42 | +0.92 | +1.00 | +0.71 | +0.71 | -1.14 (stop) | win |
| 20 | APA | RW5 | S | 10:35-13:32 | target | +1.27 | heat -35, bp -0.16, vwap +0.71%, rsi5 100, rsi 82, fo +2.0%, gap -0.2% | 0.44 / +0.03% | 1.29 / -0.65 | 177 / 252 | 2.28 | +1.18 | +0.24 | +0.42 | +0.92 | +1.58 | +1.18 | +1.18 | -1.14 (stop) | win |
| 34 | CIFR | NS3 | S | 10:35-15:55 | flatten | -0.40 | heat -1, bp +0.12, vwap +0.15%, rsi5 58, rsi 39, fo -2.1%, gap +0.7% | 0.44 / +0.03% | 0.32 / -0.54 | 249 / 249 | 0.32 | -0.33 | -0.33 | -0.33 | -0.33 | -0.33 | -0.33 | -0.33 | +0.18 (time) | late_hold |
| 35 | MT | MF4 | S | 10:35-15:55 | flatten | -0.17 | heat -46, bp -0.49, vwap -0.25%, rsi5 44, rsi 81, fo -0.4%, gap +4.9% | 0.44 / +0.03% | 0.15 / -0.87 | 6 / 6 | 0.15 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | +0.08 (time) | late_hold |
| 12 | NVTS | NS3 | S | 10:35-11:58 | target | +0.83 | heat 1, bp -0.22, vwap +0.07%, rsi5 79, rsi 45, fo -3.4%, gap +2.5% | 0.44 / +0.03% | 0.88 / -0.80 | 83 / 85 | 1.02 | +0.74 | +0.32 | +0.40 | +0.90 | +0.24 | +0.74 | +0.74 | -1.20 (stop) | win |
| 15 | BMY | RW1 | S | 10:45-12:36 | stop | -0.99 | heat -20, bp -0.52, vwap -0.10%, rsi5 33, rsi 61, fo +0.8%, gap -1.2% | 0.46 / +0.00% | 0.85 / -1.11 | 5 / 264 | 1.22 | -0.15 | +0.20 | +0.40 | -1.15 | -1.15 | -2.31 | -0.25 | +0.90 (target) | stopped_then_reversed |
| 6 | SHLD | MF3 | S | 10:45-11:15 | stop | -1.08 | heat -31, bp -0.28, vwap +0.32%, rsi5 85, rsi 77, fo +0.4%, gap +0.1% | 0.46 / +0.00% | -0.13 / -1.08 | 4 / 4 | -0.13 | -1.30 | -1.30 | -1.30 | -1.30 | -1.30 | -0.76 | -1.97 | +0.87 (target) | never_worked |
| 36 | RAM | NS5 | L | 10:50-15:55 | flatten | +0.03 | heat -5, bp -0.15, vwap -1.81%, rsi5 32, rsi 27, fo -3.3%, gap +3.2% | 0.46 / +0.03% | 0.36 / -0.41 | 212 / 212 | 0.36 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 (time) | win |
| 5 | TRP | MF3 | S | 10:50-11:10 | target | +0.51 | heat -32, bp -0.38, vwap +0.39%, rsi5 71, rsi 76, fo +1.0%, gap -0.4% | 0.46 / +0.03% | 0.52 / -0.10 | 18 / 81 | 1.19 | +0.41 | -0.10 | +0.42 | +0.92 | +0.27 | +0.41 | +0.41 | -1.17 (stop) | win |
| 37 | BTDR | NS3 | S | 10:55-15:55 | flatten | +0.35 | heat -6, bp +0.02, vwap +0.17%, rsi5 72, rsi 64, fo -2.3%, gap +2.4% | 0.47 / +0.11% | 0.72 / -0.17 | 280 / 280 | 0.72 | +0.26 | +0.26 | +0.39 | +0.26 | +0.26 | +0.26 | +0.26 | -0.48 (time) | win |
| 8 | GD | RW3 | S | 10:55-11:26 | stop | -1.13 | heat -23, bp -0.42, vwap +0.43%, rsi5 85, rsi 68, fo +1.2%, gap -0.8% | 0.47 / +0.11% | 0.21 / -1.24 | 10 / 147 | 0.44 | -1.07 | -1.07 | -1.07 | -1.07 | -1.07 | -2.14 | -0.12 | +0.94 (target) | small MFE then failed (0.15-0.5R) |
| 38 | SMTC | NS3 | S | 10:55-15:55 | flatten | -0.41 | heat -10, bp +0.06, vwap +0.09%, rsi5 69, rsi 52, fo -3.3%, gap +2.9% | 0.47 / +0.11% | 0.70 / -0.58 | 67 / 67 | 0.70 | -0.03 | +0.18 | +0.48 | -0.45 | -0.45 | -0.45 | -0.45 | +0.42 (time) | gave_back_gains |
| 14 | KVYO | NS5 | L | 11:05-12:14 | stop | -1.00 | heat 2, bp -0.23, vwap -1.53%, rsi5 0, rsi 22, fo -2.3%, gap +0.9% | 0.50 / +0.14% | 0.07 / -1.02 | 18 / 262 | 0.28 | -1.19 | -1.19 | -1.19 | -1.19 | -1.19 | -2.38 | -0.29 | +0.90 (target) | never_worked |
| 39 | GLXY | NS3 | S | 11:15-15:55 | flatten | -0.39 | heat -17, bp +0.27, vwap +0.05%, rsi5 36, rsi 50, fo -3.0%, gap +3.8% | 0.53 / +0.12% | 0.62 / -0.44 | 194 / 194 | 0.62 | -0.12 | -0.01 | +0.43 | -0.43 | -0.43 | -0.43 | -0.43 | +0.30 (time) | gave_back_gains |
| 7 | CAI | NS1 | L | 11:20-11:23 | target | +0.47 | heat 12, bp -0.17, vwap +0.36%, rsi5 97, rsi 39, fo +3.2%, gap +0.9% | 0.56 / +0.18% | 0.51 / 0.02 | 3 / 209 | 2.48 | +0.38 | +0.62 | +0.45 | +0.95 | +1.81 | +0.38 | +0.38 | -1.10 (stop) | win |
| 9 | GILD | NS1 | L | 11:20-11:32 | target | +0.54 | heat 1, bp -0.09, vwap +0.22%, rsi5 85, rsi 38, fo +2.1%, gap -0.6% | 0.56 / +0.18% | 0.60 / -0.10 | 12 / 139 | 2.73 | +0.48 | +0.56 | +0.44 | +0.94 | +2.21 | +0.48 | +0.48 | -1.08 (stop) | win |
| 10 | XBI | NS1 | L | 11:20-11:36 | target | +0.57 | heat 5, bp +0.37, vwap +0.30%, rsi5 93, rsi 35, fo +2.0%, gap +0.0% | 0.56 / +0.18% | 0.69 / -0.05 | 16 / 119 | 2.11 | +0.52 | +1.32 | +0.45 | +0.95 | +1.27 | +0.52 | +0.52 | -1.07 (stop) | win |
| 26 | IONQ | NS5 | L | 11:30-14:46 | target | +0.86 | heat 4, bp -0.16, vwap -0.65%, rsi5 11, rsi 29, fo -2.1%, gap +1.4% | 0.55 / +0.11% | 0.94 / -0.03 | 196 / 198 | 1.35 | +0.82 | +1.06 | +0.46 | +0.96 | +1.06 | +0.82 | +0.82 | -1.07 (stop) | win |
| 22 | MARA | ST2 | L | 11:30-14:27 | stop | -1.01 | heat -6, bp +0.35, vwap -0.50%, rsi5 8, rsi 43, fo -3.8%, gap +1.7% | 0.55 / +0.11% | 0.20 / -1.01 | 8 / 8 | 0.20 | -1.21 | -1.21 | -1.21 | -1.21 | -1.21 | -1.89 | -0.77 | +0.89 (target) | wrong_side_after_big_swing |
| 19 | CLF | RW2 | S | 12:10-13:28 | stop | -1.02 | rsi5 91, sma20 +2.17%, bear_div 1, fromOpen +6.1% | 0.52 / +0.17% | 0.17 / -1.07 | 37 / 181 | 0.37 | -1.21 | -1.21 | -1.21 | -1.21 | -1.21 | -2.42 | -0.32 | +0.89 (target) | wrong_side_after_big_swing |
| 40 | HLN | MF5 | S | 12:20-15:55 | flatten | -0.59 | heat -30, bp -0.27, vwap +0.09%, rsi5 80, rsi 67, fo +0.2%, gap +0.1% | 0.53 / +0.22% | -0.00 / -0.78 | 18 / 18 | -0.00 | -0.92 | -0.92 | -0.92 | -0.92 | -0.92 | -0.92 | -0.92 | +0.06 (time) | late_hold |
| 30 | RVMD | RW2 | S | 12:35-15:41 | target | +0.93 | rsi5 91, sma20 +1.10%, bear_div 1, fromOpen +3.4% | 0.53 / +0.22% | 1.09 / -0.60 | 184 / 197 | 1.54 | +0.90 | +0.44 | +0.47 | +0.97 | +1.39 | +0.90 | +0.90 | -1.04 (stop) | win |
| 31 | OWL | RW2 | S | 12:40-15:44 | target | +0.88 | rsi5 100, sma20 +1.14%, bear_div 1, fromOpen +4.0% | 0.54 / +0.22% | 0.99 / -0.22 | 184 / 192 | 2.09 | -0.46 | -0.08 | +0.26 | +0.76 | +1.69 | +0.65 | +0.65 | -1.46 (stop) | win |
| 41 | LQDA | RW2 | S | 12:45-15:55 | flatten | +0.46 | rsi5 95, sma20 +2.25%, bear_div 1, fromOpen +4.7% | 0.55 / +0.23% | 0.54 / -0.15 | 188 / 188 | 0.54 | +0.48 | +0.48 | +0.48 | +0.48 | +0.48 | +0.48 | +0.48 | -0.51 (time) | win |
| 29 | PCVX | RW2 | S | 12:45-15:28 | stop | -1.01 | rsi5 95, sma20 +1.50%, bear_div 1, fromOpen +9.1% | 0.55 / +0.23% | 0.33 / -1.02 | 108 / 108 | 0.33 | -1.04 | -1.04 | -1.04 | -1.04 | -1.04 | -1.34 | -0.73 | +0.97 (target) | wrong_side_after_big_swing |
| 18 | CIEN | RW2 | S | 12:50-13:23 | stop | -1.08 | rsi5 94, sma20 +1.07%, bear_div 1, fromOpen +2.5% | 0.55 / +0.26% | -0.00 / -1.09 | 17 / 134 | 0.08 | -1.02 | -1.02 | -1.02 | -1.02 | -1.02 | -2.05 | -0.04 | +0.98 (target) | never_worked |
| 17 | ALHC | L3 | S | 13:00-13:13 | stop | -1.08 | heat 5, bp +0.10, vwap +5.16%, rsi5 59, rsi 52, fo +7.5%, gap -20.8% | 0.56 / +0.26% | -0.08 / -1.04 | 1 / 23 | 0.12 | -1.32 | -1.32 | -1.32 | -1.32 | -1.32 | -2.64 | -0.49 | +0.83 (target) | news_earnings |
| 42 | BTI | MF5 | S | 13:05-15:55 | flatten | -0.04 | heat -30, bp -0.59, vwap +0.10%, rsi5 89, rsi 79, fo +0.2%, gap -0.1% | 0.57 / +0.27% | 0.36 / -0.54 | 109 / 109 | 0.36 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.22 (time) | late_hold |
| 43 | MTUM | MF5 | S | 13:16-15:55 | flatten | +0.30 | heat -49, bp -0.80, vwap +0.26%, rsi5 83, rsi 82, fo -0.1%, gap +0.9% | 0.56 / +0.22% | 0.52 / -0.56 | 115 / 115 | 0.52 | +0.35 | +0.35 | +0.42 | +0.35 | +0.35 | +0.35 | +0.35 | -0.51 (time) | win |
| 44 | IOVA | RW2 | S | 13:20-15:55 | flatten | +0.67 | rsi5 90, sma20 +1.57%, bear_div 1, fromOpen +10.8% | 0.57 / +0.20% | 0.88 / -0.64 | 154 / 154 | 0.88 | +0.61 | +0.61 | +0.41 | +0.61 | +0.61 | +0.61 | +0.61 | -0.79 (time) | win |
| 45 | JCI | MF5 | S | 13:20-15:55 | flatten | +0.54 | heat -38, bp -0.56, vwap +0.72%, rsi5 75, rsi 80, fo +1.9%, gap +0.6% | 0.57 / +0.20% | 0.76 / -0.29 | 145 / 145 | 0.76 | +0.49 | +0.49 | +0.44 | +0.49 | +0.49 | +0.49 | +0.49 | -0.62 (time) | win |
| 27 | BMO | MF5 | S | 13:25-15:12 | stop | -1.03 | heat -34, bp -0.31, vwap +0.43%, rsi5 91, rsi 78, fo -0.4%, gap +1.0% | 0.56 / +0.21% | 0.08 / -1.00 | 2 / 2 | 0.08 | -1.10 | -1.10 | -1.10 | -1.10 | -1.10 | -1.21 | -1.22 | +0.93 (target) | never_worked |
| 21 | BKD | L3 | S | 13:50-13:52 | target | +0.46 | heat 23, bp +0.56, vwap +3.36%, rsi5 91, rsi 76, fo +0.6%, gap -5.0% | 0.58 / +0.25% | 0.52 / -0.12 | 2 / 84 | 2.60 | +0.16 | +0.63 | +0.24 | +0.74 | +1.42 | +0.16 | +0.16 | -1.49 (stop) | win |
| 23 | ALHC | L3 | S | 14:05-14:41 | target | +0.54 | heat -2, bp +0.02, vwap +7.42%, rsi5 78, rsi 69, fo +10.6%, gap -20.8% | 0.60 / +0.24% | 0.77 / -0.54 | 36 / 109 | 1.43 | +0.28 | -0.05 | +0.33 | +0.83 | +1.18 | +0.28 | +0.28 | -1.32 (stop) | win |
| 46 | NVTS | ST8 | L | 14:25-15:55 | flatten | +0.36 | heat -3, bp +0.42, vwap -0.33%, rsi5 55, rsi 67, fo -4.5%, gap +2.5% | 0.60 / +0.31% | 0.47 / -0.10 | 90 / 61 | 0.41 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | -0.30 (time) | win |
| 28 | FSLY | RW2 | S | 14:55-15:22 | target | +0.77 | rsi5 100, sma20 +1.05%, bear_div 1, fromOpen +11.9% | 0.60 / +0.33% | 0.81 / -0.14 | 27 / 57 | 1.41 | +0.73 | +1.20 | +0.46 | +0.96 | +1.20 | +0.73 | +0.73 | -1.07 (stop) | win |

### What-if totals and loss types per setup
`wi_base_sim` is the live geometry re-simulated with the same costs; compare against it (the live r column is gross).

#### What-if totals, primary (R, net of costs; diagnosis only)

| setup | n | wi_base_sim | wi_be0.5 | wi_trail0.5 | wi_tp0.5 | wi_tp1 | wi_hold_1555 | r_hold_nostop_1555 | wi_stop_and_reverse | wi_reentry | opp_1r1r | opp_hold_1555 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | 1 | -1.36 | -0.36 | +0.10 | +0.29 | -1.36 | -1.36 | -2.12 | -0.57 | -2.73 | +0.79 | +1.91 |
| MF3-open-flowsell-rsi5hi | 3 | -0.72 | -0.72 | -2.55 | -2.03 | -1.53 | -2.17 | -3.03 | -0.14 | -1.46 | +0.62 | +2.73 |
| MF4-h40-open-flowsell | 2 | -1.14 | -1.14 | -1.14 | -1.14 | -1.14 | -1.14 | -1.40 | -0.16 | -2.17 | +0.92 | +1.30 |
| MF5-flowsell-vwapup-rsi5hi | 5 | -1.15 | -1.15 | -1.15 | -1.18 | -1.15 | -1.15 | -1.07 | -1.27 | -1.27 | -0.41 | +0.31 |
| NS1-rsidip-rsi5pop-long | 3 | +1.23 | +1.23 | +2.27 | +1.34 | +2.84 | +5.02 | +5.02 | +1.23 | +1.23 | -3.24 | -5.18 |
| NS3-failed-vwap-reclaim-short | 8 | -2.21 | -1.54 | -1.46 | -0.80 | -2.16 | -2.74 | -1.76 | -4.50 | -0.37 | +0.82 | +1.20 |
| NS5-sma50-flush-oversold-long | 4 | +0.80 | -0.64 | -0.03 | -0.42 | +0.58 | +1.41 | +2.35 | -0.38 | +1.70 | -1.39 | -2.66 |
| exhaustion_short | 4 | +2.83 | +2.83 | +2.17 | +1.62 | +3.26 | +3.50 | +3.50 | +2.83 | +2.83 | -4.27 | -3.88 |
| heat_fade_long | 8 | -1.54 | -1.54 | -2.21 | -2.64 | -1.64 | -1.62 | -2.38 | -0.66 | -2.68 | +1.06 | +2.13 |
| heat_fade_short | 31 | -12.44 | -12.98 | -12.32 | -9.17 | -9.67 | -11.48 | -18.83 | -6.18 | -20.98 | +6.44 | +17.57 |
| orb20_a | 1 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | +0.06 | -0.09 | -0.08 |
| ALL | 70 | -15.64 | -15.95 | -16.25 | -14.07 | -11.91 | -11.67 | -19.66 | -9.74 | -25.82 | +1.26 | +15.37 |

#### Loss types, primary

| primary type | MF1 | MF3 | MF4 | MF5 | NS1 | NS3 | NS5 | exh | hfl | hfs | orb | All |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gave_back_gains | 1 (ILF) |  |  |  |  | 2 (SMTC, GLXY) |  |  |  | 4 (JBL, RIO, GE, ACN) |  | **7** |
| late_hold |  |  | 1 (MT) | 2 (HLN, BTI) |  | 1 (CIFR) | 1 (RAM) |  | 2 (AXTI, SITM) | 2 (GLD, SNPS) |  | **9** |
| never_worked |  | 1 (SHLD) | 1 (MXL) | 1 (BMO) |  | 2 (PURR, FCEL) | 1 (KVYO) |  | 1 (NTR) | 6 (AFRM, MDB, XME, CRCL, MSTR, SPXL) |  | **13** |
| news_earnings |  |  |  |  |  |  |  |  | 1 (ARM) | 3 (LITE, HUT, HOOD) |  | **4** |
| small MFE then failed (0.15-0.5R) |  |  |  |  |  |  |  |  |  | 6 (COPX, SPY, CRWD, AKAM, CLS, BE) |  | **6** |
| win |  | 2 |  | 2 | 3 | 3 | 2 | 4 | 2 | 10 | 1 | **29** |
| wrong_side_after_big_swing |  |  |  |  |  |  |  |  | 2 (ON, FICO) |  |  | **2** |
| All | 1 | 3 | 2 | 5 | 3 | 8 | 4 | 4 | 8 | 31 | 1 | **70** |

#### What-if totals, testing (R, net of costs; diagnosis only)

| setup | n | wi_base_sim | wi_be0.5 | wi_trail0.5 | wi_tp0.5 | wi_tp1 | wi_hold_1555 | r_hold_nostop_1555 | wi_stop_and_reverse | wi_reentry | opp_1r1r | opp_hold_1555 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen | 1 | -1.32 | -1.32 | -1.32 | -1.32 | -1.32 | -1.32 | -0.51 | -2.64 | -0.49 | +0.83 | +0.35 |
| L3-gap-slope-rsi5hi | 2 | +0.43 | +0.43 | +0.58 | +0.58 | +1.58 | +2.61 | +2.61 | +0.43 | +0.43 | -2.81 | -3.03 |
| MF3-open-flowsell-rsi5hi | 3 | -1.91 | -1.91 | -2.43 | -1.91 | -1.41 | -2.05 | -2.18 | -1.76 | -2.40 | +0.68 | +1.95 |
| MF4-h40-open-flowsell | 1 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | -0.21 | +0.08 | +0.15 |
| MF5-flowsell-vwapup-rsi5hi | 5 | -1.19 | -1.19 | -1.19 | -1.18 | -1.19 | -1.19 | -1.12 | -1.31 | -1.31 | -0.35 | +0.36 |
| NS1-rsidip-rsi5pop-long | 3 | +1.37 | +1.37 | +2.50 | +1.34 | +2.84 | +5.28 | +5.28 | +1.37 | +1.37 | -3.25 | -5.45 |
| NS3-failed-vwap-reclaim-short | 8 | -2.39 | -1.65 | -1.75 | -0.80 | -2.23 | -2.89 | -1.74 | -4.69 | -0.55 | +0.90 | +1.19 |
| NS5-sma50-flush-oversold-long | 4 | +0.27 | +0.27 | +0.10 | -0.38 | +0.62 | +0.79 | +1.77 | -0.92 | +1.17 | -1.38 | -2.06 |
| RW1-gapdn-bounce-flowsell-short | 3 | -1.41 | -0.41 | -0.25 | -0.20 | -1.26 | -1.27 | +0.40 | -2.73 | -0.45 | +0.80 | -0.58 |
| RW2-exhaustion-noon-adv150-short | 8 | +0.10 | -1.01 | -0.62 | -1.19 | +0.51 | +2.10 | +3.94 | -2.43 | +2.28 | -2.03 | -4.51 |
| RW3-gapdn-rsi5pop-flowsell-short | 1 | -1.07 | -1.07 | -1.07 | -1.07 | -1.07 | -1.07 | -0.23 | -2.14 | -0.12 | +0.94 | +0.18 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short | 1 | +1.18 | +1.18 | +0.24 | +0.42 | +0.92 | +1.58 | +1.58 | +1.18 | +1.18 | -1.14 | -1.66 |
| RW7-gapdn-bounce-early-short | 2 | +1.71 | +1.71 | +1.13 | +0.61 | +1.61 | +2.00 | +2.00 | +1.71 | +1.71 | -2.71 | -2.39 |
| ST2-slope20up-long-am-t05s1 | 3 | -1.17 | -0.90 | -1.03 | -0.24 | -0.52 | -0.57 | +0.10 | -1.85 | -0.73 | +0.13 | -0.24 |
| ST8-volspikedn-long-pm-t1s1 | 1 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | +0.07 | -0.30 | -0.18 |
| ALL | 46 | -5.54 | -4.64 | -5.25 | -5.49 | -1.07 | +3.84 | +11.74 | -15.92 | +1.95 | -9.60 | -15.94 |

#### Loss types, testing

| primary type | L3 | MF3 | MF4 | MF5 | NS1 | NS3 | NS5 | RW1 | RW2 | RW3 | RW5 | RW7 | ST2 | ST8 | All |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gave_back_gains |  |  |  |  |  | 2 (SMTC, GLXY) |  |  |  |  |  |  | 1 (SOXL) |  | **3** |
| late_hold |  |  | 1 (MT) | 2 (HLN, BTI) |  | 1 (CIFR) |  |  |  |  |  |  |  |  | **4** |
| never_worked |  | 2 (MXL, SHLD) |  | 1 (BMO) |  | 2 (PURR, FCEL) | 1 (KVYO) |  | 1 (CIEN) |  |  |  |  |  | **7** |
| news_earnings | 1 (ALHC) |  |  |  |  |  |  |  |  |  |  |  |  |  | **1** |
| small MFE then failed (0.15-0.5R) |  |  |  |  |  |  |  | 1 (ABNB) |  | 1 (GD) |  |  |  |  | **2** |
| stopped_then_reversed |  |  |  |  |  |  |  | 1 (BMY) |  |  |  |  |  |  | **1** |
| win | 2 | 1 |  | 2 | 3 | 3 | 3 | 1 | 5 |  | 1 | 2 | 1 | 1 | **25** |
| wrong_side_after_big_swing |  |  |  |  |  |  |  |  | 2 (CLF, PCVX) |  |  |  | 1 (MARA) |  | **3** |
| All | 3 | 3 | 1 | 5 | 3 | 8 | 4 | 3 | 8 | 1 | 1 | 2 | 3 | 1 | **46** |

- **Primary what-ifs:** no exit change rescues the day. Against the re-simulated base (−15.64R): BE0.5 −0.31R, trail −0.61R, tp0.5 +1.57R, tp1 +3.73R, hold to 15:55 +3.97R, stop-and-reverse +5.90R (all from heat_fade_short's reversals: +6.26R), re-entry −10.18R (heat_fade_short −8.54R: the re-entries were stopped again).
- **Testing what-ifs:** hold to 15:55 +9.38R vs base (−5.54R), tp1 +4.47R; SAR −10.38R; re-entry +7.49R. Testing's afternoon shorts (RW2, L3) and longs (NS1) kept going after their targets.
- **The two accounts disagree on every exit what-if except SAR on heat_fade_short**, and both days (10-08, 10-09) disagree with each other (10-08: BE0.5 best, hold worst; 10-09: hold among the best). That is what single-day exit what-ifs look like when there is no exit edge.
- Median time to the best price while held: 31.5 min (primary), 36.5 min (Testing); to 15:55: 115 / 142 min. Median held MFE of losers: 0.32R (primary), 0.17R (Testing).

### Opposite side and the hindsight check
- **The opposite side (1R/1R, same entry) hit its target first on 26 of 41 primary losers and 1 of 29 winners** (+1.26R over all 70 trades vs −15.64R live geometry); **Testing: 14 of 21 losers, 0 of 25 winners** (−9.60R vs −5.54R: on Testing the live side was better).
- **No rule known at entry points to the other side consistently.** Counter-signal flags at the signal bar (win rate with the flag vs without):

| flag | primary 10-09 | Testing 10-09 | primary 10-08 |
|---|---|---|---|
| SPY 30-minute move against the trade | 27% (n 15) vs 45% (n 55) | 37% (n 19) vs 67% (n 27) | 44% (n 18) vs 38% (n 21) |
| 5-min SMA20 sloping against the trade | 41% (n 56) vs 43% (n 14) | 55% (n 29) vs 53% (n 17) | 41% (n 32) vs 43% (n 7) |
| fading the day's direction from the open | 50% (n 22) vs 38% (n 48) | 58% (n 31) vs 47% (n 15) | 39% (n 33) vs 50% (n 6) |
| 15-minute flow against the trade | 45% (n 42) vs 36% (n 28) | 62% (n 21) vs 48% (n 25) | 48% (n 21) vs 33% (n 18) |

- The SPY-30-minute flag separated winners from losers on both accounts today, and the other way round on 10-08. Its nearest tested relative on the history is gate G3 (SPY's move from the open on the trade's side): it does not pass and does not separate trade outcomes (Part B). Logged as a backlog idea (`loop-1009-spy30-against`), not a rule.
- As on 10-08, what "worked" was hindsight: the session's direction after the entry. Part B tested whether any market signal at the entry bar predicts that direction; none does.

## Loss types (one primary type per trade; precedence as `research/oct7/autopsy/classify.py` and 10-08)
Precedence: news/earnings, then stopped then reversed, then wrong side after a big swing (≥3% from the open, and the opposite 1R/1R would have won), then gave back gains (MFE ≥ 0.5R), then late hold (flattened red), then never worked (MFE < 0.15R), then small MFE then failed.

News on losers (Alpaca headlines before the exit; none is an earnings report, so the blackout could not catch them):
- **LITE** (hfs, 09:51 short, −$19.46): "Lumentum stock rises after CEO says AI demand has the company sold out through early 2029" (08:54).
- **HUT** (hfs, 10:06, −$43.47): "Why is Hut 8 stock trending after hours?" (00:01). Weak catalyst.
- **HOOD** (hfs, 10:16, −$2.83): "Robinhood CEO sells $42M in stock" (10:26, after the entry).
- **ARM** (hfl, 12:15 long, −$4.27): Eliyan takeover-talks report (09:41) and "Why is Arm stock falling" (14:08).
- **ALHC** (Testing L3, 13:00 short, −$17.78): "Alignment Healthcare stock hit by bearish outlook after Medicare Advantage rating downgrade" (08:49): a short on a name already down on news that bounced.

### Pattern tally (`research/bdi/patterns.csv`; 4 sessions, 10-06..10-09; 10-09 rows for both accounts)
- **Book-wide, every loss type has now been seen on 3–4 days:** late hold 23 trades (4 days), never worked 24 (3), gave back gains 20 (4), news/earnings 16 (4), small MFE then failed 15 (4), wrong side after a big swing 15 (3), stopped then reversed 9 (4). Five of them were already 3-day patterns on 10-08 and are in the backlog or were tested (10-08 report). The two that reached 3 days today, never worked and wrong side after a big swing, are the "opposite side would have won" family; the entry-time flags (3 sessions) and Part B's market gates found no rule known at entry that picks them out. Logged as `loop-1009-opposite-side-family` (analysis).
- **New 3-day setup x loss-type pattern: heat_fade_short x "small MFE then failed (0.15–0.5R)"**: 10 trades on 10-06, 10-07 and 10-09. Backlog hypothesis `loop-1009-hfs-small-mfe-scratch` (an early scratch when a heat_fade_short trade has not reached +0.5R within N minutes). The related exit lineages (breakeven, tp0.5, trail) already failed on the history; this one is a time-based scratch, not yet tested (needs a 1-minute path simulation on the history).
- On 2 days so far (watch list): heat_fade_long x wrong side after a big swing (10 trades), heat_fade_long x late hold (8), heat_fade_short x never worked (8), orb20_a x news (6), heat_fade_short x gave back gains (5), exhaustion_short x late hold (4), heat_fade_short x news (4).

## Tests (history; diagnosis -> hypothesis; no locked holdout)
### T1/T2 heat_fade_short splits (the 10-09 loop item `loop-1009-heat-fade-short-open-drain`), 4 configurations: FAILED as fixes
Declared in `tests.py` before scoring. Open 2-year history, production costs, t bar 4.44 (N = 19,211).

| set | split | n | exp R | t | up / flat / down | WF share | ex-best-day | verdict |
|---|---|---|---|---|---|---|---|---|
| live window | all (base) | 14,433 | +0.017 | 0.68 | −0.199 / +0.082 / +0.154 | 0.71 | +0.006 | rework |
| live window | T1 near-open (−0.15% < fromOpen < 0) | 4,895 | −0.003 | −0.12 | −0.262 / +0.086 / +0.164 | 0.71 | −0.012 | rework |
| live window | T1c fromOpen ≤ −0.15% | 9,538 | +0.027 | 1.03 | −0.165 / +0.079 / +0.149 | 0.65 | +0.015 | rework |
| live window | T2 gap > 0 | 13,351 | +0.015 | 0.56 | −0.202 / +0.084 / +0.145 | 0.71 | +0.003 | rework |
| live window | T2c gap ≤ 0 | 1,082 | +0.041 | 0.92 | −0.167 / +0.044 / +0.258 | 0.65 | +0.033 | rework |
| full day | all (base) | 75,136 | −0.032 | −2.22 | −0.235 / −0.043 / +0.131 | 0.35 | −0.034 | rework |
| full day | T1 near-open | 13,628 | −0.028 | −1.72 | −0.277 / +0.010 / +0.184 | 0.29 | −0.032 | rework |
| full day | T1c fromOpen ≤ −0.15% | 61,508 | −0.033 | −2.17 | −0.224 / −0.056 / +0.121 | 0.35 | −0.035 | rework |
| full day | T2 gap > 0 | 42,831 | −0.015 | −1.09 | −0.201 / −0.031 / +0.137 | 0.35 | −0.020 | rework |
| full day | T2c gap ≤ 0 | 32,305 | −0.054 | −2.39 | −0.274 / −0.064 / +0.124 | 0.41 | −0.057 | rework |

- Today's two traits (gap-up, barely below the open) are 93% and 34% of the live window's history trades. Near-open entries are slightly worse (−0.003 vs +0.027R), but no split fixes the setup: every row loses in up sessions (−0.16 to −0.28R).
- **The full-day version (Testing from 10-12) is worse than the live window on the history** (−0.032R, t −2.22 vs +0.017R): widening heat_fade_short adds 60k trades at about −0.04R.
- With the market-context gates of Part B: live window G1 (breadth < 0.5 at entry) +0.017R (n 7,265, up −0.355 / down +0.137), G5 (breadth < 0.5 at 10:00) +0.039R (n 3,209, t 0.99, up −0.297): the gate does not remove the up-session loss.
- Verdict for the loop item: there is no history-backed fix; the open question is retire vs keep (owner decision pending). On the evidence (2-year +0.017R, t 0.68, regime-dependent; 4 live sessions negative), BDI's recommendation stays: **off in primary** after the close with a ledger entry, keep observing the windowed version rather than the full-day one in Testing.

## Part B of today's BDI run: market-regime gate (summary; full report `research/bdi/regime1009/NOTES.md`)
- Question: can a signal known at 10:00 / 10:30 / the entry bar predict the session regime or the rest-of-day direction, so that longs trade only in "up" and shorts only in "down"?
- **Answer: no.** 16 signals x 2 bars (SPY/QQQ/IWM gap and move from the open, breadth from the open and vs VWAP, SPY VWAP position and slope, prior-day regime, gap dispersion, SPY ATR%, opening-range width, volume, dispersion): no directional signal correlates with the rest-of-day move (|rho| ≤ 0.09, none with p < 0.05; walk-forward tercile accuracy 0.31–0.39 vs 0.33). 6 gates + 4 plateau neighbours on 102 trade lists (32 live-window and 30 full-day lab setups, 40 Reddit base rules) = 1,020 gated configurations: **0 pass** the live-probation bar; gating makes the up/down split *wider*. Volatility signals (SPY ATR%, range, volume) do predict the size of the rest-of-day move (rho up to +0.23).

## Proposed changes
### Housekeeping (no change to trades or exits; can ship after tests pass)
- **H-1 (repeat of 10-08). Journal the numeric rule values at entry.** Today's 115 recomputations matched, but the autopsy still has to rebuild every frame.
- **H-5. Market context in the EOD report** (display only): SPY/QQQ/IWM gap and move from the open, universe breadth from the open at 10:00 / 12:00 / close, and the session class (up/flat/down with the rule-19 cuts). Today it took a 1,223-symbol fetch to see that the open had no direction.
- **H-6. Per-window P/L split in the EOD headline** (09:50–10:30 vs later), since two of four sessions were decided in one window.

### Setup / strategy (backlog only; nothing changes during market hours)
- **S-1. heat_fade_short: recommend off in primary** (see Tests; the loop item's fix candidates fail; the setup's 2-year record is +0.017R, t 0.68, regime-dependent). The lead/owner decides; ledger entry after the close.
- **S-2. exhaustion_short (repeat of 10-08 S-1):** today's +$106.87 does not change the 2-year verdict (retire, −0.010R, walk-forward 0.29).
- **S-3. New backlog items:** `loop-1009-hfs-small-mfe-scratch` (3-day pattern), `loop-1009-opposite-side-family` (analysis), `loop-1009-spy30-against` (idea), `loop-1009-heat-fade-short-split` (failed, T1/T2), and the Part B items `bdi-rg-*`.

## Owner notes
*Reserved for the owner's notes on today's 10 worst trades. Each flagged ticker and time will be turned into a rule using only information known at that minute, and tested across all stocks and days (charter item 3).*

| # | account | id | ticker | setup | in–out (ET) | P/L | loss type | owner note | rule to test | result |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | primary | 175 | FCEL | NS3-failed-vwap-reclaim-short | 10:26–10:51 | −$46.21 | never_worked | | | |
| 2 | primary | 179 | HUT | heat_fade_short | 10:06–11:05 | −$43.47 | news_earnings | | | |
| 3 | primary | 173 | PURR | NS3-failed-vwap-reclaim-short | 10:21–10:35 | −$39.33 | never_worked | | | |
| 4 | primary | 171 | MXL | MF4-h40-open-flowsell | 10:01–10:23 | −$39.11 | never_worked | | | |
| 5 | primary | 167 | CRCL | heat_fade_short | 09:50–10:08 | −$36.80 | never_worked | | | |
| 6 | primary | 206 | BE | heat_fade_short | 10:05–15:17 | −$34.39 | small MFE then failed (0.15-0.5R) | | | |
| 7 | primary | 186 | AKAM | heat_fade_short | 09:50–11:31 | −$30.42 | small MFE then failed (0.15-0.5R) | | | |
| 8 | primary | 200 | CLS | heat_fade_short | 10:30–14:24 | −$29.35 | small MFE then failed (0.15-0.5R) | | | |
| 9 | primary | 198 | FICO | heat_fade_long | 12:30–14:16 | −$28.76 | wrong_side_after_big_swing | | | |
| 10 | primary | 192 | KVYO | NS5-sma50-flush-oversold-long | 11:06–12:14 | −$26.41 | never_worked | | | |
