"""regime1022 Part C (ii): can the session's regime be identified AT ENTRY? For each at-entry proxy and checkpoint,
precision / recall / lift for calling a Bull or a Bear session (hindsight labels from regime.py), TRAIN vs VALID.
One observation per session. Writes detect.csv. Descriptive (counted in counts.json). Educational only - not
financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from rc import HERE, SCR, lib, split_of
from regime import day_table

CHECK = (1000, 1030, 1100, 1200)


def session_state() -> pd.DataFrame:
    ctx = pd.concat([lib.load_context(m) for m in lib.months()], ignore_index=True)
    ctx["date"] = pd.to_datetime(ctx["date"]).dt.date
    idx = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "idx").glob("*.parquet"))], ignore_index=True)
    idx["date"] = pd.to_datetime(idx["date"]).dt.date
    spy = idx[idx["symbol"] == "SPY"][["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "spy_vwap"})
    ctx = ctx.merge(spy, on=["date", "tod"], how="left")
    rows = []
    for c in CHECK:
        x = ctx[ctx["tod"] == c].set_index("date")
        pt = max(950, (c - 30) if c % 100 >= 30 else (c - 70))      # 10:00 uses 09:50 (frames start 09:50)
        prev = ctx[ctx["tod"] == pt].set_index("date")["breadth"]
        x = x.assign(b_slope=x["breadth"] - prev.reindex(x.index), check=c)
        rows.append(x.reset_index())
    return pd.concat(rows, ignore_index=True)


def main():
    dt = day_table()
    st = session_state().join(dt[["regime", "spy_prev", "spy_c2c_today"]], on="date")
    st = st[st["regime"].notna()]
    st["split"] = split_of(st["date"])
    calls = {
        "HINDSIGHT (gates1021 spy_prev bug): today's SPY close-to-close >= +0.5% | <= -0.5%":
            (st["spy_c2c_today"] >= 0.5, st["spy_c2c_today"] <= -0.5),
        "prior SPY >= +0.5% | <= -0.5%": (st["spy_prev"] >= 0.5, st["spy_prev"] <= -0.5),
        "SPY from open >= +0.25% | <= -0.25%": (st["spy_fo"] >= 0.25, st["spy_fo"] <= -0.25),
        "SPY from open >= +0.5% | <= -0.5%": (st["spy_fo"] >= 0.5, st["spy_fo"] <= -0.5),
        "QQQ from open >= +0.25% | <= -0.25%": (st["qqq_fo"] >= 0.25, st["qqq_fo"] <= -0.25),
        "SPY above | below its VWAP": (st["spy_vwap"] > 0, st["spy_vwap"] < 0),
        "SPY >= +0.25% and above VWAP | mirror": ((st["spy_fo"] >= 0.25) & (st["spy_vwap"] > 0),
                                                 (st["spy_fo"] <= -0.25) & (st["spy_vwap"] < 0)),
        "breadth >= 0.6 | <= 0.4": (st["breadth"] >= 0.6, st["breadth"] <= 0.4),
        "breadth rising >= 0.1 in 30 min | falling": (st["b_slope"] >= 0.1, st["b_slope"] <= -0.1),
        "prior SPY >= +0.5% and SPY >= 0 | mirror": ((st["spy_prev"] >= 0.5) & (st["spy_fo"] >= 0),
                                                    (st["spy_prev"] <= -0.5) & (st["spy_fo"] <= 0)),
    }
    out = []
    for name, (up, dn) in calls.items():
        for c in CHECK:
            for sp in ("train", "valid"):
                m = (st["check"] == c) & (st["split"] == sp)
                g = st[m]
                for target, call in (("Bull", up[m]), ("Bear", dn[m])):
                    y = g["regime"] == target
                    n_call = int(call.sum())
                    prec = float(y[call].mean()) if n_call else np.nan
                    rec = float(call[y].mean()) if y.sum() else np.nan
                    base = float(y.mean())
                    # the opposite outcome among the calls (e.g. called Bull, ended Bear)
                    opp = "Bear" if target == "Bull" else "Bull"
                    wrong = float((g["regime"][call] == opp).mean()) if n_call else np.nan
                    out.append({"proxy": name, "check": c, "split": sp, "target": target, "sessions": len(g),
                                "calls": n_call, "base_rate": round(base, 3), "precision": round(prec, 3),
                                "recall": round(rec, 3), "lift": round(prec / base, 2) if base else np.nan,
                                "opposite_rate": round(wrong, 3)})
    df = pd.DataFrame(out)
    df.to_csv(HERE / "detect.csv", index=False)
    piv = df[df["check"].isin([1030, 1100])].pivot_table(index=["proxy", "target", "check"], columns="split",
                                                          values=["precision", "recall", "lift"])
    print(piv.round(2).to_string())


if __name__ == "__main__":
    main()
