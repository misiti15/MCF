"""top20 (2026-11-04): 5 pre-declared "half size" checks from tonight's live + 2-year condition read (not filters: each
condition holds > 30% of trades or > 10% of top-decile winners). R per unit of risk = sum(w * R) / sum(w), w = 0.5 in
the condition, else 1. BACKTEST rows = gates1021 live-shaped signals (TRAIN / VALID, costs in, locked block never
loaded); LIVE = paper trades 10-06..11-04. Day-clustered t of the paired difference vs full size.
    G21SCR=/dev/shm/t5_1104/g python sizing_check.py /dev/shm/t5_1104/a   -> sizing_check.csv
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
import conditions_2y as C2  # noqa: E402
from load import load_sig  # noqa: E402

CHECKS = [("MF4-h40-open-flowsell-FD", "spyfob", "flat"),          # S1 (top5_1104/PLAN.md section 4)
          ("RW7-gapdn-bounce-early-short-FD", "spy10b", "flat"),    # S2
          ("NS4-pm-vwap-reclaim-oversold-short", "atrb", "2-3.5"),  # S3
          ("MF3-open-flowsell-rsi5hi", "todb", "0950-1030"),        # S4
          ("exhaustion_short", "spy10b", "below")]                  # S5


def score(d, rcol, cond):
    w = np.where(cond, 0.5, 1.0)
    d = d.assign(w=w, wr=w * d[rcol], r0=d[rcol])
    g = d.groupby("date").agg(wr=("wr", "sum"), w=("w", "sum"), r0=("r0", "sum"), n=("r0", "size"))
    full = g.r0.sum() / g.n.sum(); half = g.wr.sum() / g.w.sum()
    # paired day-clustered t of (half-size R per risk unit - full-size R per trade)
    e = (g.wr - half * g.w) / g.w.sum() - (g.r0 - full * g.n) / g.n.sum()   # linearised ratio difference per day
    diff = half - full
    se = np.sqrt((e ** 2).sum())
    return dict(n=len(d), cond_share=float(np.mean(cond)), full=round(full, 4), half=round(half, 4), d=round(diff, 4),
                t=round(diff / se, 2) if se > 0 else np.nan)


def main():
    S = load_sig([c[0] for c in CHECKS])
    S["sp"] = C2.split(S["date"]); S = S[S.sp != "hold"].copy()
    S["dkey"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m-%d"); S = S.join(C2.spy10(), on="dkey")
    b = lambda v: np.where(v > 0.10, "above", np.where(v < -0.10, "below", "flat"))
    S["spy10b"], S["spyfob"] = b(S.spy10), b(S.spy_fo)
    S["r"] = S["r"] / S["setup"].map(C2.STOP_UNITS).fillna(1.0)
    S["atrb"] = pd.cut(S.atr_d / S.close * 100, [0, 2, 3.5, 5, 1e9], right=False, labels=["<2", "2-3.5", "3.5-5", ">=5"]).astype(str)
    S["todb"] = pd.cut(S.tod, [0, 1030, 1130, 1300, 1400, 1700], right=False,
                       labels=["0950-1030", "1030-1130", "1130-1300", "1300-1400", "1400-1600"]).astype(str)
    L = pd.read_parquet(Path(sys.argv[1]) / "live_feat.parquet")
    rows = []
    for s, dim, k in CHECKS:
        for sp in ("train", "valid"):
            d = S[(S.setup == s) & (S.sp == sp)]
            rows.append(dict(setup=s, cond=f"{dim}={k}", src=f"2y {sp}", **score(d, "r", (d[dim] == k).to_numpy())))
        d = L[L.strategy == s]
        rows.append(dict(setup=s, cond=f"{dim}={k}", src="live", **score(d, "r_multiple", (d[dim] == k).to_numpy())))
    R = pd.DataFrame(rows); R.to_csv(OUT / "sizing_check.csv", index=False); print(R.to_string(index=False))


if __name__ == "__main__":
    main()
