Educational only — not financial advice.

# TAPE-1126 pre-registration (written 2026-11-26 18:32 UTC, before any configuration below was built or scored)

Source: consultant memo B (research/consultants_1126/B_TAPE_TRADER.md, rules S1, S2, S3, H1, H2; thresholds copied, not tuned),
diagnosis memo A (setups are index bets), validation standard and goal metrics memo C. Research only: no config, ledger,
decisions.json, backlog or live change.
**Rule 26 guard:** day-type on/off switches and hedge promotions are on the rule-26 "ask the owner first" list. **On 2026-11-26
the owner explicitly asked for steering and diversification research; that request lifts the rule-26 guard for this work.**
Priors flagged as rule 26 asks: REGSW 0/74, GATE1 0/112, BREADTH-1125 0/12, day-type 0/67 (memo C §0), R2 squeeze exit
(squeeze_1125, fails tail), R05 gap-fill long +0.010R (research/bdi/reddit), L19 −0.120R.
Not duplicated: HEDGE-B (research/hedgeb_1126: continuous net-beta hedge H8/H4 = memo B's S4) and REGSTEER-1
(research/regsteer_1126: per-setup state weights). S4 and S5 are not tested here. Live data: B derived S1/S2 from live trades,
so live is in-sample for them and is not scored; the bench is the test.

## Configurations (N = 7)
1. **S1 down-tape long brake.** From 11:30 (entry minute ≥ 690), no new entry of a long lot with β > 0 (long-beta; inverse /
   long-vol ETPs have β < 0 and are not braked) in an affected long setup while SPY fo ≤ −0.30%.
   Affected setups (named now): **NM-ETF-late-dip-di-long** (the Primary long) and the two top live long contenders as fixed by
   REGSTEER-1's PREREG (highest live total R outside Primary, ≥ 30 live trades): **GEN-261020-09-EMAdChgge0p093-Z12lem0p82-
   VWAPcrossesle0-MID-QQQltm0p3-holdtr-long** (home account_gen.yaml) and **GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-
   VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long** (home account_testing2.yaml). NM-ETF is scored inside the Primary book; the two
   contenders are scored standalone under Primary book rules (they are not in Primary).
2. **S2 midday-chop short pause.** From 11:30, no new L3-gap-slope-fromopen-FD / RW3 / RW5 entry while |SPY fo| < 0.30%.
3. **S3+H1-SPY** and 4. **S3+H1-IWM** (book add-on). S3 fires once per day on the first closed 5-min bar ending at T,
   11:30 ≤ T ≤ 13:30, when ALL hold: SPY 1-min low ≤ open × (1 − 0.0040) at some minute in [10:30, T); SPY close (last 1-min
   close before T) ≥ session VWAP × 1.0010; breadth_vwap(T) ≥ 0.70; ≥ 8 of 11 sector SPDRs (XLB XLC XLE XLF XLI XLK XLP XLRE
   XLU XLV XLY) with last close before T > their 09:30 open; Primary net beta NB ≤ −8R per +1% SPY (open lots at the end of
   minute T−1; b_i = side × β_i × 0.01 × entry / risk, β_i as squeeze_1125). Action at T: (a) H1 long sized h = −4 − NB R per
   +1% SPY (IWM config: h / β_IWM→SPY, β = IWM's 60-session point-in-time beta to SPY, else 1.2); (b) no new L3/RW3/RW5 entry
   for the rest of the day; open shorts untouched. The trigger is the same in both configs (SPY tape + book); config 4 only
   trades IWM instead of SPY, with IWM's own stop / target levels. The hedge is an overlay (not in the latch or the −20R halt).
5. **H1-SPY** and 6. **H1-IWM** standalone, 1R per trade: S3's trigger without the sector and book clauses (memo B: "S3 without
   the book clause"; H1 lists SPY VWAP reclaim, the −0.40% post-10:30 dip and breadth_vwap ≥ 0.70). Same instrument rule.
   **H1 trade (both uses):** entry at the open of the first 1-min bar at T; stop = instrument's low over [10:30, T) × (1 − 0.0005),
   capped at 0.60% below entry; target = instrument's prior close if it gapped down (09:30 open < prior close) and prior close >
   entry, else none; once high ≥ entry + 1.5 × risk, stop trails at (highest high − 1 × risk); flat at the 15:55 bar open
   (= 15:54 close). Same-bar stop and target → stop. Cost: 1 bp per side + SEC 20.60 $/M on the sell (as HEDGE-B), in R.
7. **H2 trapped-short gap reclaim long** (stock, standalone, 1R per trade). Universe per day: symbols with 09:30 gap vs prior
   close ≤ −2.657% (L3's threshold), ADV20 (prior day) ≥ $95M, open ≥ $5. Trigger: first closed 5-min bar ending at T,
   10:30 ≤ T ≤ 14:30, whose close > the stock's 09:30 open, after the stock's 1-min low since 09:30 reached ≤ open − 0.50 ×
   ATR14 (daily, prior days), with SPY last close ≥ SPY VWAP at T. Entry next bar open (1-min open at T); stop = session low
   since 09:30, capped at entry − 0.50 ATR; skip if entry − low < 0.15 ATR, or entry ≥ prior close; target = prior close; flat
   15:55; first signal per symbol-day; max 10 names per day (earliest T, then symbol). Cost: LIVE-L (primshorts_1126
   cells_live.json, predict_R by price/stop width/exit kind). Prior art to beat: R05 gap-fill long +0.010R/trade.
   Universe note: 1-min data from cache_hist (2024-09-16..2026-11-04, 1,226 names) and cache_fresh (2023-24, 469 names).

**Cumulative count:** ≈ 2,271 (primshorts_1126) + 2 (HEDGE-B) = ≈ 2,273 before → **≈ 2,280** (plus REGSTEER-1's count if it
reports first). Random brakes, constant cuts and placebos are controls, not configurations. Family bar (info): √(2 ln 2280) ≈ 3.93.

## Engine and books (rule 31: E4 = squeeze_1125 / neveragain minute book engine, re-used; H1/H2 exits on 1-min bars)
Primary rules book: P4 lineup (L3-gap-slope-fromopen-FD, RW3, RW5, NM-ETF-late-dip-di-long), ≥ $5, shorts ETB ≥ 0.9, 30 lots
per setup, ≤ 3 per symbol per setup, 77 slots, burst brake 30/10 min, sticky −2R latch, −20R closed+open halt. Lots = bench10
for the 4 setups (squeeze_1125/gen.py; the lots built by HEDGE-B's build.py are re-used: LIVE-L costs on shorts, LR8 on NM-ETF,
betas). Contenders' lots from REGSTEER-1's bench10 run (same engine), LR8 + LIVE-L on shorts only (they are longs: LR8).
Four contexts: BASE, LO (LATCH-OPEN), L3-OUT, LO+L3-OUT. In L3-OUT, S2 affects RW3/RW5 only.
SPY fo (S1, S2) = close of the last fully closed 5-min SPY bar before the entry minute vs the 09:30 open (memo B: "last closed
10-min (or 5-min) bar"). Breadth = research/breadth_1125/build_breadth.py pct_vwap (469 names, bars < T).

## Splits
FIT 2024-10 + 2025-03..09 (reported only); CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13. The locked block
2024-11-01..2025-02-28 is never read: pyarrow filters at every load and `assert` in every script.

## Controls
- **Random brake** (S1, S2): each eligible candidate lot (affected setup, entry ≥ 11:30, S1: long with β > 0) is blocked with
  probability p = the share of eligible candidates the rule blocks (per setup × split), 20 draws, seed 1126.
- **Constant cut** (S1, S2): every eligible candidate keeps its slot but its R is scaled by (1 − p).
- **S3 placebo:** the same action fired on randomly drawn (day, T) pairs, T on the 5-min grid in 11:30..13:30, drawn among
  pairs where NB(T) ≤ −8 in the reference run, one per day, same number of fire days per split as S3; 20 draws.
- **H1 placebo:** same instrument and exit rules entered at a random 5-min T in 11:30..13:30 on randomly drawn days of the same
  split, same count; 20 draws. **H2 control:** for each H2 signal, a random other universe name the same day entered at the
  same minute with H2's stop / skip / target rules (up to 20 tries per signal); 20 draws.

## Metrics (per context × config × split)
Avg daily R, total R and dR/yr, red days per month (× 21), worst-5 sum, days ≤ −10R, 20-session floor (minimum rolling
20-session sum), best-day share of dR, per-setup dR (improve / worse counts with R). H1/H2: avg R/trade, w/o best day, day t,
trades/yr, sum on the BASE book's worst 10 / 20 days, book + hedge worst-5.

## Pass bars (fixed by the caller; judged on BASE and on LO+L3-OUT, both must hold; other contexts reported)
- **Brakes S1, S2:** on BOTH CHECK and T2: avg daily R improves vs baseline AND beats the random brake (paired daily
  difference vs the mean of the 20 draws) with t ≥ 2, AND fewer than half the affected setups get worse (S1: NM-ETF in the book
  plus the two contenders standalone, pooled = 3 setups, ≤ 1 worse; S2: L3/RW3/RW5, ≤ 1 worse; L3-OUT: RW3/RW5, 0 worse).
  For S1 the book bar is applied to the Primary book; the contenders' standalone results enter the per-setup count and are
  reported with the same avg-R and random-brake test.
- **Hedges S3+H1 (SPY, IWM), H1, H2:** on BOTH CHECK and T2, book + hedge worst-5 sum improves ≥ 20% vs the book, at a cost of
  at most 10R/yr (dR/yr ≥ −10), AND the worst-5 improvement exceeds the placebo's 90th percentile (H2: and its avg R/trade beats
  R05 +0.010R and the random control's mean on both splits). H1 and H2 are added to the BASE / LO+L3-OUT book at 1R per trade.
- Stricter memo-C bar for information: t ≥ 3.46 vs the random control.
If anything passes: a DECISION draft in REPORT.md (journal-only shadow tag first); decisions.json is not edited.
Educational only — not financial advice.
