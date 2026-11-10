"""BURST2 simulator (PLAN.md, 13 configs). Loaders are BURST1's (burst1/sim.py) with live data through 2026-11-06.
2-year:  python sim2.py 2y <scratch>    (needs <scratch>/enr from burst1/enrich.py)
live:    python sim2.py live <scratch>  (needs <scratch>/live_trades.parquet, live_bars5.parquet, live_idx1.parquet from live.py)
Writes <scratch>/keep2_<mode>.parquet + trades2_<mode>.parquet. Educational only - not financial advice."""
import os, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "burst1"))
from rules import pace, latch  # noqa: E402
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "burst2 never reads the locked block"
mode, S = sys.argv[1], Path(sys.argv[2]); TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]


def load_2y():
    T, MK = [], []
    for p in sorted((S / "enr").glob("*.parquet")):
        t = pd.read_parquet(p); mk = np.load(str(p).replace(".parquet", "_mk.npy"))
        keep = (t.date <= "2026-10-05").values
        T.append(t[keep]); MK.append(mk[keep])
    T = pd.concat(T, ignore_index=True)
    MK = pd.DataFrame(np.vstack(MK).astype(np.float32)).ffill(axis=1).fillna(0).to_numpy(np.float32)
    acc = pd.read_csv("/home/user/MCF/research/bdi/1104/setups.csv").set_index("setup").account
    T["account"] = T.setup.map(acc).fillna("lab")
    T["m"] = (T.tod // 100) * 60 + T.tod % 100; T["xm"] = (T.xtod // 100) * 60 + T.xtod % 100
    T["dollar_risk"] = np.minimum(250.0, 3980.0 * T.stop_pct.fillna(0.01))
    sl = lambda t: min(73, max(0, (int(t) - 590) // 5))
    I = []
    for s in ("SPY", "QQQ"):
        b = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/%s.parquet" % s)
        b["date"] = b.index.strftime("%Y-%m-%d"); b = b[~((b.date >= LOCK[0]) & (b.date <= LOCK[1]))]
        b["mm"] = b.index.hour * 60 + b.index.minute; b = b[(b.mm >= 570) & (b.mm < 960)]
        I.append(pd.DataFrame(dict(date=b.date, symbol=s, mm=b.mm, o=b.open, c=b.close)))
    return T, (lambda j, t: float(MK[j, sl(t)])), pd.concat(I, ignore_index=True)


def load_live():
    T = pd.read_parquet(S / "live_trades.parquet").rename(columns={"strategy": "setup", "R": "r"})
    T = T.sort_values(["account", "setup", "date", "ent_ts", "id"]).reset_index(drop=True)
    B = pd.read_parquet(S / "live_bars5.parquet")
    B["cm"] = B.t.dt.hour * 60 + B.t.dt.minute + 5; B["sm"] = B.cm - 5
    G = {k: (g.sm.to_numpy(), g.cm.to_numpy(), g.c.to_numpy()) for k, g in B.groupby(["date", "symbol"])}
    T["m"] = T.ent; T["xm"] = T.ext; T["dollar_risk"] = T.risk.where(T.run_id == 1, np.nan)
    e, sd, sd_ = T.entry.to_numpy(float), T.side.to_numpy(int), (T.entry - T.stop).abs().to_numpy(float)
    keys = list(zip(T.date, T.symbol)); m0 = T.m.to_numpy()

    def mk(j, t):
        g = G.get(keys[j])
        if g is None: return 0.0
        sm, cm, c = g; ok = (sm >= m0[j]) & (cm <= t)
        return float(sd[j] * (c[ok][-1] - e[j]) / sd_[j]) if ok.any() else 0.0
    I = pd.read_parquet(S / "live_idx1.parquet"); I["mm"] = I.t.dt.hour * 60 + I.t.dt.minute
    I = I[(I.mm >= 570) & (I.mm < 960)]
    return T, mk, I[["date", "symbol", "mm", "o", "c"]]


T, mk, I = load_2y() if mode == "2y" else load_live()
T["fam"] = T.setup.map(fam)
# index features at entry minute m: last 1-min bar with start < m
IX = {}
for (d, s), g in I.sort_values("mm").groupby(["date", "symbol"]):
    mm, c = g.mm.to_numpy(), g.c.to_numpy(float); o = g.o.iloc[0] if g.mm.iloc[0] == 570 else np.nan
    IX[(d, s)] = (mm, c, o)


def feat(d, s, m, kind):
    v = IX.get((d, s))
    if v is None: return np.nan
    mm, c, o = v; i = np.searchsorted(mm, m) - 1
    if i < 0: return np.nan
    if kind == "fo": return c[i] / o - 1
    j = np.searchsorted(mm, m - 30) - 1
    return c[i] / (c[j] if j >= 0 else o) - 1


dates, ms = T.date.to_numpy(), T.m.to_numpy()
T["spy_fo"] = [feat(d, "SPY", m, "fo") for d, m in zip(dates, ms)]
T["qqq_r30"] = [feat(d, "QQQ", m, "r30") for d, m in zip(dates, ms)]
m_, xm_, r_, side_ = T.m.to_numpy(), T.xm.to_numpy(), T.r.to_numpy(float), T.side.to_numpy(int)
fo_, q30_ = T.spy_fo.to_numpy(float), T.qqq_r30.to_numpy(float)


def burst_cond(ix, B, cond, W=15):
    keep = np.ones(len(ix), bool)
    for k in range(len(ix)):
        prev = keep[:k] & (m_[ix[:k]] > m_[ix[k]] - W) & (side_[ix[:k]] == side_[ix[k]])
        if prev.sum() >= B and cond(ix[k]):
            keep[k] = False
    return keep


COND = {"C_compass_2_0": (2, lambda j: side_[j] == -1 and fo_[j] > 0),
        "C_compass_2_25": (2, lambda j: side_[j] == -1 and fo_[j] > 0.0025),
        "C_compass_3_0": (3, lambda j: side_[j] == -1 and fo_[j] > 0),
        "C_compass_3_25": (3, lambda j: side_[j] == -1 and fo_[j] > 0.0025),
        "Csym_compass_2_0": (2, lambda j: (side_[j] == -1 and fo_[j] > 0) or (side_[j] == 1 and fo_[j] < 0)),
        "D_flush_2_40": (2, lambda j: side_[j] == -1 and q30_[j] <= -0.004),
        "D_flush_2_70": (2, lambda j: side_[j] == -1 and q30_[j] <= -0.007)}
base_seq = np.ones(len(T), bool) if mode == "2y" else (T.run_id == 1).to_numpy()
cols = {c: np.zeros(len(T), bool) for c in list(COND) + [f"A_openlatch_{L}" for L in (-2, -3, -4)] + [f"B_family_{N}" for N in (4, 6, 8)]}
cols["base"] = base_seq.copy(); cols["latch_realised_-2"] = np.zeros(len(T), bool); cols["latchoff"] = np.ones(len(T), bool)
for (su, d), ix in T.groupby(["setup", "date"], sort=False).indices.items():
    ix = np.asarray(ix); ix = ix[np.lexsort((ix, m_[ix]))]
    for L in (-2, -3, -4):
        cols[f"A_openlatch_{L}"][ix] = latch(m_[ix], xm_[ix], r_[ix], L, mk=lambda jj, t, ix=ix: mk(ix[jj], t))
    cols["latch_realised_-2"][ix] = latch(m_[ix], xm_[ix], r_[ix], -2)
    sub = ix[base_seq[ix]]
    for c, (B, cond) in COND.items():
        cols[c][sub] = burst_cond(sub, B, cond) if len(sub) > B else True
bidx = np.flatnonzero(base_seq)
for k, ix in T[base_seq].groupby(["account", "fam", "date", "side"], sort=False).indices.items():
    ix = bidx[np.asarray(ix)]; ix = ix[np.lexsort((ix, m_[ix]))]
    for N in (4, 6, 8):
        cols[f"B_family_{N}"][ix] = pace(m_[ix], N)
K = pd.DataFrame(cols); K.to_parquet(S / f"keep2_{mode}.parquet")
kc = ["setup", "account", "fam", "side", "date", "m", "xm", "r", "dollar_risk", "symbol", "stop_pct", "spy_fo", "qqq_r30"] + (["run_id", "blocked_live"] if mode == "live" else ["geom"])
T[kc].to_parquet(S / f"trades2_{mode}.parquet")
print(mode, len(T), "spy_fo nan", round(float(np.isnan(fo_).mean()), 4), K.mean().round(4).to_dict())
