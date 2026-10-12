# CWT test plan: the top 25 setup families from Chat with Traders (pre-declared)

*Educational only - not financial advice. This file is a pre-declaration written on 2026-10-12 before any CWT rule
was scored. Nothing here is a backtest, paper or live result. Guest numbers are claims, unverified.*

Source: `CATALOG.md` / `catalog.jsonl` (411 setups from 336 episode records, 49 families). Selection rule (fixed in
CATALOG.md before this plan): the top 25 families by priority score, excluding families whose equivalent already
failed in MCF (novelty 0: CWT16 RS vs SPY, CWT17 pairs, CWT24 momentum rotation, CWT29 PEAD, CWT39 multi-timeframe
indicators) and families that need data MCF does not have yet (CWT03, CWT15, CWT18, CWT33, CWT37 and below).

## 0. Rules that apply to every family

- **Data and holdouts (RESEARCH_RULES 2, 19; swarm1010/RULES.md).** Intraday: the open two-year history through
  `research/history2y/lib.py` (426 sessions, 1,226 symbols, survivorship caveat). Never load the locked block
  2024-11-01..2025-02-28 and never set `MCF_HIST_ALLOW_LOCKED`; the lead scores finalists on it once. Daily: the
  10-year bars `research/swarm1010/w3_daily/data/daily_2016.parquet` with the W3 splits (train 2016-2022, valid1
  2023-01..2024-10, valid2 2025-03..2026-10) and the locked block excluded.
- **Costs always in (rule 1).** Production cost model (`gates.prod_r`: 1c + 1 bps per side, target fills free of
  exit slippage, +2c on stops). Entries before 09:50 pay **2x** cost (opening spreads, bdi-tod-open-0935-simple).
  Names with gap >= 20% or price < $5 pay **3x** slippage (extended tier). Shorts: easy-to-borrow is only known for
  today, so short results on gappers/runners are flagged "borrow unverified".
- **Fills:** next-bar entries (or the stated stop/limit price when the bar trades through it), stop-first inside a
  bar, gaps through stops fill at the open. One trade per symbol-day per configuration (first qualifying signal).
- **Windows: full day first (owner).** Every intraday family is scored first on the full day - decision bars
  09:50-15:00 (or 09:35-15:00 for package A families whose trigger can fire before 09:50, with the 2x cost) - and
  only second in the guest's own window. Time of day is reported, not assumed.
- **Exits.** Each family has a structural exit **S** taken from the guests (simulated on 5-min rows as in
  `research/bdi/reddit/engine.py` `_sexit`, or on 1-min bars for package A) plus the lab geometries **t1s1 / t05s1 /
  t1s05** (R = 0.25 x daily ATR, `mcf/research/setup_lab.py`), all exits by 15:55 unless a family says otherwise.
- **Gates (fixed, `mcf/research/gates.py`).** exp > 0 after costs; day-clustered t >= max(1.5, sqrt(2 ln N)) with N
  = configurations tried in the lineage (this plan's count for the family **plus** the count already spent by the
  overlapping backlog lineage named in the family line); exp > 0 in up AND down sessions; walk-forward positive share
  >= 0.6; plateau (neighbours' mean > 0); ex-best-day > 0; busiest session <= 10% of trades; n >= 150 for the
  live-probation bar. Report every configuration, failures first, with the random same-side same-window baseline.
- **Earnings blackout conflict.** `config/default.yaml` has `earnings_blackout_days: 4` (owner 2026-10-07: no trades
  within 4 trading days of earnings). The `earn_day` variants of A7, A8 and A9 trade exactly those days, so a pass
  there would need an owner exception to the blackout. Their other level (E = outside the blackout) keeps live parity
  and is reported next to them.
- **Live parity.** A candidate becomes a lab module (SIDE, GEOM, LAYERS, mask(df)) using live-frame columns only;
  any new column below must also be added to the live frame before a Testing YAML is staged (never edit `config/`).

## 1. New features (build once, one process, month by month, git-ignored)

Derived from existing data; no new downloads are needed for the 25 families below.

| feature | definition | source |
|---|---|---|
| `open_d`, `pc` | day open = close / (1 + fromOpen/100); prior close = open_d / (1 + gap/100) | lab frames |
| `vwap`, `hod`, `lod` | close / (1 + vwapDistPct/100); close + dist_hod_atr x atr_d; close - dist_lod_atr x atr_d | lab frames |
| `hod_tod`, `lod_tod` | bar time at which the current session high / low was set | lab frames (cumulative) |
| `rng_used` | (hod - lod) / atr_d | lab frames |
| `run_hod` | (hod - open_d) / atr_d; `drop_hod` = (hod - close) / (hod - open_d) | lab frames |
| `rvol_tod` | cumulative volume since 09:30 / mean cumulative volume at the same minute over the prior 20 sessions | 1-min cache |
| `rvol_15` | volume 09:30-09:45 / its 20-session mean | 1-min cache |
| `or5h/or5l`, `or15h/or15l`, `orh/orl` | 5-, 15-, 30-minute opening range | 1-min cache; `research/bdi/stack1009/data/base.npz` |
| `pd_clv` | prior day (close - low) / (high - low); `pd_hc` = (prior high - prior close) / atr_d | daily table |
| `run3`, `run5`, `upstreak`, `ret5` | prior 3- / 5-day close-to-close return, consecutive up closes, 5-day return to yesterday | daily table |
| `d1_gap`, `d1_rvol`, `d1_inside` | yesterday's gap, volume / 20-day mean, and inside-day flag (for day-2 / day-3 plays) | daily table |
| `earn_day` | earnings reaction day: report date d if Yahoo time is before the open, d+1 if after the close; rows with unknown time use the volume-free rule of research/bdi/earnings 1.2 only as a labelled proxy | `earnings_yf.parquet` (research-data) |
| `beta60` | 60-session beta of daily returns to SPY | daily bars |
| `spy_from_open` | SPY return from its open at the bar close | lab frames (SPY rows) |

Locked-block rows are dropped right after each symbol's load, before any rolling computation.

## 2. Package A - open, gap and in-play setups (9 families, 566 configurations)

Data: 1-min cache from 09:30 (RTH only), daily table for prior-day context, `earn_day`, `rvol_tod`. Universe: the lab
symbols with point-in-time adv20 >= the lowest live tier. Event counts checked before writing this plan (counts only,
no returns; open sessions 2024-10..2026-10 minus the locked block): gap >= +10% 1,800 symbol-days, >= +20% 426,
>= +30% 189; gap <= -10% 1,293; prior 3-day run >= 30% 1,398, >= 50% 346; 5-day drop <= -20% 4,089. Small-cap rules
therefore run on the lab's own biggest movers; float and dilution filters are not available (noted per family).

**A1 CWT02 First Red Day Short** (guests: Kellogg, Edu, Temiz, Glick, Michaud, Bullo, IFYXXI; N = 68, t bar 2.90;
overlap lineage bdi-rdt-r06-red-green)
- Universe R (3): `run3 >= 30%` | `run3 >= 50%` | `upstreak >= 3 and run5 >= 50%`; price >= $1.
- Trigger (2): T1 first bar close < `pc` (goes red); T2 first bar close < `pc` and < `vwap` (Temiz's first add).
- Stop: session high at entry (`hod`). Exits (5): S = hold to 15:55; ON = hold to the next session's 09:35 bar
  (IFYXXI overnight cover); t1s1, t05s1, t1s05.
- Windows (2): full day 09:35-15:00; guest window 09:35-10:30.
- 3 x 2 x 5 x 2 = 60, plus the **day-3 failed push** (Bullo): `d1_ret >= 8%`, `d1_rvol >= 2`, day 2 inside day,
  day 3 opens within 2% below the day-1 high; short the first close below `or5l` after the push fails; stop `hod`;
  4 exits (S, t-geoms) x 2 windows = 8. **Total 68.**

**A2 CWT01 Small-Cap Gapper Morning Fade** (Edu, Gluzman, Frohlich, Miesse, Nico, Dederle; N = 96, t bar 3.02;
overlap P1/L2 gap shorts, heat_fade_short, r05)
- Descriptive first (not a configuration): share of gap >= 20% names closing below the open, and the distribution of
  `hod_tod` (Edu claims about 76-77% close red and the spike peaks near 09:50).
- Universe G (3): gap >= 10% | >= 20% | >= 30%; `rvol_tod` at the signal >= 3.
- Condition H (2): session high set by 09:50 | by 10:15 (`hod_tod`), and no new high since.
- Trigger (2): T1 first bar close < `vwap` after `hod_tod`; T2 lower high: bar high < hod and close < prior bar low.
- Stop: `hod` (+3x slippage). Exits (4): S = 15:55 (fade into the close), t1s1, t05s1, t1s05.
- Windows (2): full day; guest window to 12:00 (Gluzman is flat by noon). 3 x 2 x 2 x 4 x 2 = **96**.
- Missing: float, dilution filings, premarket volume (cheap later: EDGAR, Alpaca extended hours).

**A3 CWT10 Prior-Day High Breakout (Day-Two Play)** (Shapiro x2, Glick, Bellafiore, Edwards, Breitstein, Beggs;
N = 72, t bar 2.92; overlap ST5, r17, r07)
- Setup q (3): `pd_hc` < 0.1 | < 0.2 | < 0.3 (yesterday closed near its high). Catalyst C (2): none | yesterday
  `|d1_gap| >= 4%` and `d1_rvol >= 2`.
- Side (2): long = first bar trading above the prior-day high (`dist_pdh_atr` crosses <= 0); short mirror = prior
  close near the low and first trade below the prior-day low (Bellafiore day-2 below day-1 low).
- Stop: prior close (Shapiro). Exits (3): S = half at +2R, rest to 15:55 with stop moved to entry; t1s1; t1s05.
- Windows (2): full day; guest window to 11:30 (Glick). 3 x 2 x 2 x 3 x 2 = **72**.

**A4 CWT06 Gapper Opening Range Breakout (volume-gated / hold to close)** (Mabe, Maltman, Bullo, Schultz, Muir,
Raschke; N = 32 + the ORB lineages (orb20_a, orb5, t2-orb15, r01, t1-orb-exits ~ 700+), so the bar is >= 3.6)
- (a) Narrowing range (Mabe): |gap| >= 3%, the first k 5-min bars (k = 3 or 6) each with a smaller range than the
  one before; buy stop above that range high on gap-ups, sell stop below the low on gap-downs; stop at the other side;
  exit 15:55 only, or t1s1 (2 exits). 2 x 2 sides x 2 = 8.
- (b) Volume gate (Maltman): `rvol_15` >= 1.5 | >= 2.5; trade the 15-min OR break in the gap direction; stop at the
  OR midpoint; exit 3R target or 15:55 | t1s1. 2 x 2 x 2 = 8.
- Windows (2): full day; guest window 09:45-10:30. **Total 32.** Expect failure (ORB lineage); included only because
  the rvol gate and hold-to-close variants were never run.

**A5 CWT19 Opening Print Fair-Value Fade** (Dennis Dick x3, Tuchman, Porbanderwalla x2; N = 18, t bar 2.40; new)
- Universe: top 300 by adv20. Fair open = `pc` x (1 + `beta60` x SPY gap). Dislocation d = (official open - fair
  open) / atr_d (official open = auction print from the daily bars).
- Rule: d >= +k -> short at the official open; d <= -k -> long. k (3): 0.3 | 0.5 | 0.75.
- Exit at the 1-min close after H (3) minutes: 5 | 15 | 30. Hedge (2): unhedged | SPY beta hedge (SPY leg at its
  open and exit, its costs included). Both sides pooled, each side reported.
- Window: the open only. Cost: 2x (opening auction; MOO fill assumed at the print - flagged optimistic).
  3 x 3 x 2 = **18**. The imbalance-feed versions (closing auction, CWT19 members ep60/ep77/ep174) are not testable.

**A6 CWT43 Failed Gap Auction Fade to Gap Fill** (Dante x2, Jelinek, Adrian; N = 64, t bar 2.88; overlap r05)
- Gap g (2): >= 0.3 or >= 0.5 x atr_d/close in % (up-gaps; mirrored for down-gaps).
- Reference (2): prior-day high | 5-day high (lows for down-gaps). Condition: price trades beyond the reference within
  the first 60 minutes. Trigger: the first 5-min close back inside the reference.
- Side (2): short the failed up-gap / long the failed down-gap. Stop: the session extreme.
- Exits (4): S = limit at the prior close (gap fill) else 15:55; t1s1; t05s1; t1s05.
- Windows (2): full day; guest window 09:35-11:00. 2 x 2 x 2 x 4 x 2 = **64**.

**A7 CWT09 Bad-News Gap-Down Bounce Short** (Sidial, Humbled Trader, Fabrio, Parker; N = 64, t bar 2.88; overlap
RW1/RW3/RW7, er-react)
- Universe G (2): gap <= -5% | <= -10%. Catalyst E (2): outside the earnings blackout (live parity) | `earn_day`.
- Condition: price traded above `vwap` at some point between 09:35 and 10:30 (the dip-buying bounce).
- Trigger (2): T1 (Sidial) first close < `vwap` at or after 10:30; T2 (Humbled) a bounce bar that reaches `vwap` or
  the 09:30-10:00 high and closes in its lower half.
- Stop: the first-hour high. Exits (4): S = 15:55; t1s1; t05s1; t1s05.
- Windows (2): full day; guest window 10:30-15:00. 2 x 2 x 2 x 4 x 2 = **64**. Prior evidence is negative (gap-down
  shorts lose in up sessions; negative earnings reactions bounce) - the regime split decides.

**A8 CWT07 Catalyst Gap-and-Go (Money Trade)** (Bellafiore, Desai, Sykes, Drinon, Edwards, Dimitroff; N = 80,
t bar 2.96; overlap r04, er-react-gap)
- Universe g (2): gap >= 3% | >= 5%, with `rvol_tod` >= 2 at 10:15. Catalyst E (2): outside the earnings blackout (live parity) | `earn_day`.
- Condition at 10:15: the low since the open stayed above `pc` (gap held) and close > `vwap`; consolidation = the last
  6 bars' range <= c x atr_d, c (2): 0.25 | 0.40.
- Trigger: first 5-min close above the consolidation high after 10:15. Stop: the consolidation low.
- Exits (5): S = 15:55; S2 = hold 2 more sessions to the close (daily table, Bellafiore 1-3 days); t1s1; t05s1; t1s05.
- Windows (2): full day from 10:15; guest window 10:15-12:00. 2 x 2 x 2 x 5 x 2 = **80**.

**A9 CWT08 Good-News Gap Opening Dip Buy** (Beamish, Humbled Trader, Holden; N = 72, t bar 2.92; overlap
heat_fade_long - add its lineage count)
- Universe g (2): gap >= 3% | >= 5%, `rvol_tod` >= 2. Catalyst E (2): outside the earnings blackout (live parity) | `earn_day`.
- Condition k (2): the pullback from the open reaches 25% | 40% of the gap (low <= open_d - k x (open_d - pc)).
- Trigger: first 5-min close back above `vwap` after the pullback low (Beamish). Stop: session low.
- Exits (4): S = 15:55 (institutional drift into the close); t1s1; t05s1; t1s05.
- Windows (2): full day; guest window 09:35-11:30. 2 x 2 x 2 x 4 x 2 = 64, plus the alternative trigger (Humbled:
  first bar closing above the prior bar's high after the pullback) on g 3%, E outside the blackout, k 25%: 4 exits x 2 windows = 8.
  **Total 72.**

## 3. Package B - intraday VWAP, level, mean-reversion and breakout setups (7 families, 368 configurations)

Data: the lab frames (09:50-15:00 decision bars), `research/bdi/stack1009/data/base.npz` (orh/orl/pdh/pdl), the
features in section 1, SPY rows for `spy_from_open`. Engine: `research/bdi/reddit/engine.py` (fixed geometries from
the frames + structural exit S on the 5-min rows + gates).

**B1 CWT04 Backside Lower-High Short** (Edu, Katz x2, Trost, Shapiro, Lee, Gluzman; N = 32 + NS3/RW4 lineage, t bar
>= 2.63; overlap NS3, x_vwaploss_run)
- Run a (2): `run_hod` >= 1.5 | >= 2.5 daily ATRs. Breakdown: `drop_hod` >= 0.4 and close < `vwap`.
- Trigger (2): T1 (Edu) bar high reaches `vwap` (within 0.05 atr_d) and closes back below; T2 (Katz H pattern) the
  bounce retraces 38-62% of the drop and a bar closes below the prior bar's low.
- Stop: the highest high since the breakdown. Exits (4): S = 15:55; t1s1; t05s1; t1s05.
- Windows (2): full day; guest window 10:30-15:00. 2 x 2 x 4 x 2 = **32**.

**B2 CWT13 Stretched-from-VWAP Fade (ATR-gated)** (Jeff Davis x2, Fabrio, Cady, Chan, Harris, Ruffley, Cortes Lopez;
N = 64 + r03 lineage, t bar >= 2.88)
- Gate: `rng_used` >= 0.4 (Davis: 40% of the average range done). Stretch z (2): |close - vwap| >= 0.5 | 0.75 x atr_d.
- At the extreme: short when `dist_hod_atr` <= 0.05 and the next bar makes a lower high; long mirror at the low.
- Universe U (2): all lab symbols | SPY, QQQ, IWM, DIA only (the guests trade the index).
- Side (2). Stop: the session extreme + 0.1 x atr_d. Exits (4): S = limit at `vwap` else 15:55; t1s1; t05s1; t1s05.
- Windows (2): full day; guest window 11:00-15:00 (Fabrio: after the first hour). 2 x 2 x 2 x 4 x 2 = **64**.

**B3 CWT14 Failed Breakout / Stop-Run Reversal** (Adam Ryan, Ben BLB, Frohlich, Adib, Kyle Ng x2, Schwager, Walker,
Singh, Carreon; N = 96 + r15 lineage, t bar >= 3.02; overlap r15, ST1, bdi-reddit-orb-failed-break)
- Level L (2): prior-day high/low | 30-min opening range high/low. Poke p (2): price trades >= 0.05 | >= 0.10 x atr_d
  beyond the level, then a 5-min close back inside within 3 bars.
- Volume V (2): any | the poke bar's volumeRatio < 1 (Ben: the push comes on low volume).
- Side (2): fade the poke. Stop: the poke extreme. Exits (3): S = limit at the opposite side of the range (prior-day
  midpoint for PD levels, the other OR side for OR levels) else 15:55; t1s1; t05s1.
- Windows (2): full day; guest window 09:50-12:00. 2 x 2 x 2 x 2 x 3 x 2 = **96**.

**B4 CWT12 Intraday Flag / Coil Breakout** (Dante x2, Kellogg, TAGR, Michaud, Trost, Cortes Lopez, Carreon,
Carter, Barrett, Cady; N = 32 + r08 lineage, t bar >= 2.63)
- (a) Coil under resistance (Dante): resistance = `hod` touched >= 3 times (bar highs within 0.1 x atr_d) today; the
  last n bars (n = 4 | 6) have ranges < 0.5x their 20-bar mean and close within 0.25 x atr_d below it; buy at the
  close; stop below the coil low; S = limit at resistance + 0.25 x atr_d (the probe) else 15:55; plus t1s1, t05s1,
  t1s05. 2 x 4 = 8.
- (b) Spike-pullback-breakout (Kellogg/TAGR/Michaud): push from the open >= s x atr_d (s = 1 | 2), pullback of 30-50%
  of the push holding above `vwap`; buy the first close above the pullback's starting high; stop at the pullback low;
  4 exits. 2 x 4 = 8.
- Windows (2): full day; guest window 09:50-11:30. **Total 32.**

**B5 CWT05 Panic Flush V-Reversal Long** (Porbanderwalla x2, Breitstein x3, Gluzman, Kellogg, Michaud, Shapiro; N =
64 + heat_fade_long / NS5 lineage, t bar >= 2.88)
- Flush m (2): the last 6 bars fell >= 0.5 | >= 0.75 x atr_d and the close is a new session low. Climax v (2):
  vol_climax >= 3 | >= 5 on one of the last 3 bars.
- Prior decline D (2): none | `ret5` <= -15% (Breitstein right side of the V).
- Trigger: the first bar that closes above the prior bar's high. Stop: the flush low.
- Exits (4): S = limit at `vwap` else 15:55; t1s1; t05s1; t1s05. Windows (2): full day; 09:50-11:30.
  2 x 2 x 2 x 4 x 2 = **64**.

**B6 CWT46 Afternoon Breakout in a Strong Mover** (Desai, Capablanca; N = 32, t bar 2.63; new)
- Universe u (2): fromOpen at 12:00 >= 4% | >= 8%, with `rvol_tod` >= 2.
- Midday range = 11:30-13:30 high/low; width w (2): <= 0.3 | <= 0.5 x atr_d. VWAP condition (2): none | the midday
  low stays above `vwap` (Capablanca).
- Trigger: first 5-min close above the midday high between 13:30 and 15:00. Stop: the midday low.
- Exits (4): S = 15:55 (into the close); t1s1; t05s1; t1s05. Window: the setup defines its own window (13:30-15:00),
  so there is no full-day version; reported as such. 2 x 2 x 2 x 4 = **32**.
- Note: this is the long side of what exhaustion_short (Afternoon Blow-off Short, retired) shorts.

**B7 CWT11 VWAP Trend Pullback - untested variants only** (Stolcers, McDermitt; N = 48 + r09/r02 lineages, t bar
>= 2.78)
- (a) First oversold in a breakout name (McDermitt): daily close within 2% of the 252-day high in the last 5 sessions
  and 20-day return >= 15%; the first bar of the session with RSI(14) < 30 | < 25; buy the next close above the prior
  bar's high; stop at the session low; 4 exits (S = limit at the session high else 15:55; t-geoms). 2 x 4 = 8.
- (b) RS reset (Stolcers): RS = fromOpen - beta60 x spy_from_open. RS max by 10:15 >= +2% | >= +3%; RS then falls
  below 0.5x its max | below 0, and a bar closes with RS rising and above the prior bar's high; stop at the dip low;
  4 exits. 2 x 2 x 4 = 16.
- Windows (2): full day; guest window 10:15-15:00. (8 + 16) x 2 = **48**.

## 4. Package C - daily, swing and calendar setups (9 families incl. 2 overlays, 117 configurations)

Data: 10-year daily bars (W3 file and loader, eligibility as `research/bdi/saturday1010/new/lib.py`), earnings dates
for C6, FOMC dates (public calendar, to be typed in as a static list before scoring). Fills at the open/close prints
(MOO/MOC) or at a limit price when the day's range trades through it. Costs 1c + 1 bps per side, 3%/yr borrow on
shorts. Report net and **net excess vs the equal-weighted eligible universe** (W3 found most daily long returns are
market beta), per split, up/flat/down months, 2018 and 2022.

**C1 CWT21 Oversold Dip Buy with a Limit Entry** (Radge x2, Bensdorp x2, Parker, Hanna x2, Burns, Hoang, Kruger,
Gogolak, Kershner, Ghauri, Furey; N = 28 + W3 Connors 64 + sat1010 reworks, t bar >= 3.0)
- Long signal at close t: close > SMA200; sig (2): RSI(3) < 15 | RSI(2) < 5. Regime R (2): none | SPY > SMA200.
- Entry: buy limit at close x (1 - L) on day t+1, L (3): 2% | 3% | 5%; filled if the day's low <= limit (fill at
  min(open, limit)). Exit (2): first close > SMA5, max 5 sessions | next session's open (Radge's open exit).
  2 x 2 x 3 x 2 = 24.
- Short mirror (Bensdorp): RSI(3) > 90 and 3 up closes; sell limit +L above the close, L (2): 3% | 5%; same 2 exits.
  2 x 2 = 4. **Total 28.** The untested piece is the limit-below-close entry; the market-order version already failed
  the locked block.

**C2 CWT22 Tight Base Breakout (VCP / Flag / Box)** (16 guests incl. Kullamagi, Gluzman, Ritchie, Rolly, Brandt x2,
Komar, Koenig, Grimes, Leavitt, Farley, Haber, Greer, Carreon, Stolcers, Glick; N = 20, t bar 2.45; overlap W3 F3)
- Universe: close > SMA50 > SMA200, within 25% of the 252-day high; momentum M (2): 63-day return in the top 10% |
  top 20% of eligible stocks.
- Base: the last B (2) = 10 | 20 sessions with (max high - min low) / close < w (2) = 8% | 12%.
- Trigger: close above the base high -> buy the next open. Stop: the base low.
- Exit X (2): first close below SMA10 | SMA20, max 40 sessions. 2 x 2 x 2 x 2 = 16.
- Intraday-entry variant on the two-year 5-min history (Kullamagi): on the breakout day buy the first 5-min close
  above the 5-min / 30-min opening-range high (2) when the price is above the base high; same stop; exits X (2).
  2 x 2 = 4. **Total 20.**

**C3 CWT25 Uptrend Pullback to a Moving Average** (Greer, Rolly, Sayce, Shannon, Jesse, Falde, Robinson; N = 8,
t bar 2.04)
- Condition: close > SMA200 and SMA50 rising (20-day slope > 0); the day's low within 1% of SMA k (2) = 20 | 50 and
  the close above it.
- Entry (2): buy at that close | buy stop above that day's high on the next day (Rolly: buy the uptick).
- Stop: 1 x ATR(14) below the MA. Exit (2): second close below SMA20 | 10 sessions. 2 x 2 x 2 = **8**.

**C4 CWT23 New-High Breakout with a Trailing Stop** (Boorman, Radge, Walsh, Parker x2, Burns, Ivanhoff, Shannon,
Lindzen, Grittani; N = 12, t bar 2.23; overlap lh-52wh-fail)
- Signal: close at an N-day high, N (2) = 50 | 252, with SPY > SMA200. Volume V (2): none | volume >= 1.5x its
  50-day mean (Parker's unusual volume). Buy the next open.
- Exit (3): Donchian 20-day low | Donchian 50-day low | bracket +5% / -7% with a 5-day time stop (Parker).
  2 x 2 x 3 = **12**.

**C5 CWT26 Calendar Effects** (Ziemba x3, Hanna, Kyle Ng, Sharkness, Tracy; N = 7, t bar 1.97)
- (a) FOMC eve to FOMC day (Hanna): buy SPY at the close before the FOMC day; condition (2): all | prior-day return < 0;
  exit (2): FOMC-day close (10 years) | 13:55 bar (5-min, two-year history, before the announcement). 4 configs.
- (b) Turn of the year (Ziemba): long IWM / short SPY equal dollars from the first close on or after Dec 15 to the
  last December close. 1 config.
- (c) January loser rebound (Sharkness): bottom decile | bottom quintile (2) of YTD return on Dec 15 among eligible
  stocks, buy the Dec 20 close, sell the Jan 15 close. 2 configs.
- **Total 7.** (b) and (c) have about 10 yearly events: descriptive only, they cannot pass the bars. The FOMC-week day
  filter (Kyle Ng) is applied as a reporting split on packages A/B, not as a configuration.

**C6 CWT47 Event-Anchored VWAP Level** (Shannon, Bruzzese; N = 4, t bar 1.67; overlap AVWAP video tests)
- Anchor (2): the latest earnings reaction day (`earn_day`, 2019+) | the 252-day-high day. Daily anchored VWAP from
  the anchor (typical price x volume).
- Long when the day's low touches the AVWAP from above (within 0.5 x ATR) and closes above it, close > SMA50; buy the
  next open; stop 1 ATR below the AVWAP; exit (2): first close below the AVWAP | 10 sessions. 2 x 2 = **4**.

**C7 CWT45 Index Day-Count / Streak Bias** (Gogolak, Morad, Raschke, Breitstein; N = 10, t bar 2.15)
- SPY, QQQ, IWM pooled (each reported): N (3) consecutive down closes = 3 | 4 | 5 -> buy the close; exit (2): first up
  close | 5 sessions. 6 configs.
- Day 3 (Raschke): two closes in the top 25% of the day's range inside the 20-day range -> short day 3 at the open;
  exit (2): close | first down close. 2 configs.
- Day 5 (Morad): after 4 lower lows, buy the 5-min reclaim of the prior-day low on day 5 (two-year history); exit (2):
  15:55 | t1s1. 2 configs. **Total 10.**

**C8 CWT27 Index regime filter as an overlay** (13 guests; N = 12, t bar 2.23)
- Gates (3): SPY > SMA200 | SPY > SMA10 (Holdford) | in an IBD-style follow-through state (index up >= 1.25% on higher
  volume on day 4+ of a rally attempt, valid until a close below the rally low; Haber).
- Applied to the pre-declared base configuration of C1, C2, C3 and C4 (the first configuration listed in each).
  3 x 4 = **12**. Reported as the change in each book; never used to choose among C1-C4 configurations.

**C9 CWT40 Exit and sizing overlays on the daily books** (11 guests; N = 16, t bar 2.35; overlap sw-w4-book-exits)
- Overlays (4): two-day close below SMA20 (Haber) | two-stage 8/21 EMA trail (Kidd) | 3-ATR Keltner target (Carter)
  | equity-curve governor (Komar: half size when the book's 20-trade equity curve is below its 20-trade average).
- Applied to the base configurations of C1-C4: 4 x 4 = **16**.

## 5. Counts

| package | families | configurations | largest single-family bar (this plan only) |
|---|---|---|---|
| A open / gap / in-play | 9 | 566 | t >= 3.02 (A2) |
| B intraday VWAP / level / reversion / breakout | 7 | 368 | t >= 3.02 (B3) |
| C daily / swing / calendar (incl. 2 overlays) | 9 | 117 | t >= 2.58 (C1) before its lineage add-on |
| **total** | **25** | **1,051** | sqrt(2 ln 1,051) = 3.73 if the round is judged as one lineage |

Each family is its own lineage for the t bar (plus the overlapping backlog lineage named above). The lead may instead
judge the whole round as one lineage (t >= 3.73); the report gives both.

## 6. Ideas that need data MCF lacks (not in this round)

| data | families it unlocks | cheap source? |
|---|---|---|
| Premarket / overnight bars (04:00-09:30) | CWT37 premarket high/low break, reclaim and fade; CWT01/CWT07 premarket volume filters; CWT15 overnight high/low tags | **Yes**: Alpaca SIP 1-min extended hours (already licensed). To save disk, fetch only symbol-days with |gap| >= 3% (about 35k open-history symbol-days; about 20k at |gap| >= 4%). |
| Float / shares outstanding | CWT01, CWT02, CWT03 low-float filters | **Yes**: SEC EDGAR XBRL companyfacts (dei:EntityCommonStockSharesOutstanding), quarterly, free. |
| Dilution filings (S-3 shelf, ATM, 424B, warrants) | CWT01, CWT03 "agenda" small-cap shorts | **Yes**: EDGAR full-index (free), some parsing work. |
| News headlines with timestamps | CWT07/CWT08/CWT09 beyond earnings; CWT28 news overreaction | **Yes**: Alpaca news API history (Benzinga), already in the subscription (backlog sw-w5-news-history). |
| Economic release and FOMC calendars | CWT26 FOMC, CWT28 data releases | **Yes**: federalreserve.gov, BLS/FRED calendars (free). |
| Sector / theme mapping | CWT18 leader-laggard, CWT22 group strength | **Yes**: SEC SIC codes (free) or correlation clusters from our own bars. |
| Index membership changes | CWT33 rebalance / reconstitution | **Partly**: FTSE Russell preliminary lists, S&P press releases (free, manual). |
| VIX history | CWT05 crash-regime flag, CWT27 VIX > 30 | **Yes**: CBOE CSV (free). |
| Halt / LULD history, IPO calendar | CWT38 | **Partly**: Nasdaq Trader halts (recent only); IPO dates from first bar. Most IPOs are outside the lab universe. |
| Opening/closing auction imbalance feeds | CWT19 imbalance versions | **No** (paid exchange data). |
| Level 2 depth / full tape | CWT36 order-flow reads | **No** (MCF's 1-second order-flow sample already failed). |
| Options chains / IV history | CWT30 volatility premium | **No** for history (Alpaca options from 2024 only; OPRA paid). |
| Futures, crypto, FX, betting, Treasuries | CWT31, CWT34, CWT35 | Out of scope for MCF's stock/ETF runner. |

## 7. Order of work (suggested)

1. Build the section 1 features once (one process, under 2.5 GB RAM, month by month).
2. Package B first (lab frames and the reddit engine exist; fastest), then A (needs the 1-min opening work and
   `earn_day`), then C (daily, cheap).
3. Append every family to `research/backlog.jsonl` with prefix `cwt-` (failures too) and keep
   `python -m pytest tests/test_backlog.py` passing. The lead scores finalists on the locked block once.

## Amendment 2026-10-12 (package C, worker CWT-C), written before any package C configuration was scored

- **C8 and C9 also run on the longhold book S6** (`S6_mom12_1rev_N20_W`, lead's instruction for this round): the three
  C8 gates and the four C9 overlays applied to S6 = **+7 configurations; package C total 124** (C8 15, C9 20). S6 is a
  weekly top-20 weight book, not a trade list, so the overlays are mapped as follows: C8 gate off at the weekly signal
  -> the whole book goes to cash (0 return) until the next weekly signal with the gate on; C9 exits act on single names
  between weekly rebalances (a name is sold at the next open after its exit signal, or intraday at the Keltner limit;
  the freed weight sits in cash until the next weekly rebalance, which rebuilds the normal S6 targets); the C9
  governor uses **20 weekly rebalances** as its "20 trades" (half exposure, rest in cash, when the S6 equity at the
  signal close is below the mean of its last 20 weekly closes). S6 lineage for the bar: 123 configurations already
  spent (longhold 105 + sat1010 crash guards 18) + 7 = 130, t bar sqrt(2 ln 130) = 3.12; S6 has had one locked look,
  so any S6-overlay version would be look 2 (t >= 1.5) on the locked block.
- **FOMC dates (C5a)** are typed from the public Federal Reserve calendar from memory, because federalreserve.gov is
  blocked from this machine (proxy 403). Scheduled statement days only (the unscheduled 2020-03-03 and 2020-03-15
  actions are excluded, so March 2020 has no event). The list is in `test_c/families.py` and must be checked against
  federalreserve.gov before any live use.
- **Implementation choices the plan left open** (fixed now, see `test_c/NOTES.md` section 1) do not change any grid
  level or count.

## Amendment 2026-10-12 (package A, worker CWT-A), written before any package A configuration was scored

No grid level or count changes (package A stays 566 configurations). Points the plan could not be run exactly as
written, or left open, fixed now (details in `test_a/NOTES.md` section 1):
- **Costs are stricter than written, never looser.** The entry-side multiplier is `gates.tod_cost_mult` (3.8x before
  the 09:35 bar close, 2.1x to 09:50, 1.4x to 10:30; ledger 2026-10-10-tod-costs), which is >= the plan's 2x before
  09:50; it is also applied to non-target exits filled before 10:30 (ON exit at 09:35, A5 time exits, early stops).
  A5's entry at the opening auction print pays the plan's 2x (an auction fill has no spread to cross). The 3x
  extended-tier slippage applies to |gap| >= 20%, price < $5 **and** adv20 < $5M (the config's extended tier).
- **Universe floor:** point-in-time adv20 >= $1M (the extended tier, `extended_min_avg_dollar_volume`) and price >= $1.
- **Unit of R:** every exit (structural or lab geometry) is reported in R = 0.25 x daily ATR, so exits are comparable
  and the gates apply unchanged. The lab geometries use their own +-kR target/stop (the structural stop is not added).
- **`earn_day` for the 53 rows with unknown report time** is left out (no proxy): too few to matter.
- **A1 day-3 play:** "push fails" = the first 5-min close below `or5l` (the 09:30-09:35 bar low), decision bars from
  09:40.
- **A3:** "first bar trading above the prior-day high" = a buy stop at PDH armed from 09:35 on days that open below
  PDH and have not traded above it before 09:35 (mirror for the short). The Shapiro stop at the prior close is floored
  at 0.05 x atr_d below the entry when the prior close is at or within that of PDH (zero-risk otherwise); the S exit's
  "+2R" uses that structural risk.
- **A4 (b):** the plan gives no gap threshold for the volume-gated ORB; it uses the same |gap| >= 3% as (a). Its "3R
  target" uses the structural risk (entry to the OR midpoint).
- **A7:** T1 fires only at or after 10:30, so its full-day and guest-window versions are identical; both are still
  counted (8 duplicated configurations). "Price traded above vwap" = a 5-min bar high above vwap (bar closes
  09:35-10:30, or the trigger bar itself for T2). Stop = the session high so far for triggers before 10:30.
- **Controls (rule 6):** the same-time control for each trade is the mean outcome of a deterministic ~3% sample of the
  same day's universe at the same entry bar, side and exit (structural, ON and S2 exits use the hold-to-15:55 control).
- **Earnings blackout:** E-out = no Yahoo report date within +-4 business days (as `mcf/data/earnings.py`); symbols
  without Yahoo coverage (~17%) count as outside the blackout, like a live day with no calendar entry.

## Amendment 2026-10-12 (package B, worker CWT-B), written before any package B configuration was scored

No grid level or count changes (package B stays 368 configurations). Points the plan could not run exactly as written,
or left open, fixed now (details in `test_b/NOTES.md` section 1):
- **Exits to 15:55.** The lab frames and `stack1009/base.npz` stop at the 15:00 bar, and `reddit/engine.py` `_sexit`
  goes flat at that 15:00 close, so the plan's "all exits by 15:55" cannot run on them. The 5-min bars 09:30-09:45 and
  15:00-15:55 (OHLC, session VWAP on 5-min hlc3 as `mcf.features.vwap`) are rebuilt from the 1-minute cache
  (`data/cache_hist/1Min`, locked-block rows dropped at read) and appended to each symbol-day; every exit (structural S
  and the lab geometries, re-simulated with the lab's rules: stop-first in a bar, target as a free limit, close of the
  15:55 bar) runs on these rows. The re-simulated geometries are checked against the frames' `r_*` columns.
- **Unit of R:** every exit is reported in R = 0.25 x daily ATR (as `_sexit` and package A). The structural S exit
  uses the family's stop price; the lab geometries use their own +-kR target/stop. Entry = the signal bar's close (the
  lab / engine convention); a trade whose structural stop is not beyond the entry is skipped.
- **Costs** = `gates.prod_r` rules with `gates.tod_cost_mult` on the entry side (1.4x before 10:30; no package B
  entry is before 09:50), x3 slippage (per share, bps and the stop extra) when |gap| >= 20% or price < $5.
- **Universe:** point-in-time adv20 >= $95M (the lab frames / base.npz floor and the Testing -FD min_adv).
- **B5 flush** "last 6 bars fell" = close 6 bars ago minus the close >= m x atr_d, and "new session low" = the close
  below the prior low of the day; the trigger is the first later bar that closes above the prior bar's high (stop: the
  session low). **B4 (a)** "20-bar mean" = mean range of up to 20 session bars before the coil (>= 6 needed; the
  frames carry no prior-day bars). **B6** `rvol_tod` at 12:00 = 09:30-12:00 volume / its mean over the prior 20 open
  sessions (1-minute cache). **B7 (a)** 252-day high and 20-day return come from the 10-year daily file
  (`w3_daily/daily_2016.parquet`, locked rows dropped; return windows that span the dropped block are NaN).
  **B3 OR levels** exist only from the 10:05 bar close (the 30-min range ends at 10:00).
- **Neighbours for the plateau gate:** configurations of the same family, exit and window that differ in one grid
  level. **Market-neutral control:** each trade minus beta60 x SPY's return over the same bars, SPY leg costs in.
- **FOMC-week split** (reported only, never used to select): scheduled statement days typed from memory (2024-11-07,
  2024-12-18, 2025-01-29, 03-19, 05-07, 06-18, 07-30, 09-17, 10-29, 12-10, 2026-01-28, 03-18, 04-29, 06-17, 07-29,
  09-16); unverified against federalreserve.gov (blocked from this machine).
- **C8 follow-through state, amended 2026-10-12 before scoring (only its on-share was looked at, no return):** as
  written ("valid until a close below the rally low") the state never turns off after March 2016 (SPY never closed
  below the February 2016 rally low again), so the gate would be on 100 % of the time and identical to no gate. The
  IBD-style state therefore also turns **off on distribution**: 6 or more distribution days (SPY close down >= 0.2 %
  on volume above the prior day) within the last 25 sessions. Everything else unchanged; the count stays 12 (+3 S6).
