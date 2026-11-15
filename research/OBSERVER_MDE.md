# Observer — minimum detectable effects for closed / 'no effect' results (2026-11-15; Lead's MDE standard lead-20261115-0100-1)

SE = estimate / t from each study's own output; MDE80 = 2.8 x SE (80% power, 5% two-sided). Read each line as 'nothing above MDE80; smaller unknown'.

| study | claim | estimate | t | MDE80 | unit |
|---|---|---|---|---|---|
| OBS-COMPASS-RW (COMPCAL) | rest-of-day hold vs empirical benchmark | +0.4 | +0.38 | 2.95 | pt accuracy |
| OBS-MIN10 | untriggered trades after minute 10, k 0.10 | -0.0013 | -0.14 | 0.026 | ATR/trade |
| OBS-MIN10 | untriggered trades after minute 10, k 0.25 | -0.011 | -1.75 | 0.0176 | ATR/trade |
| OBS-MORNINGMAP | L1 aligned minus counter, VALID | +0.051 | +1.11 | 0.129 | R/trade |
| OBS-MORNINGMAP | L2 aligned minus no reading, VALID | +0.036 | +1.27 | 0.0794 | R/trade |
| OBS-LATEDIP index analog | SPY 15-min dip 14:00-14:55 -> 15:55 | -2.7 | -0.30 | 25.2 | bps |
| OBS-LATEDIP index analog | QQQ | +1.3 | +0.18 | 20.2 | bps |
| OBS-LATEDIP index analog | IWM | -4.1 | -0.63 | 18.2 | bps |
| OBS-FILLCLOCK lag cost | Primary entry drift per minute of lag | +0.0023 | +0.07 | 0.092 | R/min |
| OBS-FILLCLOCK lag cost | On Deck | +0.0201 | +1.94 | 0.029 | R/min |
| OBS-FILLCLOCK lag cost | Graveyard | +0.0128 | +1.20 | 0.0299 | R/min |
| OBS-FILLCLOCK lag cost | Gen | +0.006 | +0.99 | 0.017 | R/min |

Also: OBS-UPDAY-NULL (research/obs-upday-null/mde_out.txt): all days 7-12bps, buckets 10-40bps (x3 for 3x ETFs).
OBS-VERDICTS (no demote rule beats the 69% base rate): 35-42 calls, so a rule would need ~+20 pts accuracy to show (binomial SE ~7 pts);
'no rule beats base' means 'nothing above ~20 pts'.
Readings: index-level nulls (COMPCAL, LATEDIP, UPDAY) exclude only large effects (3 pts accuracy; 18-25bps). Trade-level ones
(MIN10 ~0.02-0.03 ATR, MORNINGMAP ~0.08-0.13R) sit near or above round-trip cost. FILLCLOCK: lag cost per minute is below ~0.02-0.09R/min,
except Testing A (slope -0.010R/min, t -3.5, i.e. later fills were slightly BETTER there).
Educational only — not financial advice.
