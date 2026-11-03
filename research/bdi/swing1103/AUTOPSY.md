# Primary 2026-11-03: the 10:54 low and the turn (autopsy)

*Educational only — not financial advice.* Paper account (Primary), live paper fills. Intraday analysis while the market is open; nothing on the trading path was changed.

## Data and units
- Primary state: `origin/mcf-data` as of 13:36 ET (`status.json`, `journal.db` trades/orders/signals, `intraday/2026-11-03.jsonl`).
- Market data: Alpaca SIP 1-minute bars through 13:23 ET (44 symbols: SPY, QQQ, IWM, sector ETFs, every traded name); betas = 5-minute-return beta to SPY over 2026-10-06..11-02 (20 sessions).
- **R** = each trade's P/L ÷ its own $ risk at entry (|fill − stop| × qty), summed across trades; **$** also given because $ risk per trade ranged $4.8 (IWB) to $121 (UVIX), so R sums overweight the tiny index-ETF trades.
- Open positions are marked at the last 1-min close; my $ curve matches the bot's `intraday` log within ~$5 (bot: −$196 at 10:54, mine −$200).
- 33 Primary positions (lots) opened today: 31 shorts + 2 "longs" (NS5 bought UVIX and UVXY, volatility ETPs with beta −8.4 / −6.4, so they are **short the market**).

## 1. Timeline (5-min steps, 09:50–13:20 ET)
| ET | open R | realized R | total R | total $ | SPY % | QQQ % | longs/shorts | net beta (R per +1% SPY) | net beta $ |
|---|---|---|---|---|---|---|---|---|---|
| 09:50 | +0.00 | +0.00 | +0.00 | +0 | +0.17 | +0.29 | 0/0 | +0.0 | +0k |
| 09:55 | +0.00 | +0.00 | +0.00 | +0 | +0.12 | +0.01 | 0/0 | +0.0 | +0k |
| 10:00 | -0.08 | +0.00 | -0.08 | -4 | +0.15 | +0.07 | 0/1 | -0.3 | -2k |
| 10:05 | +0.17 | +0.00 | +0.17 | +9 | +0.08 | +0.07 | 0/1 | -0.3 | -2k |
| 10:10 | +0.06 | +0.00 | +0.06 | +3 | +0.18 | +0.21 | 0/1 | -0.3 | -2k |
| 10:15 | -0.21 | +0.00 | -0.21 | -12 | +0.22 | +0.22 | 0/1 | -0.3 | -2k |
| 10:20 | -0.43 | +0.00 | -0.43 | -32 | +0.23 | +0.31 | 0/2 | -1.3 | -4k |
| 10:25 | -0.58 | +0.00 | -0.58 | -39 | +0.20 | +0.14 | 0/3 | -8.7 | -8k |
| 10:30 | -0.02 | -1.05 | -1.07 | -58 | +0.24 | +0.25 | 0/2 | -8.4 | -6k |
| 10:35 | -0.15 | -1.05 | -1.20 | -66 | +0.21 | +0.17 | 0/2 | -8.4 | -6k |
| 10:40 | -0.49 | -1.05 | -1.54 | -69 | +0.20 | +0.12 | 0/3 | -11.2 | -9k |
| 10:45 | -1.46 | -2.08 | -3.54 | -84 | +0.28 | +0.28 | 0/6 | -11.9 | -16k |
| 10:50 | -1.94 | -3.11 | -5.05 | -145 | +0.36 | +0.34 | 1/8 | -14.0 | -49k |
| 10:55 | -1.52 | -4.22 | -5.74 | -164 | +0.34 | +0.32 | 2/9 | -17.0 | -75k |
| 11:00 | -0.92 | -4.22 | -5.14 | -150 | +0.46 | +0.54 | 2/16 | -21.6 | -85k |
| 11:05 | +3.04 | -2.91 | +0.13 | -43 | +0.45 | +0.57 | 2/19 | -31.4 | -98k |
| 11:10 | +0.49 | -2.91 | -2.42 | -56 | +0.46 | +0.49 | 2/19 | -31.4 | -98k |
| 11:15 | -1.86 | -2.91 | -4.77 | -86 | +0.46 | +0.45 | 2/19 | -31.5 | -98k |
| 11:20 | +0.72 | -3.94 | -3.22 | -37 | +0.41 | +0.37 | 2/18 | -27.1 | -95k |
| 11:25 | +2.56 | -3.94 | -1.38 | +3 | +0.37 | +0.28 | 2/18 | -27.1 | -95k |
| 11:30 | +2.39 | -4.93 | -2.54 | -47 | +0.41 | +0.29 | 2/17 | -26.5 | -93k |
| 11:35 | +3.33 | -2.74 | +0.59 | +53 | +0.25 | +0.07 | 2/14 | -19.7 | -84k |
| 11:40 | +3.75 | -1.65 | +2.10 | +61 | +0.30 | +0.19 | 2/12 | -16.3 | -79k |
| 11:45 | +2.12 | -0.00 | +2.12 | +66 | +0.28 | +0.18 | 2/10 | -11.8 | -73k |
| 11:50 | +1.29 | -0.00 | +1.29 | +42 | +0.26 | +0.14 | 2/10 | -11.8 | -73k |
| 11:55 | +0.56 | -0.00 | +0.56 | +4 | +0.33 | +0.26 | 2/10 | -11.7 | -73k |
| 12:00 | +0.95 | -0.00 | +0.95 | +9 | +0.35 | +0.34 | 2/10 | -11.7 | -73k |
| 12:05 | +1.63 | +2.01 | +3.64 | +95 | +0.27 | +0.26 | 2/7 | -10.5 | -70k |
| 12:10 | +1.17 | +2.01 | +3.18 | +72 | +0.35 | +0.42 | 2/7 | -10.4 | -69k |
| 12:15 | +1.39 | +2.01 | +3.40 | +102 | +0.35 | +0.42 | 2/7 | -10.5 | -70k |
| 12:20 | +2.17 | +2.01 | +4.18 | +117 | +0.32 | +0.40 | 2/7 | -10.5 | -70k |
| 12:25 | +1.87 | +2.01 | +3.88 | +91 | +0.35 | +0.41 | 2/7 | -10.4 | -69k |
| 12:30 | +1.24 | +2.01 | +3.25 | +54 | +0.39 | +0.43 | 2/7 | -10.4 | -69k |
| 12:35 | +2.84 | +3.10 | +5.94 | +190 | +0.28 | +0.28 | 2/6 | -10.0 | -68k |
| 12:40 | +2.63 | +3.10 | +5.73 | +176 | +0.28 | +0.28 | 2/6 | -10.0 | -68k |
| 12:45 | +2.86 | +3.10 | +5.96 | +163 | +0.29 | +0.27 | 2/6 | -9.9 | -68k |
| 12:50 | +1.21 | +3.10 | +4.31 | +41 | +0.42 | +0.43 | 2/6 | -9.9 | -67k |
| 12:55 | +0.97 | +3.10 | +4.07 | +64 | +0.36 | +0.34 | 2/6 | -9.9 | -68k |
| 13:00 | +0.12 | +3.10 | +3.22 | +41 | +0.39 | +0.38 | 2/7 | -7.2 | -36k |
| 13:05 | +0.18 | +3.10 | +3.28 | +48 | +0.42 | +0.42 | 2/7 | -7.2 | -36k |
| 13:10 | -0.91 | +3.10 | +2.19 | -27 | +0.51 | +0.54 | 2/7 | -7.1 | -36k |
| 13:15 | +0.10 | +3.10 | +3.20 | -6 | +0.53 | +0.53 | 2/8 | -7.3 | -36k |
| 13:20 | -1.03 | +3.10 | +2.07 | -64 | +0.47 | +0.39 | 2/8 | -7.3 | -36k |

- Read: the book was net short beta all day; at 10:55 it was −$75k beta-dollars on ~$95k equity, and $58k of that came from the two NS5 "longs" in UVIX/UVXY.
- SPY opened +0.08% vs the prior close and was up the whole window (+0.12% to +0.53%); there was no down open today.
- The R curve and the $ curve split after 12:35: R stays +2 to +6 while $ falls back, because the big-$-risk UVIX/UVXY longs give back whenever SPY rises.

## 2. The dip: 09:50 → 10:54 trough
- **Trough: 10:54 ET, −6.47 R / −$200** (realized −4.22 R from four stops: VG 10:25, IWB 10:44, IWR 10:47, MMM 10:50; the rest open).
- (a) **Market direction (beta × SPY move): −3.18 R / −$65.** SPY rose from +0.12% (09:55) to +0.34% (10:54) against an all-short book; IWB×2 and IWO alone give −2.19 R of this, as ETFs with tiny $ risk.
- (b) **Bad entries (stock-specific move in the first 5 min after the fill, spread included): +0.07 R net / −$21.** Gross adverse −1.08 R: ISRG twin −0.42, IWR −0.35, UVXY −0.14, UVIX −0.10, VG −0.07. Other entries had favourable first-5-min moves. Fill vs mid cost −0.60 R (−$17), already inside (b). No fill was outside the 30 bps spread cap.
- (c) **Setup–day mismatch (the shorts' groups beating SPY, i.e. sector/size return minus beta × SPY): −1.05 R / −$34.** Gap-down-short setups shorted the morning's leaders: MMM/XLI −0.91 R, IWR (mid caps +0.84% at 10:50 vs SPY +0.33%) −0.36 R, VG/XLE −0.29 R.
- (e) **Stock-specific remainder: −2.31 R / −$80.** VG −0.67, KMI twin −1.02, MMM −0.32.
- Check: −3.18 + 0.07 − 1.05 − 2.31 = **−6.47 R**. In $: −65 − 21 − 34 − 80 = **−$200**.
- (a) + (c) together, i.e. "short on an up morning", = −4.23 R (65% of the dip).
- (d) **Top 5 names (a cross-cut of the same −6.47 R, not an extra part):**
  - MMM, Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD`: −1.11 R (−$28)
  - VG, same setup `RW3-gapdn-rsi5pop-flowsell-short-FD`: −1.05 R (−$59)
  - IWB, Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD`: −1.03 R (−$5)
  - IWR, `RW3-gapdn-rsi5pop-flowsell-short-FD`: −1.03 R (−$12)
  - KMI twin, Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` + `RW3-…`: −0.88 R (−$21)
  - Together: −5.10 R of −6.47 R.
  - In $ the order changes: UVIX, Big Loser Flush Buy `NS5-sma50-flush-oversold-long`, is #2 at −$47 (−0.38 R).
- By setup: RW3 −3.54 R (−$108), MF2 −1.03, MF4 −0.68, RW5 −0.65, NS5 −0.57 R (−$62).
- RW3 reached the Primary per-setup −2R latch at 10:47–10:50 (ledger 2026-10-28, effective 10-29). Its later signals were skipped as "setup daily loss limit" (13 skips: HON, SPLV, VTR, CMS, TTAN, ACN, DIA, INTU, VFLO 10:50–11:00, plus 4 after 13:15). The RW5 twins on HON/SPLV/DIA/VFLO made +0.69/+0.74/+0.83/+0.32 R.

## 3. The turn at ~10:52–11:05: what changed
- **Not an SPY reversal.** SPY kept rising from +0.34% (10:54) to +0.45% (11:05), and QQQ from +0.32% to +0.58% (session high 11:03). Market beta *cost* the book −1.71 R in the turn.
- **Rotation inside the tape (the main driver).** From 10:54 to 11:03, mega-cap tech and semis ripped while everything the book was short rolled over:
  - up: XLK +0.66 → +1.15%, SMH +0.07 → +0.68%
  - down: KRE +0.05 → −0.23%, KBE +0.29 → +0.04%, XLF +0.08 → −0.16%, XLV +1.04 → +0.67%, XLI +0.84 → +0.69%, IWR +0.84 → +0.68%, SPLV +0.19 → −0.05%
- **Turn 10:54 → 11:05 = +6.59 R (+$157):** market −1.71 R, group/sector rotation +5.25 R, first-5-min of new entries +2.08 R, stock-specific +0.97 R.
- **New entries in the same (short) direction at the turn:** 12 shorts filled 10:50–11:00 (ISRG×2, HON×2, IWS, SPLV, WDAY, HIG, TD, DIA, IWR×2, ZM, VFLO), almost all from RW5 (all-day gap-down pop fade) and MF4 (strong heat). They averaged **+0.40 R** to now (n = 12; 15 entries before 10:50 averaged −0.15 R).
- **Stops had already cleared:** four losers were out at −1 R by 10:50, and realized R stayed flat; the recovery is open-position R and then targets.
- **Targets then banked it:** PNC 11:03, TD 11:02, KBE 11:32, IWO 11:33, IWR/IWS/DIA 11:30–11:43, HON/SPLV 12:00, ISRG 12:03/12:34. Realized went from −4.22 R to +3.10 R by 12:35.
- **Second leg 11:25–11:35:** SPY faded +0.41% → +0.25% and QQQ +0.29% → +0.07%, so the beta-short book finally gained from the market; 10:54 → 12:35 = +12.41 R (+$390): market +2.25, rotation +4.06, first-5 +2.08, stock-specific +4.02.
- **Recovery by setup (10:54 → 12:35):**
  - RW5 `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` +6.73 R
  - MF4 Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` +2.21 R
  - NS5 `NS5-sma50-flush-oversold-long` +1.74 R (+$180, the largest $ share; UVIX +$102, UVXY +$78, i.e. vol rising into the 11:30 SPY fade)
  - RW3 +1.73 R (KBE, PNC, KMI)
- **News/macro:** a JOLTS release was scheduled for 10:00 ET today (calendar only, not checked against the actual print). Nothing verifiable sits at 10:52. 2026-11-03 is also US Election Day. Neither is claimed as a cause.

## 4. Leads (pre-registered today, 2026-11-03, before any test)
Common test protocol: 2-year SIP lab history 2024-09-16..2026-10-07 **excluding the locked block 2024-11-01..2025-02-28** (scored once only if a finalist exists, rule-18 bar). Production cost haircut, next-bar fills, day-clustered t ≥ max(1.5, √(2 ln N)), positive in up AND down regime sessions, walk-forward ≥ 60% positive months, avg R without the best day reported, same-time random-entry baseline. Every config tried is counted and reported. Shadow logging only (no live effect), merged outside 09:30–16:00 via the backlog.

- **L1 Vol/inverse-ETP beta guard (tweak to NS5 `NS5-sma50-flush-oversold-long`; also check L3 `L3-gap-slope-rsi5hi-FD`, which shorted SOXS today).**
  - Rule: a long-setup signal on a symbol whose 20-session 5-min beta to SPY is ≤ −1.5 is a market-short bet.
  - Hypothesis: NS5 trades on those symbols have avg R at least 0.10 below NS5 on all other symbols, and their day R correlates with SPY open-to-close at ≤ −0.5.
  - Configs: beta cut −1.0 / −1.5 / −2.0 = 3.
  - Forward: tag NS5 signals by beta class in shadow for 15 sessions. Pass = beta ≤ −1.5 class avg R < other class avg R − 0.10 with ≥ 10 trades in each class.
  - Home: tweak tested as `NS5-…-nobeta` in **Testing 1**.
- **L2 Rotation turn: tech leads, the rest rolls over (new short-timing filter).**
  - Rule: between 10:30 and 11:30 ET, QQQ prints a new session high while IWM (a) is up ≥ 0.40% from the open and (b) is ≥ 0.10% below its own session high for ≥ 5 consecutive minutes.
  - Hypothesis: short entries from the RW3/RW5/MF2/MF4 family in non-XLK/SMH names, entered within 30 min of the trigger, average ≥ +0.25 R after costs and beat the same setups' other entries that day by ≥ 0.15 R.
  - Configs: IWM-up 0.3/0.4/0.5 × lag 0.05/0.10/0.15 = 9.
  - Forward: shadow-tag 20 sessions. Pass = tagged avg R ≥ +0.15 R on ≥ 30 trades and ≥ 0.15 R above untagged.
  - Home: filter variant of RW5 in **Testing 2**.
- **L3 Up-morning delay for gap-down short setups (setup–day mismatch).**
  - Rule: on days SPY is ≥ +0.15% and IWM ≥ +0.25% from the open at 10:00, RW3/RW5/MF2/MF4 shorts entered before the first 5-min SPY bar after 10:30 that closes below the prior bar's low (or before 10:50 if none) average ≤ −0.20 R; shorts after that bar average ≥ 0 R.
  - Today: before 10:50, n = 15, −0.15 R avg; 10:50–11:04, n = 12, +0.40 R.
  - Configs: SPY 0.10/0.15/0.25 × IWM 0.25/0.40 = 6.
  - Forward: shadow-tag 20 sessions. Pass = (after − before) ≥ 0.25 R on ≥ 40 trades, with ≥ 6 qualifying days.
  - Home: "delayed" variants of RW3 and RW5 in **Testing 1**.
- **L4 Net-beta cap (risk rule, not an edge).**
  - Rule: block new entries that push the account's beta-weighted net exposure beyond ±50% of equity (beta = 20-session 5-min beta; vol/inverse ETPs count with their negative beta).
  - Hypothesis: on the 2-year joint-portfolio replay it cuts the worst intraday drawdown per session by ≥ 30% at a cost of ≤ 0.02 avg R per trade.
  - Configs: cap 30/50/75% = 3.
  - Forward: compute the would-block flag live in shadow for 15 sessions. Pass = the blocked trades' avg R ≤ the kept trades' avg R.
  - Home: tested on **Testing 1** sizing first, never Primary directly.
- **L5 Latch after a fast −2R (context check, not a new setup).**
  - Rule: when a Primary setup latches at −2R before 11:00, its skipped signals in the next 15 min are tracked as what-ifs.
  - Hypothesis: they average ≥ +0.20 R, i.e. an early latch sells the low.
  - Configs: 1.
  - Forward: log skipped-signal what-ifs 20 sessions. Pass = ≥ 25 skipped signals with avg R ≥ +0.20.
  - Today: twins of 4 of the 9 skipped RW3 signals averaged +0.65 R, n = 4 (anecdote).
  - Any change goes through the backlog; the latch stays as is.

## 5. Rule-change context (`research/ledger.jsonl`, effective 2026-10-27..11-03, Primary-relevant)
- 10-27: GX1 lab setups evaluated on the 5-minute clock (all accounts); CWT13-vwapstretch-z05-long demoted Primary → Testing 2.
- 10-28: CWT14-failbrk-pdl-p10-lowvol-long, NS4-pm-vwap-reclaim-oversold-short and MF2-open-rsimidhi-flowsell (window version) moved Primary → Testing 2 (MF2 **-FD** stays in Primary).
- 10-28: Primary position size ~$5k then ~$4k (slots/max concurrent 77, per-setup 30).
- 10-29: **Primary per-setup daily stop −2R (latched)**; it fired today on RW3 at ~10:50, so RW3's later signals were skipped.
- 10-30: L3-gap-slope-rsi5hi-FD promoted Testing 2 → Primary; L3-gap-slope-fromopen-FD re-promoted Testing 1 → Primary. Today L3 took 1 trade (SOXS); 72 of its 73 signals were skipped, mostly "not shortable/ETB".
- 11-02 / 11-03: Graveyard and Testing 2 moves (NS3-FD, RW4-FD, MF3-FD, MF5-FD; RW3S added to Testing 2). None of them touch Primary.
- No rule change took effect during today's session; all of today's figures are under the 10-28 sizing, the 10-29 −2R latch and the 10-30 L3 promotions.

## Failures and limits
- Single session, n = 33 lots. Every lead is a hypothesis from one day; none is evidence of edge.
- Betas come from 20 sessions of 5-min data, and the vol-ETP betas are noisy.
- The sector map is approximate (e.g. SSNC/TD/HIG → XLF, WDAY/ZM → XLK). For ETF trades, all non-SPY moves count as "group".
- Bars end at 13:23 ET, so positions opened after 13:20 are barely marked. The session is still open.
- Files: `timeline.csv`, `dip.csv`, `recovery.csv`, and `scripts/` (read scratch copies of `mcf-data` plus Alpaca bars; no keys are written).

Educational only — not financial advice.
