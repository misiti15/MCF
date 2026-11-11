# REGSW-2 — setup on/off switches on a WINNING base (Builder, frozen 2026-11-11 ~08:45 ET, before any score)

*Educational only — not financial advice.* Owner task (owner-20261111-0821-1, item 2): Phase 1 (main session, 99 configs,
0 of 74 pass) ran on a losing lab base, so fits learned "trade less". Research only; nothing switches anything live.
SKEPTIC_CHECKLIST walked: items 2, 4, 8, 9, 13, 15-18, 21, 24-26 are built in below; 22 n/a (no live-price join; live
check uses journal R only).

## Base (selected BEFORE any switch is scored; TRAIN + live only, VALID / FWD outcomes not read)
Setups with a 2-year lab list (bt_lab1104 / bt_hold) AND (a) lab **TRAIN** (<= 2025-09-30) **gross** avg R > 0 (bt_all
cost inverted, as compassbf/retag.py) AND (b) live paper net avg R > 0 with >= 20 trades in Scout's
research/whatworks/whatworks_all.csv (journals to 11-10). Earnings-blackout days (+-4 sessions, live rule) removed from
the base (checklist 18). The base list is printed and frozen by the script's first stage (`--base-only`) and committed
before stage 2 runs.

## Switches (4 configs; lineage continues from Phase 1's 99 -> N 103, full bar 3.04, BAR90 2.74)
Readings from the backfilled live compass (research/compassbf/compass_2y, mark strictly BEFORE the entry bar close,
checklist 2), or the day's open (known at 09:30):
- **S1 GAP-U** (Phase 1's survivor, as described on the board): SPY open vs prior close > +0.25% -> shorts off all day;
  < -0.25% -> longs off all day.
- **S2 CHK:** latest 30-min checkpoint (from 10:30) is UP -> shorts off, DOWN -> longs off.
- **S3 W60:** W60 compass confirmed opposite to the trade's side -> off.
- **S4 SPYFO:** SPY >= 0.30% from its open against the trade's side at the last mark -> off.

## Score (per switch)
- delta = -(sum of R of switched-off trades) per day; **control = a random off-set of the same size within each
  setup-day** (200 draws, checklist 9 / 13); excess = delta - mean random delta; day-clustered t.
- GROSS first (excess on gross R), then net; ATR-unit excess beside R (checklist 15); TRAIN / VALID / FWD (lab lists
  10-08..11-09); SPY up / down / quiet split of the excess (checklist 16); w/o best day.
- Per setup better / worse and worst setup delta (Phase 1's harm test; Remedies rule); retention (trades kept, top-decile
  winners kept) per setup; distinct switched-off symbol-days (checklist 25).
- Live check (separate, labelled live paper): the same switch applied to the base setups' live trades 10-06..11-10
  (journals, fixed window, checklist 21), excess vs random.
- **Pass:** net excess t >= 2.74 AND gross excess > 0, TRAIN and VALID excess > 0, w/o best day > 0, no more setups worse
  than better and none worse by > 0.03R/trade, live excess > 0. Report all 4, failures first, PBO beside them.
