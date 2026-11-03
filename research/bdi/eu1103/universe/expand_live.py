"""eu1103/universe step 3: the LIVE period 2026-10-06..11-02 re-scored on a LARGER universe. Read-only Alpaca GET of
SIP 5-minute RTH bars 2026-09-08..11-02 for every name with ADV >= $20M in the 10-05 universe (data/universe.csv,
core tier, price >= $5, ATR >= 1%, PTP denylist out), in batches; lab frames built per symbol with the live pipeline
(mcf.research.setup_lab: heat_frame + extra_features + lab outcomes, rows from 09:35 so the CWT modules see the
09:35-09:45 bars as live does; adv20 from the bars); live earnings blackout applied (origin/mcf-data earnings/<day>.json,
10-06/10-07 use 10-08's file). Each setup's module mask, first bar per symbol-day in its window, production costs
(gates.lab_trades). Bars are never stored: only trades + the per symbol-day random control are kept.
    python expand_live.py <scratch>  -> <scratch>/exp/trades.parquet, ctrl.parquet
Educational only - not financial advice."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

SC = Path(sys.argv[1])
sys.argv = [sys.argv[0], str(SC)]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score2y as Z  # noqa: E402  (SETUPS, MODS; loads no frames at import)
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.priors import _bars, _client  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import GEOMS, _outcomes_asym, extra_features  # noqa: E402
from mcf.research import gates as G  # noqa: E402
sys.path.insert(0, "/home/user/MCF/research/history2y")
from build_frames import daily_table  # noqa: E402

OUT = SC / "exp"
OUT.mkdir(exist_ok=True)
FIRST, LAST = "2026-10-06", "2026-11-02"


def blackout():
    bo = {}
    files = subprocess.run(["git", "-C", "/home/user/MCF", "ls-tree", "--name-only", "origin/mcf-data", "earnings/"],
                           capture_output=True, text=True).stdout.split()
    for f in files:
        d = Path(f).stem
        j = json.loads(subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/mcf-data:{f}"], capture_output=True, text=True).stdout)
        bo[d] = set(j["symbols"])
    for d in ("2026-10-06", "2026-10-07"):
        bo[d] = bo["2026-10-08"]
    return bo


def frame(sym, d5):
    d5 = d5[["open", "high", "low", "close", "volume"]].astype("float64")
    if len(d5) < 300:
        return None
    f = heat_frame(d5)
    f = f.join(extra_features(d5, f))
    for g, (up, dn) in GEOMS.items():
        for k, arr in _outcomes_asym(f, 0.25, 0.01, up, dn).items():
            f[f"{k}_{g}"] = arr
    f["symbol"] = sym
    f["date"] = f.index.date
    dd = daily_table(d5, sym)
    f = f.merge(dd[["date", "adv20"]], on="date", how="left")
    f = f[(f.date.astype(str) >= FIRST) & (f.tod >= 935) & (f.tod <= 1500) & f.atr_d.notna()]
    return f


def score(F):
    F = F.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    head = F["tod"].to_numpy() < 950
    f = F[~head & F["rsi"].notna().to_numpy()].reset_index(drop=True)      # the 2-year frame rows
    F["ri"] = -1
    F.loc[~head & F["rsi"].notna().to_numpy(), "ri"] = np.arange(len(f))
    ri = F["ri"].to_numpy()
    tod = f["tod"].to_numpy(float)
    out = []
    for name, (path, kind, win, _) in Z.SETUPS.items():
        mod = Z.MODS[name]
        with np.errstate(invalid="ignore", divide="ignore"):
            if kind == "cwt":
                mx = np.asarray(mod.mask(F), bool)
                m = np.zeros(len(f), bool)
                m[ri[mx & (ri >= 0)]] = True
                side, geom = mod.SIDE, mod.GEOM
            elif kind == "heat":
                m = np.nan_to_num(np.asarray(mod.score(f), float), nan=np.inf) <= mod.SHORT_AT
                side, geom = "short", "t1s1"
            else:
                m = np.asarray(mod.mask(f), bool)
                side, geom = mod.SIDE, mod.GEOM
        if name.startswith("L3-"):
            m &= f["gap"].to_numpy(float) <= -2.6573517322540283
        m &= (tod >= win[0]) & (tod <= win[1])
        t = G.lab_trades(f, m, side, geom)
        idx = G.first_per_symbol_day(f["symbol"].to_numpy(), f["date"].to_numpy(), m & np.isfinite(f[f"r_{side}_{geom}"].to_numpy(float)))
        t["adv20"] = f["adv20"].to_numpy(float)[idx]
        t["atr_d"] = f["atr_d"].to_numpy(float)[idx]
        t["px"] = f["close"].to_numpy(float)[idx]
        t["setup"], t["side"], t["geom"] = name, side, geom
        out.append(t)
    ctrl = []
    for side in ("long", "short"):
        for geom in ("t1s1", "t05s1"):
            rr = f[f"r_{side}_{geom}"].to_numpy(float)
            ok = np.isfinite(rr)
            r = G.prod_r(rr[ok], f[f"win_{side}_{geom}"].to_numpy(float)[ok], f["close"].to_numpy(float)[ok],
                         f["atr_d"].to_numpy(float)[ok], geom, tod=tod[ok])
            c = pd.DataFrame({"symbol": f["symbol"].to_numpy()[ok], "date": f["date"].to_numpy()[ok], "r": r})
            ctrl.append(c.groupby(["date", "symbol"]).r.mean().rename("rc").reset_index().assign(side=side, geom=geom))
    return pd.concat(out, ignore_index=True), pd.concat(ctrl, ignore_index=True)


def main():
    import yaml
    cfg = yaml.safe_load(open("/home/user/MCF/config/default.yaml"))
    deny = set(cfg["universe"]["ptp_denylist"])
    u = pd.read_csv("/home/user/MCF/data/universe.csv")
    u = u[(u.adv >= 20e6) & (u.tier == "core") & (u.price >= 5) & (u.atr_pct >= 1.0) & ~u.symbol.isin(deny)]
    syms = sorted(u.symbol.astype(str))
    bo = blackout()
    dc = _client()
    t0 = time.time()
    B = 150
    for i in range(0, len(syms), B):
        p = OUT / f"b{i:05d}.parquet"
        if p.exists():
            continue
        raw = _bars(dc, syms[i:i + B], datetime(2026, 9, 8, 13), datetime(2026, 11, 2, 21), 5, "sip", batch=50, workers=4)
        tr_all, c_all = [], []
        fr = []
        for s, g in raw.groupby(level=0):
            g = rth(normalize(g.droplevel(0)))
            x = frame(s, g)
            if x is not None and len(x):
                fr.append(x)
        if fr:
            tr, c = score(pd.concat(fr, ignore_index=True))
            keep = np.array([s not in bo.get(str(d), set()) for s, d in zip(tr.symbol, tr.date)], bool)
            tr = tr[keep]
            kc = np.array([s not in bo.get(str(d), set()) for s, d in zip(c.symbol, c.date)], bool)
            c = c[kc]
            c.to_parquet(OUT / f"c{i:05d}.parquet", index=False)
            tr.to_parquet(p, index=False)
        print(i, len(syms), len(fr), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
