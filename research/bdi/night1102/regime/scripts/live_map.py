"""night1102/regime step 2: regime map of the live book (paper, run 1, all accounts, 2026-10-06..11-02).
Per trade: EOD type of its session (eod3 up/down/quiet at +-0.25% SPY open-to-close; eod4 Bull/Bear/Choppy/Quiet as
regime1022) and at-entry state (SPY vs VWAP, SPY from open, breadth proxy RSP-SPY, at the last 1-minute bar closed
at or before the entry minute). Per setup with 30+ trades: R by type, day-clustered. Educational only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from live import trades

SCR = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[1]


def tagged() -> pd.DataFrame:
    T = trades(SCR)
    D = pd.read_parquet(SCR / "days.parquet")
    M = pd.read_parquet(SCR / "minute.parquet"); M["tod"] = M["tod"].astype("int64"); M = M.sort_values("tod")
    T = T.sort_values("etod")
    T["etod_i"] = T["etod"].astype("int64")
    T = pd.merge_asof(T, M[["date", "tod", "fo_SPY", "vw_SPY", "br"]].rename(columns={"tod": "etod_i"}),
                      on="etod_i", by="date", direction="backward")
    for c in ("eod3", "eod4", "o2c", "vw_SPY@950", "vw_SPY@1000", "vw_SPY@1030", "fo_SPY@1000", "fo_SPY@1030",
              "br@1000", "br@1030"):
        T[c] = T["date"].map(D[c])
    T["vwap_side"] = np.where(T["vw_SPY"] >= 0, "SPY>VWAP", "SPY<VWAP")
    T["with_tape"] = np.where(np.sign(T["fo_SPY"]) == np.sign(T["side"]), "with", "against")
    return T.reset_index(drop=True)


def cl(r: pd.Series, d: pd.Series):
    """mean, day-clustered t, n, sessions."""
    n = len(r)
    if n == 0:
        return np.nan, np.nan, 0, 0
    m = r.mean()
    g = pd.DataFrame({"r": r.to_numpy(), "d": d.to_numpy()}).groupby("d")["r"].agg(["sum", "size"])
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / n if len(g) > 1 else np.nan
    return m, (m / se if se and se > 0 else np.nan), n, len(g)


def main():
    T = tagged()
    T.to_parquet(SCR / "tagged.parquet")
    rows = []
    cnt = T.groupby("strategy").size()
    for s in cnt[cnt >= 30].index:
        t = T[T.strategy == s]
        r = {"setup": s, "side": "long" if t.side.mean() > 0 else "short", "accts": ",".join(sorted(set(t.acct))),
             "first": str(t.date.min()), "last": str(t.date.max())}
        m, tt, n, k = cl(t.R, t.date)
        r.update(n=n, sessions=k, avgR=m, t=tt, sumR=t.R.sum())
        dr = t.groupby("date").R.sum()
        r["best_day_share"] = dr.max() / dr[dr > 0].sum() if (dr > 0).any() else np.nan
        r["avgR_wo_best"] = t[t.date != dr.idxmax()].R.mean()
        o2c = pd.Series(dr.index.map(pd.read_parquet(SCR / "days.parquet")["o2c"]), index=dr.index)
        r["corr_spy"] = np.corrcoef(dr, o2c)[0, 1] if len(dr) > 3 else np.nan
        for col, labs in (("eod3", ["up", "down", "quiet"]), ("eod4", ["Bull", "Bear", "Choppy", "Quiet"]),
                          ("vwap_side", ["SPY>VWAP", "SPY<VWAP"]), ("with_tape", ["with", "against"])):
            for L in labs:
                x = t[t[col] == L]
                m, tt, n, k = cl(x.R, x.date)
                r[f"{L}_n"], r[f"{L}_d"], r[f"{L}_avg"], r[f"{L}_t"] = n, k, m, tt
        rows.append(r)
    R = pd.DataFrame(rows)
    ok = [R[f"{L}_d"] >= 2 for L in ("up", "down", "quiet")]
    R["robust3"] = (R["up_avg"] > 0) & (R["down_avg"] > 0) & (R["quiet_avg"] > 0) & ok[0] & ok[1] & ok[2]
    R["n_pos_eod3"] = sum((R[f"{L}_avg"] > 0).astype(int) for L in ("up", "down", "quiet"))
    R = R.sort_values("sumR")
    R.round(4).to_csv(OUT / "live_regime_map.csv", index=False)
    pd.set_option("display.width", 300)
    cols = ["setup", "side", "accts", "n", "sessions", "avgR", "t", "corr_spy", "up_n", "up_avg", "down_n", "down_avg",
            "quiet_n", "quiet_avg", "SPY>VWAP_avg", "SPY<VWAP_avg", "with_avg", "against_avg", "n_pos_eod3"]
    print(R[cols].round(3).to_string(index=False))
    # book-level
    print("\nall live trades by eod3 x side")
    print(T.groupby(["eod3", "side"]).R.agg(["size", "mean", "sum"]).round(3))
    print(T.groupby(["vwap_side", "side"]).R.agg(["size", "mean", "sum"]).round(3))
    print(T.groupby(["with_tape", "side"]).R.agg(["size", "mean", "sum"]).round(3))
    print(R.groupby("side").corr_spy.describe())
    print("robust3:", R.robust3.sum(), R[R.robust3].setup.tolist())


if __name__ == "__main__":
    main()
