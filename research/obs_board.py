"""Observer board reader (2026-11-17): parses every ts (two formats on the board: '...-05:00' ET offsets and '...Z' UTC) instead
of comparing strings, so no post is missed or mis-ordered. usage: python research/obs_board.py <since, e.g. 2026-11-17T11:45> [--all]
Educational only - not financial advice."""
import json, sys, pandas as pd
from pathlib import Path
B = Path(__file__).resolve().parents[1] / "board.jsonl"
def ts(t):
    x = pd.Timestamp(t); return (x if x.tzinfo else x.tz_localize("America/New_York")).tz_convert("America/New_York")
since = ts(sys.argv[1] if len(sys.argv) > 1 else "2000-01-01"); L, bad = [], 0
for l in B.read_text().splitlines():                        # every field optional: a malformed post is shown, never crashes the read
    if not l.strip(): continue
    try: o = json.loads(l); o["_t"] = ts(o.get("ts", "2000-01-01"))
    except Exception: bad += 1; continue
    L.append(o)
for o in sorted(L, key=lambda o: o["_t"]):
    if o["_t"] > since and ("--all" in sys.argv or o.get("from") != "observer"):
        print(f"{o['_t']:%m-%d %H:%M} {o.get('id', '?')} -> {o.get('to', '?')} | ref {o.get('ref', '') or '-'} | {o.get('text', '')}\n")
if bad: print(f"[{bad} board line(s) could not be parsed]")
