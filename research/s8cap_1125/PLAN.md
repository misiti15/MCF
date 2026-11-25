Educational only — not financial advice.

# S8-CAP pre-registration (written 2026-11-25 before any configuration below was scored)

Owner 11-24/25: one package = a per-setup cap that lets setups breathe + a lineup-scaled account stop that never halts
the account prematurely but stops a crash/glitch. Research only: no config, ledger, setup or account change; nothing
committed. Prior: hsscale_1125 (SCALED-K4 + SHOCK-V recommended; exploratory S8 = per-setup closed+open cap at -8R, not
pre-registered, t 1.14-2.26), capfit_1125 (no stable per-setup bottom-out level; -2R latch not selective).

## Engine (bench)
hsscale sim2 engine, rebuilt intermediates (build.py unchanged; bench10 lots, LR8 research costs + 1.2 bp borrow, 1-min
exits and 1-min close marks, Primary book: price >= $5, shorts ETB >= 0.9, per-setup open-lot cap 30, <= 3 lots / symbol
/ setup, 77 account slots, burst brake 30 / 10 min per setup). Point in time: entries see minute m-1 state. Periods
T2 2023-01-03..2024-09-13, FIT 2024-10 + 2025-03..09, CHECK >= 2025-10-01; locked block 2024-11-01..2025-02-28 never
read (asserts in build). Lineups P4 (NM-ETF, RW5, RW3, L3-fromopen) and P9 (P4 + L3-lowdist, L3-rsi5hi, RW7, RW6,
GEN-261029-06; hypothetical). Every configuration is a DIRECT minute-by-minute re-simulation (not a path overlay), so a
cap that frees slots / burst room, and the account rules, interact correctly.

Per-setup cap (all variants): at the end of minute m, if setup s's closed + open cost-R for the day (open lots marked at
the minute close less the market-exit cost) <= -L_s: flatten all of s's open lots at that close (cost in) and allow no
new s entries for the rest of the day. Other setups continue.
Account layer (every configuration except NOW): SCALED-K4 as hsscale: X_w = clip(4 sigma, 2.5 N, 8 N) R, sigma = std of
the configuration's OWN simulated daily closed R over the trailing <= 250 sessions (min 120) before the ISO week; at
account closed + open <= -X_w flatten everything, no entries rest of day. No-new-entries halt H_w = max(20, 0.6 X_w) on
closed + open. Sessions before a week with 120 prior sessions = warm-up (X = none, H = 20, sigma-cap fallback 8R), not
scored for any configuration (one shared scored set). SHOCK-V is a no-new-entries alert layer (hsscale); not re-scored here.

## Configurations (8 candidates) + references
| id | -2R closed latch | per-setup cap L_s |
|---|---|---|
| C6L / C6N | on / off | 6R |
| C8L / C8N | on / off | 8R |
| C10L / C10N | on / off | 10R |
| CSL / CSN | on / off | clip(1.5 x sigma_s, 4, 12) R; sigma_s = std of setup s's own daily closed R on its active days (>= 1 lot) in the trailing <= 250 lineup sessions before the ISO week, >= 20 active days, else 8R |
k = 1.5 and the [4, 12] clip were chosen after looking only at FIT-period per-setup sigma of the hsscale P9-LAT base (1.3R NM-ETF .. 11.1R RW7), so the level lands near the fixed grid; disclosed.
References (not eligible): REF = -2R latch + SCALED-K4 + H, no cap (the hsscale package without a setup cap; the
comparison baseline for every candidate); NOW = live today (-2R latch, -20R no-new halt, no account stop, no cap);
K4N = no latch, no cap, SCALED-K4 + H (separates "drop the latch" from "add the cap").
Configurations counted: 8 candidates (+3 references). Bar sqrt(2 ln 8) = 2.04 -> t >= 2.0 as owner-suggested; lineage
with hardstop_1123 / hsscale / capfit / rules_1122 is ~90 configs -> ~3.0, stated descriptively.

## Books (so trading less is not mistaken for skill)
RAW = bench costs as built. NEUTRAL = every lot of setup s repriced by -a_s (a_s = s's avg R per lot in REF RAW over
all scored sessions of that lineup), the drift removed linearly over the lot's holding time (open mark at fraction f of
its holding time shifted by -a_s x f), so each setup's book has zero expectancy and a truncated lot is not credited
with avoided negative drift. P10 = same with shift a_s - 0.10 (every setup earns +0.10R / lot). Each book is fully
re-simulated (cap and account triggers see the repriced marks); thresholds calibrate on that book's own history.

## Metrics (per lineup x config x book; FIT / T2 / CHECK / pooled), vs REF on the same book
dR, dR/yr, worst day, avg of worst 5 days, days <= -6R, day-clustered t of daily dR; cap fires (setup-days, per yr) per
setup; R saved on fired setup-days whose REF final <= -L_s vs R lost on fired setup-days that recovered (REF final > -L_s),
and fired setup-days REF ended positive; account-stop fires/yr; per-setup dR (better / worse days, sums), setups better /
worse and by how much (Remedies rule); lots entered.

## Live replay (journals: capfit/all_trades.parquet = every account 10-06..11-24, LR8 cost-R, deduped)
Minute grid per account-day; lot mark = side x (close - entry) / risk - lot cost (cost = gross R - LR8 R), closes from
cache_hist 1Min + pyramid/G/live_bars; no bar -> marked at entry less cost (share reported). Variants: LIVE-L = the -2R
closed latch applied to every account-day as a what-if (drop entries after the setup's closed R <= -2), = REF_live;
latch-off variants = actual trades + journal what-if rows skipped by "setup daily loss limit" (r = r_multiple less that
setup's median cost gap; only the 21 capfit setups have them) ; cap levels as above (CS: sigma_s from the setup's prior
replayed live sessions, >= 8 else 8R); account layer: X = clip(4 sigma_acct, 2.5 N, 8 N), N = distinct setups the
account traded that day, sigma_acct from the account's prior replayed days (>= 10 else 8 N), H = max(20, 0.6 X).
Real account halts / what-if rows for other reasons are not re-created. Reported: Primary, Primary since the latch went
live 10-29, all accounts pooled; total R, worst account-day, avg worst 5, cap fires, per-setup dR, and a NEUTRAL live
version (per setup live avg R / lot removed linearly as above).

## Pass bar (fixed now). A candidate PASSES if all hold:
1. NEUTRAL dR vs REF > 0 in each of FIT, T2, CHECK, on both P4 and P9.
2. Day-clustered t of pooled NEUTRAL daily dR vs REF >= 2.0 on both P4 and P9.
3. No setup worse by > 10R (NEUTRAL, pooled, per lineup).
4. RAW worst day not worse than REF's in any period on either lineup.
5. Live replay RAW total not worse than LIVE-L for Primary and for all accounts pooled; live worst account-day not worse.
Pick: among passing candidates, the highest pooled NEUTRAL dR/yr summed over P4 + P9; ties (within 10%) -> latch off
("let setups breathe"), then fixed level over sigma-scaled, then fewer fires. If none passes: say so, name the best
candidate and what failed. RAW and P10 results reported for every finalist; all 8 candidates reported.
Package = chosen cap + latch on/off + SCALED-K4 (+H) + SHOCK-V (alert layer, unchanged from hsscale).
