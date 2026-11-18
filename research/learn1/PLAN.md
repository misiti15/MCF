Educational only — not financial advice.

# LEARN1: retraining audit, daily skill, stop/continue rule (pre-registered 2026-11-18, after the close)

Owner "LEARN1 yes" (2026-11-17). Research / display only: Hunch and the Market Compass place no orders, read no trading
config and feed nothing to trading. Nothing in this plan changes a setup, an exit, sizing or an account. This file was
committed before any session of the evaluation window (2026-11-19 on) was scored, and is not amended after.

## 1. Retraining audit (state on 2026-11-18)

**Hunch (live shadow, `mcf/hunch/live.py`, `.github/workflows/hunch.yml`).** It does not refit nightly; it learns
*online*. Each bar's guess is frozen first, then scored when the next 3-min bar closes, then the pooled logistic model
and the 200 per-ticker logistic models take one SGD step on it. The model state is carried across days
(`state/model.npz` on `mcf-data-hunch`, seeded by the 2-year replay), so it is trained on all data collected so far,
walk-forward, with no look-ahead (`tests/test_hunch.py`: guesses never change with later data; features at bar b use
bars <= b). 11,117,933 scored rows by 11-18 (2-year replay + 10 live sessions).
- **Gap found:** 2026-11-11 was never finalised (no `model_2026-11-11.npz`; 11-12 started from 11-10's model), so its
  22,390 scored guesses were never learned (0.2% of rows). **Fix:** `live.catch_up` learns any session between the
  model's last date and today that is in the fetched 7-day window, before today's first guess.
- The boosted trees / top-k learners exist only in the replay; the live shadow runs the two logistic learners.
- **Inputs before (21 + time-of-day buckets + per-ticker intercept):** ret1, ret3, ret5, vwap_atr, rsi14, rsi5, vol20,
  pressure, gap, fo, orh, orl, pdh, pdl, atr_pct, tod, spy_ret1, spy_fo, qqq_ret1, qqq_fo, sector_ret1.
- **Added (5, cheap, point in time; `mcf/hunch/data.py` EXTRA):** breadth_open (share of the 200 names above their
  open at the same bar close), breadth_ret1 (share whose same bar closed up), sector_fo (mapped sector ETF % from open),
  vol_tod (bar volume / same bar of the previous 5 sessions), roll_spread (Roll spread proxy in bps; no historical
  quotes). Time of day was already in (tod + 5 buckets). **26 inputs after.** They join the live model on 2026-11-19
  with zero weight (`live.extend_model`: the first guesses are identical) and are learned online from then on. The
  2-year replay and its seed keep the frozen 21 (`FEATURES`); no replay is re-run.

**Market Compass.** The live readings (W60 15-min votes, 30-min GATE1 compass, 0.30% checkpoint, GATE1 state) are
fixed rules: nothing retrains. The "In plain English" hit rates (`mcf/report/compass_plain.json`) are a static table
built once from TRAIN+VALID. Two parts do learn: the conditional cell table (all sessions since 2024-09, locked block
excluded) and COMPCAL (the last 60 sessions' moves to the close, by design), both refreshed by
`mcf/report/compass_cond.py` — until now only from the nightly Claude routine.
- **Gaps found:** (a) 2026-11-13 was never appended to `cond_obs.csv` (465 sessions to 11-17, 11-13 missing).
  (b) Since 11-16 the live card recorded only the 09:45 mark: GitHub fired the in-session crons only after the close
  and the 16:15 cut-off turned those runs into no-ops. **Fixes:** `compass_cond.catch_up` appends missed sessions
  (oldest first); `compass.yml` now runs to 23:59 ET (late runs backfill the day's marks, tagged backfilled), adds a
  17:30/18:30 ET run, and appends the nightly table itself from 16:00 ET (idempotent with the routine).
- **Inputs before (9):** SPY / QQQ / IWM % from open, SPY vs VWAP, breadth (200 names above open), persistence (same
  side over the last hour), time of day, SPY vs previous close, gap. **Added, recorded only (4, not votes):**
  breadth_vwap, breadth_15 (share up over the last 15 min), breadth_dvol (dollar-volume-weighted breadth), sector_up
  (share of the 11 SPDR sector ETFs above their open). **13 after.** COMPASS-LEARN found extra inputs hurt as votes,
  so they are only logged for later pre-registered studies. No spread input: there is no quote history.

## 2. Daily skill metric (`mcf/report/skill.py` -> `docs/live/skill.json`, dashboard card "Model skill (LEARN1)")

Per model and session: hit rate minus the base-rate forecast's hit rate; Brier score vs the base-rate forecast's
Brier score (Brier skill score bss = 1 - B / B_base); running mean with a 95% t interval, sessions as the unit.
Models: hunch_pooled, hunch_own (M1, base = the live majority answer; base probability = earlier live sessions' yes
share), compass_w60 (the dashboard's plain-English chance at every mark), compass_cal (COMPCAL, walk-forward over
every session; sessions before 11-17 are a deterministic replay, tagged). For the compass the base that counts is
"stay" (the share of earlier sessions that closed on the side SPY was on at that mark); the plain base rate is reported
too but is beaten trivially once SPY has moved. Run nightly:
`python -m mcf.report.skill --hunch <mcf-data-hunch checkout> --compass <mcf-data-compass checkout> --fetch`.

Baseline on 2026-11-18 (10 live Hunch sessions, 9 live compass sessions; before the window, FYI only):
| model | 11-18 skill (hit − base) | 11-18 bss | live sessions | live bss mean (95% CI) |
|---|---|---|---|---|
| Hunch pooled | −0.2 pts | −0.008 | 10 | −0.015 (−0.030 to −0.000), worse than base |
| Hunch per ticker | +0.4 pts | −0.004 | 10 | −0.004 (−0.009 to +0.000) |
| Compass live reading (vs stay) | +4.0 pts | +0.123 | 9 | +0.034 (−0.245 to +0.313) |
| COMPCAL (vs stay) | +2.8 pts | +0.484 | 2 live (404 replay: +0.173, 0.127 to 0.219) | +0.544 (−0.224 to +1.313) |
Compass 11-16/17/18 marks were completed in memory from read-only bars for this table (the data branch still holds
only 09:45 for those days until a backfill run).

## 3. Stop / continue rule (pre-registered)

- **Window:** the first 20 sessions from 2026-11-19 with scored data for that model (expected decision after the close
  on 2026-12-17; later if sessions are missing). Each model is decided on its own.
- **Primary metric:** daily Brier skill score — vs the base rate for Hunch (pooled and per ticker), vs "stay" for the
  compass models. Secondary (reported, not deciding): hit rate minus base.
- **Skill:** the 95% t interval of the 20 daily values is entirely above 0. **No skill:** the interval includes 0
  (or is below 0).
- **No skill -> cut to a weekly light check:** the model keeps running (it costs nothing to trading) but its review
  becomes one line in the Friday brief; no further research effort on it until a new owner-approved idea.
- **Skill -> propose ONE pre-registered filter test** to the owner (a decision item, not shipped): e.g. Hunch's pooled
  probability as a skip filter on setups that trade the same names / bars, or the compass "stay" probability as a
  late-day filter; tested on locked replay data with costs in, scored once (RESEARCH_RULES). Four models are tested,
  so about one false "skill" in five windows is expected by chance; that is why "skill" only earns a test, never a
  live change.
- Configurations tried in this plan: 4 models x 1 primary metric = 4 (plus 4 secondary readings).
- **Rule-change context:** 11-05 Hunch live start; 11-09 compass live start; 11-11 Hunch session not learned; 11-17
  COMPCAL display line; 11-19 the LEARN1 inputs and fixes above (ledger `2026-11-19-learn1-skill-inputs`). Any later
  change to Hunch or the compass inside the window is logged in the ledger and noted beside the result.
