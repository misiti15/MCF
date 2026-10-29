# BDI 2026-10-29 (Thursday): first Move Hunt, 2 precursor tests, account blocks

*Educational only — not financial advice. Live numbers are **paper** results from one session. The precursor tests use
the open two-year history (pod1022 `score_batch.py`: costs in, live earnings blackout in, ADV20 >= $95M, 09:50-15:00);
**the locked block 2024-11-01..2025-02-28 was never read.** **16 configurations were tried tonight** (MH1 8, MH2 8), all
reported below; none passes. No config, setup, exit, ledger or docs/live file was changed.*

Reused, not redone: Primary red day and brake (primary1029), close / coverage / Gen burst (nightly1029), signal parity and
blackout size (ops/coverage1029), BAR90 re-screen (bar90_1029).

## Today's win
**The Move Hunt exists and has a first measured capture rate.** research/bdi/moves/moves.csv is the move library (100 rows
for 10-29). The baseline is **26% of the day's 50 biggest tradable moves caught in the right direction, +3.6R captured.**
The run also found where the misses come from: the earnings blackout (44 of the 50 biggest moves overall) and the open
(30 of the 50 biggest tradable moves start before the 09:50 lab window). Two precursors were tested and both were ruled out
on two years, which saves the team from building setups on them.

## 0a. Move Hunt (scripts: research/bdi/moves/)
**Definition (v1, fixed before the list was seen).**
- Universe: liquid names, i.e. live priors ADV >= $95M plus `universe_ok`. That is 1,165 names (643 of them outside the blackout).
- Decision points: every 5-minute bar close from 09:35 to 15:00.
- Move: from the decision close to the highest high (long) or lowest low (short) in the next 90 minutes, capped at 15:55.
  It is measured in daily ATRs.
- Each symbol and side keeps its best decision point, and the top 25 per side are listed.
- There are two sets: `all`, where blackout names are flagged, and `tradable`, where blackout names are removed.
- Caught: a live run-1 trade in any of the 5 accounts, on the right side, entered between the decision point minus 30 min
  and the move's extreme. The R counted is after costs.

**Inputs.** `fetch5.py`: SIP 5-minute bars from 09-22 to 10-29 for 1,535 symbols. `frames_today.py`: the history2y
features plus the lab context. `moves.py` writes the catalogue and the capture rate.

**Capture rate, 10-29**

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | **1 / 50 (2%)** | +2.68 (IOVA short, GY / T2 CWT09) | 9, −8.65R | blackout 44 |
| tradable (blackout removed) | **13 / 50 (26%)**: long 3/25, short 10/25 | **+3.59** | 24, **−16.13R** | traded outside the move 17, skipped 7 (spread rules), no setup 7, wrong side only 6 |

- **The blackout holds the day's biggest moves.**
  - 44 of the top 50 overall are blackout names: GKOS +3.0 ATR, TXT, HII (long +2.4 and short −4.5), INSM, VMC, CRH, CP, XPO and others.
  - 41 of those 44 were on their event day (they reported before the open or after the 10-28 close).
  - This is an owner rule and nothing is changed here. It does mean the remaining edge has to come from names that are not reporting.
- **The open is the second hole.**
  - 30 of the 50 tradable moves had their best decision point at 09:35-09:45, before the 09:50 window most lab setups use.
  - Live caught 5 of those 30, against 8 of the 20 later moves.
- **Wrong-side trades cost more than the catches earned.** In the tradable set they lost −16.1R, against +3.6R captured.
  PURR was the largest: 5 longs, −6.0R.

**Precursors (one day of decision rows, hindsight labels, `precursors.py`).** The base rate of a move of 0.5 ATR or more
within 90 minutes was 2.0% for longs and 1.3% for shorts (40,413 non-blackout rows from 09:50 on).
1. **In play (vol_exp = 5-min ATR / daily ATR).** The top quintile had 3.6× the base rate on both sides, and the bottom
   three quintiles had about 0.2×. It was the strongest single feature. RSI14 >= 72 (q5) showed 2.5× for longs only.
2. **Earnings sympathy.** About 17 of the 50 tradable movers were peers of event-day reporters:
   - TENB (reported 10-28) → CRWD, S, ZS, OKTA, QLYS, PANW, NTSK, RBRK, GTLB, CIBR, BUG and IGV went up 09:35-10:05, then came back down 10:05-10:53.
   - HII, TXT and LHX (reported 10-29) → GE, HEI, WWD, AVAV, XAR and ITA went up 09:45-11:15.
3. **Opening drive.** The move often starts at the 09:35 bar (see above).

## 3. New tested ideas (research/bdi/1029/, backlog rows mh-1029-*)

| config | n | avg R | t (day-clustered) | train / valid | excess vs random | avg R w/o best day |
|---|---|---|---|---|---|---|
| MH1-inplay-q12-hold-long | 78,744 | −0.093 | −2.16 | −0.061 / −0.122 | +0.004 | −0.126 |
| MH1-inplay-q12-hold-short | 80,792 | −0.109 | −2.68 | −0.063 / −0.154 | −0.003 | −0.126 |
| MH1-inplay-q12-holdtr-long | 78,744 | −0.110 | −4.65 | −0.109 / −0.112 | +0.005 | −0.123 |
| MH1-inplay-q12-holdtr-short | 80,792 | −0.115 | −4.71 | −0.112 / −0.118 | −0.003 | −0.123 |
| MH1-inplay-q17-hold-long | 29,951 | −0.087 | −1.24 | −0.047 / −0.122 | +0.002 | −0.148 |
| MH1-inplay-q17-hold-short | 30,551 | −0.116 | −2.20 | −0.040 / −0.190 | +0.015 | −0.141 |
| MH1-inplay-q17-holdtr-long | 29,951 | −0.118 | −3.99 | −0.134 / −0.103 | +0.008 | −0.135 |
| MH1-inplay-q17-holdtr-short | 30,551 | −0.099 | −2.80 | −0.070 / −0.126 | +0.020 | −0.119 |
| MH2-sympathy-at950-hold-long | 3,023 | **−0.049** | −0.68 | −0.063 / −0.036 | **+0.054** | −0.067 |
| MH2-sympathy-at950-hold-short | 2,723 | −0.203 | −3.53 | −0.270 / −0.152 | −0.065 | −0.228 |
| MH2-sympathy-at950-holdtr-long | 3,023 | −0.092 | −1.64 | −0.108 / −0.077 | +0.021 | −0.107 |
| MH2-sympathy-at950-holdtr-short | 2,723 | −0.142 | −2.88 | −0.210 / −0.090 | −0.011 | −0.158 |
| MH2-sympathy-confirm-hold-long | 2,107 | −0.047 | −0.67 | −0.030 / −0.064 | +0.041 | −0.068 |
| MH2-sympathy-confirm-hold-short | 1,865 | −0.181 | −2.98 | −0.193 / −0.172 | −0.040 | −0.202 |
| MH2-sympathy-confirm-holdtr-long | 2,107 | −0.072 | −1.22 | −0.075 / −0.069 | +0.027 | −0.091 |
| MH2-sympathy-confirm-holdtr-short | 1,865 | −0.113 | −2.17 | −0.133 / −0.097 | +0.013 | −0.128 |

**MH1: in-play continuation (vol_exp >= 0.12 or 0.17, trading with the day's trend).** Failed. It is negative in train and
in valid, and its excess over random entries is about 0. vol_exp predicts **how big** the next move is, not **which way** it goes.
On today's data the q12 long version hit 15 of the 25 tradable long movers, but it needed 245 first signals to do it, at −0.15R.

**MH2: earnings sympathy (top-5 return-correlated peers of a reporter that gaps 4% or more, traded in the gap's direction).**
Failed. Longs beat random entries by +0.04 to +0.05R but are still negative after costs. Shorts are negative.
The peer table (`sympathy.py`) has 10,037 peer symbol-days over 297 days. It is kept as **rework**, for two reasons:
- The 10-29 sympathy moves ran 09:35-10:05, and that window cannot be tested in frames that start at 09:50.
- Return correlation is a crude stand-in for an industry peer group.

Bars: BAR90 for N = 16 is 2.12 (full bar 2.35). The best t was −0.67, so no locked look was spent and no Testing entry is proposed.
The filter-creep rule does not apply, because these are new setups, not filters.

## 0. Accounts (P/L after costs; `accounts.py`; peak and close from nightly1029)

| account | P/L | trades | win% / break-even | avg R | peak → close | best / worst | one maximization edit |
|---|---|---|---|---|---|---|---|
| Primary | **−$411** | 16 | 25% / 68% | −0.71 | +$20 (13:21) → −$411 | RW3-FD −1.3R / RW5-FD −3.4R, MF4 −2.9R | Short book on an up day; use the primary1029 shadow brake line, not a new filter |
| Testing 1 | **+$250** | 174 | 56% / 56% | −0.00 | +$475 (13:53) → +$250 | L3-gap-slope-fromopen-FD +14.8R / CWT14-pdl-p05-long −10.3R | Demotion review of CWT14-pdl-p05 (owner mark; −0.117R without its best day over 675 trades) |
| Testing 2 | **+$246** | 204 | 67% / 64% | +0.03 | +$285 (15:26) → +$246 | exhaustion_short-FD +7.9R / CWT14-pdl-p05-lowvol −4.7R | Same CWT14 review (−0.142R without its best day) |
| Graveyard | **−$301** | 401 | 61% / 64% | −0.05 | +$124 (10:53) → −$301 | CWT14-orl-p05-lowvol +8.5R / CWT09-gapdn-bounce-lowerhalf −4.7R, CWT12-coil-k4 −6.9R | None needed; the Graveyard keeps collecting data |
| Gen | **−$3,928** | 217 | 21% / 60% | −0.63 | +$278 (11:34) → −$3,928 | (none positive) / GEN-261020-07 −44.4R (46 lots), GEN-261027-10 −15.3R | Burst risk sharing (backlog nightly-1029-burst20-one-bet): a sizing fix, not a filter |

Compared with 10-28, Primary went from green to red and Gen had its worst day. Testing 1 and 2 were green on their short books.

## Next
- Run the Move Hunt every day and track the capture rate. Two numbers matter: the tradable-set rate (26% today) and wrong-side R (−16.1R today).
- Count the opening-drive share on more days before building the 09:35 frame (mh-1029-open-drive-window).
- MH2 rework once that frame exists: peers by industry, entry at 09:35.

Reproduce: `python research/bdi/moves/fetch5.py <scratch> 2026-10-29`, then `frames_today.py`, `moves.py` and
`precursors.py <scratch> 2026-10-29 0.5`. Those need `<scratch>/cov` from research/ops/coverage1029/fetch.py and the 5
journal.db files from the data branches. For the 2-year tests: `python research/bdi/1029/sympathy.py`, then
`python research/bdi/pod1022/score_batch.py research/bdi/1029/modules/*.py --out ... --ref-cache ''`.
Overlap with the live setups was not run: the `--ref-config` pass takes about 9 minutes per month, and no candidate passed.

Educational only — not financial advice.
