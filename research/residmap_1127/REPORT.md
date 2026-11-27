Educational only — not financial advice
# RESID-MAP-1127: market-adjusted cross-section map, 4 checkpoints x 5 features (inspector 1127 idea #5; research only)
Pre-registered: PREREG.md (sha256 bceb8391…19fb8 committed 99591f8e58; addendum A, which takes half days from the NYSE list, committed e5810621ac; both before any score). **Configs: 20** (all reported). Cumulative N ≈ 8,921 (regsteer 8,891 + cfprimary/stopx/taileff) + 20 ≈ **8,941**, so the lineage bar is t ≈ 4.3 (pass bar t ≥ 2.45 per ideas.json). Locked block never read: row filter at read time plus asserts in rm_build/rm_score. Data: 1-min caches, 947 sessions, ex-ETF; FIT 170 / CHECK 276 / T2 438 days; ~59 names per decile (T2 ~469-symbol universe, survivorship as of 2026-10).
**Verdict: FAIL, 0 of 20 cells pass.** Net of LR8 (7.0-9.0 bp per long+short pair, market in/out, $10k per name), no cell is > 0 on all 3 splits. The best pooled CHECK+T2 t is +0.13 (bar 2.45); 12 of 20 cells sit below t −1.4. Under LIVE-L stress (spread part) every cell is ≤ −3.4 bp on CHECK and T2.
| Cell (s = side, fixed on FIT) | gross bp FIT / CHECK / T2 | net LR8 bp FIT / CHECK / T2 | OOS t |
|---|---|---|---|
| 0945 F1 RGAP (L top) | +0.6 / +6.3 / −3.7 | −8.1 / −1.2 / −12.5 | −1.46 |
| 0945 F2 RINTRA (L top) | +4.0 / +11.9 / −2.2 | −4.7 / +4.4 / −11.5 | −1.21 |
| 0945 F3 RLAST5 (L bot) | +1.4 / +6.1 / +10.3 | −7.1 / −1.3 / +0.9 | +0.01 |
| 0945 F4 RZ (L top) | +2.4 / +4.9 / −1.4 | −5.3 / −2.1 / −8.4 | −1.63 |
| 0945 F5 RPREV (L bot) | +20.6 / +0.5 / +15.1 | +11.7 / −7.2 / +5.6 | +0.13 |
| 1030 F1 / F2 / F3 / F4 / F5 | +1.0/+5.8/−2.5 · +6.5/−1.1/+4.9 · +13.9/+0.8/+1.7 · +4.2/−2.4/+5.2 · +19.3/−6.0/+11.9 | −7.7/−1.7/−11.2 · −2.2/−8.6/−4.5 · +5.1/−6.7/−8.0 · −3.3/−9.4/−1.8 · +10.4/−13.7/+2.5 | −1.67 · −1.71 · −1.90 · −1.66 · −0.94 |
| 1200 F1 / F2 / F3 / F4 / F5 | +4.9/+2.4/−2.0 · +5.7/−2.4/+3.4 · +4.7/+7.2/+3.6 · +5.7/−5.0/−0.8 · +10.1/+1.9/+5.8 | −3.9/−5.2/−10.8 · −3.0/−10.0/−6.1 · −4.3/−0.5/−6.1 · −1.7/−11.9/−7.7 · +1.2/−5.8/−3.7 | −2.70 · −2.89 · −1.54 · −4.47 · −1.44 |
| 1400 F1 / F2 / F3 / F4 / F5 | +2.0/−0.7/−1.1 · +8.3/−7.7/+1.9 · +1.3/+3.8/−0.7 · +6.5/−8.9/−0.7 · +2.2/+6.6/+1.9 | −6.8/−8.3/−9.9 · −0.6/−15.4/−7.7 · −7.8/−3.9/−10.4 · −0.9/−15.9/−7.7 · −6.8/−1.2/−7.6 | −4.47 · −5.22 · −4.50 · −6.43 · −2.41 |
- Other bars, best cells. 0945 F5: avg w/o best day CHECK −9.9 / T2 +4.7 bp; best-day share n/a on CHECK (total < 0), 17% on T2; SPY-up/down CHECK +12.0 / −27.8. 0945 F2 is the only cell positive on CHECK (+4.4; w/o best +2.8; best-day share 35%), but it is −11.5 on T2. Every other cell is negative on CHECK and T2 with no positive total, so best-day share does not apply.
- Goal metrics, best cell (0945 F5, per session in bp of the pair): CHECK red days 10.6/21, worst-5 −2,593, 20-session floor −1,741; T2 10.0/21, −1,625, −1,314.
- Beta leak: with beta = 1, the 09:45-10:30 gap and move cells carry market exposure (0945 F1 CHECK +28 on SPY-down days vs −29 on SPY-up days). The spread is partly a beta bet, not a stock-specific one.
## What can be salvaged (optimistic read, no claim)
- Stock-specific signal does exist gross, but it is smaller than one round trip. 12 of 20 cells are gross > 0 on CHECK and 11 on T2. Two cells are gross > 0 on all 3 splits with monotone deciles: 0945 F3 (last-5-min reversal, +1.4/+6.1/+10.3, mono +0.85/+0.73) and 1200 F3 (+4.7/+7.2/+3.6). 0945 F5 (prior-day residual reversal) is +15 to +21 bp on FIT/T2 but ≈ 0 on CHECK (decay?).
- Read: as standalone decile books these die on costs (≈ 8.5 bp per pair vs 0-10 bp gross). The only use left is as a free tilt or tiebreak inside trades already taken (no extra round trip). That would be a new backlog idea with its own PREREG and N, not a pass here. No DECISION draft.
## Caveats and rule-change context
- Historical bars, one fixed cost model (LR8 as in config today; SEC fee from 2026-04-04 in CHECK). No live journal rows used, so the live ledger changes 10-23..11-27 (sizing, latches, LR8 on 11-12, Epoch 1, stop rounding, moves) do not enter these figures. Fills at the bar open/close carry no spread (LR8 sits on paper fills), so LR8 understates costs; the LIVE-L stress is worse in every cell.
- Scripts: rm_build.py (rows, kept out of git), rm_score.py → cells.csv / cells.json. Nothing in config, decisions.json or live changed.
