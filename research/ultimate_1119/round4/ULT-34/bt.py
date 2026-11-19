"""ULT-34 NO-NEWS REVERSAL backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-34", 5, 6). Reuses round4/ULT-30/bt.py
(which reuses ULT-28's 1-minute walk_job and the ULT-23 stats) unchanged: walk, cost_R (LR8, borrow), bind, the
random control and short_stats. New code: the no-news event columns, the signal superset, the grid, the selection.

Events: research/history2y daily closes (lib.daily(): locked rows removed) -> r1 = close(d-1)/close(d-2) - 1 with d-2,
d-1 consecutive NYSE sessions in the data (so a look-back into the locked block is dropped, never filled; first March
session 2025-03-05) -> no scheduled report (round4/data/earnings_yf.parquet, any session; never the _lockedblock file)
with reaction position in d-5..d+1; symbol covered by the calendar or an ETF; no leveraged / inverse / vol funds.
Built by the LIVE module's nonews_events(). e_k = |r1| / atr_d%, atr_d% = 100 x frame atr_d (ATR14 of bars < d) /
close(d-1). Side = -sign(r1).
Signals: lab frames + context (spy_fo); features / rule from the LIVE module (modules/ULT-34.py). Superset per half:
window 10:00-13:00, e_k >= 2, rule with F = V (the VO flag s x fromOpen >= 0 stored), both sides, shorts easy-to-borrow
by data/universe.csv (today's flag). Grid configs are sub-filters (K, F) plus an exit.
Chassis: entry at the OPEN of the 1-minute bar starting at the decision-bar close (LR8 entry cost); exits walked on
1-minute bars (stop first; gap-through at the worse of open/stop; target at the limit, no exit cost; +2c on stops;
time exit 45 min or 15:49). T = t1s1 (u = 0.25 x atr_d), X = TX-45 with a 2u catastrophic stop (R per 2u).
Shorts pay 1.2 bp of entry notional borrow (3 bp under $20); no earnings-window surcharge (no event is near earnings).
One lot per symbol; refire >= 30 min after the exit; max 2 per symbol-session; day cap 30 (time, ADV20 desc).
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

_s = importlib.util.spec_from_file_location("ult30bt", HERE.parent / "ULT-30" / "bt.py")
B30 = importlib.util.module_from_spec(_s)
sys.modules["ult30bt"] = B30
_s.loader.exec_module(B30)
B28, B23 = B30.B28, B30.B23
stats, sub_halves, no_locked, m2, hhmm, sha = B23.stats, B23.sub_halves, B23.no_locked, B23.m2, B23.hhmm, B23.sha
DATA, EARN, CACHE = B28.DATA, B28.EARN, B28.CACHE
half_months, etb_set = B28.half_months, B28.etb_set

MOD = HERE.parents[1] / "modules" / "ULT-34.py"
N_CUM = 996
DAY_CAP = 30
WINDOW = (1000, 1300)
B30.WINDOW = WINDOW            # the random control draws bars inside this candidate's window
K_MIN = 2.0


def load_mod(name="ult34"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def event_table(mod):
    import research.history2y.lib as lib
    lib.DATA = DATA
    d = lib.daily()[["symbol", "date", "close"]].copy()
    d["date"] = d["date"].astype(str)
    no_locked(d.date.unique())
    e = pd.read_parquet(EARN)
    ed = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    e = e[(ed >= "2024-08-01") & (ed <= "2026-12-31")]
    no_locked(pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d").unique())
    sess = mod.sessions("2024-08-01", "2026-12-31")
    ev = mod.nonews_events(d, e, sess)
    ev = ev[~ev.d.between(*B23.LOCK)].reset_index(drop=True)      # event session itself in the block: dropped
    no_locked(ev.d.unique())
    return ev


# ---------------------------------------------------------------- stage 1: signal superset
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    ev = event_table(mod)
    ev = ev[ev.d.str[:7] == month]
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "vwapDistPct", "fromOpen", "rsi5"]
    f = lib.load_month(month, columns=cols, context=True)
    f = f[[c for c in f.columns if not (c.startswith("win_") or c.startswith("r_long") or c.startswith("r_short")
                                        or "heat" in c.lower())]].copy()
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    k = f["symbol"] + "|" + f["date"]
    ek = ev.symbol + "|" + ev.d
    r1 = k.map(dict(zip(ek, ev.r1))).astype(float).to_numpy()
    pc = k.map(dict(zip(ek, ev.prev_close))).astype(float).to_numpy()
    okm = dict(zip(ek, (~ev.news) & ev.covered & (~ev.lev)))
    newsm = dict(zip(ek, ev.news))
    ok = k.map(okm).fillna(False).astype(bool).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = 100 * f["atr_d"].to_numpy(float) / pc
        kk = np.abs(r1) / atrp
    f["e_ok"], f["e_r1"], f["e_k"] = ok, r1, kk
    r = mod.features(f)
    tod = r["tod"]
    win = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    etb = f["symbol"].isin(etb_set()).to_numpy()
    out = []
    for sgn in (1, -1):
        mk = mod.signal(r, sgn, K_MIN, "V") & win
        if sgn < 0:
            mk &= etb
        s = f.loc[mk, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "e_r1", "e_k"]].copy()
        s["side"] = sgn
        s["vo"] = (sgn * r["fo"][mk] >= 0)
        s["evt"] = np.int8(0)
        s["cost_r"] = r["cost_r"][mk]
        out.append(s)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    # point-in-time event counts (no outcomes): names per session at 10:00 passing intake-free event tests
    d0 = f[f.tod == 1000].copy()
    q = d0.e_ok & (d0.e_k >= 2) & (d0.adv20 >= 50e6)
    n2 = d0[q].groupby("date").size().to_dict()
    n3 = d0[q & (d0.e_k >= 3)].groupby("date").size().to_dict()
    # how many K2 extreme moves were dropped for news (the reaction-day set the candidate deliberately avoids)
    nw = k[(f.tod == 1000).to_numpy()].map(newsm).fillna(False).astype(bool).to_numpy()
    qn = (d0.e_k >= 2).to_numpy() & (d0.adv20 >= 50e6).to_numpy() & nw
    nn = int(qn.sum())
    return month, pd.concat(out, ignore_index=True), days, n2, n3, nn


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    """Grid (8): K {2, 3} x F {V, VO} x exit {t1s1 cap45, TX-45}; names 34a..34h in the order K, F, exit."""
    out, names = {}, iter("abcdefgh")
    for kk in (2.0, 3.0):
        for f in ("V", "VO"):
            for ex, key, lab in (("T", "25T", "t1s1cap45"), ("X", "25X", "TX45")):
                out["34" + next(names)] = dict(k=kk, f=f, exit=ex, key=key, label=f"K{kk:g}-{f}-{lab}")
    return out


def select(S, cfg, cap=DAY_CAP):
    S = B30.bind(S, cfg["key"])
    m = (S.tod >= WINDOW[0]) & (S.tod <= WINDOW[1]) & (S.e_k >= cfg["k"]) & S.r.notna()
    if cfg["f"] == "VO":
        m &= S.vo
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


def _b(x):
    return {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None}


def full_stats(t, n):
    o = stats(t, n)
    o.update(sub_halves(t))
    o["by_side"] = {nm: {k: v for k, v in stats(t[t.side == sg], n).items()
                         if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "total_r",
                                  "t_day_clustered", "avg_r_u025", "avg_r_ex_0403_0409")}
                    for nm, sg in (("long", 1), ("short", -1))}
    o["by_k"] = {"2_3": _b(t[t.e_k < 3]), "3_5": _b(t[(t.e_k >= 3) & (t.e_k < 5)]), "5_plus": _b(t[t.e_k >= 5])}
    sg = t.side * t.gap
    o["by_sgap"] = {"lt0": _b(t[sg < 0]), "0_1": _b(t[(sg >= 0) & (sg < 1)]), "1_plus": _b(t[sg >= 1])}
    o["by_entry_time"] = {"1000_1055": _b(t[t.tod < 1100]), "1100_1155": _b(t[(t.tod >= 1100) & (t.tod < 1200)]),
                          "1200_1300": _b(t[t.tod >= 1200])}
    return o


def short_stats(o):
    keys = ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r",
            "total_r_wo_best_day", "total_r_per_session", "worst_day_per_trade_session", "t_day_clustered",
            "avg_r_ex_0403_0409", "A_avg_r", "B_avg_r", "first_half_avg_r", "second_half_avg_r", "avg_r_u025")
    x = {k: o.get(k) for k in keys}
    x["long_avg_r"] = o["by_side"]["long"].get("avg_r")
    x["short_avg_r"] = o["by_side"]["short"].get("avg_r")
    return x


def load_half(work, half):
    S = pd.read_parquet(Path(work) / f"walked_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, days, n2, n3, nn = [], [], {}, {}, 0
        with Pool(2) as p:
            for m, s, d, a, b, c in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), "K2 names/session", round(sum(a.values()) / max(1, len(d)), 2),
                      "K3", round(sum(b.values()) / max(1, len(d)), 2), "K2 dropped for news", c, flush=True)
                sigs.append(s); days += d; n2.update(a); n3.update(b); nn += c
        S = pd.concat(sigs, ignore_index=True)
        S["date"] = S["date"].astype(str)
        no_locked(S.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
        (W / f"meta_{half}.json").write_text(json.dumps({
            "n_days": len(days), "k2_names_per_session": sum(n2.values()) / len(days),
            "k3_names_per_session": sum(n3.values()) / len(days), "k2_dropped_for_news_total": nn}))
        print(json.loads((W / f"meta_{half}.json").read_text()))
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        t0 = time.time()
        T = B30.walk(S)
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
                  o.get("avg_r_ex_0403_0409"), flush=True)
        elig = {k: v for k, v in res.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else res
        pick = max(pool, key=lambda k: (pool[k].get("total_r_wo_best_day", -1e9), -list(res).index(k)))
        pick_total = max(pool, key=lambda k: (pool[k].get("total_r", -1e9), -list(res).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-34 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick, "cfg": res[pick]["cfg"],
              "eligible_2_per_session": sorted(elig), "any_eligible": bool(elig),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "pick_by_plain_total_r": pick_total, "fit": res[pick], "sha256_bt": sha(__file__),
              "sha256_module_at_freeze": sha(MOD), "sha256_earnings": sha(EARN),
              "sha256_ult30_bt": sha(HERE.parent / "ULT-30" / "bt.py"),
              "sha256_ult28_bt": sha(HERE.parent / "ULT-28" / "bt.py"), "configs_counted_this_candidate": 9,
              "configs_note": "8 grid + 1 bias diagnostic (PLAN sec. 4)", "check_informed": "NO",
              "needs_owner_blackout_exception": False, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, res[pick]["cfg"]["label"], "eligible:", sorted(elig), "plain-total pick:", pick_total)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit")
        t = select(S, fs["cfg"])
        o = B30.rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = short_stats(full_stats(select(S, fs["cfg"], cap=0), n))
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
        o.update(B30.rand_block(t, cfg))
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
        t[["symbol", "date", "tod", "side", "gap", "e_r1", "e_k", "r", "r_u", "kd", "hold"]].to_csv(
            HERE / "check_trades.csv.gz", index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        S, n = load_half(W, "check")
        res = {}
        for name, cfg in configs().items():
            res[name] = short_stats(full_stats(select(S, cfg), n))
            res[name]["label"] = cfg["label"]
            print(name, cfg["label"], res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
