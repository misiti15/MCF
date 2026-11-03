"""eu1103/universe step 4: the pre-declared universe rules applied to the LIVE paper trades (run_id 1, 5 accounts,
10-06..11-02; live_trades.parquet from live_buckets.py). Point-in-time: dollar-ATR rank = adv x atr_pct among that
morning's universe snapshot names with adv >= $95M; move history = share of the prior 60 sessions on which the name was a
top-50 |open->close| / ATR(14) mover among ADV >= $50M names (daily.parquet, SIP daily bars). Kept vs dropped, all
setups and the busiest 8. Usage: python live_rules.py <scratch> -> live_rules_out.txt. Educational only - not financial advice."""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
BUSY = ["CWT14-failbrk-orl-p05-long", "CWT14-failbrk-pdl-p05-long", "CWT12-coil-k4-long", "CWT14-failbrk-pdh-p10-short",
        "heat_fade_short-FD", "RW7-gapdn-bounce-early-short-FD", "RW2-exhaustion-noon-adv150-short-FD", "L3-gap-slope-fromopen-FD"]


def mh60():
    d = pd.read_parquet(S / "daily.parquet").sort_values(["symbol", "date"]).reset_index(drop=True)
    pc = d.groupby("symbol").close.shift()
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    d["atr"] = tr.groupby(d.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    d["adv"] = (d.close * d.volume).groupby(d.symbol).transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    d["mv"] = (d.close - d.open).abs() / d.atr
    ok = (d.adv >= 50e6) & d.mv.notna()
    d["rk"] = np.where(ok, d.groupby("date").mv.rank(ascending=False), np.nan)
    d["top50"], d["elig"] = (d.rk <= 50).astype(float), ok.astype(float)
    g = d.groupby("symbol")
    d["mh60"] = g.top50.transform(lambda s: s.shift(1).rolling(60, min_periods=20).sum()) / \
        g.elig.transform(lambda s: s.shift(1).rolling(60, min_periods=20).sum()).replace(0, np.nan)
    return d[["symbol", "date", "mh60"]]


def ranks():
    snaps = {"2026-10-05": pd.read_csv("/home/user/MCF/data/universe.csv")}
    for p in sorted(glob.glob(str(S / "uni" / "*.csv"))):
        snaps[Path(p).stem] = pd.read_csv(p)
    out = {}
    for k, u in snaps.items():
        u = u[u.adv >= 95e6].copy()
        u["rk"] = (u.adv * u.atr_pct).rank(ascending=False)
        out[k] = u.set_index("symbol").rk
    return out


def stat(x):
    if not len(x):
        return 0, np.nan, np.nan, np.nan
    ds = x.groupby("date").R.agg(["sum", "size"])
    mu = x.R.mean()
    se = np.sqrt(((ds["sum"] - ds["size"] * mu) ** 2).sum()) / len(x) if len(ds) > 1 else np.nan
    bd = ds["sum"].idxmax()
    wo = (ds["sum"].sum() - ds.loc[bd, "sum"]) / max(1, len(x) - ds.loc[bd, "size"])
    return len(x), round(mu, 3), round(mu / se, 2) if se > 0 else np.nan, round(wo, 3)


def main():
    t = pd.read_parquet(S / "live_trades.parquet")
    t = t.merge(mh60(), on=["symbol", "date"], how="left")
    rk = ranks()
    keys = sorted(rk)
    t["rk"] = [rk[max(k for k in keys if k <= d)].get(s, np.nan) for s, d in zip(t.symbol, t.date)]
    rules = {"S1 top-300 dollar-ATR": t.rk <= 300, "S1 top-500 dollar-ATR": t.rk <= 500, "S1 top-800 dollar-ATR": t.rk <= 800,
             "S2 move history >= 3% (prior 60d)": t.mh60 >= 0.03, "S3 ATR% >= 3": t.atr_pct >= 3,
             "S4 drop idiosyncratic (sector none)": t.sector != "none", "S5 ADV >= 300M": t.adv >= 300e6,
             "L0 below 95M only (what a lower floor adds)": t.adv < 95e6}
    lines = ["Educational only - not financial advice. LIVE paper trades (run_id 1, 5 accounts, 10-06..11-02, 20 sessions), "
             "after costs. kept / dropped avg R, day-clustered t, avg R w/o best session; kd = per-session kept minus dropped mean."]
    for scope, x0 in (("ALL setups", t), ("busiest 8", t[t.strategy.isin(BUSY)]), ("Primary", t[t.acct == "p"])):
        rows = []
        for name, keep in rules.items():
            keep = keep.fillna(False).loc[x0.index]
            k, dr = x0[keep], x0[~keep]
            nk, rk_, tk, wk = stat(k)
            nd, rd, td, wd = stat(dr)
            dd = pd.concat([k.groupby("date").R.mean().rename("k"), dr.groupby("date").R.mean().rename("d")], axis=1).dropna()
            diff = dd.k - dd.d
            gk = k.groupby("date").R.sum()
            rows.append(dict(rule=name, n_kept=nk, kept_R=rk_, kept_t=tk, kept_wo_best=wk, n_drop=nd, drop_R=rd,
                             kd=round(diff.mean(), 3) if len(diff) else np.nan,
                             kd_t=round(diff.mean() / (diff.std() / np.sqrt(len(diff))), 2) if len(diff) > 2 else np.nan,
                             kept_totR=round(k.R.sum(), 1), green_days_kept=f"{int((gk > 0).sum())}/{len(gk)}"))
        a = stat(x0)
        lines.append(f"\n== {scope}: all trades n {a[0]} avg R {a[1]} t {a[2]} w/o best {a[3]}, "
                     f"green sessions {int((x0.groupby('date').R.sum() > 0).sum())}/{x0.date.nunique()}")
        lines.append(pd.DataFrame(rows).to_string(index=False))
    (HERE / "live_rules_out.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
