"""SIZESTOP pre-score data check (Skeptic skeptic-20261114-1051-2): how many top-quintile |gap|/ATR name-days are ex-dividend days?
Proxy universe: SHORTUP's 489 top-adv names (daily bars, scratch), 2025-04..2026-11. Dividends: Alpaca corporate actions
(cash_dividend ex_date, rate; GET only). Also: the gap with the dividend added back. Reads no trade outcome.
    python -I exdiv_check.py <shortup data dir>        Educational only - not financial advice."""
import os, sys, json, urllib.request, urllib.parse, numpy as np, pandas as pd
# --- checklist #43 (Lead 2026-11-15): refuse any request whose date range touches the locked block 2024-11-01..2025-02-28 ---
import urllib.parse as _lk_up, urllib.request as _lk_ur
_lk_real_urlopen = _lk_ur.urlopen
def _lk_guarded_urlopen(req, *a, **k):
    u = req.full_url if hasattr(req, "full_url") else str(req)
    q = dict(_lk_up.parse_qsl(_lk_up.urlsplit(u).query))
    s, e = q.get("start", "")[:10], q.get("end", "")[:10]
    if (s and e and not (e < "2024-11-01" or s > "2025-02-28")) or (s and not e and s <= "2025-02-28"):
        raise RuntimeError(f"locked block: request {s}..{e or 'open'} overlaps 2024-11-01..2025-02-28 (checklist #43)")
    return _lk_real_urlopen(req, *a, **k)
_lk_ur.urlopen = _lk_guarded_urlopen
# --- end checklist #43 ---
D = sys.argv[1]
d = pd.read_csv(f"{D}/daily.csv.gz"); d["date"] = d.t.str[:10]; d = d.sort_values(["symbol", "date"])
syms = sorted(d.symbol.unique())
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
rows = []
for i in range(0, len(syms), 50):
    tok = None
    while True:
        q = {"symbols": ",".join(syms[i:i + 50]), "types": "cash_dividend", "start": "2025-03-01", "end": "2026-11-13", "limit": 1000}
        if tok: q["page_token"] = tok
        j = json.load(urllib.request.urlopen(urllib.request.Request("https://data.alpaca.markets/v1/corporate-actions?" + urllib.parse.urlencode(q), headers=H), timeout=60))
        rows += [dict(symbol=x["symbol"], date=x["ex_date"], rate=x["rate"], special=x.get("special")) for x in j.get("corporate_actions", {}).get("cash_dividends", [])]
        tok = j.get("next_page_token")
        if not tok: break
dv = pd.DataFrame(rows).drop_duplicates(["symbol", "date"]); print(f"cash-dividend ex-dates: {len(dv)} ({dv.symbol.nunique()} names; special {int(dv.special.fillna(False).sum())})")
pc = d.groupby("symbol").c.shift(1); gp = (pd.to_datetime(d.date) - pd.to_datetime(d.groupby("symbol").date.shift(1))).dt.days
pc[gp > 5] = np.nan
d["tr"] = np.maximum(d.h, pc) - np.minimum(d.l, pc)
d["atrp"] = d.groupby("symbol").tr.transform(lambda x: x.rolling(14, min_periods=10).mean().shift(1)) / pc
d = d.merge(dv[["symbol", "date", "rate"]], on=["symbol", "date"], how="left")
d["gapA"] = (d.o / pc - 1).abs() / d.atrp
d["gapA_adj"] = ((d.o + d.rate.fillna(0)) / pc - 1).abs() / d.atrp
X = d[(d.date >= "2025-04-01") & d.gapA.notna() & (d.atrp > 0)].copy()
X["q"] = X.groupby("date").gapA.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False)) + 1
X["exdiv"] = X.rate.notna()
for q in (1, 3, 4, 5):
    x = X[X.q == q]; print(f"quintile {q}: name-days {len(x)}, ex-div {int(x.exdiv.sum())} ({x.exdiv.mean():.2%})")
ex = X[X.exdiv]
print(f"ex-div name-days by quintile: {ex.q.value_counts().sort_index().to_dict()}")
X["q_adj"] = X.groupby("date").gapA_adj.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False)) + 1
moved = ((X.q >= 4) != (X.q_adj >= 4)).sum()
print(f"name-days whose Q4-5 membership changes when the dividend is added back: {moved} ({moved / len(X):.2%} of all; "
      f"{moved / (X.q >= 4).sum():.2%} of Q4-5)")
print("Educational only - not financial advice.")
