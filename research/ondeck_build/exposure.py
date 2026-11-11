"""ONDECK build 2026-11-11: exposure check for the proposed On Deck roster (and per-setup peaks for the testing areas).

Uses the trades written by ondeck.py (<scratch>/ondeck_trades.parquet, all accounts, run_id=1, closed) and every
account's `signals` table (skip reasons). Concurrency = lots open at the same time (entry_time < t < exit_time), merged
across accounts, so it shows demand as if all of a setup's live fills had been in one account. Fills only: signals
skipped elsewhere (borrow, gates, caps) are not in it, so the skip table is shown next to it.
Usage: python exposure.py <scratch> . Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
ROSTER = [l.split(",")[0] for l in open(HERE / "roster.csv").read().split("\n")[1:] if l]
T = pd.read_parquet(S / "ondeck_trades.parquet")
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed"); T["xt"] = pd.to_datetime(T.exit_time, utc=True, format="mixed")


def peak(g):
    ev = pd.concat([pd.DataFrame({"t": g.et, "d": 1}), pd.DataFrame({"t": g.xt, "d": -1})]).sort_values(["t", "d"])
    return int(ev.d.cumsum().max()) if len(ev) else 0


# per-setup peak concurrent lots per session (all scope setups)
ps = T.groupby(["strategy", "date"]).apply(peak).rename("peak").reset_index()
per = ps.groupby("strategy").peak.agg(["max", lambda x: x.quantile(0.9), "mean"]); per.columns = ["peak_max", "peak_p90", "peak_mean"]
per.to_csv(HERE / "setup_peaks.csv", float_format="%.2f")
R = T[T.strategy.isin(ROSTER)]
# roster book: concurrent lots per session, entries per session
book = R.groupby("date").apply(peak).rename("peak")
ent = R.groupby("date").size().rename("entries")
B = pd.concat([book, ent], axis=1)
print("ROSTER", len(ROSTER), "setups; sessions with a trade:", len(B))
print("roster peak concurrent lots per session: max %d, p90 %.0f, median %.0f; entries/session median %.0f, max %d" % (
    B.peak.max(), B.peak.quantile(.9), B.peak.median(), B.entries.median(), B.entries.max()))
print(B.tail(10).T.to_string())
print("\nper-setup peak concurrent lots (max / p90) for roster:")
print(per.loc[[s for s in ROSTER if s in per.index]].round(1).to_string())
# same-symbol overlap among roster setups (two different roster setups open on one symbol at once)
ov = []
for (d, sym), g in R.groupby(["date", "symbol"]):
    if g.strategy.nunique() < 2: continue
    g = g.sort_values("et").reset_index(drop=True)
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            a, b = g.loc[i], g.loc[j]
            if a.strategy != b.strategy and a.et < b.xt and b.et < a.xt:
                ov.append(dict(date=d, symbol=sym, a=a.strategy, b=b.strategy, same_side=bool(np.sign(a.side) == np.sign(b.side))))
OV = pd.DataFrame(ov)
if len(OV):
    OV["pair"] = OV.apply(lambda r: " + ".join(sorted([r.a, r.b])), axis=1)
    print("\nsame-symbol overlaps among roster setups (fills only):", len(OV), "| opposite side:", int((~OV.same_side).sum()))
    print(OV.groupby("pair").size().sort_values(ascending=False).head(12).to_string())
# skip reasons for roster setups, every account
sk = []
for a in ("p", "t1", "t2", "gy", "gen", "ex1", "ll"):
    c = sqlite3.connect(S / a / "journal.db")
    q = pd.read_sql("select strategy, status, reason from signals where run_id=1", c)
    q = q[q.strategy.isin(ROSTER)]; q["acct"] = a; sk.append(q)
SK = pd.concat(sk)
SK["why"] = SK.reason.fillna("").str.replace(r"[\d\.\-:,()$%]+", "", regex=True).str.strip().str[:40]
tab = SK.groupby("why").size().sort_values(ascending=False)
print("\nroster signals, all accounts:", len(SK), "| by reason (top 15):")
print((tab / len(SK)).round(3).to_string())
by = SK.assign(ok=SK.why.eq("ok"), etb=SK.why.str.contains("shortable"), split=SK.why.str.contains("splittape"),
               cost=SK.why.str.contains("cost filter"), spread=SK.why.str.contains("spread"),
               latch=SK.why.str.contains("setup daily loss"),
               slots_caps=SK.why.str.contains("slots|setup cap|max positions|positions per", regex=True),
               crowd=SK.why.str.contains("twin held|already in symbol|opposite side|lot cap", regex=True)
               ).groupby("strategy")[["ok", "etb", "split", "cost", "spread", "latch", "slots_caps", "crowd"]].mean()
by["signals"] = SK.groupby("strategy").size()
print("\nshare of each roster setup's signals: entered / not ETB / split-tape gate / cost filter / spread / -2R latch / slots-caps / crowding (twin, same symbol, opposite side, lot cap)")
print(by.round(3).to_string())
json.dump(dict(roster=ROSTER, peak_max=int(B.peak.max()), peak_p90=float(B.peak.quantile(.9)), entries_median=float(B.entries.median()),
               overlaps=len(OV), overlaps_opposite=int((~OV.same_side).sum()) if len(OV) else 0), open(HERE / "exposure_out.json", "w"), indent=1)
