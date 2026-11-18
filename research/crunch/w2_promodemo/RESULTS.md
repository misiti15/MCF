Educational only — not financial advice

# W2-promodemo — promote / demote review (crunch 2026-11-18, after the close)

Research and proposals only: no config, runtime, ledger or assignments change. The promotion hold (11-17) stands.
C3-BAR2, C3-EXIT100, C3-NS5 and GY-LIFE are still open decisions (inbox 11-18 recommends Yes); this scores against
them as proposed. Pre-registered in [PLAN.md](PLAN.md) (2 amendments, both views reported). Every scored setup is in
[SCORES.csv](SCORES.csv); full tables are in [TABLES.md](TABLES.md); code is in `code/` (score.py, tables.py).

**Data.** Live journals (run 1) of all ten accounts, 10-06..11-18 (11-18 included). R after costs =
pnl_adj / (|entry − stop| × shares). Identical signals across accounts are counted once. Active days come from the
per-session setup snapshots, with benched sessions left out. The locked block was not read.
**Scored:** 217 setups (6 Primary, 13 On Deck, 150 Testing A-F incl. 15 GY-BENCH guests at home, 14 Gen with ≥ 10
trades, 34 Graveyard residents). **Configurations: 7** (rule sets × record views, no tuning). t bar = max(1.5,
√(2 ln 217)) = **3.28**.

**Rule changes inside the window (ledger):** 10-21 promotion = move; 10-23 per-setup −2R latch rules (testing off,
Graveyard on); 10-28 Primary sizing ~$4-5k; 10-29 Primary −2R per-setup latch; 10-30 L3-fromopen re-promoted and
L3-rsi5hi in Primary (to 11-10); 11-11 TEAM-6 in Primary (MF2-FD, MF4-FD, L3-rsi5hi out to On Deck); 11-12 LR1-LR8
(R after costs, live cost model), REPV caps, GEN-GRAD (5 Gen setups → Testing D/E/F), On Deck re-tier; 11-16 TEAM-6
open-ended; 11-17 TSZ1 half-size testing lots (R comparable, $ not), KILL-FLAT, promotion hold; 11-18 GY-BENCH
(17 residents rest, 20 guests), SRCV1, recorded quotes. Records before and after 11-12 use different cost bases.

## Headline

- **Nothing passes C3-BAR2 today.** 0 of 13 On Deck setups and 0 of 164 arena setups pass. The two closest are
  both L3 twins, and both fail only the one-big-day check because of **11-12**.
- **Primary: no member reaches the −10R demotion line.** C3-NS5 is still the only demotion on the table. The current
  six made +40.8R since 10-30, but **+1.0R without 11-12**: they were green on 43% of days, with a median day of
  −1.1R. The Primary account itself made −48.0R over the same 14 sessions (29% green). Its losses before 11-11
  came from setups that have since left.
- **18 arena setups meet C3-EXIT100** (3,893 trades, **−760.0R**). Two ex-Primary On Deck setups, MF2-FD and MF4-FD,
  meet it on their whole live record. Over the last 5 sessions these 20 setups lost **−342.5R** (−68.5R per
  session; −41.6R per session without GEN-261022-09).
- **No Graveyard resident graduates.** RW6G1-FD is closest: 37 Graveyard trades, +0.120 w/o best day, but only 9
  of the 15 Graveyard days needed and a 64% best-day share.

## (a) Primary — keep / demote

| Setup | Since | Trades | Traded / active sessions | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to rest of Primary | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD) | 10-30 | 152 | 11 / 14 | +0.297 (t 4.95) | **+0.142** | 68% `1 day` (11-12) | 55% | +39.4 | −0.021 / +0.351 | +0.39 | **Keep (protected)** |
| Late-Day ETF Dip Buy (NM-ETF-late-dip-di-long) | 11-11 | 12 | 5 / 6 | +0.168 | +0.159 | 37% | 100% | +2.0 | +0.217 / +0.151 | n/a | Keep (too early to judge) |
| Gap-Down Pop Fade, Heavy Selling (RW3-gapdn-rsi5pop-flowsell-short-FD) | 10-16 | 161 | 23 / 24 | +0.144 | −0.008 | 104% `1 day` (10-22) | 48% | +1.9 | +0.441 / −0.001 | +0.60 | Keep, watch (P3: do not trim) |
| Gap-Down Pop Fade (RW5-heat30-flowsell-rsi5pop-gapdn-short-FD) | 10-16 | 173 | 24 / 24 | +0.108 | −0.007 | 105% `1 day` (10-22) | 58% | +10.6 | +0.327 / −0.045 | +0.53 | Keep, watch |
| RSI Collapse Dip Buy (ST7-rsi50dn-long-pm-t1s1-FD) | 10-28 | 34 | 12 / 16 | +0.060 | −0.044 | 155% `1 day` | 50% | −1.8 | +0.133 / −0.059 | −0.07 | Keep; watch (+2.0R, far from −10R) |
| Big Loser Flush Buy (NS5-sma50-flush-oversold-long) | 10-09 | 41 | 17 / 29 | +0.003 | −0.050 | 1782% `1 day` (10-15) | 53% | −1.1 | +0.142 / −0.086 | −0.03 | **C3-NS5 (open): move to Testing** |

- No member is at −10R since admission. NS5 is flat: +0.1R on this R basis (P3 had −0.9R, a different R basis), it
  is negative without its best day, and it is losing in the check half. C3-NS5 stands as written.
- RW3/RW5 correlate +0.53 to +0.60 with the rest of the book, and both are one-day records from 10-22. L3-fromopen is
  the only member positive without its best day.

## (b) On Deck → Primary — "ready when the hold lifts"

**None ready.** The closest three:

| Setup | Record | Trades | Traded / active sessions | Avg R | Avg R w/o best day | Best-day share | Green days | Shrunk | Last-5 R | Fit / check avg | Corr to Primary | Fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down Bounce-off-Low Fade (L3-gap-slope-lowdist-FD) | On Deck (plan) | 109 | 19 / 28 | +0.252 (t 3.00) | +0.120 | 66% `1 day` (11-12) | 53% | +0.048 | +22.6 | +0.066 / +0.398 | +0.33 | best day |
|  | non-overlap, any account | 57 | — | — | +0.073 | 78% `1 day` | — | < 0 | — | — | — | best day, shrunk |
| Gap-Down Rebound Overbought Short (L3-gap-slope-rsi5hi-FD) | outside Primary (plan) | 136 | 16 / 20 | +0.191 (t 3.62) | +0.131 | 51% `1 day` (11-12) | 69% | +0.038 | +12.8 | +0.196 / +0.188 | +0.28 | best day (by 1 pt) |
|  | whole live incl. Primary 10-30..11-10 (22 trades, −10.0R) | 158 | 23 / 28 | +0.101 | +0.024 | 82% `1 day` | 57% | +0.003 | — | — | — | best day |
| Gap-Down VWAP Loss Short (10% gap) (CWT09-gapdn-vwaploss-g10-short) | outside Primary | 24 | 13 / 28 | +0.228 | +0.150 | 48% | 77% | −0.055 | +0.6 | +0.395 / +0.061 | −0.02 | n < 30, shrunk |

- **Order once the hold lifts:** (1) L3-lowdist. It is 100% clean on reps, but its best-day share has to fall below
  50%. At its pace without the best day (~+0.5R per session) that needs about +9R more, roughly 15-20 sessions.
  (2) CWT09-vwaploss-g10. It needs 6 more trades (~7 sessions) and avg > +0.5R at n = 30 for shrunk > 0, so its
  real gate is reps. (3) L3-rsi5hi, only if C3-BAR2 is read on the testing record: on its whole live record it
  failed in Primary 10-30..11-10.
- All three are L3 or gap-down shorts, the same family as L3-fromopen. P1 found 46% of L3-lowdist's trades duplicate
  L3-fromopen. Promotion would add depth, not diversification.

**On Deck setups losing since admission (C3-BAR2 −10R line applied to On Deck):**

| Setup | Since On Deck | Trades / R since | Whole live record (incl. Primary stint) | Meets EXIT100 on whole record? |
|---|---|---|---|---|
| Early Sellers, Mid-High RSI (all day) (MF2-open-rsimidhi-flowsell-FD) | 11-11 | 53 / **−35.7R** (−0.674) | 187 trades, −28.3R, −0.152, w/o best −0.351, 32% green, 28 active days | **yes** |
| Early Sellers, Strong Heat (all day) (MF4-h40-open-flowsell-FD) | 11-11 | 63 / **−17.6R** (−0.279) | 220 trades, −53.1R, −0.241, w/o best −0.275, 46% green, 28 active days | **yes** |
| Gap-Down Bounce Short, Heavy Selling (RW1-gapdn-bounce-flowsell-short-FD) | 11-12 | 98 / **−10.8R** (−0.110) | 219 trades, −6.0R, −0.028, w/o best −0.056, 52% green | no (avg > −0.05) |

## (c) Arena → On Deck

**None pass C3-BAR2.** 96 of 164 arena setups have < 30 trades, and 11 have none. The positive records are all
low-rep:

| Setup | Account | Trades | Traded / active sessions | Avg R (t) | Avg R w/o best day | Best-day share | Green | Last-5 R | Fit / check avg | Short of |
|---|---|---|---|---|---|---|---|---|---|---|
| Generated: Lunch New-Low Short (selling) (GEN-261026-03-…-holdtr-short) | Testing D (WB1 copy in E) | 25 | 6 / 18 | +0.454 (1.95) | +0.288 | 54% `1 day` | 83% | +10.3 | +0.509 / +0.403 | n, sessions, best day, shrunk |
| Generated: Late Pullback Buy (MACD rising) (GEN-261027-01-…-t05s1-long) | Testing E (WB5 copy in D) | 17 | 7 / 17 | +0.201 (1.54) | +0.160 | 35% | 86% | +1.9 | +0.164 / +0.254 | n, sessions, shrunk |
| Generated: PM Lower-Band Dip Buy (uptrend) (GEN-261019-02-…-t05s1-long) | Testing F | 13 | 7 / 23 | +0.231 (1.30) | +0.142 | 53% `1 day` | 71% | +3.1 | −0.247 / +0.443 | n, sessions, best day, shrunk |
| Early NS3 Short While QQQ Up (NM-RWR3-ns3-qqqup-early-short) | Testing C | 11 | 6 / 23 | +0.410 (1.33) | +0.133 | 76% `1 day` | 50% | +4.8 | −0.155 / +0.733 | n, sessions, best day, shrunk |
| Generated: Lunch Failed-Breakdown Short (GEN-261027-08-…-hold-short) | Testing B | 78 | 6 / 17 | +0.112 (1.17) | +0.030 | 79% `1 day` | 50% | +5.1 | +0.170 / +0.047 | sessions, best day, shrunk |
| Generated: Late-AM Divergence Short (quiet) (GEN-261021-01-…-t1s1-short) | Testing E (GY-BENCH guest) | 15 | 2 / 21 | +0.335 (1.57) | +0.561 | 89% `1 day` | 100% | +5.0 | n/a | n, sessions, best day, shrunk |

- **Big one-day records, not candidates:** Generated Midday Stretched Dip Buy (GEN-261020-09): +61.3R, t 4.67 (above
  the 3.28 bar), but 11-13 gave +72.6R (118%), so it is −0.100 w/o best day. GEN-261021-02: +26.9R, 133%. RW6-FD: +13.6R,
  281%. RW7-FD: +12.1R on 767 trades, 130%.
- None of these has ≥ 8 common days with Primary, so correlation to Primary is n/a. Overlap with Primary trades is
  ≤ 7%.

## (d) Arena → Graveyard — C3-EXIT100 list (18 setups)

| Setup | Account | Trades | Active days | Total R | Avg R | Avg R w/o best day | Green | Last-5 R | Note |
|---|---|---|---|---|---|---|---|---|---|
| Generated: Morning Strong-Trend Drop Short (GEN-261022-09) | Gen | 211 | 20 | −181.8 | −0.862 | −0.882 | 0% | −181.8 | 144 trades / −134.6R on 11-17 alone (see W2-HK-GEN09) |
| Failed Prior-Day-Low Break Long (CWT14-failbrk-pdl-p10-long) | Testing A | 870 | 28 | −105.3 | −0.121 | −0.143 | 43% | −54.4 | CWT14 closed to variants |
| Generated: Morning Overbought Drop Short (GEN-261029-08) | Gen | 169 | 15 | −61.7 | −0.365 | −0.766 | 50% | −61.8 | W7-DRAIN |
| Generated: Open Prior-Day-Low Buy (SPY down) (GEN-261019-05) | Testing D | 103 | 23 | −57.2 | −0.555 | −0.617 | 0% | −57.2 | W7-DRAIN; 11 trades −0.04 since GEN-GRAD |
| Failed Prior-Day-Low Break Long (0.1 ATR, low volume) (CWT14-failbrk-pdl-p10-lowvol-long) | Testing D | 436 | 23 | −43.5 | −0.100 | −0.134 | 35% | −21.6 | ex-Primary |
| Generated: Morning RSI Surge Buy (GEN-261020-07) | Testing E | 129 | 22 | −42.3 | −0.328 | −0.505 | 29% | −49.1 | GEN-GRAD 11-12 |
| Generated: Midday Gap-Up Failed-Break Buy (GEN-261021-06) | Gen | 237 | 21 | −41.6 | −0.175 | −0.258 | 55% | +6.4 | last-5 positive (flag) |
| Stretched Below VWAP Bounce (CWT13-vwapstretch-z05-long) | Testing A | 334 | 27 | −31.5 | −0.094 | −0.125 | 54% | +4.4 | ex-Primary; last-5 positive (flag) |
| Generated: Morning Selling-Burst Buy (GEN-261028-09) | Testing E | 136 | 16 | −30.7 | −0.226 | −0.251 | 14% | −14.7 | |
| Generated: Morning VWAP Reclaim Buy (SPY up) (GEN-261021-07) | Gen | 143 | 21 | −27.6 | −0.193 | −0.339 | 33% | −42.4 | |
| Generated: Lunch Tight-Range Pop Buy (GEN-261028-08) | Testing B | 132 | 16 | −27.2 | −0.206 | −0.230 | 20% | −27.2 | |
| Generated: Midday Volume Buy (volatile) (GEN-261027-05) | Testing C | 107 | 17 | −23.5 | −0.219 | −0.281 | 40% | −23.5 | |
| Generated: Morning Failed-Break Buy (wild) (GEN-261022-01) | Gen | 161 | 20 | −19.6 | −0.122 | −0.266 | 33% | −3.2 | |
| Generated: Lunch Failed Breakdown Buy (GEN-261020-05) | Testing F | 123 | 22 | −19.4 | −0.158 | −0.203 | 56% | −17.2 | |
| Big Gainer Dip-and-Pop (all day) (NS1-rsidip-rsi5pop-long-FD) | Testing E | 109 | 28 | −17.8 | −0.163 | −0.245 | 42% | −11.1 | |
| Afternoon Blow-off Short (all day) (exhaustion_short-FD) | Testing A | 248 | 28 | −12.7 | −0.051 | −0.102 | 46% | −8.5 | ex-Primary family |
| Generated: Morning VWAP-Loss Low Buy (QQQ up) (GEN-261028-02) | Gen | 131 | 16 | −8.8 | −0.067 | −0.174 | 50% | −5.6 | |
| Sellers into Strength (all day) (MF5-flowsell-vwapup-rsi5hi) | Testing A | 114 | 23 | −7.9 | −0.069 | −0.152 | 50% | +8.0 | **+0.258 on 31 trades in Testing A**; GY-LIFE "no recovery" would fail, so hold back |

Full ids, fit/check and correlation are in TABLES.md (d). Today 18 meet the rule; P3 counted 31 (−1,251R). The
difference: active days now come from snapshots (several big GEN losers have < 15 eligible sessions or < 100 trades,
e.g. GEN-261026-05 −61.8R on 68 trades) and 20 setups moved under GY-BENCH. A watch list of 20 more on the same path
(n 50-99 or < 15 active days, e.g. intraday_momentum −19.3R on 69 trades, NS3 −15.6R on 80) is in TABLES.md (d2).
None of these are low-activity trims, so the owner's 11-03 trim rule does not apply.

## (e) Graveyard → arena

**None graduate under GY-LIFE.** All 34 residents fail on the whole-record test (w/o best day > 0 with best day
< 50%). Closest:
- **Big Gainer Fade, VWAP Band Guard (all day) (RW6G1-ns2-up3-vwap2sd-short-FD)**. Graveyard: 37 trades on 9 days,
  +0.171, +0.120 w/o best day, 64% best-day share. Whole record: 67 trades, +0.020, −0.055 w/o best day. Correlation
  to Primary +0.26. It needs 6 more Graveyard days and a best day under 50%; re-check at the 11-27 review. Its WB3
  copy already runs in Testing A.
- **Midday Gap-Up Dip Buy (heat_fade_long)**. Graveyard: 137 trades on 18 days, +0.093, +0.012 w/o best day, 90%
  best-day share. Whole record: −0.190 w/o best day. Corr +0.02 (a true diversifier, but a one-day record).
- RW6-FD and ST4-FD are already in the arena, with whole records of 281% and 406% best-day share.

## Proposals (reply codes; nothing applied)

| Code | Proposal | Reply |
|---|---|---|
| **W2-EXIT17** | At the Friday 11-20 after-close review, propose the 17 EXIT100 setups above, without MF5 (its Testing A record recovered), for the Graveyard: ledger entry + assignments.json in the same commit, freed slots to the lowest-rep setups. Last 5 sessions: −342.5R across all 18 plus MF2/MF4-FD. Arena paper R, not Primary. | "W2-EXIT17 yes" / "W2-EXIT17 list" (names) / "no" |
| **W2-ODOUT** | On Deck: move **MF2-FD** (−35.7R since 11-11) and **MF4-FD** (−17.6R) to the Graveyard. Both meet EXIT100 on their whole live record and both are ex-Primary. Option: send them to Testing C/D instead (no MF twin there), because C3-WB5 #3 (MF2/MF4 with NM-MF3's 2-part gate) is a pending family test (GY-LIFE TUNE-CANDIDATE). **RW1-FD** is at −10.8R since 11-12 but its whole record is −0.028: back to Testing A or E, or keep. | "W2-ODOUT gy" / "W2-ODOUT test" / "W2-ODOUT +RW1" / "no" |
| **W2-HK-GEN09** | Housekeeping check (no setup change): GEN-261022-09 opened 144 positions on 11-17 (−134.6R, median stop −1.18R) under the Gen per-setup cap of 150. Check burst entry and stop slippage in Gen before it goes anywhere. | "W2-HK-GEN09 yes" / "no" |
| **W2-REPS** | Give the six positive low-rep arena setups in (c) reps priority at the next rotation (C3-ROT ordering: never benched, early in setup_order in their own account; no new copies, no Primary effect). | "W2-REPS yes" / "no" |
| W2-HOLDLIST (FYI) | When the hold lifts, the On Deck → Primary order under C3-BAR2 is L3-lowdist, then CWT09-vwaploss-g10, then L3-rsi5hi (only if read on the testing record). Today none is ready. | none needed |
| W2-PRIM (FYI) | Primary: keep L3-fromopen (protected), NM-ETF, RW3, RW5 and ST7. NS5 goes via C3-NS5 (open). No −10R demotion today. | none needed |

## Caveats

- Records are 3-28 sessions. 11-12 alone makes the L3 twins' case, and 11-13 makes GEN-261020-09's. The fit/check
  halves are 2-14 sessions each.
- Correlation is daily R vs Primary's account R on common dates (≥ 8). Most low-rep and GEN setups show n/a.
- The non-overlap view counts same symbol / date / side as overlap; it does not check entry time. Shrunk uses the
  C3-BAR2 prior (−0.10, weight 150), which requires avg > +0.15 at n = 100.
- NS5's +0.1R differs from P3's −0.9R. The R basis differs (LR8 pnl_adj from 11-12); the sign w/o best day agrees.
- No candidate clears t ≥ 3.28 except L3-rsi5hi (3.62 on the testing record) and GEN-261020-09 (4.67, a one-day
  record). Neither passes the one-big-day check.
