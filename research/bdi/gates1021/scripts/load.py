"""gates1021: load the scan output with controls, regimes and day types. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import SCR, lib, no_locked, split_of


def day_table() -> pd.DataFrame:
    d = lib.daily()
    spy = d[d["symbol"] == "SPY"].set_index("date")
    reg = lib.regimes()["regime"]
    out = pd.DataFrame({"spy_o2c": (spy["close"] / spy["open"] - 1) * 100})
    out["regime"] = reg
    out["choppy"] = out["spy_o2c"].abs() < 0.3
    return out


def load_sig(setups=None) -> pd.DataFrame:
    parts = []
    for p in sorted((SCR / "sig").glob("*.parquet")):
        x = pd.read_parquet(p)
        if "error" in x:
            x = x[x["error"].isna()].drop(columns="error")
        if setups is not None:
            x = x[x["setup"].isin(setups)]
        parts.append(x)
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s["date"]).dt.date
    no_locked(s["date"].unique())
    c = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "ctrl").glob("*.parquet"))], ignore_index=True)
    c["date"] = pd.to_datetime(c["date"]).dt.date
    s = s.merge(c, on=["date", "tod"], how="left")
    dt = day_table()
    s = s.join(dt, on="date")
    s["split"] = split_of(s["date"])
    return s


def ctrl_col(side: str, geom: str) -> str:
    return f"c_{side}_{geom}"


def day_delta(var: pd.DataFrame, par: pd.DataFrame) -> dict:
    """Variant vs parent on the same days: delta = (sum var R - sum parent R) / n_parent, day-clustered t."""
    a = par.groupby("date")["r"].agg(["sum", "size"])
    b = var.groupby("date")["r"].sum().reindex(a.index.union(var["date"].unique()), fill_value=0.0)
    a = a.reindex(b.index, fill_value=0)
    D = b - a["sum"]
    n = a["size"].sum()
    if n == 0:
        return {"delta": np.nan, "t": np.nan}
    dl = D.sum() / n
    se = np.sqrt(((D - dl * a["size"]) ** 2).sum()) / n
    return {"delta": round(float(dl), 4), "t": round(float(dl / se), 2) if se > 0 else np.nan}
