"""Crypto round 3 (pre-registered in research/crypto_r3/PREREG.md; sha256 in PREREG.sha256).

    python research/crypto_r3/run_r3.py fit     # 9 daily-trend + 8 vol-regime configs on FIT -> fit_*.json/csv
    python research/crypto_r3/run_r3.py check   # all 17 scored ONCE on CHECK + benchmarks (needs the FIT files)
Clean signal bars: Amendment-1 bad-print filter, then traded minutes only (mcf/crypto/exec1m.clean_traded).
Daily trend = swing/daily (mcf/crypto/trend.py), NOT intraday. LOCKED is never read (loader clips at its start).
Educational only — not financial advice.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.crypto import data as D  # noqa: E402
from mcf.crypto import splits as S  # noqa: E402
from mcf.crypto import trend as TR  # noqa: E402
from mcf.crypto.backtest import summarize  # noqa: E402
from mcf.crypto.costs import CostModel  # noqa: E402
from mcf.crypto.exec1m import Minutes, Plan, clean_prints, clean_traded, run, to_min  # noqa: E402
from mcf.crypto.features import wilder  # noqa: E402

HERE = Path(__file__).parent
PAIRS = ("BTC", "ETH", "SOL")
SEED = 20261128
N_PRIOR = 1460
MIN_TRADES, MAX_SHARE = 60, 0.5
CHECK_T = 1.5                     # CHECK window on its third look (PREREG.md)
RAND_TREND, RAND_VOL = 200, 100
COSTS = CostModel()
MINS: dict = {}
DAY: dict = {}                    # pair -> daily indicator frame (common daily index)
HOUR: dict = {}                   # pair -> hourly frame (c, m, real, q99, q98, atr)

TREND = [TR.TrendRule(r, ma, draw_id=980 + 3 * i + j) for i, r in enumerate("ABC") for j, ma in enumerate((50, 100, 200))]
VOL = [dict(draw_id=989 + k, dir=d, p=p, hold_h=h) for k, (d, p, h) in
       enumerate([(d, p, h) for d in ("cont", "rev") for p in (0.99, 0.98) for h in (4, 24)])]
N_CUM = N_PRIOR + len(TREND) + len(VOL)
BAR = float(np.sqrt(2 * np.log(N_CUM)))


def load() -> None:
    t0 = time.time()
    idx = pd.date_range("2021-01-01", S.LOCKED_START, freq="D", tz="UTC", inclusive="left")
    for p in PAIRS:
        raw = D.load_bars(p)
        MINS[p] = Minutes.from_bars(clean_prints(raw))
        sig = clean_traded(raw)
        d = D.resample(sig, "1D", ffill=True)[["o", "h", "l", "c"]].reindex(idx).ffill()
        DAY[p] = TR.indicators(d)
        h = D.resample(sig, "60min", ffill=True)
        f = pd.DataFrame(index=h.index)
        f["c"] = h["c"]
        f["real"] = ~h["filled"].astype(bool) if "filled" in h else True
        f["m"] = np.log(h["c"] / h["c"].shift(1))
        am = f["m"].abs().where(f["real"])
        for q in (0.99, 0.98):
            f[f"q{int(q*100)}"] = am.rolling(720, min_periods=360).quantile(q).shift(1)
        pc = h["c"].shift(1)
        trr = pd.concat([h["h"] - h["l"], (h["h"] - pc).abs(), (h["l"] - pc).abs()], axis=1).max(axis=1)
        f["atr"] = wilder(trr, 14)
        HOUR[p] = f
    print(f"loaded in {time.time()-t0:.0f}s", flush=True)


# ------------------------------------------------------------------ daily trend
def _split_rows(split: str) -> np.ndarray:
    a, z = S.bounds(split)
    ix = DAY[PAIRS[0]].index
    return np.flatnonzero((ix >= a) & (ix < z))


def _dec(rows: np.ndarray) -> np.ndarray:
    return to_min(DAY[PAIRS[0]].index[rows]) + 1440            # decision = the day's close (next 00:00 UTC)


def _r_frame(tr: pd.DataFrame) -> pd.DataFrame:
    if tr.empty:
        return pd.DataFrame(columns=["day", "r", "cost_r", "gross_r", "pair"])
    unit = 3 * tr["atr_pct"]
    gross = tr["exit"] / tr["entry"] - 1
    return pd.DataFrame({"day": pd.to_datetime(tr["t_in"].astype(np.int64), unit="m", utc=True).dt.floor("D"),
                         "r": tr["net"] / unit, "gross_r": gross / unit,
                         "cost_r": (gross - tr["net"]) / unit, "pair": tr["pair"]})


def trend_run(rule: TR.TrendRule, split: str, mode: str | None = None, tier: int = 1, windows=None):
    rows = _split_rows(split)
    dec = _dec(rows)
    trades, eqs = [], []
    for p in PAIRS:
        f = DAY[p].iloc[rows]
        close = f["c"].to_numpy(np.float64)
        if windows is not None:
            en, ex = windows[p]
            mh = 0
        else:
            en, ex = TR.signals(rule, f)
            mh = rule.max_hold if rule.rule == "C" else 0
        tr = TR.simulate(p, dec, close, en, ex, MINS[p], COSTS, mode=mode or rule.entry, expiry=rule.expiry_min,
                         max_hold=mh, tier=tier, atr=f["atr"].to_numpy(np.float64))
        trades.append(tr)
        eqs.append(TR.sleeve_equity(tr, dec, close))
    tr = pd.concat(trades, ignore_index=True)
    eq = np.mean(eqs, axis=0)
    return tr, eq, eqs, len(dec)


def trend_summary(rule, split, mode=None, tier=1) -> dict:
    tr, eq, eqs, n_dec = trend_run(rule, split, mode, tier)
    sm = summarize(_r_frame(tr))
    m = TR.metrics(eq)
    expo = float((tr["k_out"] - tr["k_in"]).sum() / (3 * n_dec)) if len(tr) else 0.0
    out = {"draw_id": rule.draw_id, "label": rule.label(), **{f"pf_{k}": v for k, v in m.items()},
           "exposure": expo, **{k: sm[k] for k in ("n", "avg_r", "avg_r_wo_best", "best_day_share", "day_t",
                                                   "avg_cost_r", "avg_gross_r")},
           "avg_net_ret": float(tr["net"].mean()) if len(tr) else np.nan}
    for p, e in zip(PAIRS, eqs):
        pm = TR.metrics(e)
        out.update({f"{p}_total": pm["total"], f"{p}_sharpe": pm["sharpe"], f"{p}_maxdd": pm["maxdd"],
                    f"{p}_n": int((tr["pair"] == p).sum())})
    return out


def buy_hold(split: str) -> dict:
    rows = _split_rows(split)
    dec = _dec(rows)
    eqs = []
    out = {}
    for p in PAIRS:
        close = DAY[p]["c"].to_numpy(np.float64)[rows]
        tr = TR.simulate(p, dec, close, np.ones(len(dec), bool), np.zeros(len(dec), bool), MINS[p], COSTS,
                         mode="taker")
        e = TR.sleeve_equity(tr, dec, close)
        eqs.append(e)
        out.update({f"{p}_{k}": v for k, v in TR.metrics(e).items()})
    out.update({f"pf_{k}": v for k, v in TR.metrics(np.mean(eqs, axis=0)).items()})
    return out


def trend_random(args) -> dict:
    rule, split, seed = args
    tr, _, _, n_dec = trend_run(rule, split)
    rng = np.random.default_rng(seed)
    durs = {p: (tr.loc[tr["pair"] == p, "k_out"] - tr.loc[tr["pair"] == p, "k_in"]).tolist() for p in PAIRS}
    res = []
    for _ in range(RAND_TREND):
        w = {p: TR.random_windows(rng, durs[p], n_dec) for p in PAIRS}
        rt, req, _, _ = trend_run(rule, split, windows=w)
        m = TR.metrics(req)
        res.append((m["total"], m["sharpe"], m["maxdd"], _r_frame(rt)["r"].mean() if len(rt) else np.nan))
    a = np.array(res, float)
    return {"draw_id": rule.draw_id, "rand_total": a[:, 0], "rand_sharpe": a[:, 1], "rand_maxdd": a[:, 2],
            "rand_avg_r": a[:, 3]}


# ------------------------------------------------------------------ vol-regime intraday
def vol_trades(cfg: dict, split: str, rand_rng=None, counts=None) -> pd.DataFrame:
    a, z = S.bounds(split)
    am, zm = int(to_min(pd.DatetimeIndex([a]))[0]), int(to_min(pd.DatetimeIndex([z]))[0])
    plan = Plan(mode="maker", off_atr=0.0, expiry_min=60, stop_atr=3.0, min_stop_pct=0.03, target_r=None,
                hold_min=int(cfg["hold_h"] * 60))
    out = []
    for p in PAIRS:
        f = HOUR[p]
        dec = to_min(f.index) + 60
        sel = (dec >= am) & (dec < zm)
        g = f[sel]
        real = g["real"].to_numpy(bool)
        if rand_rng is None:
            m = g["m"].to_numpy()
            q = g[f"q{int(cfg['p']*100)}"].to_numpy()
            big = real & (np.abs(m) > q)
            sig = big & ((m > 0) if cfg["dir"] == "cont" else (m < 0))
        else:
            idx = np.flatnonzero(real & g["atr"].notna().to_numpy())
            k = min(counts.get(p, 0), len(idx))
            sig = np.zeros(len(g), bool)
            if k:
                sig[rand_rng.choice(idx, k, replace=False)] = True
        if not sig.any():
            continue
        tr, _, _ = run(p, MINS[p].slice(am, zm), dec[sel][sig], g["c"].to_numpy(np.float64)[sig],
                       g["atr"].to_numpy(np.float64)[sig], plan, COSTS)
        if len(tr):
            out.append(tr)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["day", "r", "cost_r", "gross_r",
                                                                              "pair"])


def vol_label(c) -> str:
    return f"1h top {100 - int(c['p'] * 100)}% |move| hour, {c['dir']} long, mk 60m, s3ATR>=3%, h{c['hold_h']}"


def vol_score(args) -> dict:
    cfg, split, seed = args
    tr = vol_trades(cfg, split)
    sm = summarize(tr)
    row = {"draw_id": cfg["draw_id"], "label": vol_label(cfg), **sm}
    if seed is not None and len(tr):
        rng = np.random.default_rng(seed)
        counts = tr.groupby("pair").size().to_dict()
        rb = np.array([vol_trades(cfg, split, rng, counts)["r"].mean() for _ in range(RAND_VOL)], float)
        row["rand_mean"] = float(np.nanmean(rb))
        row["rand_pct"] = float(np.nanmean(rb < sm["avg_r"]))
    for p in PAIRS:
        row[f"{p}_n"] = int((tr["pair"] == p).sum()) if len(tr) else 0
    return row


def eligible(r) -> bool:
    return bool(r["n"] >= MIN_TRADES and r["best_day_share"] < MAX_SHARE and r["avg_r_wo_best"] > 0
                and r["day_t"] >= BAR)


# ------------------------------------------------------------------ runs
def fit() -> None:
    load()
    rows = [trend_summary(r, "fit") for r in TREND]
    tdf = pd.DataFrame(rows)
    tdf["elig"] = tdf.apply(eligible, axis=1)
    tdf.to_csv(HERE / "fit_trend.csv", index=False, float_format="%.4f")
    with mp.get_context("fork").Pool(4) as pool:
        vrows = pool.map(vol_score, [(c, "fit", None) for c in VOL])
    vdf = pd.DataFrame(vrows)
    vdf["elig"] = vdf.apply(eligible, axis=1)
    vdf.to_csv(HERE / "fit_vol.csv", index=False, float_format="%.4f")
    stats = {"frozen_utc": pd.Timestamp.now(tz="UTC").isoformat(), "configs_r3": len(TREND) + len(VOL),
             "n_cum": N_CUM, "noise_bar": BAR, "eligible_trend": int(tdf.elig.sum()),
             "eligible_vol": int(vdf.elig.sum()), "buy_hold_fit": buy_hold("fit")}
    (HERE / "fit_stats.json").write_text(json.dumps(stats, indent=1, default=float))
    print(json.dumps(stats, indent=1, default=float))
    print(tdf[["draw_id", "pf_total", "pf_sharpe", "pf_maxdd", "exposure", "n", "avg_r", "avg_r_wo_best", "day_t",
               "elig", "label"]].to_string())
    print(vdf[["draw_id", "n", "avg_r", "avg_r_wo_best", "day_t", "avg_cost_r", "avg_gross_r", "elig", "label"]]
          .to_string())


def check() -> None:
    fz = json.loads((HERE / "fit_stats.json").read_text())
    elig_t = set(pd.read_csv(HERE / "fit_trend.csv").query("elig").draw_id)
    elig_v = set(pd.read_csv(HERE / "fit_vol.csv").query("elig").draw_id)
    load()
    bh = {s: buy_hold(s) for s in ("fit", "check")}
    jobs = [(r, s, SEED + 10 * k + (s == "check")) for k, r in enumerate(TREND) for s in ("fit", "check")]
    with mp.get_context("fork").Pool(4) as pool:
        rnd = pool.map(trend_random, jobs)
        vrows = pool.map(vol_score, [(c, s, SEED + 1000 + 10 * k + (s == "check")) for k, c in enumerate(VOL)
                                     for s in ("fit", "check")])
    rnd = {(j[0].draw_id, j[1]): x for j, x in zip(jobs, rnd)}
    rows = []
    for r in TREND:
        row = {"draw_id": r.draw_id, "label": r.label(), "fit_eligible": r.draw_id in elig_t}
        for s in ("fit", "check"):
            sm = trend_summary(r, s)
            rb = rnd[(r.draw_id, s)]
            row.update({f"{s}_{k}": v for k, v in sm.items() if k not in ("draw_id", "label")})
            row[f"{s}_rand_total_med"] = float(np.nanmedian(rb["rand_total"]))
            row[f"{s}_rand_sharpe_med"] = float(np.nanmedian(rb["rand_sharpe"]))
            row[f"{s}_rand_maxdd_med"] = float(np.nanmedian(rb["rand_maxdd"]))
            row[f"{s}_pct_total"] = float(np.mean(rb["rand_total"] < sm["pf_total"]))
            row[f"{s}_pct_sharpe"] = float(np.mean(rb["rand_sharpe"] < sm["pf_sharpe"]))
            row[f"{s}_pct_avg_r"] = float(np.nanmean(rb["rand_avg_r"] < sm["avg_r"]))
            for tag, kw in (("taker", {"mode": "taker"}), ("t3", {"tier": 3})):
                ss = trend_summary(r, s, **kw)
                row[f"{s}_{tag}_total"], row[f"{s}_{tag}_sharpe"], row[f"{s}_{tag}_avg_r"] = (
                    ss["pf_total"], ss["pf_sharpe"], ss["avg_r"])
        row["survivor"] = bool(row["fit_eligible"] and row["check_n"] >= 20 and row["check_avg_r"] > 0
                               and row["check_avg_r_wo_best"] > 0 and row["check_best_day_share"] < MAX_SHARE
                               and row["check_day_t"] >= CHECK_T and row["check_pct_avg_r"] > 0.5
                               and row["check_pf_sharpe"] >= bh["check"]["pf_sharpe"])
        rows.append(row)
    tdf = pd.DataFrame(rows)
    tdf.to_csv(HERE / "check_trend.csv", index=False, float_format="%.4f")
    vd = {}
    for v in vrows:
        s = "check" if v["draw_id"] in vd and "fit_n" in vd[v["draw_id"]] else "fit"
        d = vd.setdefault(v["draw_id"], {"draw_id": v["draw_id"], "label": v["label"],
                                         "fit_eligible": v["draw_id"] in elig_v})
        d.update({f"{s}_{k}": x for k, x in v.items() if k not in ("draw_id", "label")})
    vdf = pd.DataFrame(list(vd.values()))
    vdf["survivor"] = (vdf.fit_eligible & (vdf.check_n >= 20) & (vdf.check_avg_r > 0) & (vdf.check_avg_r_wo_best > 0)
                       & (vdf.check_best_day_share < MAX_SHARE) & (vdf.check_day_t >= CHECK_T)
                       & (vdf.check_rand_pct > 0.5))
    vdf.to_csv(HERE / "check_vol.csv", index=False, float_format="%.4f")
    (HERE / "buy_hold.json").write_text(json.dumps({**bh, "n_cum": fz["n_cum"]}, indent=1, default=float))
    print(json.dumps(bh, indent=1, default=float))
    cols = ["draw_id", "fit_pf_total", "fit_pf_sharpe", "fit_pf_maxdd", "check_pf_total", "check_pf_sharpe",
            "check_pf_maxdd", "check_exposure", "check_n", "check_avg_r", "check_day_t", "check_pct_sharpe",
            "check_pct_total", "survivor"]
    print(tdf[cols].to_string())
    print(vdf[["draw_id", "fit_n", "fit_avg_r", "fit_day_t", "fit_rand_pct", "check_n", "check_avg_r",
               "check_avg_r_wo_best", "check_day_t", "check_rand_pct", "survivor"]].to_string())


if __name__ == "__main__":
    np.seterr(all="ignore")
    {"fit": fit, "check": check}[sys.argv[1]]()
