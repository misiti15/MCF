## QA area: primary-numbers (week 2026-11-16..11-20)

I re-derived every number from scratch. Sources:
- R: `live_trades()` (written to `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/primary-numbers/live.csv`), checked against the raw `origin/mcf-data:journal.db` re-costed with `cost_r_lr8`. Both give the same result.
- $: `origin/mcf-data:status.json`, using history `alpaca_day_pl` and account `equity` / `last_equity`.
- Broker reconcile files: `reports/pl_reconcile/*.json`.
- The post's own dollar logic: `mcf.report.daily_post.accounts()`.
- Compass: `origin/mcf-data-compass:compass/2026-11-20.csv`.

### Checks

| # | Claim (source) | My number | Result |
|---|---|---|---|
| 1 | Week Primary +4.1R, 193 trades (post.md, image 1) | 193 trades, +4.11R | PASS |
| 2 | Week Primary +$756 | Alpaca day P/L sum: 1474.81 − 466.67 + 296.01 − 762.76 + 214.16 = **$755.55**. Close-to-close in `daily_post.accounts()` = $754.64. Journal fills = $766.61 | PASS (Alpaca basis) |
| 3 | Daily R: Mon +25.3, Tue −2.5, Wed −5.5, Thu −16.2, Fri +3.0 | +25.31 / −2.46 / −5.52 / −16.21 / +3.00 | PASS |
| 4 | Daily $ in image: +1,475 / −467 / +296 / −763 / +214 | status `alpaca_day_pl`: 1474.81 / −466.67 / 296.01 / −762.76 / 214.16 | PASS |
| 5 | Trades 57/22/49/32/33; win rates 82/59/49/25/64% | 57/22/49/32/33; 82.5/59.1/49.0/25.0/63.6% | PASS |
| 6 | 2 of 5 days green (R) | Mon and Fri | PASS |
| 7 | Since 10-23: −66.0R, 7 of 21 days green | −65.97R, 21 sessions, 7 green on R | PASS |
| 8 | Since 10-23: Alpaca +$313, 11-05/06 glitch excluded | Sum of `alpaca_day_pl` with the PL_ADJUSTMENTS applied = **$312.64**. Equity check: 95,662.39 (10-22 close) → 84,334.80, plus 11,456.31 and 183.92 for the glitch = $312.64 | PASS |
| 9 | 11-20 Primary +3.00R / +$214.16, 33 trades, 21 wins | +2.996R; journal $214.16; Alpaca equity − last_equity = 84,334.80 − 84,120.64 = $214.16; 33 trades, 21 wins | PASS |
| 10 | 11-20 shorts 20/20, +15.3R (L3 7 / +6.01, RW3 7 / +5.50, RW5 6 / +3.84) | 20 trades, 20 wins (side −1), +15.34R; per setup exactly as claimed | PASS |
| 11 | ST7 1 trade +0.23R (SEI flatten); ex-NM-ETF +15.6R | +0.226R, flatten; 15.57R | PASS |
| 12 | NM-ETF −12.57R, 12 lots, 0 wins, all stopped, burst 14:10–14:15 bars, 9 within 15 s | 12 stops, −12.57R. Entries 14:11:04–14:11:19 ET (9 lots), then 14:15:50, 14:15:57, 14:16:05 | PASS |
| 13 | Exits: 17 targets, 12 stops, 4 flattened | 17 / 12 / 4 | PASS |
| 14 | Compass gate (DOWN confirmed 11:15) would block 13 Primary trades, −12.35R (12 NM-ETF + 1 ST7) | Compass CSV: 11:15 row is `DOWN-confirmed`, computed 11:21, not backfilled. Primary longs after 11:15: 13 trades (12 NM-ETF + SEI ST7 at 14:31), −12.347R | PASS |
| 15 | Nightly line (inbox:244): 3-day −18.73R, −0.164R/trade, 46% win | 114 trades, −18.74R, −0.164, 46.5% | PASS |
| 16 | Primary records (inbox:145): RW3 25 sess / 176 trades +0.175 (w/o best +0.043, 79%); RW5 26 / 186 +0.109 (+0.004, 97%); L3 15 / 188 +0.200 (+0.049, 82%); NM-ETF 7 / 27 −0.424 (w/o −0.530); ST7 14 / 43 −0.149 (−0.281); last-4 sums | All match exactly | PASS |
| 17 | 11-16..11-19 daily brief R (−2.46, −5.52, −16.21, +25.31) | Match | PASS |
| 18 | Post: gap-down shorts "+73.4R on 530 trades since 10-06; everything else −161R" | Through 11-20: **550 trades +88.8R; everything else −173.3R**. Through 11-19: 530 / +73.5R and −161.0R | FAIL (one day stale) |
| 19 | Inbox:236: NM-ETF "record before 11-19 was 33 tr, +0.21R" | Primary before 11-19: 12 trades, +2.01R (+0.168/trade). 33 trades / +0.21R only reproduces as all accounts **through** 11-19 (30 de-duplicated trades before 11-19 plus Primary's 3 on 11-19) | FAIL (wording) |
| 20 | Daily briefs label "Alpaca $" (11-16 +$1,478.68, 11-18 +$299.32, 11-19 −$760.48, 11-17 −$465.07) | These are journal fill P/L. Alpaca day P/L is 1,474.81 / 296.01 / −762.76 / −466.67 | FAIL (label; $2–4 per day) |

### Findings

1. **Minor: week post, "Where Primary's money comes from", uses data that stops at 11-19.** The post says the three gap-down shorts made "+73.4R on 530 trades since 10-06; everything else that's run in Primary: −161R". Those numbers hold only through 11-19. Through 11-20 the shorts are **+88.8R on 550 trades** and everything else is **−173.3R**. The post's own Friday story (shorts 20/20 +15.3R, NM-ETF −12.6R) is left out of this figure. The direction is unchanged, but the published figure is stale. Source: `docs/posts/week-2026-11-20/post.md`, "This week's story" bullet 3.

2. **Minor: inbox DECISION item 2 (NMETF-SIZE) states NM-ETF's pre-11-19 record wrongly.** `research/owner_inbox/2026-11-20.md:236` says "record before 11-19 was 33 tr, +0.21R", right after the Primary figures. It is actually all accounts **including** 11-19 (Testing A 10, Testing C 8, Primary 15). Primary alone before 11-19 was 12 trades, +2.01R (+0.168R/trade). The owner is deciding on this item, so the basis should be stated. The consultant line (`:187`, "+2.01R before 11-19") does use the correct Primary basis, so the two lines disagree.

3. **Minor: two dollar bases are both called "Alpaca", and a third is used in code.**
   - The daily briefs and nightly "hold streak" lines give the journal's fill P/L as "Alpaca $": +$1,478.68, −$465.07, +$299.32, −$760.48.
   - The week post uses the broker's day P/L (+$1,475, −$467, +$296, −$763), which sums to $756. The journal fills sum to $766.61.
   - On 11-20 the two are identical ($214.16).
   - The repo's own `daily_post.accounts()` uses close-to-close equity from stored reconcile closes. It gives $211.88 for 11-20, $754.64 for the week and **$309.03 since 10-23**, not $313. The cause: the stored 11-19 close (84,122.92) differs from Alpaca's `last_equity` (84,120.64), and the method mixes `alpaca_day_pl` days with close-to-close days, so the days do not telescope.
   - The post's +$313 is the correct equity change after the glitch adjustment (checked against equity directly). But anyone regenerating it with the repo tool will get $309.
   - No figure is materially wrong; the tolerance is $2–5.

4. **Info, no error:** −66.0R since 10-23 includes 11-05/06. That is correct, since the broker glitch affected dollars only, not the journal's R. The post's parenthetical "(11-05/11-06 broker glitch excluded)" sits next to both figures but applies only to the $ figure.

No critical or major findings. Every headline Primary number the owner would decide on is confirmed:
- week +4.1R / ~$756, 193 trades
- 11-20: +3.00R / $214.16, shorts 20/20 +15.3R, NM-ETF −12.57R burst, Compass gate 13 trades −12.35R
- since 10-23: −66.0R, +$313, 7 of 21 days green


## Verifier

```json
{
 "confirmed": [
  {
   "finding": "The week post's 'Where Primary's money comes from' figures are one day out of date. It says the gap-down shorts made +73.4R on 530 trades since 10-06 and everything else made -161R. Those numbers hold only through 11-19 and leave out 11-20.",
   "severity": "minor",
   "evidence": "docs/posts/week-2026-11-20/post.md:21. I recomputed it from live.csv, Primary only, from 10-06, for L3-gap-slope-fromopen-FD, RW3-gapdn-rsi5pop-flowsell-short-FD and RW5-heat30-flowsell-rsi5pop-gapdn-short-FD. Through 11-19: 530 trades, +73.43R; everything else -160.96R. Through 11-20: 550 trades, +88.77R; everything else -173.31R. The post was committed on 2026-11-21 at 00:53 UTC, after 11-20 closed, so it should include 11-20.",
   "fix": "Change the figures to +88.8R on 550 trades and -173R for everything else, or label them 'through 11-19'."
  },
  {
   "finding": "Inbox decision item 2 (NMETF-SIZE) gives NM-ETF's record 'before 11-19' as '33 tr, +0.21R', right after the Primary figures. Primary alone before 11-19 was 12 trades, +2.01R. That disagrees with the consultant line in the same file, which uses the Primary basis.",
   "severity": "minor",
   "evidence": "research/owner_inbox/2026-11-20.md:236. live.csv, Primary, NM-ETF, dates before 11-19: 12 trades, +2.015R. The same file at about line 187 says 'green on 5 of 7 days (+2.01R) before 11-19'. I did not re-check the claim that 33 trades / +0.21R is all accounts including 11-19.",
   "fix": "State the basis: Primary before 11-19 was 12 trades, +2.01R. If the 33-trade figure stays, label it as all accounts and give its date range."
  },
  {
   "finding": "The daily briefs label the journal's fill P/L as 'Alpaca $'. The broker's own day P/L, which the week post uses, differs by $2-4 per day.",
   "severity": "minor",
   "evidence": "The briefs give 11-16 +$1,478.68 (research/owner_inbox/2026-11-16.md:35,57), 11-18 +$299.32 (2026-11-18.md:95,99) and 11-19 -$760.48 (research/bdi/1119/NOTES.md:69). origin/mcf-data:status.json history alpaca_day_pl gives 1474.81 / -466.67 / 296.01 / -762.76 / 214.16 for 11-16..11-20.",
   "fix": "Use status.json alpaca_day_pl for any figure labelled 'Alpaca', or relabel the journal figure as 'journal fills'."
  }
 ],
 "rejected": [
  "Sub-point of finding 3: daily_post.accounts() gives $309.03 since 10-23 instead of $313. Not reproduced here; I did not run the repo tool. The post's $313 matches the equity change after the glitch adjustment, so the published figure is correct.",
  "Finding 4 is informational and not an error. The -66.0R since 10-23 correctly includes 11-05/06, because the glitch affected dollars only."
 ]
}
```
