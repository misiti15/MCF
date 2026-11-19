"""ULT-17 SECTOR-LAG backtest (ultimate_1119 round2/PLAN.md sec. 1-2, 3 "ULT-17", 5, 6).

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo), plus the
point-in-time sector columns sec_fo (sector ETF frame fromOpen at the same date/tod), sec_atrp (100 x sector ETF atr_d /
its close at the bar) and sec_beta. Sector map = ULT-11's sector_map() (imported, unchanged): argmax Pearson correlation
of daily close-to-close returns over the prior <= 60 open non-locked sessions (min 20) among 22 ETFs, beta OLS clipped
[0.3, 3]; FIT map built from daily rows <= 2025-09-30 only; the CHECK map is built only after fitsel.json is frozen.
Features and trigger come from the LIVE module (modules/ULT-17.py: features(), trigger()); a superset (S 0.15, Lmin 0.10,
window 10:15-15:00, both sides, stocks only = module SYMBOLS, ADV20 >= $50M, cost_r <= 0.08, universal filters, shorts
ETB) is built once per half; every grid config is a sub-filter (S 0.25 / Lmin 0.20 / exit TX30 or TX45).
Chassis (round 2): entry at the OPEN of the 1-minute bar that starts at the decision-bar close (LR8 entry cost on it);
catastrophic stop 2u from the entry (u = 0.25 x prior-day daily ATR), walked on 1-minute bars (data/cache_hist/1Min):
stop gap-through at the worse of open/stop; time exit at the close of minute entry + h - 1 (flat 15:50). R per 2u
(actual risk); R in 0.25-dATR units = 2 x R. Costs LR8 (entry (1c + 1bp) x tod mult; exit 1c + 1bp; +2c stops) + 1.2 bp
of entry notional borrow fee on every short. One lot per symbol (both sides share it); refire only >= 30 min after the
exit; max 2 per symbol-session; day cap 30 over both sides (first by time, ties ADV20 desc).
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK secmap fit|check ; sig fit|check ; walk fit|check ; fit | fitrandom | check | plateau
Educational only - not financial advice."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ULT = HERE.parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ULT / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
MOD = ULT / "modules" / "ULT-17.py"
N_CUM = 774
DAY_CAP = 30
BORROW = 1.2e-4
HS = (30, 45)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B14 = _load(HERE.parent / "ULT-14" / "bt.py", "bt14")      # shared helpers: stats, sub_halves, etb_set, half_months
B11 = _load(HERE.parent / "ULT-11" / "bt.py", "bt11")      # sector_map (unchanged)
no_locked, m2, hhmm, etb_set, half_months, sha = B14.no_locked, B14.m2, B14.hhmm, B14.etb_set, B14.half_months, B14.sha


def load_mod():
    return _load(MOD, "ult17")


def stats(t, n, col="r", sides=True):
    return B14.stats(t, n, col, sides)


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(args):
    month, work = args
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower())]]
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    no_locked(f["date"].unique())
    half = "fit" if month in FIT_MONTHS else "check"
    sm = pd.read_parquet(Path(work) / f"secmap_{half}.parquet",
                         filters=[("date", ">=", month + "-01"), ("date", "<=", month + "-31")])
    no_locked(sm.date.unique())
    e = f[f.symbol.isin(mod.SECTOR_ETFS)][["symbol", "date", "tod", "fromOpen", "atr_d", "close"]].copy()
    e["sec_atrp"] = 100 * e.atr_d / e.close
    e = e.rename(columns={"symbol": "sec", "fromOpen": "sec_fo"})[["sec", "date", "tod", "sec_fo", "sec_atrp"]]
    e = e.drop_duplicates(["sec", "date", "tod"])
    f = f[f.symbol.isin(mod.SYMBOLS)]
    f = f.merge(sm, on=["symbol", "date"], how="left").merge(e, on=["sec", "date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    r = mod.features(f)
    tod = r["tod"]
    adv = f["adv20"].fillna(0).to_numpy()
    base = (tod >= 1015) & (tod <= 1500) & (adv >= mod.MIN_ADV)
    etb = f["symbol"].isin(etb_set()).to_numpy()
    tl = mod.trigger(r, 1, 0.15, 0.10) & base
    ts_all = mod.trigger(r, -1, 0.15, 0.10) & base
    ts = ts_all & etb
    out = []
    for sgn, mk in ((1, tl), (-1, ts)):
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "sec"]].copy()
        s["side"] = sgn
        for k in ("sret3", "nret3", "lag", "smove", "beta", "satrp", "cost_r", "spy_fo"):
            s[k] = r[k][mk]
        out.append(s)
    s = pd.concat(out, ignore_index=True)
    cover = float(np.isfinite(r["sret3"])[base].mean()) if base.any() else np.nan
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, s, days, int((ts_all & ~etb).sum()), cover


# ---------------------------------------------------------------- stage 2: 1-minute walk (TX30 + TX45, side-aware)
def walk_job(args):
    sym, T = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    ds_ = sorted(T.date.unique())
    a, b_ = pd.Timestamp(ds_[0], tz=tz), pd.Timestamp(ds_[-1], tz=tz) + pd.Timedelta(days=1)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= a) & (fld < b_)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hm_all = m2((b.index.hour * 100 + b.index.minute).to_numpy())
    day = b.index.date.astype(str)
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[x]: np.arange(x, y) for x, y in zip(st, en)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        row = [r.Index]
        if ix is None:
            res.append(tuple(row + [np.nan] * (1 + 4 * len(HS)))); continue
        hm = hm_all[ix]
        t0 = m2(r.tod)
        j0 = np.searchsorted(hm, t0)
        if j0 >= len(ix) or hm[j0] - t0 > 4 or hm[j0] >= m2(1550):
            res.append(tuple(row + [np.nan] * (1 + 4 * len(HS)))); continue
        e = O[ix[j0]]
        dclose = r.close
        if r.random:      # random control: decision close = close of the minute before tod
            if j0 == 0 or hm[j0 - 1] < t0 - 5:
                res.append(tuple(row + [np.nan] * (1 + 4 * len(HS)))); continue
            dclose = C[ix[j0 - 1]]
        s, u = int(r.side), 0.25 * r.atr_d
        mult = float(tod_cost_mult(np.array([r.tod]))[0])
        row.append(e)
        for h in HS:
            tend = min(hm[j0] + h - 1, m2(1549))
            outs = []
            for ee in (e, dclose):           # chassis fill; signal-close fill (bias diagnostic)
                stop = ee - s * 2 * u
                px = None
                for q in ix[j0:]:
                    if hm_all[q] > tend:
                        break
                    if (s > 0 and L[q] <= stop) or (s < 0 and H[q] >= stop):
                        px, kd, xt = (min(O[q], stop) if s > 0 else max(O[q], stop)), 1, hm_all[q] + 1
                        break
                    px, kd, xt = C[q], 0, hm_all[q] + 1
                    last = q
                if px is not None and kd == 0:
                    px = C[last]
                outs.append((px, kd, xt))
            (pA, kA, xA), (pB, kB, _) = outs
            rA = (s * (pA - e) - ((0.01 + e * 1e-4) * mult + 0.01 + pA * 1e-4 + 0.02 * (kA == 1)
                                  + (BORROW * e if s < 0 else 0))) / (2 * u)
            rB = (s * (pB - dclose) - ((0.01 + dclose * 1e-4) * mult + 0.01 + pB * 1e-4 + 0.02 * (kB == 1))) / (2 * u)
            row += [rA, kA, xA, rB]
        res.append(tuple(row))
    return res


def walk(T, random=False, procs=3):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(procs) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    cols = ["i", "e"] + [f"{k}{h}" for h in HS for k in ("r", "kd", "xmin", "rsc")]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    return T.drop(columns=["random"]).join(a)


def bind(T, h):
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"] = T[f"r{h}"], T[f"kd{h}"], T[f"xmin{h}"], T[f"rsc{h}"]
    T["r_u"] = 2 * T["r"]                     # R in 0.25-dATR units
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    out, names = {}, iter("abcdefgh")
    for s in (0.15, 0.25):
        for lm in (0.10, 0.20):
            for h in HS:
                out["17" + next(names)] = dict(s=s, lmin=lm, h=h, label=f"S{s:.2f}-L{lm:.2f}-TX{h}")
    return out


def select(S, cfg, cap=DAY_CAP):
    S = bind(S, cfg["h"])
    m = (S.smove >= cfg["s"]) & (S.lag >= cfg["lmin"]) & S.r.notna()
    s = S[m].sort_values(["symbol", "date", "tod", "side"], kind="mergesort")
    keep = []
    for _, g in s.groupby(["symbol", "date"], sort=False):
        n, free_at = 0, -1
        for i, t, x in zip(g.index, m2(g.tod.to_numpy()), g.xmin.to_numpy()):
            if n >= 2:
                break
            if t >= free_at:
                keep.append(i); n += 1; free_at = x + 30
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    return s


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar in 10:15-15:00; same exit."""
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(1015), m2(1500) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    return bind(walk(R, random=True), cfg["h"])


def rand_block(t, cfg):
    t = t.reset_index(drop=True)
    Rc = random_control(t, cfg)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr = t.r.to_numpy()
    o = {"random_avg_r": round(float(Rc.r[ok].mean()), 4),
         "signal_minus_random": round(float(tr[ok].mean() - Rc.r[ok].mean()), 4), "random_n": int(ok.sum())}
    for nm, sg in (("long", 1), ("short", -1)):
        k = ok & (t.side.to_numpy() == sg)
        if k.any():
            o[f"random_avg_r_{nm}"] = round(float(Rc.r[k].mean()), 4)
            o[f"signal_minus_random_{nm}"] = round(float(tr[k].mean() - Rc.r[k].mean()), 4)
    return o


def extra(t):
    return {"avg_r_0p25datr_units": round(float(t.r_u.mean()), 4) if len(t) else None,
            "n_sectors_traded": int(t.sec.nunique()) if len(t) else 0,
            "top_sectors": {k: int(v) for k, v in t.sec.value_counts().head(6).items()}}


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "secmap":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        B11.sector_map(W, half)
        print(pd.read_parquet(W / f"secmap_{half}.parquet").sec.value_counts().head(25))
    elif stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days, nf, cov = [], [], 0, {}
        with Pool(2) as p:
            for m, s, d, k, c in p.imap_unordered(month_job, [(m, str(W)) for m in half_months(half)]):
                print(m, len(s), int((s.side > 0).sum()), int((s.side < 0).sum()), "non-ETB", k, "sector cover",
                      round(c, 3), flush=True)
                sigs.append(s); days += d; nf += k; cov[m] = round(c, 3)
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"meta_{half}.json").write_text(json.dumps({"non_etb_short_bars": nf, "sector_cover": cov}))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r30.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = stats(t, n)
            o.update(B14.sub_halves(t)); o.update(extra(t))
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"), "L", o["long"].get("avg_r"),
                  o["long"].get("trades"), "S", o["short"].get("avg_r"), o["short"].get("trades"), flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-17 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "fit": res[pick], "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "configs_counted_this_candidate": 9, "configs_note": "8 grid + 1 bias diagnostic (PLAN sec. 4)",
              "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig))
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, fs["cfg"], cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = select(S, cfg)
        o = stats(t, n)
        o.update(extra(t))
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, cfg, cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
        fit = fs["fit"]
        tierA = (o["avg_r"] > 0 and (o["avg_r_wo_best_day"] or -1) > 0 and fit["avg_r"] > 0
                 and o["trades_per_session"] >= 2.0)
        beats = (tierA and o["avg_r"] > 0.0836 and o["avg_r_wo_best_day"] > 0.0734 and o["total_r_per_session"] > 0
                 and o["worst_day_per_trade_session"] >= -2.152 and (o["t_day_clustered"] or 0) >= z)
        tierB = fit["avg_r"] > 0 and o["avg_r"] > -0.02
        o["t_bar"] = round(z, 3)
        o["tier"] = "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL"))
        o["pick"] = fs["pick"]
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_once.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
        o2 = rand_block(t, cfg)
        (HERE / "check_random.json").write_text(json.dumps(o2, indent=1, default=float))
        print(o2)
    elif stage == "plateau":
        assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = stats(t, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                                "total_r", "t_day_clustered", "worst_day_per_trade_session",
                                                "first_half_avg_r", "second_half_avg_r", "avg_r_ex_0403_0409")}
            res[name]["long_avg_r"] = o["long"].get("avg_r"); res[name]["long_n"] = o["long"].get("trades")
            res[name]["short_avg_r"] = o["short"].get("avg_r"); res[name]["short_n"] = o["short"].get("trades")
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
