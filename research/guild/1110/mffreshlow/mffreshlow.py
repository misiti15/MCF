"""MFFRESHLOW (plan PLAN.md, frozen 2026-11-10 before any score): skip an MF2/MF4 flow-sell short when the session low
was set in the last 15 minutes and the entry is within X x ATR10 of it (X 0.10 / 0.20). Excess vs same-variant
same-day random skip blocks (200 draws); gross first; retention per variant. N 4 -> BAR90 1.67.
    python mffreshlow.py > mffreshlow_out.txt          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
from mcf.research.gates import GEOMK, tod_cost_mult
HERE = Path(__file__).resolve().parent
NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
SPLIT = pd.Timestamp("2025-09-30").date(); N = 4; T90 = round(max(1.35, .9 * G.t_required(N)), 2)
SCORED = ["MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "MF4-h40-open-flowsell"]
SL, BP, SX = 0.01, 1e-4, 0.02

L = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
L = L[L.setup.str.startswith("MF")].copy(); L["date"] = pd.to_datetime(L.date).dt.date; L["tod"] = L.tod.astype(int)
L["symbol"] = L.symbol.astype(str)
# entry price, R, gross (bt_all cost inverted)
parts = []
for m in sorted(pd.to_datetime(L.date).dt.strftime("%Y-%m").unique()):
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "gap"])
    f["tod"] = f.tod.astype(int); f["symbol"] = f.symbol.astype(str)
    parts.append(L[pd.to_datetime(L.date).dt.strftime("%Y-%m") == m].merge(f, on=["symbol", "date", "tod"], how="left"))
L = pd.concat(parts, ignore_index=True)
e = L.close.to_numpy(float); R = .25 * L.atr_d.to_numpy(float); dn = L.geom.map(lambda g: GEOMK[g][1]).to_numpy(float)
tier = np.where((L.gap.abs().to_numpy(float) >= 20) | (e < 5), 3.0, 1.0); kd = L.kind.to_numpy()
cost = (SL + e * BP) * tod_cost_mult(L.tod.to_numpy()) + np.where(kd == 2, 0.0, SL + e * BP) + np.where(kd == 1, SX, 0.0)
L["gross"] = (L.r.to_numpy() * dn + tier * cost / R) / dn

# fresh-low features from the 1-min cache (bars that start before the entry bar close)
feat = {}
for sym, g in L.groupby("symbol"):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"; ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    df.index = pd.DatetimeIndex(df.index).tz_convert(NY); df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = df.index.hour * 60 + df.index.minute; df = df[(mm >= 570) & (mm < 960)]
    d_ = df.index.date
    day = df.groupby(d_).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
    pc = day.c.shift(1); gap = pd.Series(pd.to_datetime(day.index)).diff().dt.days.to_numpy() > 5; pc[gap] = np.nan
    tr = np.maximum(day.h - day.l, np.maximum((day.h - pc).abs(), (day.l - pc).abs()))
    atr10 = tr.shift(1).rolling(10, min_periods=5).mean()
    byd = {d: x for d, x in df.groupby(d_)}
    for i, r in g.iterrows():
        x = byd.get(r.date)
        if x is None: continue
        em = r.tod // 100 * 60 + r.tod % 100
        xm = x.index.hour * 60 + x.index.minute; y = x[xm < em]
        if not len(y) or not np.isfinite(atr10.get(r.date, np.nan)): continue
        lo = y.low.min(); tlo = int((y.low.values == lo).nonzero()[0][-1]); t_lo = int(xm[xm < em][tlo])
        feat[i] = ((r.close - lo) / atr10[r.date], em - t_lo <= 15)
L["dist_lo"] = pd.Series({i: v[0] for i, v in feat.items()}); L["fresh15"] = pd.Series({i: v[1] for i, v in feat.items()}).astype("boolean")
print(f"MF trades {len(L)}; feature coverage {L.dist_lo.notna().mean():.2%}; lineage N {N}, BAR90 {T90}")

D = lib.daily(); S = D[D.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
rng = np.random.default_rng(20261110)
rows = []
for X in (0.10, 0.20):
    L["skip"] = (L.fresh15.fillna(False) & (L.dist_lo <= X)).astype(bool)
    print(f"\nX {X}: skip share by setup (all MF, info): {L.groupby('setup').skip.mean().round(4).to_dict()}")
    P = L[L.setup.isin(SCORED)].reset_index(drop=True)
    r = P.r.to_numpy(); gr = P.gross.to_numpy(); sk = P.skip.to_numpy(); var = P.setup.to_numpy()
    for lab_, vals in (("net", r), ("gross", gr)):
        ex = {}
        for d, ii in P.groupby("date").indices.items():
            k = sk[ii]
            if not k.any(): ex[d] = 0.0; continue
            blocks = [(ii[var[ii] == v], int((k & (var[ii] == v)).sum())) for v in np.unique(var[ii])]
            rnd = np.mean([sum(-vals[rng.choice(jj, kv, replace=False)].sum() for jj, kv in blocks if kv) for _ in range(200)])
            ex[d] = -vals[ii][k].sum() - rnd
        E = pd.Series(ex).sort_index(); Ed = pd.Series(E.index, index=E.index)
        tt = lambda s: round(s.mean() / (s.std(ddof=1) / np.sqrt(len(s))), 2) if len(s) > 2 and s.std() > 0 else None
        ty = E.groupby(E.index.map(dtype)).sum()
        top = np.zeros(len(P), bool)
        for v in SCORED:
            m_ = var == v; top[m_] = gr[m_] >= np.quantile(gr[m_], .9)
        per = "; ".join(f"{v.replace('-flowsell','').replace('-open','')} n{int((var == v).sum())} skip{int((sk & (var == v)).sum())} "
                        f"kept{1 - sk[var == v].mean():.3f} top{1 - sk[(var == v) & top].mean():.3f} "
                        f"sk_g{np.nanmean(gr[(var == v) & sk]):+.3f} kp_g{np.nanmean(gr[(var == v) & ~sk]):+.3f}" for v in SCORED)
        row = dict(config=f"MFFL-X{X:.2f}", basis=lab_, n=len(P), skipped=int(sk.sum()), excess=round(E.sum(), 1), t=tt(E),
                   train=round(E[Ed <= SPLIT].sum(), 1), train_t=tt(E[Ed <= SPLIT]), valid=round(E[Ed > SPLIT].sum(), 1), valid_t=tt(E[Ed > SPLIT]),
                   wo_best=round(E.drop(E.idxmax()).sum(), 1), up=round(ty.get("up", 0), 1), down=round(ty.get("down", 0), 1),
                   quiet=round(ty.get("quiet", 0), 1), kept=round(1 - sk.mean(), 3), top_kept=round(1 - sk[top].mean(), 3), per_variant=per)
        rows.append(row)
R = pd.DataFrame(rows); pd.set_option("display.width", 500); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 500)
print("\n" + R.to_string(index=False))
ok = R[R.basis == "net"].apply(lambda x: (x.t or 0) >= T90 and x.train > 0 and x.valid > 0 and x.wo_best > 0 and x.up >= 0 and x.down >= 0
                                and x.kept >= .8 and x.top_kept >= .9, axis=1)
grs = R[R.basis == "gross"].excess.to_numpy() > 0
print(f"\npass (net bar {T90}, gross excess > 0 required, retention pooled; per-variant retention in the table): "
      f"{[f'{c}: {bool(a and b)}' for c, a, b in zip(R[R.basis == 'net'].config, ok, grs)]}")
R.to_csv(HERE / "mffreshlow_results.csv", index=False); print("Educational only - not financial advice.")
