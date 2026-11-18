"""U7 Workbench at scale: one tune per setup chosen on fit sessions, verdict on later (check) sessions. See PLAN.md."""
import math, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u7"
x = pd.read_pickle(f"{S}/prep.pkl"); P = pd.read_pickle(f"{S}/paths.pkl"); top = open(f"{S}/top20.txt").read().split()
FEATS = ["emin", "risk_pct", "ext", "vwd", "gap", "rvol", "stopcost"]
NV = 20; BAR = max(1.5, math.sqrt(2 * math.log(NV)))
rng = np.random.default_rng(20261118)

def thr(px): return max(0.01, 3e-4 * px)
def flatc(px): return max(0.01, 1e-4 * px) + 0.01

def raw(r):
    """1-min path in the journal's (unadjusted) price units: Alpaca bars are split-adjusted, so a later split (e.g. ITA)
    shows as a jump vs the live entry; rescale when the last close before entry differs from the entry by > 3%."""
    Pp = P.get((r.date, r.symbol))
    if Pp is None: return None
    k = max(np.searchsorted(Pp["m"], int(r.emin)) - 1, 0); q = r.entry / Pp["c"][k]
    if abs(math.log(q)) <= 0.03: return Pp
    return dict(Pp, o=Pp["o"] * q, h=Pp["h"] * q, l=Pp["l"] * q, c=Pp["c"] * q)

def exit_variant(r, tgtR=None, tstop=None):
    """Earlier exit only: walk bars after entry up to the live exit. Returns R after costs."""
    Pp = raw(r)
    if Pp is None: return r.R
    rps = abs(r.entry - r.stop); em = r.emin
    xm = (r.xt.hour * 60 + r.xt.minute) - 570 + r.xt.second / 60 if r.xt.strftime("%Y-%m-%d") == r.date else 385.0
    xm = min(xm, 385.0)
    T = r.entry + r.side * tgtR * rps if tgtR else None
    for m, h, l, c in zip(Pp["m"], Pp["h"], Pp["l"], Pp["c"]):
        if m < math.ceil(em) or m + 1 > xm: continue
        if T is not None and ((r.side > 0 and h >= T + thr(T)) or (r.side < 0 and l <= T - thr(T))):
            return (r.pnl_adj + r.side * (T - r.exit) * r.shares) / r.risk
        if tstop is not None and m + 1 >= em + tstop:
            return (r.pnl_adj + (r.side * (c - r.exit) - flatc(c)) * r.shares) / r.risk
    return r.R

def sim(r, u, tgtR, tstop):
    """Simplified engine (same for real and random entries): entry at open of minute u."""
    Pp = raw(r)
    if Pp is None: return np.nan
    m = Pp["m"]; k = np.searchsorted(m, u)
    if k >= len(m) or m[k] > 385: return np.nan
    e0 = Pp["o"][k]; e = e0 + r.side * (max(0.01, 1e-4 * e0) + 1e-4 * e0)
    rps = abs(r.entry - r.stop); st = e0 - r.side * rps
    T = e0 + r.side * tgtR * rps if tgtR and tgtR == tgtR else None
    for j in range(k, len(m)):
        o, h, l, c = Pp["o"][j], Pp["h"][j], Pp["l"][j], Pp["c"][j]
        if (r.side > 0 and l <= st) or (r.side < 0 and h >= st):
            px = (min(o, st) if r.side > 0 else max(o, st)) - r.side * (max(0.02, 4e-4 * st) + 0.01)
            return r.side * (px - e) / rps
        if T is not None and ((r.side > 0 and h >= T + thr(T)) or (r.side < 0 and l <= T - thr(T))):
            return r.side * (T - e) / rps
        if (tstop is not None and m[j] + 1 >= m[k] + tstop) or m[j] >= 385:
            return r.side * (c - r.side * flatc(c) - e) / rps
    return r.side * (Pp["c"][-1] - r.side * flatc(Pp["c"][-1]) - e) / rps

def stats(df, col):
    if len(df) == 0: return dict(n=0, days=0, tot=0.0, avg=np.nan, wob=np.nan, bsh=np.nan, worst=np.nan)
    d = df.groupby("date")[col].sum(); bd = d.idxmax(); nb = (df.date == bd).sum()
    wob = (d.sum() - d.max()) / (len(df) - nb) if len(df) > nb else np.nan
    return dict(n=len(df), days=len(d), tot=d.sum(), avg=df[col].mean(), wob=wob,
                bsh=d.max() / d.sum() if d.sum() > 0 else np.nan, worst=d.min())

out, cand_rows = [], []
for s in top:
    g = x[x.strategy == s].sort_values("et").copy()
    days = sorted(g.date.unique()); nf = math.ceil(len(days) / 2)
    fitd, chkd = set(days[:nf]), set(days[nf:])
    full = stats(g, "R"); proven = full["avg"] > 0 and full["wob"] > 0
    fit = g[g.date.isin(fitd)]; chk = g[g.date.isin(chkd)]
    hasT = g.tR.notna().mean() > 0.5 and (g.exit_reason == "target").any()
    cands = []
    if proven:
        for k in ([0.5, 0.75] if hasT else [1.0, 1.5, 2.0]):
            cands.append(("exit", f"target {k}x parent target" if hasT else f"target {k}R", dict(tg=k, rel=hasT)))
        for n in (30, 60, 120): cands.append(("exit", f"time stop {n} min", dict(ts=n)))
        cands.append(("gate", "refire off", dict(refire=True)))
    else:
        for f in FEATS:
            q33, q67 = fit[f].quantile([1 / 3, 2 / 3])
            cands.append(("gate", f"{f} >= {q33:.4g} (drop bottom third)", dict(f=f, lo=q33)))
            cands.append(("gate", f"{f} <= {q67:.4g} (drop top third)", dict(f=f, hi=q67)))
        cands.append(("gate", "refire off", dict(refire=True)))
    def apply(df, kind, p):
        df = df.copy()
        if kind == "gate":
            if p.get("refire"): keep = df.nth == 1
            elif "lo" in p: keep = df[p["f"]] >= p["lo"]
            else: keep = df[p["f"]] <= p["hi"]
            df["V"] = np.where(keep.fillna(True), df.R, np.nan)   # a missing feature never blocks
        else:
            tg = (lambda r: p["tg"] * r.tR) if p.get("rel") else (lambda r: p.get("tg"))
            df["V"] = [exit_variant(r, tg(r) if "tg" in p else None, p.get("ts")) for r in df.itertuples()]
        return df
    pf = fit.R.sum(); best = None
    for kind, label, p in cands:
        fv = apply(fit, kind, p); kept = fv.V.notna().sum()
        ok = kind == "exit" or (kept >= 0.5 * len(fv) and kept >= 5)
        cand_rows.append(dict(setup=s, kind=kind, tune=label, fit_n=kept, fit_tot=round(fv.V.sum(), 2), parent_fit_tot=round(pf, 2), eligible=ok))
        if ok and fv.V.sum() > pf + 1e-9 and (best is None or fv.V.sum() > best[3]): best = (kind, label, p, fv.V.sum())
    row = dict(setup=s, proven=proven, menu="X (exit/frequency)" if proven else "G (one gate)", n_cands=len(cands),
               fit_days=len(fitd), chk_days=len(chkd), parent_fit_tot=round(pf, 2), parent_fit_avg=fit.R.mean())
    pc = stats(chk, "R"); row.update({f"parent_chk_{k}": v for k, v in pc.items()})
    if best is None:
        row.update(tune="none found (no candidate beat the parent on fit)", verdict="FAIL (no tune)"); out.append(row); continue
    kind, label, p, ft = best
    row.update(tune=label, tune_kind=kind, var_fit_tot=round(ft, 2))
    cv = apply(chk, kind, p); vv = cv[cv.V.notna()]
    vc = stats(vv.assign(R=vv.V), "R"); row.update({f"var_chk_{k}": v for k, v in vc.items()})
    dp = chk.groupby("date").R.sum(); dv = cv.groupby("date").V.sum().reindex(dp.index).fillna(0)
    diff = dv - dp; tdiff = diff.mean() / diff.std(ddof=1) * math.sqrt(len(diff)) if len(diff) > 1 and diff.std(ddof=1) > 0 else np.nan
    row.update(chk_diff_tot=diff.sum(), chk_diff_t=tdiff)
    # random-subset control (gates)
    pct = np.nan
    if kind == "gate" and len(vv):
        kd = cv.groupby("date").V.apply(lambda v: v.notna().sum()); draws = []
        Rd = {d: chk[chk.date == d].R.to_numpy() for d in kd.index}
        for _ in range(2000):
            tot = sum(rng.choice(Rd[d], kd[d], replace=False).sum() for d in kd.index if kd[d] > 0)
            draws.append(tot / kd.sum())
        pct = (np.array(draws) < vv.V.mean()).mean()
    row["rand_subset_pct"] = pct
    # random entries vs real entries, simplified engine, variant's exit rule
    span = (int(g.emin.min()), int(g.emin.max()))
    tgf = (lambda r: p["tg"] * r.tR if p.get("rel") else p["tg"]) if "tg" in p else (lambda r: r.tR if hasT else None)
    real, rnd = [], []
    for r in vv.itertuples():
        real.append(sim(r, math.ceil(r.emin), tgf(r), p.get("ts")))
        for _ in range(5): rnd.append(sim(r, int(rng.integers(span[0], span[1] + 1)), tgf(r), p.get("ts")))
    row.update(sim_real=np.nanmean(real) if real else np.nan, sim_rand=np.nanmean(rnd) if rnd else np.nan)
    c1 = vc["avg"] >= pc["avg"] + 0.02 and vc["avg"] > 0
    c2 = vc["wob"] == vc["wob"] and vc["wob"] > 0 and (vc["bsh"] < 0.5)
    c3 = vc["worst"] >= pc["worst"] - 0.1 * abs(pc["worst"])
    c4 = tdiff == tdiff and tdiff >= BAR
    c5 = (row["sim_real"] > row["sim_rand"]) and (kind == "exit" or pct >= 0.8)
    c6 = vc["days"] >= 4 and vc["n"] >= 15
    row.update(c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6)
    row["verdict"] = "PASS" if all([c1, c2, c3, c4, c5, c6]) else ("LEAD (not proposed)" if c1 and c2 else "FAIL")
    out.append(row)
R = pd.DataFrame(out); C = pd.DataFrame(cand_rows)
NALL = len(C); print("configs tried", NALL, "bar_v", round(BAR, 2), "bar_all", round(max(1.5, math.sqrt(2 * math.log(NALL))), 2))
R.to_csv(f"{S}/u7_results.csv", index=False); C.to_csv(f"{S}/u7_candidates.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 45)
print(R[["setup", "menu", "tune", "parent_chk_n", "parent_chk_avg", "var_chk_n", "var_chk_avg", "var_chk_wob", "var_chk_bsh", "chk_diff_tot", "chk_diff_t", "rand_subset_pct", "sim_real", "sim_rand", "verdict"]].round(3).to_string())
print(R[["setup","c1","c2","c3","c4","c5","c6"]].to_string())
