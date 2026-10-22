"""regime1022 Part C: regime profile of every covered live setup, class, (i) net expectancy over the real regime mix,
(iii) the selection rule applied with 6 pre-declared at-entry gates (PLAN.md). Writes regime_by_setup.csv,
classes.csv, gates_c.csv, selection.csv, years.csv, live_by_regime.csv. Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from asrun import sequence
from live import journals
from rc import HERE, SCR, gates, lib
from regime import LABELS, day_table

N_PRIOR = 718 + 196          # gates1021 + bdi1021 market-context gate lineage
GATES = ("R1", "R2", "R3", "R4", "R5", "U7")
REF = ("U7h",)        # gates1021 U7 as it was actually scored (today's c2c = hindsight); reference only, not counted


def summ(x):
    if not len(x):
        return {"n": 0, "avg_r": None, "t": None, "se": None}
    s = gates.summary(x[["date", "r"]])
    t = s.get("t")
    se = (s["exp_r"] / t) if t else None
    return {"n": int(s["n"]), "avg_r": s["exp_r"], "t": t, "se": se}


def add_state(a: pd.DataFrame) -> pd.DataFrame:
    idx = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "idx").glob("*.parquet"))], ignore_index=True)
    idx["date"] = pd.to_datetime(idx["date"]).dt.date
    spy = idx[idx["symbol"] == "SPY"]
    a = a.merge(spy[["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "spy_vwap"}), on=["date", "tod"], how="left")
    ctx = pd.concat([lib.load_context(m) for m in lib.months()], ignore_index=True)
    ctx["date"] = pd.to_datetime(ctx["date"]).dt.date
    s1030 = ctx[ctx["tod"] == 1030].set_index("date")["spy_fo"]
    a["spy_1030"] = a["date"].map(s1030)
    dt = day_table()
    # the scan's spy_prev came from gates1021's spy_prev.parquet, which is TODAY's close-to-close (lookahead): replace it
    a["spy_c2c_today"] = a["date"].map(dt["spy_c2c_today"])
    a["spy_prev"] = a["date"].map(dt["spy_prev"])
    return a


def gate_mask(a: pd.DataFrame, g: str, side: str) -> np.ndarray:
    sp, fo, vw, b, d2 = (a[k].to_numpy(float) for k in ("spy_prev", "spy_fo", "spy_vwap", "breadth", "d2"))
    if g == "U7h":
        sp, g = a["spy_c2c_today"].to_numpy(float), "U7"
    s1030, tod = a["spy_1030"].to_numpy(float), a["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        if side == "short":
            m = {"R1": sp >= 0.5, "R2": (sp >= 0.5) & (fo >= 0), "R3": (vw > 0) & (fo >= 0.25),
                 "R4": (tod >= 1030) & (s1030 >= 0.25), "R5": (b >= 0.60) & (d2 > 0), "U7": (sp >= 0.5) & (fo >= 0.25)}[g]
        else:
            m = {"R1": sp <= -0.5, "R2": (sp <= -0.5) & (fo <= 0), "R3": (vw < 0) & (fo <= -0.25),
                 "R4": (tod >= 1030) & (s1030 <= -0.25), "R5": (b <= 0.40) & (d2 < 0), "U7": (sp <= -0.5) & (fo <= -0.25)}[g]
    return np.nan_to_num(m, nan=0).astype(bool)


def day_delta(var, par):
    a = par.groupby("date")["r"].agg(["sum", "size"])
    b = var.groupby("date")["r"].sum().reindex(a.index, fill_value=0.0)
    D = b - a["sum"]
    n = a["size"].sum()
    if n == 0:
        return np.nan, np.nan
    dl = D.sum() / n
    se = np.sqrt(((D - dl * a["size"]) ** 2).sum()) / n
    return float(dl), (float(dl / se) if se > 0 else np.nan)


def classify(reg: dict, pooled: dict, tr: dict, va: dict) -> tuple[str, str, str]:
    ok = {k: v for k, v in reg.items() if v["n"] >= 30 and v["avg_r"] is not None}
    if not ok:
        return "loser", None, None
    best = max(ok, key=lambda k: ok[k]["avg_r"])
    worst = min(ok, key=lambda k: ok[k]["avg_r"])
    if all(v["avg_r"] >= -0.02 for v in ok.values()) and len(ok) == 4 and (pooled["avg_r"] or 0) >= 0:
        return "all-weather", best, worst
    b = ok[best]
    if b["avg_r"] >= 0.03 and (b["t"] or 0) >= 2.0 and (tr.get(best, {}).get("avg_r") or -1) > 0 \
            and (va.get(best, {}).get("avg_r") or -1) > 0:
        return "regime specialist", best, worst
    return "loser", best, worst


def main():
    A = pd.read_parquet(SCR / "asrun.parquet")
    A = add_state(A)
    meta = pd.read_csv(HERE / "setups_scored.csv")
    dt = day_table()
    mix = dt[dt["regime"].notna() & (pd.Index(dt.index) <= pd.Timestamp("2026-10-07").date())]
    rows, cls, grows, sel, yrs = [], [], [], [], []
    for _, m in meta.iterrows():
        s = A[A["skey"] == m["skey"]].reset_index(drop=True)
        if s.empty:
            continue
        par = s[s["asrun"]]
        reg, regs = {}, {"train": {}, "valid": {}}
        for lab in LABELS:
            reg[lab] = summ(par[par["regime"] == lab])
            for sp in ("train", "valid"):
                regs[sp][lab] = summ(par[(par["regime"] == lab) & (par["split"] == sp)])
            rows.append({"skey": m["skey"], "names": m["names"], "regime": lab, **{f"all_{k}": v for k, v in reg[lab].items()},
                         **{f"train_{k}": v for k, v in regs["train"][lab].items()},
                         **{f"valid_{k}": v for k, v in regs["valid"][lab].items()}})
        pooled = summ(par)
        ptr, pva = summ(par[par["split"] == "train"]), summ(par[par["split"] == "valid"])
        c, best, worst = classify(reg, pooled, regs["train"], regs["valid"])
        # (i) net expectancy over the real regime mix: avg R per regime x share of sessions in that regime x trades/day
        net = {}
        for lab in LABELS:
            days_lab = int((mix["regime"] == lab).sum())
            traded = par[par["regime"] == lab]
            net[lab] = {"sessions": days_lab, "R_total": round(float(traded["r"].sum()), 1)}
        cls.append({"skey": m["skey"], "names": m["names"], "accounts": m["accounts"], "side": m["side"], "class": c,
                    "best": best, "worst": worst, "n": pooled["n"], "avg_r": pooled["avg_r"], "t": pooled["t"],
                    "train_avg_r": ptr["avg_r"], "valid_avg_r": pva["avg_r"], "train_n": ptr["n"], "valid_n": pva["n"],
                    "total_R": round(float(par["r"].sum()), 1),
                    "best_regime_R": net[best]["R_total"] if best else None,
                    "rest_R": round(float(par[par["regime"] != best]["r"].sum()), 1) if best else None,
                    "by_regime": json.dumps({k: {"trades": v["n"], "avg_r": v["avg_r"], "t": v["t"]} for k, v in reg.items()}),
                    "by_regime_train": json.dumps({k: {"trades": v["n"], "avg_r": v["avg_r"]} for k, v in regs["train"].items()}),
                    "by_regime_valid": json.dumps({k: {"trades": v["n"], "avg_r": v["avg_r"]} for k, v in regs["valid"].items()})})
        for y in sorted(pd.to_datetime(par["date"]).dt.year.unique()):
            py = par[pd.to_datetime(par["date"]).dt.year == y]
            yrs.append({"skey": m["skey"], "names": m["names"], "year": int(y), "n": len(py),
                        "avg_r": round(float(py["r"].mean()), 4), "total_R": round(float(py["r"].sum()), 1),
                        **{f"{lab}_R": round(float(py[py["regime"] == lab]["r"].sum()), 1) for lab in LABELS}})
        # S1: worst regime vs the rest, train and valid
        s1 = {}
        for sp in ("train", "valid"):
            pp = par[par["split"] == sp]
            u, rest = summ(pp[pp["regime"] == worst]), summ(pp[pp["regime"] != worst])
            if u["se"] and rest["se"]:
                s1[sp] = (rest["avg_r"] - u["avg_r"]) / np.sqrt(u["se"] ** 2 + rest["se"] ** 2)
            else:
                s1[sp] = np.nan
        S1 = bool((s1["train"] >= 2) and (s1["valid"] >= 1))
        # gates
        best_g = None
        for g in GATES + REF:
            blk = gate_mask(s, g, m["side"])
            idx = np.flatnonzero(~blk)
            k = np.zeros(len(s), bool)
            sub = s.iloc[idx]
            k[idx[sequence(sub["date"].astype(str).to_numpy(), sub["tod"].to_numpy(), sub["symbol"].to_numpy(),
                           sub["exit_tod"].to_numpy())]] = True
            var = s[k]
            r = {"skey": m["skey"], "names": m["names"], "side": m["side"], "gate": g}
            for sp in ("train", "valid", "all"):
                pp = par if sp == "all" else par[par["split"] == sp]
                vv = var if sp == "all" else var[var["split"] == sp]
                dl, dtt = day_delta(vv, pp)
                r.update({f"{sp}_kept_pct": round(100 * len(vv) / max(1, len(pp)), 1),
                          f"{sp}_parent_avg": round(float(pp["r"].mean()), 4) if len(pp) else None,
                          f"{sp}_gated_avg": round(float(vv["r"].mean()), 4) if len(vv) else None,
                          f"{sp}_parent_total": round(float(pp["r"].sum()), 1), f"{sp}_gated_total": round(float(vv["r"].sum()), 1),
                          f"{sp}_delta": round(dl, 4), f"{sp}_delta_t": round(dtt, 2)})
            r["winners_blocked_pct"] = round(100 * (1 - (var["r"] > 0).sum() / max(1, (par["r"] > 0).sum())), 1)
            r["blocked_in_worst_regime_pct"] = round(100 * float((par[~par.index.isin(var.index)]["regime"] == worst).mean()), 1) \
                if (~par.index.isin(var.index)).any() else None
            grows.append(r)
        cls[-1].update({"S1_t_train": round(s1["train"], 2), "S1_t_valid": round(s1["valid"], 2), "S1": S1})
    G = pd.DataFrame(grows)
    G["reference_only"] = G["gate"].isin(REF)
    N = N_PRIOR + int((~G["reference_only"]).sum())
    bar = max(1.5, np.sqrt(2 * np.log(N)))
    G["S2"] = (G["train_delta"] > 0) & (G["valid_delta"] > 0)
    G["S3"] = (G["train_kept_pct"] >= 80) & (G["valid_kept_pct"] >= 80) & (G["winners_blocked_pct"] <= 20)
    G["S4"] = (G["train_gated_avg"] > G["train_parent_avg"]) & (G["valid_gated_avg"] > G["valid_parent_avg"]) & \
        (G["train_gated_total"] >= G["train_parent_total"]) & (G["valid_gated_total"] >= G["valid_parent_total"])
    G["S6"] = G["all_delta_t"] >= bar
    C = pd.DataFrame(cls)
    G = G.merge(C[["skey", "class", "S1"]], on="skey")
    G["S5"] = G["class"] != "all-weather"
    G["pass"] = G[["S1", "S2", "S3", "S4", "S5", "S6"]].all(axis=1) & ~G["reference_only"]
    G.to_csv(HERE / "gates_c.csv", index=False)
    C.to_csv(HERE / "classes.csv", index=False)
    pd.DataFrame(rows).to_csv(HERE / "regime_by_setup.csv", index=False)
    pd.DataFrame(yrs).to_csv(HERE / "years.csv", index=False)
    # live by regime (paper, all accounts merged, by setup name)
    T = journals()
    T["regime"] = T["date"].map(dt["regime"])
    lv = T.dropna(subset=["radj"]).groupby(["strategy", "regime"]).agg(trades=("radj", "size"), avg_r=("radj", "mean"),
                                                                        pnl=("pnl_adj", "sum"), sessions=("date", "nunique"))
    lv.round(3).to_csv(HERE / "live_by_regime.csv")
    json.dump({"part_c_gate_configs": int((~G["reference_only"]).sum()), "reference_rows_not_counted": int(G["reference_only"].sum()), "lineage_N": N, "bar": round(bar, 2), "gates": GATES,
               "setups_scored": int(C.shape[0])}, open(HERE / "counts_c.json", "w"), indent=1)
    print("N", N, "bar", round(bar, 2))
    print(C[["names", "class", "best", "worst", "n", "avg_r", "train_avg_r", "valid_avg_r", "S1"]].to_string())
    print(G[G["pass"]][["names", "gate", "train_kept_pct", "valid_kept_pct", "train_parent_avg", "train_gated_avg",
                        "valid_parent_avg", "valid_gated_avg", "all_delta_t"]].to_string())


if __name__ == "__main__":
    main()
