"""Part B: stock-level dip-timed longs (88 configs). Outputs results_B.csv. Educational only - not financial advice."""
import numpy as np
import pandas as pd

from common import HERE, SCR, regimes, split_of
from mcf.research import gates

PG = {"NS1": "t05s1", "NS5": "t1s1", "ST2": "t05s1", "ST4": "t1s05"}
LAB = ("t1s1", "t05s1", "t1s05")


def main():
    T = pd.read_parquet(SCR / "b_trades.parquet")
    T["date"] = pd.to_datetime(T["date"]).dt.date
    S = pd.read_parquet(SCR / "sim.parquet", columns=["symbol", "date", "tod", "s_holdtr", "s_time60"])
    S["date"] = pd.to_datetime(S["date"]).dt.date
    C = pd.read_parquet(SCR / "ctrl_rows.parquet", columns=["symbol", "date", "tod"])
    C["date"] = pd.to_datetime(C["date"]).dt.date
    C = C.merge(S, on=["symbol", "date", "tod"], how="left")
    cm = C.groupby(["date", "tod"])[["s_holdtr", "s_time60"]].mean().rename(columns=lambda k: "c_" + k[2:])
    T = T.merge(S, on=["symbol", "date", "tod"], how="left").merge(cm, left_on=["date", "tod"], right_index=True, how="left")
    T["split"] = split_of(T["date"])
    T["regime"] = T["date"].map(regimes())
    nses = T.groupby("split")["date"].nunique()            # sessions with any trade (frames sessions ~ all)
    frames_sessions = {"train": 0, "valid": 0}
    ctx = pd.read_parquet(SCR / "ctx.parquet", columns=["date"]).drop_duplicates()
    for sp, n in pd.Series(split_of(ctx["date"])).value_counts().items():
        frames_sessions[sp] = int(n)
    rows = []
    parent_exp = {}
    bases = sorted(T["base"].unique(), key=lambda b: (b.startswith("B5"), not b.endswith("parent"), b))
    for b in bases:
        if b.startswith("B5"):
            p = b.split("-")[1]
            exits = (PG[p], "holdtr")
        else:
            exits = ("t1s1", "t05s1", "holdtr", "time60")
        g0 = T[T.base == b]
        for ex in exits:
            rc, cc = ("r_" + ex, "c_" + ex) if ex in LAB else ("s_" + ex, "c_" + ex)
            g = g0[["date", "symbol", "split", "regime", "spy_fo", rc, cc]].rename(columns={rc: "r", cc: "c"}).dropna(subset=["r"])
            rec = dict(cfg=f"{b}-{ex}", part="B5-parent" if b.endswith("parent") else ("B5" if b.startswith("B5") else "B"),
                       base=b, exit=ex)
            for sp in ("train", "valid"):
                x = g[g.split == sp]
                st = gates.summary(x[["date", "r"]])
                rec.update({f"{sp}_n": st.get("n", 0), f"{sp}_exp": st.get("exp_r"), f"{sp}_t": st.get("t"),
                            f"{sp}_per_day": round(st.get("n", 0) / max(1, frames_sessions[sp]), 2),
                            f"{sp}_ex_best": st.get("ex_best_day"), f"{sp}_ctrl": round(float(x["c"].mean()), 4) if len(x) else None})
                xe = x.dropna(subset=["c"]).assign(r=lambda z: z["r"] - z["c"])
                se = gates.summary(xe[["date", "r"]])
                rec[f"{sp}_excess"], rec[f"{sp}_excess_t"] = se.get("exp_r"), se.get("t")
                if b.startswith("B5") and not b.endswith("parent"):
                    rec[f"{sp}_parent_exp"] = parent_exp.get((b.split("-")[1], ex, sp))
            for k in ("up", "flat", "down"):
                st = gates.summary(g[g.regime == k][["date", "r"]])
                rec[f"{k}_n"], rec[f"{k}_exp"], rec[f"{k}_t"] = st.get("n", 0), st.get("exp_r"), st.get("t")
            st = gates.summary(g[g.spy_fo <= -0.3][["date", "r"]])
            rec["badtape_n"], rec["badtape_exp"] = st.get("n", 0), st.get("exp_r")
            st = gates.summary(g[["date", "r"]])
            rec["all_n"], rec["all_exp"], rec["all_t"], rec["all_ex_best"] = st.get("n", 0), st.get("exp_r"), st.get("t"), st.get("ex_best_day")
            if b.endswith("parent"):
                for sp in ("train", "valid"):
                    parent_exp[(b.split("-")[1], ex, sp)] = rec[f"{sp}_exp"]
            rows.append(rec)
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "results_B.csv", index=False)
    cols = ["cfg", "train_n", "train_exp", "train_t", "train_excess", "valid_n", "valid_exp", "valid_t", "valid_excess",
            "valid_per_day", "up_exp", "down_exp", "badtape_exp"]
    print(res[cols].sort_values("valid_t", ascending=False).to_string())


if __name__ == "__main__":
    main()
