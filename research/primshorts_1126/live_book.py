"""PRIMSHORTS-1126 live replay of the Friday lineup options on Primary's journal lots (run 1, LR8 cost-R as
footrace.live_trades) on the 18 sessions L3-gap-slope-fromopen-FD traded in Primary (10-21, 10-22, 10-30..11-25), all
Primary lots of those days kept (book-level halt / cap interplay). Open marks from Alpaca SIP 1-min closes (GET only).
The replay can only drop lots (latch / halt) or rescale them; lots live rules blocked are not added back.
Usage (repo root): python live_book.py LIVEDIR [lineup]  (lineup = only today's 4 Primary setups: L3, RW3, RW5, NM-ETF). Educational only - not financial advice."""
import os, sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(H + "/../..")); sys.path.insert(0, H)
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.priors import _bars, _client  # noqa: E402
from booksim import sim_day  # noqa: E402
L = Path(sys.argv[1]); TZ = "America/New_York"
L3 = "L3-gap-slope-fromopen-FD"
t = pd.read_parquet(L / "live.parquet")
t = t[(t.account == "primary") & t.r.notna()].copy()
days = sorted(t[t.strategy == L3].date.unique())
t = t[t.date.isin(days)].copy()
LINEUP = len(sys.argv) > 2 and sys.argv[2] == "lineup"
if LINEUP:
    t = t[t.strategy.isin([L3, "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
                           "NM-ETF-late-dip-di-long"])].copy()
t["side_n"] = np.where(t.side.astype(float) > 0, 1, -1)
t["risk"] = (t.entry - t.stop).abs(); t = t[t.risk > 0].copy()
t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
for c, s in (("em", "entry_time"), ("xm", "exit_time")):
    tt = pd.to_datetime(t[s].astype(str), utc=True, format="mixed").dt.tz_convert(TZ)
    t[c] = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
t["e_ns"] = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").astype("int64")
t["xm"] = np.maximum(t.xm, t.em).clip(upper=959)
t = t[(t.em >= 570) & (t.em < 960)].sort_values(["date", "e_ns"]).reset_index(drop=True)
print("lots", len(t), "days", len(days), "R", round(t.r.sum(), 1), t.groupby("strategy").r.agg(["size", "sum"]).round(1).to_dict("index"))
gp = L / "grid_primary.npz"
if not gp.exists():
    dc = _client(); G = {}
    for d, g in t.groupby("date"):
        a = datetime.fromisoformat(d) + timedelta(hours=13); b = a + timedelta(hours=9)
        raw = _bars(dc, sorted(set(g.symbol)), a, b, 1, "sip")
        for s, x in raw.groupby(level=0):
            x = rth(normalize(x.droplevel(0))); x.index = pd.DatetimeIndex(x.index).tz_convert(TZ)
            x = x[x.index.date.astype(str) == d]
            if not len(x):
                continue
            k = (x.index.hour * 60 + x.index.minute).to_numpy() - 570; ok = (k >= 0) & (k < 390)
            c = np.full(390, np.nan); c[k[ok]] = x.close.to_numpy()[ok]
            G[f"{s}|{d}"] = pd.Series(c).ffill().bfill().to_numpy()
        print(d, len(set(g.symbol)), flush=True)
    np.savez_compressed(gp, keys=np.array(list(G)), arr=np.stack(list(G.values())))
z = np.load(gp, allow_pickle=True); G = dict(zip(z["keys"], z["arr"]))

OPTS = {"a_keep": (1.0, False), "b_L3_out": (0.0, False), "c_L3_half": (0.5, False), "d_L3_latchopen": (1.0, True)}
rows = []
for LOALL in (False, True):
    for name, (wl3, lol3) in OPTS.items():
        for d, g in t.groupby("date"):
            g = g.reset_index(drop=True)
            if wl3 == 0.0:
                g = g[g.strategy != L3].reset_index(drop=True)
            S = sorted(g.strategy.unique()); N = len(S); si = g.strategy.map({s: k for k, s in enumerate(S)}).to_numpy()
            w = np.array([wl3 if s == L3 else 1.0 for s in S]); lo = np.array([LOALL or (lol3 and s == L3) for s in S])
            side, ent, risk, cost = g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float), g.cost.to_numpy(float)
            grids = []
            for q, s in enumerate(g.symbol):
                a = G.get(f"{s}|{d}")
                if a is not None:
                    a = a.copy(); g0 = a[min(389, max(0, g.em[q] - 570))]
                    if g0 > 0 and abs(g0 / ent[q] - 1) > 0.05:
                        a = a * (ent[q] / g0)
                grids.append(a)
            gm = np.stack([a if a is not None else np.full(390, np.nan) for a in grids]) if grids else np.zeros((0, 390))
            def markf(o, m):
                return side[o] * (gm[o, min(389, max(0, m - 570))] - ent[o]) / risk[o] - cost[o]
            R, taken, tot, tr = sim_day(si, pd.factorize(g.symbol)[0], side, ent, risk, cost, g.em.to_numpy(), g.xm.to_numpy(),
                                        g.r.to_numpy(float), markf, N, w, lo)
            rows.append(dict(lo=LOALL, opt=name, date=d, R=tot, trough=tr, lots=int(taken.sum()),
                             **{f"S|{s}": R[k] * w[k] for k, s in enumerate(S)}, **{f"N|{s}": int(taken[si == k].sum()) for k, s in enumerate(S)}))
out = pd.DataFrame(rows).fillna(0.0)
out.to_csv(H + ("/live_book_days_lineup.csv" if LINEUP else "/live_book_days.csv"), index=False)
act = t.groupby("date").r.sum()
print("actual journal R on these days", round(act.sum(), 1))
for (lo, opt), g in out.groupby(["lo", "opt"]):
    d = g.set_index("date").R
    print("LO" if lo else "--", opt, "tot", round(d.sum(), 1), "avg/day", round(d.mean(), 2), "worst5", round(d.nsmallest(5).sum(), 1),
          "red", int((d < 0).sum()), "L3", round(g.get(f"S|{L3}", pd.Series([0])).sum(), 1), "lots", int(g.lots.sum()))
