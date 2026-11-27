"""OPENDRIVE_1127 score: K6-at-T ranker (frozen MOVEHUNT coefficients, FIT standardisation per T), rules R1 DRIVE / R2 GAP-GO /
R3 GAP-FILL at T = 09:35/09:40/09:45/09:50 on the top-20 list, LIVE-L + early surcharge (main), harsh, LR8, stress, random
control, one-big-day, 09:50 sibling comparison, mover capture. Usage: python score.py WORK.
Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/primshorts_1126"))
from mcf.research.gates import tod_cost_mult  # noqa: E402
import calib_live as CL  # noqa: E402

W = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
CELLS = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))
COEF = json.load(open(ROOT / "research/movehunt_1127/results.json"))["logit_coef"]
ETB = pd.read_csv("/home/user/MCF/data/universe.csv").set_index("symbol").easy_to_borrow.astype(bool).to_dict()
FEATS = ["gap", "rvol", "rng", "mv", "idio", "pdr", "dv", "atrp"]
TS = (5, 10, 15, 20)
TNAME = {5: "0935", 10: "0940", 15: "0945", 20: "0950"}
GATES_RATIO = {5: 3.8 / 1.4, 10: 2.1 / 1.4, 15: 2.1 / 1.4, 20: 1.0}
E_BPS = 4.43          # slip_tod_out.txt: live mean signed entry slip 09:49-09:59 + 1 bp fees
RNG = np.random.default_rng(1127)
OUT = []
PERS = ("EARLY", "FIT", "CHECK", "T2")


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


def day_t(v):
    v = np.asarray(v, float)
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std() > 0 else float("nan")


def load():
    x = pd.concat([pd.read_parquet(W / "days_t1.parquet"), pd.read_parquet(W / "days_t2.parquet")], ignore_index=True)
    no_locked(x.date.unique())
    x["per"] = x.date.map(period)
    x = x[x.per != "none"].reset_index(drop=True)
    lastmax = x.groupby("date").last_mm.transform("max")
    base = (x.adv20 >= 20e6) & x.atr.gt(0) & x.open.notna() & x.prev_close.notna() & (x.last_mm >= lastmax - 5)
    x["atrp"] = x.atr / x.prev_close
    x["gap_s"] = x.open / x.prev_close - 1
    x["gap"] = x.gap_s.abs() / x.atrp
    x["pdr"] = x.pdr_raw / x.atr
    x["dv"] = np.log(x.adv20.clip(lower=1))
    spy = x[x.symbol == "SPY"].set_index("date")
    for T in TS:
        x[f"spy{T}"] = x.date.map(spy[f"p{T}"] / spy.open - 1)
        x[f"ok{T}"] = base & (x[f"p{T}"] >= 5) & (x[f"n{T}"] >= max(4, 0.75 * T)) & x[f"vmed{T}"].gt(0) & x[f"spy{T}"].notna() \
            & x[f"px{T}L"].notna() & x[f"px{T}S"].notna()
    return x


def rank_at(x, T, mu_sd):
    ok = x[f"ok{T}"].to_numpy()
    f = pd.DataFrame({"gap": x.gap, "rvol": x[f"v{T}"] / x[f"vmed{T}"], "rng": (x[f"h{T}"] - x[f"l{T}"]) / x.atr,
                      "mv": (x[f"p{T}"] - x.open).abs() / x.atr,
                      "idio": ((x[f"p{T}"] / x.open - 1) - x[f"spy{T}"]).abs() / x.atrp, "pdr": x.pdr, "dv": x.dv, "atrp": x.atrp})
    Z = np.column_stack([np.log1p(f[k].clip(lower=0)) if k != "dv" else f[k] for k in FEATS]).astype(float)
    fit = ok & (x.per == "FIT").to_numpy()
    if T not in mu_sd:
        mu_sd[T] = (np.nanmean(Z[fit], 0), np.nanstd(Z[fit], 0))
    mu, sd = mu_sd[T]
    Z = (Z - mu) / sd
    k6 = Z @ np.array([COEF[k] for k in FEATS])
    k6 = np.where(ok & np.isfinite(k6), k6, np.nan)
    s = pd.Series(k6)
    rk = s.groupby(x.date).rank(ascending=False, method="first")
    return f.rvol.to_numpy(), (rk <= 20).to_numpy() & ok


def rules(x, T, rvol):
    p, o, h, l, pc = x[f"p{T}"], x.open, x[f"h{T}"], x[f"l{T}"], x.prev_close
    rng = (h - l).replace(0, np.nan)
    D = np.sign(p - o)
    loc = (p - l) / rng
    r1 = np.where((D > 0) & (loc >= 0.8) & (rvol >= 2.0), 1, np.where((D < 0) & (loc <= 0.2) & (rvol >= 2.0), -1, 0))
    G = np.sign(x.gap_s)
    big = x.gap >= 0.5
    r2 = np.where(big & (G * (p - o) > 0), G, 0)
    r3 = np.where(big & (G * (p - o) < 0) & (G * (p - pc) > 0), -G, 0)
    return {"R1": r1.astype(int), "R2": np.asarray(r2).astype(int), "R3": np.asarray(r3).astype(int)}


def trades(x, T, side, m):
    nm = "L" if side > 0 else "S"
    s = x[m]
    e, st, px, kd = s[f"e{T}"], s[f"st{T}{nm}"], s[f"px{T}{nm}"], s[f"k{T}{nm}"]
    t = pd.DataFrame({"date": s.date, "per": s.per, "symbol": s.symbol, "entry": e, "stop": st, "px": px, "kind": kd,
                      "e1": s[f"e1{T}"], "px1": s[f"px1{T}{nm}"], "k1": s[f"k1{T}{nm}"], "gap_s": s.gap_s, "gap": s.gap,
                      "em": s[f"em{T}"], "mdir": np.sign(s.d_close - s.open)})
    t = t[t.px.notna() & (side * (t.entry - t.stop) > 0)]
    if side < 0:
        t = t[t.symbol.map(ETB).fillna(False).astype(bool)]
    t = t.copy()
    t["risk"] = (t.entry - t.stop).abs()
    t["r_gross"] = side * (t.px - t.entry) / t.risk
    kdn = np.where(t.kind == 1, "stop", "market")
    sur = E_BPS * (MT[T] - 1.0) * 1e-4 * t.entry / t.risk
    t["r_live"] = t.r_gross - CL.predict_R(CELLS, t.entry.to_numpy(), t.risk.to_numpy(), kdn) - sur
    t["r_harsh"] = t.r_live - sur
    mins = 570 + t.em.astype(int)
    tod = (mins // 60) * 100 + mins % 60
    tier = np.where((t.gap_s.abs() >= 0.20) | (t.entry < 5), 3.0, 1.0)
    ec = (0.01 + t.entry * 1e-4) * tod_cost_mult(tod.to_numpy())
    xc = 0.01 + t.px * 1e-4 + np.where(t.kind == 1, 0.02, 0.0)
    bor = 1.2e-4 * t.entry if side < 0 else 0.0
    t["r_lr8"] = (side * (t.px - t.entry) - tier * (ec + xc) - bor) / t.risk
    # stress: entry +1 min (same stop) and +2 bp per side
    r1 = (t.e1 - t.stop).abs()
    # bug fix (disclosed in REPORT): a +1 min entry can land a hair from the fixed stop (float risk ~0 -> R of -1e11);
    # apply the MOVEHUNT minimum-risk rule (risk >= 0.10% of price) to the stressed trade
    v = t.px1.notna() & (side * (t.e1 - t.stop) > 0) & (r1 >= 0.001 * t.e1)
    k1 = np.where(t.k1 == 1, "stop", "market")
    t["r_stress"] = np.where(v, side * (t.px1 - t.e1) / r1 - CL.predict_R(CELLS, t.e1.fillna(t.entry).to_numpy(), r1.where(r1 > 0, 1).to_numpy(), k1)
                             - (E_BPS * (MT[T] - 1.0) + 4.0) * 1e-4 * t.e1 / r1, np.nan)
    return t


def st(t, col, nses):
    t = t[t[col].notna()]
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
            "wo_best": round(float(r[t.date != best].mean()), 4), "best_share": round(float(day.max() / tot), 3) if tot > 0 else None,
            "total": round(tot, 1), "per_session": round(tot / nses, 3), "win": round(float((r > 0).mean()), 3),
            "gross": round(float(t.r_gross.mean()), 4)}


def control(tl, pool, col):
    pk = pool.groupby("date")[col].agg(["mean", "size"])
    lk = tl.groupby("date")[col].agg(["sum", "size"])
    j = lk.join(pk, rsuffix="_p", how="inner")
    j = j[j["size_p"] >= j["size"]]
    if len(j) < 3:
        return {"days": int(len(j))}
    diff = j["sum"] - j["size"] * j["mean"]
    ntr = j["size"].sum()
    return {"days": int(len(j)), "ctrl_avg": round(float((j["size"] * j["mean"]).sum() / ntr), 4),
            "diff_avg": round(float(diff.sum() / ntr), 4), "paired_t": round(day_t(diff), 2)}


def sibling(a, b, days):
    """per-session R totals (0 on days with no trade) of early config a vs its 09:50 sibling b over the period's sessions."""
    sa = a.groupby("date").r_live.sum().reindex(days, fill_value=0.0)
    sb = b.groupby("date").r_live.sum().reindex(days, fill_value=0.0)
    d = sa - sb
    return {"early_R_ses": round(float(sa.mean()), 3), "r0950_R_ses": round(float(sb.mean()), 3),
            "diff_R_ses": round(float(d.mean()), 3), "paired_t": round(day_t(d), 2)}


MT = {}


def main():
    x = load()
    days = {p: sorted(x[x.per == p].date.unique()) for p in PERS}
    nses = {p: len(v) for p, v in days.items()}
    say("sessions", nses)
    # surcharge multiplier: measured entry-bar 1-min range ratio vs 09:50 (median, eligible rows) vs gates ratio
    meas = {}
    for T in TS:
        meas[T] = float(np.nanmedian(x.loc[x[f"ok{T}"], f"br{T}"].replace(0, np.nan)))
    for T in TS:
        MT[T] = max(meas[T] / meas[20], GATES_RATIO[T]) if T < 20 else 1.0
    say("entry-bar median 1-min range (bp):", {TNAME[T]: round(meas[T] * 1e4, 1) for T in TS},
        "-> m_T", {TNAME[T]: round(MT[T], 2) for T in TS}, "surcharge bp", {TNAME[T]: round(E_BPS * (MT[T] - 1), 2) for T in TS})
    res = {"note": "Educational only - not financial advice. OPENDRIVE_1127.", "sessions": nses, "E_bps": E_BPS,
           "range_bp": {TNAME[T]: round(meas[T] * 1e4, 1) for T in TS}, "m_T": {TNAME[T]: round(MT[T], 3) for T in TS},
           "configs": {}, "capture": {}}
    # movers
    u = x["ok20"]
    x["M"] = np.where(u, (x.d_close - x.open).abs() / x.atr, np.nan)
    x["M35"] = np.where(u, (x.d_close - x.p5).abs() / x.atr, np.nan)
    g = x.groupby("date")
    nel = g.ok20.transform("sum")
    ntop = np.maximum(1, np.round(0.02 * nel))
    x["mov"] = u & (g.M.rank(ascending=False, method="first") <= ntop)
    x["mov35"] = u & (g.M35.rank(ascending=False, method="first") <= ntop)
    mu_sd = {}
    T_trades = {}
    for T in TS:
        rvol, inl = rank_at(x, T, mu_sd)
        rl = rules(x, T, rvol)
        x[f"inl{T}"] = inl
        caught = {"all": np.zeros(len(x), bool)}
        for R, dvec in rl.items():
            for side in (1, -1):
                key = f"{R}_{TNAME[T]}_{'long' if side > 0 else 'short'}"
                fire = (dvec == side) & x[f"ok{T}"].to_numpy()
                tl = trades(x, T, side, fire & inl)
                tp = trades(x, T, side, fire & ~inl)
                T_trades[key] = tl
                caught["all"] |= (fire & inl & (np.sign(x.d_close - x.open).to_numpy() == side))
                e = {}
                for p in PERS:
                    a, b = tl[tl.per == p], tp[tp.per == p]
                    e[p] = {"live": st(a, "r_live", nses[p]), "harsh": st(a, "r_harsh", nses[p]), "lr8": st(a, "r_lr8", nses[p]),
                            "stress": st(a, "r_stress", nses[p]), "control": control(a, b, "r_live")}
                ct = tl[tl.per.isin(["CHECK", "T2"])]
                fam = {}
                for fk, mk in (("gap>=1atr", ct.gap >= 1), ("gap<1atr", ct.gap < 1), ("px<20", ct.entry < 20),
                               ("px20-100", (ct.entry >= 20) & (ct.entry < 100)), ("px100+", ct.entry >= 100)):
                    s_ = ct[mk]
                    fam[fk] = {"n": int(len(s_)), "avg": round(float(s_.r_live.mean()), 4) if len(s_) else None}
                e["family_check_t2"] = fam
                res["configs"][key] = e
        # capture
        cap = {}
        for p in PERS:
            m = (x.per == p)
            for tg in ("mov", "mov35"):
                mv = x[m & x[tg]]
                dd = pd.DataFrame({"date": mv.date, "inl": mv[f"inl{T}"], "c": caught["all"][mv.index]})
                gd = dd.groupby("date").agg(n=("inl", "size"), inl=("inl", "sum"), c=("c", "sum"))
                cap[f"{p}_{tg}"] = {"movers": int(gd.n.sum()), "on_list": round(float(gd.inl.sum() / gd.n.sum()), 4),
                                     "traded_right_way": round(float(gd.c.sum() / gd.n.sum()), 4)}
        # R of list trades on movers taken the right way / the wrong way, and on non-movers (all rules pooled)
        allt = pd.concat([T_trades[k].assign(side=1 if k.endswith("long") else -1) for k in T_trades if f"_{TNAME[T]}_" in k])
        mvset = set(zip(x.date[x.mov], x.symbol[x.mov]))
        im = np.array([(a, b) in mvset for a, b in zip(allt.date, allt.symbol)])
        for p in ("CHECK", "T2"):
            q = allt[allt.per == p]
            qm = im[(allt.per == p).to_numpy()]
            right = qm & (q.side.to_numpy() == q.mdir.to_numpy())
            wrong = qm & ~right
            cap[f"{p}_R"] = {"all_n": int(len(q)), "all_avg": round(float(q.r_live.mean()), 4), "all_gross": round(float(q.r_gross.mean()), 4),
                             "all_cost": round(float((q.r_gross - q.r_live).mean()), 4),
                             "all_avg_no_surcharge": round(float((2 * q.r_live - q.r_harsh).mean()), 4),
                             "all_avg_lr8": round(float(q.r_lr8.mean()), 4), "med_risk_bp": round(float((q.risk / q.entry).median() * 1e4), 1), "R_ses": round(float(q.r_live.sum() / nses[p]), 3),
                             "right_n": int(right.sum()), "right_avg": round(float(q.r_live[right].mean()), 3),
                             "wrong_n": int(wrong.sum()), "wrong_avg": round(float(q.r_live[wrong].mean()), 3),
                             "nonmover_avg": round(float(q.r_live[~qm].mean()), 4)}
        res["capture"][TNAME[T]] = cap
        for k_, v_ in cap.items():
            if k_.split('_')[0] in ('CHECK', 'T2'):
                say(f"capture T={TNAME[T]} {k_}", v_)
    # gates + sibling
    say("\n== configs (LIVE-L+surcharge | harsh | LR8 | stress; t day-clustered; ctrl diff) ==")
    npass = 0
    for key, e in res["configs"].items():
        R, Tn, sd = key.split("_")
        sib = f"{R}_0950_{sd}"
        if Tn != "0950":
            e["sibling"] = {p: sibling(T_trades[key][T_trades[key].per == p], T_trades[sib][T_trades[sib].per == p], days[p])
                            for p in ("CHECK", "T2", "FIT")}
        C, T2 = e["CHECK"], e["T2"]
        gates = {
            "pos_costs": all((z[k].get("avg") or -1) > 0 for z in (C, T2) for k in ("live", "lr8")),
            "t": (C["live"].get("t_day") or 0) >= 3.1 and (T2["live"].get("t_day") or 0) >= 2.0,
            "one_big_day": all((z["live"].get("wo_best") or -1) > 0 and (z["live"].get("best_share") or 1) < 0.5 for z in (C, T2)),
            "control": (C["control"].get("diff_avg", -1) > 0 and T2["control"].get("diff_avg", -1) > 0 and (C["control"].get("paired_t") or 0) >= 2.0),
            "stress": all((z["stress"].get("avg") or -1) > 0 for z in (C, T2)),
        }
        if Tn != "0950":
            s = e["sibling"]
            gates["beats_0950"] = s["CHECK"]["diff_R_ses"] > 0 and s["T2"]["diff_R_ses"] > 0 and (s["CHECK"]["paired_t"] or 0) >= 2.0
        e["gates"] = gates
        e["pass"] = bool(Tn != "0950" and all(gates.values()))
        npass += e["pass"]
        for p in PERS:
            L = e[p]["live"]
            say(f"{key:16s} {p:5s} n {L.get('n')} avg {L.get('avg')} | {e[p]['harsh'].get('avg')} | {e[p]['lr8'].get('avg')} | "
                f"{e[p]['stress'].get('avg')} gross {L.get('gross')} t {L.get('t_day')} woBest {L.get('wo_best')} bestSh {L.get('best_share')} "
                f"R/ses {L.get('per_session')} ctrl {e[p]['control'].get('diff_avg')} pt {e[p]['control'].get('paired_t')}")
        if "sibling" in e:
            say(f"{key:16s} vs 0950 {e['sibling']}")
        say(f"{key:16s} gates {gates} PASS={e['pass']}")
    res["n_pass"] = npass
    say("n_pass", npass)
    json.dump(res, open(H / "results.json", "w"), indent=1, default=float)
    (H / "score_out.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
