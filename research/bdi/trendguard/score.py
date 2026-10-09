"""Step 3: score the pre-declared trend-guard grid (NOTES.md section 1) on the 2-year open history with mcf/research/gates.py.

Per setup: 71 guard sets (none, 12 single G1-G5 variants, C3/C6/C12, 55 cross-family G pairs) x 3 exits (cur, E1, E2).
Lab / heat setups: guards are layers on the raw signal bars (signals.parquet), first unblocked bar per symbol-day; exits
simulated on 5-min bars exactly as setup_lab._outcomes_asym (validated against the frames' r column), production costs.
orb20_a / intraday_momentum: guards filter the backtester trades at entry; exits and C re-simulated on 1-min bars with the
engine's cost model. Outputs: results.csv (every configuration), data/best_trades.parquet. Locked block never loaded.
    python research/bdi/trendguard/score.py
Educational only - not financial advice.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
from lib import LOCKED_MONTHS, regimes  # noqa: E402
from mcf.research import gates as G  # noqa: E402

DATA = HERE / "data"
GEOMK = G.GEOMK
EXITS = ("cur", "E1", "E2")
NEW_PER_SETUP = 212

# ------------------------------------------------------------------ lineages (NOTES 1.7)
RESCORE = pd.read_csv(ROOT / "research/history2y/rescore.csv")
LINEAGE = {"exhaustion_short": "exh", "RW2 bdi-rw-exhaustion-noon-adv150": "exh", "heat_fade_short": "heat", "heat_fade_long": "heat",
           "orb20_a": "screen", "intraday_momentum": "screen"}


def lineage(setup: str) -> str:
    if setup in LINEAGE:
        return LINEAGE[setup]
    if setup.startswith("MF"):
        return "MF"
    if setup.startswith("NS"):
        return "NS"
    t = int(RESCORE.set_index("setup").loc[setup, "tries"])
    return f"rw{t}"


def tries_for(setup: str, setups: list[str]) -> int:
    lin = lineage(setup)
    k = sum(lineage(s) == lin for s in setups)
    return int(RESCORE.set_index("setup").loc[setup, "tries"]) + NEW_PER_SETUP * k


# ------------------------------------------------------------------ guard menu (NOTES 1.3 / 1.4)
SINGLES = {"G1": ["G1k1", "G1k2"], "G2": ["G2e9", "G2e21", "G2e9or21"], "G3": ["G3a", "G3b"],
           "G4": ["G4a25d5", "G4a25d10", "G4a30d5", "G4a30d10"], "G5": ["G5"]}


def guard_sets() -> list[str]:
    out = ["none"] + [v for vs in SINGLES.values() for v in vs] + ["C3", "C6", "C12"]
    for fa, fb in itertools.combinations(SINGLES, 2):
        out += [f"{a}+{b}" for a in SINGLES[fa] for b in SINGLES[fb]]
    assert len(out) == 71, len(out)
    return out


def block_arrays(F: pd.DataFrame, side: int) -> dict[str, np.ndarray]:
    """side -1 = short (owner's wording), +1 = long (mirror). True = do not enter on this bar."""
    s = -side                      # +1 for short: 'above' tests
    c, vw, sd = F["close"].to_numpy(), F["vwap"].to_numpy(), F["vsd"].to_numpy()
    out = {}
    with np.errstate(invalid="ignore"):
        beyond = s * (c - vw) > 0
        back = ~(s * (c - vw) > 0)                      # a close at or through VWAP resets the excursion
        seg = pd.Series(back.astype(np.int64)).groupby(F["dayid"].to_numpy()).cumsum().to_numpy()
        key = F["dayid"].to_numpy().astype(np.int64) * 10_000 + seg
        for k in (1, 2):
            band = s * (c - (vw + s * k * sd)) > 0
            flag = pd.Series(band).groupby(key).cummax().to_numpy()
            out[f"G1k{k}"] = beyond & flag
        for L in (9, 21):
            e, sl = F[f"ema{L}"].to_numpy(), F[f"ema{L}_sl"].to_numpy()
            out[f"G2e{L}"] = (s * (c - e) > 0) & (s * sl > 0)
        out["G2e9or21"] = out["G2e9"] | out["G2e21"]
        rsi, cmf, csl, osl = (F[k].to_numpy() for k in ("rsi", "cmf", "cmf_sl", "obv_sl"))
        ob = (rsi > 70) if s > 0 else (rsi < 30)
        a = ob & (s * cmf > 0) & (s * csl > 0)
        out["G3a"], out["G3b"] = a, a | (ob & (s * osl > 0))
        adx, gap = F["adx"].to_numpy(), s * (F["pdi"].to_numpy() - F["mdi"].to_numpy())
        for A in (25, 30):
            for D in (5, 10):
                out[f"G4a{A}d{D}"] = (adx > A) & (gap > D)
        lvl = F["vah"].to_numpy() if s > 0 else F["val"].to_numpy()
        out["G5"] = s * (c - lvl) > 0
    return out


def confirm_arrays(F: pd.DataFrame, side: int) -> tuple[np.ndarray, np.ndarray]:
    """C trigger (close through VWAP or EMA9 in the trade's direction) and volume divergence, per row."""
    c, vw, e9 = F["close"].to_numpy(), F["vwap"].to_numpy(), F["ema9"].to_numpy()
    with np.errstate(invalid="ignore"):
        if side == -1:
            trig = (c < vw) | (c < e9)
            div = (F["cmf"].to_numpy() < 0) | ((F["high"].to_numpy() >= F["hh20"].to_numpy()) & (F["volume"].to_numpy() < F["hh20v"].to_numpy()))
        else:
            trig = (c > vw) | (c > e9)
            div = (F["cmf"].to_numpy() > 0) | ((F["low"].to_numpy() <= F["ll20"].to_numpy()) & (F["volume"].to_numpy() < F["ll20v"].to_numpy()))
    return trig, div


# ------------------------------------------------------------------ numba kernels
@nb.njit(cache=True)
def c_entries(sig, N, side, high, low, trig, div, tod, dayid, cap):
    """sig: signal row indices sorted by row. Returns the confirmed entry row per opened wait (-1 = dropped), one trade
    per symbol-day."""
    out = np.full(len(sig), -1, np.int64)
    n = len(high)
    i = 0
    while i < len(sig):
        s = sig[i]
        d = dayid[s]
        ext = high[s] if side == -1 else low[s]
        lh = False
        dv = div[s]
        ent = -1
        for j in range(s + 1, min(n, s + N + 1)):
            if dayid[j] != d or tod[j] > cap:
                break
            x = high[j] if side == -1 else low[j]
            if side == -1:
                if x < ext:
                    lh = True
                ext = max(ext, x)
            else:
                if x > ext:
                    lh = True
                ext = min(ext, x)
            dv = dv or div[j]
            if lh and trig[j] and dv:
                ent = j
                break
        if ent >= 0:
            out[i] = ent
            while i < len(sig) and dayid[sig[i]] == d:      # one trade per symbol-day
                i += 1
        else:
            k = i + 1
            while k < len(sig) and dayid[sig[k]] == d and sig[k] <= s + N:
                k += 1
            i = k
    return out


@nb.njit(cache=True)
def sim5(e, side, upk, dnk, mode, R, atr, high, low, close, ema9, hi6, lo6, tod, dayid):
    """5-min path from entry row e. Returns (val in risk units, won, stopped, unit)."""
    px = close[e]
    unit = R
    sdist = dnk * R
    if mode == 2:
        if side == -1:
            dd = hi6[e] + 0.1 * atr - px
        else:
            dd = px - (lo6[e] - 0.1 * atr)
        if dd > 1.5 * R:
            dd = 1.5 * R
        if dd > 0 and np.isfinite(dd):
            sdist = dd
            unit = dd
    stop = px - side * sdist
    tgt = px + side * upk * R
    armed = False
    last = e
    n = len(close)
    for k in range(e + 1, n):
        if dayid[k] != dayid[e] or tod[k] > 1555:
            break
        last = k
        hs = (low[k] <= stop) if side == 1 else (high[k] >= stop)
        if hs:
            return -sdist / unit, 0, 1, unit
        ht = (high[k] >= tgt) if side == 1 else (low[k] <= tgt)
        if ht:
            return upk * R / unit, 1, 0, unit
        if mode == 1:
            fav = high[k] if side == 1 else low[k]
            if side * (fav - px) >= 0.5 * R:
                armed = True
            if armed and side * (close[k] - ema9[k]) < 0:
                return side * (close[k] - px) / unit, 0, 0, unit
    return side * (close[last] - px) / unit, 0, 0, unit


@nb.njit(cache=True)
def sim_many(ents, side, upk, dnk, mode, Rs, atrs, high, low, close, ema9, hi6, lo6, tod, dayid):
    m = len(ents)
    val, won, stp, unit = np.empty(m), np.empty(m, np.int64), np.empty(m, np.int64), np.empty(m)
    for i in range(m):
        val[i], won[i], stp[i], unit[i] = sim5(ents[i], side, upk, dnk, mode, Rs[i], atrs[i], high, low, close, ema9, hi6, lo6, tod, dayid)
    return val, won, stp, unit


def prod_cost(val, won, stp, unit, px):
    cost = (G.SLIP_PS + px * G.SLIP_BPS) + np.where(won == 1, 0.0, G.SLIP_PS + px * G.SLIP_BPS) + np.where(stp == 1, G.STOP_EXTRA, 0.0)
    return val - cost / unit


# ------------------------------------------------------------------ evaluation
def evaluate(tr: pd.DataFrame, reg: pd.DataFrame, n_tries: int, wf_months) -> dict:
    tr = tr[tr["date"].isin(reg.index)]
    o = G.summary(tr)
    if not o.get("n"):
        return {"n": 0, "verdict": "retire", "failed_gates": "no trades"}
    rs = G.regime_split(tr, reg)
    wf = G.walk_forward(tr, months=wf_months, exclude_months=LOCKED_MONTHS)
    dsr = G.deflated_sharpe(tr.groupby("date")["r"].sum().to_numpy(), n_tries)
    v, fails = G.verdict(o, rs, wf, n_tries)
    return {"n": o["n"], "days": o["days"], "per_day": round(o["n"] / o["days"], 2), "win_rate": o["win_rate"], "exp_r": o["exp_r"],
            "se": o["se"], "t": o["t"], "t_required": G.t_required(n_tries), "ex_best_day": o["ex_best_day"], "green_days": o["green_days"],
            "up_n": rs["up"].get("n", 0), "up_exp": rs["up"].get("exp_r"), "up_t": rs["up"].get("t"),
            "flat_n": rs["flat"].get("n", 0), "flat_exp": rs["flat"].get("exp_r"),
            "down_n": rs["down"].get("n", 0), "down_exp": rs["down"].get("exp_r"), "down_t": rs["down"].get("t"),
            "wf_folds": wf["n_folds"], "wf_share_pos": wf["share_positive"], "dsr": dsr.get("dsr"),
            "verdict": v, "failed_gates": "; ".join(fails)}


def load_features() -> pd.DataFrame:
    F = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "feat").glob("part-*.parquet"))], ignore_index=True)
    F = F.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    F["dayid"] = pd.factorize(F["symbol"].astype(str) + "|" + F["date"].dt.strftime("%Y-%m-%d"))[0].astype(np.int64)
    return F


def lab_part(F, reg, wf_months, setups_all, rows, keep_trades, validation):
    sig = pd.read_parquet(DATA / "signals.parquet")
    sig = sig.merge(F[["symbol", "date", "tod"]].reset_index(names="row"), on=["symbol", "date", "tod"], how="left")
    miss = sig["row"].isna().groupby(sig["setup"]).mean()
    validation["signals_without_feature_row"] = {k: round(float(v), 5) for k, v in miss.items()}
    sig = sig.dropna(subset=["row"]).astype({"row": np.int64}).sort_values(["setup", "row"]).reset_index(drop=True)
    arr = {k: F[k].to_numpy(np.float64) for k in ("high", "low", "close", "ema9", "hi6", "lo6")}
    tod, dayid = F["tod"].to_numpy(np.int64), F["dayid"].to_numpy(np.int64)
    dates, syms = F["date"].dt.date.to_numpy(), F["symbol"].astype(str).to_numpy()
    blocks = {sd: block_arrays(F, sd) for sd in (-1, 1)}
    confs = {sd: confirm_arrays(F, sd) for sd in (-1, 1)}
    # per-day atr from the frames (R = 0.25 x atr_d); every row of a day gets that day's value
    atr_day = sig.groupby(dayid[sig["row"].to_numpy()])["atr_d"].first()
    atr_row = pd.Series(dayid).map(atr_day).to_numpy(np.float64)
    gsets = guard_sets()
    for (setup, side_s, geom), g in sig.groupby(["setup", "side", "geom"], sort=False):
        name = setup if setup not in ("heat_fade_short", "heat_fade_long") else setup
        side = -1 if side_s == "short" else 1
        upk, dnk = GEOMK[geom]
        n_tries = tries_for(name, setups_all)
        srows = g["row"].to_numpy(np.int64)
        bl = blocks[side]
        trig, div = confs[side]
        t0 = time.time()
        for gs in gsets:
            if gs.startswith("C"):
                ent = c_entries(srows, int(gs[1:]), side, arr["high"], arr["low"], trig, div, tod, dayid, 1500)
                ent = ent[ent >= 0]
            else:
                ok = np.ones(len(srows), bool)
                if gs != "none":
                    for p in gs.split("+"):
                        ok &= ~bl[p][srows]
                cand = srows[ok]
                if not len(cand):
                    ent = cand
                else:
                    _, first = np.unique(dayid[cand], return_index=True)
                    ent = cand[np.sort(first)]
            for mode, ex in enumerate(EXITS):
                R = 0.25 * atr_row[ent]
                val, won, stp, unit = sim_many(ent, side, upk, dnk, mode, R, atr_row[ent], arr["high"], arr["low"], arr["close"],
                                               arr["ema9"], arr["hi6"], arr["lo6"], tod, dayid)
                r = prod_cost(val, won, stp, unit, arr["close"][ent])
                tr = pd.DataFrame({"date": dates[ent], "symbol": syms[ent], "tod": tod[ent], "r": r})
                if gs == "none" and ex == "cur":
                    # validation: the simulator against the frames' lab outcome (lab R incl. 1c per side)
                    fr = g.drop_duplicates("row").set_index("row").loc[ent]
                    lab = val - 2 * 0.01 / R
                    validation[f"{name}"] = {"n": int(len(ent)), "max_abs_diff_lab_r": round(float(np.nanmax(np.abs(lab - fr["r_frame"].to_numpy()))), 5),
                                             "share_diff_gt_0.01": round(float(np.mean(np.abs(lab - fr["r_frame"].to_numpy()) > 0.01)), 5)}
                res = evaluate(tr, reg, n_tries, wf_months)
                rows.append({"setup": name, "side": side_s, "geom": geom, "guard": gs, "exit": ex, "lineage": lineage(name), "tries": n_tries, **res})
                keep_trades[(name, gs, ex)] = tr
        print(f"{name}: {len(gsets) * 3} configs ({time.time() - t0:.0f}s)", flush=True)


# ------------------------------------------------------------------ bt setups (1-min re-simulation)
@nb.njit(cache=True)
def sim1(j, side, fill, stop, tgt, has_tgt, mode, E2stop, o, h, l, c, ema_close, hhmm, bps, ps, sx):
    """1-min path from minute j (the fill minute, as the engine). Returns r (engine cost model)."""
    risk = side * (fill - stop)
    if mode == 2 and np.isfinite(E2stop):
        d = side * (fill - E2stop)
        if d > 1.5 * risk:
            d = 1.5 * risk
        if d > 0:
            stop = fill - side * d
            risk = d
    armed = False
    n = len(o)
    for k in range(j, n):
        if hhmm[k] >= 1555:
            ex = o[k] * (1 - side * bps / 1e4) - side * ps
            return side * (ex - fill) / risk
        hs = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hs:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            ex = px * (1 - side * bps / 1e4) - side * (ps + sx)
            return side * (ex - fill) / risk
        if has_tgt:
            ht = (h[k] >= tgt) if side == 1 else (l[k] <= tgt)
            if ht:
                return side * (tgt - fill) / risk
        if mode == 1:
            fav = h[k] if side == 1 else l[k]
            if side * (fav - fill) >= 0.5 * risk:
                armed = True
            if armed and np.isfinite(ema_close[k]) and side * (c[k] - ema_close[k]) < 0:
                ex = c[k] * (1 - side * bps / 1e4) - side * ps
                return side * (ex - fill) / risk
    ex = c[n - 1] * (1 - side * bps / 1e4) - side * ps
    return side * (ex - fill) / risk


def bt_part(F, reg, wf_months, setups_all, rows, keep_trades, validation):
    from mcf.backtest.engine import Costs
    from mcf.config import load_config
    cs = Costs.from_cfg(load_config()["costs"])
    b = pd.read_parquet(ROOT / "research/history2y/data/bt_trades.parquet")
    et = pd.to_datetime(b["entry_time"])
    b = b[(et.dt.hour * 100 + et.dt.minute >= 950)].copy()
    b["date"] = pd.to_datetime(b["date"])
    b = b[b["date"].isin(pd.to_datetime(list(reg.index)))].reset_index(drop=True)
    et = pd.to_datetime(b["entry_time"])
    mins = et.dt.hour * 60 + et.dt.minute
    fl = (mins // 5) * 5
    b["tod5"] = ((fl // 60) * 100 + fl % 60).astype(int)
    Fi = F[["symbol", "date", "tod"]].reset_index(names="frow")
    b = b.merge(Fi.rename(columns={"tod": "tod5"}), on=["symbol", "date", "tod5"], how="left")
    m1 = pd.read_parquet(DATA / "bt1m.parquet")
    m1["date"] = pd.to_datetime(m1["ts"].dt.date)
    m1["hhmm"] = (m1["ts"].dt.hour * 100 + m1["ts"].dt.minute).astype(np.int64)
    end = m1["ts"] + pd.Timedelta(minutes=1)
    m1["tod_end"] = np.where(end.dt.minute % 5 == 0, end.dt.hour * 100 + end.dt.minute, -1)
    m1 = m1.merge(F[["symbol", "date", "tod", "ema9"]].rename(columns={"tod": "tod_end"}), on=["symbol", "date", "tod_end"], how="left")
    m1 = m1.sort_values(["symbol", "ts"]).reset_index(drop=True)
    grp = {k: (v.index.min(), v.index.max() + 1) for k, v in m1.groupby(["symbol", "date"])}
    O, H, L, C, E9 = (m1[k].to_numpy(np.float64) for k in ("open", "high", "low", "close", "ema9"))
    HM = m1["hhmm"].to_numpy(np.int64)
    TS = m1["ts"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
    blocks = {sd: block_arrays(F, sd) for sd in (-1, 1)}
    confs = {sd: confirm_arrays(F, sd) for sd in (-1, 1)}
    fa = {k: F[k].to_numpy(np.float64) for k in ("high", "low", "close", "hi6", "lo6", "atr_d")}
    ftod, fday = F["tod"].to_numpy(np.int64), F["dayid"].to_numpy(np.int64)
    gsets = guard_sets()
    for name, g in b.groupby("strategy"):
        n_tries = tries_for(name, setups_all)
        g = g[g["frow"].notna()].copy()
        validation[f"{name}_trades_without_feature_row"] = int(b[(b.strategy == name) & b.frow.isna()].shape[0])
        g["frow"] = g["frow"].astype(np.int64)
        recs = []
        for _, t in g.iterrows():
            key = (t["symbol"], t["date"])
            if key not in grp:
                continue
            a, z = grp[key]
            ts = TS[a:z]
            jj = np.searchsorted(ts, np.datetime64(pd.Timestamp(t["entry_time"]).tz_convert("UTC").tz_localize(None)))
            if jj >= len(ts):
                continue
            recs.append((a, z, a + jj, int(t["side"]), float(t["entry"]), float(t["stop"]), float(t["target"]) if pd.notna(t["target"]) else np.nan,
                         int(t["frow"]), float(t["r_multiple"]), t["date"].date(), t["symbol"], int(t["tod5"])))
        R = pd.DataFrame(recs, columns=["a", "z", "j", "side", "fill", "stop", "tgt", "frow", "r_rec", "date", "symbol", "tod"])
        for gs in gsets:
            for mode, ex in enumerate(EXITS):
                rr, keep = np.full(len(R), np.nan), np.zeros(len(R), bool)
                for i, t in enumerate(R.itertuples(index=False)):
                    sd = t.side
                    if gs.startswith("C"):
                        Nn = int(gs[1:])
                        trig, div = confs[sd]
                        e = c_entries(np.array([t.frow]), Nn, sd, fa["high"], fa["low"], trig, div, ftod, fday, 1550)[0]
                        if e < 0:
                            continue
                        px = fa["close"][e]
                        fill = px * (1 + sd * cs.bps / 1e4) + sd * cs.per_share
                        stop, tgt = fill + (t.stop - t.fill), (t.tgt + (fill - t.fill)) if np.isfinite(t.tgt) else np.nan
                        hh = ftod[e]
                        j = t.a + int(np.searchsorted(HM[t.a:t.z], hh))      # first minute starting at the bar's end
                        frow = e
                        if j >= t.z:
                            continue
                    else:
                        if gs != "none" and any(blocks[sd][p][t.frow] for p in gs.split("+")):
                            continue
                        fill, stop, tgt, j, frow = t.fill, t.stop, t.tgt, t.j, t.frow
                    e2 = (fa["hi6"][frow] + 0.1 * fa["atr_d"][frow]) if sd == -1 else (fa["lo6"][frow] - 0.1 * fa["atr_d"][frow])
                    rr[i] = sim1(j - t.a, sd, fill, stop, tgt if np.isfinite(tgt) else 0.0, bool(np.isfinite(tgt)), mode, e2,
                                 O[t.a:t.z], H[t.a:t.z], L[t.a:t.z], C[t.a:t.z], E9[t.a:t.z], HM[t.a:t.z], cs.bps, cs.per_share, cs.stop_extra_per_share)
                    keep[i] = True
                tr = pd.DataFrame({"date": R["date"][keep].to_numpy(), "symbol": R["symbol"][keep].to_numpy(), "tod": R["tod"][keep].to_numpy(), "r": rr[keep]})
                if gs == "none" and ex == "cur":
                    d = np.abs(rr - R["r_rec"].to_numpy())
                    validation[name] = {"n": int(keep.sum()), "median_abs_diff_r": round(float(np.nanmedian(d)), 5),
                                        "share_diff_gt_0.05": round(float(np.nanmean(d > 0.05)), 4),
                                        "resim_exp": round(float(np.nanmean(rr)), 4), "recorded_exp": round(float(R["r_rec"].mean()), 4)}
                res = evaluate(tr, reg, n_tries, wf_months)
                rows.append({"setup": name, "side": "both", "geom": "bt", "guard": gs, "exit": ex, "lineage": lineage(name), "tries": n_tries, **res})
                keep_trades[(name, gs, ex)] = tr
        print(f"{name}: done", flush=True)


if __name__ == "__main__":
    t0 = time.time()
    reg = regimes()
    wf_months = sorted(set(pd.PeriodIndex(pd.to_datetime(list(reg.index)), freq="M").astype(str)))
    setups_all = [s for s in RESCORE["setup"] if not str(s).startswith("VID")]
    assert len(setups_all) == 23, setups_all
    F = load_features()
    print(f"features {len(F)} rows, {F['dayid'].max() + 1} symbol-days ({time.time() - t0:.0f}s)", flush=True)
    rows, keep, validation = [], {}, {}
    lab_part(F, reg, wf_months, setups_all, rows, keep, validation)
    bt_part(F, reg, wf_months, setups_all, rows, keep, validation)
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "results.csv", index=False)
    (HERE / "validation.json").write_text(json.dumps(validation, indent=1, default=str))
    best = res.sort_values("t", ascending=False).groupby("setup").head(1)
    bt = pd.concat([keep[(r.setup, r.guard, r.exit)].assign(setup=r.setup, guard=r.guard, exit=r.exit) for r in best.itertuples()])
    bt.to_parquet(DATA / "best_trades.parquet", index=False)
    print(f"configs scored: {len(res)} ({time.time() - t0:.0f}s)")
    print(res["verdict"].value_counts().to_string())
