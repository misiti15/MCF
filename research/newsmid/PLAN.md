# NEWSMID — a mid-session analyst action (published 10:00-14:30 ET): does the name drift its way to 15:55? (DRAFT, not frozen)
Educational only — not financial advice. Tomorrow's (11-12) direction pilot. Freeze after Skeptic's pre-audit; one look.
Outcomes NOT read yet: only headline counts (below) have been looked at.

## Why it might work / why it might not
New information arriving DURING the session (Lead's ask): unlike overnight news (NEWSDIR: direction already in the gap by 09:50),
a 10:00-14:30 publication can carry direction the morning did not price. Risk: Benzinga often re-posts a note issued
pre-market (already priced), and post-earnings PT changes ride the earnings reaction — so the pre-entry move is reported and
earnings days are excluded.

## Data (fetched 11-11, Alpaca GET only)
News: `research/newsmid/fetch.py` -> 27,467 items, sessions 10-08..11-09, 13:30-21:00 UTC, no content (headline, symbols,
created_at, updated_at, source). updated != created on 2.9% (created_at used; it is the first-publish time).
Bars: HODSEP 5-min SIP (lab names, 10-08..11-09) + daily for ATR (days < D only). Same 23 test sessions as DISP1.
Counts looked at (no outcomes): single-symbol lab items 10:00-14:30: 7,073 (benzinga 4,176, fiscal.ai 2,897).
Lexicon hits: an_up 1,413 (558 names), an_dn 1,270 (527 names); explainers ("Why is X stock falling") only 63 -> dropped.

## Event (fixed lexicon, case-insensitive, frozen as written)
an_up: `\b(upgrade[sd]?|raises? (its )?price target|boosts? price target|initiates? .*(buy|outperform|overweight))`
an_dn: `\b(downgrade[sd]?|lowers? (its )?price target|cuts? price target|initiates? .*(sell|underperform|underweight))`
Single-symbol, lab name, source benzinga, created_at in [10:00, 14:30) ET; both lexicons hit -> dropped.
First qualifying item per name-day only; if a name has opposite-sign items that day before entry -> dropped.
Earnings exclusion (checklist 18, in-data): drop the name-day if any item for that name D-1 16:00 .. D 16:00 matches
`earnings|Q[1-4] 20\d\d|results|guidance|transcript`. Price >= $5.

## Trade and outcome
s = +1 (an_up) / -1 (an_dn). Entry = open of the first 5-min bar whose START is >= created_at + 1 minute (strict, checklist 2);
entry bar must start <= 14:30. Exit = close of the 15:50 bar. ATR units; ex-SPY over the same hold (checklist 16):
c = s x [(exit/entry - 1) - beta 1 x (SPY exit/entry - 1)] / ATR%.
Costs (member leg, production): entry 1c + 1bp x 1.4 + 4.4bp spread, exit 1c + 1bp (no hedge leg charged; ex-SPY is a
measurement). Pre-entry move m = s x (entry / 09:30 open - 1) / ATR% reported per tercile (checklist 5: selection is by
headline only; the outcome starts after entry).

## Control (checklist 9-11)
For each event: all lab names with NO news item that day, entering at the SAME 5-min bar, in the same terciles of signed
pre-entry move (s x move 09:30 -> entry, in ATR) and ATR%; control value = their mean c with the event's s.
Excess = c - control. Primary metric = mean excess, day-clustered t.

## Counting and bar
Configs 2 (follow / fade). Family = news family (NEWSDIR's 145: bdi-1008-material-news-filter, news-catalyst, orb-news-guard,
NEWSDIR, UNGAP's news split counted there) + 2 = 147 -> BAR90 2.84.

## Pass (all of)
1. |t(excess)| >= 2.84 and the chosen direction's net (mean c minus cost, in ATR) > 0 per trade (gross first: c itself > cost).
2. Same sign w/o the best day; same sign on an_up and an_dn legs separately; same sign in TRAIN half (10-08..10-23) and
   second half (10-26..11-09).
3. Long leg (an_up) on its own > 0 net (we prefer longs; reported, a pass without it is flagged).
Reported (not gates): pre-entry move terciles, entry-time buckets (10:00-11:00 / 11-12:30 / 12:30-14:30), per-day counts,
skip funnel, SPY up/down day split (reporting only, checklist 4), median c.

## Kill line
Fails 1 -> NEWSMID closed. Passes -> forward shadow plan (40-60 sessions, checklist 29) to Lead; nothing live.

## Checklist run (research/SKEPTIC_CHECKLIST.md, 30 items)
1 no lookback slices (prices by bar time); 2 strict +1 min; 3 no default lookups (assert bars present); 4 no day labels as
gates; 5 selection by headline only, pre-move reported; 6 publish time = created_at, earnings days excluded; 7 news fetched
after the fact — created_at is the vendor's first-publish stamp (risk: back-dated items; check 20 random items' created_at
vs the first 5-min volume spike as a sanity table, reported); 8 no locked block (2026 only); 9-11 matched same-bar control
with pre-move/ATR terciles; 12 n/a; 13 legs stratified; 14 control uses ALL no-news names; 15 ATR only (no stop -> no R);
16 ex-SPY over the hold; 17 gross first; 18 in-data earnings exclusion; 19 fixed lab list; 20 n/a (no classifier precision
claim); 21 window fixed 10-08..11-09; 22 bars and prices both from the same split-adjusted SIP source; 23 n/a; 24 family 147;
25 distinct name-days only; 26 cells shown are reporting only; 27 n/a; 28 n/a; 29 forward needs 40-60 sessions; 30 if all
days one sign -> look-ahead hunt first.
