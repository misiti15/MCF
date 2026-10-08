"""ADV (mean daily $ volume of the PRIOR 20 sessions, min 5) per symbol-date from data/cache/1Min, read with the
parquet filter timestamp < 2026-09-16 (nothing later is loaded). Writes data/adv.parquet (git-ignored).
Educational only - not financial advice."""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CUT = pd.Timestamp("2026-09-16", tz="America/New_York")


def main():
    out = []
    for f in sorted(Path("data/cache/1Min").glob("*.parquet")):
        d = pd.read_parquet(f, columns=["close", "volume", "timestamp"], filters=[("timestamp", "<", CUT)])
        if d.empty:
            continue
        idx = d.index if "timestamp" not in d else pd.DatetimeIndex(d["timestamp"])
        idx = idx.tz_convert("America/New_York")
        assert idx.max() < CUT
        hm = idx.hour * 100 + idx.minute
        rth = (hm >= 930) & (hm < 1600)
        dv = (d["close"] * d["volume"])[rth].groupby(idx[rth].date).sum()
        adv = dv.shift(1).rolling(20, min_periods=5).mean()
        out.append(pd.DataFrame({"symbol": f.stem, "date": [str(x) for x in adv.index], "adv": adv.to_numpy()}))
    a = pd.concat(out)
    a.to_parquet(HERE / "data" / "adv.parquet")
    print(len(a), a.adv.describe())


if __name__ == "__main__":
    main()
