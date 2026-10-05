# MarcoFlow paper account closeout — 2026-10-05

*Educational only — not financial advice.*

Owner asked to flatten the Alpaca paper account (expected nothing open). It held **126 positions**
(23 long, 103 short) left over from MarcoFlow's last session (orders stop 2026-10-02 13:02 ET).
No open orders. All 126 were closed with market orders at ~14:01 ET on 2026-10-05; all filled.

| | Positions | Realized vs avg entry | Closed green |
|---|---|---|---|
| Long | 23 | +$329.92 | 61% |
| Short | 103 | −$198.18 | 53% |
| **Total** | 126 | **+$131.74** | |

- Unrealized at the 14:00 snapshot was +$169.70; ~$38 was lost to the market-order closes.
- Account after: equity = cash = $96,392.91, no positions.
- These were held over a weekend, outside MarcoFlow's intraday design, so they are **not**
  evidence about MarcoFlow's exits. MarcoFlow's own `PaperTrade` rows for them remain open.

Files: `positions_before_close.csv` (broker snapshot), `open_orders_before_close.csv` (empty),
`close_orders.csv` (fills), `closeout_realized.csv` (per-symbol P&L).
