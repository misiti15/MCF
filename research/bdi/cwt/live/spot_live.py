"""Live-path spot check for the Testing 2 modules: real 1-minute bars through mcf LabStrategy.generate (the code the
trade workflow runs), compared with the scored entries. Educational only - not financial advice.

verify.py proves the modules reproduce the scored trades on the lab frames; this checks that the LIVE frame
(heat_frame on today's bars + PRIOR5_BARS prior 5-minute bars, ctx levels) gives the same entry bar. Per setup: up
to K scored trades (must fire at the same bar) and K symbol-days with no scored trade (must not fire), drawn at
random (seed 20261012) from the open history (locked block never touched).

    python research/bdi/cwt/live/spot_live.py [K] [NAME ...]    # -> spot_live.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
from selection import S  # noqa: E402

from mcf.strategies.base import PRIOR5_BARS, DayContext  # noqa: E402
from mcf.strategies.setups import LabStrategy, _LAB_FRAMES  # noqa: E402

TB = HERE.parent / "test_b" / "data"
CACHE = ROOT / "data" / "cache_hist" / "1Min"
_BARS: dict = {}


def bars_of(sym):
    if sym not in _BARS:
        p = pd.read_parquet(CACHE / f"{sym}.parquet")
        t = p.index.hour * 60 + p.index.minute
        p = p[(t >= 570) & (t < 960)]
        lo, hi = lib.LOCKED
        d = p.index.strftime("%Y-%m-%d")
        _BARS[sym] = p[(d < lo) | (d > hi)]
        if len(_BARS) > 40:
            _BARS.pop(next(iter(_BARS)))
    return _BARS[sym]


def ctx_for(sym, day, atr, adv):
    b = bars_of(sym)
    ds = b.index.date
    today = b[ds == day]
    prior = b[ds < day]
    if today.empty or prior.empty:
        return None
    pday = prior.index.date[-1]
    pd_ = prior[prior.index.date == pday]
    p5 = prior.tail(PRIOR5_BARS * 5 + 300).resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna().tail(PRIOR5_BARS)
    return DayContext(symbol=sym, date=day, bars=today, prev_close=float(pd_["close"].iloc[-1]),
                      prev_high=float(pd_["high"].max()), prev_low=float(pd_["low"].min()), atr=float(atr),
                      avg_dollar_volume=float(adv), prior5=p5)


def main(k=15, names=None):
    rng = np.random.default_rng(20261012)
    z = np.load(TB / "trades.npz", allow_pickle=True)
    dates = json.load(open(TB / "baseline.json"))["dates"]
    sel = [s for s in S if s["pkg"] == "B" and (not names or s["name"] in names)]
    # atr_d / adv20 per symbol-day from the frames (the 09:50 row), for ctx.atr and the universe
    need = {}
    picks = {}
    for s in sel:
        cid = s["cid"]
        days = np.array([dates[d] for d in z[f"{cid}|day"]])
        syms = z[f"{cid}|sym"].astype(str)
        tods = z[f"{cid}|tod"].astype(int)
        ii = rng.choice(len(days), size=min(k, len(days)), replace=False)
        pos = [(str(syms[i]), str(days[i]), int(tods[i])) for i in ii]
        picks[s["name"]] = {"pos": pos, "have": set(zip(syms.tolist(), days.tolist()))}
        for p in pos:
            need.setdefault(p[1][:7], set()).add((p[0], p[1]))
    frames = {}
    neg_pool = []
    for month in sorted(need) + list(rng.choice(lib.months(), size=3, replace=False)):
        f = lib.load_month(month, ["symbol", "date", "tod", "atr_d", "adv20"])
        f = f[(f["tod"] == 950) & (f["adv20"] >= 95e6) & (f["atr_d"] > 0)]
        for r in f.itertuples(index=False):
            frames[(str(r.symbol), str(r.date))] = (r.atr_d, r.adv20)
        neg_pool += [(str(a), str(b)) for a, b in zip(f["symbol"], f["date"])]
    out = {}
    for s in sel:
        st = LabStrategy(s["name"], str(HERE / f"{s['name']}.py"), min_adv=95e6, window=s["window"])
        res = {"pos_ok": 0, "pos_n": 0, "neg_ok": 0, "neg_n": 0, "mismatch": []}
        negs = [p for p in (neg_pool[i] for i in rng.choice(len(neg_pool), size=k * 4, replace=False))
                if p not in picks[s["name"]]["have"]][:k]
        for sym, day, tod in picks[s["name"]]["pos"] + [(a, b, None) for a, b in negs]:
            if (sym, day) not in frames:
                continue
            atr, adv = frames[(sym, day)]
            ctx = ctx_for(sym, pd.Timestamp(str(day)).date(), atr, adv)
            if ctx is None:
                continue
            _LAB_FRAMES.clear()
            sig = st.generate(ctx)        # full day (390 bars): first hit in the window, as the backtester runs it
            got = None
            if sig:
                # the signal sits on the last minute of its 5-minute bar (the next minute present when the 1-minute
                # data has a gap there), so map it back to that 5-minute bar's end time
                e = ctx.bars.index[sig[0].bar_index]
                km = e.hour * 60 + e.minute - 570
                end = 570 + (km - 4) // 5 * 5 + 5
                got = (end // 60) * 100 + end % 60
            key = "pos" if tod is not None else "neg"
            res[f"{key}_n"] += 1
            if got == tod:
                res[f"{key}_ok"] += 1
            else:
                res["mismatch"].append([sym, day, tod, got])
        out[s["name"]] = res
        print(s["name"], {k2: v for k2, v in res.items() if k2 != "mismatch"}, res["mismatch"][:4], flush=True)
    json.dump(out, open(HERE / "spot_live.json", "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 15, a[1:])
