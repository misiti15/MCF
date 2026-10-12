"""Parity of the Testing 2 A7 modules (CWT09 bad-news gap-down bounce short) with the scored package A trades, through
the LIVE code path. Educational only - not financial advice.

Package A ran on its own 1-minute engine (research/bdi/cwt/test_a/engine.py), not on the lab frames, so the check runs
the real mcf LabStrategy.generate on each candidate symbol-day: the day's raw 1-minute bars from data/cache_hist/1Min
(the locked block is dropped at load by engine.Sym), the prior close / high / low, daily ATR and adv20 from engine.Sym,
and the prior 60 5-minute bars. Candidates = package A's own universe and earnings filter for A7 E=out (adv20 >= $1M,
open >= $1, gap <= -5%, no earnings report within +-4 business days). Each module's first signal in its window is
compared with the scored trades in test_a/data/trades.parquet (same symbol, date and 5-minute entry bar), and for
the structural versions the stop price with package A's (the 09:30-10:30 high).

    python research/bdi/cwt/live/verify_a.py [--limit N]     # -> verify_a.json (merged into verify.json)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TA = HERE.parent / "test_a"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TA))
sys.path.insert(0, str(HERE))
from engine import Sym, kidx  # noqa: E402
from run import EARN, earn_flags  # noqa: E402
from selection import S  # noqa: E402

from mcf.strategies.base import PRIOR5_BARS, DayContext  # noqa: E402
from mcf.strategies.setups import LabStrategy, _LAB_FRAMES  # noqa: E402

TZ = "America/New_York"


def main(limit=0):
    t0 = time.time()
    sel = [s for s in S if s["pkg"] == "A"]
    strat = {s["name"]: LabStrategy(s["name"], str(HERE / f"{s['name']}.py"), min_adv=s["min_adv"], window=s["window"])
             for s in sel}
    tr = pd.read_parquet(TA / "data" / "trades.parquet")
    ref = {}
    for s in sel:
        x = tr[tr["cid"] == s["cid"]]
        m = 570 + x["m0"].to_numpy()
        tod = (m // 60) * 100 + m % 60
        ref[s["name"]] = dict(zip(zip(x["symbol"], x["date"]), tod))
    er = pd.read_parquet(EARN, columns=["symbol", "date", "session"])
    er = er[(er["date"] >= "2024-08-01") & (er["date"] <= "2026-11-30")]
    er_by = {k: g for k, g in er.groupby("symbol")}
    syms = [x.strip() for x in (ROOT / "research" / "lab_symbols.txt").read_text().split() if x.strip()]
    if limit:
        syms = syms[:limit]
    got = {s["name"]: {} for s in sel}
    stop_bad = {s["name"]: 0 for s in sel}
    k1030 = kidx(1030)
    n_days = 0
    for n, sym in enumerate(syms):
        try:
            s = Sym(sym)
        except Exception as ex:  # noqa: BLE001
            print("skip", sym, ex, flush=True)
            continue
        if s.D < 30:
            continue
        ef = earn_flags(s, er_by.get(sym))
        cand = np.flatnonzero(s.ok & (s.gap <= -5) & ~ef["black"])
        if not len(cand):
            continue
        raw = pd.read_parquet(ROOT / "data" / "cache_hist" / "1Min" / f"{sym}.parquet")
        idx = raw.index.tz_convert(TZ) if raw.index.tz is not None else raw.index.tz_localize("UTC").tz_convert(TZ)
        raw.index = idx
        mins = idx.hour * 60 + idx.minute
        raw = raw[(mins >= 570) & (mins < 960)]
        dstr = raw.index.strftime("%Y-%m-%d").to_numpy()
        for d in cand:
            day = str(s.dates[d])
            if d == 0 or s.seg[d - 1] != s.seg[d]:
                continue
            bars = raw[dstr == day]
            prior = raw[(dstr < day) & (dstr >= s.dates[max(0, d - 3)])]
            if bars.empty or prior.empty:
                continue
            p5 = prior.resample("5min", label="left", closed="left").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna().tail(PRIOR5_BARS)
            ctx = DayContext(symbol=sym, date=pd.Timestamp(day).date(), bars=bars, prev_close=float(s.pc[d]),
                             prev_high=float(s.hi[d - 1]), prev_low=float(s.lo[d - 1]), atr=float(s.atr[d]),
                             avg_dollar_volume=float(s.adv20[d]), prior5=p5)
            n_days += 1
            _LAB_FRAMES.clear()
            fh = float(np.nanmax(s.h5[d, :k1030 + 1]))
            for name, st in strat.items():
                sig = st.generate(ctx)
                if not sig:
                    continue
                e = bars.index[sig[0].bar_index]
                km = e.hour * 60 + e.minute - 570
                end = 570 + (km - 4) // 5 * 5 + 5
                got[name][(sym, day)] = (end // 60) * 100 + end % 60
                if st.structural and abs(sig[0].stop - fh) > 1e-6 * max(1.0, fh):
                    stop_bad[name] += 1
        if n % 100 == 0:
            print(f"{n}/{len(syms)} {sym} days {n_days} {time.time() - t0:.0f}s", flush=True)
    out = {}
    trr = tr.set_index(["cid", "symbol", "date"])["r"]
    for s in sel:
        nm = s["name"]
        g, r = got[nm], ref[nm]
        same = [k for k in r if g.get(k) == r[k]]
        rr = trr.loc[s["cid"]]
        out[nm] = {"source": f"package A {s['cfg']} (cid {s['cid']})", "window": s["window"], "geom": s["geom"],
                   "side": s["side"], "scored_n": len(r), "module_n": len(g), "matched": len(same),
                   "only_scored": len(set(r) - set(g)), "only_module": len(set(g) - set(r)),
                   "other_bar": sum(1 for k in r if k in g and g[k] != r[k]),
                   "stop_mismatch": stop_bad[nm] if s["geom"] == "S" else None,
                   "parity": bool(len(same) == len(r) == len(g)),
                   "match_share": round(len(same) / max(1, len(r)), 4),
                   "exp_scored": round(float(rr.mean()), 4),
                   "exp_matched": round(float(rr.loc[same].mean()), 4) if same else None,
                   "examples_only_scored": [list(k) + [int(r[k])] for k in list(set(r) - set(g))[:5]],
                   "examples_only_module": [list(k) + [int(g[k])] for k in list(set(g) - set(r))[:5]],
                   "per_day": round(len(r) / 426, 3), "path": "live LabStrategy.generate on raw 1-minute bars"}
        print(nm, {k: v for k, v in out[nm].items() if not k.startswith("examples")}, flush=True)
    json.dump(out, open(HERE / "verify_a.json", "w"), indent=1, default=str)
    print("done", n_days, "candidate days", round(time.time() - t0), "s")


if __name__ == "__main__":
    main(int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--limit" else 0)
