"""LATCH-OPEN on the Monday roster, live window 10-23..11-27 (25 Primary sessions), descriptive and in-sample.
Primary journal (run 1, closed lots, LR8 cost-R as roster_options.py) for roster A = RW3, RW5, NM-ETF and roster B = A + L3.
Engine: research/primshorts_1126/booksim.py (Primary book rules; -2R latch closed-only vs closed + open marks).
Open marks: Alpaca SIP 1-min closes (GET only, cached in LIVEDIR/grid.npz). The replay can only drop lots that were taken
live; lots live rules blocked are not added back. Writes LIVEDIR/live_days.csv and LIVEDIR/live_taken.parquet.
cwd = repo checkout. Usage: python live_replay.py LIVEDIR  (LIVEDIR holds journal.db, a read-only copy of
origin/mcf-data:journal.db). Educational only - not financial advice."""
import os, sqlite3, sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, str(Path.cwd() / "research/primshorts_1126"))
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from booksim import sim_day  # noqa: E402
L = Path(sys.argv[1]); TZ = "America/New_York"
L3, NM = "L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long"
RW3, RW5 = "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"
ROSTERS = {"A": [RW3, RW5, NM], "B": [L3, RW3, RW5, NM]}
con = sqlite3.connect(L / "journal.db")
x = pd.read_sql("SELECT * FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close()
x["date"] = x.date.astype(str).str[:10]
x = x[(x.date >= "2026-10-23") & (x.date <= "2026-11-27")].copy()
DAYS = sorted(x.date.unique())
x["r"] = cost_r_lr8(x, load_config()).astype(float)
t = x[x.strategy.isin(ROSTERS["B"]) & x.r.notna()].copy()
t["side_n"] = np.where(t.side.astype(float) > 0, 1, -1)
t["risk"] = (t.entry - t.stop).abs(); t = t[t.risk > 0].copy()
t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
for c, s in (("em", "entry_time"), ("xm", "exit_time")):
    tt = pd.to_datetime(t[s].astype(str), utc=True, format="mixed").dt.tz_convert(TZ)
    t[c] = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
t["e_ns"] = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").astype("int64")
t["xm"] = np.maximum(t.xm, t.em).clip(upper=959)
t = t[(t.em >= 570) & (t.em < 960)].sort_values(["date", "e_ns"]).reset_index(drop=True)
t["lid"] = np.arange(len(t))
print("sessions", len(DAYS), "roster-B lots", len(t), "R", round(t.r.sum(), 1),
      t.groupby("strategy").r.agg(["size", "sum"]).round(1).to_dict("index"), flush=True)
gp = L / "grid.npz"
if not gp.exists():
    from mcf.data.bars import normalize, rth
    from mcf.data.priors import _bars, _client
    dc = _client(); G = {}
    for d, g in t.groupby("date"):
        a = datetime.fromisoformat(d) + timedelta(hours=13); b = a + timedelta(hours=9)
        raw = _bars(dc, sorted(set(g.symbol)), a, b, 1, "sip")
        for s, xx in raw.groupby(level=0):
            xx = rth(normalize(xx.droplevel(0))); xx.index = pd.DatetimeIndex(xx.index).tz_convert(TZ)
            xx = xx[xx.index.date.astype(str) == d]
            if not len(xx):
                continue
            k = (xx.index.hour * 60 + xx.index.minute).to_numpy() - 570; ok = (k >= 0) & (k < 390)
            c = np.full(390, np.nan); c[k[ok]] = xx.close.to_numpy()[ok]
            G[f"{s}|{d}"] = pd.Series(c).ffill().bfill().to_numpy()
        print(d, len(set(g.symbol)), flush=True)
    np.savez_compressed(gp, keys=np.array(list(G)), arr=np.stack(list(G.values())))
z = np.load(gp, allow_pickle=True); G = dict(zip(z["keys"], z["arr"]))
rows, tk = [], []
for ros, keep in ROSTERS.items():
    for lo_on in (False, True):
        for d in DAYS:
            g = t[(t.date == d) & t.strategy.isin(keep)].reset_index(drop=True)
            if not len(g):
                rows.append(dict(roster=ros, lo=lo_on, date=d, R=0.0, lots=0)); continue
            S = sorted(g.strategy.unique()); N = len(S); si = g.strategy.map({s: k for k, s in enumerate(S)}).to_numpy()
            side, ent, risk, cost = g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float), g.cost.to_numpy(float)
            gm = np.full((len(g), 390), np.nan)
            for q, s in enumerate(g.symbol):
                a = G.get(f"{s}|{d}")
                if a is not None:
                    a = a.copy(); g0 = a[min(389, max(0, g.em[q] - 570))]
                    if g0 > 0 and abs(g0 / ent[q] - 1) > 0.05:
                        a = a * (ent[q] / g0)
                    gm[q] = a

            def markf(o, m):
                return side[o] * (gm[o, min(389, max(0, m - 570))] - ent[o]) / risk[o] - cost[o]
            R, taken, tot, tr = sim_day(si, pd.factorize(g.symbol)[0], side, ent, risk, cost, g.em.to_numpy(), g.xm.to_numpy(),
                                        g.r.to_numpy(float), markf, N, np.ones(N), np.full(N, lo_on))
            rows.append(dict(roster=ros, lo=lo_on, date=d, R=tot, lots=int(taken.sum())))
            tk.append(pd.DataFrame(dict(roster=ros, lo=lo_on, date=d, lid=g.lid, setup=g.strategy, r=g.r, taken=taken)))
out = pd.DataFrame(rows); out.to_csv(L / "live_days.csv", index=False)
pd.concat(tk).to_parquet(L / "live_taken.parquet", index=False)
for (ros, lo), g in out.groupby(["roster", "lo"]):
    print(ros, "LO" if lo else "--", "R", round(g.R.sum(), 1), "lots", g.lots.sum())
print("Educational only - not financial advice.")
