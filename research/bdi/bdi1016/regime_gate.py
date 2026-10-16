"""BDI 2026-10-16 Part B: early-session market-regime DIRECTION gate on 6 live lab parents (pre-declared in PLAN.md).
Educational only - not financial advice.

    python research/bdi/bdi1016/regime_gate.py          # scan (cached in the scratchpad) + score -> regime_*.csv

Open two-year history only: lib.load_month refuses the rule-19 locked block 2024-11-01..2025-02-28 and
MCF_HIST_ALLOW_LOCKED is never set; head rows are read only for open months.
"""
from __future__ import annotations

import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "refire1014"), str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
import scan  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "locked block must stay closed"
OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/b1016")
NAMES = ["CWT14-failbrk-orl-p05-long", "CWT14-failbrk-pdl-p05-long", "LIQ-orl-sweep-open15-s25-long",
         "CWT14-failbrk-pdh-p05-lowvol-short", "RW7-gapdn-bounce-early-short-FD", "RW2-exhaustion-noon-adv150-short-FD"]
TS = (1000, 1030)
N_CONFIGS = 84
BAR_STUDY = gates.t_required(N_CONFIGS)
BAR_LINEAGE = gates.t_required(2366 + N_CONFIGS)


def day_features(month: str) -> pd.DataFrame:
    f = lib.load_month(month, columns=None)
    f["symbol"] = f["symbol"].astype(str)
    out = []
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(scan.HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)),
                                           ("tod", "<", 950), ("symbol", "in", ["SPY"])])
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    orng = ht[ht["tod"] <= 945].groupby("date").agg(or_hi=("h", "max"), or_lo=("l", "min"))
    for T in TS:
        x = f[f["tod"] == T]
        br = (x["vwapDistPct"] > 0).groupby(x["date"]).mean().rename("breadth")
        idx = x[x["symbol"].isin(["SPY", "QQQ", "IWM"])].pivot_table(index="date", columns="symbol",
                                                                       values=["fromOpen", "gap", "close"])
        d = pd.DataFrame({"spy_fo": idx[("fromOpen", "SPY")], "qqq_fo": idx[("fromOpen", "QQQ")],
                          "iwm_fo": idx[("fromOpen", "IWM")], "spy_gap": idx[("gap", "SPY")],
                          "spy_c": idx[("close", "SPY")]})
        d = d.join(br).join(orng)
        d["spy_pc"] = ((1 + d.spy_gap / 100) * (1 + d.spy_fo / 100) - 1) * 100
        d["T"] = T
        out.append(d.reset_index())
    return pd.concat(out, ignore_index=True)


def month_job(args):
    month, sts = args
    rows, _ = scan.month_hits(month, sts)
    return pd.concat(rows, ignore_index=True), day_features(month)


def classify(F: pd.DataFrame, K: str, k: float) -> pd.Series:
    """+1 trend-up, -1 trend-down, 0 chop, per date (F = features at one T)."""
    if K == "K1":
        dn = (F.spy_fo <= -k) & (F.qqq_fo <= -k) & (F.iwm_fo <= -k)
        up = (F.spy_fo >= k) & (F.qqq_fo >= k) & (F.iwm_fo >= k)
    elif K == "K2":
        dn = (F.spy_fo <= -k) & (F.breadth <= 0.35)
        up = (F.spy_fo >= k) & (F.breadth >= 0.65)
    else:
        vd = ((F.spy_fo <= -k).astype(int) + (F.qqq_fo <= -k) + (F.iwm_fo <= -k) + (F.spy_pc <= -k)
              + (F.breadth <= 0.40) + (F.spy_c < F.or_lo))
        vu = ((F.spy_fo >= k).astype(int) + (F.qqq_fo >= k) + (F.iwm_fo >= k) + (F.spy_pc >= k)
              + (F.breadth >= 0.60) + (F.spy_c > F.or_hi))
        dn, up = vd >= 5, vu >= 5
    c = pd.Series(np.where(dn, -1, np.where(up, 1, 0)), index=F["date"].values)
    return c


def first(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d["r"].notna()].sort_values(["key", "symbol", "date", "tod"])
    return d.groupby(["key", "symbol", "date"], sort=False).head(1)


def stats(t: pd.DataFrame) -> dict:
    if not len(t):
        return {"n": 0, "exp": np.nan, "t": np.nan}
    s = gates.summary(t)
    return {"n": s["n"], "exp": s["exp_r"], "t": s["t"]}


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    hp, fp = SCR / "hits.parquet", SCR / "feats.parquet"
    sts = [s for s in scan.account_setups() if s["name"] in NAMES]
    assert len(sts) == 6, [s["name"] for s in sts]
    names = {s["key"]: s["name"] for s in sts}
    sides = {s["key"]: scan.load_mod(s).SIDE for s in sts}
    if not hp.exists():
        months = lib.months()
        assert not set(months) & set(lib.LOCKED_MONTHS)
        with Pool(3) as p:
            res = p.map(month_job, [(mo, sts) for mo in months])
        pd.concat([r[0] for r in res], ignore_index=True).to_parquet(hp)
        pd.concat([r[1] for r in res], ignore_index=True).to_parquet(fp)
    hits = pd.read_parquet(hp)
    feats = pd.read_parquet(fp)
    hits["date"] = pd.to_datetime(hits["date"]).dt.date
    feats["date"] = pd.to_datetime(feats["date"]).dt.date
    lo, hi = pd.Timestamp(lib.LOCKED[0]).date(), pd.Timestamp(lib.LOCKED[1]).date()
    assert not ((hits.date >= lo) & (hits.date <= hi)).any() and not ((feats.date >= lo) & (feats.date <= hi)).any()
    hits["name"] = hits["key"].map(names)
    hits["sgn"] = hits["key"].map(lambda k: 1 if sides[k] == "long" else -1)
    reg = lib.regimes()
    reg.index = pd.to_datetime(reg.index).date
    regime = reg["regime"]
    sessions = np.array(sorted(feats["date"].unique()))
    parent = {k: first(g) for k, g in hits.groupby("key")}
    parent_all = pd.concat(parent.values(), ignore_index=True)
    rng_seeds = range(200)

    def deltas(P, G):
        late_p = pd.to_datetime(P.date) >= "2026-01-01"
        late_g = pd.to_datetime(G.date) >= "2026-01-01"
        rp, rg = P.date.map(regime), G.date.map(regime)
        o = {"d_exp": G.r.mean() - P.r.mean(), "d_H1": G.r[~late_g].mean() - P.r[~late_p].mean(),
             "d_H2": G.r[late_g].mean() - P.r[late_p].mean()}
        for z in ("up", "flat", "down"):
            o[f"g_{z}"] = G.r[rg == z].mean()
            o[f"d_{z}"] = G.r[rg == z].mean() - P.r[rp == z].mean()
        return o

    rows, regrows, classrows = [], [], []
    for T in TS:
        F = feats[feats["T"] == T].reset_index(drop=True)
        for K in ("K1", "K2", "K3"):
            for k in (0.25, 0.50):
                cls = classify(F, K, k)
                cmap = cls.to_dict()
                # class frequencies and alignment with hindsight regime / SPY T->close
                cr = pd.DataFrame({"cls": cls, "reg": pd.Series(cls.index, index=cls.index).map(regime)})
                for c, g in cr.groupby("cls"):
                    classrows.append({"T": T, "K": K, "k": k, "cls": int(c), "days": len(g),
                                      **{f"reg_{z}": int((g.reg == z).sum()) for z in ("up", "flat", "down")}})
                gate_label = f"{K}-k{k:.2f}-T{T}"
                Gs, Bs, Ps = [], [], []
                for key, P in parent.items():
                    sg = P["sgn"].iloc[0]
                    dc = P.date.map(cmap).fillna(0).to_numpy()
                    blk = (P.tod.to_numpy() >= T) & (dc == -sg)
                    G, B = P[~blk], P[blk]
                    Gs.append(G); Bs.append(B); Ps.append(P)
                    # per-regime (class) result of the ungated parent
                    for c in (-1, 0, 1):
                        sub = P[dc == c]
                        regrows.append({"gate": gate_label, "setup": names[key], "cls": c, **stats(sub)})
                    against_days = int((cls == -sg).sum())
                    rows.append(one_row(gate_label, names[key], P, G, B, against_days, sessions, T, sg, deltas,
                                        rng_seeds))
                P, G, B = (pd.concat(x, ignore_index=True) for x in (Ps, Gs, Bs))
                rows.append(one_row(gate_label, "BOOK(6)", P, G, B, None, sessions, T, None, deltas, rng_seeds,
                                    cls=cls))
    R = pd.DataFrame(rows)
    # plateau: same K/T, other k
    R["K"] = R.gate.str[:2]
    R["T"] = R.gate.str[-4:]
    R["k"] = R.gate.str.extract(r"k([\d.]+)")[0]
    R = R.merge(R[["K", "T", "k", "setup", "d_exp", "b_t"]].rename(columns={"k": "k2", "d_exp": "nb_d", "b_t": "nb_bt"}),
                on=["K", "T", "setup"])
    R = R[R.k != R.k2].drop(columns=["k2"])
    R["testing_pass"] = ((R.d_exp > 0) & (R.b_t <= -BAR_STUDY) & (R.d_H1 > 0) & (R.d_H2 > 0) & (R.wf >= 0.6)
                         & (R.d_exp > R.rnd95) & (R.nb_d > 0) & (R.nb_bt <= -1.5))
    R["primary_pass"] = R.testing_pass & (R.g_exp > 0) & (R.g_t >= BAR_LINEAGE) & (R.g_up > 0) & (R.g_down > 0)
    R.drop(columns=["K", "T", "k"]).to_csv(OUT / "regime_results.csv", index=False, float_format="%.4f")
    pd.DataFrame(regrows).to_csv(OUT / "regime_by_class.csv", index=False, float_format="%.4f")
    pd.DataFrame(classrows).to_csv(OUT / "regime_class_days.csv", index=False)
    pd.set_option("display.width", 260)
    print("bars: study", BAR_STUDY, "lineage", BAR_LINEAGE, "sessions", len(sessions))
    cols = ["gate", "setup", "p_n", "p_exp", "g_n", "g_exp", "g_t", "b_n", "b_exp", "b_t", "d_exp", "d_H1", "d_H2",
            "d_up", "d_down", "wf", "rnd95", "testing_pass", "primary_pass"]
    print(R[cols].round(3).to_string())


def one_row(gate, setup, P, G, B, against_days, sessions, T, sg, deltas, seeds, cls=None):
    ps, gs, bs = stats(P), stats(G), stats(B)
    d = deltas(P, G)
    # walk-forward style: months in which the gate blocked anything, share with month delta > 0
    m = pd.PeriodIndex(pd.to_datetime(B.date), freq="M").unique() if len(B) else []
    per_p = pd.PeriodIndex(pd.to_datetime(P.date), freq="M")
    per_g = pd.PeriodIndex(pd.to_datetime(G.date), freq="M")
    wins = [G.r[per_g == mm].mean() > P.r[per_p == mm].mean() for mm in m]
    wf = float(np.mean(wins)) if wins else np.nan
    # random control: block the same number of (side) sessions at random from T on
    rnd = []
    for s in seeds:
        rng = np.random.default_rng(1016 + s)
        if sg is not None:
            pick = set(rng.choice(sessions, size=min(against_days, len(sessions)), replace=False))
            blk = (P.tod.to_numpy() >= T) & P.date.isin(pick).to_numpy()
        else:   # book: per side, the same number of days the gate called against that side
            n_dn, n_up = int((cls == -1).sum()), int((cls == 1).sum())
            dn = set(rng.choice(sessions, size=n_dn, replace=False))
            up = set(rng.choice(sessions, size=n_up, replace=False))
            sgn = P.sgn.to_numpy()
            blk = (P.tod.to_numpy() >= T) & (((sgn == 1) & P.date.isin(dn).to_numpy())
                                             | ((sgn == -1) & P.date.isin(up).to_numpy()))
        rnd.append(P.r[~blk].mean() - P.r.mean())
    return {"gate": gate, "setup": setup, "against_days": against_days, "p_n": ps["n"], "p_exp": ps["exp"],
            "p_t": ps["t"], "g_n": gs["n"], "g_exp": gs["exp"], "g_t": gs["t"], "b_n": bs["n"], "b_exp": bs["exp"],
            "b_t": bs["t"], **d, "g_exp_check": gs["exp"], "wf": wf, "wf_months": len(wins),
            "rnd95": float(np.quantile(rnd, 0.95)), "rnd_mean": float(np.mean(rnd))}


if __name__ == "__main__":
    main()
