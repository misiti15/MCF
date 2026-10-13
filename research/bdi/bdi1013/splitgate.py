"""Part B (PLAN.md): split-tape / index-divergence gate for the live SHORT lists (open two-year history, costs in).
Trade lists: research/bdi/indexlink/data/gate_trades.parquet (lab lists re-costed with the tod entry cost; the locked
block was never loaded). Context: indexlink 1-minute ETF array (open sessions only).
Writes splitgate_results.csv and splitgate_summary.json. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

IX = ROOT / "research" / "bdi" / "indexlink"
PRIMARY = ["MF1-945-flowsell-vwapup-cur", "MF2-open-rsimidhi-flowsell-cur", "MF3-open-flowsell-rsi5hi-cur",
           "MF4-h40-open-flowsell-cur", "MF5-flowsell-vwapup-rsi5hi-cur", "NS2-sma50break-overbought-short-cur",
           "NS3-failed-vwap-reclaim-short-cur", "NS4-pm-vwap-reclaim-oversold-short-cur", "RW6G1-ns2-up3-vwap2sd-short-cur"]
N_LINEAGE = 912 + 1052 + 370
TREQ = gates.t_required(N_LINEAGE)


def ctx():
    meta = json.load(open(IX / "data" / "meta.json"))
    z = np.load(IX / "data" / "etf1m.npz")
    syms = [str(s) for s in z["syms"]]
    out = {}
    for e in ("SPY", "QQQ", "IWM"):
        i = syms.index(e)
        o, h, l, c, v = (z[k][i].astype(float) for k in ("open", "high", "low", "close", "volume"))
        c = pd.DataFrame(c).ffill(axis=1).to_numpy()
        o0 = o[:, 0]
        tp = (np.nan_to_num(h) + np.nan_to_num(l) + c) / 3
        vv = np.nan_to_num(v)
        with np.errstate(all="ignore"):
            vw = np.cumsum(tp * vv, 1) / np.cumsum(vv, 1)
            out[e + "_fo"] = (c / o0[:, None] - 1) * 100
            out[e + "_vw"] = (c / vw - 1) * 100
            c30 = np.full_like(c, np.nan); c30[:, 30:] = c[:, :-30]
            out[e + "_d30"] = (c / c30 - 1) * 100
    return pd.to_datetime(meta["dates"]), out


def cl_t_diff(r, kept, day):
    """kept-minus-blocked mean difference with a cluster-robust (by day) SE."""
    r, kept = np.asarray(r, float), np.asarray(kept, bool)
    nk, nb = kept.sum(), (~kept).sum()
    if nk < 2 or nb < 2:
        return np.nan, np.nan
    mk, mb = r[kept].mean(), r[~kept].mean()
    u = np.where(kept, (r - mk) / nk, -(r - mb) / nb)
    s = pd.Series(u).groupby(np.asarray(day)).sum()
    se = np.sqrt((s ** 2).sum())
    return mk - mb, (mk - mb) / se if se > 0 else np.nan


def stats(d):
    if not len(d):
        return {"n": 0}
    s = gates.summary(d)
    g = d.groupby("date")["r"].agg(["sum", "size"])
    out = {"n": s["n"], "exp": s["exp_r"], "t": s["t"],
           "ex_best": round(float((d.r.sum() - g["sum"].max()) / max(1, len(d) - g["size"].loc[g["sum"].idxmax()])), 4),
           "busiest": round(float(g["size"].max() / len(d)), 3)}
    for nm, m in (("train", d.valid == 0), ("valid", d.valid == 1)):
        out[nm + "_exp"] = round(float(d.r[m].mean()), 4) if m.any() else np.nan
        out[nm + "_n"] = int(m.sum())
    for rg in ("up", "down"):
        m = d.regime == rg
        out[rg + "_exp"] = round(float(d.r[m].mean()), 4) if m.sum() >= 30 else np.nan
    return out


GATES = {
    "G1-split": lambda x: (x.x_QQQ_fo > 0) & (x.x_QQQ_vw > 0) & (x.x_IWM_fo < 0),
    "G2-split-dz": lambda x: (x.x_QQQ_fo > 0.10) & (x.x_QQQ_vw > 0.10) & (x.x_IWM_fo < -0.10),
    "G3-qqq-up": lambda x: (x.x_QQQ_fo > 0) & (x.x_QQQ_vw > 0),
    "G4-qqq-fo": lambda x: x.x_QQQ_fo > 0,
    "G5-spy-up": lambda x: (x.x_SPY_fo > 0) & (x.x_SPY_vw > 0),
    "G6-div0.25": lambda x: (x.x_QQQ_fo - x.x_IWM_fo) >= 0.25,
    "G7-div0.50": lambda x: (x.x_QQQ_fo - x.x_IWM_fo) >= 0.50,
    "G8-div0.75": lambda x: (x.x_QQQ_fo - x.x_IWM_fo) >= 0.75,
    "G9-split+div": lambda x: (x.x_QQQ_fo > 0) & (x.x_QQQ_vw > 0) & (x.x_IWM_fo < 0) & ((x.x_QQQ_fo - x.x_IWM_fo) >= 0.5),
    "G10-split-rebound": lambda x: (x.x_QQQ_d30 > 0) & (x.x_QQQ_vw > 0) & (x.x_IWM_fo < 0),
}


def main():
    dates, C = ctx()
    di = {d: i for i, d in enumerate(dates)}
    T = pd.read_parquet(IX / "data" / "gate_trades.parquet")
    T = T[(T.side == "short") & ~T.list.isin(["orb20_a-cur", "intraday_momentum-cur"])].copy()   # PLAN: 35 short lists
    T["date"] = pd.to_datetime(T["date"])
    T["s"] = T["date"].map(di)
    assert T["s"].notna().all()
    s = T["s"].to_numpy(int)
    m = ((T.tod // 100) * 60 + T.tod % 100).to_numpy() - 570 - 1          # last minute of the entry bar
    for k, a in C.items():
        T["x_" + k] = a[s, m]
    par = {"QQQ_fo_absdiff_p50_p99": [float(np.nanpercentile(np.abs(T.x_QQQ_fo - T.QQQ_fo), q)) for q in (50, 99)],
           "QQQ_vw_absdiff_p50_p99": [float(np.nanpercentile(np.abs(T.x_QQQ_vw - T.QQQ_vw), q)) for q in (50, 99)],
           "ctx_missing": int(T[["x_QQQ_fo", "x_IWM_fo", "x_QQQ_vw"]].isna().any(axis=1).sum())}
    print("parity", par, flush=True)
    reg = lib.regimes()
    rm = {pd.Timestamp(k): v for k, v in reg["regime"].items()}
    T["regime"] = T["date"].map(rm)
    T["valid"] = (T["date"] > "2025-12-31").astype(int)
    books = {l: T[T.list == l] for l in sorted(T.list.unique())}
    assert len(books) == 35, len(books)
    books["POOL-primary"] = T[T.list.isin(PRIMARY)]
    books["POOL-testing1"] = T[~T.list.isin(PRIMARY)]
    rows = []
    for b, d in books.items():
        d = d.reset_index(drop=True)
        base = stats(d)
        for g, f in GATES.items():
            blk = f(d).fillna(False).to_numpy(bool)
            k = d[~blk]
            st = stats(k)
            diff, tdiff = cl_t_diff(d.r, ~blk, d.date)
            row = {"book": b, "gate": g, "base_n": base["n"], "base_exp": base["exp"], "base_t": base["t"],
                   "base_train": base["train_exp"], "base_valid": base["valid_exp"],
                   "blocked_n": int(blk.sum()), "blocked_share": round(float(blk.mean()), 3),
                   "blocked_exp": round(float(d.r[blk].mean()), 4) if blk.any() else np.nan,
                   "kept_minus_blocked": round(diff, 4), "kmb_t": round(tdiff, 2)}
            row.update({"kept_" + kk: v for kk, v in st.items()})
            row["chg_open"] = round(st["exp"] - base["exp"], 4)
            row["chg_train"] = round(st["train_exp"] - base["train_exp"], 4)
            row["chg_valid"] = round(st["valid_exp"] - base["valid_exp"], 4)
            wf = gates.walk_forward(k[["date", "r"]], exclude_months=lib.LOCKED_MONTHS) if len(k) else {}
            row["kept_wf"] = wf.get("share_positive")
            rows.append(row)
    R = pd.DataFrame(rows)
    R["primary_pass"] = ((R.kept_n >= 150) & (R.kept_exp > 0) & (R.kept_t >= TREQ) & (R.kept_up_exp > 0) &
                         (R.kept_down_exp > 0) & (R.kept_wf >= 0.6) & (R.kept_ex_best > 0) & (R.kept_busiest <= 0.10) &
                         (R.chg_train > 0) & (R.chg_valid > 0))
    R.to_csv(HERE / "splitgate_results.csv", index=False)
    lists = R[~R.book.str.startswith("POOL")]
    summ = {"n_configs": int(len(R)), "lineage_N": N_LINEAGE, "t_required": TREQ, "parity": par,
            "primary_pass": R[R.primary_pass][["book", "gate"]].values.tolist(), "per_gate": {}}
    for g in GATES:
        x = lists[lists.gate == g]
        p1, p2 = R[(R.book == "POOL-primary") & (R.gate == g)].iloc[0], R[(R.book == "POOL-testing1") & (R.gate == g)].iloc[0]
        summ["per_gate"][g] = {
            "lists_improved_train_and_valid": int(((x.chg_train > 0) & (x.chg_valid > 0)).sum()),
            "lists_improved_open": int((x.chg_open > 0).sum()), "n_lists": int(len(x)),
            "pool_primary": {k: p1[k] for k in ("blocked_share", "base_exp", "kept_exp", "blocked_exp", "kept_minus_blocked", "kmb_t", "chg_train", "chg_valid", "kept_up_exp", "kept_down_exp")},
            "pool_testing1": {k: p2[k] for k in ("blocked_share", "base_exp", "kept_exp", "blocked_exp", "kept_minus_blocked", "kmb_t", "chg_train", "chg_valid", "kept_up_exp", "kept_down_exp")}}
    json.dump(summ, open(HERE / "splitgate_summary.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    pd.set_option("display.width", 250)
    P = R[R.book.str.startswith("POOL")][["book", "gate", "base_n", "base_exp", "blocked_share", "kept_exp", "kept_t", "blocked_exp", "kept_minus_blocked", "kmb_t", "chg_train", "chg_valid", "kept_up_exp", "kept_down_exp", "kept_wf"]]
    print(P.to_string(index=False))
    print(json.dumps({g: (v["lists_improved_train_and_valid"], v["lists_improved_open"]) for g, v in summ["per_gate"].items()}))
    print("primary_pass", summ["primary_pass"])


if __name__ == "__main__":
    main()
