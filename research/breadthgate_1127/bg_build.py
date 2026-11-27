"""BREADTHGATE-1127 lot table: bench10 lots (Primary 4 + 3 info GENs from the P4/arenastars bench run, 7 arena setups from
bg_gen.py, GEN-261020-09 from regsteer_1126 cand.parquet) -> bench10 add_r (LR8) -> price >= $5, ETB shorts -> LIVE-L on
shorts (primshorts_1126 cells_live.json; longs keep LR8) -> breadth / breadth_open at the decision bar (T1 lab context,
T2 bg_t2ctx.py). Usage (cwd = repo): python bg_build.py W  -> W/lots.parquet. Parity: P4 LIVE-L r vs cand.parquet.
Locked block 2024-11-01..2025-02-28 never read (asserted). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
sys.path.insert(0, str(ROOT / "research/primshorts_1126"))
import bench10 as B  # noqa: E402
import calib_live as CLV  # noqa: E402

W = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
CTX = Path("/home/user/MCF/research/history2y/data/context")
GEN20 = "GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long"


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def costed(x, etb, cells):
    x = x.copy(); x["date"] = x.date.astype(str)
    no_locked(x.date.unique())
    x = B.add_r(x)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"]
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)].copy()
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_lr8"] = x.r
    x["r_live"] = np.where(x.side < 0, x.r_gross - CLV.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd), x.r)
    return x[["setup", "symbol", "date", "per", "tod", "em", "xm", "side", "entry", "risk", "r_live", "r_lr8"]]


if __name__ == "__main__":
    etb = pd.read_parquet(W / "etb_rate.parquet").rate
    cells = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))
    p4 = pd.concat([pd.read_parquet(W / f"p4_trades_t{k}.parquet") for k in (1, 2)], ignore_index=True)
    p4 = p4[~p4.setup.str.startswith("RND-")]
    ar = pd.concat([pd.read_parquet(W / "a" / f"trades_t{k}.parquet") for k in (1, 2)], ignore_index=True)
    lots = pd.concat([costed(p4, etb, cells), costed(ar, etb, cells)], ignore_index=True)
    cand = pd.read_parquet(W / "cand.parquet")
    no_locked(cand.date.unique())
    g = cand[cand.setup == GEN20].copy()
    assert (g.side > 0).all()
    g["r_live"] = g.r; g["r_lr8"] = g.r
    lots = pd.concat([lots, g[lots.columns]], ignore_index=True)
    # parity: Primary 4 LIVE-L r vs regsteer cand
    c4 = cand[cand.setup.isin(lots.setup.unique())]
    m = lots.groupby(["setup", "per"]).r_live.agg(["count", "mean"]).join(
        c4.groupby(["setup", "per"]).r.agg(["count", "mean"]), rsuffix="_cand")
    print("parity vs cand.parquet\n", m.dropna().round(4).to_string())
    # breadth at the decision bar
    t1 = pd.concat([pd.read_parquet(p) for p in sorted(CTX.glob("month=*.parquet"))], ignore_index=True)
    t1["date"] = pd.to_datetime(t1.date).dt.date.astype(str)
    t2 = pd.read_parquet(W / "ctx_t2.parquet"); t2["date"] = t2.date.astype(str)
    ctx = pd.concat([t1[["date", "tod", "breadth", "breadth_open"]], t2[["date", "tod", "breadth", "breadth_open"]]])
    no_locked(ctx.date.unique())
    ctx = ctx.drop_duplicates(["date", "tod"])
    lots["tod"] = lots.tod.astype(int)
    lots = lots.merge(ctx, on=["date", "tod"], how="left")
    no_locked(lots.date.unique())
    lots.to_parquet(W / "lots.parquet", index=False)
    print(lots.groupby(["setup", "per"]).agg(n=("r_live", "size"), live=("r_live", "mean"), lr8=("r_lr8", "mean"),
                                             br_na=("breadth", lambda s: s.isna().mean())).round(4).to_string())
