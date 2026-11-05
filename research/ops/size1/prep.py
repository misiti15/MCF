"""SIZE1 prep: lab trade lists (+ stop fraction, SPY quiet proxies, ex-market residual) and live journal trades.

Reads the canonical cache in /home/user/MCF by absolute path (open months only; the locked block has no trade files and
lib.load_month refuses it). Writes pickles to the scratch dir given as argv[1]. Educational only - not financial advice.
usage: python prep.py <scratch_dir>   (journal .db files from origin/mcf-data* must already be in <scratch_dir>)
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

MCF = Path("/home/user/MCF")
sys.path.insert(0, str(MCF / "research/history2y"))
import lib  # noqa: E402

S = Path(sys.argv[1])
BT = MCF / "research/history2y/data/bt_lab1104"
GEOM_DN = {"t1s1": 1.0, "t05s1": 1.0, "t1s05": 0.5, "t05s05": 0.5}
LIVE0 = "2026-10-06"


def spy_table():
    """Per (date, minute-of-bar-close HHMM): SPY % from open, 30-min high-low range %, and its prior-20-session median."""
    s = pd.read_parquet(MCF / "data/cache_hist/1Min/SPY.parquet")
    s = s.between_time("09:30", "15:59")
    d = pd.DataFrame({"date": s.index.date.astype(str), "t": (s.index + pd.Timedelta(minutes=1)).strftime("%H%M").astype(int),
                      "o": s.open.values, "h": s.high.values, "l": s.low.values, "c": s.close.values})
    out = []
    for dt, g in d.groupby("date", sort=True):
        g = g.reset_index(drop=True)
        o0 = g.o.iloc[0]
        hi = g.h.rolling(30, min_periods=1).max(); lo = g.l.rolling(30, min_periods=1).min()
        out.append(pd.DataFrame({"date": dt, "t": g.t, "spy_fo": 100 * (g.c / o0 - 1), "rng30": 100 * (hi - lo) / g.c}))
    x = pd.concat(out, ignore_index=True)
    x = x.sort_values(["t", "date"])
    x["rng_med20"] = x.groupby("t").rng30.transform(lambda v: v.shift(1).rolling(20, min_periods=10).median())
    return x.sort_values(["date", "t"]).reset_index(drop=True)


def lab(spy):
    tr = []
    for p in sorted(BT.glob("sig_*.parquet")):
        m = p.stem.split("_", 1)[1]
        assert m not in lib.LOCKED_MONTHS
        t = pd.read_parquet(p)
        t = t[t.date < LIVE0]
        if not len(t):
            continue
        f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d"])
        f["date"] = f["date"].astype(str); f["symbol"] = f["symbol"].astype(str)
        t = t.merge(f, on=["symbol", "date", "tod"], how="left")
        t["sf"] = t.geom.map(GEOM_DN) * 0.25 * t.atr_d / t.close
        tr.append(t.drop(columns=["close", "atr_d"]))
        print(m, len(t), flush=True)
    t = pd.concat(tr, ignore_index=True)
    t = t[np.isfinite(t.sf) & (t.sf > 0)]
    # ex-market residual: trade R minus the mean R of all lab setups' same-side trades that date
    t["r_xm"] = t.r - t.groupby(["date", "side"]).r.transform("mean")
    t = t.merge(spy.rename(columns={"t": "tod"}), on=["date", "tod"], how="left")
    return t


def live(spy):
    fr = []
    for b in ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard"]:
        d = pd.read_sql("select * from trades where run_id=1 and exit is not null", sqlite3.connect(S / f"{b}.db"))
        d["acct"] = b; fr.append(d)
    t = pd.concat(fr, ignore_index=True)
    t["pnl_adj"] = t.pnl_adj.fillna(t.pnl)
    t["r"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares)
    t["sf"] = (t.entry - t.stop).abs() / t.entry
    t = t[np.isfinite(t.r) & (t.sf > 0) & (t.date >= LIVE0)]
    et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    xt = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["ent"] = et.dt.hour * 3600 + et.dt.minute * 60 + et.dt.second + et.dt.microsecond / 1e6
    t["ext"] = xt.dt.hour * 3600 + xt.dt.minute * 60 + xt.dt.second
    t["tod"] = ((et.dt.hour * 60 + et.dt.minute) // 5 * 5).map(lambda v: (v // 60) * 100 + v % 60)  # 5-min decision bucket
    t["tmin"] = (et.dt.hour * 100 + et.dt.minute).astype(int)   # last completed SPY minute = bar closing at this HHMM
    t = t.sort_values("ent").drop_duplicates(["strategy", "symbol", "date", "entry_time"])
    t = t.rename(columns={"strategy": "setup"})
    t = t.merge(spy.rename(columns={"t": "tmin"}), on=["date", "tmin"], how="left")
    return t[["setup", "side", "symbol", "date", "ent", "ext", "tod", "r", "sf", "acct", "spy_fo", "rng30", "rng_med20"]]


if __name__ == "__main__":
    spy = spy_table()
    lv = live(spy); lv.to_pickle(S / "live.pkl"); print("live", len(lv), lv.date.min(), lv.date.max())
    lb = lab(spy); lb.to_pickle(S / "lab.pkl"); print("lab", len(lb), lb.date.min(), lb.date.max())
