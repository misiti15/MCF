# MCF data-source glossary (owner 2026-11-16)

Educational only — not financial advice.

Use these exact names in chat, briefs, dashboard labels and reviews. Never mix sources in one number without saying so.

| Term | What it is | Data | Counts toward promotion |
|---|---|---|---|
| **Live** | Real paper trades in the Alpaca accounts. Dollars = Alpaca P/L; R after costs. | Live broker fills | Yes (1.0 per session) |
| **Shadow** | Forward, signals-only run inside the live runner (run_id 3): same bars and decision points as live, no orders, fills at level B (harder than live). | Live data stream, forward only | Partial, once its weight is measured (SRC-VALUE) |
| **Session replay** | Past recorded sessions re-run through the live runner code (`mcf/replay`): production costs, trade-through limit fills. On days a setup actually traded live it can be scored against live (accuracy); on other days it is a what-if. | Recorded session bars (full universe from 10-06 once storage lands) | Partial (0.35 / 0.2 / 0 by held-out accuracy) |
| **2-year backtest** | The research engine run over ~2 years of Alpaca 1-minute bars (old cache: 1,226 symbols), costs in, locked block 2024-11-01..2025-02-28 never read. | Historical 1-minute bars | No — screening only, shown separately |
| **2-year screen** | The Setup Generator's quick pass of the 2-year backtest. Same data as the 2-year backtest; use "screen" only for the Generator's pass. | Same as above | No — screening only, shown separately |
| **2-year replay** *(planned)* | The live runner code run over the full-universe 2-year bar storage. Replaces the old 2-year backtest engine once it matches session replay on overlap days. | Full-universe historical bars | No — screening only until SRC-VALUE says otherwise |

Rules:
- Non-live sources are never blended into live counts by trade volume; each source has its own columns and a fixed comparison against live ("Screen vs live").
- Each non-live source's weight is set by measurement (SRC-VALUE: how well it predicted later live results — sign hit rate and size of optimism), re-measured as live data grows.
