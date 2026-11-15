"""FAMC calendar health, headline audit (Observer 2026-11-14; replaces the gap ratio as the PRIMARY health line, which stays
as context: 74% of known AMC events open > 2x normal vs 21% of random days, so it is a weak instrument; NOTES_cal.md).
Outcome-free: for every calendar row (symbol, report_date), fetch that evening's (16:00-19:59 ET) single-symbol Alpaca news
and classify whether at least one item is a RESULTS RELEASE (strict pattern below), not just an earnings-ish headline.
Precision proxy = share of rows with a results release. It checks precision only; recall (AMC names the hybrid missed) needs
a late calendar (Skeptic). Never writes the calendar. Read-only GETs, keys from env, refuses 07:30-16:00 ET on weekdays.
usage (MCF checkout): python ../guild/research/obs-amcnews/headline_audit.py [--since YYYY-MM-DD]
Educational only - not financial advice."""
import re, sys, importlib.util, pandas as pd
from datetime import datetime
from pathlib import Path
spec = importlib.util.spec_from_file_location("famc", str(Path(__file__).with_name("build_famc_cal.py"))); F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
RESULTS = re.compile(r"(\bQ[1-4]\b.{0,30}\b(EPS|Sales|Revenue|Loss|Earnings)\b|\b(Reports?|Announces?|Posts?)\b.{0,60}\b(Results|Quarter|Fiscal)\b|"
                     r"\bFinancial Results\b|\b(Quarter|Year)(ly)?[- ]End(ed)? Results\b|\bSees (Q[1-4]|FY)\b|\bRaises FY|\bLowers FY)", re.I)
now = datetime.now(F.ET)
if now.weekday() < 5 and 450 <= now.hour * 60 + now.minute < 960: sys.exit("refusing: 07:30-16:00 ET")
since = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--since=")), "2000-01-01")
cal = pd.read_csv(F.CAL); cal = cal[cal.report_date.astype(str) >= since]; rows = []
for D, g in cal.groupby("report_date"):
    ev = F.news(str(D), 16, 19)
    for s in g.symbol:
        hs = [x.get("headline", "") for x in ev if (x.get("symbols") or []) == [s]]
        hit = [h for h in hs if RESULTS.search(h or "")]
        rows.append(dict(report_date=D, symbol=s, n_items=len(hs), results_release=bool(hit), example=(hit or hs or [""])[0][:120]))
out = pd.DataFrame(rows); out.to_csv(Path(__file__).with_name("famc_headline_audit.csv"), index=False)
by = out.groupby("report_date").results_release.agg(["sum", "size"])
print(out.to_string(index=False))
print(f"\nheadline audit (precision proxy): {int(out.results_release.sum())} of {len(out)} rows carry a results release in the evening window; "
      + "; ".join(f"{d}: {int(r['sum'])}/{int(r['size'])}" for d, r in by.iterrows()))
print("Educational only - not financial advice.")
