"""Verify the W1 candidate modules (modules/*.py) against the coordinate-search scan.

1. Offline: module mask on the scan rows (base.npz + data/ext sma100 as 'sma100_dist_pct'), month by month, first
   qualifying bar per symbol-day -> the trade list must equal the scan's (same rows, same R).
2. Live-shaped: for a sample of 2026 symbol-days (every module trade from 2026-06 on, plus symbol-days where the
   time-only control traded but the module did not), rebuild the frame exactly as mcf.strategies.setups.LabStrategy
   does (1-min cache -> 5-min, PRIOR5_BARS = 60 prior bars + today's bars, heat_frame + extra_features, today's
   volume, gap from today's open / prior close, prior-day high/low distances) plus the proposed live column
   sma100_dist_pct computed on the same history, run mask() WITHOUT symbol/date columns and compare the first
   qualifying bar (09:50-15:00) with the scan. Writes verify.json. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
import eng  # noqa: E402
import families as FM  # noqa: E402
from run import _restore  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import extra_features  # noqa: E402
from mcf.strategies.base import PRIOR5_BARS  # noqa: E402

CANDS = {  # module -> (family, variant)
    "W1-NS3-vwapreclaim-sma100-vol2-short": ("NS3-failed-vwap-reclaim-short", "sma=100;vol=2.0"),
    "W1-ST6-volspikeup-sma100above-short": ("ST6-volspikeup-short-mid-t1s1", "ma=a100"),
    "W1-ST1-ordn-sma100below-long": ("ST1-ordn-long-pm-t05s1", "ma=a100"),
    "W1-ST8-volspikedn-sma100below-long-t05s1": ("ST8-volspikedn-long-pm-t1s1", "geom=t05s1;ma=a100"),
}
COLS = ["close", "rsi", "rsi5", "emaDiff", "macdPct", "volumeRatio", "vwapDistPct", "buyPressure", "gap", "fromOpen",
        "tod", "atr_d", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "sma20_dist_pct",
        "sma50_dist_pct", "sma20_slope_pct", "flow3"]


def load_mod(name):
    sp = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / "modules" / f"{name}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def scan_trades(D, spec, P):
    s = 1 if spec["side"] == "long" else -1
    m = FM.common(D, P, s, spec["fn"](D, P, s))
    return D.trades(m, spec["side"], P["geom"], spec["min_adv"])


def offline(D, mod):
    sd = np.asarray(D.sd)
    mon = D.mon[D.day]
    hits = []
    for mi in np.unique(mon):
        rows = np.flatnonzero(mon == mi)
        a, b = rows[0], rows[-1] + 1
        assert len(rows) == b - a
        df = pd.DataFrame({k: np.asarray(D.B[k][a:b]) for k in COLS})
        df["sma100_dist_pct"] = np.asarray(D.E["sma100"][a:b], np.float32)
        df["symbol"] = sd[a:b]
        df["date"] = 0
        m = np.asarray(mod.mask(df), bool)
        hits.append(a + np.flatnonzero(m))
    idx = np.concatenate(hits)
    idx = idx[eng._first_per_sd(idx, D.sd)]
    r = np.asarray(D.outcome(mod.SIDE, mod.GEOM)[idx], float)
    ok = np.isfinite(r)
    return idx[ok], r[ok]


def live_frame(store, cache, sym, date, atr):
    if sym not in cache:
        df = store.load(sym)
        ds = pd.Series(df.index.date.astype(str), index=df.index)
        df = df[(ds < "2024-11-01") | (ds > "2025-02-28")]
        cache.clear()
        cache[sym] = (resample(df, "5min"), df)
    d5all, d1 = cache[sym]
    dd = pd.Index(d5all.index.date.astype(str))
    today = d5all[dd == date]
    prior = d5all[dd < date]
    pdays = sorted(set(dd[dd < date]))
    if not len(today) or not pdays:
        return None
    pday = prior[pd.Index(prior.index.date.astype(str)) == pdays[-1]]
    hist = pd.concat([prior.tail(PRIOR5_BARS), today])
    f = heat_frame(hist)
    f["atr_d"] = atr
    f = f.join(extra_features(hist, f))
    f["sma100_dist_pct"] = (hist["close"] / hist["close"].rolling(100).mean() - 1) * 100
    f = f.iloc[-len(today):].copy()
    f["volume"] = today["volume"].to_numpy(dtype=float)
    pc, ph, pl = float(pday["close"].iloc[-1]), float(pday["high"].max()), float(pday["low"].min())
    f["gap"] = (float(today["open"].iloc[0]) / pc - 1) * 100
    f["dist_pdh_atr"] = (ph - f["close"]) / atr
    f["dist_pdl_atr"] = (f["close"] - pl) / atr
    return f.reset_index(drop=True)


def main():
    D = eng.D()
    specs = {s["name"]: s for s in FM.all_specs()}
    res = pd.read_csv(HERE / "results.csv")
    res["params"] = pd.read_csv(HERE / "data" / "params.csv")["params"]
    store = BarStore(ROOT / "data" / "cache_hist")
    out = {}
    rng = np.random.default_rng(20261010)
    for name, (fam, var) in CANDS.items():
        mod = load_mod(name)
        sp = specs[fam]
        row = res[(res.family == fam) & (res.variant == var)].iloc[0]
        P = _restore(sp, json.loads(row["params"]))
        si, sr = scan_trades(D, sp, P)
        mi, mr = offline(D, mod)
        o = {"scan_n": int(len(si)), "module_n": int(len(mi)), "same_rows": bool(np.array_equal(si, mi)),
             "same_r": bool(len(si) == len(mi) and np.allclose(sr, mr)), "scan_exp": float(sr.mean()),
             "module_exp": float(mr.mean())}
        # live-shaped sample
        ctl = dict(P, ma=None) if P.get("ma") else dict(P, sma=None)
        ci, _ = scan_trades(D, sp, ctl)
        ci = ci[np.isfinite(np.asarray(D.F("sma100"))[ci])]
        dates = np.array(D.dates)
        mset = set(np.asarray(D.sd)[si].tolist())
        recent = si[dates[D.day[si]] >= "2026-06-01"]
        others = np.array([i for i in ci if dates[D.day[i]] >= "2026-01-01" and int(D.sd[i]) not in mset])
        if len(others) > 60:
            others = rng.choice(others, 60, replace=False)
        sample = [(int(i), True) for i in recent] + [(int(i), False) for i in others]
        sample.sort(key=lambda t: (int(D.B["sym"][t[0]]), int(D.day[t[0]])))
        agree, n_ok, details, cache = 0, 0, [], {}
        for i, is_trade in sample:
            sym = D.symbols[int(D.B["sym"][i])]
            date = dates[D.day[i]]
            f = live_frame(store, cache, sym, date, float(D.B["atr_d"][i]))
            if f is None:
                continue
            m = np.asarray(mod.mask(f), bool) & (f["tod"].to_numpy() >= 950) & (f["tod"].to_numpy() <= 1500)
            hit = int(f["tod"].to_numpy()[np.argmax(m)]) if m.any() else None
            want = int(D.tod[i]) if is_trade else None
            n_ok += 1
            agree += hit == want
            if hit != want:
                details.append({"symbol": sym, "date": date, "scan_tod": want, "live_tod": hit})
        o["live_sample"] = {"symbol_days": n_ok, "trades_in_sample": int(sum(t for _, t in sample)),
                            "agree": agree, "agree_share": round(agree / max(1, n_ok), 4), "mismatches": details[:20]}
        out[name] = o
        print(name, json.dumps(o)[:600], flush=True)
    (HERE / "verify.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
