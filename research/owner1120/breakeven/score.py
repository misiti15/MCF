"""Owner item 2 (2026-11-20) breakeven grid - scoring (PLAN.md pass bar, frozen before scoring).
Usage: python score.py lab_agg.parquet live_be.parquet OUTDIR. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/user/MCF/research/history2y")
from lab_be import CFG  # noqa: E402
import lib  # noqa: E402

SPLIT = pd.Timestamp("2025-09-30").date(); LATE = pd.Timestamp("2026-10-06").date()
NC = len(CFG); DC = [f"d{i}" for i in range(NC)]; CC = [f"c{i}" for i in range(NC)]
X = pd.read_parquet(sys.argv[1]); L = pd.read_parquet(sys.argv[2]); OUT = Path(sys.argv[3]); OUT.mkdir(exist_ok=True)
SM = pd.read_csv(Path(__file__).resolve().parents[2] / "bdi/1119/ntbe_setups.csv")[["setup", "side"]].drop_duplicates("setup")
X = X.merge(SM, on="setup", how="left"); assert X.side.notna().all()
X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
X["fs"] = X.family + ("_L" if False else "") + np.where(X.side > 0, "_L", "_S")
L["fs"] = L.family + np.where(L.side > 0, "_L", "_S")
D_ = lib.daily(); S = D_[D_.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
DTYPE = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
fsn = X.groupby("fs").n.sum(); FS = sorted(fsn[fsn >= 300].index)
stn = X.groupby("setup").n.sum(); ST = set(stn[stn >= 300].index)
N_CFG = 2 * NC * (1 + 2 + 3 + len(FS)); BAR = max(1.5, float(np.sqrt(2 * np.log(N_CFG))))
BOOKDAY = X.groupby("date").base.sum(); TOPD = set(BOOKDAY[BOOKDAY >= BOOKDAY.quantile(0.9)].index)


def stats(x):
    """x: rows of one scope -> dict of arrays (NC,) for full/fit/check and diagnostics."""
    g = x.groupby("date")[["n", "base"] + DC].sum()
    dates = np.array(g.index); n = g.n.to_numpy(float); M = g[DC].to_numpy(float)
    out = {"n": int(n.sum()), "days": len(g), "base": g.base.sum() / n.sum()}
    for nm, m in (("full", np.ones(len(dates), bool)), ("fit", dates <= SPLIT), ("chk", dates > SPLIT), ("late", dates >= LATE)):
        nn = n[m].sum()
        if nn < 2: out[nm] = np.full(NC, np.nan); out[nm + "_t"] = np.full(NC, np.nan); continue
        mu = M[m].sum(0) / nn; se = np.sqrt(((M[m] - n[m, None] * mu) ** 2).sum(0)) / nn
        out[nm] = mu; out[nm + "_t"] = np.where(se > 0, mu / np.where(se > 0, se, 1), 0.0); out[nm + "_n"] = nn
    tot = M.sum(0); b = M.argmax(0); bs = M[b, np.arange(NC)]; bn = n[b]
    out["total"] = tot; out["wo_best"] = (tot - bs) / np.maximum(1, n.sum() - bn)
    out["best_share"] = np.where(tot > 0, bs / np.where(tot != 0, tot, 1), np.nan)
    dt = pd.Series(dates).map(DTYPE).to_numpy()
    for k in ("up", "down", "quiet"): out[k] = M[dt == k].sum(0)
    tm = np.isin(dates, list(TOPD)); out["topdec"] = M[tm].sum(0)
    out["chg"] = x[CC].sum().to_numpy(float) / n.sum()
    return out


def units(x, key, keep):
    g = x[x[key].isin(keep)].groupby(key)[["n"] + DC].sum()
    mu = g[DC].to_numpy(float) / g.n.to_numpy(float)[:, None]; tot = g[DC].to_numpy(float)
    return dict(better=(mu > 0).sum(0), worse=(mu < 0).sum(0), worst=mu.min(0) if len(mu) else np.zeros(NC),
                better_R=np.where(tot > 0, tot, 0).sum(0), worse_R=np.where(tot < 0, tot, 0).sum(0), nunits=len(g))


def live(lx):
    if not len(lx): return np.zeros(NC), 0, np.zeros(NC)
    M = lx[DC].to_numpy(float); g = lx.groupby("date")[DC].sum().to_numpy(float); n = len(lx); mu = M.mean(0)
    cnt = lx.groupby("date").size().to_numpy(float); se = np.sqrt(((g - cnt[:, None] * mu) ** 2).sum(0)) / n
    return mu, n, np.where(se > 0, mu / np.where(se > 0, se, 1), 0)


scopes = [("book", "all", X, L, "fs", FS)]
for sd, nm in ((1, "long"), (-1, "short")): scopes.append(("side", nm, X[X.side == sd], L[L.side == sd], "fs", FS))
for it in ("stock", "etf", "invvol"): scopes.append(("itype", it, X[X.itype == it], L[L.itype == it], "fs", FS))
for f in FS: scopes.append(("family", f, X[X.fs == f], L[L.fs == f], "setup", ST))
rows = []
for kind, nm, x, lx, ukey, keep in scopes:
    s = stats(x); u = units(x, ukey, keep); lm, ln, lt = live(lx)
    for half in (False, True):
        k = 0.5 if half else 1.0
        for i, c in enumerate(CFG):
            r = dict(scope=kind, unit=nm, cfg=c + ("|H" if half else "|F"), n=s["n"], base=round(s["base"], 4),
                     delta=k * s["full"][i], t=s["full_t"][i], fit=k * s["fit"][i], fit_t=s["fit_t"][i], chk=k * s["chk"][i],
                     chk_t=s["chk_t"][i], late=k * s["late"][i], late_t=s["late_t"][i], total=k * s["total"][i],
                     wo_best=k * s["wo_best"][i], best_share=s["best_share"][i], up=k * s["up"][i], down=k * s["down"][i],
                     quiet=k * s["quiet"][i], topdec=k * s["topdec"][i], chg=s["chg"][i] * (0.5 if half else 1),
                     u_better=u["better"][i], u_worse=u["worse"][i], u_worst=k * u["worst"][i], u_better_R=k * u["better_R"][i],
                     u_worse_R=k * u["worse_R"][i], n_units=u["nunits"], live=k * lm[i], live_n=ln, live_t=lt[i])
            cand = r["fit"] > 0 and r["fit_t"] >= 2.0
            r["cand"] = bool(cand)
            r["pass"] = bool(cand and r["chk"] > 0 and r["chk_t"] >= 1.5 and r["t"] >= BAR and r["wo_best"] > 0
                             and (r["best_share"] < 0.5) and r["up"] > 0 and r["down"] > 0 and r["u_better"] > r["u_worse"]
                             and r["u_worst"] >= -0.03 and (r["live_n"] < 100 or r["live"] >= 0))
            r["topdec_flag"] = bool(r["total"] > 0 and r["topdec"] < -0.25 * r["total"])
            rows.append(r)
R = pd.DataFrame(rows)
for c in R.columns:
    if R[c].dtype == float: R[c] = R[c].round(4)
R.to_csv(OUT / "grid_all.csv.gz", index=False)
print(f"configs counted N {N_CFG} (432 rules x {1 + 2 + 3 + len(FS)} scopes); bar {BAR:.2f}; family-sides {len(FS)}; setups n>=300 {len(ST)}")
print(f"book: trades {int(X.n.sum())}, days {X.date.nunique()}, base {X.base.sum() / X.n.sum():+.4f}; top-decile days {len(TOPD)} "
      f"(base sum {BOOKDAY[list(TOPD)].sum():+.0f}R of {BOOKDAY.sum():+.0f}R)")
print("candidates (fit t>=2, delta>0):", int(R.cand.sum()), " pass:", int(R["pass"].sum()))
# per-family best-5 base days cost for the book configs
fb = []
for f in FS:
    x = X[X.fs == f]; bd = x.groupby("date").base.sum().nlargest(5).index
    fb.append(x[x.date.isin(bd)][DC].sum().to_numpy())
pd.DataFrame({"cfg": CFG, "fam_best5_delta": np.array(fb).sum(0).round(1)}).to_csv(OUT / "fam_best5.csv", index=False)
print("Educational only - not financial advice.")
