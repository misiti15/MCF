"""Observer board reader (2026-11-17): parses every ts (two formats on the board: '...-05:00' ET offsets and '...Z' UTC) instead
of comparing strings, so no post is missed or mis-ordered. usage: python research/obs_board.py <since, e.g. 2026-11-17T11:45> [--all]
Educational only - not financial advice."""
import json, sys, pandas as pd
from pathlib import Path
B = Path(__file__).resolve().parents[1] / "board.jsonl"
def ts(t):
    x = pd.Timestamp(t); return (x if x.tzinfo else x.tz_localize("America/New_York")).tz_convert("America/New_York")
since = ts(sys.argv[1] if len(sys.argv) > 1 else "2000-01-01"); L = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
for o in sorted(L, key=lambda o: ts(o["ts"])):
    if ts(o["ts"]) > since and ("--all" in sys.argv or o["from"] != "observer"):
        print(f"{ts(o['ts']):%m-%d %H:%M} {o['id']} -> {o['to']} | {o['text']}\n")
