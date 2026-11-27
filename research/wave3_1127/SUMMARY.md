# Research wave 3 — 2026-11-27 (half day) — synthesis

**Educational only — not financial advice.**

## In plain words

Eight studies ran tonight, each pre-registered before scoring, with costs in (LIVE-L first, LR8 alongside) and the locked
block 2024-11-01..2025-02-28 never read. **Nothing passed cleanly.** One study (QQQOPEN: the IDX3 SPY open-dip rule) met its own
pre-registered bars, but one of its two skeptics refuted the pass, so it is **INCONCLUSIVE**: a real-looking but thin edge
(about t 2) that does not yet justify more size. Two studies called LEAD (MOVEHUNT, SHORTCOST) were refuted by both skeptics:
their "beats random" gains were cost arithmetic, not trade selection. They are **FAIL** here.

What we learned that is useful:
- **The big live GEN arena records (G05 / G07 / G37) are one-day records** and bets on SPY's afternoon direction. History and
  Primary's book reject them; 56 sibling variants also fail.
- **Tight stops lose money live, mostly through costs** (stops under 50 bp: about -0.3 to -0.5 R/trade vs -0.14 at 250 bp+).
  Two independent studies (STOPFLOOR, SHORTCOST) found this; a stop floor measured in *spreads* beat 500 random skips live
  (lead, no spread history to backtest).
- **At 09:50 we can find the day's big movers (4.9x chance) but not their direction (49%).**
- Breadth gates, the published "intraday momentum" rule and the short side of the index open-dip do not work after costs.

Verdict rule used: a PASS/LEAD with 2 skeptic refutations becomes FAIL; 1 refutation becomes INCONCLUSIVE.

## Table

| Study | Verdict (after skeptics) | Configs | Key numbers (R per trade after LIVE-L costs unless stated) | What next |
|---|---|---|---|---|
| ARENASTARS — audit of G05/G07/G37 | **FAIL** | 15 | Live +0.42..+0.49R but best day 97-147% of total; w/o best day -0.33..+0.02; day t -0.4..0.9. History T2 -0.07 / -0.20 / -0.15 (t -1.2 / -3.7 / -2.4). Adding to Primary costs -0.09..-1.03 R/day (0 of 12 configs pass). | Nothing to promote. Idea only: test the same day-type as one SPY position (not logged: untested, expected to fail). |
| STOPFLOOR — tight-stop remedy | **FAIL** (0/18) | 18 | Bench skip/widen rules raise R on CHECK and T2 but none beats random on both splits *and* live. Sc20 passed every bench bar, failed live (68th pct). Live spread floor (skip < 6/8 spreads): 100th pct vs random, 101/120 and 122/147 setups better, best-day share 18-19%. | Lead: shadow-log stop width in spreads and score "skip < 8 spreads" forward 20 sessions (information only). Refit LIVE-L with a spread term. |
| MOVEHUNT — 09:50 mover ranker | **FAIL** (LEAD, 2 refutations) | 14 | Ranker finds movers: top-50 catches 23% (CHECK) / 40% (T2) vs 5% / 13% chance. Direction 49%. 0/6 setups pass (CHECK -0.04..-0.17, T2 -0.04..-0.15). "Selection +0.06..0.09R vs random" refuted: before costs it is 0 (all \|t\| < 1.5) — it was wider stops, not better picks. | Ranker is a reusable tool (most of it is the plain 20-min range). No backlog entry. |
| QQQOPEN — index open-dip on 10y minute history | **INCONCLUSIVE** (PASS, 1 refutation) | 85 | IDX3 (SPY -0.75% by 09:55, SPXL bounce, trail): n 57, +0.42R (LR8 +0.43), day t 2.20 vs bar 2.13, best day 21%, w/o best day +0.34, beats random (incl. volatility-matched) in 500/500. But: on data its parent study never saw t 2.05; week-clustered t 2.09; 5 bp extra stop slip -> t 1.95; 1-min late entry -> t 1.44; neighbours (0.60-0.70) weak; QQQ version fails. IDX1-hold live record is luck (+0.03R, t 0.1). Short side fails (-0.28R, t -4.9). | Keep IDX3 as is (no size change). Backlog: size test with fill haircuts; new lead QQQ -1.5% trail (n 16, +1.15R, t 3.3) for forward test. |
| GENSIBS — 56 siblings of top GEN setups | **FAIL** (0/56) | 56 | No sibling positive on both CHECK and T2; finalists CHECK -0.001..-0.110, T2 -0.08..-0.17. Gross CHECK edge +0.09..+0.12R eaten by ~0.11R cost at R = 0.25 ATR. | Optional research-only: wider-R retest (R = 0.5 ATR). |
| BREADTHGATE — breadth gate on 12 ungated setups | **FAIL** (0/6) | 6 | Best combined t +0.09 (bar 2.64). Raw gains were size cuts (random skip does the same). Signs flip by window, about half of setups worse. | None. Reverse effect on L3 gap-down shorts (t -2.2 / -2.3) noted, guardrail 26 applies. |
| SHORTCOST — cost-zone filters for shorts | **FAIL** (LEAD, 2 refutations) | 6 | R2 history t 3.09 / 2.98 vs random was circular: filter and scoring use the same cost model; before costs gain t 0.38 / 0.56. Live kept trades slightly worse (-0.2005 vs -0.1967). Independent live finding: shorts with stops < 50 bp -0.34R/trade, t -4.7. | No LIVEL-CAP12 entry. The stop-width finding feeds the STOPFLOOR spread-floor shadow. |
| WILDCARD — Gao et al. intraday momentum | **FAIL** (0/24) | 24 | Before costs ~0 bp/trade; after LIVE-L T2 -0.145, CHECK -0.183 (OOS t -14.9); random-direction control 64th pct. | Backlog entry `intraday-momentum-paper` marked parked (tested/failed). |

**Configs tonight: 224** (15 + 18 + 14 + 85 + 56 + 6 + 6 + 24). **Cumulative N ≈ 8,952 → ≈ 9,176.** Lineage bar stays
t ≥ about 4.3; no result tonight reaches it (only the MOVEHUNT ranker's capture t 22-27, which is not a trading result).

Every finalist is listed in each study's REPORT / results file under `research/<key>_1127/`. BREADTHGATE's and QQQOPEN's
REPORT.md were blocked by the harness; their numbers are above and in their results.json.

## Rule changes inside the live windows used

Live windows (10-14..11-25) span: 10-26 GX2 caps, 10-27 GX1, 10-30 Testing cost filter (truncates tight stops in Testing),
11-05 ROLL1, 11-12 LR1/LR8 cost basis and moves to Testing D/E/F, 11-16 ROT1 (Generator -> Testing A/B), 11-17 TSZ1 sizing,
11-19 U9-TGT and the easy-to-borrow list, 11-20 stop rounding / FOOTRACE-EXIT / rotation block 2, 11-21 cost-basis fix,
11-23 BRAKE-BURST (G05's 11-20 burst would be capped: +0.30R, still one-day). All 12 live IDX trades are after 11-17.
History/bench numbers replay today's rules on every day, so no effective date falls inside them.

## Backlog actions (this commit)

- Added `qqqopen-1127-idx3-size-haircut` (risk, idea): size test for IDX3 only after a stop-slippage / entry-delay haircut
  is pre-registered and passed; owner decision, outside market hours, ledger entry.
- Added `qqqopen-1127-idx6-qqq150-trail` (setup, idea/lead): QQQ ≥ 1.5% down by 09:55, TQQQ, trail; forward test in a low-rep home.
- `intraday-momentum-paper` -> parked with the WILDCARD-1127 result.
- Not added (refuted or failed): MH-K6-PRIO, LIVEL-CAP12, GENSIBS-R, breadth reverse gate, arena breadth-index idea.
  STOPFLOOR-K8-SHADOW is recommended as the next information-only step (shadow logging, no live skip) but comes from a FAIL
  study, so it is left to the owner / next wave rather than logged as a passed idea.

No change to config/, setups, exits, docs/live/assignments.json, decisions.json or the ledger.
