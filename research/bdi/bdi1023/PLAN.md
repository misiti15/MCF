# bdi1023 swarm plan (written 2026-10-23, before any history row was scored)

*Educational only — not financial advice.*

**Idea tested:** backlog `nightly-1023-wide-stop-pct-risk` (nightly1023, live split only, 0 configurations so far).
Live sizing is min(0.25% equity / stop, slot ~$1,930); the slot binds for every stop under ~13% of price, so
$ risk = slot × stop % and the account's $ P/L = Σ R × slot × stop %. Live, the widest-stop quartile has the worst
R in Primary, Testing 1 and Testing 2. Question: on the two-year history, (1) is R worse when the stop is wide as a %
of price (known at entry: stop = dn × 0.25 × daily ATR, stop % = that / entry price), and (2) does skipping or
down-sizing those entries improve the books after costs?

**Data:** gates1021's cached live-shaped signal tables (`load_sig`; 49 live setups of Primary / Testing 1 / Testing 2
that the cache covers — the CWT12/CWT14 family is **not** in it), production + tier costs in, two-year open history,
train ≤ 2025-12-31, valid 2026-01-01..2026-10-07. **Locked block 2024-11-01..2025-02-28 never read** (`no_locked`).
No holdout scored. Books: the setups of each account in `setups_scored.csv` (a setup in two accounts counts in both).

**Configurations (21), per book (Primary, Testing 1, Testing 2):**
- **A. Skip if stop % > X**, X ∈ {1.5, 2.0, 2.5}% → 9.
- **B. Skip if stop % > the setup's own train 75th percentile** (threshold fit on train only) → 3.
- **C. Cap $ risk at slot × X%** (down-size: weight = min(stop %, X) / stop %), X ∈ {1.0, 2.0}% → 6.
- **D. Equal $ risk** (every trade sized to the book's train-median stop %) → 3.

**Bars.** A/B are entry gates and join the gate family (gates1021 718 + bdi1021 196 + regime1022 340 + bdi1022 36 + 12)
N = 1,302 → t ≥ sqrt(2 ln 1302) = **3.79**. C/D are sizing rules, a new lineage (N 9) → t ≥ max(1.5, sqrt(2 ln 9)) =
**2.10**; reported against 3.79 too.

**Pass (all must hold; fixed now):**
- A/B: kept avg R after costs > 0 in train and in valid; day-clustered delta vs the parent book > 0 in train and in valid
  and beats the same gate on the same-minute random control in both; delta ≥ 0 in up and in down sessions; all-data
  delta t ≥ 3.79; keeps ≥ 75% of trades (light touch: gates must not restrict profitable trading).
- C/D: $-weighted P/L (units of slot %, = Σ R × weight × stop %) better than the parent in train and in valid
  (day-clustered delta > 0), delta ≥ 0 in up and in down sessions, all-data t ≥ 2.10, and still better without the
  best delta day. Avg R per trade is unchanged by sizing and is reported.
- Descriptive (not configurations): avg R by stop-% quintile per book × split; per setup, top-quartile vs rest.

Report every row (`results.csv`), failures first. No routing to live tonight whatever the outcome; a pass becomes an
owner DECISION (config change) only.

## Addendum (written after A-D were scored, before E was scored): rework E, the mirror

A-D failed (swarm_out.txt). The descriptive table shows the **tightest** stop-% quintile as the worst cell in every
book × split. That direction was already pre-declared on 10-19 by backlog `gb-1019-noise-floor-stop` ("skip or widen
trades whose stop is under a noise floor", history Primary train +0.023 t 2.7 / valid +0.004 t 0.7 with a 1-min-ATR
floor), so E is that idea's stop-% version. **Caveat stated up front: the quintile table was seen on the same train and
valid rows before E was declared, so E's train/valid are not clean; only a holdout or forward sessions can confirm it.**

- **E. Skip if stop % < X**, X ∈ {0.4, 0.5, 0.6}% → 9 configurations (3 books). Gate family N = 1,302 + 9 = 1,311 →
  bar t ≥ **3.79**. Same pass rules as A/B (kept ≥ 75%, controls, up and down sessions, t).
- Also reported (not a pass criterion): per setup, is the gated avg R ≥ the parent's in both splits; and how many
  setups turn positive in both splits.
Total tonight: **30 configurations**.
