# FB1 — "sell the bounce, not the flush" (pre-registered 2026-11-05 17:26 ET, before any 2-year read)

*Educational only — not financial advice.*

Source: BURST1 (MF4 / MF2 shorted after the selling had already happened — 13 MF4 shorts 11:00-11:10 at the QQQ low, stopped
in the +1.4% bounce) vs RW3 (waits for an RSI(5) pop, sold the 11:20 bounce top, +16.5R). Question: is "entry within a hair of
the session low" a general failure mode of lab *short* setups (and its mirror for longs), across families?

Data: 2-year lab trade lists `research/history2y/data/bt_lab1104/sig_*.parquet` (95 setups, costs in, stop first, 15:55
flatten, uncapped). Features from the lab frames at the **entry bar** (same symbol, date, tod — known at the decision).
Locked block 2024-11-01..2025-02-28 not in the frame directory; asserted absent on every table. Split: TRAIN < 2025-09-01,
VALID >= 2025-09-01. R = excess over the setup's own mean in the same split; day-clustered t.

**Configs (N = 4, bar t = max(1.5, sqrt(2 ln 4)) = 1.67):**
1. **FB1-S** (stock flush-chase guard, shorts): pool = every lab short setup; class A = entry-bar `dist_lod_atr <= 0.15`.
2. **FB1-I** (index flush-chase guard, shorts): class A = QQQ `dist_lod_atr <= 0.15` AND QQQ `fromOpen <= -0.50%` at the entry bar.
3. **FB1-L** (mirror, longs chasing a squeeze): pool = every lab long setup; class A = entry-bar `dist_hod_atr <= 0.15`.
4. **FB1-B** (bounce-sold, shorts; the RW3 trait): class A = `dist_lod_atr >= 0.50` AND `rsi5 >= 50`.

**Pass bar (fixed):** guards 1-3: class A excess <= -0.10R in TRAIN AND VALID, day-clustered t <= -1.67, n_A >= 300 on >= 30
days, the filter keeps >= 80% of the pool's trades and >= 90% of its top-decile winners, and no more than 1/3 of the families
are made worse (family = setup prefix before the first '-'; worse = dropped trades' family excess > 0). Config 4: class A
excess >= +0.05R in TRAIN AND VALID, t >= +1.67, n_A >= 300 on >= 30 days (a pass = a boost/priority candidate, not a filter).
Reported for every config: per-family table (improve / worse / by how much), R by SPY day type, A excess w/o its best day.
Live check (descriptive): 11-05 live shorts in the 7 accounts with the 11-05 frames.
A pass → backlog / Testing candidate only (never Primary, never live tonight).
