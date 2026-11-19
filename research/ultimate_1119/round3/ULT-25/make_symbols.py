"""ULT-25 symbol lists from fund NAMES / types only (no outcomes), before any ULT-25 scoring.
LEV = ULT-20 LEV (name regex) + ULT-21 leverage > 1 or inverse + name-identified leveraged/inverse funds the two lists
missed. NONLEV = every known lab symbol (ULT-23 STOCKS + FUNDS) minus LEV. Educational only - not financial advice."""
import json, time
from pathlib import Path
M = Path(__file__).resolve().parents[2] / "modules"
u20 = json.loads((M / "ULT-20_symbols.json").read_text())
u21 = json.loads((M / "ULT-21_universe.json").read_text())
u23 = json.loads((M / "ULT-23_symbols.json").read_text())
extra = ["BULZ", "DDM", "DOG", "DPST", "DUST", "DXD", "ERX", "FAS", "FAZ", "FNGU", "JNUG", "LABU", "SH", "SRTY", "TECS",
         "TWM", "URTY", "UWM", "SDS", "SSO", "QLD", "PSQ", "QID", "RWM", "SPDN", "UVXY", "VXX"]
lev = set(u20["LEV"]) | {k for k, v in u21["leverage"].items() if v and abs(v) > 1} | set(u21["inverse"]) | set(extra)
allsym = set(u23["STOCKS"]) | set(u23["FUNDS"])
out = {"note": __doc__.strip(), "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "LEV": sorted(lev), "NONLEV": sorted(allsym - lev)}
(M / "ULT-25_symbols.json").write_text(json.dumps(out, indent=0))
print(len(out["LEV"]), len(out["NONLEV"]))
