"""Fit the calibrated replay's parameters on TRAIN sessions only (research/replay_cal/TARGETS.md) -> params.json.

    python research/replay_cal/fit.py --live-dir DIR --until 2026-10-30 --out research/replay_cal/params.json

spreads: per-symbol / time-of-day median live spreads (journals of every account, 10-06..until);
fill_w:  live market-entry fills vs the session pack's minute bar (open + w (close - open) + half-spread).
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.replay import livecal, store  # noqa: E402


def fill_pairs(dbs, days):
    rows = []
    for db in dbs:
        con = sqlite3.connect(str(db))
        q = pd.read_sql("SELECT t.symbol, t.side, t.entry, t.entry_time, s.info, s.entry_type FROM trades t JOIN signals s "
                        "ON s.broker_order_id=t.broker_order_id WHERE t.run_id=1 AND s.run_id=1", con)
        con.close()
        q["day"] = q["entry_time"].astype(str).str[:10]
        rows.append(q[q["day"].isin(days) & (q["entry_type"] == "market")])
    q = pd.concat(rows, ignore_index=True).drop_duplicates()
    out = []
    for d, g in q.groupby("day"):
        bars = store.read_pack(store.pack_path(pd.Timestamp(d).date()), syms=sorted(set(g.symbol)))
        if bars is None or not len(bars):
            continue
        tcol = "ts"
        bars[tcol] = pd.to_datetime(bars[tcol], utc=True).dt.floor("1min")
        bi = bars.set_index(["symbol", tcol])
        for r in g.itertuples():
            t = pd.Timestamp(r.entry_time).tz_convert("UTC").floor("1min")
            try:
                b = bi.loc[(r.symbol, t)]
            except KeyError:
                continue
            info = json.loads(r.info or "{}")
            half = (float(info.get("ask", 0)) - float(info.get("bid", 0))) / 2 if info.get("ask") else 0.0
            sec = pd.Timestamp(r.entry_time).second
            out.append(dict(fill=float(r.entry), open=float(b["open"]), close=float(b["close"]), side=int(r.side),
                            half=half, sec=sec))
    return pd.DataFrame(out)


def spread_rows(dbs, days, tab):
    """Live quotes of TRAIN signals with the replay's regressors (session pack bar before the decision, priors ADV)."""
    import gzip
    import pickle

    out = []
    for d in days:
        rows = []
        for db in dbs:
            con = sqlite3.connect(str(db))
            rows.append(pd.read_sql("SELECT ts, symbol, info FROM signals WHERE run_id=1 AND day=? AND info LIKE "
                                    "'%spread_bps%'", con, params=(d,)))
            con.close()
        g = pd.concat(rows, ignore_index=True)
        pp = store.STORE / "priors" / f"{d}.live.pkl.gz"
        if not len(g) or not pp.exists():
            continue
        with gzip.open(pp, "rb") as f:
            pri = pickle.load(f)
        mkt = store.load_day(pd.Timestamp(d).date(), sorted(set(g.symbol)))
        for r in g.itertuples():
            t = pd.Timestamp(r.ts).tz_convert("America/New_York")
            k = t.hour * 60 + t.minute - 570
            b = mkt.get(r.symbol)
            p = pri.get(r.symbol)
            if b is None or p is None or k < 1 or not p.adv:
                continue
            prev = b[b.index < t.floor("1min")]
            if not len(prev):
                continue
            bar = prev.iloc[-1][["open", "high", "low", "close", "volume"]].to_numpy(float)
            x = livecal.spread_features(float(p.adv), float(bar[3]), bar, k)
            sb = tab["symbol_bucket"].get(r.symbol, {}).get(livecal.bucket(k))
            med = sb if sb is not None else (tab["symbol"][r.symbol] * tab["factor"].get(livecal.bucket(k), 1.0)
                                             if r.symbol in tab["symbol"] else None)
            out.append(dict(lb=float(np.log(max(float(json.loads(r.info)["spread_bps"]), 0.5))), x=x,
                            lmed=None if med is None else float(np.log(max(med, 0.5)))))
    return pd.DataFrame(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live-dir", required=True)
    p.add_argument("--until", default="2026-10-30")
    p.add_argument("--fill-since", default="2026-10-22")
    p.add_argument("--model-table-until", default="2026-10-21")
    p.add_argument("--spread-model", action="store_true")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    dbs = sorted(Path(a.live_dir).glob("*.db"))
    spreads = livecal.fit_spreads(dbs, a.until)
    early = livecal.fit_spreads(dbs, a.model_table_until)
    sr = spread_rows(dbs, [str(d) for d in store.sessions(a.fill_since, a.until)], early)
    model = livecal.fit_spread_model(sr) if a.spread_model else {}
    print(f"spread model: {len(sr)} quotes, {model}")
    days = [str(d) for d in store.sessions(a.fill_since, a.until)]
    fp = fill_pairs([x for x in dbs if x.stem in ("mcf-data", "mcf-data-testing", "mcf-data-testing2")], days)
    w = livecal.fit_fill_weight(fp)
    w_half = livecal.fit_fill_weight(fp.assign(half=0.0))
    print(f"spreads: {spreads['n']} quotes, {len(spreads['symbol'])} symbols, factor {spreads['factor']}")
    print(f"fills: {len(fp)} market entries; w={w:.3f} (with half-spread), w={w_half:.3f} (no half-spread); "
          f"median sec {fp['sec'].median() if len(fp) else None}")
    json.dump({"fit_until": a.until, "spreads": spreads, "spread_model": model, "fill_w": round(w, 3), "fill_n": int(len(fp)),
               "polls": True, "shortable_day": True, "note": "Educational only - not financial advice."},
              open(a.out, "w"))


if __name__ == "__main__":
    main()
