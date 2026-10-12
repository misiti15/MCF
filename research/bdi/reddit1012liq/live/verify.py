"""Trade-for-trade parity of the Testing 1 liquidity modules with their scored configurations, plus the finalist
robustness line (next-bar-open entry). Educational only - not financial advice.

For each module: build the live-like frame per month from the study's 5-minute bars (close, high, low, tod, atr_d,
fromOpen, vwapDistPct, dist_pdh_atr, dist_pdl_atr - the columns the live LabStrategy frame carries; the locked block
is never loaded), run mask(df), keep the first True row per symbol-day in the YAML window as LabStrategy.generate does,
and compare (date, symbol, entry bar) and the stop / target with the scored trades (score.run_exits).

    python research/bdi/reddit1012liq/live/verify.py      # -> verify.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(STUDY))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
import score as S  # noqa: E402
from mcf.research import gates  # noqa: E402

MODS = {
    "LIQ-orl-sweep-open15-s25-long": (("OR", "long", 0.15, "open", 15), (1, "S", "2.5R", "none")),
    "LIQ-pdl-sweep-open15-vwap-long": (("PD", "long", 0.05, "open", 15), (1, "A", "NL", "BE+TS")),
}
WINDOW = (950, 1500)


def load_mod(name):
    spec = importlib.util.spec_from_file_location(f"v_{name.replace('-', '_')}", HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def live_frame(M) -> pd.DataFrame:
    b = M.b
    atr = b["atr_d"].to_numpy(float)
    c = b["c"].to_numpy(float)
    return pd.DataFrame({"symbol": b["symbol"].to_numpy(), "date": b["date"].to_numpy(), "tod": b["tod"].to_numpy(np.int64),
                         "close": c, "high": b["h"].to_numpy(float), "low": b["l"].to_numpy(float), "atr_d": atr,
                         "fromOpen": (c / M.dopen - 1) * 100, "vwapDistPct": (c / b["vwap"].to_numpy(float) - 1) * 100,
                         "dist_pdh_atr": (b["pdh"].to_numpy(float) - c) / atr, "dist_pdl_atr": (c - b["pdl"].to_numpy(float)) / atr})


def main():
    t0 = time.time()
    dates = list(lib.regimes().index)
    dayidx = {d: i for i, d in enumerate(dates)}
    reg = lib.regimes()["regime"]
    mods = {n: load_mod(n) for n in MODS}
    acc = {n: {"ref": [], "mine": [], "stopdiff": [], "tgtdiff": [], "r": [], "rs": [], "date": [], "r_next": [], "date_next": []}
           for n in MODS}
    for month in lib.months():
        M = S.Month(month, dayidx)
        f = live_frame(M)
        for name, (sg, ex) in MODS.items():
            a = acc[name]
            rows, E, _ = M.candidates(*sg)
            T = S.run_exits(M, rows, E, sg[1], ex)
            tr = T["row"].astype(np.int64)
            a["ref"] += list(zip(M.b["date"].to_numpy()[tr].astype(str), M.b["symbol"].to_numpy()[tr], M.tod[tr]))
            a["r"].append(T["r"]); a["rs"].append(T["rs"]); a["date"].append(np.array(dates)[M.day[tr]])
            mod = mods[name]
            m = np.asarray(mod.mask(f), bool) & (M.tod >= WINDOW[0]) & (M.tod <= WINDOW[1])
            hit = np.flatnonzero(m)
            if len(hit):
                hit = hit[np.r_[True, M.seg[hit][1:] != M.seg[hit][:-1]]]
            a["mine"] += list(zip(M.b["date"].to_numpy()[hit].astype(str), M.b["symbol"].to_numpy()[hit], M.tod[hit]))
            # stop / target on a sample of matched rows, through the module functions on single symbol-day frames
            common = np.intersect1d(hit, tr)
            for i in common[:: max(1, len(common) // 40)]:
                seg = M.seg[i]
                lo = np.searchsorted(M.seg, seg, "left"); hi = np.searchsorted(M.seg, seg, "right")
                day = f.iloc[lo:hi].drop(columns=["symbol", "date"]).reset_index(drop=True)
                j = i - lo
                st = mod.stop_price(day, j)
                tg = mod.target_price(day, j, st)
                e, st0, tg0, risk, valid = S.trade_params(M, np.array([i]), E[rows == i][:1], sg[1], ex[1], ex[2])
                a["stopdiff"].append(abs(st - st0[0])); a["tgtdiff"].append(abs(tg - tg0[0]))
            # robustness: entry at the next bar's open (same stop / target levels), stop-first from that bar
            if len(tr):
                s = 1
                ok = (tr + 1 < len(M.c)) & ~M.new[np.minimum(tr + 1, len(M.c) - 1)]
                ii = tr[ok]
                Ei = np.array([E[np.flatnonzero(rows == q)[0]] for q in ii])
                e, st0, tg0, risk, valid = S.trade_params(M, ii, Ei, sg[1], ex[1], ex[2])
                e1 = M.o[ii + 1]
                good = s * (e1 - st0) > 0
                ii, e1, st0, tg0 = ii[good], e1[good], st0[good], tg0[good]
                risk1 = s * (e1 - st0)
                tg0 = np.where(np.isnan(tg0) | (s * (tg0 - e1) > 0), tg0, np.nan)
                be, ts = ex[3] in ("BE", "BE+TS"), ex[3] in ("TS", "BE+TS")
                xp, kind, xr = S.sim(ii, s, e1, st0, tg0, risk1, be, ts, M.o, M.h, M.l, M.c, M.tod, M.new, True)
                # entry bar's own range can hit the stop/target: sim starts at ii+1 = the entry bar (conservative)
                r, _ = S.costs(M, ii, xp, kind, s, e1)
                a["r_next"].append(r); a["date_next"].append(np.array(dates)[M.day[ii]])
        print(month, round(time.time() - t0), flush=True)
        del M, f
    out = {}
    for name, a in acc.items():
        ref, mine = set(a["ref"]), set(a["mine"])
        r = np.concatenate(a["r"]); d = np.concatenate(a["date"])
        tr = pd.DataFrame({"date": d, "r": r})
        trs = pd.DataFrame({"date": d, "r": np.concatenate(a["rs"])})
        trn = pd.DataFrame({"date": np.concatenate(a["date_next"]), "r": np.concatenate(a["r_next"])})
        sp = lambda T, lo, hi: gates.summary(T[(T["date"].astype(str) >= lo) & (T["date"].astype(str) <= hi)])
        out[name] = {"config": S.cname(*MODS[name]), "scored_n": len(ref), "module_n": len(mine),
                     "matched": len(ref & mine), "only_scored": len(ref - mine), "only_module": len(mine - ref),
                     "parity": ref == mine, "max_stop_diff": float(max(a["stopdiff"] or [0])),
                     "max_target_diff": float(max(a["tgtdiff"] or [0])), "checked_levels": len(a["stopdiff"]),
                     "open": gates.summary(tr), "train": sp(tr, "2000", "2025-12-31"), "valid": sp(tr, "2026-01-01", "2100"),
                     "open_structural_R": gates.summary(trs),
                     "regimes": {k: v for k, v in gates.regime_split(tr, lib.regimes()).items()},
                     "walk_forward_share": gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)["share_positive"],
                     "next_bar_open_entry": gates.summary(trn), "per_day": round(len(ref) / len(dates), 3)}
        print(name, json.dumps(out[name], default=str), flush=True)
    out["_meta"] = {"what": "trade-for-trade parity of the Testing 1 liquidity modules with the scored configurations "
                            "(open two-year history; the locked block is never loaded). Educational only - not "
                            "financial advice.", "sessions": len(dates), "updated": time.strftime("%Y-%m-%d %H:%M")}
    json.dump(out, open(HERE / "verify.json", "w"), indent=1, sort_keys=True, default=str)


if __name__ == "__main__":
    main()
