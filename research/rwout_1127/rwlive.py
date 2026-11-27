"""RWOUT-1127 live replay (descriptive, PREREG.md): primshorts_1126 live_book.py lineup basis - Primary journal lots
(LR8 cost-R) of the P4 setups on the 18 sessions L3 traded in Primary; each removal config, LO off/on, vs keep; plus
200 size-matched random removals (same number of keep-run short lots, pooled over the days). Open marks from the
stored primshorts SIP grid (grid_primary.npz; no new fetch). The replay only drops lots.
Usage (cwd repo): python research/rwout_1127/rwlive.py LIVEDIR OUTDIR. Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/primshorts_1126")
from booksim import sim_day  # noqa: E402

L, OUT = Path(sys.argv[1]), Path(sys.argv[2])
TZ = "America/New_York"
S4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
      "NM-ETF-late-dip-di-long"]
CFG = {"keep": [], "L3-out": [0], "RW3-out": [1], "RW5-out": [2], "L3+RW3-out": [0, 1], "L3+RW5-out": [0, 2],
       "RW3+RW5-out": [1, 2], "all-three-out": [0, 1, 2]}
t = pd.read_parquet(L / "live.parquet")
t = t[(t.account == "primary") & t.r.notna()].copy()
days = sorted(t[t.strategy == S4[0]].date.unique())
t = t[t.date.isin(days) & t.strategy.isin(S4)].copy()
t["side_n"] = np.where(t.side.astype(float) > 0, 1, -1)
t["risk"] = (t.entry - t.stop).abs(); t = t[t.risk > 0].copy()
t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
for c, s in (("em", "entry_time"), ("xm", "exit_time")):
    tt = pd.to_datetime(t[s].astype(str), utc=True, format="mixed").dt.tz_convert(TZ)
    t[c] = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
t["e_ns"] = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").astype("int64")
t["xm"] = np.maximum(t.xm, t.em).clip(upper=959)
t = t[(t.em >= 570) & (t.em < 960)].sort_values(["date", "e_ns"]).reset_index(drop=True)
t["si"] = t.strategy.map({s: i for i, s in enumerate(S4)})
z = np.load(L / "grid_primary.npz", allow_pickle=True); G = dict(zip(z["keys"], z["arr"]))
DAYG = {}
for d, g in t.groupby("date"):
    g = g.reset_index(drop=True)
    side, ent, risk, cost = g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float), g.cost.to_numpy(float)
    grids = []
    for q, s in enumerate(g.symbol):
        a = G.get(f"{s}|{d}")
        if a is not None:
            a = a.copy(); g0 = a[min(389, max(0, g.em[q] - 570))]
            if g0 > 0 and abs(g0 / ent[q] - 1) > 0.05:
                a = a * (ent[q] / g0)
        grids.append(a if a is not None else np.full(390, np.nan))
    DAYG[d] = (g, np.stack(grids), pd.factorize(g.symbol)[0])


def run_day(d, keep, lo):
    g, gm, sym = DAYG[d]
    ix = np.flatnonzero(keep)
    if not len(ix):
        return np.zeros(4), np.zeros(len(g), bool)
    side, ent, risk, cost = (g[c].to_numpy(float)[ix] for c in ("side_n", "entry", "risk", "cost"))
    gmi = gm[ix]

    def markf(o, m):
        return side[o] * (gmi[o, min(389, max(0, m - 570))] - ent[o]) / risk[o] - cost[o]
    R, taken, _, _ = sim_day(g.si.to_numpy()[ix], sym[ix], side, ent, risk, cost, g.em.to_numpy()[ix], g.xm.to_numpy()[ix],
                             g.r.to_numpy(float)[ix], markf, 4, np.ones(4), np.full(4, lo))
    tk = np.zeros(len(g), bool); tk[ix[taken]] = True
    return R, tk


def stats(x, a):
    d = x - a; n = len(d); sd = d.std(ddof=1)
    return dict(avg=x.mean(), dR=d.mean(), t=d.mean() / (sd / np.sqrt(n)) if sd > 0 else 0.0,
                worst5=np.sort(x)[:5].sum(), red=int((x < 0).sum()), dR_wo_best=np.delete(d, np.argmax(d)).mean())


res = {"days": len(days), "lots": int(len(t)), "R_journal": round(float(t.r.sum()), 1),
       "by_setup": t.groupby("strategy").r.agg(["size", "sum"]).round(1).to_dict("index")}
rows = []
for lo in (False, True):
    base, tk0 = {}, {}
    for d in days:
        base[d], tk0[d] = run_day(d, np.ones(len(DAYG[d][0]), bool), lo)
    a = np.array([base[d].sum() for d in days])
    pool = [(d, k) for d in days for k in np.flatnonzero(tk0[d] & (DAYG[d][0].si.to_numpy() <= 2))]
    for cfg, rm in CFG.items():
        rr = {d: run_day(d, ~DAYG[d][0].si.isin(rm).to_numpy(), lo) for d in days}
        x = np.array([rr[d][0].sum() for d in days])
        n = sum(int((tk0[d] & DAYG[d][0].si.isin(rm).to_numpy()).sum()) for d in days)
        row = dict(lo=lo, cfg=cfg, n_removed=n, **stats(x, a),
                   **{f"dR|{S4[s][:3]}": float((np.array([rr[d][0][s] - base[d][s] for d in days])).sum()) for s in range(4)})
        if rm:
            g = np.random.default_rng(1127); rd = []
            for _ in range(200):
                pick = g.choice(len(pool), min(n, len(pool)), replace=False)
                drop = {}
                for i in pick:
                    drop.setdefault(pool[i][0], []).append(pool[i][1])
                tot = 0.0
                for d in days:
                    kp = np.ones(len(DAYG[d][0]), bool); kp[drop.get(d, [])] = False
                    tot += run_day(d, kp, lo)[0].sum() if d in drop else base[d].sum()
                rd.append(tot / len(days) - a.mean())
            rd = np.array(rd)
            row.update(rnd_mean=float(rd.mean()), rnd_p95=float(np.percentile(rd, 95)), pctile=float((rd < row["dR"]).mean() * 100))
        rows.append(row)
        print({k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in row.items()}, flush=True)
pd.DataFrame(rows).to_csv(OUT / "live_replay.csv", index=False)
res["rows"] = rows
json.dump(res, open(OUT / "live_replay.json", "w"), indent=1, default=float)
