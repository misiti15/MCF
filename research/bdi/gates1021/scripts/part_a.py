"""gates1021 Part A: NS3-failed-vwap-reclaim-short-FD and L3-gap-slope-fromopen-FD, live-shaped (refire cd1 + lot cap
3), 16 configurations each (PLAN.md). Writes results_A.csv, states_A.csv, stacking_A.csv, trades_A.parquet (scratch).
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import HERE, SCR, gates
from load import day_delta, load_sig

PART_A = {"NS3-failed-vwap-reclaim-short-FD": ("short", "t1s1"), "L3-gap-slope-fromopen-FD": ("short", "t1s1")}


def sequence(s: pd.DataFrame, cap=3, no_after_stop=False, max_open=None, day_stop=None) -> np.ndarray:
    """Keep-mask over signals s (one setup) under the live lot rules, processed day by day in time order."""
    keep = np.zeros(len(s), bool)
    s = s.reset_index(drop=True)
    for _, g in s.groupby("date", sort=False):
        g = g.sort_values(["tod", "symbol"], kind="mergesort")
        lots = []          # (symbol, exit_tod, r, kind)
        closed = []
        for i, row in zip(g.index, g.itertuples()):
            t = row.tod
            still = []
            for L in lots:
                (closed if L[1] <= t else still).append(L)
            lots = still
            if day_stop is not None and sum(L[2] for L in closed) <= day_stop:
                continue
            if no_after_stop and any(L[0] == row.symbol and L[3] == 1 for L in closed):
                continue
            if sum(L[0] == row.symbol for L in lots) >= cap:
                continue
            if max_open is not None and len(lots) >= max_open:
                continue
            keep[i] = True
            lots.append((row.symbol, row.exit_tod, row.r, row.exit_kind))
    return keep


def first_of_day(s: pd.DataFrame) -> np.ndarray:
    k = s["symbol"].astype(str) + "|" + s["date"].astype(str)
    return ~k.duplicated().to_numpy()


def stats(x: pd.DataFrame, par: pd.DataFrame, ccol: str) -> dict:
    out = {}
    for sp, xx in [("all", x), ("train", x[x["split"] == "train"]), ("valid", x[x["split"] == "valid"])]:
        pp = par if sp == "all" else par[par["split"] == sp]
        sm = gates.summary(xx[["date", "r"]])
        out[f"{sp}_n"] = sm.get("n", 0)
        out[f"{sp}_exp"] = sm.get("exp_r")
        out[f"{sp}_t"] = sm.get("t")
        out[f"{sp}_kept_pct"] = round(100 * len(xx) / max(1, len(pp)), 1)
        dd = day_delta(xx, pp)
        out[f"{sp}_delta"], out[f"{sp}_delta_t"] = dd["delta"], dd["t"]
        out[f"{sp}_excess"] = round(float((xx["r"] - xx[ccol]).mean()), 4) if len(xx) else None
    out["ex_best_day"] = gates.summary(x[["date", "r"]]).get("ex_best_day")
    pw = par["r"] > 0
    out["winners_blocked_pct"] = round(100 * (1 - x["r"].gt(0).sum() / max(1, pw.sum())), 1)
    for reg in ("up", "flat", "down"):
        xx = x[x["regime"] == reg]
        out[f"{reg}_exp"] = round(float(xx["r"].mean()), 4) if len(xx) else None
    ch = x[x["choppy"]]
    pc = par[par["choppy"]]
    out["choppy_kept_pct"] = round(100 * len(ch) / max(1, len(pc)), 1)
    out["choppy_exp"] = round(float(ch["r"].mean()), 4) if len(ch) else None
    out["choppy_delta"] = day_delta(ch, pc)["delta"]
    out["per_day"] = round(len(x) / max(1, x["date"].nunique()), 2)
    return out


def main():
    sig = load_sig(list(PART_A))
    rows, states, stack, keep_tr = [], [], [], []
    for name, (side, geom) in PART_A.items():
        s = sig[sig["setup"] == name].sort_values(["date", "tod", "symbol"]).reset_index(drop=True)
        ccol = f"c_{side}_{geom}"
        # path vs frame outcome agreement (stop / target kinds vs the frame win flag)
        dec = s["exit_kind"].isin([1, 2])
        agree = float(((s.loc[dec, "exit_kind"] == 2) == (s.loc[dec, "win"] == 1)).mean())
        a0 = sequence(s)
        par = s[a0]
        var = {"A0 parent-live (refire cd1 + lot cap 3)": a0}
        fo = first_of_day(s)
        k = np.zeros(len(s), bool)
        k[np.flatnonzero(fo)[sequence(s[fo].reset_index(drop=True))]] = True
        var["A1 first signal per symbol-day"] = k
        var["g1 no re-entry after a stop"] = sequence(s, no_after_stop=True)
        var["g2 one lot at a time per symbol"] = sequence(s, cap=1)

        def gated(block):
            kk = np.zeros(len(s), bool)
            idx = np.flatnonzero(~block)
            kk[idx[sequence(s.iloc[idx].reset_index(drop=True))]] = True
            return kk

        d2 = s["d2"].to_numpy(float)
        for x in (0.25, 0.50):
            var[f"g3 skip spy_fo>={x:.2f} & breadth rising"] = gated((s["spy_fo"].to_numpy() >= x) & (d2 > 0))
        for x in (0.25, 0.50):
            var[f"g4 skip qqq_fo>={x:.2f}"] = gated(s["qqq_fo"].to_numpy() >= x)
        for y in (1.0, 2.0):
            var[f"g5 skip peer median fo>={y:.0f}% (needs live code)"] = gated(s["peer_med"].to_numpy(float) >= y)
        var["g6 only <=11:30"] = gated(s["tod"].to_numpy() > 1130)
        var["g6 only <=13:00"] = gated(s["tod"].to_numpy() > 1300)
        var["g6 only >=10:30"] = gated(s["tod"].to_numpy() < 1030)
        for K in (5, 10):
            var[f"g7 skip when setup holds >={K} open lots"] = sequence(s, max_open=K)
        var["g8 per-setup -2R realized daily stop"] = sequence(s, day_stop=-2.0)
        for vname, kk in var.items():
            x = s[kk]
            r = {"setup": name, "variant": vname, **stats(x, par, ccol)}
            rows.append(r)
        # descriptive state splits of A0
        p = par.copy()
        bk = {
            "spy_fo": pd.cut(p["spy_fo"], [-99, -0.5, -0.15, 0.15, 0.5, 99], right=False),
            "qqq_fo": pd.cut(p["qqq_fo"], [-99, -0.5, -0.15, 0.15, 0.5, 99], right=False),
            "breadth": pd.cut(p["breadth"], [0, 0.35, 0.5, 0.65, 1.01], right=False),
            "d2": pd.cut(p["d2"], [-9, -0.05, 0.05, 9], right=False),
            "spy_prev": pd.cut(p["spy_prev"], [-99, -0.5, 0.5, 99], right=False),
            "regime(hindsight)": p["regime"], "choppy(hindsight)": p["choppy"],
            "tod": pd.cut(p["tod"], [950, 1030, 1130, 1300, 1400, 1501], right=False),
        }
        for fam, b in bk.items():
            for sp in ("train", "valid"):
                q = p[p["split"] == sp]
                bb = b[p["split"] == sp]
                for lev, g in q.groupby(bb.astype(str), observed=True):
                    sm = gates.summary(g[["date", "r"]])
                    states.append({"setup": name, "family": fam, "bucket": lev, "split": sp, "n": sm["n"],
                                   "share": round(sm["n"] / len(q), 3), "exp": sm["exp_r"], "t": sm["t"],
                                   "ctrl_exp": round(float(g[ccol].mean()), 4), "excess": round(float((g["r"] - g[ccol]).mean()), 4)})
        # stacking / re-entry / cluster diagnostics on A0
        p = p.sort_values(["date", "symbol", "tod"])
        p["lot_no"] = p.groupby(["date", "symbol"]).cumcount() + 1
        # stopped-before flag
        aft = []
        for (d, sy), g in p.groupby(["date", "symbol"], sort=False):
            st = []
            for row in g.itertuples():
                aft.append(any(e <= row.tod and k == 1 for e, k in st))
                st.append((row.exit_tod, row.exit_kind))
        p["after_stop"] = aft
        opn = []
        for d, g in p.groupby("date", sort=False):
            ex = g["exit_tod"].to_numpy()
            tt = g["tod"].to_numpy()
            for t in tt:
                opn.append(int(((tt < t) & (ex > t)).sum()))
        p["open_lots_at_entry"] = opn
        for lab, m in [("lot 1 (first on symbol-day)", p["lot_no"] == 1), ("lot 2", p["lot_no"] == 2),
                       ("lot 3+", p["lot_no"] >= 3), ("re-entry after a stop", p["after_stop"]),
                       ("setup open lots 0-4", p["open_lots_at_entry"] < 5),
                       ("setup open lots 5-9", p["open_lots_at_entry"].between(5, 9)),
                       ("setup open lots >=10", p["open_lots_at_entry"] >= 10)]:
            for sp in ("train", "valid"):
                g = p[m & (p["split"] == sp)]
                sm = gates.summary(g[["date", "r"]]) if len(g) else {"n": 0}
                stack.append({"setup": name, "group": lab, "split": sp, "n": sm.get("n", 0),
                              "share": round(len(g) / max(1, (p["split"] == sp).sum()), 3), "exp": sm.get("exp_r"),
                              "t": sm.get("t")})
        # daily concentration: share of A0 days with <= -5R and their share of total loss
        dd = p.groupby("date")["r"].sum()
        stack.append({"setup": name, "group": f"days <= -5R: {int((dd <= -5).sum())} of {len(dd)}; their R "
                      f"{dd[dd <= -5].sum():.1f} vs total {dd.sum():.1f}; path/frame outcome agreement {agree:.3f}",
                      "split": "all", "n": len(p)})
        keep_tr.append(p.assign(setup=name))
    pd.DataFrame(rows).to_csv(HERE / "results_A.csv", index=False)
    pd.DataFrame(states).to_csv(HERE / "states_A.csv", index=False)
    pd.DataFrame(stack).to_csv(HERE / "stacking_A.csv", index=False)
    pd.concat(keep_tr).to_parquet(SCR / "trades_A0.parquet")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(pd.DataFrame(rows)[["setup", "variant", "all_n", "all_exp", "all_t", "train_exp", "valid_exp", "train_kept_pct",
                              "valid_kept_pct", "train_delta", "train_delta_t", "valid_delta", "valid_delta_t",
                              "all_delta_t", "choppy_delta", "winners_blocked_pct"]].to_string())


if __name__ == "__main__":
    main()
