"""Live-path parity for the pod1022 observation setups (owner 2026-10-23): real 1-minute bars through
mcf.strategies.setups.LabStrategy.generate (the code the Setup Generator runner calls, with the YAML params of the
config entry), compared with the scored signals of the same live module (score_batch.py --trades-dir).

Per setup: up to K scored symbol-days (must fire on the same 5-minute bar) and K symbol-days of the setup's universe
without a scored trade (must not fire), drawn at random (seed 20261023) from the open history. The locked block
2024-11-01..2025-02-28 is never read (lib refuses it; the 1-minute cache rows inside it are dropped here as well).

Context: the live runner computes spy_fo / qqq_fo / breadth / qqq_vwap from the poll (tests/test_lab_context.py
checks that table against the frame definitions). Here the context table is the history's stored context for the date
(qqq_vwap = the QQQ frame vwapDistPct, as the scorer fills it), indexed by today's 5-minute bar starts, so the check
isolates the module + live frame path. Bars before 09:50 have no stored context (NaN); the live modules ignore them.

    python research/bdi/pod1022/live/parity_live.py TRADES_DIR [K]     # -> research/bdi/pod1022/live/parity.json
Educational only - not financial advice.
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
import lib  # noqa: E402

import mcf.strategies.lab_context as LC  # noqa: E402
from mcf.research.generator import data as GD  # noqa: E402
from mcf.strategies.base import PRIOR5_BARS, DayContext  # noqa: E402
from mcf.strategies.setups import LabStrategy, _LAB_FRAMES  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
_BARS: dict = {}

# name -> (live module, YAML params exactly as in config/account_gen.yaml)
SETUPS = {
    "pod-thrasher-intraday-breadth-thrust-stocks-long-live": dict(
        min_adv=500e6, window=[1015, 1400], context=["breadth", "spy_fo"], geom="holdtr"),
    "pod-breadth-thrust-midday-index-long-live": dict(
        min_adv=0, window=[1000, 1400], context=["breadth", "qqq_vwap", "spy_fo"], symbols="module", geom="holdtr"),
    "pod-wt-bull-flag-breakout-or-bailout-long-live": dict(min_adv=20e6, window=[1000, 1430], geom="S"),
}


def bars_of(sym):
    if sym not in _BARS:
        p = pd.read_parquet(CACHE / f"{sym}.parquet")
        t = p.index.hour * 60 + p.index.minute
        p = p[(t >= 570) & (t < 960)]
        lo, hi = lib.LOCKED
        d = p.index.strftime("%Y-%m-%d")
        _BARS[sym] = p[(d < lo) | (d > hi)]
        if len(_BARS) > 60:
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
                      avg_dollar_volume=float(adv), prior5=p5, peers={"_": today})


_CTX: dict = {}


def month_ctx(month):
    if month not in _CTX:
        c = lib.load_context(month)
        q = lib.load_month(month, ["symbol", "date", "tod", "vwapDistPct"])
        q = q[q["symbol"].astype(str) == "QQQ"][["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "qqq_vwap"})
        c = c.drop(columns=["qqq_vwap"], errors="ignore").merge(q.drop_duplicates(["date", "tod"]), on=["date", "tod"],
                                                                 how="left")
        c["date"] = c["date"].astype(str)
        _CTX[month] = c
    return _CTX[month]


def install_context(day: str, tz):
    c = month_ctx(day[:7])
    c = c[c["date"] == day]
    tod = c["tod"].to_numpy(int)
    mins = (tod // 100) * 60 + tod % 100 - 5            # bar START = close - 5 minutes
    idx = pd.DatetimeIndex([pd.Timestamp(day) + pd.Timedelta(minutes=int(m)) for m in mins]).tz_localize(tz)
    tab = pd.DataFrame({k: c[k].to_numpy(float) for k in LC.CONTEXT_COLS if k in c}, index=idx)
    LC.context_table = lambda peers, cols: tab[[x for x in cols]]


def signal_tod(ctx, sig):
    e = ctx.bars.index[sig.bar_index]
    km = e.hour * 60 + e.minute - 570
    end = 570 + (km - 4) // 5 * 5 + 5
    return (end // 60) * 100 + end % 60


def main(trades_dir: str, k: int = 40):
    rng = np.random.default_rng(20261023)
    out = {}
    for name, yp in SETUPS.items():
        tr = pd.read_parquet(Path(trades_dir) / f"{name}.parquet")
        tr["date"] = tr["date"].astype(str)
        have = set(zip(tr["symbol"].astype(str), tr["date"]))
        pos_i = rng.choice(len(tr), size=min(k, len(tr)), replace=False)
        pos = [(str(tr["symbol"].iloc[i]), tr["date"].iloc[i], int(tr["tod"].iloc[i])) for i in pos_i]
        st = LabStrategy(name, str(HERE / f"{name}.py"), **yp)
        # negatives: universe symbol-days of random open days (half of them on days with a scored trade), no blackout
        tdays = sorted(set(tr["date"]))
        alld = [d for m in lib.months() for d in [m]]
        neg_days = list(rng.choice(tdays, size=min(k // 2, len(tdays)), replace=False))
        neg_months = list(rng.choice(alld, size=4, replace=False))
        need = sorted({d[:7] for _, d, _ in pos} | {d[:7] for d in neg_days} | set(neg_months))
        lvl, negs = {}, []
        for m in need:
            f = lib.load_month(m, ["symbol", "date", "tod", "atr_d", "adv20"])
            f = f[(f["tod"] == 950) & (f["atr_d"] > 0) & (f["adv20"] >= max(yp.get("min_adv", 0), 20e6 if
                                                                               yp.get("symbols") is None else 0))]
            if yp.get("symbols") == "module":
                f = f[f["symbol"].astype(str).isin(st.symbols)]
            f = f.assign(symbol=f["symbol"].astype(str), date=f["date"].astype(str))
            bl = GD._blackout(f["symbol"].to_numpy(dtype=object), pd.to_datetime(f["date"]).dt.date.to_numpy())
            for r, b in zip(f.itertuples(index=False), bl):
                lvl[(r.symbol, r.date)] = (r.atr_d, r.adv20, bool(b))
            cand = f[(f["date"].isin(neg_days)) | (f["date"].str[:7].isin(neg_months))]
            negs += [(a, b) for a, b in zip(cand["symbol"], cand["date"]) if (a, b) not in have]
        negs = [negs[i] for i in rng.choice(len(negs), size=min(k, len(negs)), replace=False)] if negs else []
        res = {"pos_ok": 0, "pos_n": 0, "neg_ok": 0, "neg_n": 0, "skipped": 0, "mismatch": []}
        for sym, day, tod in pos + [(a, b, None) for a, b in negs]:
            if (sym, day) not in lvl or (tod is None and lvl[(sym, day)][2]):
                res["skipped"] += 1
                continue
            atr, adv, _ = lvl[(sym, day)]
            ctx = ctx_for(sym, pd.Timestamp(day).date(), atr, adv)
            if ctx is None:
                res["skipped"] += 1
                continue
            install_context(day, ctx.bars.index.tz)
            _LAB_FRAMES.clear()
            got = None
            # LabStrategy.eligible's universe part (adv, symbols); its bar-count gate (n % 5, n == 390) is for the live
            # poll and the gap-filled backtest day, and the raw 1-minute cache has missing minutes on some days
            if ctx.avg_dollar_volume >= st.min_adv and (st.symbols is None or sym in st.symbols):
                sig = st.generate(ctx)        # full day (390 bars): first hit in the window, as the backtester runs it
                got = signal_tod(ctx, sig[0]) if sig else None
            key = "pos" if tod is not None else "neg"
            res[f"{key}_n"] += 1
            if got == tod:
                res[f"{key}_ok"] += 1
            else:
                res["mismatch"].append([sym, day, tod, got])
        n = res["pos_n"] + res["neg_n"]
        res["match"] = round((res["pos_ok"] + res["neg_ok"]) / n, 4) if n else None
        res["pos_match"] = round(res["pos_ok"] / res["pos_n"], 4) if res["pos_n"] else None
        out[name] = res
        print(name, {a: b for a, b in res.items() if a != "mismatch"}, res["mismatch"][:6], flush=True)
    out["_note"] = "Educational only - not financial advice."
    (HERE / "parity.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], int(a[1]) if len(a) > 1 else 40)
