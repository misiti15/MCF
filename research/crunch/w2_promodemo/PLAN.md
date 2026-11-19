Educational only — not financial advice

# W2-promodemo — pre-registered plan (written 2026-11-18 ~16:40 ET, before any scoring)

Crunch workstream W2 (owner crunch 11-18..11-20). Research + proposals only: no config, runtime, ledger or
assignments change; promotion hold (11-17, PROMO2) stands; C3-BAR2 / C3-EXIT100 / GY-LIFE are still **open**
decisions, so this review scores against them *as proposed* and every output is a proposal with a reply code.

## Data
- Live journals, `run_id = 1` (the `paper` run in `runs`), all ten accounts, 10-06..11-18 (11-18 included if its
  trades are closed on the state branch). Shadow (run 3) and what-if (run 2) never count (RULE 21 / SRCV1).
- R after costs = pnl_adj / (|entry − stop| × shares); r_multiple only where pnl_adj is missing. Locked block
  2024-11-01..2025-02-28 is excluded by construction (not in live data) and never read.
- Identical signals across accounts (setup | symbol | date | entry minute) counted once ("dedup").
- Universe: every setup listed under an account in `docs/live/assignments.json` (as of 11-18), plus the 20
  GY-BENCH guests scored for their home account; Gen setups only with >= 10 trades. Graveyard residents for (e).

## Definitions (fixed now)
- **Traded sessions** = dates with >= 1 trade. **Active days** = dates with >= 1 journaled signal (taken or
  skipped) in run 1 (benched sessions emit none, so they are excluded as C3-ROT asks).
- **Avg R w/o best day** = mean R of trades not on the best-R date; **share** = best day R / total R (`1 day` tag at
  >= 50%, n/a when total <= 0). **Green-day %** = share of traded sessions with day R > 0. **Last-5** = R over the
  last 5 traded sessions. **Shrunk** = n/(n+150)·avg + 150/(n+150)·(−0.10).
- **Non-overlap record** (C3-BAR2) = the setup's trades whose symbol | date | side was not also traded by any current
  Primary member in Primary that day. For Primary members: overlap against the other five members.
- **Corr to Primary** = Pearson correlation of the setup's daily R with Primary's daily account R on the dates both
  traded (>= 8 common dates, else n/a); plus same symbol-day-side overlap %.
- **Record used**: (a) Primary account record since its Primary admission (first Primary trade date in the window);
  (b)-(d) the setup's live record outside Primary, dedup; (e) Graveyard-account record + whole record.

## Rules applied (4 rule sets, no tuning -> configurations counted: 4)
1. **C3-BAR2 promotion** (b, c): >= 30 trades, >= 8 traded sessions, >= 15 active days, non-overlap avg R w/o best day
   > 0, green-day % >= 50, best-day share < 50%, shrunk > 0. "Ready" = all pass; "Near" = fails only shrunk and/or
   active days (shown separately, not proposed for a move).
2. **Primary demotion** (a): −10R cumulative in Primary since admission (C3-BAR2 / W1-BAR demotion). Also shown:
   C3-NS5 status and EXIT100 numbers for context.
3. **C3-EXIT100** (d): non-Primary record >= 100 trades, >= 15 active days, avg R <= −0.05 and avg w/o best day <= 0.
   Low-activity trims never go to the Graveyard (owner 11-03); -WB copies judged on their own record.
4. **GY-LIFE graduation** (e): >= 15 Graveyard traded days, >= 30 Graveyard trades, whole record avg w/o best day > 0,
   best-day share < 50%.

## Honesty checks
- t-stat of avg R (trade level) shown for every candidate; bar t >= max(1.5, sqrt(2 ln N)) with N = setups scored.
- Fit/check: first half vs second half of the setup's traded sessions; a candidate negative in either half is flagged.
- Per-setup tables (every setup scored lands in SCORES.csv), not only totals. Rule changes inside the window listed
  from research/ledger.jsonl.
- Protect L3-gap-slope-fromopen-FD: it is scored but no proposal touches it.

## Amendments (written after the first run, before any proposal; both versions reported)
1. **Active days** changed from "dates with a journaled signal" to **sessions the setup was enabled and not benched**,
   read from the per-session snapshots `setups/<date>.json` on each state branch. Reason: C3-ROT / GY-LIFE define
   active days as eligible sessions; signal days undercount quiet setups. Both columns are in SCORES.csv
   (`active_days`, `signal_days`).
2. **Two extra record views** shown beside the plan's: `nx_` = non-overlap against Primary members' trades in *any*
   account with every C3-BAR2 metric on that record (P3 conflict #5 wording); `all_` = whole live record including any
   Primary stint (GY-LIFE "whole record"; matters for ex-Primary setups on On Deck). Verdicts in RESULTS.md name the
   view they use. Rule sets x views scored: 7 (BAR2 plan / strict / whole; −10R; EXIT100 arena / whole; GY-LIFE).
