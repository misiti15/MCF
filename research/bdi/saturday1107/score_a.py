"""Block A scoring (PLAN.md): BURST2 decision rule (burst2/score2.py logic) with lineage N = 36, plus the R split by SPY day
type (QDAY), the Remedies table (setups / families better vs worse), and the give-back effect (per day peak - close of the
realised-R curve by exit time) for the Primary-account setups (VALID) and the live Primary book.
Usage: python score_a.py <burst2 scratch> <sat1107 scratch>   Educational only - not financial advice."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
B2, S = Path(sys.argv[1]), Path(sys.argv[2]); HERE = Path(__file__).resolve().parent
N = 36; BAR = max(1.5, np.sqrt(2 * np.log(N)))
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]
dt = lambda x: (np.mean(x) / np.std(x, ddof=1) * np.sqrt(len(x))) if len(x) > 2 and np.std(x, ddof=1) > 0 else np.nan

T2 = pd.read_parquet(B2 / "trades2_2y.parquet"); K2 = pd.read_parquet(S / "keepA_2y.parquet")
TL = pd.read_parquet(B2 / "trades2_live.parquet"); KL = pd.read_parquet(S / "keepA_live.parquet")
# SPY day type
b = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet"); b = b[(b.index.hour * 60 + b.index.minute >= 570) & (b.index.hour * 60 + b.index.minute < 960)]
d = b.index.strftime("%Y-%m-%d"); oc = (b.groupby(d).close.last() / b.groupby(d).open.first() - 1) * 100
I = pd.read_parquet(B2 / "live_idx1.parquet"); I = I[I.symbol == "SPY"].sort_values("t"); g = I.groupby("date")
oc = pd.concat([oc[oc.index < "2026-10-06"], (g.c.last() / g.o.first() - 1) * 100])
DT = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
T2["dtype"] = T2.date.map(DT); TL["dtype"] = TL.date.map(DT)
assert not T2.date.between("2024-11-01", "2025-02-28").any()
TR = (T2.date <= "2026-02-28").to_numpy(); VA = ((T2.date >= "2026-03-01") & (T2.date <= "2026-10-05")).to_numpy()
mu = T2[TR].groupby("setup").r.mean()
LW = {"LIVE_all": np.ones(len(TL), bool), "LIVE_primary": (TL.account == "primary").to_numpy(),
      "P_11-04": ((TL.account == "primary") & (TL.date == "2026-11-04")).to_numpy(),
      "P_11-05": ((TL.account == "primary") & (TL.date == "2026-11-05")).to_numpy(),
      "P_11-06": ((TL.account == "primary") & (TL.date == "2026-11-06")).to_numpy()}
VS = {"A1_D_flush_2_30": "base", "A2_D_flush_2_50": "base", "A3_D_flush_3_40": "base", "A4_D_flushQ_2_40": "base",
      "A5_D_flushQ_2_30": "base", "A6_latch_or_-3": "latch_realised_-2", "A7_flushQ_latch_or": "latch_realised_-2"}


def giveback(T, keep):
    x = T[keep].sort_values(["date", "xm"])
    out = {}
    for dd, gg in x.groupby("date"):
        c = gg.r.cumsum().to_numpy(); pk = max(0.0, c.max()); out[dd] = (pk - c[-1], pk, c[-1])
    return pd.DataFrame(out, index=["gb", "peak", "close"]).T


def compare(T, kb, kr, w, lab):
    T = T[w]; kb = kb[w]; kr = kr[w]
    dates = sorted(T.date.unique())
    T = T.assign(dv=T.r * (kr.astype(float) - kb.astype(float)), dx=(T.r - T.setup.map(mu).fillna(0)) * (kr.astype(float) - kb.astype(float)))
    dd_ = T.groupby("date").dv.sum().reindex(dates, fill_value=0); dx_ = T.groupby("date").dx.sum().reindex(dates, fill_value=0)
    ps = T.groupby("setup").dv.sum(); fams = []
    for f, gg in T.groupby(T.setup.map(fam)):
        dfam = gg.groupby("date").dv.sum().reindex(dates, fill_value=0); s = gg.groupby("setup").dv.sum()
        fams.append(dict(window=lab, family=f, delta=dfam.sum(), t=dt(dfam), improved=int((s > 1e-9).sum()), worse=int((s < -1e-9).sum()),
                         fam_absR=T[kb & (T.setup.map(fam) == f).to_numpy()].r.abs().sum()))
    byt = T.groupby("dtype").dv.sum()
    base_tot = (T.r * kb).sum()
    o = dict(window=lab, base_R=base_tot, base_n=int(kb.sum()), blocked=int((kb & ~kr).sum()), delta=dd_.sum(), delta_t=dt(dd_),
             excess=dx_.sum(), excess_t=dt(dx_), d_up=byt.get("up", 0.0), d_down=byt.get("down", 0.0), d_quiet=byt.get("quiet", 0.0),
             imp=int((ps > 1e-9).sum()), worse=int((ps < -1e-9).sum()), imp_R=ps[ps > 0].sum(), worse_R=ps[ps < 0].sum(),
             worst_setup=ps.idxmin() if len(ps) and ps.min() < 0 else "", worst_d=float(ps.min()) if len(ps) else 0.0,
             blocked_avgR=T[kb & ~kr].r.mean() if (kb & ~kr).any() else np.nan)
    return o, fams, ps.rename(lab)


res, FA, EF, GB = [], [], [], []
for c, bc in VS.items():
    for lab, T, K, w in [("TRAIN", T2, K2, TR), ("VALID", T2, K2, VA)] + [(k, TL, KL, v) for k, v in LW.items()]:
        kb = K[bc].to_numpy() & K["base"].to_numpy() if bc == "base" else K[bc].to_numpy()
        kr = K[c].to_numpy() & (K["base"].to_numpy() if bc == "base" else np.ones(len(K), bool))
        if bc != "base" and c == "A7_flushQ_latch_or":
            kr = K[c].to_numpy()
        o, f, e = compare(T, kb, kr, w, lab); o.update(config=c, vs=bc); res.append(o)
        F = pd.DataFrame(f); F["config"] = c; FA.append(F); EF.append(e.rename(f"{c}|{lab}"))
    # give-back: Primary-account setups VALID, live Primary
    for lab, T, K, w in (("VALID_primary_setups", T2, K2, VA & (T2.account == "primary").to_numpy()), ("LIVE_primary", TL, KL, (TL.account == "primary").to_numpy())):
        kb = (K[bc].to_numpy() & K["base"].to_numpy()) if bc == "base" else K[bc].to_numpy()
        kr = (K[c].to_numpy() & K["base"].to_numpy()) if bc == "base" else K[c].to_numpy()
        gb0, gb1 = giveback(T[w], kb[w]), giveback(T[w], kr[w])
        j = gb0.join(gb1, rsuffix="_c", how="outer").fillna(0)
        sw0 = ((j.peak >= 3) & (j.close <= 0)).sum(); sw1 = ((j.peak_c >= 3) & (j.close_c <= 0)).sum()
        GB.append(dict(config=c, window=lab, days=len(j), gb_mean_base=j.gb.mean(), gb_mean_cfg=j.gb_c.mean(), gb_p90_base=j.gb.quantile(.9),
                       gb_p90_cfg=j.gb_c.quantile(.9), peak_mean_base=j.peak.mean(), peak_mean_cfg=j.peak_c.mean(),
                       swing_days_base=int(sw0), swing_days_cfg=int(sw1), close_sum_base=j.close.sum(), close_sum_cfg=j.close_c.sum()))
R = pd.DataFrame(res); FA = pd.concat(FA, ignore_index=True); E = pd.concat(EF, axis=1); G = pd.DataFrame(GB)
R.round(4).to_csv(HERE / "a_results.csv", index=False); FA.round(3).to_csv(HERE / "a_families.csv", index=False)
E.round(3).to_csv(HERE / "a_setups_effect.csv"); G.round(3).to_csv(HERE / "a_giveback.csv", index=False)
rows = []
for c, gg in R.groupby("config", sort=False):
    gg = gg.set_index("window"); fv = FA[(FA.config == c) & (FA.window == "VALID")]
    harm = ((fv.delta < 0) & (fv.t <= -1.0)) | ((fv.worse > 2 * fv.improved) & (fv.delta < -0.05 * fv.fam_absR))
    p = (gg.at["VALID", "delta_t"] >= BAR and gg.at["VALID", "excess_t"] >= 1.0 and gg.at["TRAIN", "delta"] > 0
         and gg.at["TRAIN", "excess"] > 0 and gg.at["LIVE_all", "delta"] > 0 and harm.sum() == 0)
    rows.append(dict(config=c, vs=VS[c], tr_d=gg.at["TRAIN", "delta"], tr_xt=gg.at["TRAIN", "excess_t"], va_d=gg.at["VALID", "delta"],
                     va_t=gg.at["VALID", "delta_t"], va_xt=gg.at["VALID", "excess_t"], va_up=gg.at["VALID", "d_up"], va_down=gg.at["VALID", "d_down"],
                     va_quiet=gg.at["VALID", "d_quiet"], va_imp=gg.at["VALID", "imp"], va_worse=gg.at["VALID", "worse"],
                     live_d=gg.at["LIVE_all", "delta"], live_t=gg.at["LIVE_all", "delta_t"], live_up=gg.at["LIVE_all", "d_up"],
                     live_down=gg.at["LIVE_all", "d_down"], live_quiet=gg.at["LIVE_all", "d_quiet"],
                     L_imp=gg.at["LIVE_all", "imp"], L_imp_R=gg.at["LIVE_all", "imp_R"], L_worse=gg.at["LIVE_all", "worse"], L_worse_R=gg.at["LIVE_all", "worse_R"],
                     L_worst=f'{gg.at["LIVE_all", "worst_setup"]} {gg.at["LIVE_all", "worst_d"]:+.1f}',
                     P_d=gg.at["LIVE_primary", "delta"], P_imp=gg.at["LIVE_primary", "imp"], P_worse=gg.at["LIVE_primary", "worse"], P_worse_R=gg.at["LIVE_primary", "worse_R"],
                     d1104=gg.at["P_11-04", "delta"], d1105=gg.at["P_11-05", "delta"], d1106=gg.at["P_11-06", "delta"],
                     fam_harmed=",".join(fv.family[harm]), passes=bool(p)))
D = pd.DataFrame(rows); D.round(3).to_csv(HERE / "a_decision.csv", index=False)
pd.set_option("display.width", 400); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 60)
txt = f"bar {BAR:.2f} (N {N})\n" + D.round(2).to_string() + "\n\ngive-back (R per day; peak - close of the realised curve):\n" + G.round(2).to_string()
open(HERE / "a_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
