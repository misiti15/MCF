Educational only — not financial advice

# MCF crypto setups, round 1: the first hand-built setups (2026-11-26)

These are the first crypto setups built by hand from research, in the way the first equity setups were built
before the generator (docs/RESEARCH.md). Each card gives the name, the id, the mechanism (why it should exist), the
exact rules, the coins and the evidence. Rules were fixed in `PREREG.md` (sha256 in `PREREG.sha256`) before any
scoring; results are in `REPORT.md`. **None passed the testing-candidate bar, so none runs anywhere.**

**Rules common to every card**
- **Long only:** Alpaca crypto spot has no shorting and no margin.
- **Data:** signals come from clean traded-only bars (bad prints removed, minutes with no trade ignored).
- **Entry:** always a resting **maker limit buy**. It fills only if a later real trade goes *through* the limit.
  A missed order is never chased.
- **Stop:** max(1.5 × ATR(14, 4h), 3 % for BTC/ETH or 4 % for alts) below the fill. It is a taker exit.
- **Positions:** one position or resting order per coin per setup.
- **Costs:** Alpaca tier 1 (maker 0.15 %, taker 0.25 %), plus the half-spread and slippage on taker exits.
- **Gates:** "BTC down-trend off" means no new trades while BTC's last daily close is below its SMA50 *and* that
  SMA50 is lower than it was 10 days earlier. "BTC uptrend" means BTC's last daily close is above its SMA50.
- **Coins:** majors are BTC and ETH. Alts are SOL, DOGE, LINK and UNI, the coins with the best range per unit of
  cost (ANATOMY §1).

---
### CRY-FLUSH-1 · Flush rebound
- **Mechanism:** a liquidation flush overshoots. Forced selling is done within the hour, so price snaps back over
  the next 4-12 h. Measured: after a ≤ −3σ hour, +106 bps at 12 h, +132 bps on alts (ANATOMY §3).
- **Trigger:** a 1-hour return of ≤ −3σ, where σ is the trailing 30-day hourly σ. The hour must have at least 3
  traded minutes, and so must the hour before it.
- **Entry:** a limit at the hour's close − 0.25 × ATR(1h), live for 2 h. Never buy the print (ANATOMY §3c).
- **Exit:** a time stop at 12 h, with no target.
- **Gate and filter:** BTC down-trend off, because the flush median flips in the 2022 bear. Runs 24/7.
- **Coins:** variant a = BTC, ETH; variant b = SOL, DOGE, LINK, UNI.

### CRY-SHOCK-1 · Down-shock bounce, skip the first hour
- **Mechanism:** a moderate down-shock (2-3σ) also mean-reverts. About a third of the 4h bounce sits in the first
  hour, where bid-ask bounce lives, so the setup waits that hour out. It trades only when the vol clock says there
  is movement to capture (ANATOMY §2-3: h+1→h+4 is still +29..+55 bps on alts).
- **Trigger:** a 1-hour return between −3σ and −2σ (it does not overlap FLUSH). The hour must fall on a weekday
  between 13:00 and 20:59 UTC (the US session), or in the 00 UTC hour.
- **Entry:** wait one hour; that hour must trade. Then a limit at its close − 0.25 × ATR(1h), live for 1 h.
- **Exit:** a time stop at 12 h.
- **Gate:** BTC down-trend off.
- **Coins:** SOL, DOGE, LINK, UNI.

### CRY-REV12-1 · 12-hour session reversal
- **Mechanism:** traders overreact across the 12-hour Asia/EU and US blocks, and the next block partly reverses the
  move (JRFM 2025 via KNOWLEDGE #3; daily autocorrelation −0.01..−0.09, ANATOMY §3). There are only two decisions a
  day.
- **Trigger:** at 00:00 or 12:00 UTC on a weekday, the prior 12-hour return is ≤ −2σ12, where σ12 is taken over
  the trailing 180 blocks. The block's last hour must have traded.
- **Entry:** a limit at the close − 0.25 × ATR(1h), live for 1 h.
- **Exit:** a time stop at 12 h, which is about the next block boundary.
- **Gate:** BTC down-trend off.
- **Coins:** variant a = BTC, ETH; variant b = majors plus alts.

### CRY-UPDIP-1 · Don't chase: buy the pullback after an extreme up-day
- **Mechanism:** big up-moves fade. Up hours give back −23 bps over 4 h (ANATOMY §3), and there is no momentum at
  any horizon. A long-only book should not chase the up-day; it should bid where the fade usually ends, inside a
  BTC uptrend.
- **Trigger:** a weekday UTC day D with a daily z of at least +2 (σ over the trailing 90 days) and a close above
  its open. The decision is at 00:00 on D+1.
- **Entry:** a limit at a 50 % retrace of D's body, live for 24 h.
- **Exit:** a maker target at D's close, and a time stop at 24 h.
- **Gate:** BTC uptrend.
- **Coins:** variant a = BTC, ETH; variant b = alts.

### CRY-DAY2-1 · Day-2 crash bounce
- **Mechanism:** after a crash day, the forced sellers are gone, and the next session finds a base and retraces
  part of the range (KNOWLEDGE #7; down-shock bounces keep their sign in every regime, ANATOMY §5).
- **Trigger:** a crash day D, with a UTC-day return of ≤ −8 % for BTC/ETH or ≤ −12 % for alts.
- **Entry, variant a "reclaim":** on D+1 between 00:00 and 16:00 UTC, price first trades below D's low; at the
  first 1h close back above that low, place a limit at D's low, live for 4 h.
- **Entry, variant b "open":** at 00:00 on D+1, a limit at D's close − 0.25 × ATR(1d), live for 16 h.
- **Exit:** a maker target at the middle of D's range (at least +0.5R), and a time stop at 24 h.
- **Gate:** none, because the setup is built for crashes.
- **Coins:** majors plus alts.

### CRY-WKND-1 · Weekend-drop Monday reclaim
- **Mechanism:** thin weekend books overshoot. When weekday liquidity returns, a reclaim of the Friday consensus
  price marks the end of the weekend drop (KNOWLEDGE #5; weekend moves run at 0.75-0.88× weekday moves, ANATOMY §2).
- **Trigger:** the weekend low (Friday 16:00 ET to Sunday 22:00 UTC) is at least 4 % below the Friday 16:00 ET
  price for BTC/ETH, or 6 % for alts. Then comes the first 1h close back above the Friday price between Sunday
  22:00 and Monday 15:00 UTC.
- **Entry:** a limit at the Friday price, live for 4 h.
- **Exit:** a maker target at max(the weekend high, +1R), and a time stop at 24 h.
- **Gate:** BTC down-trend off.
- **Coins:** variant a = BTC, ETH, LINK; variant b = majors plus alts.

### CRY-CPI-1 · CPI-morning drift
- **Mechanism:** CPI is the one macro print that moves BTC, and the first-hour reaction tracks the surprise
  (KNOWLEDGE #6). A firm up-reaction should drift on.
- **Few events:** only 64 CPI days fall in FIT and CHECK, and 22 triggered and 13 filled. This setup **cannot** reach
  60 trades.
- **Trigger:** on a CPI day at 08:45 ET, the last print is ≥ +1.2 % above the last print before 08:30, and it is
  above the 08:30-08:45 VWAP.
- **Entry:** a limit at that VWAP, live for 30 min.
- **Exit:** the stop sits at the pre-08:30 price (at least 2 % below). A maker target at +2R; the time stop is
  16:00 ET.
- **Gate:** none.
- **Coins:** BTC, ETH.

### CRY-DIP-1 · Oversold dip inside an uptrend
- **Mechanism:** intraday returns mean-revert at every horizon (ANATOMY §3). Inside an uptrend, where both the
  coin and BTC sit above their SMA50, a sharp 24-hour dip is a pause, not a regime break.
- **Trigger:** at each weekday 4h close, the 24-hour return is ≤ −1.5σ24, where σ24 is taken over the trailing 90
  days.
- **Entry:** a limit at the close − 0.25 × ATR(1h), live for 4 h.
- **Exit:** a time stop at 24 h.
- **Gate:** BTC uptrend, and the coin's own last daily close is above its SMA50.
- **Coins:** variant a = BTC, ETH; variant b = alts.

### CRY-TREND-REF · Daily trend overlay (reference only, swing)
- **Rule:** round-3 rule 980. Hold BTC, ETH and SOL (equal sleeves) while the daily close is above its SMA50.
- **Status:** it was not re-scored here.
- **Round-3 result:** on CHECK it returned +7.6 % with a 32 % max drawdown, against −37.6 % and 59 % for
  buy-and-hold. The trade t was 0.48.
- **Use:** it is the swing reference and the regime context for the setups above. It is outside the intraday
  charter unless the owner widens the scope.

---
**Dropped as seeds (no edge in ANATOMY §6):**
- Asia-range breakout
- CME gap fill
- round numbers
- BTC→alt lead (a stale-print artifact)
- SPY lead
- hour-of-day drift
- big-hour continuation

**Capacity:** Alpaca's venue is tiny. Since 2025, BTC trades about $166k a day and the alts $2-45k (ANATOMY §0).
A realistic size is ≤ 1-2 % of a day's prints: about $2-3k notional per BTC trade, $1-2k for ETH, and $20-900
for the alts.

Educational only — not financial advice
