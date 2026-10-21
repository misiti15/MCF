"""gates1021: read-only fetch of the 2026-10-20 and 2026-10-21 SIP 1-minute bars (lab universe + the names Primary
traded today) into the session scratchpad, for the live-day diagnosis only (no scoring of any configuration uses
these bars). Market-data GET only; keys come from the environment and are never written anywhere.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SCR  # noqa: E402

EXTRA = "SPY QQQ IWM ROIV CLSK HUT RIOT FPS CIFR SKHY NBIS FTNT TKNO AAOI AKAM AXTI CBRS CRWV IBRX JD IREN WULF MARA " \
        "BITF CORZ APLD BTDR GLXY XLK SMH SOXX IGV".split()


def main():
    tz = ZoneInfo("America/New_York")
    syms = sorted(set((ROOT / "research" / "lab_symbols.txt").read_text().split()) | set(EXTRA))
    out = SCR / "today"
    out.mkdir(parents=True, exist_ok=True)
    cl = _client()
    parts = []
    for i in range(0, len(syms), 200):
        got = fetch_bars(syms[i:i + 200], datetime(2026, 10, 20, 9, 30, tzinfo=tz), datetime(2026, 10, 21, 16, 0, tzinfo=tz),
                         feed="sip", client=cl)
        for s, df in got.items():
            d = df.copy()
            d["symbol"] = s
            parts.append(d)
        print(i, len(got), flush=True)
    allb = pd.concat(parts)
    allb.to_parquet(out / "bars_1020_1021.parquet")
    print("rows", len(allb), "symbols", allb["symbol"].nunique(), "last", allb.index.max())


if __name__ == "__main__":
    main()
