# Bespoke per-setup rules in Primary: framework and evidence bar (W4 proposal, code W4-FRAME)

*Educational only — not financial advice.* A proposal for the owner; nothing is implemented. It extends
research/l3_bespoke_1117/BESPOKE_RULES.md (which covers per-setup latch levels and exit knobs and the config hooks that
already exist) to **entry-condition rules** ("this setup only when ..."), using what W4 measured.

## Why a stricter bar than "it helped in the fit half"
W4 (RESULTS.md): one rule per setup chosen from each setup's own live failure mode, fit on its earlier sessions.
- 0 of 31 reached the bar; 8 of 31 made the setup worse on later sessions (-58R).
- Raw check gains (+167R) were mostly the arithmetic of removing trades from losing setups: random removal of the same
  number of trades gives +135R. Real excess +32R, ~6% of the +550R the fit half promised.
- Condition effects per setup agree in sign between halves 56% of the time and shrink to ~0.23x. Time of day, gap and
  distance-from-open persist best (corr 0.4-0.5); SPY-at-10:00 and VWAP distance not at all.
- P4 (consultant_p3): 60/60 Workbench variants passed in-sample; filters on proven parents lowered total R 4 of 4.
So the framework judges every rule against **random removal**, on **unseen sessions**, with **enough sessions**.

## The framework
**Scope.** Primary setups only (and a candidate on its way to Primary). One active bespoke entry rule per setup, at
most 2 changed parts (C3-WB). A rule never changes another setup or the account default. L3-gap-slope-fromopen-FD
stays protected until the owner lifts it.

**Step 0 — failure mode first.** The rule must name the failure mode from the setup's live record (e.g. "afternoon
entries", "shallow gaps", "already extended from open") and a mechanism reason; the candidate family (conditions and
cut levels) is written in PLAN.md before any scoring, and its count N goes to the setup's lineage total.

**Step 1 — split.** Fit on the setup's earlier active days, verdict on later unseen ones; **at least 15 active days
and 60 trades in each half** (W4's halves of 5-14 days were too small to separate signal from noise). Below that,
the setup is only tagged (step 2) and waits.

**Step 2 — shadow tag (no live change).** The rule runs in Primary as a journal-only tag (W4-TAGS makes the
conditions available at every decision): each trade carries "would skip" yes/no. No order changes. This collects
the unseen sample at zero cost while the setup trades normally.

**Step 3 — evidence bar (all must hold, on unseen sessions, costs in):**
1. **Excess over random removal > 0**: the rule's ΔR beats removing the same number of random trades from the same
   sessions, at ≥ 95th percentile of 2,000 draws.
2. **Day-clustered paired t of the excess ≥ max(1.5, sqrt(2 ln N))**, N = all candidate rules ever tried for this
   setup's lineage (Workbench copies and bespoke tries included).
3. **Keeps ≥ 70% of trades and ≥ 90% of the top-decile winners** (the big days the owner wants kept).
4. **Plateau**: the neighbouring cut levels (± one step) also show a positive excess.
5. **One-big-day check**: excess without its best day > 0 and the best day < 50% of the excess.
6. **No cross-epoch artefact**: the rule's effect is shown inside one ledger epoch (or each epoch separately) so a
   rule change (latch, LR8, sizing) is not mistaken for a condition effect.
Older evidence (2-year screen, replay) may be shown but counts zero (SRCV1; rank corr ~0 vs live).

**Step 4 — apply.** After hours only (setup-freeze), ledger entry with before/after config, evidence path, N and
the bar; dashboard shows "bespoke: <rule> since <date>". Config: an `entry_when` block on the setup in Primary
(point-in-time conditions only), resolved identically by the runner, the shadow book and the backtest engine.

**Step 5 — review and auto-revert.** Primary keeps the skipped signals as shadow trades. After 10 Primary sessions
the paired difference (taken vs would-have-taken) is reviewed; if the skipped trades' shadow avg R is above a
pre-set tolerance (e.g. > +0.05R/trade, i.e. the rule is skipping winners), it reverts to the parent automatically and the ledger says so.

**Board-level signal.** If the same rule survives on 3+ setups of a family, it is re-tested as a family remedy under
the owner's remedies rule (report each setup improve/worsen), not stacked as many bespoke rules.

## What this means today
- No Primary setup qualifies for a bespoke entry rule now. NM-ETF (27 trades), NS5 (37) and ST7 (49) cannot be split;
  RW3 and RW5 had no rule that held; L3 is protected and its fit-chosen rule failed (-18R on check).
- Leads to shadow-tag first (W4-WATCH): L3 13:30-15:00 entries (-0.36R, n 32; also l3_bespoke_1117 AM/PM — via the
  existing WB4 copy, not a Primary tag), RW3 gap < -2% split (record), heat_fade_long VWAP rule and NS3 prior-day
  rule (arena setups, Graveyard).
- Time of day is the condition most worth tagging first: it is the most persistent per-setup effect (0.49) and the
  first hour is the board's weakest time in both halves.

## Reply codes
- **W4-FRAME yes** — adopt steps 0-5 as the standard for any bespoke Primary entry rule (written into RESEARCH_RULES
  after hours; no live change).
- **W4-TAGS yes** — housekeeping: journal the 12 point-in-time conditions at every decision (reporting only).
- **W4-WATCH yes** — freeze the watch list thresholds (data/results.csv) and score once after 15 more active days.
- **W4-NOFILTER yes** — confirm: no live per-setup condition filter from short live samples.
