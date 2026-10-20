"""5-minute index/ETF bars (from 1-minute, locked block filtered at read) + per-session table. Educational only.
Outputs (scratch): idx5.parquet (sym, date, tod, o, h, l, c, v, vwap, fo, runmin), idx1/<sym>.parquet."""
import numpy as np
import pandas as pd

from common import SCR, load_1min

SYMS = ["SPY", "QQQ", "IWM", "SPXL", "TQQQ"]


def five(df: pd.DataFrame, sym: str) -> pd.DataFrame:
    df = df.copy()
    df["date"] = df.index.date
    m = df.index.hour * 60 + df.index.minute - 570
    df["m"] = m
    df["b"] = m // 5
    tp = (df["high"] + df["low"] + df["close"]) / 3
    df["pv"] = tp * df["volume"]
    g = df.groupby(["date", "b"], sort=True)
    out = g.agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), v=("volume", "sum"),
                pv=("pv", "sum")).reset_index()
    out["cv"] = out.groupby("date")["v"].cumsum()
    out["cpv"] = out.groupby("date")["pv"].cumsum()
    out["vwap"] = out["cpv"] / out["cv"]
    op = out.groupby("date")["o"].transform("first")
    out["open"] = op
    out["fo"] = (out["c"] / op - 1) * 100
    out["runmin"] = out.groupby("date")["fo"].cummin()
    out["lowfo"] = (out.groupby("date")["l"].cummin() / op - 1) * 100       # intrabar running low
    end = (out["b"] + 1) * 5 + 570
    out["tod"] = ((end // 60) * 100 + end % 60).astype(int)
    out["sym"] = sym
    return out.drop(columns=["pv", "cpv"])


def main():
    parts = []
    (SCR / "idx1").mkdir(exist_ok=True)
    for s in SYMS:
        d = load_1min(s)
        d.to_parquet(SCR / "idx1" / f"{s}.parquet")
        parts.append(five(d, s))
        print(s, len(d))
    x = pd.concat(parts, ignore_index=True)
    x.to_parquet(SCR / "idx5.parquet", index=False)
    print(x.shape, x.date.min(), x.date.max())


if __name__ == "__main__":
    main()
