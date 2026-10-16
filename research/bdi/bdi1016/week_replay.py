"""Descriptive (not evidence, rule 7): what the 12 pre-declared day-class gates (PLAN.md Part B) would have called on
2026-10-12..10-16 at 10:00 / 10:30, and the live paper P/L of the trades (all setups, all three accounts, S6 excluded)
they would have blocked (entries at/after T on the side against the class). Features rebuilt from SIP 1-minute bars
(fetch_week.py) exactly as the history frames define them: bar closing at T, fromOpen vs the 09:30 open, breadth =
share of the lab universe above its session VWAP, SPY OR = 09:30-09:45. Educational only - not financial advice.
Usage: python week_replay.py <wk_dir>"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from regime_gate import classify  # noqa: E402

W = Path(sys.argv[1])
NY = "America/New_York"
def rth(b):
    b.index = pd.to_datetime(b.index, utc=True).tz_convert(NY)
    return b.between_time("09:30", "15:59")
I = {s: rth(pd.read_parquet(W / f"idx_{s}.parquet")) for s in ("SPY", "QQQ", "IWM")}
U = pd.read_parquet(W / "uni_open.parquet")
U.index = pd.to_datetime(U.index, utc=True).tz_convert(NY)
DAYS = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
feat = []
for d in DAYS:
    day = pd.Timestamp(d).date()
    for T in (1000, 1030):
        tt = pd.Timestamp(f"{d} {T // 100:02d}:{T % 100:02d}", tz=NY)
        row = {"date": day, "T": T}
        for s, b in I.items():
            x = b[b.index.date == day]
            pre = x[x.index < tt]
            row[f"{s.lower()}_fo"] = (pre.close.iloc[-1] / x.open.iloc[0] - 1) * 100
            if s == "SPY":
                prev = b[b.index.date < day]
                pc = prev.close.iloc[-1]
                row["spy_gap"] = (x.open.iloc[0] / pc - 1) * 100
                row["spy_c"] = pre.close.iloc[-1]
                o = x[x.index < pd.Timestamp(f"{d} 09:45", tz=NY)]
                row["or_hi"], row["or_lo"] = o.high.max(), o.low.min()
                row["spy_rest"] = (x.close.iloc[-1] / pre.close.iloc[-1] - 1) * 100
        u = U[(U.index.date == day) & (U.index < tt)]
        tp = (u.high + u.low + u.close) / 3
        g = pd.DataFrame({"pv": tp * u.volume, "v": u.volume, "c": u.close, "s": u.symbol})
        a = g.groupby("s").agg(pv=("pv", "sum"), v=("v", "sum"), c=("c", "last"))
        a = a[a.v > 0]
        row["breadth"] = float((a.c > a.pv / a.v).mean()); row["n_uni"] = len(a)
        row["spy_pc"] = ((1 + row["spy_gap"] / 100) * (1 + row["spy_fo"] / 100) - 1) * 100
        feat.append(row)
F = pd.DataFrame(feat)
pd.set_option("display.width", 250)
print(F.round(3).to_string())
tr = []
for d in DAYS:
    t = pd.read_csv(f"/home/user/MCF/research/bdi/nightly{d[5:7]}{d[8:]}/trades.csv")
    t["et"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert(NY)
    t["date"] = pd.to_datetime(t["date"]).dt.date
    tr.append(t[["date", "acct", "strategy", "side", "pnl", "r_multiple", "et"]])
TR = pd.concat(tr, ignore_index=True)
TR["tod"] = TR.et.dt.hour * 100 + TR.et.dt.minute
out = []
for T in (1000, 1030):
    FT = F[F["T"] == T].reset_index(drop=True)
    for K in ("K1", "K2", "K3"):
        for k in (0.25, 0.50):
            c = classify(FT, K, k).to_dict()
            cls = TR.date.map(c)
            blk = (TR.tod >= T) & (TR.side == -cls)
            for a, g in TR[blk].groupby("acct"):
                out.append({"gate": f"{K}-k{k:.2f}-T{T}", "acct": a, "blocked_n": len(g), "blocked_pnl": round(g.pnl.sum(), 2)})
            out.append({"gate": f"{K}-k{k:.2f}-T{T}", "acct": "calls", "calls": " ".join(f"{str(dd)[5:]}:{ {-1: 'DN', 0: 'chop', 1: 'UP'}[v]}" for dd, v in c.items())})
O = pd.DataFrame(out)
print(O.to_string())
O.to_csv(Path(__file__).resolve().parent / "week_replay_out.csv", index=False)
F.to_csv(Path(__file__).resolve().parent / "week_features.csv", index=False, float_format="%.4f")
print(TR.groupby(["date", "acct", "side"]).pnl.sum().round(0).unstack().to_string())
