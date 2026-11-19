"""ULT-18 XS-MOMREV backtest (ultimate_1119 round2/PLAN.md sec. 1-2, 3 "ULT-18", 5, 6).

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo) + the
point-in-time sector map / sector-ETF fromOpen of ULT-11 (round2/ULT-11/bt.py sector_map + month_frame, reused: sector =
argmax corr of prior <= 60 non-locked daily returns, min 20; beta OLS clipped [0.3, 3]; fit map from rows <= 2025-09-30
only). Keys and eligibility from the LIVE module (modules/ULT-18.py features(); the book from select_book()).
Superset per half: at 11:00 / 13:00 / 14:00, per key (K1, K2) and side, the DEPTH highest and DEPTH lowest eligible names
(DEPTH 40 >= N 10 + 2N blocked + N used on the other side, so the full-universe rank is reproduced exactly), plus 10
random eligible names per side and moment (same-moment random-names control). Each walked once on 1-minute bars.
Chassis (round 2): entry = OPEN of the 1-minute bar starting at the decision-bar close (LR8 entry cost on it); TX45 = time
exit at the close of minute entry+44 (flat 15:50) with a catastrophic stop 2u beyond the DECISION close (u = 0.25 x
prior-day daily ATR, as the live GEOM "S" stop_price), stop gap-through at the worse of open/stop; R per 2u (actual
risk; R in 0.25-dATR units = 2x). Costs LR8 (entry (1c+1bp) x tod mult; exit 1c+1bp; +2c on stops) + 1.2 bp borrow on
every short; shorts only easy_to_borrow (data/universe.csv, today's flag). One lot per symbol; refire >= 30 min after the
exit; max 2 per symbol-session (a blocked name is replaced by the next eligible one, as an excluded one); day cap 6N.
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ; python bt.py WORK fit|fitrandom|check|plateau
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
MOD = ULT / "modules" / "ULT-18.py"
N_CUM = 774
BORROW = 1.2e-4
DEPTH = 40
NRND = 10
TIMES = (1100, 1300, 1400)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_mod():
    return _load(MOD, "ult18")


B11 = _load(HERE.parent / "ULT-11" / "bt.py", "b11")        # sector_map, month_frame, guard_cols (reused)
B14 = _load(HERE.parent / "ULT-14" / "bt.py", "b14")        # stats, sub_halves (reused)


def no_locked(dates):
    s = pd.Series([str(x)[:10] for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def etb_set():
    u = pd.read_csv(ROOT / "data" / "universe.csv")
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def hhmm(mins):
    mins = np.asarray(mins, int)
    return (mins // 60) * 100 + mins % 60


# ---------------------------------------------------------------- stage 1: superset
def month_job(args):
    month, work = args
    mod = load_mod()
    src = MOD.read_text()
    assert not any(f'"{c}' in src for c in ("win_", "r_long", "r_short", "heat", "Heat")), "forbidden column in module"
    f = B11.guard_cols(B11.month_frame(month, work))
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    no_locked(f["date"].unique())
    F = mod.features(f)
    etb = f["symbol"].isin(etb_set()).to_numpy()
    okS_all = F["ok_short"].copy()
    F["ok_short"] = F["ok_short"] & etb
    sel = F["ok_long"] | F["ok_short"]
    X = f.loc[sel, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "rsi5", "spy_fo", "sec", "sec_beta",
                    "sec_fo"]].copy()
    for k in ("k1", "k2", "cost_r", "ok_long", "ok_short", "spy_r30"):
        X[k] = F[k][sel]
    rng = np.random.default_rng(int(month.replace("-", "")))
    rows, mom = [], []
    for (d, t), g in X.groupby(["date", "tod"], sort=True):
        keep = {}
        info = {"date": d, "tod": int(t), "n_long": int(g.ok_long.sum()), "n_short": int(g.ok_short.sum()),
                "n_k2_missing": int((~np.isfinite(g.k2)).sum())}
        mom.append(info)
        for side in ("long", "short"):
            e = g[g[f"ok_{side}"]]
            for key in ("k1", "k2"):
                ee = e[np.isfinite(e[key])]
                o = ee.sort_values([key, "adv20"], ascending=[False, False])
                for i in list(o.index[:DEPTH]) + list(o.index[-DEPTH:]):
                    keep.setdefault((i, side), 0)
            perm = rng.permutation(e.index.to_numpy())[:NRND]
            for r, i in enumerate(perm):
                keep[(i, side)] = r + 1          # random-names control rank (1..NRND)
        if keep:
            ii = [i for i, _ in keep]
            s = X.loc[ii].copy()
            s["side"] = [1 if sd == "long" else -1 for _, sd in keep]
            s["rnd"] = list(keep.values())
            rows.append(s)
    S = pd.concat(rows, ignore_index=True) if rows else X.iloc[:0]
    import research.history2y.lib as lib
    lib.DATA = DATA
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, S, pd.DataFrame(mom), days, int((okS_all & ~etb).sum())


# ---------------------------------------------------------------- stage 2: 1-minute walk (TX45)
def walk_job(args):
    sym, T = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    dmin = pd.Timestamp(min(T.date), tz=tz)
    dmax = pd.Timestamp(max(T.date), tz=tz) + pd.Timedelta(days=1)
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= dmin) & (fld < dmax)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hm_all = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        out = None
        if ix is not None:
            hm = hm_all[ix]
            j0 = np.searchsorted(hm, r.tod)
            ok = j0 < len(ix) and m2(hm[j0]) - m2(r.tod) <= 4 and hm[j0] < 1550
            dclose = r.close
            if ok and r.random_time:
                if j0 == 0 or m2(hm[j0 - 1]) < m2(r.tod) - 5:
                    ok = False
                else:
                    dclose = Cc[ix[j0 - 1]]
            if ok:
                s, u = int(r.side), 0.25 * r.atr_d
                e = O[ix[j0]]
                stop = dclose - s * 2 * u
                tend = min(int(hhmm(m2(hm[j0]) + 44)), 1549)
                px, kd, xt = None, 0, None
                for q in ix[j0:]:
                    if hm_all[q] > tend:
                        break
                    if (s > 0 and Lo[q] <= stop) or (s < 0 and Hh[q] >= stop):
                        px, kd, xt = (min(O[q], stop) if s > 0 else max(O[q], stop)), 1, hm_all[q]
                        break
                    px, xt = Cc[q], hm_all[q]
                if px is not None:
                    out = (e, dclose, px, kd, int(hhmm(m2(xt) + 1)))
        res.append((r.Index,) + (out if out else (np.nan,) * 5))
    return res


def cost_R(side, tod, e, px, kd, u, borrow=True):
    """After-cost R per u (0.25 dATR)."""
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xc = 0.01 + px * 1e-4 + np.where(kd == 1, 0.02, 0.0)
    bf = np.where((side < 0) & borrow, BORROW * e, 0.0)
    return (side * (px - e) - ec - xc - bf) / u


def walk(T, random_time=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random_time"] = random_time
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "e", "dclose", "px", "kd", "xt"]).set_index("i")
    T = T.drop(columns=["random_time"]).join(a)
    u = 0.25 * T.atr_d.to_numpy()
    sd, tod = T.side.to_numpy(), T.tod.to_numpy()
    T["r_u"] = cost_R(sd, tod, T.e.to_numpy(), T.px.to_numpy(), T.kd.to_numpy(), u)
    T["r"] = T["r_u"] / 2.0                                          # R per 2u = actual risk
    T["r_sigclose"] = cost_R(sd, tod, T.dclose.to_numpy(), T.px.to_numpy(), T.kd.to_numpy(), u, borrow=False) / 2.0
    T["xmin"] = np.where(T.xt.notna(), m2(T.xt.fillna(0)), np.nan)
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + book
def configs():
    out, names = {}, iter("abcdefgh")
    for key in ("k1", "k2"):
        for dr in ("MOM", "REV"):
            for n in (5, 10):
                out["18" + next(names)] = dict(key=key, direction=dr, n=n, label=f"{key.upper()}-{dr}-N{n}-TX45")
    return out


def select(S, cfg, mod, cap=True):
    """The book, moment by moment (11:00 -> 13:00 -> 14:00), with the chassis' one-lot / refire-30 / max-2 blocks.
    Rows whose 1-minute walk failed (no path) are selected (they used the slot) but carry r = NaN."""
    key, dr, n = cfg["key"], cfg["direction"], cfg["n"]
    cand = S[S.rnd >= 0]
    keep = []
    for d, gd in cand.groupby("date", sort=True):
        free_at, cnt = {}, {}
        for t in TIMES:
            g = gd[gd.tod == t]
            if not len(g):
                continue
            tm = int(m2(t))
            blocked = {s for s, fa in free_at.items() if fa > tm} | {s for s, c in cnt.items() if c >= 2}
            xs = g.groupby("symbol", sort=False).agg(k1=("k1", "first"), k2=("k2", "first"), adv20=("adv20", "first"))
            sides = g.groupby(["symbol", "side"]).size().unstack(fill_value=0)
            xs["ok_long"] = sides.get(1, pd.Series(0, index=sides.index)).reindex(xs.index).fillna(0).to_numpy() > 0
            xs["ok_short"] = sides.get(-1, pd.Series(0, index=sides.index)).reindex(xs.index).fillna(0).to_numpy() > 0
            xs = xs.reset_index()
            picks, _ = mod.select_book(xs, key, dr, n, blocked)
            assert len(picks) <= 2 * n
            gi = g.set_index(["symbol", "side"])
            for sym, side in picks:
                row = gi.loc[(sym, 1 if side == "long" else -1)]
                idx = int(row["_i"]) if np.ndim(row["_i"]) == 0 else int(row["_i"].iloc[0])
                keep.append(idx)
                x = S.at[idx, "xmin"]
                free_at[sym] = (x if np.isfinite(x) else tm + 45) + 30
                cnt[sym] = cnt.get(sym, 0) + 1
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        assert s.groupby("date").size().max() <= 6 * n, "day cap 6N exceeded"
    return s


def rnd_names(S, cfg):
    """Same-moment random-names control: per date, moment and side, the first N random eligible names (no blocking)."""
    return S[(S.rnd >= 1) & (S.rnd <= cfg["n"])]


def stats(t, n):
    t = t.copy()
    o = B14.stats(t, n)
    x = t[t.r.notna()]
    o["avg_r_u"] = round(float(x.r_u.mean()), 4) if len(x) else None
    o["no_path"] = int(t.r.isna().sum())
    return o


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    S["_i"] = S.index
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


def controls(S, t, cfg):
    o = {}
    R = rnd_names(S, cfg)
    R = R[R.r.notna()]
    o["random_names_avg_r"] = round(float(R.r.mean()), 4)
    o["random_names_n"] = int(len(R))
    o["signal_minus_random_names"] = round(float(t.r.mean() - R.r.mean()), 4)
    for nm, sg in (("long", 1), ("short", -1)):
        o[f"random_names_avg_r_{nm}"] = round(float(R.r[R.side == sg].mean()), 4)
        o[f"signal_minus_random_names_{nm}"] = round(float(t.r[t.side == sg].mean() - R.r[R.side == sg].mean()), 4)
    # same-name random time: same symbol-sessions and sides, a random 5-min decision bar 10:00-15:00, same exit
    rng = np.random.default_rng(1119)
    slots = np.arange(m2(1000), m2(1500) + 1, 5)
    Q = t[["symbol", "date", "atr_d", "close", "tod", "side", "adv20"]].copy()
    Q["tod"] = hhmm(rng.choice(slots, size=len(Q)))
    W = walk(Q, random_time=True)
    ok = W.r.notna().to_numpy() & t.r.notna().to_numpy()
    o["random_time_avg_r"] = round(float(W.r[ok].mean()), 4)
    o["signal_minus_random_time"] = round(float(t.r.to_numpy()[ok].mean() - W.r[ok].mean()), 4)
    o["random_time_n"] = int(ok.sum())
    return o


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        B11.sector_map(W, half)
        sigs, moms, days, nf = [], [], [], 0
        with Pool(2) as p:
            for m, s, mo, d, k in p.imap_unordered(month_job, [(m, str(W)) for m in half_months(half)]):
                print(m, len(s), "moments", len(mo), "eligible long/short per moment",
                      round(mo.n_long.mean(), 1), round(mo.n_short.mean(), 1), "non-ETB short rows", k, flush=True)
                sigs.append(s); moms.append(mo); days += d; nf += k
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.concat(moms).to_parquet(W / f"moments_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"nonetb_{half}.txt").write_text(str(nf))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        mod = load_mod()
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg, mod)
            o = stats(t, n)
            o.update(B14.sub_halves(t[t.r.notna()]))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o["avg_r"], o["avg_r_wo_best_day"], o["total_r"],
                  o["total_r_wo_best_day"], o.get("A_avg_r"), o.get("B_avg_r"), "L", o["long"].get("avg_r"),
                  "S", o["short"].get("avg_r"), "t", o["t_day_clustered"], flush=True)
        grid = dict(res)
        elig = {k: v for k, v in grid.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else grid
        pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(grid).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-18 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": grid[pick]["cfg"],
              "eligible_2_per_session": sorted(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "fit": grid[pick], "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "configs_counted_this_candidate": 9, "configs_note": "8 grid + 1 bias diagnostic (PLAN sec. 4)",
              "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, grid[pick]["cfg"]["label"], "eligible:", sorted(elig))
    elif stage == "fitrandom":
        mod = load_mod()
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"], mod)
        t = t[t.r.notna()]
        o = controls(S, t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "check":
        mod = load_mod()
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = select(S, cfg, mod)
        o = stats(t, n)
        tt = t[t.r.notna()]
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(tt.r_sigclose.mean()), 4)
        o.update(controls(S, tt, cfg))
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
    elif stage == "plateau":
        assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
        mod = load_mod()
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg, mod)
            o = stats(t, n)
            res[name] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                                "total_r", "t_day_clustered", "worst_day_per_trade_session",
                                                "first_half_avg_r", "second_half_avg_r")}
            res[name]["long_avg_r"] = o["long"].get("avg_r"); res[name]["short_avg_r"] = o["short"].get("avg_r")
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
