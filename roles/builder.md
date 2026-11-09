# builder notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09, run 1)
- Data: the container had NO 2-year cache (data/cache_hist), lab frames (research/history2y/data), open frame
  (research/bdi/timeofday/data/open), o5_hist or bt_lab1104 lists. All git-ignored. Rebuild recipe: MCF
  research/bdi/1104/DATA.md (download wrapper dl_wrapper.py, build_frames.py --context, build_open.py, build_o5.py,
  bt_all.py). Do it after 16:00 ET only: download.py's STOP_UTC guard exists to keep the live 08:35 job's Alpaca
  rate budget; keys are in the env (never print them). Needs `pip install -e ".[dev,alpaca]"` + `pip install pyarrow` (installed 11-09; the combined command timed out once in the background, run them separately).
- Plans frozen (no scores yet): research/gate2/PLAN.md (Lead P1, 11 configs, N 123 with GATE1's looks, BAR90 2.79),
  research/c3fr/PLAN.md + c3fr.py (6 configs, N 21, BAR90 2.22; simulator unit-checked on synthetic paths),
  Observer's 09:50 opening-drive measurement (pre-declared on the board, builder-20261109-0820-3).

- Run 2 (08:40 ET): gate2.py written + synthetic-checked (trigger, E1, E2 trail, gap stop). Scout pre-writes SC2
  (research/sc2/); tonight's order: rebuild -> GATE2 -> Observer 09:50 -> SC2 -> C3FR.

## Learned
- The 2-year lab book is negative (~-0.06R VALID), so gates/blocks get raw t for free: always score excess over a
  control (Skeptic), report kept avg R.
- Lag/peer signals pick names (COMBO1 C3 +0.096R vs random) but opening friction (0.16-0.23R at R 0.25 ATR) kills them;
  friction in R scales with 1/R — the targeted remedy is wider R, not a new filter.
- Tags so far mostly restate SPY direction (L1/L2/L3/L6): always split by SPY up/down/quiet and compare to a
  same-side control.

## Failed
- (none scored yet)

## Next
1. After 16:00 ET: rebuild cache + frames + open frame + o5 (+ bt_all lists for GATE2 sizing).
2. Run gate2.py per PLAN (report all 11, failures first), then Observer measurement, then c3fr.py.
