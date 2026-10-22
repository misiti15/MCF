# bdi1022 swarm plan (written 2026-10-22 21:27 UTC, before any history row was scored)

*Educational only — not financial advice.*

Today's notable live pattern (paper, one session, a diagnosis): Primary's +$1,369 came 73% from gap-down shorts
(RW3/RW5/MF2 -FD) entered in the 12:10-12:20 polls just before a Nasdaq leg down (nightly1022), and every long book
lost on a QQQ -1.27% day. [Correction after scoring, plan otherwise unchanged: on 10-20 the family did not lose live, 35 trades +7.6R; the
10-20 vs 10-22 contrast is in the long book, +43.0R vs -74.4R.] Two questions, both answerable with
information known at the minute of entry:

**A. Is "midday" a real window for the gap-down short family, or was 12:10-12:20 one day's luck?**
Family: RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD,
MF2-open-rsimidhi-flowsell-FD, MF4-h40-open-flowsell-FD (the four Primary gap-down / flow-sell shorts).
Variant = keep only entries whose decision time is inside the window (the parent's other rules unchanged):
W1 09:50-10:59, W2 11:00-11:59, W3 12:00-12:59, W4 13:00-15:00, W5 11:30-12:29. 4 x 5 = **20 configs**.

**B. Should long setups stand aside when the Nasdaq is already weak at entry?**
Long setups in the live-shaped signal cache with >= 500 two-year signals (NS5-FD, NS1-FD, NM-HL-T75-pm-long,
NM-AR-AM-gapdown-capitulation-long, NS5, ST4-FD, ST7-FD, ST8-FD) x block when QQQ from-open at entry
<= -0.5% / <= -0.75%. 8 x 2 = **16 configs**. (regime1022 tested SPY-based mirrors R1-R5; st7_1022 tested
QQQ-below-VWAP for ST7 only; this is the QQQ from-open level, not yet tested.)

**Total 36 configurations.** Lineage (gate family gates1021 718 + bdi1021 196 + regime1022 340 + 36) N = 1,290 ->
bar t >= sqrt(2 ln 1290) = **3.78**.

Data: gates1021's cached live-shaped signal tables (`load_sig`, production + tier costs in, two-year open history),
train <= 2025-12-31, valid 2026-01-01..2026-10-07. **Locked block 2024-11-01..2025-02-28 never read** (asserted by
`no_locked`). No holdout scored. Same-minute random control (c_<side>_<geom>) for the beta check.

Pass (all must hold; fixed now):
1. variant avg R after costs > 0 in train and in valid;
2. variant beats the parent per parent trade (day-clustered delta > 0) in train and in valid;
3. delta beats the same gate applied to the same-minute random control in both periods (not plain market beta);
4. delta >= 0 in up and in down regime sessions;
5. all-data delta day-clustered t >= 3.78.
B additionally: keeps >= 80% of trades (light touch, regime1022 S3).
Report every row (results.csv), failures first. No routing tonight whatever the outcome.
