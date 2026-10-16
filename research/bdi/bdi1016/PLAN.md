# BDI 2026-10-16 pre-declaration (written before any history configuration below was scored)

*Educational only - not financial advice.*

## Part A: per-trade analysis of 2026-10-16 (descriptive, not gated)
`analyse_1016.py` = `bdi1015/analyse_1015.py` re-dated. It re-uses `research/bdi/nightly1016/trades.csv` (747 real
trades, S6 excluded) and the nightly's SIP 1-minute bars. Same what-ifs (be05, tr05, t05, t1, eod, SAR, re-entry,
opposite side with the hindsight pointer) and the same loss-type classifier. Losers are merged into
`research/bdi/patterns.csv` (idempotent by date). One session: a diagnosis, not evidence (rule 7).

## Part B: early-session market-regime DIRECTION gate (new idea, 2026-10-16)
**Motivation (one session plus one week, not evidence).** 10-16 was a one-way down day (SPY -1.29%, QQQ -2.16% open to
close, lows 15:07). Long books lost (T2 longs -$1,115, T1 longs -$814), shorts won. Over 10-12..10-16 all three
accounts lost and the losses followed the day's direction. Question: does a day class fixed EARLY in the session
(10:00 or 10:30), from index features known at that time, separate the days on which a long-only or short-only
setup loses, well enough that blocking the against-trend side from then on beats the ungated parent and a random
block of the same size?

**How this differs from the failed index filters (and what is NOT repeated).**
- `ix-gate` (912), `bdi-rg-g1..g5` (regime1009, 1,052), `nightly-1012-cwt14-long-index-confirm`,
  `nightly-1014-liq-orl-index-confirm`, `bdi1013-splitgate-*`, `nightly-1015-gapdn-reclaim-short-veto`,
  `bdi1015-short-index-up-veto`: each re-evaluated ONE index feature at EVERY entry bar (SPY above/below open or VWAP,
  SPY up >= k, split tape), so every session was split on a single noisy sign and roughly half of all trades were
  blocked. G5 (breadth at 10:00, fixed for the day) is the closest relative: it is single-feature and two-class
  (every day is "up" or "down").
- Here the class is fixed once per day at T, needs SEVERAL independent features to AGREE, and has a third class,
  **chop**, in which nothing is gated. The aim is to act only on clear trend days (expected 15-35% of sessions),
  i.e. a selective day-type call, not an entry-bar filter. It is the causal form of 10-16's hindsight pointer.
- Not repeated: no SPY-vs-VWAP entry filter, no split-tape rule, no single SPY-sign veto, no per-bar re-evaluation.

**Data.** research/history2y lab frames via `lib.load_month` (open months only; the rule-19 locked block
2024-11-01..2025-02-28 is refused by the loader and `MCF_HIST_ALLOW_LOCKED` is never set), the 09:35-09:45 head rows
(`research/bdi/cwt/test_b/data/headtail.parquet`, read only for open months), production + time-of-day costs and
live semantics exactly as `research/bdi/refire1014/scan.py` `month_hits` (all qualifying decision bars kept; the
gate is applied BEFORE "first qualifying bar per setup-symbol-day", so a bar before T still fires).

**Parents (6, the highest-volume live lab families this week, 3 long / 3 short).**
CWT14-failbrk-orl-p05-long (T2, 256 live trades 10-13..10-16), CWT14-failbrk-pdl-p05-long (T2, 176),
LIQ-orl-sweep-open15-s25-long (T1, 120), CWT14-failbrk-pdh-p05-lowvol-short (T2, 142),
RW7-gapdn-bounce-early-short-FD (T1, 119), RW2-exhaustion-noon-adv150-short-FD (T1, 109).
(heat_fade_* are type heat, not in the lab frames: not testable here.)

**Features at T (bar closing at T, all known at T).** SPY/QQQ/IWM fromOpen (frame); SPY change from the prior close
= (1+gap)(1+fromOpen)-1; breadth = share of frame-universe symbols with vwapDistPct > 0 at T; SPY opening range =
high/low of the 09:30-09:45 bars (head rows tod 935-945), OR break down = SPY close at T < OR low (up: > OR high).

**Classifiers (k = index threshold in %).**
- K1 index-agree: down if SPY, QQQ and IWM fromOpen are all <= -k; up if all >= +k; else chop.
- K2 index+breadth: down if SPY fromOpen <= -k AND breadth <= 0.35; up if SPY fromOpen >= +k AND breadth >= 0.65.
- K3 composite: 6 votes (SPY fo, QQQ fo, IWM fo each beyond +-k; SPY from prior close beyond +-k; breadth <= 0.40 /
  >= 0.60; SPY OR break). down if >= 5 down votes; up if >= 5 up votes; else chop.

**Gate.** From T on, on a trend-down day no long-setup bar qualifies; on a trend-up day no short-setup bar qualifies.
Chop days and bars before T are unchanged.

**Grid (every configuration counted).** classifier {K1, K2, K3} x k {0.25, 0.50} x T {10:00, 10:30} = 12 gates,
applied to each of the 6 parents = 72, plus the 12 gates on the pooled 6-setup book = **84 configurations**.

**Reported for every configuration (failures included).** parent / gated n, exp R, day-clustered t; blocked trades
n, exp R, t; delta (gated - parent) overall, in H1 (<= 2025-12) and H2 (2026-), and in rule-19 up / flat / down
sessions; walk-forward share of test months with delta > 0; random control: the same number of sessions blocked
for that side from T, drawn at random (200 seeds) -> delta 95th percentile; plateau neighbour (other k).
Per regime: each parent's exp R on trend-down / trend-up / chop days (by gate), class frequencies, and how the class
lines up with the rule-19 hindsight regime and SPY's T -> close move.

**Bars (fixed now).**
- Study bar: max(1.5, sqrt(2 ln 84)) = **2.98**.
- Lineage (market-context gates: regime1009 1,052 + ix-gate 912 + splitgate 370 + nightly1014 12 + nightly1015 10 +
  bdi1015 C2 10 = 2,366, + 84) = 2,450 -> **3.95**.
- **Testing-account bar** (per configuration, all must hold): delta > 0; blocked trades' day-clustered t <= -2.98;
  delta > 0 in H1 and H2; WF share of months with delta > 0 >= 0.60; delta > random 95th percentile; plateau (the
  other k of the same classifier and T has delta > 0 and blocked t <= -1.5).
- **Primary bar** adds: gated exp > 0 with day-clustered t >= 3.95, gated exp > 0 in rule-19 up AND down sessions.
- No holdout is scored tonight (the older holdouts sit inside the open history the harness reads; the clean locked
  block is never loaded). A Testing-bar pass gives a proposed Testing config only.

**Total configurations tonight: 84.**
