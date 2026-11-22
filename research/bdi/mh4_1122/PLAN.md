Educational only — not financial advice.

# BDI-MH4 (owner yes 2026-11-22): 2-year screen of two Move Hunt ideas — PRE-REGISTRATION

Written 2026-11-22 **before any row was scored**. Research only: no setup, exit, config or account changes.
Mirrors `research/bdi/mh4_1122/`. Backlog ids: `mh-1121-crypto-complex-follow`, `mh-1121-peer-cluster-laggard`.

## Engine (bench10 "normal way" conventions, research/ultimate_1119/top10/bench10.py)
- **Data.** T1 = `data/cache_hist/1Min` (1,226 symbols), loaded with a pyarrow filter that excludes 2024-11-01..2025-02-28
  and an assert on every load (the locked block is never read). T2 = `data/cache_fresh/1Min` (469 symbols,
  2023-01-03..2024-09-13).
- **Splits.** FIT = 2024-10 + 2025-03..2025-09. CHECK = 2025-10-01..latest (2026-11-04), **scored once, only for the
  FIT picks** (below). T2 is scored for the FIT picks only.
- **Decision row.** The 09:50 bar close (close of the 09:49 minute, the bar-end label as the lab frames). Daily values
  from RTH 1-minute bars as `mcf/research/heat.py`: prev close; `atr_d` = 14-session mean daily true range (min 10),
  shifted one session; `adv20` = prior-20-session mean RTH dollar volume (min 5). The series restarts after the locked gap
  (no locked row is read, so early March 2025 lacks atr_d until 10 sessions exist). `move` = (close_0950 − prev
  close) / atr_d (the move from the prior close in daily-ATR units, gap included).
- **Entry / exits.** Entry at the decision close. Exits on 1-minute bars from 09:50: stop first (gap-through at the worse
  of open/stop), target only when traded through by $0.01, flat at 15:55. Two exits:
  `t1s1` = target / stop ±0.25 × atr_d; `hold` = stop 0.25 × atr_d, no target, flat 15:55.
- **Costs.** LR8 research basis exactly as bench10 `add_r`: entry (1c + 1 bp) × tod multiplier (1.4 at 09:50), exit 1c + 1 bp
  except target fills, +2c on stops, ×3 extended tier (|gap| ≥ 20% or price < $5), shorts + 1.2 bp borrow.
- **Book.** Testing-arena rules (destination account): price ≥ $5, shorts ETB ≥ 90% of snapshots (etb_rate.parquet,
  the Workbench file), cost filter 0.15R, cap 100 open lots, ≤ 3 lots / symbol (one entry per symbol-day here anyway).
  `adv20 ≥ $20M` on every traded name. No earnings blackout (bench10 does not apply one either; noted).

## Idea 1 — crypto complex follows bitcoin (16 configs)
- **BTC proxy:** IBIT `move` at 09:50 (spot BTC ETF; trades the overnight BTC move at the open).
- **Members (pre-registered, every crypto-linked symbol in the T1 cache):** spot BTC/ETH ETFs FBTC, GBTC, BITO, ETHA;
  leveraged BITX, MSTU, MSTX, CONL, ETHU; equities MSTR, COIN, HOOD, GLXY, CRCL, BMNR, FIGR; miners / ex-miners MARA, CLSK,
  RIOT, HUT, CIFR, WULF, IREN, BTDR, CORZ, APLD. A member is tradable only on days it has bars and atr_d (point in time).
  Caveat: CRCL / BMNR / FIGR / GLXY are labelled crypto with today's knowledge (BMNR became an ETH-treasury name mid-2025).
- **Inverse crypto ETPs (MSTZ, BTCZ, SBIT, BITI) are NOT in the bar cache**, so the backlog's "long-only via inverse ETPs
  on down days" cannot be tested; down days are tested as shorts (ETB rule removes MSTU / MSTX / CONL / ETHU shorts).
- **Grid:** threshold k ∈ {0.50, 0.75} (|IBIT move| ≥ k, side = its sign) × set ∈ {all members, laggards = members whose
  own move in the BTC direction is < 0.5 × |IBIT move|} × exit ∈ {t1s1, hold} × side ∈ {long (BTC up), short (BTC down)}
  = **16**. Bar (N = 16): max(1.5, √(2 ln 16)) = **2.355**; BAR90 = 2.12.
- **T2:** no BTC proxy exists in `cache_fresh` (IBIT is from 2024-01 and is not in that cache; no GBTC / BITO) ⇒ T2 is
  **not scorable** for this idea ⇒ Tier A is not reachable; at most Tier B. Stated up front.
- **Day-type control (backlog falsifier):** the same members, same side and exit, at 09:50 on **non-trigger** days.

## Idea 2 — peer-group laggards (16 configs)
- **Universe:** stocks only (ETF / ETN / fund / leveraged names removed by a name filter on data/universe.csv), with
  intraday bars in the test's cache.
- **Groups, point in time:** per calendar month, from the trailing 120 sessions **before** the month start (≥ 50 with data,
  ≥ 90% coverage): daily returns minus β × SPY (β from the same window); a name's peers = up to 10 names with residual
  correlation ≥ c. T1 history before 2024-09-16 comes from `data/cache_fresh/daily.parquet` (2022-10..2024-09-13);
  the return across the locked gap is dropped. A name needs ≥ 3 peers to be eligible.
- **Trigger at 09:50 (name X, side s):** ≥ 3 of X's peers have s × move ≥ m, and at most 1 peer has s × move ≥ m the other
  way. **Laggard:** −0.5 < s × move(X) < 0.25. Both sides triggered on one name-day ⇒ skipped.
- **Grid:** c ∈ {0.35, 0.50} × m ∈ {0.50, 0.75} × exit ∈ {t1s1, hold} × side ∈ {long, short} = **16**.
  Lineage N = 16 + 16 (parked mh-1102-open-group-move) = 32 ⇒ bar max(1.5, √(2 ln 32)) = **2.633**; BAR90 = 2.37.
- **Overlap with mh-1102 (required):** share of the picks' symbol-days that also carry an MH4-style lag signal computed
  at the 09:50 row (peers K = 10, corr ≥ 0.30; P = median peer z from the open minus the cross-sectional median ≥ 0.40,
  agree ≥ 0.7, own z < P/2). Approximation of MH4 (its frame was 09:40-09:50); reported, not a gate.
- **Day-type control:** the same names, same side and exit, at 09:50 on days they are **not** signalled.

## FIT picks, then CHECK once
For each idea and side: the FIT config with the highest day-clustered t among configs with ≥ 20 FIT trades (≤ 4 picks
total). Only those are scored on CHECK and T2, once. Every config's FIT row is reported.

## Reported for every pick (and FIT rows for all)
trades, trades/session, win, avg R (net and gross), avg R w/o best day, w/o top-2 days, best-day share, total R / session,
worst day, day-clustered t vs bar, SPY up / flat / down split (±0.3% open→close), walk-forward months positive, April-2025
share of total R and avg R ex-April-2025, random-entry null, day-type control.
- **Random-entry null:** 1,000 draws; for each session the config trades n names, draw n random symbol-day 09:50 entries
  from the eligible pool (same filters: adv20, price, ETB for shorts, cost filter; same side and exit). Report the
  percentile of the config's avg R. "Beats random" = ≥ 95th percentile.

## Decision rule (binding, from research/ultimate_1119/top10/PLAN.md)
- **Tier A (meets top-10 standard):** T1 combined avg R ≥ −0.0383 and T1 check ≥ −0.0464; avg R w/o best day ≥ −0.0674
  (comb) / −0.0781 (check); total R / session ≥ −0.4862 / −0.5218; T2 avg R ≥ −0.1048; ≥ 20 trades on check and on T2.
- **REALLY BAD:** T1 combined ≤ −0.05 with day-clustered t ≤ −2.0, or < −0.03 on all of FIT, CHECK and T2 (T2 counts only
  with ≥ 20 trades; else FIT and CHECK both < −0.03).
- **Tier B:** debatable (not A, not really bad) **and** derived from a promising parent. Neither idea is derived from a
  top-10 / promising live setup (both are Move Hunt originals), so Tier B does not apply unless the report names a parent
  honestly. ⇒ A DECISION line is written only for a Tier-A pick. Otherwise FYI only, backlog status updated.
- Reminder carried into the report: the top-10 medians are negative, so "meets the standard" ≠ "profitable in backtest".
