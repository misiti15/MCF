"""Escalation study (key: escalation): the "obvious shorts" of 2026-10-06 and related ideas, as lab-frame masks.

Educational only - not financial advice.
Grids are pre-declared below (and listed in NOTES.md). Every configuration is counted: cartesian product of the
slot options x windows x geometries. Train (to 2026-08-25) is searched, valid (2026-08-26..09-15) chooses.
Nothing dated >= 2026-09-16 is read.
    python research/primitives/escalation/search.py [family ...]
"""
from __future__ import annotations

import gc
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lab import GEOMS, Split, Sub, cond  # noqa: E402

N = None  # "off" option


def S_(name, *opts):
    return {"name": name, "opts": list(opts)}


# ---------------------------------------------------------------------------------------------- families
# Each slot lists options loosest -> tightest; None = layer off. Plateau neighbours = one step in one slot.
FAMILIES = {
    # D/E: gap-up names that faded below the open and VWAP -> SHORT (gap fade continuation)
    "gapfade": dict(side="short", universe=[("gap", ">", 0), ("fromOpen", "<", 0), ("vwapDistPct", "<", 0)],
                    windows=[(950, 1030), (1000, 1100), (1030, 1130), (1100, 1200), (1130, 1300)],
                    slots=[S_("gap", ("gap", ">", 0), ("gap", ">", 1), ("gap", ">", 2)),
                           S_("fo", ("fromOpen", "<", 0), ("fromOpen", "<", -0.5), ("fromOpen", "<", -1), ("fromOpen", "<", -2)),
                           S_("vwap", ("vwapDistPct", "<", 0), ("vwapDistPct", "<", -0.25), ("vwapDistPct", "<", -0.5)),
                           S_("mom", N, ("momentum", "<", 0), ("momentum", "<", -0.5)),
                           S_("rsi", N, ("rsi", "<", 40), ("rsi", "<", 35), ("rsi", "<", 30), ("rsi", "<", 25)),
                           S_("vol", N, ("volumeRatio", ">", 1), ("volumeRatio", ">", 1.5)),
                           S_("flow", N, ("flow3", "<", 0), ("flow3", "<", -0.5))]),
    # F: find the bottom (long) on the same names - only after a reclaim / divergence / wick / higher low
    "bottom": dict(side="long", universe=[("gap", ">", 0), ("fromOpen", "<", 0)],
                   windows=[(1030, 1200), (1105, 1330), (1200, 1430)],
                   slots=[S_("gap", ("gap", ">", 0), ("gap", ">", 1)),
                          S_("fo", ("fromOpen", "<", 0), ("fromOpen", "<", -1), ("fromOpen", "<", -2)),
                          S_("reclaim", N, ("vwapReclaim", "==", 1)),
                          S_("bulldiv", N, ("bull_div", "==", 1)),
                          S_("lwick", N, ("lower_wick", ">", 0.4), ("lower_wick", ">", 0.6)),
                          S_("hl", N, ("dist_lod_atr", ">", 0.1), ("dist_lod_atr", ">", 0.2), ("dist_lod_atr", ">", 0.35)),
                          S_("rsislope", N, ("rsiSlope", ">", 0), ("rsiSlope", ">", 5)),
                          S_("flip", N, ("flowflip", ">", 0), ("flowflip", ">", 0.5))]),
    # A: ORB-style breakout long with an extension cap
    "orbext": dict(side="long", universe=[("fromOpen", ">", 0), ("dist_hod_atr", "<=", 0.05), ("vwapDistPct", ">", 0)],
                   windows=[(950, 1030), (950, 1130), (1000, 1130)],
                   slots=[S_("hod", ("dist_hod_atr", "<=", 0.05), ("dist_hod_atr", "<=", 0.02)),
                          S_("volr", ("volumeRatio", ">", 1), ("volumeRatio", ">", 1.5), ("volumeRatio", ">", 2)),
                          S_("vwapcap", N, ("vwap_atr", "<", 1.0), ("vwap_atr", "<", 0.75), ("vwap_atr", "<", 0.5), ("vwap_atr", "<", 0.3)),
                          S_("focap", N, ("fo_atr", "<", 1.5), ("fo_atr", "<", 1.0), ("fo_atr", "<", 0.75)),
                          S_("rsi5cap", N, ("rsi5", "<", 95), ("rsi5", "<", 90), ("rsi5", "<", 85)),
                          S_("smacap", N, ("sma20_dist_pct", "<", 2), ("sma20_dist_pct", "<", 1.5), ("sma20_dist_pct", "<", 1))]),
    # B: failed breakout short - HOD well above the open, price now back near/below the open
    "failbo": dict(side="short", universe=[("hod_fo_atr", ">=", 0.3), ("dist_hod_atr", ">=", 0.2), ("fo_atr", "<", 0.5)],
                   windows=[(1000, 1100), (1000, 1200), (1030, 1300)],
                   slots=[S_("hodup", ("hod_fo_atr", ">=", 0.3), ("hod_fo_atr", ">=", 0.5), ("hod_fo_atr", ">=", 0.75), ("hod_fo_atr", ">=", 1.0)),
                          S_("back", ("dist_hod_atr", ">=", 0.2), ("dist_hod_atr", ">=", 0.3), ("dist_hod_atr", ">=", 0.45), ("dist_hod_atr", ">=", 0.6)),
                          S_("fo", ("fo_atr", "<", 0.5), ("fo_atr", "<", 0.3), ("fo_atr", "<", 0.15), ("fo_atr", "<", 0.0)),
                          S_("vwap", N, ("vwapDistPct", "<", 0.25), ("vwapDistPct", "<", 0), ("vwapDistPct", "<", -0.25)),
                          S_("uwick", N, ("upper_wick", ">", 0.3), ("upper_wick", ">", 0.5)),
                          S_("mom", N, ("momentum", "<", 0), ("momentum", "<", -0.5)),
                          S_("gap", N, ("gap", ">", 0), ("gap", ">", 1))]),
    # H: morning exhaustion short (rsi5 high, extended above SMA20, bear_div)
    "mexh": dict(side="short", universe=[("rsi5", ">", 80), ("sma20_dist_pct", ">", 0.5)],
                 windows=[(950, 1030), (950, 1130), (1030, 1130)],
                 slots=[S_("rsi5", ("rsi5", ">", 80), ("rsi5", ">", 85), ("rsi5", ">", 90), ("rsi5", ">", 95)),
                        S_("sma20", ("sma20_dist_pct", ">", 0.5), ("sma20_dist_pct", ">", 1), ("sma20_dist_pct", ">", 1.5), ("sma20_dist_pct", ">", 2)),
                        S_("bdiv", N, ("bear_div", "==", 1)),
                        S_("uwick", N, ("upper_wick", ">", 0.3), ("upper_wick", ">", 0.5)),
                        S_("fo", N, ("fo_atr", ">", 0.5), ("fo_atr", ">", 1.0)),
                        S_("climax", N, ("vol_climax", ">", 1.5), ("vol_climax", ">", 2.5)),
                        S_("gap", N, ("gap", ">", 0), ("gap", ">", 2))]),
    # I1: confirmation short - just lost VWAP (crossed below within 3 bars) after a run-up
    "vwaploss": dict(side="short", universe=[("vwapReclaim", "==", -1)],
                     windows=[(1000, 1130), (1000, 1300), (1100, 1400)],
                     slots=[S_("hodup", N, ("hod_fo_atr", ">=", 0.3), ("hod_fo_atr", ">=", 0.6), ("hod_fo_atr", ">=", 1.0)),
                            S_("back", N, ("dist_hod_atr", ">=", 0.2), ("dist_hod_atr", ">=", 0.4)),
                            S_("mom", N, ("momentum", "<", 0), ("momentum", "<", -0.5)),
                            S_("volr", N, ("volumeRatio", ">", 1), ("volumeRatio", ">", 1.5)),
                            S_("gap", N, ("gap", ">", 0), ("gap", ">", 1)),
                            S_("flow", N, ("flow3", "<", 0), ("flow3", "<", -0.5))]),
    # I2: confirmation short - lower high (off the 20-bar high, RSI turning down) after a run-up
    "lowerhigh": dict(side="short", universe=[("hod_fo_atr", ">=", 0.3), ("pricePosition", "<", 0.8), ("rsiSlope", "<", 0)],
                      windows=[(1000, 1130), (1000, 1300), (1100, 1400)],
                      slots=[S_("hodup", ("hod_fo_atr", ">=", 0.3), ("hod_fo_atr", ">=", 0.6), ("hod_fo_atr", ">=", 1.0)),
                             S_("pp", ("pricePosition", "<", 0.8), ("pricePosition", "<", 0.6), ("pricePosition", "<", 0.4)),
                             S_("rslope", ("rsiSlope", "<", 0), ("rsiSlope", "<", -3), ("rsiSlope", "<", -6)),
                             S_("vwap", N, ("vwapDistPct", "<", 0.25), ("vwapDistPct", "<", 0)),
                             S_("uwick", N, ("upper_wick", ">", 0.3), ("upper_wick", ">", 0.5)),
                             S_("sma20", N, ("sma20_dist_pct", "<", 0), ("sma20_dist_pct", "<", -0.25)),
                             S_("gap", N, ("gap", ">", 0), ("gap", ">", 1))]),
    # G: short the drop (MarcoFlow lesson) - new low of day, below open and VWAP
    "lodbreak": dict(side="short", universe=[("dist_lod_atr", "<=", 0.1), ("fromOpen", "<", 0), ("vwapDistPct", "<", 0)],
                     windows=[(950, 1030), (1000, 1100), (1030, 1200), (1100, 1300)],
                     slots=[S_("lod", ("dist_lod_atr", "<=", 0.1), ("dist_lod_atr", "<=", 0.05), ("dist_lod_atr", "<=", 0.02)),
                            S_("fo", ("fo_atr", "<", 0), ("fo_atr", "<", -0.25), ("fo_atr", "<", -0.5), ("fo_atr", "<", -1.0)),
                            S_("vwap", ("vwap_atr", "<", 0), ("vwap_atr", "<", -0.15), ("vwap_atr", "<", -0.3)),
                            S_("volr", N, ("volumeRatio", ">", 1), ("volumeRatio", ">", 1.5), ("volumeRatio", ">", 2)),
                            S_("gap", N, ("gap", ">", 0), ("gap", ">", 1)),
                            S_("rsi", N, ("rsi", ">", 25), ("rsi", ">", 30))]),
}


# ---------------------------------------------------------------------------------------------- stats
def stats(S, idx, side, geom):
    r_all = S.r[(side, geom)]
    if len(idx) == 0:
        return None
    r = r_all[idx].astype(np.float64)
    ok = np.isfinite(r)
    idx, r = idx[ok], r[ok]
    n = len(r)
    if n < 2:
        return None
    di = S.date_id[idx]
    mu = r.mean()
    nd = len(S.dates)
    sums = np.bincount(di, weights=r, minlength=nd)
    cnt = np.bincount(di, minlength=nd)
    act = cnt > 0
    dm = sums[act] - cnt[act] * mu
    se = float(np.sqrt((dm ** 2).sum()) / n) if act.sum() > 1 else np.nan
    best = int(np.argmax(np.where(act, sums, -np.inf)))
    exb = (r.sum() - sums[best]) / (n - cnt[best]) if n > cnt[best] else np.nan
    rp = r - S.prod_extra(idx, side, geom)
    mup = rp.mean()
    sp = np.bincount(di, weights=rp, minlength=nd)
    sep = float(np.sqrt(((sp[act] - cnt[act] * mup) ** 2).sum()) / n) if act.sum() > 1 else np.nan
    w = S.w[(side, geom)][idx]
    return dict(n=n, days=int(act.sum()), win=float(np.nanmean(w)), exp_r=float(mu), t=float(mu / se) if se > 0 else np.nan,
                exb=float(exb), green=float((sums[act] > 0).mean()), ctrl=float(np.nanmean(S.ctrl[(side, geom)][idx])),
                exp_prod=float(mup), t_prod=float(mup / sep) if sep > 0 else np.nan)


def run_family(fam, spec, splits, log):
    side = spec["side"]
    tmin, tmax = min(w[0] for w in spec["windows"]), max(w[1] for w in spec["windows"])
    subs, opts_masks, win_masks, base = {}, {}, {}, {}
    for nm, S in splits.items():
        u = (S.c["tod"] >= tmin) & (S.c["tod"] <= tmax)
        for c in spec["universe"]:
            u &= cond(S, *c)
        T = Sub(S, u)
        subs[nm] = T
        opts_masks[nm] = [[np.ones(T.n, bool) if o is None else cond(T, *o) for o in sl["opts"]] for sl in spec["slots"]]
        win_masks[nm] = [(T.c["tod"] >= a) & (T.c["tod"] <= b) for a, b in spec["windows"]]
        for wi, (a, b) in enumerate(spec["windows"]):
            for g in GEOMS:
                base[(nm, wi, g)] = S.baseline(side, g, a, b, key="all")
                # universe-restricted baseline: same window, same side, every bar of the family's universe
                base[(nm, wi, g, "u")] = float(np.nanmean(T.r[(side, g)][win_masks[nm][wi]])) if win_masks[nm][wi].any() else np.nan
        log(f"{fam} {nm}: universe rows {T.n:,}")
    shape = [len(sl["opts"]) for sl in spec["slots"]]
    rows = []
    for combo in itertools.product(*[range(k) for k in shape]):
        for nm in splits:
            T = subs[nm]
            m = np.ones(T.n, bool)
            for si, oi in enumerate(combo):
                if spec["slots"][si]["opts"][oi] is not None:
                    m &= opts_masks[nm][si][oi]
            for wi in range(len(spec["windows"])):
                idx = T.first_idx(m & win_masks[nm][wi])
                for g in GEOMS:
                    st = stats(T, idx, side, g)
                    rows.append((combo, wi, g, nm, st))
    # reshape -> one record per (combo, window, geom)
    rec = {}
    for combo, wi, g, nm, st in rows:
        k = (combo, wi, g)
        rec.setdefault(k, {})[nm] = st
    log(f"{fam}: {len(rec):,} configurations")
    return rec, base, shape


def neighbours(combo, shape):
    for i, k in enumerate(combo):
        for d in (-1, 1):
            j = k + d
            if 0 <= j < shape[i]:
                yield combo[:i] + (j,) + combo[i + 1:]


def describe(spec, combo, wi):
    parts = []
    for sl, oi in zip(spec["slots"], combo):
        o = sl["opts"][oi]
        if o is not None:
            parts.append(f"{o[0]} {o[1]} {o[2]}")
    a, b = spec["windows"][wi]
    return parts, f"{a:04d}-{b:04d}"


def summarise(fam, spec, rec, base, shape):
    side = spec["side"]
    out = []
    for (combo, wi, g), d in rec.items():
        tr, va = d.get("train"), d.get("valid")
        if not tr or not va:
            continue
        nb = [rec.get((c, wi, g), {}).get("valid") for c in neighbours(combo, shape)]
        nb_v = [x["exp_r"] for x in nb if x and x["n"] >= 10]
        nbt = [rec.get((c, wi, g), {}).get("train") for c in neighbours(combo, shape)]
        nb_t = [x["exp_r"] for x in nbt if x and x["n"] >= 10]
        bv, bvu = base[("valid", wi, g)], base[("valid", wi, g, "u")]
        bt, btu = base[("train", wi, g)], base[("train", wi, g, "u")]
        pl_v = float(np.mean(nb_v)) if nb_v else np.nan
        pl_t = float(np.mean(nb_t)) if nb_t else np.nan
        gate = (tr["exp_r"] > 0 and va["exp_r"] > 0 and va["n"] >= 30 and (va["t"] or 0) >= 1.5 and pl_v > 0
                and va["exp_r"] > bv and va["exp_r"] > bvu and tr["exp_r"] > bt)
        parts, win = describe(spec, combo, wi)
        out.append(dict(family=fam, side=side, combo=list(combo), window=win, geom=g, layers=parts, train=tr, valid=va,
                        base_valid=bv, base_valid_univ=bvu, base_train=bt, base_train_univ=btu,
                        plateau_valid=pl_v, plateau_valid_min=float(np.min(nb_v)) if nb_v else np.nan,
                        plateau_train=pl_t, n_neighbours=len(nb_v), gate=bool(gate)))
    return out


def main(fams):
    t0 = time.time()
    log = lambda s: print(f"[{time.time() - t0:7.1f}s] {s}", flush=True)
    splits = {"train": Split("train"), "valid": Split("valid")}
    log("loaded")
    allrows, counts = [], {}
    for fam in fams:
        spec = FAMILIES[fam]
        rec, base, shape = run_family(fam, spec, splits, log)
        counts[fam] = len(rec)
        rows = summarise(fam, spec, rec, base, shape)
        allrows += rows
        ok = [r for r in rows if r["gate"]]
        log(f"{fam}: gate passers {len(ok)} / {len(rows)}")
        with open(HERE / f"results_{fam}.jsonl", "w") as fh:
            for r in rows:
                fh.write(json.dumps(r, default=lambda x: None if x != x else float(x)) + "\n")
        del rec
        gc.collect()
    (HERE / "counts.json").write_text(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or list(FAMILIES))
