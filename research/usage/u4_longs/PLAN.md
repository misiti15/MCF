Educational only — not financial advice

# U4 long-side program — pre-registration (written 2026-11-18 ~17:45 UTC, before any spec was scored)

USAGE PLAN item 4 (owner 2026-11-18). Research only, market hours: no config / code / runtime change, no PR, no merge.
Primary is ~80% short (1,075 of 1,316 live trades). Goal: long setups that make R on SPY up days and quiet days,
where Primary loses, with low correlation to Primary's daily R.

## Part A — existing live long setups (descriptive, no tuning)

- Source: journal.db (run_id 1) of all ten mcf-data* state branches, 10-06..11-17 (11-18 still open, left out).
  R after costs = pnl_adj / (|entry - stop| x shares) (r_multiple where pnl_adj is missing).
- Every long setup with >= 30 live trades is listed: n, active days, total, avg, avg w/o best day, best-day share,
  fit (10-06..10-27) / check (10-28..11-17) avg, day-clustered t, accounts. "With evidence" = avg w/o best day > 0
  AND positive in both halves.
- For the setups "with evidence" and the top 5 by avg w/o best day: R by SPY day type and the correlation of their
  daily R with Primary's daily R (Primary journal as traded).
- A live long setup cannot become a new Testing copy from this part alone (no new evidence); Part A only says which
  existing long records deserve exposure.

## Part B — five new mechanism-based long specs (one pre-registered config each, two fixed exit packages)

Data: live-session full-universe packs (GitHub release bars-2026-10 / bars-2026-11, 1min + 1day), 31 sessions
10-06..11-17; plus the 2-year packs (bars2y-*) where stored and where the session's 60 calendar days of priors do not
touch the locked block 2024-11-01..2025-02-28: sessions 2024-09-16..2024-10-31 and 2025-05-01..2026-01-30.
The locked block is never read (1day rows inside it are dropped and asserted absent). Packs are streamed one day at a
time and deleted.

Universe per session: prior close >= $5, 20-day average dollar volume >= $20M, >= 15 prior daily bars, ATR14 > 0.
Priors from daily bars strictly before the session. Decision on 5-minute bars (09:35..15:55 bar ends) built from the
1-minute pack. VWAP = cumulative session VWAP. rvol = cumulative volume / (ADV20 shares x elapsed/390).
ret_o = close / session open - 1. SPY ret_o the same for SPY at the same bar.

| Code | Mechanism (falsifiable reason) | Conditions (decision bar ends T) |
|---|---|---|
| U4-ODC | Opening-drive continuation: gap-ups with relative strength and heavy volume keep driving after they clear the opening range (buyers still in control) | gap in [+2%, +15%]; T in 09:45..10:30; first bar with close > 09:30-09:45 high, close > VWAP, ret_o - SPY ret_o >= +0.5%, rvol >= 2.0 |
| U4-VWR | VWAP reclaim on up-tape days: in a daily up-trend name, losing and then reclaiming VWAP while SPY is up is a failed sell-off that trapped shorts | SPY ret_o >= +0.20% at T; prior close > SMA20d > SMA50d; T in 10:00..14:30; previous 5-min close < VWAP and this close > VWAP; rvol >= 1.0; first per symbol-day |
| U4-RSB | Relative-strength leader breakout (sector map not in the packs, so "leader" = universe RS): leaders breaking to new 20-day highs on a green tape see continuation | 20-day return in the day's top 10% of the universe and prior close within 5% of its 20-day high; SPY ret_o >= 0; T in 10:00..15:00; first bar with close > max(prior-day high, 20-day high), close > VWAP, ret_o > SPY ret_o, rvol >= 1.5 |
| U4-MPB | Morning pullback in strong names: an early-strong name that pulls back to VWAP and resumes is bought by late buyers | at the 10:00 bar ret_o >= +1.5%, ret_o - SPY ret_o >= +1.0%, rvol >= 2.0; T in 10:15..11:30; the low since the day's high <= HOD - 0.4 x (HOD - open) and >= VWAP - 0.1 x ATR14; trigger: close > previous bar high and close > VWAP; first per symbol-day |
| U4-PMT | PM trend continuation (aimed at quiet and up days): names that trended above VWAP all day and sit near the high at 13:30 keep drifting up into the close (accumulation / MOC demand) | T = 13:30 only; ret_o >= +2%; close >= HOD - 0.25 x ATR14; every 5-min close from 10:30 to T > VWAP; rvol >= 1.2 |

Common execution (all specs, fixed): long only; entry at the open of the 1-minute bar that starts at T; stop =
entry - 0.30 x ATR14 (daily); two exit packages, both fixed in advance:
- E1: target +1.5R (fills only if the bar high trades through the target by >= $0.01), stop, flat at 15:55.
- E2: no target; stop, flat at 15:55.
Stop first inside a bar; a gap through the stop fills at the bar open. One entry per symbol per day per spec; at most
15 entries per spec per day in time order (ties: higher rvol first).

Costs (LR8 + engine slippage, against us): entry + max($0.01, 1 bp) slippage + 1 bp; stop exits + max($0.02, 4 bps)
+ $0.01; flat exits + max($0.01, 1 bp) + $0.01; target at the limit; SEC 27.8 per $M on the sell, TAF $0.000166/share.

Configurations: 5 specs x 2 exits = **N = 10** (plus the 2-year re-score of the same 10, not new configs).
Bar: day-clustered t >= max(1.5, sqrt(2 ln 10)) = **2.15** (full bar); Testing bar (BAR90) 0.9 x 2.15 = 1.93.

## Splits, controls and reporting

- Live packs: fit = 10-06..10-27 (16 sessions), check = 10-28..11-17 (15 sessions). 2-year: H1 = 2024-09-16..2025-08-29,
  H2 = 2025-09-02..2026-01-30.
- Day types (SPY): up = open-to-close > +0.25%, down < -0.25%, quiet otherwise; also SPY gap-up (open vs prior close
  >= +0.30%). R per trade and per day reported by day type.
- Correlation of each config's daily R (sessions with no trade = 0) with Primary's daily R (journal as traded), and
  Primary's R on the days the spec is green.
- Random controls (5 seeds each): (a) same-time control — a random universe name at the same decision bar, same exits;
  (b) same symbol-day at a random bar inside the spec's window, same exits.
- Every config reported (failures first): n, days, avg R, total, day-clustered t, avg w/o best day + best-day share,
  fit/check, 2-year halves, day types, random controls.

## Pass rule for a Testing-copy proposal (fixed now)

All of: avg R after costs > 0 on live packs in BOTH halves; live day-clustered t >= 1.93 (BAR90) — a full pass needs
2.15; avg w/o best day > 0 and best-day share < 50%; beats both random controls on avg R; 2-year avg R > 0 in both
2-year halves; avg R >= 0 on SPY up days and on quiet days (the target day types). Anything passing becomes a Testing
copy proposal (decision code), never deployed by this study (promotion hold on). If nothing passes, the best 1-3 are
reported as "not proposed" with the gap to the bar.
