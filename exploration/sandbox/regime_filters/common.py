"""Shared loaders for regime_filters. Educational only - not financial advice."""
import numpy as np, pandas as pd
ARENA = ["testing", "testing2", "gen", "livelab", "explore1", "testingd", "testinge", "testingf"]
DISC0 = "2026-10-23"

def load(S):
    t = pd.read_parquet(f"{S}/lots.parquet")
    t = t[t.account != "graveyard"].copy()
    t.loc[t.xdate != t.date, "xmin"] = 960
    a = t[t.account != "primary"].drop_duplicates("k")
    t = pd.concat([t[t.account == "primary"], a], ignore_index=True)
    t["period"] = np.where(t.date >= DISC0, "DISC", "HOLD")
    t["book"] = np.where(t.account == "primary", "primary", "arena")
    # point-in-time L: median lots/day over previous up-to-5 sessions of the account
    n = t.groupby(["account", "date"]).size().rename("n").reset_index().sort_values(["account", "date"])
    n["L"] = n.groupby("account").n.transform(lambda s: s.shift(1).rolling(5, min_periods=1).median())
    t = t.merge(n[["account", "date", "L"]], on=["account", "date"], how="left")
    return t.sort_values(["account", "date", "emin"]).reset_index(drop=True)

def dayt(d):
    d = pd.Series(d).dropna()
    if len(d) < 3 or d.std(ddof=1) == 0:
        return np.nan
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
