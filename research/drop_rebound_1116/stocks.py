"""Drop-rebound stock variant (owner 2026-11-16): on each SPY drop-rebound signal day, at the trigger minute, long the
5 liquid names that have rebounded most off their own low since 09:30 (liquid = >= $30M traded 09:30..trigger).
Stop 5 bp under each name's own low; exit 15:55 or +90 min; costs as in study.py. Control: 5 random liquid names, same
minute, same rules (20 draws). Reads data/cache_hist/1Min (lab universe, read-only, locked block skipped).
Signal days come from signal_days.csv (cache sessions only; the cache ends 2026-11-04).
Usage: MCF_ROOT=/home/user/MCF python research/drop_rebound_1116/stocks.py   Educational only - not financial advice.
"""
import os, sys, math
from pathlib import Path
from multiprocessing import Pool
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from study import trade, stats, M0, ROOT  # noqa: E402

SIG = pd.read_csv(HERE / "signal_days.csv")
SIG = SIG[SIG.defn == "from_runhigh"]
TRIG = {pd.Timestamp(d).date(): int(e) for d, e in zip(SIG.day, SIG.trig_i)}
SKIP = {"SPY", "QQQ", "SPXL", "TQQQ", "IWM", "DIA", "SSO", "UPRO", "SPUU", "QLD", "SQQQ", "SPXS", "SH", "PSQ"}


def per_symbol(path):
    s = path.stem
    if s in SKIP:
        return []
    try:
        d = pd.read_parquet(path)
    except Exception:
        return []
    d.index = d.index.tz_convert("America/New_York")
    out = []
    for day, e in TRIG.items():
        x = d[(d.index >= pd.Timestamp(str(day), tz="America/New_York") + pd.Timedelta(minutes=M0)) &
              (d.index < pd.Timestamp(str(day), tz="America/New_York") + pd.Timedelta(minutes=960))]
        if len(x) < 300:
            continue
        m = (x.index.hour * 60 + x.index.minute - M0).values
        a = np.full((390, 5), np.nan)
        a[m] = x[["open", "high", "low", "close", "volume"]].values
        v = np.nan_to_num(a[:, 4])
        a = pd.DataFrame(a).ffill().bfill().to_numpy(copy=True)
        a[:, 4] = v
        dv = float((a[:e + 1, 3] * a[:e + 1, 4]).sum())
        if dv < 30e6:
            continue
        lo = a[:e + 1, 2].min()
        reb = a[e, 3] / lo - 1
        stop = lo * (1 - 0.0005)
        res = {xk: trade(a, e, stop, xk) for xk in ("1555", "90")}
        out.append(dict(day=day, sym=s, reb=reb, dv=dv, risk_pct=100 * (a[e, 3] - stop) / a[e, 3],
                        **{f"R_{k}": (v[0] if v else np.nan) for k, v in res.items()}))
    return out


def main():
    files = sorted((ROOT / "data/cache_hist/1Min").glob("*.parquet"))
    with Pool(4) as p:
        rows = [r for rr in p.imap_unordered(per_symbol, files, chunksize=8) for r in rr]
    D = pd.DataFrame(rows)
    split = dict(zip(pd.to_datetime(SIG.day).dt.date, SIG.split))
    rng = np.random.default_rng(11163)
    res = []
    for day, g in D.groupby("day"):
        g = g[g.risk_pct > 0]
        top = g.nlargest(5, "reb")
        ctl = {k: np.mean([g.sample(min(5, len(g)), random_state=int(rng.integers(1e9)))[f"R_{k}"].mean()
                           for _ in range(20)]) for k in ("1555", "90")}
        res.append(dict(day=day, split=split[day], names=len(g), top=",".join(top.sym),
                        top_reb_pct=round(100 * top.reb.mean(), 2), top_risk_pct=round(top.risk_pct.mean(), 2),
                        R_1555=top.R_1555.mean(), R_90=top.R_90.mean(), rand_1555=ctl["1555"], rand_90=ctl["90"],
                        all_1555=g.R_1555.mean(), all_90=g.R_90.mean()))
    R = pd.DataFrame(res)
    R.to_csv(HERE / "trades_stocks.csv", index=False)
    rows = []
    for k in ("1555", "90"):
        row = dict(config=f"top5 rebounders|stop=own low|exit={k}")
        for sp in ("TRAIN", "VALID", "ALL"):
            x = R if sp == "ALL" else R[R.split == sp]
            row.update({f"{a}_{sp}": b for a, b in stats(x[f"R_{k}"]).items()})
            row[f"random_avgR_{sp}"] = round(x[f"rand_{k}"].mean(), 3)
            row[f"all_liquid_avgR_{sp}"] = round(x[f"all_{k}"].mean(), 3)
        rows.append(row)
    G = pd.DataFrame(rows)
    G.to_csv(HERE / "trade_grid_stocks.csv", index=False)
    print(G.T.to_string())


if __name__ == "__main__":
    main()
