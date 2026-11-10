"""BURST2 scoring (copy of burst1/score.py: lineage bar N=29, BURST2 configs, + P_11-06 window, no $ cap)
BURST1 scoring (PLAN.md metrics + decision rule). python score.py <scratch> -> results.csv, families.csv, setups_effect.csv
here, printed summary. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
BAR = max(1.5, np.sqrt(2 * np.log(29)))
import re
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]


def dt(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def book(T, w, dates):
    d = T.loc[w].groupby("date").v.sum().reindex(dates, fill_value=0.0)
    n = int(w.sum()); tot = d.sum(); bd = d.idxmax() if len(d) else None
    nb = int((w & (T.date == bd)).sum()) if bd is not None else 0
    cum = d.cumsum(); dd = (cum.cummax() - cum).max()
    return dict(total=tot, n=n, avg=tot / n if n else np.nan, avg_wo_best=(tot - d.max()) / (n - nb) if n > nb else np.nan,
                best_share=d.max() / tot if tot > 0 else np.nan, green=(d > 0).mean(), maxdd=dd)


def compare(T, kb, kr, win, label, mu, wcol=None):
    T = T[win].copy(); kb = kb[win]; kr = kr[win]
    wt = T[wcol].to_numpy(float) if wcol else np.ones(len(T))
    wb = wt * kb; wr = (T["w_rem"].to_numpy(float) if wcol else wt) * kr
    T["v"] = T.r * wr; dates = sorted(T.date.unique())
    rem = book(T, kr.astype(bool) | (wr != 0), dates); T["v"] = T.r * wb; base = book(T, kb.astype(bool), dates)
    T["dv"] = T.r * (wr - wb); T["dx"] = (T.r - T.setup.map(mu).fillna(0)) * (wr - wb)
    dd_ = T.groupby("date").dv.sum().reindex(dates, fill_value=0); dx_ = T.groupby("date").dx.sum().reindex(dates, fill_value=0)
    ps = T.groupby("setup").dv.sum()
    T["fam"] = T.setup.map(fam)
    fams = []
    for f, g in T.groupby("fam"):
        d = g.groupby("date").dv.sum().reindex(dates, fill_value=0); s = g.groupby("setup").dv.sum()
        fams.append(dict(window=label, family=f, n_setups=g.setup.nunique(),
                         delta=d.sum(), t=dt(d), improved=int((s > 1e-9).sum()), worse=int((s < -1e-9).sum()),
                         worst=float(s.min()) if len(s) else 0.0, worst_setup=s.idxmin() if len(s) else ""))
    out = dict(window=label, **{f"base_{k}": v for k, v in base.items()}, **{f"rem_{k}": v for k, v in rem.items()},
               delta=dd_.sum(), delta_t=dt(dd_), excess=dx_.sum(), excess_t=dt(dx_),
               blocked=int((kb & ~kr).sum()), setups_improved=int((ps > 1e-9).sum()), setups_worse=int((ps < -1e-9).sum()),
               worst_setup=ps.idxmin() if len(ps) else "", worst_setup_delta=float(ps.min()) if len(ps) else 0.0)
    return out, fams, ps.rename(label)


def famharm(F, T, kb, win, wcol=None):
    """add family base |R| for the 5% test"""
    g = T[win & kb].groupby(T.setup.map(fam)).r.apply(lambda x: x.abs().sum())
    F["fam_absR"] = F.family.map(g).fillna(0)
    return F


T2 = pd.read_parquet(S / "trades2_2y.parquet"); K2 = pd.read_parquet(S / "keep2_2y.parquet")
TL = pd.read_parquet(S / "trades2_live.parquet"); KL = pd.read_parquet(S / "keep2_live.parquet")
TR = T2.date <= "2026-02-28"; VA = (T2.date >= "2026-03-01") & (T2.date <= "2026-10-05")
mu = T2[TR].groupby("setup").r.mean()
CONF = [c for c in K2.columns if c[:2] in ("A_", "B_", "C_", "Cs", "D_")]
res, fams, eff = [], [], []
LW = {"LIVE_all": np.ones(len(TL), bool), "LIVE_primary": (TL.account == "primary").to_numpy(),
      "P_11-04": ((TL.account == "primary") & (TL.date == "2026-11-04")).to_numpy(),
      "P_11-05": ((TL.account == "primary") & (TL.date == "2026-11-05")).to_numpy(),
      "P_11-06": ((TL.account == "primary") & (TL.date == "2026-11-06")).to_numpy(),
      "LIVE_1105_1106": TL.date.isin(["2026-11-05", "2026-11-06"]).to_numpy()}
for c in CONF:
    bases = [("base", "base")] if not c.startswith("A_") else [("latch_realised_-2", "vsLatchR2"), ("latchoff", "vsNoLatch")]
    for bcol, btag in bases:
        for lab, T, K, w in [("TRAIN", T2, K2, TR.to_numpy()), ("VALID", T2, K2, VA.to_numpy())] + [(k, TL, KL, v) for k, v in LW.items()]:
            kb = K[bcol].to_numpy(); kr = K[c].to_numpy()
            if c.startswith("A_") and lab.startswith(("LIVE", "P_")) and bcol == "base":
                continue
            o, f, e = compare(T, kb, kr, w, lab, mu)
            o.update(config=c, vs=btag); res.append(o)
            F = pd.DataFrame(f); F = famharm(F, T[w].reset_index(drop=True), kb[w], np.ones(w.sum(), bool)); F["config"] = c; F["vs"] = btag; fams.append(F)
            eff.append(e.rename(f"{c}|{btag}|{lab}"))
R = pd.DataFrame(res); FA = pd.concat(fams, ignore_index=True); E = pd.concat(eff, axis=1)
R.to_csv(HERE / "results.csv", index=False); FA.to_csv(HERE / "families.csv", index=False); E.to_csv(HERE / "setups_effect.csv")
# decision rule
rows = []
for (c, vs), g in R.groupby(["config", "vs"]):
    g = g.set_index("window")
    if "VALID" not in g.index:
        continue
    fv = FA[(FA.config == c) & (FA.vs == vs) & (FA.window == "VALID")]
    harm = ((fv.delta < 0) & (fv.t <= -1.0)) | ((fv.worse > 2 * fv.improved) & (fv.delta < -0.05 * fv.fam_absR.fillna(np.inf)))
    p1 = g.at["VALID", "delta_t"] >= BAR and g.at["VALID", "excess_t"] >= 1.0
    p2 = g.at["TRAIN", "delta"] > 0 and g.at["TRAIN", "excess"] > 0
    p3 = g.at["LIVE_all", "delta"] > 0 if "LIVE_all" in g.index else False
    rows.append(dict(config=c, vs=vs, tr_d=g.at["TRAIN", "delta"], tr_t=g.at["TRAIN", "delta_t"], tr_x=g.at["TRAIN", "excess"], tr_xt=g.at["TRAIN", "excess_t"],
                     va_d=g.at["VALID", "delta"], va_t=g.at["VALID", "delta_t"], va_x=g.at["VALID", "excess"], va_xt=g.at["VALID", "excess_t"],
                     live_d=g.at["LIVE_all", "delta"] if "LIVE_all" in g.index else np.nan, live_t=g.at["LIVE_all", "delta_t"] if "LIVE_all" in g.index else np.nan,
                     P_d=g.at["LIVE_primary", "delta"] if "LIVE_primary" in g.index else np.nan,
                     d1104=g.at["P_11-04", "delta"] if "P_11-04" in g.index else np.nan, d1105=g.at["P_11-05", "delta"] if "P_11-05" in g.index else np.nan, d1106=g.at["P_11-06", "delta"] if "P_11-06" in g.index else np.nan,
                     P_imp=g.at["LIVE_primary", "setups_improved"] if "LIVE_primary" in g.index else np.nan, P_worse=g.at["LIVE_primary", "setups_worse"] if "LIVE_primary" in g.index else np.nan,
                     L_imp=g.at["LIVE_all", "setups_improved"] if "LIVE_all" in g.index else np.nan, L_worse=g.at["LIVE_all", "setups_worse"] if "LIVE_all" in g.index else np.nan,
                     va_imp=g.at["VALID", "setups_improved"], va_worse=g.at["VALID", "setups_worse"], va_worst=g.at["VALID", "worst_setup_delta"], va_worst_setup=g.at["VALID", "worst_setup"],
                     fam_harmed=int(harm.sum()), fam_harmed_list=",".join(fv.family[harm]), passes=bool(p1 and p2 and p3 and harm.sum() == 0)))
D = pd.DataFrame(rows); D.to_csv(HERE / "decision.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print("bar", round(BAR, 2)); print(D.round(2).to_string())
