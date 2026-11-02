"""saturday1031 A: earlier day-trade flatten (15:40 / 15:45 / 15:50 vs 15:55) on the two-year lab trade lists
(backlog nightly-1027-flatten-1545). PLAN.md section A was written before this ran.
Every lab trade (research/history2y/data/lab_trades.parquet; 21 live / probation lab setups, base windows) gets its
entry price and ATR_d from the history2y 5-min frame row (bar close = entry), R = 0.25 x ATR_d, and is walked on the
1-min SIP cache (data/cache_hist/1Min) from the entry bar end: stop first inside a bar; target / stop multiples per
setup = the GEOMK geometry whose simulated 15:55 result best matches the lab r (reported). A trade untouched at the
flatten minute F is closed at the 1-min close ending at F; otherwise unchanged. Costs: entry 1c + 1 bps x ToD multiplier,
target exit free, stop 1c + 1 bps + 2c, flatten 1c + 1 bps.
Locked block 2024-11-01..2025-02-28: not in the lab file, dropped from every 1-min read (asserted). Old holdouts
2026-04..06 and >= 2026-09-16 dropped before scoring. Writes flat2y_out.txt and a small per-trade parquet in scratch.
Usage: python flat2y.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
import os
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
from lib import load_month  # noqa
from mcf.research import gates as G  # noqa
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
L = pd.read_parquet(ROOT / "research/history2y/data/lab_trades.parquet")
L["date"] = pd.to_datetime(L.date).dt.date
assert not ((L.date >= LK0) & (L.date <= LK1)).any()
ds = L.date.astype(str)
L = L[~(ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16"))].reset_index(drop=True)
SHORT = ("short", "RW", "MF", "NS2", "NS3", "NS4")
L["side"] = np.where(L.setup.str.contains("|".join(SHORT)) & ~L.setup.str.contains("long"), -1, 1)
L["month"] = pd.to_datetime(L.date).dt.strftime("%Y-%m")
parts = []
for mo, g in L.groupby("month"):
    f = load_month(mo, columns=["symbol", "date", "tod", "close", "atr_d"])
    f["date"] = pd.to_datetime(f.date).dt.date
    parts.append(g.merge(f.drop_duplicates(["symbol", "date", "tod"]), on=["symbol", "date", "tod"], how="left"))
L = pd.concat(parts, ignore_index=True)
L = L[np.isfinite(L.close) & (L.atr_d > 0)].reset_index(drop=True)
GEO = list(G.GEOMK.items())
FL = (1540, 1545, 1550, 1555)
n = len(L)
mult = G.tod_cost_mult(L.tod.to_numpy())
CACHE = ROOT / "data/cache_hist/1Min"


def walk(args):
    """1-min walk for one symbol's trades: {(geometry, F): r} per trade index."""
    sy, g = args
    p = CACHE / f"{sy}.parquet"
    o = {}
    if not p.exists():
        return o
    b = pd.read_parquet(p, columns=["high", "low", "close"])
    dd = b.index.date
    b = b[~((dd >= LK0) & (dd <= LK1))]
    dd = b.index.date
    assert not ((dd >= LK0) & (dd <= LK1)).any()
    st = (b.index.hour * 100 + b.index.minute).to_numpy()           # bar start HHMM
    H, Lo, C = (b[c].to_numpy(float) for c in ("high", "low", "close"))
    di = pd.Series(np.arange(len(b))).groupby(dd).indices
    for j, d, tod, e, atr, sd, mu in zip(g.index, g.date, g.tod, g.close, g.atr_d, g.side, g.mult):
        ix = di.get(d)
        if ix is None:
            continue
        t = st[ix]
        w = ix[(t >= tod) & (t <= 1554)]
        if not len(w):
            continue
        R = 0.25 * atr
        ec = (G.SLIP_PS + e * G.SLIP_BPS) * mu
        for gk, (up, dn) in GEO:
            stop, tgt = e - sd * dn * R, e + sd * up * R
            adv = Lo[w] if sd == 1 else H[w]
            fav = H[w] if sd == 1 else Lo[w]
            hs = sd * (adv - stop) <= 0
            ht = sd * (fav - tgt) >= 0
            a = np.flatnonzero(hs | ht)
            first = a[0] if len(a) else None
            for F in FL:
                if first is not None and st[w[first]] < F:
                    if hs[first]:
                        x = stop; xc = G.SLIP_PS + x * G.SLIP_BPS + G.STOP_EXTRA
                    else:
                        x = tgt; xc = 0.0
                else:
                    q = w[st[w] <= F - 1]
                    if not len(q):
                        continue
                    x = C[q[-1]]; xc = G.SLIP_PS + x * G.SLIP_BPS
                o[(j, gk, F)] = sd * (x - e) / R - (ec + xc) / R
    return o


RC = S / "flat2y_walk.parquet"
if RC.exists():
    W = pd.read_parquet(RC)
else:
    from multiprocessing import Pool
    L["mult"] = mult
    jobs = [(sy, g[["date", "tod", "close", "atr_d", "side", "mult"]]) for sy, g in L.groupby("symbol")]
    recs = []
    with Pool(4) as pool:
        for k, o in enumerate(pool.imap_unordered(walk, jobs, chunksize=4)):
            recs.extend((j, gk, F, v) for (j, gk, F), v in o.items())
            if k % 200 == 0:
                print(k, flush=True)
    W = pd.DataFrame(recs, columns=["j", "geo", "F", "r"])
    W.to_parquet(RC)
res = {}
for (gk, F), w in W.groupby(["geo", "F"]):
    a = np.full(n, np.nan); a[w.j.to_numpy()] = w.r.to_numpy(); res[(gk, int(F))] = a
for gk, _ in GEO:
    for F in FL:
        res.setdefault((gk, F), np.full(n, np.nan))
# geometry per setup: best match of the simulated 15:55 result to the lab r
out = []; P = lambda *x: out.append(" ".join(str(y) for y in x))
geo = {}
for s_, g in L.groupby("setup"):
    best = None
    for gk, _ in GEO:
        v = res[(gk, 1555)][g.index]; ok = np.isfinite(v)
        if ok.sum() < 30:
            continue
        mae = np.nanmean(np.abs(v[ok] - g.r.to_numpy()[ok]))
        cr = np.corrcoef(v[ok], g.r.to_numpy()[ok])[0, 1]
        if best is None or mae < best[1]:
            best = (gk, mae, cr, ok.mean())
    geo[s_] = best
    P(f"geometry {s_:42s} {best[0]:7s} mean|sim-lab| {best[1]:.3f}R corr {best[2]:.3f} covered {best[3]:.3f}")
for F in FL:
    L[f"r{F}"] = np.nan
    for s_, (gk, *_r) in geo.items():
        m = (L.setup == s_).to_numpy()
        L.loc[m, f"r{F}"] = res[(gk, F)][m]
L = L.dropna(subset=[f"r{F}" for F in FL]).reset_index(drop=True)
L["split"] = np.where(L.date.astype(str) <= "2025-08-31", "train", "valid")
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D.date).dt.date
REG = G.session_regimes(D[["date", "open", "close"]])
L["regime"] = L.date.map(REG["regime"])
P(f"\ntrades {len(L)} (holdouts dropped), sessions {L.date.nunique()}; sim 15:55 vs lab r: mean {L.r1555.mean():+.4f} vs {L.r.mean():+.4f}, "
  f"corr {np.corrcoef(L.r1555, L.r)[0,1]:.3f}")
def tday(dates, x):
    g = pd.Series(x).groupby(np.asarray(dates)).sum()
    alld = g.reindex(L.date.unique(), fill_value=0.0) if False else g
    return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if g.std() > 0 else np.nan
bar = max(1.5, np.sqrt(2 * np.log(5)))
P(f"bar (N 5): t >= {bar:.2f}\n")
top = L.r1555 >= L.r1555.quantile(0.9)
rows = []
for name, F, side in (("F1540 all", 1540, 0), ("F1545 all", 1545, 0), ("F1550 all", 1550, 0), ("F1545 longs", 1545, 1), ("F1545 shorts", 1545, -1)):
    m = np.ones(len(L), bool) if side == 0 else (L.side == side).to_numpy()
    x = L[m]; dlt = (x[f"r{F}"] - x.r1555).to_numpy()
    aff = dlt != 0
    # per-day delta over ALL sessions (zero on days without affected trades)
    dd = pd.Series(dlt).groupby(x.date.to_numpy()).sum().reindex(L.date.unique(), fill_value=0.0)
    t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
    r = dict(cfg=name, n=len(x), affected=int(aff.sum()), d_per_trade=dlt.mean(), d_per_affected=dlt[aff].mean() if aff.any() else np.nan,
             sum_d=dlt.sum(), t_day=t)
    for sp in ("train", "valid"):
        mm = (x.split == sp).to_numpy(); r[f"d_{sp}"] = dlt[mm].mean()
    for rg in ("up", "flat", "down"):
        mm = (x.regime == rg).to_numpy(); r[f"d_{rg}"] = dlt[mm].mean() if mm.any() else np.nan
    tp = top[m].to_numpy()
    r["top10_R_kept"] = x[f"r{F}"].to_numpy()[tp].sum() / x.r1555.to_numpy()[tp].sum()
    dsum = pd.Series(dlt).groupby(x.date.to_numpy()).sum()
    r["best_day_share"] = dsum.max() / dsum.sum() if dsum.sum() > 0 else np.nan
    r["wo_best_day"] = (dsum.sum() - dsum.max()) / len(x)
    mo = pd.Series(dlt).groupby(pd.to_datetime(x.date).dt.strftime("%Y-%m").to_numpy()).sum()
    r["months_pos"] = (mo > 0).mean()
    r["pass"] = bool(r["d_train"] > 0 and r["d_valid"] > 0 and r["d_up"] > 0 and r["d_down"] > 0 and t >= bar and r["top10_R_kept"] >= 0.9)
    rows.append(r)
R = pd.DataFrame(rows)
P(R.round(4).to_string(index=False))
P("\nby setup (F1545, delta per trade, affected):")
x = L.assign(d=L.r1545 - L.r1555)
P(x.groupby("setup").agg(n=("d", "size"), aff=("d", lambda v: int((v != 0).sum())), d=("d", "mean"), sum_d=("d", "sum")).round(4).to_string())
R.to_csv(OUT / "flat2y.csv", index=False)
L[["setup", "symbol", "date", "tod", "side", "r", "r1540", "r1545", "r1550", "r1555"]].to_parquet(S / "flat2y_trades.parquet")
open(OUT / "flat2y_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
