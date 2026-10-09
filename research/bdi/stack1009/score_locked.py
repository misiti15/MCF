"""ONE-TIME scoring of the stack1009 candidates ST1-ST8 (and RW6G1, live since 2026-10-09) on the rule-19 locked
block 2024-11-01..2025-02-28, by the lead. Production costs (mcf.research.gates), YAML min_adv (adv20) and window applied.
Bar (look 1, rule 19): t >= 1.0 and exp > 0. Educational only - not financial advice.
    MCF_HIST_ALLOW_LOCKED=1 python research/bdi/stack1009/score_locked.py"""
import glob, importlib.util, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
import lib as L
from mcf.research import gates as G

mods = sorted(Path(ROOT / "research/bdi/stack1009/modules").glob("ST*.py")) + [ROOT / "research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py"]
df = pd.concat([L.load_month(m) for m in L.LOCKED_MONTHS], ignore_index=True)
df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
reg = L.regimes(include_locked=True)


def add_volume(df):
    """5-min volume from the 1-minute history cache (RW6G1's VWAP band needs it); full RTH days, as live."""
    vols = []
    for sym in df["symbol"].unique():
        p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
        if not p.exists():
            continue
        m1 = pd.read_parquet(p, columns=["open", "high", "low", "close", "volume"])
        idx = pd.DatetimeIndex(m1.index).tz_convert("America/New_York")
        m1.index = idx
        m1 = m1[(idx >= "2024-11-01") & (idx < "2025-03-01")]
        d5 = m1.resample("5min", label="left", closed="left").agg({"high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
        d5 = d5[(d5.index.hour * 100 + d5.index.minute >= 930) & (d5.index.hour * 100 + d5.index.minute < 1600)]
        end = d5.index + pd.Timedelta(minutes=5)
        vols.append(pd.DataFrame({"symbol": sym, "date": d5.index.date, "tod": end.hour * 100 + end.minute,
                                  "high": d5.high.to_numpy(), "low": d5.low.to_numpy(), "close": d5.close.to_numpy(), "volume": d5.volume.to_numpy()}))
    return pd.concat(vols, ignore_index=True)


out = {}
for p in mods:
    spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    doc = p.read_text()
    adv = float(re.search(r"min_adv (\d+)", doc).group(1)); lo, hi = map(int, re.search(r"window \[(\d+), (\d+)\]", doc).groups())
    if p.stem.startswith("RW6G1"):
        base = df.copy()
        v = add_volume(base[["symbol"]].drop_duplicates())
        # full-day 5-min bars (09:35..16:00 closes) with lab columns where the frame has them
        full = v.merge(base.drop(columns=["high", "low", "close"]), on=["symbol", "date", "tod"], how="left")
        full = full.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        mk = np.asarray(m.mask(full), bool) & (full["adv20"].fillna(0).to_numpy() >= adv)
        mk &= (full["tod"].to_numpy() >= max(950, lo)) & (full["tod"].to_numpy() <= min(1500, hi))
        tr = G.lab_trades(full, mk, m.SIDE, m.GEOM)
    else:
        mk = np.asarray(m.mask(df), bool) & (df["adv20"].fillna(0).to_numpy() >= adv)
        mk &= (df["tod"].to_numpy() >= max(950, lo)) & (df["tod"].to_numpy() <= min(1500, hi))
        tr = G.lab_trades(df, mk, m.SIDE, m.GEOM)
    s = G.summary(tr); rs = G.regime_split(tr, reg)
    s.update(up=rs["up"].get("exp_r"), up_n=rs["up"].get("n"), down=rs["down"].get("exp_r"), down_n=rs["down"].get("n"),
             passed=bool(s.get("n", 0) > 0 and s.get("exp_r", -1) > 0 and (s.get("t") or 0) >= 1.0))
    out[p.stem] = s
    print(p.stem, {k: s.get(k) for k in ("n", "win_rate", "exp_r", "t", "ex_best_day", "up", "down", "passed")}, flush=True)
json.dump(out, open(ROOT / "research/bdi/stack1009/locked.json", "w"), indent=1, default=str)
