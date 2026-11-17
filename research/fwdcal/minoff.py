"""FWDCAL exact-minute diagnostic (Builder 11-17; engine diagnostic, no strategy score): for matched replay/live pairs,
seconds of replay entry_time minus live entry_time, by account, plus live seconds-past-the-minute. Explains why exact-minute
match (0.34) is far below the 5-min match (0.95).   python minoff.py --dates A..B --variant qm0
Educational only - not financial advice."""
import argparse, json, sys
from pathlib import Path
import numpy as np, pandas as pd
_a = sys.argv; sys.argv = [sys.argv[0]]
sys.path.insert(0, str(Path(__file__).resolve().parent)); import mirror as M  # noqa: E402
sys.argv = _a
ap = argparse.ArgumentParser(); ap.add_argument("--dates"); ap.add_argument("--variant", default="qm0"); a = ap.parse_args()
d0, d1 = a.dates.split(".."); days = [str(d.date()) for d in pd.bdate_range(d0, d1)]
fs = [f for f in sorted((M.OUT / "books" / a.variant).glob("*/*.json")) if f.parent.name in days]
reps = [r for r in (json.loads(f.read_text()) for f in fs) if not r.get("skipped")]
X = pd.DataFrame([{"date": r["day"], "acct": r["acc"], "setup": t["strategy"], "symbol": t["symbol"], "side": int(t["side"]),
                   "entry_time": t["entry_time"]} for r in reps for t in r["trades"]])
X["et"] = pd.to_datetime(X.entry_time, utc=True, format="mixed")
L = M.live_trades_x(); keys = {(r["day"], r["acc"]) for r in reps}
L = L[[(d, c) in keys for d, c in zip(L.date, L.acct)]].copy()
rows = []
for d, c in sorted(keys):
    x = X[(X.date == d) & (X.acct == c)]; l = L[(L.date == d) & (L.acct == c)]
    for i, j in M.REP.match(x, l, 5.0):
        rows.append(dict(acct=c, setup=L.loc[j, "setup"], dsec=(X.loc[i, "et"] - L.loc[j, "et"]).total_seconds(),
                         lsec=L.loc[j, "et"].second + L.loc[j, "et"].microsecond / 1e6, xsec=X.loc[i, "et"].second,
                         exact=X.loc[i, "et"].floor("min") == L.loc[j, "et"].floor("min")))
m = pd.DataFrame(rows)
m["dmin"] = np.round(m.dsec / 60).astype(int)
print(f"matched pairs {len(m)}; exact-minute {m.exact.mean():.3f}")
print("replay - live entry, whole minutes (rounded):"); print(m.dmin.value_counts().sort_index().to_string())
print("by account: share at -1 / 0 / +1 min, median seconds diff, live seconds-past-minute median, replay seconds median")
g = m.groupby("acct").agg(n=("dsec", "size"), m1=("dmin", lambda s: (s == -1).mean()), z=("dmin", lambda s: (s == 0).mean()),
                          p1=("dmin", lambda s: (s == 1).mean()), med_dsec=("dsec", "median"), live_sec=("lsec", "median"),
                          rep_sec=("xsec", "median"), exact=("exact", "mean"))
print(g.round(3).to_string())
print("live seconds-past-minute deciles:", np.round(m.lsec.quantile(np.linspace(0, 1, 11)).values, 1))

# --- live signal minute (submitted signal <= 10 min before the logged entry) ---
S = M.live_signals(sorted({c for _, c in keys}), days); S = S[S.status == "submitted"].copy()
S["side"] = S.side.astype(float).astype(int); L["side"] = L.side.astype(float).astype(int)
k = ["date", "acct", "setup", "symbol", "side"]
J = L.reset_index().merge(S[k + ["et"]].rename(columns={"et": "st"}), on=k)
J = J[(J.st <= J.et + pd.Timedelta(seconds=5)) & (J.st >= J.et - pd.Timedelta(minutes=10))].sort_values("st").groupby("index").tail(1).set_index("index")
L.loc[J.index, "st"] = J.st
print(f"live trades paired to a submitted signal: {len(J)} of {len(L)}; median signal->entry {(J.et - J.st).dt.total_seconds().median():.1f}s")
rr = []
for d, c in sorted(keys):
    x = X[(X.date == d) & (X.acct == c)]; l = L[(L.date == d) & (L.acct == c)]
    for i, j in M.REP.match(x, l, 5.0):
        rr.append(dict(acct=c, ex_fill=X.loc[i, "et"].floor("min") == L.loc[j, "et"].floor("min"),
                       ex_sig=pd.notna(L.loc[j, "st"]) and X.loc[i, "et"].floor("min") == L.loc[j, "st"].floor("min")))
q = pd.DataFrame(rr); n = L.groupby("acct").size()
g = q.groupby("acct")[["ex_fill", "ex_sig"]].sum().div(n, axis=0); g.loc["ALL"] = [q.ex_fill.sum() / len(L), q.ex_sig.sum() / len(L)]
print("exact-minute match per live trade: vs live ENTRY(fill) minute | vs live SIGNAL minute"); print(g.round(3).to_string())
print("Diagnostic only (Session replay vs Live, matched pairs). Educational only - not financial advice.")
