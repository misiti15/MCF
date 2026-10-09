"""Regime study step 3 (NOTES.md 1.4-1.7): the market-context gates G1-G6 (+ plateau neighbours) on 102 base trade
lists. Every gated configuration is counted. Outputs: gates.csv (one row per gated configuration + the ungated base),
counts.json. Locked block: none of the inputs contain it (ctx and the trade lists come from the open history; bt
trades are filtered explicitly). Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

REG = lib.regimes()
RS = pd.read_csv(ROOT / "research" / "history2y" / "rescore.csv").set_index("setup")["tries"]
ST_N, RDT_N, BT_N = 120375, 2551, 15
TOD_ADD, THIS = 7, 20                  # timeofday study sets per setup; this study per lineage (2 lists x 10)


def lineage_n(setup: str) -> int:
    if setup.startswith("RDT-"):
        return RDT_N + 400
    if setup in ("orb20_a", "intraday_momentum"):
        return BT_N + 10
    if setup.startswith("ST"):
        return ST_N + TOD_ADD + THIS
    if setup.startswith("RW6G1"):
        return int(RS["RW6 bdi-rw-ns2-up3"]) + 5158 + TOD_ADD + THIS
    if setup.startswith("RW"):
        k = [x for x in RS.index if x.startswith(setup.split("-")[0] + " ")][0]
        return int(RS[k]) + TOD_ADD + THIS
    return int(RS[setup]) + TOD_ADD + THIS


def load_lists() -> dict[str, pd.DataFrame]:
    out = {}
    T = pd.read_parquet(ROOT / "research" / "bdi" / "timeofday" / "data" / "trades.parquet")
    for (s, st), g in T[T.set.isin(["current", "full"])].groupby(["setup", "set"]):
        out[f"{s}|{st}"] = pd.DataFrame({"date": g["date"].astype(str).to_numpy(), "tod": g["tod"].to_numpy(int),
                                         "r": g["r"].to_numpy(float), "s": np.where(g["side"].to_numpy() == "long", 1, -1),
                                         "lineage": s})
    R = pd.read_parquet(HERE / "data" / "reddit_trades.parquet")
    for s, g in R.groupby("setup"):
        out[f"{s}|full"] = pd.DataFrame({"date": g["date"].astype(str).to_numpy(), "tod": g["tod"].to_numpy(int),
                                         "r": g["r"].to_numpy(float), "s": np.where(g["side"].to_numpy() == "long", 1, -1),
                                         "lineage": s})
    b = pd.read_parquet(ROOT / "research" / "history2y" / "data" / "bt_trades.parquet")
    et = pd.to_datetime(b["entry_time"])
    st = pd.to_datetime(b["signal_time"])
    b = b[(et.dt.hour * 100 + et.dt.minute >= 950)].copy()   # as rescore.bt_trades
    st = pd.to_datetime(b["signal_time"])
    m5 = st.dt.floor("5min")
    b["tod"] = (m5.dt.hour * 100 + m5.dt.minute).to_numpy()
    d = pd.to_datetime(b["date"]).dt.strftime("%Y-%m-%d")
    b = b[(d < lib.LOCKED[0]) | (d > lib.LOCKED[1])]
    for s, g in b.groupby("strategy"):
        out[f"{s}|current"] = pd.DataFrame({"date": pd.to_datetime(g["date"]).dt.strftime("%Y-%m-%d").to_numpy(),
                                            "tod": g["tod"].to_numpy(int), "r": g["r_multiple"].to_numpy(float),
                                            "s": g["side"].to_numpy(int), "lineage": s})
    return out


def attach(T: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """Context at the trade's decision bar: the latest ctx bar <= tod (5-min grid; tod > 15:00 uses 15:00)."""
    tq = np.minimum(T["tod"].to_numpy(), 1500)
    hh, mm = tq // 100, tq % 100
    tq = hh * 100 + (mm // 5) * 5
    k = T["date"].astype(str) + "|" + pd.Series(tq).astype(str).str.zfill(4).to_numpy()
    T = T.copy()
    for c in ("S1_brd_fo", "S4_spy_fo"):
        T[c] = ctx[c].reindex(k.to_numpy()).to_numpy()
    T["S1_1000"] = ctx["S1_brd_fo"].reindex((T["date"].astype(str) + "|1000").to_numpy()).to_numpy()
    T = T[np.isfinite(T["S1_brd_fo"].to_numpy())].reset_index(drop=True)
    dt = pd.to_datetime(T["date"])
    T["dcode"] = (dt.dt.year * 10000 + dt.dt.month * 100 + dt.dt.day).to_numpy()
    T["mcode"] = (dt.dt.year * 12 + dt.dt.month).to_numpy()
    T["reg"] = pd.Series(REG["regime"].to_numpy(), index=pd.Index(REG.index).astype(str)).reindex(T["date"].astype(str)).to_numpy()
    return T


def gate_mask(T, kind, th):
    s = T["s"].to_numpy()
    if kind == "brd":
        x = T["S1_brd_fo"].to_numpy()
        return ((s > 0) & (x >= 0.5 + th) & (x > 0.5)) | ((s < 0) & (x <= 0.5 - th) & (x < 0.5))
    if kind == "spy":
        x = T["S4_spy_fo"].to_numpy()
        return ((s > 0) & (x >= th) & (x > 0)) | ((s < 0) & (x <= -th) & (x < 0))
    if kind == "brd1000":
        x = T["S1_1000"].to_numpy()
        ok = T["tod"].to_numpy() >= 1000
        return ok & (((s > 0) & (x > 0.5)) | ((s < 0) & (x < 0.5)))
    raise ValueError(kind)


def against_mask(T, kind, th):
    s = T["s"].to_numpy()
    T2 = T.assign(s=-s)
    return gate_mask(T2, kind, th)


def wf_gate(T):
    """G6: dead zone d fitted on the 3 previous open months (max gated exp, n >= 30, else 0.10), applied to the next."""
    mon = T["mcode"].to_numpy()
    months = sorted(set(mon))
    keep = np.zeros(len(T), bool)
    chosen = {}
    masks = {d: gate_mask(T, "brd", d) for d in (0.0, 0.05, 0.10, 0.15)}
    r = T["r"].to_numpy()
    for i in range(3, len(months)):
        w = months[i - 3:i + 1]
        if any(b - a != 1 for a, b in zip(w, w[1:])):
            continue
        tr = np.isin(mon, w[:3])
        te = mon == w[3]
        best, bd = -np.inf, 0.10
        for d, m in masks.items():
            mm = m & tr
            if mm.sum() >= 30 and r[mm].mean() > best:
                best, bd = r[mm].mean(), d
        chosen[f"{(w[3] - 1) // 12}-{(w[3] - 1) % 12 + 1:02d}"] = bd
        keep |= te & masks[bd]
    return keep, chosen


def _summary(r, d):
    """gates.summary on integer day codes (same formulas)."""
    n = len(r)
    if not n:
        return {"n": 0}
    u, inv = np.unique(d, return_inverse=True)
    S = np.bincount(inv, weights=r)
    C = np.bincount(inv)
    mu = float(r.mean())
    se = float(np.sqrt(((S - C * mu) ** 2).sum()) / n) if len(u) > 1 else float("nan")
    b = int(np.argmax(S))
    return {"n": n, "days": len(u), "win_rate": round(float((r > 0).mean()), 4), "exp_r": round(mu, 4),
            "t": round(mu / se, 2) if np.isfinite(se) and se > 0 else None,
            "ex_best_day": round(float((S.sum() - S[b]) / max(1, n - C[b])), 4), "busiest": float(C.max() / n)}


def _wf(r, mon):
    """gates.walk_forward share (3 train months, 1 test, step 1; folds touching a non-consecutive month - the locked
    gap - are skipped; test folds with n >= FOLD_MIN_N) on integer month codes (year*12+month)."""
    months = np.unique(mon)
    ok = []
    for i in range(len(months) - 3):
        w = months[i:i + 4]
        if np.any(np.diff(w) != 1):
            continue
        b = mon == w[3]
        if b.sum() >= gates.FOLD_MIN_N:
            ok.append(r[b].mean() > 0)
    return (round(sum(ok) / len(ok), 3) if ok else None), len(ok)


def stats(T, m, n_tries):
    r = T["r"].to_numpy(float)[m]
    d = T["dcode"].to_numpy()[m]
    sm = _summary(r, d)
    if not sm.get("n"):
        return {"n": 0}
    rg = T["reg"].to_numpy()[m]
    reg = {k: _summary(r[rg == k], d[rg == k]) for k in ("up", "flat", "down")}
    rpass = all(reg[k].get("n", 0) >= gates.REGIME_MIN_N and reg[k].get("exp_r", -1) > 0 for k in ("up", "down"))
    share, nf = _wf(r, T["mcode"].to_numpy()[m])
    v, fails = gates.verdict(sm, {**reg, "pass": rpass}, {"share_positive": share}, n_tries)
    return {"n": sm["n"], "days": sm["days"], "per_day": round(sm["n"] / 426, 2), "win": sm["win_rate"], "exp": sm["exp_r"],
            "t": sm["t"], "ex_best_day": sm["ex_best_day"], "busiest_day": round(sm["busiest"], 3),
            "up_exp": reg["up"].get("exp_r"), "up_n": reg["up"].get("n", 0), "flat_exp": reg["flat"].get("exp_r"),
            "flat_n": reg["flat"].get("n", 0), "down_exp": reg["down"].get("exp_r"), "down_n": reg["down"].get("n", 0),
            "regime_pass": rpass, "wf_share": share, "wf_folds": nf, "verdict": v, "fails": "; ".join(fails)}


def main():
    ctx = pd.read_parquet(HERE / "data" / "ctx.parquet")
    ctx.index = ctx["date"].astype(str) + "|" + ctx["tod"].astype(str).str.zfill(4)
    L = load_lists()
    rows, count = [], 0
    for key, T0 in sorted(L.items()):
        T = attach(T0, ctx)
        lin = T0["lineage"].iloc[0]
        N = lineage_n(lin)
        treq = gates.t_required(N)
        base = {"list": key, "lineage": lin, "N_lineage": N, "t_req": treq, "n_raw": len(T0)}
        rows.append({**base, "gate": "base", **stats(T, np.ones(len(T), bool), N)})
        cfg = {"G1 brd0": ("brd", 0.0), "G2 brd10": ("brd", 0.10), "G3 spy0": ("spy", 0.0), "G4 spy30": ("spy", 0.30),
               "G5 brd1000": ("brd1000", 0.0), "N brd05": ("brd", 0.05), "N brd15": ("brd", 0.15),
               "N spy15": ("spy", 0.15), "N spy50": ("spy", 0.50)}
        res = {}
        for g, (kind, th) in cfg.items():
            m = gate_mask(T, kind, th)
            count += 1
            st = stats(T, m, N)
            res[g] = st
            blk = ~m
            st["blocked_exp"] = round(float(T["r"][blk].mean()), 4) if blk.any() else None
            st["blocked_n"] = int(blk.sum())
            am = against_mask(T, kind, th)
            st["against_exp"] = round(float(T["r"][am].mean()), 4) if am.any() else None
            st["against_n"] = int(am.sum())
        m6, chosen = wf_gate(T)
        count += 1
        res["G6 brdWF"] = stats(T, m6, N)
        res["G6 brdWF"]["chosen_d"] = json.dumps(chosen)
        pe = lambda g: res[g].get("exp") if res[g].get("n") else np.nan  # noqa: E731
        plateau = {"G1 brd0": [pe("N brd05")], "G2 brd10": [pe("N brd05"), pe("N brd15")], "G3 spy0": [pe("N spy15")],
                   "G4 spy30": [pe("N spy15"), pe("N spy50")], "G5 brd1000": [pe("G1 brd0")],
                   "G6 brdWF": [pe("G1 brd0"), pe("N brd05"), pe("G2 brd10"), pe("N brd15")]}
        for g, st in res.items():
            pm = float(np.nanmean(plateau[g])) if g in plateau and np.isfinite(plateau[g]).any() else None
            st["plateau_mean"] = round(pm, 4) if pm is not None else None
            ok = (st.get("n", 0) >= 150 and st.get("up_n", 0) >= 30 and st.get("down_n", 0) >= 30
                  and (st.get("up_exp") or -1) > 0 and (st.get("down_exp") or -1) > 0 and (st.get("t") or 0) >= 2.0
                  and (st.get("wf_share") or 0) >= 0.6 and (pm or -1) > 0 and (st.get("ex_best_day") or -1) > 0
                  and st.get("busiest_day", 1) <= 0.10)
            st["probation_pass"] = bool(ok) and g[0] == "G"
            rows.append({**base, "gate": g, **st})
        print(key, {g: (res[g].get("n"), res[g].get("exp"), res[g].get("t")) for g in ("G1 brd0", "G3 spy0")}, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "gates.csv", index=False)
    json.dump({"base_lists": len(L), "gated_configs": count, "signal_configs": 32,
               "study_total": count + 32}, open(HERE / "counts.json", "w"), indent=1)
    print("lists", len(L), "gated configs", count, "passers", int(df["probation_pass"].fillna(False).sum()))


if __name__ == "__main__":
    main()
