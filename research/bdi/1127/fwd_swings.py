"""BDI 1127: runs research/bdi/swings/forward.py (L1 / L2 / L3 / L6 forward rows) unchanged in logic, with three wrapper
edits made at load time: all 10 accounts (p od ta tb tc td te tf gen gy, as in the 11-25 tally), other hypotheses' rows for
the same date (L19) are kept, and the hypotheses.jsonl refresh is skipped (its running dicts are kept as they are).
Half day 11-27: bars end 12:59. Usage: python fwd_swings.py <scratch> <day>. Educational only - not financial advice."""
import sys
from pathlib import Path
src = Path(__file__).resolve().parents[1] / "swings" / "forward.py"
s = src.read_text()
s = s.replace('for a in ("p", "t1", "t2", "gy", "gen"):', 'for a in ("p", "od", "ta", "tb", "tc", "td", "te", "tf", "gen", "gy"):')
s = s.replace("old = old[old.date != D]", 'old = old[~((old.date == D) & old.hyp.isin(["L1", "L2", "L3", "L6"]))]')
s = s.split("# refresh running forward numbers")[0] + 'print(F[F.date == D].to_string(index=False)); print("Educational only - not financial advice.")\n'
assert '"od"' in s and "isin([" in s
exec(compile(s, str(src), "exec"), {"__file__": str(src), "__name__": "__main__"})
