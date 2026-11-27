"""PYRAMID L2 shared helpers. Educational only - not financial advice."""
import numpy as np
import pandas as pd


def grp_keys(df):
    k = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
    return k


def gate_g(df):
    """Pre-registered single regime gate G: SPY at or above its open at the decision bar (spy_fo >= 0)."""
    if "spy_fo" not in df.columns:
        return np.zeros(len(df), bool)
    v = df["spy_fo"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        return v >= 0
