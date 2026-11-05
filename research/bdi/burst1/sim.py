"""BURST1 simulator: apply the 16 pre-registered configs (PLAN.md) to a trade table and write keep flags.
2-year:  python sim.py 2y <scratch>    (needs <scratch>/enr from enrich.py, <scratch>/state.parquet from gate1/state.py)
live:    python sim.py live <scratch>  (needs <scratch>/live_trades.parquet, live_bars5.parquet, state.parquet)
Writes <scratch>/keep_<mode>.parquet (one bool column per config + baselines) and <scratch>/trades_<mode>.parquet.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rules import pace, latch, fof, burst_compass  # noqa: E402

mode, S = sys.argv[1], Path(sys.argv[2])
CONFIGS = ([("a_pace", N) for N in (2, 3, 4)] + [("b_openlatch", L) for L in (-2, -3)] +
           [("c_fof", K) for K in (2, 3, 4)] + [("d_cluster", M) for M in (4, 6, 8)] +
           [("e_burstcompass", B) for B in (2, 3)])          # (f) $ cap is a sizing re-weight, scored in score.py

st = pd.read_parquet(S / "state.parquet")
st = st[st["T"] >= 600]; st["date"] = st.date.astype(str)
STATE = {d: (g["T"].to_numpy(), g.st.to_numpy()) for d, g in st.groupby("date")}


def load_2y():
    T, MK, MF = [], [], []
    for p in sorted((S / "enr").glob("*.parquet")):
        t = pd.read_parquet(p); mk = np.load(str(p).replace(".parquet", "_mk.npy")); mf = np.load(str(p).replace(".parquet", "_mfe.npy"))
        keep = t.date <= "2026-10-05"
        T.append(t[keep.values]); MK.append(mk[keep.values]); MF.append(mf[keep.values])
    T = pd.concat(T, ignore_index=True); MK = np.vstack(MK).astype(np.float32); MF = np.vstack(MF).astype(np.float32)
    MK = pd.DataFrame(MK).ffill(axis=1).fillna(0).to_numpy(np.float32)
    MF = pd.DataFrame(MF).ffill(axis=1).fillna(0).to_numpy(np.float32)
    acc = pd.read_csv("/home/user/MCF/research/bdi/1104/setups.csv").set_index("setup").account
    T["account"] = T.setup.map(acc)
    T["m"] = (T.tod // 100) * 60 + T.tod % 100; T["xm"] = (T.xtod // 100) * 60 + T.xtod % 100
    T["dollar_risk"] = np.minimum(250.0, 3980.0 * T.stop_pct.fillna(0.01))
    sl = lambda t: min(73, max(0, (int(t) - 590) // 5))
    mk = lambda j, t: float(MK[j, sl(t)]); mfe = lambda j, t: float(MF[j, sl(t)])
    return T, mk, mfe


def load_live():
    T = pd.read_parquet(S / "live_trades.parquet").rename(columns={"strategy": "setup", "R": "r"})
    T = T.sort_values(["account", "setup", "date", "ent_ts", "id"]).reset_index(drop=True)
    B = pd.read_parquet(S / "live_bars5.parquet")
    B["cm"] = B.t.dt.hour * 60 + B.t.dt.minute + 5; B["sm"] = B.cm - 5
    G = {k: (g.sm.to_numpy(), g.cm.to_numpy(), g.h.to_numpy(), g.l.to_numpy(), g.c.to_numpy()) for k, g in B.groupby(["date", "symbol"])}
    T["m"] = T.ent; T["xm"] = T.ext
    T["dollar_risk"] = T.risk.where(T.run_id == 1, np.nan)
    e, sd, sd_ = T.entry.to_numpy(float), T.side.to_numpy(int), (T.entry - T.stop).abs().to_numpy(float)
    keys = list(zip(T.date, T.symbol))

    def path(j, t):
        g = G.get(keys[j])
        if g is None:
            return 0.0, 0.0
        sm, cm, h, l, c = g; ok = (sm >= T.m.iat[j]) & (cm <= t)
        if not ok.any():
            return 0.0, 0.0
        mk_ = sd[j] * (c[ok][-1] - e[j]) / sd_[j]
        mf_ = (sd[j] * ((l if sd[j] == -1 else h)[ok] - e[j]) / sd_[j]).max()
        return float(mk_), float(mf_)
    return T, (lambda j, t: path(j, t)[0]), (lambda j, t: path(j, t)[1])


T, mk, mfe = load_2y() if mode == "2y" else load_live()
m_, xm_, r_, side_ = T.m.to_numpy(), T.xm.to_numpy(), T.r.to_numpy(float), T.side.to_numpy(int)


def against(d):
    Ts, sts = STATE.get(d, (np.array([]), np.array([])))
    def f(t, side):
        k = np.searchsorted(Ts, t, side="right") - 1
        return k >= 0 and sts[k] == -side
    return f


K = {}
base_seq = np.ones(len(T), bool) if mode == "2y" else (T.run_id == 1).to_numpy()
seq_all = np.ones(len(T), bool)     # live: run1 + latch-blocked what-ifs (latch-off sequence) for (b)
cols = {f"{a}_{p}": np.zeros(len(T), bool) for a, p in CONFIGS}
cols["base"] = base_seq.copy(); cols["latch_realised_-2"] = np.zeros(len(T), bool); cols["latchoff"] = seq_all.copy()
gs = T.groupby(["setup", "date"], sort=False).indices
for (su, d), ix in gs.items():
    ix = np.asarray(ix); ix = ix[np.lexsort((ix, m_[ix]))]
    for a, p in CONFIGS:
        if a == "d_cluster":
            continue
        if a == "b_openlatch":
            sub = ix                                     # latch-off sequence
            loc = latch(m_[sub], xm_[sub], r_[sub], p, mk=lambda jj, t, sub=sub: mk(sub[jj], t))
            cols[f"{a}_{p}"][sub] = loc
            continue
        sub = ix[base_seq[ix]]
        if len(sub) < 2:
            cols[f"{a}_{p}"][sub] = True; continue
        if a == "a_pace":
            loc = pace(m_[sub], p)
        elif a == "c_fof":
            loc = fof(m_[sub], xm_[sub], p, 0.5, lambda jj, t, sub=sub: mfe(sub[jj], t))
        else:
            loc = burst_compass(m_[sub], side_[sub][0], p, against(d))
        cols[f"{a}_{p}"][sub] = loc
    cols["latch_realised_-2"][ix] = latch(m_[ix], xm_[ix], r_[ix], -2)
ga = T[base_seq].groupby(["account", "date", "side"], sort=False).indices
bidx = np.flatnonzero(base_seq)
for M in (4, 6, 8):
    for k, ix in ga.items():
        ix = bidx[np.asarray(ix)]; ix = ix[np.lexsort((ix, m_[ix]))]
        cols[f"d_cluster_{M}"][ix] = pace(m_[ix], M)
Kp = pd.DataFrame(cols)
Kp.to_parquet(S / f"keep_{mode}.parquet")
keepcols = ["setup", "account", "side", "date", "m", "xm", "r", "dollar_risk"] + (["symbol", "run_id", "blocked_live", "stop_pct"] if mode == "live" else ["symbol", "stop_pct", "geom"])
T[keepcols].to_parquet(S / f"trades_{mode}.parquet")
print(mode, len(T), Kp.mean().round(4).to_dict())
