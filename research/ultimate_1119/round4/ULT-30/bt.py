"""ULT-30 EARN-DAY2 backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-30", 5, 6). Reuses round4/ULT-28/bt.py
(1-minute walk walk_job, stats / sub-halves / no_locked from round3/ULT-23) unchanged; only the event table, the
signal superset, the grid and the cost wrapper are new.

Events: round4/data/earnings_yf.parquet (never the _lockedblock sibling) -> RD table -> RD+1 table with
REACT = close(RD)/close(RD-1) - 1 minus SPY's, from research/history2y daily bars (lib.daily(): locked rows removed);
events with RD-1, RD or RD+1 in the locked block are dropped (never filled). Built by the LIVE module's day2_events().
Signals: lab frames + context (spy_fo); features and side rule from the LIVE module (modules/ULT-30.py) with frame
columns e_d2 / e_react. Superset per half: window 09:50-12:30, |REACT| >= 4, side = sign(REACT), the day-2 rule, both
sides (shorts easy-to-borrow by data/universe.csv, today's flag) on (a) RD+1 rows (evt = 1) and (b) the non-earnings
twin (evt = 0: names covered by the earnings table, no raw report RD position in [d-2, d+5], REACT = the previous
session's close-to-close move vs SPY). Grid configs are sub-filters (evt 1, T, side) plus an exit.
Chassis (round 3/4): entry at the OPEN of the 1-minute bar starting at the decision-bar close (LR8 entry cost);
brackets around the decision close walked on 1-minute bars (stop first, then target; stop gap-through at the worse of
open/stop; target at the limit, no exit cost; +2c on stops; time exit 45 min or the 15:49 minute).
T = t1s1 (+1u / -1u), R per u; X = TX-45 with a 2u catastrophic stop, R per 2u. u = 0.25 x atr_d.
Costs LR8; borrow on shorts 5 bp of entry notional on RD+1 (earnings window; 8 bp under $20), 1.2 / 3 bp on twin rows.
The reaction-day x1.5 first-hour surcharge is PLAN-scoped to RD bars, so it is not in the main figure; a sensitivity
column applies it to RD+1 bars before 10:30 as well (reported).
One lot per symbol; refire >= 30 min after the exit; max 2 per symbol-session; day cap 30.
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ; python bt.py WORK fit|fitrandom|check|plateau
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parents[1] / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

_s = importlib.util.spec_from_file_location("ult28bt", HERE.parent / "ULT-28" / "bt.py")
B28 = importlib.util.module_from_spec(_s)
sys.modules["ult28bt"] = B28
_s.loader.exec_module(B28)
B23 = B28.B23
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha
walk_job, exit_keys, EXITS, MS, CACHE, DATA, EARN = (B28.walk_job, B28.exit_keys, B28.EXITS, B28.MS, B28.CACHE,
                                                       B28.DATA, B28.EARN)
half_months, etb_set = B28.half_months, B28.etb_set

MOD = HERE.parents[1] / "modules" / "ULT-30.py"
N_CUM = 996
DAY_CAP = 30
WINDOW = (950, 1230)
SURCH_T = 1030
T_MIN = 4.0


def load_mod(name="ult30"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def daily_closes():
    import research.history2y.lib as lib
    lib.DATA = DATA
    d = lib.daily()[["symbol", "date", "close"]].copy()
    d["date"] = d["date"].astype(str)
    d["symbol"] = d["symbol"].astype(str)
    no_locked(d.date.unique())
    return d


def events():
    """RD+1 table on the NYSE calendar 2024-08-01..2026-12-31; events touching the locked block dropped."""
    mod = load_mod()
    e = pd.read_parquet(EARN)
    d = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    e = e[(d >= "2024-08-01") & (d <= "2026-12-31")]
    no_locked(pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d").unique())
    sess = mod.sessions("2024-08-01", "2026-12-31")
    dl = daily_closes()
    ev = mod.day2_events(e, sess, dl)
    L = B23.LOCK
    bad = ev.rdm1.between(*L) | ev.rd.between(*L) | ev.d2.between(*L)
    ev = ev[~bad].reset_index(drop=True)
    for c in ("rdm1", "rd", "d2"):
        no_locked(ev[c].unique())
    allrd = e.copy()
    allrd["report_date"] = d[allrd.index]
    arr = np.array(sess)
    allrd["rd_i"] = np.where(allrd.session.to_numpy() == "amc",
                             np.searchsorted(arr, allrd.report_date.to_numpy(), "right"),
                             np.searchsorted(arr, allrd.report_date.to_numpy(), "left"))
    return ev, allrd[["symbol", "rd_i"]], sess, dl


def prev_react(dl, sess):
    """Twin REACT for (symbol, d): close(d-1)/close(d-2) - 1 minus SPY's, only when d-2, d-1 are consecutive sessions
    in the data (no fill across the locked gap). Returns dict 'sym|d' -> %."""
    sidx = {x: i for i, x in enumerate(sess)}
    dl = dl[dl.date.isin(sidx)].copy()
    dl["i"] = dl.date.map(sidx)
    dl = dl.sort_values(["symbol", "i"])
    prv = dl.groupby("symbol").close.shift()
    pi = dl.groupby("symbol").i.shift()
    r = np.where(dl.i - pi == 1, dl.close / prv - 1, np.nan)
    dl["r"] = r
    spy = dict(zip(dl.loc[dl.symbol == "SPY", "i"], dl.loc[dl.symbol == "SPY", "r"]))
    dl["rel"] = (dl.r - dl.i.map(spy)) * 100
    arr = np.array(sess)
    nxt = dl.i + 1
    ok = nxt < len(arr)
    dl = dl[ok & dl.rel.notna()]
    return dict(zip(dl.symbol + "|" + arr[(dl.i + 1).to_numpy()], dl.rel))


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    ev, allrd, sess, dl = events()
    sidx = {d: i for i, d in enumerate(sess)}
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "vwapDistPct", "fromOpen", "rsi5"]
    f = lib.load_month(month, columns=cols, context=True)
    f = f[[c for c in f.columns if not (c.startswith("win_") or c.startswith("r_long") or c.startswith("r_short")
                                        or "heat" in c.lower())]].copy()
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    evm = ev[ev.d2.str[:7] == month]
    k = f["symbol"] + "|" + f["date"]
    emap = dict(zip(evm.symbol.astype(str) + "|" + evm.d2, evm.react))
    evt = k.isin(emap.keys()).to_numpy()
    covered = set(allrd.symbol.astype(str))
    di = f["date"].map(sidx).to_numpy()
    bad = set()
    for sym, ri in zip(allrd.symbol.astype(str), allrd.rd_i.to_numpy()):
        for dd in range(ri - 5, ri + 3):          # d in [RD-5, RD+2]  <=>  RD in [d-2, d+5]
            bad.add((sym, dd))
    twin = np.array([(s in covered) and ((s, d) not in bad) for s, d in zip(f["symbol"].to_numpy(), di)])
    pr = prev_react(dl, sess)
    react = np.where(evt, k.map(emap).astype(float).to_numpy(), k.map(pr).astype(float).to_numpy())
    f["e_d2"] = True
    f["e_react"] = react
    r = mod.features(f)
    tod = r["tod"]
    win = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    etb = f["symbol"].isin(etb_set()).to_numpy()
    out = []
    for sgn in (1, -1):
        mk = mod.signal(r, sgn, T_MIN, "both") & win & (evt | twin)
        if sgn < 0:
            mk &= etb
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "e_react"]].copy()
        s["side"] = sgn
        s["evt"] = evt[mk].astype(np.int8)
        s["cost_r"] = r["cost_r"][mk]
        out.append(s)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    d50 = f.loc[f.tod == 950, ["symbol", "date", "adv20", "e_react"]].assign(evt=evt[f.tod.to_numpy() == 950])
    nev = d50.groupby("date").evt.sum().to_dict()
    q = d50[d50.evt & (d50.adv20 >= 30e6)]
    nev4 = q[q.e_react.abs() >= 4].groupby("date").size().to_dict()
    return month, pd.concat(out, ignore_index=True), days, nev, nev4


# ---------------------------------------------------------------- stage 2: walk (ULT-28's walk_job) + costs
def borrow(side, e, evt):
    bp = np.where(evt > 0, np.where(e < 20, 8e-4, 5e-4), np.where(e < 20, 3e-4, 1.2e-4))
    return np.where(side < 0, bp * e, 0.0)


def cost_R(side, tod, e, px, kd, unit, evt, xt, fixes=True, sur=False):
    """fixes=False: the bias diagnostic (no borrow). sur=True: x1.5 first-hour surcharge on RD+1 rows (sensitivity)."""
    sur_e = np.where(sur & (evt > 0) & (np.asarray(tod) < SURCH_T), 1.5, 1.0)
    sur_x = np.where(sur & (evt > 0) & (np.nan_to_num(np.asarray(xt, float), nan=9999) < SURCH_T), 1.5, 1.0)
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod) * sur_e
    xc = (np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)) * sur_x
    bf = borrow(side, e, evt) if fixes else 0.0
    return (side * (px - e) - ec - xc - bf) / unit


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    cols = ["i", "e", "dclose"] + [f"{a}{k}" for k in exit_keys() for a in ("px", "kd", "xt")]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    tod, side, atr, evt = T.tod.to_numpy(), T.side.to_numpy(), T.atr_d.to_numpy(), T.evt.to_numpy()
    for k in exit_keys():
        m, g = int(k[:2]) / 100, k[2]
        unit = EXITS[g][1] * m * atr
        px, kd, xt = T["px" + k].to_numpy(), T["kd" + k].to_numpy(), T["xt" + k].to_numpy()
        e = T.e.to_numpy()
        T["r" + k] = cost_R(side, tod, e, px, kd, unit, evt, xt)
        T["ru" + k] = cost_R(side, tod, e, px, kd, 0.25 * atr, evt, xt)
        T["rsc" + k] = cost_R(side, tod, T.dclose.to_numpy(), px, kd, unit, evt, xt, fixes=False)
        T["rsur" + k] = cost_R(side, tod, e, px, kd, unit, evt, xt, sur=True)
        T["xmin" + k] = np.where(T["xt" + k].notna(), m2(T["xt" + k].fillna(0)), np.nan)
        T = T.drop(columns=["px" + k, "xt" + k])
    return T


def bind(T, k):
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"], T["r_u"], T["r_sur"] = (T["r" + k], T["kd" + k], T["xmin" + k],
                                                                         T["rsc" + k], T["ru" + k], T["rsur" + k])
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    """Grid (8): T {4, 8} x side {both, long} x exit {t1s1 cap45, TX-45}; names 30a..30h in the order T, side, exit."""
    out, names = {}, iter("abcdefgh")
    for t in (4.0, 8.0):
        for sd in ("both", "long"):
            for ex, key, lab in (("T", "25T", "t1s1cap45"), ("X", "25X", "TX45")):
                out["30" + next(names)] = dict(t=t, sides=sd, exit=ex, key=key, label=f"T{t:g}-{sd}-{lab}")
    return out


def select(S, cfg, cap=DAY_CAP, evt=1):
    S = bind(S, cfg["key"])
    m = ((S.evt == evt) & (S.tod >= WINDOW[0]) & (S.tod <= WINDOW[1]) & (S.side * S.e_react >= cfg["t"]) & S.r.notna())
    if cfg["sides"] == "long":
        m &= S.side > 0
    s = S[m].sort_values(["symbol", "date", "tod"], kind="mergesort")
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


SEASON = None


def _b(x):
    return {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}


def full_stats(t, n):
    o = stats(t, n)
    o.update(sub_halves(t))
    o["by_side"] = {nm: {k: v for k, v in stats(t[t.side == sg], n).items()
                         if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                  "t_day_clustered", "avg_r_u025", "avg_r_ex_0403_0409")}
                    for nm, sg in (("long", 1), ("short", -1))}
    sr, sg = t.side * t.e_react, t.side * t.gap
    o["by_react"] = {"4_8": _b(t[sr < 8]), "8_15": _b(t[(sr >= 8) & (sr < 15)]), "15_plus": _b(t[sr >= 15])}
    o["by_sgap"] = {"lt0": _b(t[sg < 0]), "0_2": _b(t[(sg >= 0) & (sg < 2)]), "2_plus": _b(t[sg >= 2])}
    o["by_entry_time"] = {"0950_1025": _b(t[t.tod < 1030]), "1030_1125": _b(t[(t.tod >= 1030) & (t.tod < 1130)]),
                          "1130_1230": _b(t[t.tod >= 1130])}
    o["surcharge_sensitivity_avg_r"] = round(float(t.r_sur.mean()), 4) if len(t) else None
    if SEASON is not None:
        ss = t.date.map(SEASON).fillna(False).astype(bool)
        o["season"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None,
                            "total_r": round(float(x.r.sum()), 2)} for nm, x in (("season", t[ss]), ("off", t[~ss]))}
    return o


def random_control(sel, cfg, seed=1119):
    rng = np.random.default_rng(seed)
    slots = np.arange(m2(WINDOW[0]), m2(WINDOW[1]) + 1, 5)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side", "evt"]].copy()
    R["tod"] = hhmm(rng.choice(slots, size=len(R)))
    return bind(walk(R, random=True), cfg["key"])


def rand_block(t, cfg):
    Rc = random_control(t, cfg)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr, rr = t.r.to_numpy()[ok], Rc.r.to_numpy()[ok]
    sd = t.side.to_numpy()[ok]
    o = {"random_avg_r": round(float(rr.mean()), 4), "signal_minus_random": round(float(tr.mean() - rr.mean()), 4),
         "random_n": int(ok.sum())}
    # day-clustered t of the random draw (same dates)
    dd = t.date.to_numpy()[ok]
    dev = pd.Series(rr - rr.mean()).groupby(dd).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(rr)
    o["random_t_day_clustered"] = round(float(rr.mean() / se), 2) if se > 0 else None
    for nm, sg in (("long", 1), ("short", -1)):
        q = sd == sg
        if q.any():
            o[f"random_avg_r_{nm}"] = round(float(rr[q].mean()), 4)
            o[f"signal_minus_random_{nm}"] = round(float(tr[q].mean() - rr[q].mean()), 4)
    return o


def short_stats(o):
    keys = ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r",
            "total_r_per_session", "worst_day_per_trade_session", "t_day_clustered", "avg_r_ex_0403_0409", "A_avg_r",
            "B_avg_r", "first_half_avg_r", "second_half_avg_r", "avg_r_u025", "surcharge_sensitivity_avg_r")
    x = {k: o.get(k) for k in keys}
    x["long_avg_r"] = o["by_side"]["long"].get("avg_r")
    x["short_avg_r"] = o["by_side"]["short"].get("avg_r")
    return x


def load_half(work, half):
    global SEASON
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    meta = json.loads((Path(work) / f"meta_{half}.json").read_text())
    SEASON = {d: meta["n_events"].get(d, 0) >= 5 for d in days}
    return S, len(days)


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days, nev, n4 = [], [], {}, {}
        with Pool(2) as p:
            for m, s, d, ne, ni in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), "evt rows", int(s.evt.sum()), "RD+1 names/session",
                      round(sum(ne.values()) / max(1, len(d)), 2), "intake |REACT|>=4 names/session",
                      round(sum(ni.values()) / max(1, len(d)), 2), flush=True)
                sigs.append(s); days += d
                nev.update({k: int(v) for k, v in ne.items()}); n4.update({k: int(v) for k, v in ni.items()})
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"meta_{half}.json").write_text(json.dumps({"n_days": len(days), "n_events": nev, "n_events_react4": n4,
                                                         "d2_names_per_session": sum(nev.values()) / len(days),
                                                         "react4_names_per_session": sum(n4.values()) / len(days)}))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = walk(S)
        T.to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(T), int(T.r25T.isna().sum()), "no path", round(time.time() - t0), "s")
    elif stage == "fit":
        S, n = load_half(W, "fit")
        res = {}
        for name, cfg in configs().items():
            t = select(S, cfg)
            o = full_stats(t, n)
            o["uncapped_trades"] = int(len(select(S, cfg, cap=0)))
            o["cfg"] = cfg
            res[name] = o
            print(name, cfg["label"], o["trades_per_session"], o.get("avg_r"), o.get("avg_r_wo_best_day"),
                  o.get("total_r"), o.get("total_r_wo_best_day"), o.get("A_avg_r"), o.get("B_avg_r"),
                  o["by_side"]["long"].get("avg_r"), o["by_side"]["short"].get("avg_r"), o.get("t_day_clustered"),
                  flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k].get("total_r_wo_best_day", -1e9), -list(res).index(k)))
        pick_total = max(pool, key=lambda k: (pool[k].get("total_r", -1e9), -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-30 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "any_eligible": bool(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "pick_by_plain_total_r": pick_total, "fit": res[pick], "sha256_bt": sha(__file__),
              "sha256_module_at_freeze": sha(MOD), "sha256_earnings": sha(EARN),
              "sha256_ult28_bt": sha(HERE.parent / "ULT-28" / "bt.py"), "configs_counted_this_candidate": 9,
              "configs_note": "8 grid + 1 bias diagnostic (PLAN sec. 4)", "check_informed": "PARTLY",
              "needs_owner_blackout_exception": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig), "plain-total pick:", pick_total)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, fs["cfg"], cap=0), n))
        o["twin_fit"] = short_stats(full_stats(select(S, fs["cfg"], evt=0), n))
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_once.json").exists(), "CHECK is scored once"
        S, n = load_half(W, "check")
        cfg = fs["cfg"]
        t = select(S, cfg)
        o = full_stats(t, n)
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, cfg, cap=0), n))
        o.update(rand_block(t, cfg))
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
        t[["symbol", "date", "tod", "side", "gap", "e_react", "r", "r_u", "kd", "hold"]].to_csv(
            HERE / "check_trades.csv.gz", index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            res[name] = short_stats(full_stats(select(S, cfg), n))
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        fs = json.loads((HERE / "fitsel.json").read_text())
        res["twin_check_" + fs["pick"]] = short_stats(full_stats(select(S, fs["cfg"], evt=0), n))
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
