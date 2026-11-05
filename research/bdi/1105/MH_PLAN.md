# MH1105-P1 — gap-up names against a falling tape, short at 09:50 (pre-registered 2026-11-05 17:37 ET, before any 2-year read)

*Educational only — not financial advice.*

Recurring precursor (Move Hunt 11-03 banks short 10:45; 11-04 11 gap-up banks faded from 09:35; 11-05 the single-name short
list ≥ 09:50 is C, JPM, MS, BNY, WFC, BLK, STT, PNC, HBAN, KEY, AMP — gap +0.9..+2.0%, already below the open, SPY −1.24% at 09:50 —
each falling 1.7-2.7 daily ATR to 10:53; research/bdi/1105/moves_alt_out.txt).

Rule (known at the 09:50 bar close): lab frame rows at tod 950, adv20 >= $95M, gap >= +0.80%, fromOpen <= 0, SPY spy_fo (lab
context) <= −0.50%. Short at the 09:50 close; outcome = lab label r_short_t1s1 (R = 0.25 daily ATR, 1R target / 1R stop,
$0.01/share each side, out by 15:55). Lab frames (research/history2y), open months only, locked block never read.
Config 6 of tonight (FB1 ×4, L9, this) → full bar max(1.5, sqrt(2 ln 6)) = 1.89; Testing bar (BAR90) 1.70.
Pass (Testing bar): n >= 200 on >= 20 days; day-clustered t >= 1.70; avg R > 0 in TRAIN (< 2025-09-01) AND VALID; > 0 on up AND
down SPY sessions; beats random entries (excess over all liquid 09:50 short rows of the same days, t > 0); walk-forward positive
months >= 54%; avg R w/o best day reported (flag at >= 50% share). Pass → backlog candidate for a Testing / low-rep slot
(needs a 09:50 entry at the open of the trading window; never Primary).
