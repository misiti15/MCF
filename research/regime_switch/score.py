"""REGSW step 2: score the pre-registered switch configs (PLAN.md) on lab TRAIN / VALID / FWD and on live.
Usage: python research/regime_switch/score.py <scratch>   (after base.py). Writes research/regime_switch/*.csv + score_out.txt.
Everything is computed on a grid unit x day x decision-bucket (the switch weight is constant inside a bucket).
Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent; S = Path(sys.argv[1])
DT = [590, 600, 630, 660, 720, 780]; NB = len(DT)
SPLITS = ["TRAIN", "VALID", "FWD", "LIVE"]
DIR = ["CMP", "CMPL", "SPYO", "IDX3", "GAP", "BRDO", "BRDV", "VXX", "SECT"]
N_BAR = 100; BAR = max(1.5, math.sqrt(2 * math.log(N_BAR)))
RNG = np.random.default_rng(20261111); NPERM = 200
out = []


def p(*a):
    out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)


# ------------------------------------------------------------------ load
TG = pd.read_csv(S / "targets.csv"); TG = TG[TG.in_lab]
B = pd.read_parquet(S / "lab_base.parquet"); B["unit"] = B.setup
LV = pd.read_parquet(S / "live_trades.parquet"); LV = LV[LV.setup.isin(TG.setup)].copy(); LV["unit"] = LV.account + "|" + LV.setup
F = pd.read_parquet(S / "feats.parquet").sort_values(["date", "T"])
F["w60"] = F.groupby("date").w60.ffill().fillna(0)
FI = F.set_index(["date", "T"])
CORE = set(TG[TG.core].setup)


def grid(T):
    """unit x trading day x bucket: R, n, plus SELF (unit realised R by T) and FSTOP (family stops by T)."""
    T = T[T.b >= 0]
    meta = T.groupby("unit").agg(setup=("setup", "first"), fam=("fam", "first"), side=("side", "first"),
                                 acct=("account", "first") if "account" in T else ("setup", "first"))
    ud = T[["unit", "date", "split"]].drop_duplicates()
    G = ud.loc[ud.index.repeat(NB)].reset_index(drop=True); G["b"] = np.tile(np.arange(NB), len(ud))
    agg = T.groupby(["unit", "date", "b"]).r.agg(R="sum", n="size").reset_index()
    G = G.merge(agg, on=["unit", "date", "b"], how="left").fillna({"R": 0.0, "n": 0})
    G = G.join(meta, on="unit")
    G["T"] = np.array(DT)[G.b]
    fkey = (T.account + "|" + T.fam) if "account" in T else T.fam
    T = T.assign(fk=fkey.values, stop=(T.r <= -0.95).astype(int))
    G["fk"] = (G.acct + "|" + G.fam) if "account" in T else G.fam
    sel, fst = [], []
    for k, t in enumerate(DT):
        done = T[T.x <= t]
        sel.append(done.groupby(["unit", "date"]).r.sum().rename(k))
        fst.append(done.groupby(["fk", "date"]).stop.sum().rename(k))
    sel = pd.concat(sel, axis=1).stack().rename("self_R").reset_index().rename(columns={"level_2": "b"})
    fst = pd.concat(fst, axis=1).stack().rename("fam_stops").reset_index().rename(columns={"level_2": "b"})
    G = G.merge(sel, on=["unit", "date", "b"], how="left").merge(fst, on=["fk", "date", "b"], how="left")
    G = G.fillna({"self_R": 0.0, "fam_stops": 0})
    f = FI.reindex(pd.MultiIndex.from_arrays([G.date, G["T"]])).reset_index(drop=True)
    for c in f.columns:
        G[c] = f[c].values
    return G.sort_values(["unit", "date", "b"]).reset_index(drop=True)


GL = grid(B); GV = grid(LV); GV["split"] = "LIVE"
G = pd.concat([GL, GV], ignore_index=True)
# setup weight: 1 / TRAIN base trades per trading day (lab), so each setup counts about equally
tpd = B[B.split == "TRAIN"].groupby("setup").size() / B[B.split == "TRAIN"].groupby("setup").date.nunique()
G["sw"] = 1.0 / G.setup.map(tpd).fillna(tpd.median())
p("# REGSW score output (Educational only - not financial advice)")
p(f"targets in lab {len(TG)} (core {len(CORE & set(TG.setup))}); lab base trades {len(B):,}; live trades {len(LV):,} "
  f"({LV.groupby('account').size().to_dict()}); bar t >= {BAR:.2f} (N {N_BAR})")


# ------------------------------------------------------------------ states
def state(sig, g, m=1.0):
    nan0 = lambda a: np.nan_to_num(np.asarray(a, float))
    w = g.w60.values
    if sig == "CMP":
        return np.where(w == 2, 1, np.where(w == -2, -1, 0))
    if sig == "CMPL":
        return np.where(w >= 1, 1, np.where(w <= -1, -1, 0))
    th = lambda x, t: np.where(nan0(x) > t * m, 1, np.where(nan0(x) < -t * m, -1, 0))
    if sig == "SPYO":
        return th(g.spy_fo, 0.001)
    if sig == "IDX3":
        a, b_, c = th(g.spy_fo, 0.001), th(g.qqq_fo, 0.001), th(g.iwm_fo, 0.001)
        return np.where((a == b_) & (b_ == c), a, 0)
    if sig == "GAP":
        return th(g.gap, 0.0025)
    if sig in ("BRDO", "BRDV"):
        x = g.bo.values if sig == "BRDO" else g.bv.values
        return np.where(np.isnan(x), 0, np.where(x > 0.5 + 0.1 * m, 1, np.where(x < 0.5 - 0.1 * m, -1, 0)))
    if sig == "VXX":
        return -th(g.vxx, 0.02)
    if sig == "SECT":
        return th(g.sect, 0.003)
    if sig == "PDT":
        return th(g.pdt, 0.0025)
    if sig == "RVOL":
        x = g.rvol.values
        return np.where(np.isnan(x), 0, np.where(x > 1 + 0.25 * m, 1, np.where(x < 1 - 0.2 * m, -1, 0)))
    if sig == "DOW":
        return g.dow.values.astype(int)
    if sig == "FOMC":
        return g.fomc.values.astype(int)
    if sig == "SELF":
        return (g.self_R.values <= -1.0 * m + 1e-12).astype(int)
    if sig == "FSTOP":
        return (g.fam_stops.values >= {0.8: 2, 1.0: 3, 1.2: 4}[m]).astype(int)
    raise KeyError(sig)


STATES = {s: [-1, 0, 1] for s in DIR + ["RVOL", "PDT"]}; STATES["DOW"] = [0, 1, 2, 3, 4]

# ------------------------------------------------------------------ TRAIN fits (F family, P per-setup fingerprint)
TR = G[(G.split == "TRAIN")].copy()
FIT_F, FIT_P, FP_LAB = {}, {}, []
for sig in STATES:
    TR["st"] = state(sig, TR)
    fam_mean = TR.groupby("fam").R.sum() / TR.groupby("fam").n.sum()
    fs = TR.groupby(["fam", "st"]).agg(R=("R", "sum"), n=("n", "sum")); fs["mean"] = fs.R / fs.n.clip(lower=1)
    TR["exc"] = TR.R - TR.n * TR.fam.map(fam_mean)
    for fam, gf in TR.groupby("fam"):
        best = None
        for s_ in STATES[sig]:
            x = gf[(gf.st == s_) & (gf.n > 0)]
            if x.n.sum() == 0:
                continue
            ed = x.groupby("date").exc.sum(); nd = len(ed)
            t = ed.mean() / (ed.std(ddof=1) / math.sqrt(nd)) if nd > 2 and ed.std() > 0 else 0
            mu = x.R.sum() / x.n.sum()
            if mu < 0 and mu <= fam_mean[fam] - 0.05 and t <= -1.0 and nd >= 30 and (best is None or mu < best[1]):
                best = (s_, mu)
        FIT_F[(sig, fam)] = best[0] if best else None
    for su, gs in TR.groupby("setup"):
        fam = gs.fam.iloc[0]; mu_s = gs.R.sum() / max(gs.n.sum(), 1)
        ms = {}
        for s_ in STATES[sig]:
            x = gs[gs.st == s_]; fm = fs["mean"].get((fam, s_), 0.0)
            ms[s_] = (x.R.sum() + 100 * fm) / (x.n.sum() + 100)
        w_ = min(ms, key=ms.get)
        FIT_P[(sig, su)] = w_ if (ms[w_] < 0 and ms[w_] <= mu_s - 0.05) else None
        FP_LAB.append(dict(signal=sig, setup=su, best=max(ms, key=ms.get), worst=w_, **{f"m{k}": v for k, v in ms.items()}))
FP_LAB = pd.DataFrame(FP_LAB)


# ------------------------------------------------------------------ configs
def configs():
    C = []
    for sig in DIR:
        for mt in "UFP":
            for a in ("OFF", "HALF"):
                C.append((sig, mt, a))
    for sig, ms in (("RVOL", "UFP"), ("PDT", "FP"), ("DOW", "FP"), ("SELF", "U"), ("FSTOP", "U"), ("FOMC", "U")):
        for mt in ms:
            for a in ("OFF", "HALF"):
                C.append((sig, mt, a))
    return C


CFGS = configs(); assert len(CFGS) == 74, len(CFGS)


def switched(sig, mt, g, m=1.0, mode="re", single=None):
    st = state(sig, g, m); side = g.side.values
    if mt == "U":
        if sig in DIR:
            sw = ((side < 0) & (st == 1)) | ((side > 0) & (st == -1))
        elif sig == "RVOL":
            sw = st == -1
        else:
            sw = st == 1
    elif mt == "F":
        tgt = g.fam.map(lambda f: FIT_F.get((sig, f))).values
        sw = np.array([t is not None and not (isinstance(t, float) and np.isnan(t)) and s == t for s, t in zip(st, tgt)])
    else:
        tgt = g.setup.map(lambda s: FIT_P.get((sig, s))).values
        sw = np.array([t is not None and not (isinstance(t, float) and np.isnan(t)) and s == t for s, t in zip(st, tgt)])
    sw = np.asarray(sw, bool)
    if single is not None:                 # one decision only, at DT[single]; earlier buckets ON
        k = (g.unit + "|" + g.date).values
        at = pd.Series(np.where(g.b.values == single, sw, False)).groupby(k).transform("max").values
        sw = np.where(g.b.values >= single, at, False)
    elif mode == "sticky":
        k = (g.unit + "|" + g.date).values
        sw = pd.Series(sw.astype(int)).groupby(k).cummax().values.astype(bool)
    return sw


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan


def metrics(g, w):
    """g: grid rows of one split; w: weights. Returns metric dict + per-setup frame."""
    d = g.R.values * (w - 1); dsw = d * g.sw.values
    sd = g.unit.values + "|" + g.date.values
    base_sd = pd.Series(g.R.values).groupby(sd).sum(); d_sd = pd.Series(d).groupby(sd).sum()
    red = base_sd < 0; grn = base_sd > 0
    day = pd.Series(dsw).groupby(g.date.values).sum()
    dayraw = pd.Series(d).groupby(g.date.values).sum()
    baseday = pd.Series(g.R.values).groupby(g.date.values).sum()
    after = baseday + dayraw
    swm = (w < 1) & (g.n.values > 0)
    ps = pd.DataFrame(dict(setup=g.setup.values, fam=g.fam.values, R=g.R.values, d=d, aff=swm, sR=np.where(swm, g.R.values, 0),
                           sn=np.where(swm, g.n.values, 0), kR=np.where(swm, 0, g.R.values), kn=np.where(swm, 0, g.n.values))).groupby("setup").agg(
        fam=("fam", "first"), base=("R", "sum"), dR=("d", "sum"), aff=("aff", "max"), sR=("sR", "sum"), sn=("sn", "sum"), kR=("kR", "sum"), kn=("kn", "sum"))
    q = ps[(ps.sn >= 10) & (ps.kn >= 10)]
    sel_good = int((q.sR / q.sn < q.kR / q.kn).sum()); sel_bad = int((q.sR / q.sn > q.kR / q.kn).sum())
    a = ps[ps.aff]
    lim = np.maximum(5, 0.1 * a.base.abs())
    fam = ps[ps.aff].groupby("fam").dR.sum()
    sw = (w < 1) & (g.n.values > 0)
    nsw = g.n.values[sw].sum(); nk = g.n.values[~sw].sum()
    return dict(dR=d.sum(), dR_sw=dsw.sum(), base=g.R.sum(), t=tstat(day.values),
                red_cut=-d_sd[red].sum() / abs(base_sd[red].sum()) * 100 if red.any() else np.nan,
                green_given=-d_sd[grn].sum() / base_sd[grn].sum() * 100 if grn.any() else np.nan,
                sw_trades=int(nsw), sw_share=nsw / max(nsw + nk, 1), avgR_switched=g.R.values[sw].sum() / nsw if nsw else np.nan,
                avgR_kept=g.R.values[~sw].sum() / nk if nk else np.nan,
                aff=len(a), better=int((a.dR > 0).sum()), worse=int((a.dR < 0).sum()), worst_setup=a.dR.min() if len(a) else np.nan,
                worse_gtX=int((a.dR < -lim).sum()), fam_better=int((fam > 0).sum()), fam_worse=int((fam < 0).sum()),
                worst_day_base=baseday.min(), worst_day=after.min(), dR_wo_best=dayraw.sum() - dayraw.max(),
                best_day_share=dayraw.max() / dayraw.sum() if dayraw.sum() > 0 else np.nan,
                sel_good=sel_good, sel_bad=sel_bad), ps


# random baseline: permute each unit's day schedules within the split
def rand_base(g, w):
    res = np.zeros((NPERM, 2))
    for u, idx in g.groupby("unit").indices.items():
        R = g.R.values[idx].reshape(-1, NB); W = w[idx].reshape(-1, NB); sw_ = g.sw.values[idx[0]]
        nd = R.shape[0]
        for k in range(NPERM):
            pm = RNG.permutation(nd)
            x = (R * (W[pm] - 1)).sum()
            res[k, 0] += x; res[k, 1] += x * sw_
    return np.percentile(res[:, 0], 95), np.percentile(res[:, 1], 95), res[:, 0].mean()


SP = {s: G[G.split == s].reset_index(drop=True) for s in SPLITS}
rows, persetup = [], []
for (sig, mt, a) in CFGS:
    rec = dict(cfg=f"{sig}-{mt}-{a}", signal=sig, match=mt, action=a)
    for spn, g in SP.items():
        sw = switched(sig, mt, g); w = np.where(sw, 0.0 if a == "OFF" else 0.5, 1.0)
        m, ps = metrics(g, w)
        for k, v in m.items():
            rec[f"{spn}_{k}"] = v
        if spn in ("VALID", "FWD", "LIVE"):
            r95, r95w, rmean = rand_base(g, w)
            rec[f"{spn}_rand95"], rec[f"{spn}_rand95_sw"], rec[f"{spn}_rand_mean"] = r95, r95w, rmean
        ps = ps.reset_index(); ps["cfg"] = rec["cfg"]; ps["split"] = spn; persetup.append(ps)
    rows.append(rec)
    p(f"{rec['cfg']:<16} V dR {rec['VALID_dR']:+8.1f} (sw {rec['VALID_dR_sw']:+7.2f}, t {rec['VALID_t']:+.2f}, rand95 {rec['VALID_rand95']:+.1f}) "
      f"F dR {rec['FWD_dR']:+7.1f} (rand95 {rec['FWD_rand95']:+.1f})  LIVE {rec['LIVE_dR']:+7.1f}  "
      f"V better/worse {rec['VALID_better']}/{rec['VALID_worse']}  sw% {rec['VALID_sw_share']*100:.0f}")
R = pd.DataFrame(rows).copy()
for spn in ("VALID", "FWD", "LIVE"):
    R[f"{spn}_excess"] = R[f"{spn}_dR"] - R[f"{spn}_rand_mean"]
PS = pd.concat(persetup, ignore_index=True)


def verdict(r):
    c1 = all(r[f"{s}_dR"] > 0 and r[f"{s}_dR_sw"] > 0 for s in ("VALID", "FWD"))
    c2 = r.VALID_t >= BAR
    c3 = r.VALID_aff > 0 and r.VALID_better / r.VALID_aff >= 0.6 and r.VALID_worse_gtX == 0
    c4 = all(r[f"{s}_dR"] > r[f"{s}_rand95"] and r[f"{s}_dR_sw"] > r[f"{s}_rand95_sw"] for s in ("VALID", "FWD"))
    c5 = r.VALID_dR_wo_best > 0
    c7 = r.LIVE_dR >= 0
    return pd.Series(dict(c1_valid_fwd_pos=c1, c2_t=c2, c3_setups=c3, c4_beats_random=c4, c5_wo_best=c5, c7_live=c7))


R = pd.concat([R, R.apply(verdict, axis=1)], axis=1)

# ------------------------------------------------------------------ finalists: sensitivities (capped at 26 configs)
R["pre6"] = R[["c1_valid_fwd_pos", "c3_setups", "c4_beats_random", "c5_wo_best"]].sum(axis=1)
fin = R.sort_values(["pre6", "VALID_t"], ascending=False).head(5)
sens, nsens = [], 0
for _, r in fin.iterrows():
    sig, mt, a = r.signal, r.match, r.action
    var = []
    if sig not in ("CMP", "CMPL", "DOW", "FOMC"):
        var += [("x0.8", dict(m=0.8)), ("x1.2", dict(m=1.2))]
    var += [("sticky", dict(mode="sticky")), ("only10:00", dict(single=1)), ("only12:00", dict(single=4))]
    for nm, kw in var:
        nsens += 1
        rec = dict(cfg=r.cfg, variant=nm)
        for spn in ("VALID", "FWD", "LIVE"):
            g = SP[spn]; sw = switched(sig, mt, g, **kw); w = np.where(sw, 0.0 if a == "OFF" else 0.5, 1.0)
            m, _ = metrics(g, w)
            rec.update({f"{spn}_dR": m["dR"], f"{spn}_dR_sw": m["dR_sw"], f"{spn}_t": m["t"], f"{spn}_better": m["better"], f"{spn}_worse": m["worse"]})
        sens.append(rec)
SENS = pd.DataFrame(sens)
assert 74 + nsens <= N_BAR
c6 = {}
for cfg, g in SENS[SENS.variant.isin(["x0.8", "x1.2"])].groupby("cfg"):
    c6[cfg] = bool((g.VALID_dR > 0).all())
R["c6_thresholds"] = R.cfg.map(lambda c: c6.get(c, np.nan if c in set(fin.cfg) else None))
R["PASS"] = R.c1_valid_fwd_pos & R.c2_t & R.c3_setups & R.c4_beats_random & R.c5_wo_best & R.c7_live & (R.c6_thresholds != False)  # noqa: E712
R["near_miss"] = (~R.PASS) & R.c1_valid_fwd_pos & R.c3_setups & R.c4_beats_random & R.c5_wo_best & (
    (~R.c2_t & R.c7_live) | (R.c2_t & ~R.c7_live))
R.to_csv(HERE / "configs.csv", index=False, float_format="%.4f")
SENS.to_csv(HERE / "sensitivity.csv", index=False, float_format="%.4f")
PS.to_csv(HERE / "per_setup.csv.gz", index=False, float_format="%.3f")
p(f"\nconfigs scored: {len(CFGS)} main + {nsens} sensitivity = {len(CFGS) + nsens} (bar uses N {N_BAR}: t >= {BAR:.2f})")
p("PASS:", R[R.PASS].cfg.tolist(), " near-miss:", R[R.near_miss].cfg.tolist())
p(SENS.to_string(index=False, float_format=lambda v: f"{v:+.2f}"))

# ------------------------------------------------------------------ REGX stability (per-setup fingerprint labels)
stab = []
for spn in ("VALID", "LIVE"):
    g = SP[spn].copy()
    for sig in STATES:
        g["st"] = state(sig, g)
        for su, gs in g.groupby("setup"):
            ms = {}
            for s_ in STATES[sig]:
                x = gs[gs.st == s_]
                if x.n.sum() >= (30 if spn == "VALID" else 10):
                    ms[s_] = x.R.sum() / x.n.sum()
            tr = FP_LAB[(FP_LAB.signal == sig) & (FP_LAB.setup == su)]
            if len(ms) < 2 or not len(tr):
                continue
            tr = tr.iloc[0]
            trm = {s_: tr[f"m{s_}"] for s_ in ms}
            stab.append(dict(split=spn, signal=sig, setup=su, n_states=len(ms), train_best=max(trm, key=trm.get), train_worst=min(trm, key=trm.get),
                             best=max(ms, key=ms.get), worst=min(ms, key=ms.get),
                             rho=pd.Series(trm).corr(pd.Series(ms), method="spearman") if len(ms) >= 3 else np.nan))
ST = pd.DataFrame(stab)
ST["best_same"] = ST.best == ST.train_best; ST["worst_same"] = ST.worst == ST.train_worst
ST.to_csv(HERE / "regx_stability.csv", index=False, float_format="%.3f")
SUM = ST.groupby(["split", "signal"]).agg(setups=("setup", "size"), best_same=("best_same", "mean"), worst_same=("worst_same", "mean"),
                                          chance=("n_states", lambda v: (1 / v).mean()), rho=("rho", "mean")).reset_index()
SUM.to_csv(HERE / "regx_summary.csv", index=False, float_format="%.3f")
p("\n## REGX stability: share of setups whose TRAIN best / worst state is also best / worst in VALID / LIVE")
p(SUM.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
(HERE / "fits_F.csv").write_text("signal,family,state_switched\n" + "\n".join(f"{k[0]},{k[1]},{v}" for k, v in FIT_F.items()) + "\n")
(HERE / "fits_P.csv").write_text("signal,setup,state_switched\n" + "\n".join(f"{k[0]},{k[1]},{v}" for k, v in FIT_P.items()) + "\n")
FP_LAB.to_csv(HERE / "fingerprints_train.csv", index=False, float_format="%.4f")
(HERE / "score_out.txt").write_text("\n".join(out) + "\n")
