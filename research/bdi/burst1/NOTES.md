# BURST1 — why Primary's short-heavy 11-05 was not a big gain, and burst remedies (owner 2026-11-05)

*Educational only — not financial advice.* Live = **paper** journals (run_id 1; R = pnl_adj / (|entry − stop| × shares)),
7 accounts, 10-06..11-05, 19,456 rows incl. latch-blocked what-ifs. 2-year = lab trade lists (bt_lab1104, 95 setups,
uncapped, production costs), TRAIN ≤ 2026-02-28, VALID 2026-03-01..10-05. Locked block 2024-11..2025-02 never read.
Research only — nothing in config/ or the trading path changed. Pre-registered in `PLAN.md` (commit 660ea37dd).
**Configurations: 16 (bar max(1.5, √(2 ln 16)) = 2.35). 0 pass.**

## Failures first
- **No remedy passes.** Pacing (a), first-out-first (c) and cluster caps (d) all have large raw deltas (VALID +16k..+22k R,
  t 6.5–8.0) only because they trade less of a losing two-year book. Their **excess delta is negative** (VALID t −2.1..−2.9).
  Measured against the setup's own average in the same window, it is ≈ 0 (t −0.16..−0.34). **Burst entries are not worse
  than a setup's other entries.** Blocking them is like dropping random trades.
- **On live Primary, pacing is a wash:** a_pace_3 −0.7R, c_fof_2 +14.0R, d_cluster_4 −11.4R. It saves MF4 (+8..+11R) but
  costs MF2 (−19..−23R) and RW3 (−20..−26R). Their big days (10-22: MF2 +29.2R / 23 trades, RW3 +24.3R / 25 trades;
  11-05 RW3 +16.5R) **were** bursts. Per-family harm counts (VALID): 3–6 families materially harmed per config
  (GEN, NM, ST4, ST7, NS5, MF5).
- **The open-loss latch (b) cannot catch the 11-05 burst.** At −2R it would not have blocked one MF4 entry: the
  5-min marks were still near 0 at 11:05–11:10, because the bounce started at ~11:09. Its only effect on 11-05 was
  to cut RW3 early (−9.2R vs the live realised latch).
- **The compass gate (e) does nothing on 11-05.** The GATE1 state was DOWN at every checkpoint, so short bursts were
  "with" the tape. Two-year VALID excess t −2.65.
- **The $ risk cap (f) fixes 11-05 in dollars but not on 2 years.** Live Primary +$350..+$817 (11-05 −$419 → +$127 at
  a $50 cap). VALID −$17k..−$40k (excess t −2.7..−3.5). Wide-stop trades were not worse per R on 2 years.

## Step 0 — why MF4-FD and MF2-FD reacted so badly (plain words)
- **Both trigger on *selling that has already happened*.**
  - MF4 = MarcoFlow heat ≤ −40 + 19-bar buy-pressure < −0.25, t05s1: target +0.5R, stop −1R, 1R = 0.25 × daily ATR.
  - MF2 = heat ≤ −30 + RSI(14) 55–65 + flow-sell, t1s05: target +1R, stop at **0.125 × ATR**, i.e. very tight.
  - When a whole tape is washed out, every high-beta name meets the rule in the same 5–10 minutes. That is at the low.
- **RW3-FD needs a pop first** (RSI(5) > 80 in a gap-down name with heavy selling). It sells the *bounce*, not the flush.
- **11-05 (SPY −4.2%, QQQ −5.2%, real crash day):** QQQ low −5.3% at 10:51–11:06, then +1.4% by 11:21.
  - MF4 opened **13 shorts 11:00–11:10** (QQQ −4.9..−5.3%) before any of them exited. 12 stopped 11:10–11:18.
    MFE was 0.0–0.3R, i.e. they entered at the low.
  - RW3 opened its 13 shorts **11:20–14:00**, after that bounce had happened, and banked 11 targets: +16.5R.
  - MF2 opened 8 shorts at 12:05–12:10 (QQQ −4.7%). A ~0.2% index wiggle stopped 7 of them by 12:19 (≈ −8R). Its 12:00
    and 12:15 entries then won 8 of 12, ending −1.7R. The tight stop turns a right-direction trade into a coin toss on noise.
- **11-04 (up day: SPY +0.5%, QQQ +0.5%, high +1.9% at 10:15):**
  - MF4 shorted the 10:25 rollover: 6 tiny winners (+0.06..+0.6R) and 6 full −1R losers. With a +0.5R / −1R geometry
    it needs a win rate above 67%. It had 50%.
  - MF2 shorted the 12:15 rebound: 6 entries 12:15–12:20, all stopped (5 within 12 minutes).
- **Two years agree:** all three are negative overall (MF4 −0.085, MF2 −0.088, RW3 −0.071R per trade, costs in). They
  make money only on down days (MF2 +0.078, RW3 +0.066, MF4 +0.010) and lose on up days (−0.24..−0.32R). Burst entries
  (4+ in 15 min) are no worse than single entries on down days (MF2 +0.095, RW3 +0.106, MF4 +0.020).
- **Same-symbol stacking on 11-05:** MRVL was traded 4 times by 4 setups, CLSK 3, FIX / LRCX 2. MF2 re-entered
  BAI / JPM / IBIT (refire). This was minor: MRVL netted +3.4R.

## $ per R — why 11-05 was −$419 on +4.5R
- **Sizing is notional, not risk:** shares = min(0.25% equity = $250 risk, slot ≈ $3,980 notional). For any stop under
  6.3% the slot binds, so **$ risk = $3,980 × stop%**, and stop% = k × 0.25 × ATR%.
- On 11-05, MF4 shorted high-ATR names (BE, NBIS, TTMI, FPS, AXTI, STRL, FIX: stops 2.0–4.3%). That gave an average
  risk of **$111 per lot (stop 2.8%) vs $49 on 11-04 (1.2%)**, so $121 per R.
- RW3's winners averaged $53 per lot ($48 per R): +16.5R = +$790, while MF4's −10.7R = −$1,293.
- **Rule change behind the jump:** 10-28 Primary slots 160 → 77, so the lot doubled from ~$2k to ~$4k. MF4's average risk
  per lot was $7–30 a day before 10-28 and $10–111 after.

## Step 1 — 11-05 timeline (Primary +4.54R, −$419)
- **SPY:** −1.5% at 10:00, −3.3% at 11:00, bounce to −2.6% at 11:20, −3.9% at 13:00, −4.2% at the close.
  **QQQ:** low at 10:53, then the bounce to 11:20, closed −5.2%.
- **MF4:** 2 winners at 09:55 / 10:11. Then the 11:00–11:10 burst (13 entries), with the per-setup 30-position cap not
  binding.
  - The **realised −2R latch fired at 11:12**, two minutes after the last entry, with about 10 of them still open.
  - It is realised-only, so it can never act before the first stops. The 30 entries it blocked afterwards were worth
    +0.65R (what-if), i.e. neutral.
- **MF2:** latch at 12:14, after 11 entries had opened before the first exit. The 15 entries it blocked were −2.75R
  (what-if).
- **L3-rsi5hi:** latch at 14:43. Its 31 blocked entries would have made **+12.8R** (the latch's cost on the day).
- **14:36–14:49 no-session gap (GitHub outage):** no signals in the 14:40 / 14:45 bars. The broker stops still filled
  (CLSK, IBIT, FBTC, DASH, GLXY exits 14:41–14:43). Few setups were eligible then: L3 was mostly not shortable, then
  latched. **No evidence it changed the day materially**, but missed signals are not logged, so this is unquantified.

## Results (TRAIN / VALID raw delta and t; excess t; live all-accounts; Primary; 11-04 / 11-05 Primary replays) — `decision.csv`
| config | TRAIN Δ (t) | VALID Δ (t) | VALID excess t | live Δ (t) | Primary Δ | 11-04 | 11-05 | VALID setups +/− | fam harmed |
|---|---|---|---|---|---|---|---|---|---|
| a pace N=2/3/4 | +36.3k/+31.6k/+28.0k (8.1/7.2/6.5) | +19.4k/+17.8k/+16.1k (7.3/6.9/6.5) | −2.42/−2.13/−2.08 | +1,423/+1,219/+1,050 (4.1/3.9/3.7) | +3.3/−0.7/−2.0 | +4.9/+3.8/+2.6 | +2.6/+1.5/+1.5 | 49/45, 43/50, 42/51 | 6/6/6 |
| b open-loss latch −2 vs live latch | +10.1k (9.2) | +6.3k (6.8) | −0.31 | +192 (2.2) | +5.2 | +0.3 | **−9.2** | 51/35 | 2 |
| b open-loss latch −3 vs live latch | +7.0k (6.8) | +4.7k (5.4) | **+0.09** | +39 (0.6) | +3.0 | −2.6 | +4.6 | 49/37 | 3 |
| c first-out-first K=2/3/4 | +41.7k/+38.2k/+35.2k | +22.2k/+20.8k/+19.8k (8.0/7.6/7.3) | −2.73/−2.66/−2.52 | +1,603/+1,328/+1,172 | +14.0/−8.6/+0.9 | +8.1/+3.9/+2.6 | −3.1/−5.1/−2.9 | 49/45, 44/49, 42/51 | 4/4/5 |
| d cluster M=4/6/8 | +41.4k/+37.9k/+35.1k | +21.2k/+20.0k/+19.0k (7.7/7.4/7.1) | −2.91/−2.70/−2.56 | +1,555/+1,335/+1,174 | −11.4/−12.4/−24.3 | +1.6/+0.3/−2.3 | +1.1/−1.8/−4.5 | 45/50, 40/55, 40/55 | 4/4/3 |
| e burst+compass B=2/3 | +11.7k/+10.3k (3.7/3.4) | +2.2k/+1.8k (1.3/1.2) | −2.65/−2.65 | +371/+327 (1.9) | +20.3/+21.9 | +6.2/+5.2 | 0/0 | 44/36, 40/39 | 9/11 |
| f $ cap 50/75/100 ($) | +$250k/+$119k/+$56k (2.1/1.5/1.1) | −$17k/−$40k/−$27k (−0.2/−0.9/−0.9) | −3.47/−3.17/−2.72 | +$407/−$74/−$0 | +$817/+$582/+$350 | −$102/−$104/−$45 | **+$546/+$444/+$300** | 37/56, 32/60, 31/61 | 7/8/9 |
- Book shape (VALID, base → a_pace_3): avg R −0.057 → −0.048, w/o best day −0.059 → −0.049, green days 20% → 26%,
  max DD 24.4k → 6.7k R. TRAIN avg R gets *worse* (−0.077 → −0.088): the per-trade quality does not improve.
- **Live excess is positive** for a / c / d (t 2.6–3.0, all accounts). The Graveyard / Testing bursts lost more than
  their setups' average; on Primary the excess is negative (t −0.2..−0.4). Two years (VALID, setup-mean basis ≈ 0)
  and live disagree, so there is no reproducible "bursts are bad" effect.

## Best near-miss → forward shadow `burst1-openloss-latch3`
The open-loss latch at −3R (realised + open mark-to-market), replacing the realised −2R latch.
- **TRAIN:** +7,008R (t 6.83), excess +1,095R (t 1.06).
- **VALID:** +4,714R (t 5.44), excess +83R (t 0.09; setup-mean basis +383R, t 0.44).
- **Live (all accounts):** +38.8R (t 0.58). Primary +3.0R; 11-04 −2.6R, 11-05 +4.6R.
- **Families harmed (VALID):** 3 of 34 (CWT09 −63R, NS5 −32R, NS4 −16R).
- **It fails** the VALID excess t ≥ 1.0 test and the family-harm test.
- **Journal-only shadow:** log when it would latch and what it would have blocked or freed. No trading change.

## What would actually address the owner's flaw (for a later pre-registered study, not tested here)
- The 11-05 loss in **dollars** comes from sizing: equal notional, so $ per R scales with ATR%. The **R** result was
  +4.5R. Equal-$-risk sizing (shares = fixed $ / stop distance) would make the $ P/L track the R the setups are judged
  on. This is a sizing-rule change: backlog, owner decision.
- The R loss of MF4 on 11-05 is the setup itself: it sells exhaustion lows, and on a V-bounce every position fails
  together. A setup-level fix (e.g. MF4 requiring an RW3-style pop) would be setup-specific, so it belongs in that
  setup's own rework, not a system remedy.

## Rule changes in the live window (research/ledger.jsonl effective dates)
- 10-13 per-lot stacking (3 lots/symbol); 10-14 refire option B; 10-20 MF2-FD / MF4-FD promoted to Primary.
- 10-20/21 twin cap + per-setup −2R stop (Graveyard), latched from 10-23; 10-23 stop off in T1 / T2 / Gen.
- 10-27 GX1 5-minute clock gate.
- **10-28 Primary lot ~$4k (slots 77, per-setup 30): doubles $ per R.**
- **10-29 Primary −2R latch.**
- 10-30 Testing cost filter (CF); 11-04 T2 top-500 pool (UNI1); 11-05 Explore 1 / Live Lab start (ROLL1).
- Live comparisons spanning 10-28/10-29 mix sizing and latch regimes. R is unaffected by sizing; $ is.

Files: `enrich.py` (2-year MTM / MFE paths), `rules.py`, `sim.py` (keep flags), `score.py`; `decision.csv`,
`results.csv`, `families.csv` (per-family effect, every config / window), `setups_effect.csv` (per-setup deltas).
