"""Build video-digest features + structural-exit outcomes for the setup-lab frame (train+valid dates only).

Reads data/cache/1Min with a parquet filter timestamp < 2026-09-16 (later rows are never loaded).
Writes research/bdi/videos/data/parts/<SYM>.parquet keyed by symbol, date, tod (git-ignored).
Structural outcomes (R = 0.25 x daily ATR, the lab's atr_d definition), simulated on 1-minute bars:
market entry at the next 1-minute open after the signal bar closes; 1c + 1 bps against us per side, +2c on stop
fills; stop first inside a bar; gaps through a stop fill at the open; flat at the 15:55 open.
Requires numba (research only; the live mask path needs only numpy/pandas).
Usage: python research/bdi/videos/build.py [--test-causal] [--symbols A,B]
Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, str(Path(__file__).parent))
from features import ANCHORS, BLK_C, BLK_E, BLK_L, day_features  # noqa: E402

CACHE = Path("data/cache/1Min")
CUT = pd.Timestamp("2026-09-16", tz="America/New_York")
FIRST = pd.Timestamp("2026-06-30").date()
OUT = Path("research/bdi/videos/data/parts")
SLIP_BPS, SLIP_C, STOP_C = 1e-4, 0.01, 0.02


@njit(cache=True)
def sim(o, h, l, c, entries, side, stops, tgts, line, use_line, flags, tend, R):
    out = np.full(len(entries), np.nan)
    nm = len(o)
    for k in range(len(entries)):
        e = entries[k]
        if e < 0 or e >= tend or not (R > 0):
            continue
        fill = o[e] + side * (o[e] * SLIP_BPS + SLIP_C)
        st = stops[k]
        tg = tgts[k]
        ex = np.nan
        is_stop = False
        for t in range(e, tend):
            if st == st:
                if (side == 1 and l[t] <= st) or (side == -1 and h[t] >= st):
                    ex = min(o[t], st) if side == 1 else max(o[t], st)
                    is_stop = True
                    break
            lv = tg
            if use_line:
                lv = line[t - 1] if t > e else line[e - 1]
            if lv == lv:
                if (side == 1 and h[t] >= lv) or (side == -1 and l[t] <= lv):
                    ex = max(o[t], lv) if side == 1 else min(o[t], lv)
                    break
            if flags[t]:
                ex = o[t + 1] if t + 1 < nm else c[t]
                break
        if ex != ex:
            ex = o[tend] if tend < nm else c[nm - 1]
        net = ex - side * (ex * SLIP_BPS + SLIP_C + (STOP_C if is_stop else 0.0))
        out[k] = side * (net - fill) / R
    return out


@njit(cache=True)
def sim_blk(o, h, l, c, starts, side, pocs, stops, tgts, close5_min, close5_px, cancel_idx, tend, R):
    """Limit at POC from `starts`; cancel on a 5-minute close beyond the stop level or at cancel_idx (15:00)."""
    out = np.full(len(starts), np.nan)
    nm = len(o)
    for k in range(len(starts)):
        s = starts[k]
        if s < 0 or not (R > 0):
            continue
        pc, st, tg = pocs[k], stops[k], tgts[k]
        f = -1
        fill = np.nan
        for t in range(s, min(cancel_idx, tend)):
            if (side == 1 and l[t] <= pc) or (side == -1 and h[t] >= pc):
                px = min(o[t], pc) if side == 1 else max(o[t], pc)
                fill = px + side * (px * SLIP_BPS + SLIP_C)
                f = t
                break
            if close5_min[t]:
                if (side == 1 and close5_px[t] < st + 0.01) or (side == -1 and close5_px[t] > st - 0.01):
                    break
        if f < 0:
            continue
        ex = np.nan
        is_stop = False
        for t in range(f, tend):
            if (side == 1 and l[t] <= st) or (side == -1 and h[t] >= st):
                ex = min(o[t], st) if side == 1 else max(o[t], st)
                if t == f:
                    ex = st
                is_stop = True
                break
            if t > f and ((side == 1 and h[t] >= tg) or (side == -1 and l[t] <= tg)):
                ex = max(o[t], tg) if side == 1 else min(o[t], tg)
                break
        if ex != ex:
            ex = o[tend] if tend < nm else c[nm - 1]
        net = ex - side * (ex * SLIP_BPS + SLIP_C + (STOP_C if is_stop else 0.0))
        out[k] = side * (net - fill) / R
    return out


def outcomes(b1, F, aux, atr):
    o, h, l, c = (b1[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    mos = aux["mos"]
    nm = len(o)
    tend = int(np.searchsorted(mos, 385))
    cancel = int(np.searchsorted(mos, 330))
    R = 0.25 * atr if np.isfinite(atr) else np.nan
    m_end = aux["m_end"]
    n = len(F)
    ent = (m_end + 1).astype(np.int64)
    ent[ent >= nm] = -1
    g = lambda k: F[k].to_numpy(float)
    c5, h5, l5, e9, vw5 = g("c5"), g("h5"), g("l5"), g("e9"), g("vw5")
    e91 = pd.Series(c).ewm(span=9, adjust=False).mean().to_numpy()
    nan = np.full(n, np.nan)
    empty = np.zeros(1)
    res = {}
    for side, nm_ in ((1, "long"), (-1, "short")):
        fl_jd = np.zeros(nm, np.bool_)
        jd_bad = (c5 < np.maximum(e9, vw5)) if side == 1 else (c5 > np.minimum(e9, vw5))
        fl_jd[m_end[jd_bad]] = True
        fl_e9 = (c < e91) if side == 1 else (c > e91)
        hod_p, lod_p, vpk_p = g("hod_p"), g("lod_p"), g("vpk_p")
        with np.errstate(invalid="ignore"):
            if side == 1:
                top = (~(h5 < hod_p)) & (g("uw") >= 0.5) & (~(g("v5") < vpk_p))
            else:
                top = (~(l5 > lod_p)) & (g("lw") >= 0.5) & (~(g("v5") < vpk_p))
        fl_vt = np.zeros(nm, np.bool_)
        fl_vt[m_end[top]] = True
        fl_vt9 = fl_vt.copy()
        fl_vt9[m_end[(c5 < e9) if side == 1 else (c5 > e9)]] = True
        noflag = np.zeros(nm, np.bool_)
        entry_px = np.where(ent >= 0, o[np.clip(ent, 0, nm - 1)], np.nan)
        hard = entry_px - side * 2 * R
        ext3 = (pd.Series(l5).rolling(3, min_periods=1).min() - 0.01) if side == 1 else (pd.Series(h5).rolling(3, min_periods=1).max() + 0.01)
        ext3 = ext3.to_numpy()
        run = lambda stops, tgts, flags, line=empty, ul=False: sim(o, h, l, c, ent, side, stops, tgts, line, ul, flags, tend, R)
        res[f"x_{nm_}_jd"] = run(hard, nan, fl_jd)
        res[f"x_{nm_}_e9c1"] = run(hard, nan, fl_e9)
        res[f"x_{nm_}_vt"] = run(ext3, nan, fl_vt)
        res[f"x_{nm_}_vt9"] = run(ext3, nan, fl_vt9)
        res[f"x_{nm_}_tx"] = run(hard, nan, noflag)
        lodx = (g("lod") - 0.01) if side == 1 else (g("hod") + 0.01)
        for nmx, tgt in (("poc", g("ppoc")), ("poc2", g("pvah70") if side == 1 else g("pval70"))):
            ahead = side * (tgt - c5) > 0
            res[f"x_{nm_}_{nmx}"] = np.where(ahead, run(lodx, np.where(ahead, tgt, np.nan), noflag), np.nan)
        for a in ANCHORS:
            av = g(f"av_{a}")
            if a not in aux["lines"]:
                res[f"x_{nm_}_avw_{a}"] = nan.copy()
                continue
            ahead = side * (av - c5) > 0
            r = run(entry_px - side * R, nan, noflag, aux["lines"][a], True)
            res[f"x_{nm_}_avw_{a}"] = np.where(ahead, r, np.nan)
        # block limit orders
        c5min = np.zeros(nm, np.bool_)
        c5px = np.full(nm, np.nan)
        c5min[m_end] = True
        c5px[m_end] = c5
        sk = "L" if side == 1 else "S"
        for L in BLK_L:
            for cp in BLK_C:
                for e in BLK_E:
                    key = f"{L}_{cp}_{e}"
                    col = np.full(n, np.nan)
                    orders = aux["blk"][(sk, key)]
                    if orders:
                        bi = np.array([x[0] for x in orders])
                        st = np.array([x[1] for x in orders], float)
                        stp = np.array([x[2] for x in orders], float) - side * 0.01
                        tg = np.array([x[3] for x in orders], float)
                        starts = np.where(m_end[bi] + 1 < nm, m_end[bi] + 1, -1).astype(np.int64)
                        col[bi] = sim_blk(o, h, l, c, starts, side, st, stp, tg, c5min, c5px, cancel, tend, R)
                    res[f"x_{nm_}_blk_{key}"] = col
    return pd.DataFrame({k: v.astype(np.float32) for k, v in res.items()}, index=F.index)


def load_symbol(path):
    m = pd.read_parquet(path, filters=[("timestamp", "<", CUT)])
    m = m[m.index < CUT].between_time("09:30", "15:59")
    return m


def symbol_days(m):
    """Per-day context exactly as the engine builds it (SymbolHistory)."""
    dates = np.array(m.index.date)
    days = sorted(set(dates))
    daily = m.groupby(dates).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = daily["close"].shift(1)
    tr = pd.concat([daily.high - daily.low, (daily.high - pc).abs(), (daily.low - pc).abs()], axis=1).max(axis=1)
    atr_lab = tr.rolling(14, min_periods=10).mean().shift(1)            # heat_frame's atr_d
    sma20 = daily["close"].rolling(20, min_periods=15).mean().shift(1)    # engine's ctx.sma20
    mos = m.index.hour * 60 + m.index.minute - 570
    prof = pd.DataFrame({"d": dates, "mos": mos, "v": m["volume"].to_numpy()}).pivot_table(
        index="d", columns="mos", values="v", aggfunc="sum").fillna(0).cumsum(axis=1)
    acv = prof.rolling(14, min_periods=5).mean().shift(1)
    d5all = m.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"])
    d5d = np.array(d5all.index.date)
    by = {d: g for d, g in m.groupby(dates)}
    return days, by, atr_lab, sma20, acv, d5all, d5d


def one(path, check_causal=False):
    try:
        m = load_symbol(path)
    except Exception:
        return None
    if len(m) < 2000:
        return None
    days, by, atr_lab, sma20, acv, d5all, d5d = symbol_days(m)
    out = []
    for i, d in enumerate(days):
        if d < FIRST or i == 0:
            continue
        b1 = by[d]
        if len(b1) < 60:
            continue
        p1 = by[days[i - 1]]
        a = np.searchsorted(d5d, d)
        prior5 = d5all.iloc[max(0, a - 40): a]
        atr = float(atr_lab.get(d, np.nan))
        ac = acv.loc[d].to_numpy() if d in acv.index else None
        F, aux = day_features(b1, p1, prior5, ac, atr, aux=True)
        if F.empty:
            continue
        if check_causal:
            for cut in (25, 70, 150, 260):
                if cut < len(b1):
                    Ft = day_features(b1.iloc[:cut], p1, prior5, ac, atr)
                    if len(Ft):
                        A_, B_ = F.iloc[:len(Ft)], Ft
                        for col in F.columns:
                            x, y = A_[col].to_numpy(float), B_[col].to_numpy(float)
                            bad = ~((np.isclose(x, y, rtol=1e-5, atol=1e-6)) | (np.isnan(x) & np.isnan(y)))
                            if bad.any():
                                raise AssertionError(f"look-ahead in {col} {path.stem} {d} cut {cut}: {x[bad][:3]} vs {y[bad][:3]}")
        X = outcomes(b1, F, aux, atr)
        F = F.join(X)
        F["d_sma20"] = np.float32(sma20.get(d, np.nan))
        F["atr_b"] = np.float32(atr)
        F = F[(F.tod >= 950) & (F.tod <= 1500)]
        F["date"] = d
        out.append(F.reset_index(drop=True))
    if not out:
        return None
    x = pd.concat(out, ignore_index=True)
    x["symbol"] = path.stem
    x["tod"] = x["tod"].astype("int16")
    OUT.mkdir(parents=True, exist_ok=True)
    x.to_parquet(OUT / f"{path.stem}.parquet", index=False)
    return len(x)


if __name__ == "__main__":
    args = sys.argv[1:]
    files = sorted(CACHE.glob("*.parquet"))
    if "--symbols" in args:
        want = set(args[args.index("--symbols") + 1].split(","))
        files = [f for f in files if f.stem in want]
    if "--test-causal" in args:
        for f in files[:int(args[args.index("--test-causal") + 1]) if len(args) > args.index("--test-causal") + 1
                       and args[args.index("--test-causal") + 1].isdigit() else 5]:
            print(f.stem, one(f, check_causal=True), "rows - causal check passed", flush=True)
        sys.exit(0)
    done = {p.stem for p in OUT.glob("*.parquet")} if OUT.exists() else set()
    files = [f for f in files if f.stem not in done]
    tot = 0
    with Pool(4) as p:
        for k, r in enumerate(p.imap_unordered(one, files, chunksize=2)):
            tot += r or 0
            if k % 50 == 0:
                print(k, len(files), tot, flush=True)
    print("done rows", tot)
