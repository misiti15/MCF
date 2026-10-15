"""Fetch SPUU (Direxion 2x S&P 500) SIP 1-minute bars into data/cache_hist/1Min with the history2y downloader
(same format, read-only market data). Its STOP_UTC guard is for the 2026-10-08 bulk run; lifted here for one symbol.
Keys from ALPACA_API_KEY / ALPACA_SECRET_KEY (never printed). Educational only - not financial advice."""
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
load_dotenv(ROOT / ".env")
import download as dl  # noqa: E402

dl.STOP_UTC = datetime(2100, 1, 1, tzinfo=timezone.utc)
dl.ARGS.update({"start": "2024-09-16T00:00:00Z", "end": "2026-10-08T00:00:00Z"})
for sym in sys.argv[1:] or ["SPUU"]:
    print(dl.fetch(sym))
