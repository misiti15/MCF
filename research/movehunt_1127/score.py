"""MOVEHUNT_1127 score: rankers (capture of the day's top-2% after-09:50 movers) and the S1/S2/S3 setups on the chosen
ranker's top-20 list, LIVE-L + LR8 costs, size-matched random control, one-big-day, family split.
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
FEATS = ["gap", "rvol", "rng", "mv", "idio", "pdr", "dv", "atrp"]
RNG = np.random.default_rng(1127)
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
    return "none"


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load():
    x = pd.concat([pd.read_parquet(W / "days_t1.parquet"), pd.read_parquet(W / "days_t2.parquet")], ignore_index=True)
    no_locked(x.date.unique())
    x["per"] = x.date.map(period)
    x = x[x.per != "none"].copy()
    # T1 and T2 share no dates (T1 starts 2024-09-16, T2 ends 2024-09-13); keep era per row
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
    x["r20"] = x.p50 / x.open - 1
    x["idio"] = (x.r20 - x.spy_r20).abs() / x.atrp
    x["pdr"] = x.pdr_raw / x.atr
    x["dv"] = np.log(x.adv20)
    x["M"] = (x.d_close - x.p50).abs() / x.atr
    x["M_oc"] = (x.d_close - x.open).abs() / x.atr
    x["M_mx"] = np.maximum(x.post_h - x.p50, x.p50 - x.post_l) / x.atr
    x["mdir"] = np.sign(x.d_close - x.p50)
    g = x.groupby("date")
    x["n_el"] = g.symbol.transform("size")
    x["ntop"] = np.maximum(1, np.round(0.02 * x.n_el)).astype(int)
    for k in ("M", "M_oc", "M_mx"):
        x[f"top_{k}"] = g[k].rank(ascending=False, method="first") <= x.ntop
    return x.reset_index(drop=True)


def add_rankers(x):
    pr = lambda c: x.groupby("date")[c].rank(pct=True)  # noqa: E731
    x["K1"], x["K2"], x["K3"], x["K4"] = x.rvol, x.gap, x.rng, x.pdr
    x["K5"] = (pr("rvol") + pr("gap") + pr("rng")) / 3
    x["K7"], x["K8"] = x.dv, x.atrp
    Z = np.column_stack([np.log1p(x[f].clip(lower=0)) if f not in ("dv",) else x[f] for f in FEATS])
    fit = (x.per == "FIT").to_numpy()
    mu, sd = Z[fit].mean(0), Z[fit].std(0)
    Z = (Z - mu) / sd
    m = LogisticRegression(max_iter=2000, C=1.0).fit(Z[fit], x.top_M[fit])
    x["K6"] = m.decision_function(Z)
    coef = dict(zip(FEATS, np.round(m.coef_[0], 3)))
    return x, coef


def day_t(v):
    v = np.asarray(v, float)
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std() > 0 else float("nan")


def capture(x, K, N, tgt="top_M"):
    rk = x.groupby("date")[K].rank(ascending=False, method="first")
    inl = rk <= N
    d = pd.DataFrame({"date": x.date, "per": x.per, "hit": inl & x[tgt], "top": x[tgt], "n": x.n_el, "inl": inl})
    dd = d.groupby("date").agg(per=("per", "first"), hit=("hit", "sum"), top=("top", "sum"), n=("n", "first"))
    dd["cap"] = dd.hit / dd.top
    dd["base"] = np.minimum(N, dd.n) / dd.n
    res = {}
    for p, g in dd.groupby("per"):
        res[p] = {"days": int(len(g)), "cap": round(float(g.cap.mean()), 4), "base": round(float(g.base.mean()), 4),
                  "lift": round(float(g.cap.mean() / g.base.mean()), 2), "t": round(day_t(g.cap - g.base), 2)}
    return res, inl


def direction(x, inl):
    res = {}
    for p in ("FIT", "CHECK", "T2"):
        s = x[inl & (x.per == p)]
        mv = s[s.top_M]
        res[p] = {"list_n": int(len(s)), "cont_hit_list": round(float((s.D == s.mdir).mean()), 3),
                  "cont_hit_movers": round(float((mv.D == mv.mdir).mean()), 3) if len(mv) else None,
                  "gap_hit_list": round(float((np.sign(s.gap_s) == s.mdir).mean()), 3),
                  "gap_hit_movers": round(float((np.sign(mv.gap_s) == mv.mdir).mean()), 3) if len(mv) else None,
                  "movers_in_list": int(len(mv))}
    return res


def trades(x, rule):
    """candidate trade per eligible symbol-day for rule s1/s2/s3: columns side, entry, risk, px, kind, tod, r_live, r_lr8."""
    if rule == "s1":
        side, entry, stop, em = x.D, x.entry, x.s1_stop, x.i0_mm
    elif rule == "s2":
        side, entry, stop, em = -x.D, x.entry, x.s2_stop, x.i0_mm
    else:
        side, entry, stop, em = x.D, x.s3_entry, x.s3_stop, x.s3_em
    px, kind = x[f"{rule}_px"], x[f"{rule}_kind"]
    t = pd.DataFrame({"date": x.date, "per": x.per, "symbol": x.symbol, "side": side, "entry": entry, "risk": (entry - stop).abs(),
                      "px": px, "kind": kind, "em": em, "gap_s": x.gap_s, "atrp": x.atrp})
    ok = t.px.notna() & t.entry.notna() & (side != 0) & (t.risk >= 0.001 * t.entry) & (side * (t.entry - stop) > 0)
    ok &= (t.side > 0) | t.symbol.map(ETB).fillna(False).astype(bool)
    t = t[ok].copy()
    mins = 570 + t.em.astype(int)
    t["tod"] = (mins // 60) * 100 + mins % 60
    t["r_gross"] = t.side * (t.px - t.entry) / t.risk
    tier = np.where((t.gap_s.abs() >= 0.20) | (t.entry < 5), 3.0, 1.0)
    ecost = (0.01 + t.entry * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xcost = 0.01 + t.px * 1e-4 + np.where(t.kind == 1, 0.02, 0.0)
    borrow = np.where(t.side < 0, 1.2e-4 * t.entry, 0.0)
    t["r_lr8"] = (t.side * (t.px - t.entry) - tier * (ecost + xcost) - borrow) / t.risk
    kd = np.where(t.kind == 1, "stop", "market")
    t["r_live"] = t.r_gross - CL.predict_R(CELLS, t.entry.to_numpy(), t.risk.to_numpy(), kd)
    return t


def st(t, col, nses):
    if len(t) < 3:
        return {"n": int(len(t))}
    r = t[col]
    day = r.groupby(t.date).sum()
    tot = float(r.sum())
    best = day.idxmax()
    m = float(r.mean())
    e = (r - m).groupby(t.date).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(t)
    return {"n": int(len(t)), "days": int(day.size), "avg": round(m, 4), "t_day": round(m / se, 2) if se > 0 else None,
            "wo_best": round(float(r[t.date != best].mean()), 4), "best_day": str(best),
            "best_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total": round(tot, 1),
            "per_session": round(tot / nses, 3), "win": round(float((r > 0).mean()), 3),
            "gross": round(float(t.r_gross.mean()), 4), "worst_day": round(float(day.min()), 1)}


def control(tl, pool, col):
    """exact expectation of a size-matched random draw (k * pool mean per day) + 50 draws; paired day diffs."""
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
    return {"days": int(len(j)), "setup_avg": round(float(j["sum"].sum() / ntr), 4),
            "ctrl_avg": round(float((j["size"] * j["mean"]).sum() / ntr), 4),
            "diff_avg": round(float(diff.sum() / ntr), 4), "paired_t": round(day_t(diff), 2),
            "pct_draws_below": round(float((draws < j["sum"].sum()).mean()), 2)}


def main():
    x = load()
    x, coef = add_rankers(x)
    nses = x.groupby("per").date.nunique().to_dict()
    res = {"note": "Educational only - not financial advice. MOVEHUNT_1127.", "sessions": nses,
           "eligible_per_day": x.groupby("per").n_el.mean().round(0).to_dict(), "logit_coef": coef, "rankers": {}}
    say("sessions", nses, "eligible/day", res["eligible_per_day"])
    say("LOGIT coef (FIT)", coef)
    # univariate feature info: top-mover rate by within-day decile of each feature (CHECK)
    say("\n== capture of top-2% after-09:50 movers (M = |C - P50|/ATR) ==")
    for K in ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"]:
        res["rankers"][K] = {}
        for N in (20, 50, 100):
            c, _ = capture(x, K, N)
            res["rankers"][K][N] = c
            say(K, N, " | ".join(f"{p}: cap {c[p]['cap']:.3f} base {c[p]['base']:.3f} lift {c[p]['lift']} t {c[p]['t']}"
                                 for p in ("FIT", "CHECK", "T2")))
    best = max(["K1", "K2", "K3", "K4", "K5", "K6"], key=lambda k: (res["rankers"][k][50]["FIT"]["cap"], k == "K5"))
    res["setup_ranker"] = best
    say("\nsetup ranker (max FIT cap@50):", best)
    for tgt in ("top_M_oc", "top_M_mx"):
        c, _ = capture(x, best, 50, tgt)
        res[f"secondary_{tgt}"] = c
        say("secondary", tgt, best, "@50", c)
    _, inl20 = capture(x, best, 20)
    res["direction_top20"] = direction(x, inl20)
    say("direction (top-20 list)", res["direction_top20"])
    # ranker strength bar
    c50 = res["rankers"][best][50]
    res["ranker_strong"] = bool(all(c50[p]["lift"] >= 2.0 and c50[p]["t"] >= 3.0 for p in ("CHECK", "T2")))
    say("ranker strong (lift>=2, t>=3 CHECK+T2):", res["ranker_strong"])
    # setups
    say("\n== setups on", best, "top-20 (LIVE-L | LR8) ==")
    res["setups"] = {}
    xl = x[inl20]
    xp = x[~inl20]
    for rule in ("s1", "s2", "s3"):
        tl_all, tp_all = trades(xl, rule), trades(xp, rule)
        for sd, nm in ((1, "long"), (-1, "short")):
            key = f"{rule}_{nm}"
            tl, tp = tl_all[tl_all.side == sd], tp_all[tp_all.side == sd]
            e = {}
            for p in ("FIT", "CHECK", "T2"):
                a, b = tl[tl.per == p], tp[tp.per == p]
                e[p] = {"live": st(a, "r_live", nses[p]), "lr8": st(a, "r_lr8", nses[p]),
                        "control_live": control(a, b, "r_live"), "pool_live_avg": round(float(b.r_live.mean()), 4) if len(b) else None}
            # family split (CHECK + T2 pooled, LIVE-L)
            ct = tl[tl.per.isin(["CHECK", "T2"])]
            fam = {}
            for fk, m in (("gap>=1atr", ct.gap_s.abs() / ct.atrp >= 1), ("gap<1atr", ct.gap_s.abs() / ct.atrp < 1),
                          ("px<20", ct.entry < 20), ("px20-100", (ct.entry >= 20) & (ct.entry < 100)), ("px100+", ct.entry >= 100),
                          ("stop", ct.kind == 1), ("time", ct.kind == 0)):
                s = ct[m]
                fam[fk] = {"n": int(len(s)), "avg": round(float(s.r_live.mean()), 4) if len(s) else None}
            e["family_check_t2"] = fam
            C, T = e["CHECK"], e["T2"]
            gates = {
                "pos_costs": all(z[k].get("avg", -1) > 0 for z in (C, T) for k in ("live", "lr8")),
                "t": (C["live"].get("t_day") or 0) >= 3.0 and (T["live"].get("t_day") or 0) >= 2.0,
                "one_big_day": all((z["live"].get("wo_best") or -1) > 0 and (z["live"].get("best_share") or 1) < 0.5 for z in (C, T)),
                "control": (C["control_live"].get("diff_avg", -1) > 0 and T["control_live"].get("diff_avg", -1) > 0
                            and (C["control_live"].get("paired_t") or 0) >= 2.0),
            }
            e["gates"] = gates
            e["pass"] = all(gates.values())
            res["setups"][key] = e
            for p in ("FIT", "CHECK", "T2"):
                L, R8, Ct = e[p]["live"], e[p]["lr8"], e[p]["control_live"]
                say(f"{key:9s} {p:5s} n {L.get('n')} avg {L.get('avg')} | {R8.get('avg')} gross {L.get('gross')} t {L.get('t_day')} "
                    f"woBest {L.get('wo_best')} bestSh {L.get('best_share')} R/ses {L.get('per_session')} | ctrl {Ct.get('ctrl_avg')} "
                    f"diff {Ct.get('diff_avg')} pt {Ct.get('paired_t')} draws< {Ct.get('pct_draws_below')}")
            say(f"{key:9s} gates {gates} PASS={e['pass']}  family {fam}")
    # descriptive: mover rate by decile of the setup ranker on CHECK/T2 (where does the edge in ranking live)
    dec = {}
    for p in ("CHECK", "T2"):
        s = x[x.per == p]
        q = s.groupby("date")[best].rank(pct=True)
        dec[p] = s.groupby(np.minimum((q * 10).astype(int), 9)).top_M.mean().round(4).to_dict()
    res["mover_rate_by_decile"] = dec
    say("top-mover rate by ranker decile", dec)
    json.dump(res, open(H / "results.json", "w"), indent=1, default=float)
    (H / "score_out.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
