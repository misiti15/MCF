"""WILDCARD-1127 scoring (PREREG.md): LIVE-L / LR8 / ETF-TIGHT costs, 24-config grid, H1 + H2 bars, random-direction
control, always-long baseline, per-ETF effects, up/down sessions, years. Locked block never read (asserted).
    python research/wildcard_1127/wc_score.py <out_dir>    -> research/wildcard_1127/{grid.csv,results.json}
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from mcf.research.gates import tod_cost_mult  # noqa: E402

LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
CELLS = json.load(open(HERE.parent / "primshorts_1126/cells_live.json"))
PB = [0, 5, 10, 20, 50, 100, 1e9]; PBL = ["<5", "5-10", "10-20", "20-50", "50-100", "100+"]
IDX4 = ["SPY", "QQQ", "IWM", "DIA"]
SEC12 = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "XLRE", "XLC", "SMH"]
GROUPS = {"IDX4": IDX4, "SEC12": SEC12}
SPLITS = ["EARLY", "T2", "FIT", "CHECK"]
H1 = ("IDX4", "P1", 0.0, 2.0)


def add_costs(t: pd.DataFrame) -> pd.DataFrame:
    price = t.entry.to_numpy(float)
    pb = pd.cut(price, PB, labels=PBL, right=False).astype(str)
    mult = tod_cost_mult(np.full(len(t), 1525))
    for s in (1.0, 2.0):
        risk = s * t.a20.to_numpy(float)
        bps = risk / price * 1e4
        for nm, side in (("L", 1), ("S", -1)):
            kind = t[f"k{nm}{s:g}"].to_numpy(int); px = t[f"x{nm}{s:g}"].to_numpy(float)
            a = np.array([CELLS.get(f"{p}|{'stop' if k else 'market'}", CELLS[f"*|{'stop' if k else 'market'}"])[0]
                          for p, k in zip(pb, kind)])
            b = np.array([CELLS.get(f"{p}|{'stop' if k else 'market'}", CELLS[f"*|{'stop' if k else 'market'}"])[1]
                          for p, k in zip(pb, kind)])
            g = t[f"g{nm}{s:g}"].to_numpy(float)
            livel = a / bps + b
            ec = (0.01 + price * 1e-4) * mult
            xc = 0.01 + px * 1e-4 + np.where(kind == 1, 0.02, 0.0)
            br = 1.2e-4 * price if side < 0 else 0.0
            lr8 = (ec + xc + br) / risk
            tight = (1e-4 * price + 1e-4 * px + np.where(kind == 1, 0.01, 0.0)) / risk
            t[f"gross_{nm}{s:g}"] = g
            t[f"livel_{nm}{s:g}"] = g - livel
            t[f"lr8_{nm}{s:g}"] = g - lr8
            t[f"tight_{nm}{s:g}"] = g - tight
    return t


def st(x, d=None) -> dict:
    x = np.asarray(x, float); n = len(x)
    if n == 0:
        return dict(n=0)
    s = pd.Series(x).groupby(np.asarray(d)).sum().to_numpy() if d is not None else x
    m = s.mean(); sd = s.std(ddof=1) if len(s) > 1 else np.nan
    tot = x.sum(); best = s.max()
    return dict(n=n, days=len(s), mean=round(float(x.mean()), 4), tot=round(float(tot), 2),
                t=round(float(m / (sd / np.sqrt(len(s)))), 2) if len(s) > 1 and sd > 0 else None,
                win=round(float((x > 0).mean()), 3),
                best_share=round(float(best / tot), 3) if tot > 0 else None,
                wo_best=round(float((tot - best) / (n - 1)), 4) if n > 1 else None)


def select(t, grp, pred, k):
    m = t.sym.isin(GROUPS[grp]) & (t.r1 != 0) & (t.r1.abs() >= k * t.sig20)
    if pred == "P2":
        m &= np.sign(t.rov) == np.sign(t.r1)
    return t[m]


def net(g, s, cost="livel", side=None):
    side = np.sign(g.r1).to_numpy() if side is None else side
    return np.where(side > 0, g[f"{cost}_L{s:g}"], g[f"{cost}_S{s:g}"])


def config_stats(g, s):
    r = {}
    for cost in ("livel", "lr8", "tight", "gross"):
        x = net(g, s, cost)
        r[cost] = {"ALL": st(x, g.date)}
        for sp in SPLITS:
            m = (g.split == sp).to_numpy(); r[cost][sp] = st(x[m], g.date[m])
        for nm, sps in (("DEV", ["EARLY", "FIT"]), ("OOS", ["T2", "CHECK"])):
            m = g.split.isin(sps).to_numpy(); r[cost][nm] = st(x[m], g.date[m])
    return r


def control(g, s, draws, rng):
    oos = g[g.split.isin(["T2", "CHECK"])]
    L = oos[f"livel_L{s:g}"].to_numpy(); S = oos[f"livel_S{s:g}"].to_numpy()
    actual = net(oos, s).mean()
    flips = rng.integers(0, 2, size=(draws, len(oos))).astype(bool)
    means = np.where(flips, L, S).mean(axis=1)
    return dict(actual=round(float(actual), 4), ctrl_mean=round(float(means.mean()), 4),
                ctrl_p95=round(float(np.quantile(means, 0.95)), 4), pct=round(float((means < actual).mean()), 4),
                always_long=round(float(L.mean()), 4), always_short=round(float(S.mean()), 4))


def detail(g, s):
    oos = g[g.split.isin(["T2", "CHECK"])].copy()
    oos["r"] = net(oos, s)
    per_etf = {k: st(v.r, v.date) for k, v in oos.groupby("sym")}
    updn = {"up": st(oos.r[oos.spy_cc > 0], oos.date[oos.spy_cc > 0]),
            "down": st(oos.r[oos.spy_cc <= 0], oos.date[oos.spy_cc <= 0])}
    allg = g.copy(); allg["r"] = net(allg, s); allg["year"] = allg.date.str[:4]
    years = {y: st(v.r, v.date) for y, v in allg.groupby("year")}
    big = allg.assign(ab=allg.r1.abs() / allg.sig20)
    big["bucket"] = pd.cut(big.ab, [0, 0.5, 1, 2, 99], labels=["<0.5", "0.5-1", "1-2", ">2"])
    buckets = {str(k): st(v.r, v.date) for k, v in big[big.split.isin(["T2", "CHECK"])].groupby("bucket", observed=True)}
    buckets_g = {str(k): st(np.where(np.sign(v.r1) > 0, v[f"gross_L{s:g}"], v[f"gross_S{s:g}"]), v.date)
                 for k, v in big[big.split.isin(["T2", "CHECK"])].groupby("bucket", observed=True)}
    stop_rate = float(np.where(np.sign(oos.r1) > 0, oos[f"kL{s:g}"], oos[f"kS{s:g}"]).mean())
    cost_mean = float((np.where(np.sign(oos.r1) > 0, oos[f"gross_L{s:g}"], oos[f"gross_S{s:g}"]) - oos.r).mean())
    return dict(per_etf=per_etf, updown=updn, years=years, abs_r1_buckets_livel=buckets, abs_r1_buckets_gross=buckets_g,
                stop_rate=round(stop_rate, 3), livel_cost_R=round(cost_mean, 4),
                stop_bps_median=round(float((s * oos.a20 / oos.entry * 1e4).median()), 1))


def bars(r, ctrl, det, n_etf, t_bar, frac_etf, base=None):
    L = r["livel"]; L8 = r["lr8"]
    b = {"livel_T2_pos": (L["T2"].get("mean") or -1) > 0, "livel_CHECK_pos": (L["CHECK"].get("mean") or -1) > 0,
         "lr8_T2_pos": (L8["T2"].get("mean") or -1) > 0, "lr8_CHECK_pos": (L8["CHECK"].get("mean") or -1) > 0,
         f"OOS_t_ge_{t_bar}": (L["OOS"].get("t") or -9) >= t_bar}
    for sp in ("T2", "CHECK"):
        b[f"{sp}_wo_best_pos"] = (L[sp].get("wo_best") or -1) > 0
        b[f"{sp}_best_share_lt_50"] = L[sp].get("best_share") is not None and L[sp]["best_share"] < 0.5
    b["ctrl_ge_p95"] = ctrl["pct"] >= 0.95
    pos = sum(1 for v in det["per_etf"].values() if (v.get("mean") or -1) > 0)
    b["per_etf"] = pos >= np.ceil(frac_etf * n_etf)
    b["up_pos"] = (det["updown"]["up"].get("mean") or -1) > 0
    b["down_pos"] = (det["updown"]["down"].get("mean") or -1) > 0
    if base is not None:
        b["beats_k0"] = L["OOS"]["mean"] > base
    return b


def main(out_dir: str):
    t = pd.read_csv(Path(out_dir) / "rows.csv.gz")
    dd = pd.to_datetime(t.date).dt.date
    assert not ((dd >= LOCK[0]) & (dd <= LOCK[1])).any()
    t = t[t.split != "LATE"].reset_index(drop=True)
    t = add_costs(t)
    rng = np.random.default_rng(1127)
    grid = []; res = {"configs": {}}
    for grp in GROUPS:
        for pred in ("P1", "P2"):
            for k in (0.0, 0.5, 1.0):
                for s in (1.0, 2.0):
                    g = select(t, grp, pred, k)
                    r = config_stats(g, s)
                    name = f"{grp}|{pred}|k{k:g}|s{s:g}"
                    res["configs"][name] = r
                    row = dict(config=name)
                    for cost in ("livel", "lr8", "tight", "gross"):
                        for sp in SPLITS + ["DEV", "OOS"]:
                            row[f"{cost}_{sp}_mean"] = r[cost][sp].get("mean"); row[f"{cost}_{sp}_t"] = r[cost][sp].get("t")
                    row["n_OOS"] = r["livel"]["OOS"]["n"]
                    grid.append(row)
    gdf = pd.DataFrame(grid)
    gdf.to_csv(HERE / "grid.csv", index=False)
    res["n_configs"] = len(gdf)
    # H1
    out = {}
    def judge(name, t_bar, frac, base=None):
        grp, pred, k, s = name.split("|"); k = float(k[1:]); s = float(s[1:])
        g = select(t, grp, pred, k)
        ctrl = control(g, s, 2000, rng); det = detail(g, s)
        b = bars(res["configs"][name], ctrl, det, len(GROUPS[grp]), t_bar, frac, base)
        return dict(config=name, stats=res["configs"][name], control=ctrl, detail=det, bars=b, passed=all(b.values()))
    out["H1"] = judge("IDX4|P1|k0|s2", 2.0, 0.75)
    others = gdf[gdf.config != "IDX4|P1|k0|s2"]
    fin = others.sort_values("livel_DEV_t", ascending=False).iloc[0].config
    grp, pred, k, s = fin.split("|")
    base = res["configs"][f"{grp}|{pred}|k0|{s}"]["livel"]["OOS"]["mean"] if k != "k0" else None
    out["H2"] = judge(fin, 2.87, 0.6, base)
    # informational: every config's control percentile + OOS (all finalists listed in REPORT)
    info = {}
    for name in gdf.config:
        grp, pred, k, s = name.split("|")
        g = select(t, grp, pred, float(k[1:]))
        info[name] = control(g, float(s[1:]), 500, rng)
    out["controls_all"] = info
    res.update(out)
    json.dump(res, open(HERE / "results.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    print(gdf[["config", "n_OOS"] + [f"livel_{x}_mean" for x in ("EARLY", "T2", "FIT", "CHECK")] +
              ["livel_DEV_t", "livel_OOS_t", "gross_OOS_mean", "gross_OOS_t", "tight_OOS_mean"]].to_string())
    for h in ("H1", "H2"):
        print(h, out[h]["config"], "passed", out[h]["passed"]); print(" bars", out[h]["bars"]); print(" ctrl", out[h]["control"])
        print(" det", {k: v for k, v in out[h]["detail"].items() if k in ("stop_rate", "livel_cost_R", "stop_bps_median")})


if __name__ == "__main__":
    main(sys.argv[1])
