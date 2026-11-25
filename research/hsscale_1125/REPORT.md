Educational only — not financial advice

# hsscale_1125: a scaled account stop + glitch failsafe for Primary (research only)

Owner 11-24: "HS wait for the scaling version… don't stop the account prematurely, but don't let it crash from a bug or glitch; lean into the setup caps." Pre-registered (PLAN.md, sha256 4ae6b058…82c2). Engine: hardstop_1123 generalised to N setups (bench10 lots, LR8 + borrow, 1-min marks, Primary book rules; reproduction −1,710R vs −1,701R). Lineups P4 = today's Primary (NM-ETF, RW5, RW3, L3-fromopen) and hypothetical P9 (+ L3-lowdist, L3-rsi5hi, RW7, RW6, GEN-261029-06); latch variants LAT (−2R on all) and GDX (gap-down family exempt). Walk-forward weekly, ~2.9 scored years; locked block never read. 15 configurations; nothing claims edge (bar 2.33; lineage ~2.9).

## Failures first
- The bench book loses (~−0.08R/lot except NM-ETF), so every rule is also scored at zero expectancy and on a +0.10R book.
- No account stop catches a one-minute shock (2026-07-29 14:00: −10R → −40.7R in a minute; flattening locks in −40.6R vs a −34.8R close).
- The scaled rules sit on their 8R-per-setup ceiling most weeks.
- Fixed −12R (A12) fires 46 days/yr for 4 setups and 132/yr for 9 setups, turning 49 positive 9-setup days negative — premature, as the owner suspected.

## Layer 2 — SCALED-K4 (recommended)
X = clip(4σ, 2.5R×N, 8R×N), σ = std of the lineup's simulated daily closed R (trailing 250 sessions, min 120), recomputed every Friday and at any lineup change. At closed + open R ≤ −X: flatten all MCF lots, no new entries for the day. No-new-entries halt H = max(20, 0.6X).
| Lineup | Rule | Fires/yr | dR | Positive days turned negative | Worst day (none → rule) |
|---|---|---|---|---|---|
| P4-LAT | A12 (−12R) | 46.4 | +330 | 3 | −48.1 → −40.6 |
| P4-LAT | K4 (≈ −32R) | 7.5 | +13 | 0 | −48.1 → −40.6 |
| P9-LAT | A12 | 132.2 | +1,233 | 49 | −73.4 → −25.4 |
| P9-LAT | K4 (≈ −72R) | 1.3 | +8 | 0 | −73.4 → −72.2 |
Insurance, not edge: passes all four pre-registered criteria in both lineups and latch variants; no setup hurt by more than ~10R. Risk scales ~N^0.8 (daily σ 10.4R for 4 setups, 20.0R for 9): the tails move together.

## Layer 1 — SHOCK-V glitch failsafe (recommended)
V1: closed + open R falls ≥ max(8, 0.5X) within 2 minutes; V2: ≥ max(12, 0.75X) within 10 minutes; confirmed on 2 consecutive polls. Action: no new entries for the session + push alert (not a flatten — flattening after a shock locks in the low). Live: 0 fires on Primary's 13 snapshot days; across 118 account-days it caught the Gen 11-17 runaway (143 lots in 5 min, −127R) and Live Lab 11-20 (−116R) with 2 false fires. It does not separate the 11-20 NM-ETF burst from good bursts (that stays with the ETF-STOP AV50 change).
Missing bug guards (owner decisions): MISMATCH-$ (broker-vs-journal excess > ~2 slot notionals for 5 polls → account no-new-entries + alert; auto-flatten needs the owner's yes), LR10 order-size guard at submit, LR6 collar/stuck-order cancel, re-stop/flatten of lots with no working stop leg.

## Setup caps
- Exempting the gap-down family from the −2R latch makes the bench book worse and the worst day deeper (P4 −48 → −52R; P9 −73 → −98R) — conflicts with rules_1122 live evidence; unresolved; re-test only paired with SCALED-K4 or S8.
- S8 (exploratory, after the plan): per-setup closed + open cap at −8R → flatten that setup and stop it for the day. P4 +133R (worst day −48 → −41, positive in all periods), P9 +221R, 7 of 8 setups improve; t 1.14–2.26 (below the bar). Backlog: pre-registered test + live replay.

## Process
Any adoption is a Primary change: Friday epoch window, skeptic review, owner's yes, ledger entry + check. Caveats: P9 hypothetical; buying power and twin blocks not modelled; live snapshot window only 13 days. Scripts/data: scratchpad hsscale/ (not committed).
