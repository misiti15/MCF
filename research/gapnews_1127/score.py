"""GAPNEWS_1127 score: direction screen inside the frozen K6 high-mover list (13 rules), 3 directional setups and the
N1/N2 OCO bracket, LIVE-L + LR8 costs, random-direction and size-matched controls, stress, one-big-day, family split.
Usage: python score.py WORK. Writes results.json + score_out.txt next to this file. Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/primshorts_1126"))
from mcf.research.gates import tod_cost_mult  # noqa: E402
import calib_live as CL  # noqa: E402

W = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
CELLS = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))
ETB = pd.read_csv("/home/user/MCF/data/universe.csv").set_index("symbol").easy_to_borrow.astype(bool).to_dict()
K6_FROZEN = json.load(open(ROOT / "research/movehunt_1127/results.json"))["logit_coef"]
FEATS = ["gap", "rvol", "rng", "mv", "idio", "pdr", "dv", "atrp"]
ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH", "XBI", "KRE"]
PERS = ("FIT", "CHECK", "T2", "EARLY")
RNG = np.random.default_rng(112702)
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    if "2022-10-01" <= d <= "2022-12-31":
        return "EARLY"
    return "none"


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def etf_map(raw):
    """point-in-time sector ETF per symbol-day: max corr of daily returns over the prior 60 sessions (per era)."""
    out = []
    for era, g in raw.groupby("era"):
        R = g.pivot_table(index="date", columns="symbol", values="cc_ret").sort_index()
        best, bestc = None, None
        for e in ETFS:
            if e not in R:
                continue
            c = R.rolling(60, min_periods=40).corr(R[e]).shift(1)
            if e in c:
                c[e] = np.nan
            if best is None:
                best = pd.DataFrame(e, index=c.index, columns=c.columns)
                bestc = c.fillna(-9)
            else:
                m = c.fillna(-9) > bestc
                best = best.mask(m, e)
                bestc = bestc.where(~m, c.fillna(-9))
        best = best.where(bestc > -9)
        s = best.stack().rename("etf").reset_index()
        out.append(s)
    return pd.concat(out, ignore_index=True)


def load():
    raw = pd.concat([pd.read_parquet(W / "days_t1.parquet"), pd.read_parquet(W / "days_t2.parquet")], ignore_index=True)
    no_locked(raw.date.unique())
    em = etf_map(raw)
    raw["r20"] = raw.p50 / raw.open - 1
    er = raw[raw.symbol.isin(ETFS)][["date", "symbol", "r20"]].rename(columns={"symbol": "etf", "r20": "etf_r20"})
    x = raw.copy()
    x["per"] = x.date.map(period)
    x = x[x.per != "none"].copy()
    x = x.merge(em, on=["date", "symbol"], how="left").merge(er, on=["date", "etf"], how="left")
    spy = x[x.symbol == "SPY"].set_index("date")
    x["spy_r20"] = x.date.map(spy.p50 / spy.open - 1)
    lastmax = x.groupby("date").last_mm.transform("max")
    ok = (x.p50 >= 5) & (x.adv20 >= 20e6) & x.atr.gt(0) & (x.n20 >= 15) & x.open.notna() & x.prev_close.notna() \
        & (x.last_mm >= lastmax - 5) & x.v20_med.gt(0) & x.spy_r20.notna()
    x = x[ok].copy()
    x["atrp"] = x.atr / x.prev_close
    x["gap_s"] = x.open / x.prev_close - 1
    x["gap"] = x.gap_s.abs() / x.atrp
    x["rvol"] = x.v20 / x.v20_med
    x["rng"] = (x.h20 - x.l20) / x.atr
    x["mv"] = (x.p50 - x.open).abs() / x.atr
    x["idio"] = (x.r20 - x.spy_r20).abs() / x.atrp
    x["pdr"] = x.pdr_raw / x.atr
    x["dv"] = np.log(x.adv20)
    x["M"] = (x.d_close - x.p50).abs() / x.atr
    x["ymv"] = (x.d_close - x.p50) / x.atr          # signed remaining move (target only)
    x["D"] = np.sign(x.p50 - x.open)
    g = x.groupby("date")
    x["n_el"] = g.symbol.transform("size")
    x["ntop"] = np.maximum(1, np.round(0.02 * x.n_el)).astype(int)
    x["top_M"] = g["M"].rank(ascending=False, method="first") <= x.ntop
    # direction features
    x["orpos"] = ((x.p50 - x.l20) / (x.h20 - x.l20)).where(x.h20 > x.l20, 0.5)
    x["rs_sec"] = (x.r20 - x.etf_r20) / x.atrp
    x["vw"] = (x.p50 - x.vwap20) / x.atr
    return x.reset_index(drop=True)


def add_k6(x):
    Z = np.column_stack([np.log1p(x[f].clip(lower=0)) if f != "dv" else x[f] for f in FEATS])
    fit = (x.per == "FIT").to_numpy()
    mu, sd = Z[fit].mean(0), Z[fit].std(0)
    Z = (Z - mu) / sd
    m = LogisticRegression(max_iter=2000, C=1.0).fit(Z[fit], x.top_M[fit])
    coef = dict(zip(FEATS, np.round(m.coef_[0], 3)))
    for k in FEATS:
        assert abs(coef[k] - K6_FROZEN[k]) <= 0.0015, f"K6 does not reproduce MOVEHUNT: {k} {coef[k]} vs {K6_FROZEN[k]}"
    x["K6"] = m.decision_function(Z)
    x["k6rank"] = x.groupby("date").K6.rank(ascending=False, method="first")
    return x, coef


DFEATS = ["f_gap", "f_mv", "f_or", "f_rs", "f_pcl", "f_vw", "f_vimb", "f_r5", "f_r20", "f_gxd"]


def add_rules(x):
    x["f_gap"] = x.gap_s / x.atrp
    x["f_mv"] = (x.p50 - x.open) / x.atr
    x["f_or"] = x.orpos - 0.5
    x["f_rs"] = x.rs_sec
    x["f_pcl"] = x.pcl - 0.5
    x["f_vw"] = x.vw
    x["f_vimb"] = x.vimb
    x["f_r5"] = x.r5 / x.atrp
    x["f_r20"] = x.r20d / x.atrp
    x["f_gxd"] = np.sign(x.gap_s) * x.D
    sg = lambda c: np.sign(x[c]).fillna(0)  # noqa: E731
    x["R1"] = np.sign(x.gap_s)
    x["R2"] = x.D
    x["R3"] = np.where(np.sign(x.gap_s) == x.D, x.D, 0)
    x["R4"] = np.where((np.sign(x.gap_s) != x.D) & (x.gap_s != 0), x.D, 0)
    x["R5"] = sg("f_or")
    x["R6"] = sg("f_rs")
    x["R7"] = sg("f_pcl")
    x["R8"] = sg("f_vw")
    x["R9"] = sg("f_vimb")
    x["R10"] = sg("f_r5")
    x["R11"] = sg("f_r20")
    x["R12"] = np.sign(x[["R1", "R2", "R5", "R6", "R7", "R8", "R9", "R10", "R11"]].sum(1))
    # R13 DLOGIT fit on FIT top-50 list only
    ok = x[DFEATS].notna().all(1)
    clip = lambda Z: np.clip(Z, -5, 5)  # noqa: E731
    fm = ((x.per == "FIT") & (x.k6rank <= 50) & ok).to_numpy()
    Z = x[DFEATS].fillna(0).to_numpy(float)
    mu, sd = Z[fm].mean(0), Z[fm].std(0)
    Z = clip((Z - mu) / sd)
    m = LogisticRegression(max_iter=2000, C=1.0).fit(Z[fm], (x.ymv[fm] > 0))
    p = m.predict_proba(Z)[:, 1]
    x["dl_p"] = np.where(ok, p, np.nan)
    x["R13"] = np.sign(x.dl_p - 0.5).fillna(0)
    thr = float(np.nanquantile(np.abs(x.dl_p[(x.per == "FIT") & (x.k6rank <= 20)] - 0.5), 2 / 3))
    return x, dict(zip(DFEATS, np.round(m.coef_[0], 3))), thr


def cl_stats(v, dates):
    """mean, day-clustered t."""
    v = pd.Series(np.asarray(v, float))
    d = pd.Series(np.asarray(dates))
    if len(v) < 3:
        return float(v.mean()) if len(v) else float("nan"), float("nan")
    m = float(v.mean())
    e = (v - m).groupby(d.values).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(v)
    return m, (m / se if se > 0 else float("nan"))


def day_t(v):
    v = np.asarray(v, float)
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std() > 0 else float("nan")


def screen(x):
    res = {}
    for R in [f"R{i}" for i in range(1, 14)]:
        e = {}
        for N in (50, 20):
            for p in PERS:
                s = x[(x.k6rank <= N) & (x.per == p) & (x[R] != 0)]
                y = s[R] * s.ymv
                m, t = cl_stats(y, s.date)
                e[f"{p}@{N}"] = {"n": int(len(s)), "mean_y": round(m, 4), "t": round(t, 2),
                                 "hit": round(float((y > 0).mean()), 3) if len(s) else None}
        orient = 1 if e["FIT@50"]["mean_y"] > 0 else -1
        e["orient"] = orient
        o = lambda k: (orient * e[k]["mean_y"], orient * e[k]["t"])  # noqa: E731
        e["skill"] = bool(o("CHECK@50")[0] > 0 and o("CHECK@50")[1] >= 3.0 and o("T2@50")[0] > 0 and o("T2@50")[1] >= 2.0)
        res[R] = e
        say(f"{R:4s} orient {orient:+d} | " + " | ".join(
            f"{p} y {orient * e[p + '@50']['mean_y']:+.4f} t {orient * e[p + '@50']['t']:+.2f} hit "
            f"{(e[p + '@50']['hit'] if orient > 0 else 1 - e[p + '@50']['hit']) if e[p + '@50']['hit'] is not None else None}"
            f" n {e[p + '@50']['n']}" for p in PERS) + f" | top20 CHECK {orient * e['CHECK@20']['mean_y']:+.4f} "
            f"T2 {orient * e['T2@20']['mean_y']:+.4f} | skill {e['skill']}")
    return res


def costs(t):
    risk = t.risk.to_numpy()
    mins = 570 + t.em.astype(int)
    tod = ((mins // 60) * 100 + mins % 60).to_numpy()
    tier = np.where((t.gap_s.abs() >= 0.20) | (t.entry < 5), 3.0, 1.0)
    ecost = (0.01 + t.entry * 1e-4) * tod_cost_mult(tod)
    xcost = 0.01 + t.px * 1e-4 + np.where(t.kind == 1, 0.02, 0.0)
    borrow = np.where(t.side < 0, 1.2e-4 * t.entry, 0.0)
    t["r_lr8"] = (t.r_gross * risk - tier * (ecost + xcost) - borrow) / risk
    kd = np.where(t.kind == 1, "stop", "market")
    t["r_live"] = t.r_gross - CL.predict_R(CELLS, t.entry.to_numpy(), risk, kd)
    t["r_bp2"] = t.r_live - 2e-4 * (t.entry + t.px) / risk
    return t


def mk(x, side, x_tag, lag, rows_mask=None):
    """trade frame for rows of x with side (+1/-1 array), exit x1/x2, entry lag 0/1."""
    sd = pd.Series(np.asarray(side), index=x.index)
    m = sd != 0 if rows_mask is None else (sd != 0) & rows_mask
    xs, sd = x[m], sd[m]
    L = sd > 0
    g = lambda f: np.where(L, xs[f"{x_tag}L{lag}_{f}"], xs[f"{x_tag}S{lag}_{f}"])  # noqa: E731
    t = pd.DataFrame({"date": xs.date.values, "per": xs.per.values, "symbol": xs.symbol.values, "side": sd.values,
                      "entry": g("e"), "stop": g("st"), "px": g("px"), "kind": g("k"), "em": xs.i0_mm.values + lag,
                      "gap_s": xs.gap_s.values, "atrp": xs.atrp.values, "both": 0}, index=xs.index)
    return finish(t)


def finish(t):
    t["risk"] = (t.entry - t.stop).abs()
    ok = t.px.notna() & t.entry.notna() & (t.risk >= 0.001 * t.entry) & (t.side * (t.entry - t.stop) > 0)
    ok &= (t.side > 0) | t.symbol.map(ETB).fillna(False).astype(bool)
    t = t[ok].copy()
    t["r_gross"] = np.where(t.both == 1, -1.0, t.side * (t.px - t.entry) / t.risk)
    t.loc[t.both == 1, "kind"] = 1
    return costs(t)


def mk_bracket(x, n_tag, lag):
    xs = x[x.nb_side.notna() & x[f"{n_tag}{lag}_e"].notna() & x.symbol.map(ETB).fillna(False).astype(bool)]
    t = pd.DataFrame({"date": xs.date.values, "per": xs.per.values, "symbol": xs.symbol.values, "side": xs.nb_side.values,
                      "entry": xs[f"{n_tag}{lag}_e"].values, "stop": xs[f"{n_tag}{lag}_st"].values,
                      "px": xs[f"{n_tag}{lag}_px"].values, "kind": xs[f"{n_tag}{lag}_k"].values,
                      "em": xs.nb_mm.values + lag, "gap_s": xs.gap_s.values, "atrp": xs.atrp.values,
                      "both": xs.nb_both.fillna(0).values}, index=xs.index)
    return finish(t)


def st(t, col, nses):
    if len(t) < 3:
        return {"n": int(len(t))}
    r = t[col]
    day = r.groupby(t.date).sum()
    tot = float(r.sum())
    best = day.idxmax()
    m, tt = cl_stats(r, t.date)
    return {"n": int(len(t)), "days": int(day.size), "avg": round(m, 4), "t_day": round(tt, 2),
            "wo_best": round(float(r[t.date != best].mean()), 4), "best_day": str(best),
            "best_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total": round(tot, 1),
            "per_session": round(tot / nses, 3), "win": round(float((r > 0).mean()), 3),
            "gross": round(float(t.r_gross.mean()), 4)}


def ctrl_dir(tl, tlong, tshort):
    """random-direction control: same names, coin-flip side = mean of long and short outcome (names with both sides)."""
    both = tlong.index.intersection(tshort.index).intersection(tl.index)
    if len(both) < 3:
        return {"n": int(len(both))}
    s = tl.loc[both]
    c = (tlong.loc[both, "r_live"] + tshort.loc[both, "r_live"]) / 2
    diff = (s.r_live - c).groupby(s.date).sum()
    return {"n": int(len(both)), "setup_avg": round(float(s.r_live.mean()), 4), "ctrl_avg": round(float(c.mean()), 4),
            "diff_avg": round(float((s.r_live - c).mean()), 4), "paired_t": round(day_t(diff), 2)}


def ctrl_size(tl, pool, col="r_live"):
    pk = pool.groupby("date")[col].agg(["mean", "size"])
    lk = tl.groupby("date")[col].agg(["sum", "size"])
    j = lk.join(pk, rsuffix="_p", how="inner")
    j = j[j["size_p"] >= j["size"]]
    if len(j) < 3:
        return {"days": int(len(j))}
    diff = j["sum"] - j["size"] * j["mean"]
    pv = {d: g[col].to_numpy() for d, g in pool.groupby("date")}
    draws = np.array([sum(RNG.choice(pv[d], int(k), replace=False).sum() for d, k in j["size"].items()) for _ in range(50)])
    ntr = j["size"].sum()
    return {"days": int(len(j)), "ctrl_avg": round(float((j["size"] * j["mean"]).sum() / ntr), 4),
            "diff_avg": round(float(diff.sum() / ntr), 4), "paired_t": round(day_t(diff), 2),
            "pct_draws_below": round(float((draws < j["sum"].sum()).mean()), 2)}


def family(t):
    ct = t[t.per.isin(["CHECK", "T2"])]
    fam = {}
    for fk, m in (("long", ct.side > 0), ("short", ct.side < 0), ("gap>=1atr", ct.gap_s.abs() / ct.atrp >= 1),
                  ("gap<1atr", ct.gap_s.abs() / ct.atrp < 1), ("px<20", ct.entry < 20),
                  ("px20-100", (ct.entry >= 20) & (ct.entry < 100)), ("px100+", ct.entry >= 100)):
        s = ct[m]
        fam[fk] = {"n": int(len(s)), "avg": round(float(s.r_live.mean()), 4) if len(s) else None}
    return fam


def evaluate(name, x, side_all, x_tag, top, nses, directional=True, n_tag=None):
    inl = (x.k6rank <= 20) & top
    if directional:
        t0, t1 = mk(x, side_all, x_tag, 0, inl), mk(x, side_all, x_tag, 1, inl)
        pool = mk(x, side_all, x_tag, 0, (x.k6rank > 20))
        tlong = mk(x, np.ones(len(x)), x_tag, 0, inl)
        tshort = mk(x, -np.ones(len(x)), x_tag, 0, inl)
    else:
        b0, b1 = mk_bracket(x, n_tag, 0), mk_bracket(x, n_tag, 1)
        t0, t1 = b0[b0.index.isin(x.index[inl])], b1[b1.index.isin(x.index[inl])]
        pool = b0[~b0.index.isin(x.index[x.k6rank <= 20])]
    e = {}
    for p in PERS:
        a = t0[t0.per == p]
        e[p] = {"live": st(a, "r_live", nses[p]), "lr8": st(a, "r_lr8", nses[p]), "bp2": st(a, "r_bp2", nses[p]),
                "lag1": st(t1[t1.per == p], "r_live", nses[p]),
                "long": st(a[a.side > 0], "r_live", nses[p]), "short": st(a[a.side < 0], "r_live", nses[p]),
                "ctrl_size": ctrl_size(a, pool[pool.per == p]) if p != "EARLY" else ctrl_size(a, pool[pool.per == p])}
        if directional:
            e[p]["ctrl_dir"] = ctrl_dir(a, tlong[tlong.per == p], tshort[tshort.per == p])
        if directional and p in ("CHECK", "T2"):
            e[p]["both_hit"] = round(float((a.r_gross > 0).mean()), 3) if len(a) else None
    e["family_check_t2"] = family(t0)
    C, T, E = e["CHECK"], e["T2"], e["EARLY"]
    g = {"pos_costs": all(z[k].get("avg", -1) > 0 for z in (C, T) for k in ("live", "lr8"))
         and (E["live"].get("n", 0) < 30 or E["live"].get("avg", -1) > 0),
         "t": (C["live"].get("t_day") or 0) >= 3.0 and (T["live"].get("t_day") or 0) >= 2.0,
         "one_big_day": all((z["live"].get("wo_best") or -1) > 0 and (z["live"].get("best_share") or 1) < 0.5 for z in (C, T)),
         "stress": all(z[k].get("avg", -1) > 0 for z in (C, T) for k in ("lag1", "bp2"))}
    if directional:
        g["control"] = (C["ctrl_dir"].get("diff_avg", -1) > 0 and (C["ctrl_dir"].get("paired_t") or 0) >= 2.0
                        and T["ctrl_dir"].get("diff_avg", -1) > 0)
    else:
        g["control"] = C["ctrl_size"].get("diff_avg", -1) > 0 and T["ctrl_size"].get("diff_avg", -1) > 0
    e["gates"], e["pass"] = g, all(g.values())
    for p in PERS:
        L, R8 = e[p]["live"], e[p]["lr8"]
        cd = e[p].get("ctrl_dir", {})
        cs = e[p]["ctrl_size"]
        say(f"{name:3s} {p:5s} n {L.get('n')} live {L.get('avg')} lr8 {R8.get('avg')} gross {L.get('gross')} t {L.get('t_day')} "
            f"woBest {L.get('wo_best')} bestSh {L.get('best_share')} R/ses {L.get('per_session')} | lag1 {e[p]['lag1'].get('avg')} "
            f"bp2 {e[p]['bp2'].get('avg')} | long {e[p]['long'].get('avg')} (n {e[p]['long'].get('n')}) short {e[p]['short'].get('avg')} "
            f"(n {e[p]['short'].get('n')}) | ctrlDir diff {cd.get('diff_avg')} pt {cd.get('paired_t')} | ctrlSize diff "
            f"{cs.get('diff_avg')} pt {cs.get('paired_t')}")
    say(f"{name:3s} gates {g} PASS={e['pass']} family {e['family_check_t2']}")
    return e


def main():
    x = load()
    x, coef = add_k6(x)
    x, dcoef, thr = add_rules(x)
    nses = x.groupby("per").date.nunique().to_dict()
    res = {"note": "Educational only - not financial advice. GAPNEWS_1127.", "sessions": nses, "k6_coef": coef,
           "dlogit_coef": dcoef, "sc_threshold_abs_p": round(thr, 4),
           "etf_map_coverage_top50": round(float(x[x.k6rank <= 50].etf_r20.notna().mean()), 3)}
    say("sessions", nses, "| K6 reproduced", coef, "| DLOGIT coef (FIT top-50)", dcoef, "| SC |p-.5| thr", round(thr, 4))
    say("ETF map coverage (top-50)", res["etf_map_coverage_top50"], "ETF counts",
        x[x.k6rank <= 50].etf.value_counts().head(14).to_dict())
    say("\n== direction screen on K6 top-50 (y = oriented remaining move / ATR; orientation fixed on FIT) ==")
    res["screen"] = screen(x)
    # cells: gap direction x first-20 continuation (descriptive, part of R3/R4)
    say("\n== gap x first-20 cells (top-50; y = D-signed remaining move) ==")
    cells = {}
    for p in PERS:
        s = x[(x.k6rank <= 50) & (x.per == p) & (x.D != 0) & (x.gap_s != 0)]
        for cn, m in (("gap_up_cont_up", (s.gap_s > 0) & (s.D > 0)), ("gap_up_rev_down", (s.gap_s > 0) & (s.D < 0)),
                      ("gap_dn_cont_dn", (s.gap_s < 0) & (s.D < 0)), ("gap_dn_rev_up", (s.gap_s < 0) & (s.D > 0))):
            q = s[m]
            mm, tt = cl_stats(q.D * q.ymv, q.date)
            cells[f"{p}|{cn}"] = {"n": int(len(q)), "y_follow_D": round(mm, 4), "t": round(tt, 2)}
        say(p, {k.split('|')[1]: v for k, v in cells.items() if k.startswith(p)})
    res["gap_cells"] = cells
    # setups
    fitt = {R: abs(res["screen"][R]["FIT@50"]["t"]) for R in [f"R{i}" for i in range(1, 12)]}
    sa_rule = max(fitt, key=fitt.get)
    res["SA_rule"] = sa_rule
    say(f"\nSA rule (max FIT |t| among R1..R11): {sa_rule} orient {res['screen'][sa_rule]['orient']:+d} (FIT t {fitt[sa_rule]:.2f})")
    allrows = pd.Series(True, index=x.index)
    o13 = res["screen"]["R13"]["orient"]
    say("\n== setups on K6 top-20 (LIVE-L | LR8) ==")
    res["setups"] = {
        "SA": evaluate("SA", x, x[sa_rule] * res["screen"][sa_rule]["orient"], "x1", allrows, nses),
        "SB": evaluate("SB", x, x.R13 * o13, "x1", allrows, nses),
        "SC": evaluate("SC", x, x.R13 * o13, "x2", (np.abs(x.dl_p - 0.5) >= thr), nses),
        "N1": evaluate("N1", x, None, None, allrows, nses, directional=False, n_tag="n1"),
        "N2": evaluate("N2", x, None, None, allrows, nses, directional=False, n_tag="n2"),
    }
    nb = x[(x.k6rank <= 20) & x.nb_side.notna()]
    res["bracket_both_same_bar_share"] = round(float(nb.nb_both.fillna(0).mean()), 4)
    res["bracket_trigger_rate_top20"] = round(float(x[x.k6rank <= 20].nb_side.notna().mean()), 3)
    say("bracket: trigger rate top-20", res["bracket_trigger_rate_top20"], "both-in-one-bar share", res["bracket_both_same_bar_share"])
    json.dump(res, open(H / "results.json", "w"), indent=1, default=float)
    (H / "score_out.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
