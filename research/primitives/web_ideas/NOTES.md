# Outside intraday ideas (key: web_ideas), 2026-10-07

*Educational only - not financial advice. Nothing here was backtested. These are ideas for the Testing paper account, not same-day decisions.*

- Configurations tried: 0. Finalists: none. This was a literature and web sweep only (about 20 searches; reddit.com is blocked).
- Outputs:
  - `docs/live/ideas.json`: 20 dashboard rows, with status untested, in-backlog or tested-failed.
  - `research/backlog.jsonl`: 11 new `wi-*` rows with status `idea`. Each row's notes list the lab-frame columns it needs and its red flags.
- Sources are mostly search-engine summaries of blogs and papers. Every number they quote (for example "Sharpe 2.1") is unverified until it is re-measured in MCF with costs.

## New ideas, untested in MCF (added to the backlog)
| id | needs new data or columns? |
|---|---|
| wi-vwap-first-pullback | a per-day count of VWAP touches |
| wi-red-to-green | no (prior close comes from gap and fromOpen) |
| wi-eod-reversal | the lab frame must extend to 15:30 |
| wi-same-halfhour | a trailing same-slot return column |
| wi-vwap-trend-etf | an ETF harness (reddit_bt), not a lab mask |
| wi-lunch-reversal | no |
| wi-williams-volbo | no (fromOpen*close/atr_d) |
| wi-ib-narrow-extension | first-hour high/low (approximate with dist_hod/lod) |
| wi-overreaction-fade | no |
| wi-intraday-vcp | no (approximate) |
| wi-ema-cross | the prior-bar emaDiff (for the cross event); a control test |

The quickest of these to test as plain lab masks are red-to-green, Williams breakout, lunch reversal and overreaction fade.

## Already covered (status shown on the dashboard)
- In the backlog: nr7-orb, intraday-momentum-paper, gap fade (escalation X-gapfade).
- Tested and failed: SIP ORB (orb5, t1-orb-exits), Holy Grail (trend-pullback), RSI(2)-style (obos-vwap-ma), pin bar at levels (obos-levels), noise band (t7), RVOL breakout (t3).

## Recurring metrics in the sources
The metrics the sources mention most are:
- relative volume at the same time of day (used to pick stocks, not direction)
- distance from VWAP
- prior close, PDH and PDL levels
- move from the open in ATR units
- first-hour or opening range
- time of day

All but the opening range before 09:50 are already lab columns or simple to derive from them.
