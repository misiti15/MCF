"""STOPX-1127 Step 1 scoring (PREREG.md): costs (LIVE-L shorts / LR8 research NM-ETF; confirmed + catastrophe exits charged
as "stop", "market" as sensitivity), BASE parity vs the rs_cand lots, Primary book (primshorts_1126 booksim, LATCH-OPEN on) per
config with its own exit minutes / R / open marks, paired dR/trade on the BASE book's lots (day-clustered t), per setup,
pass bar, goal metrics. Usage (repo root): python research/stopx_1127/sx_score.py WORK OUT.json.
Locked block 2024-11-01..2025-02-28 never read (asserted). Educational only - not financial advice."""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/primshorts_1126"))
from mcf.research.gates import tod_cost_mult  # noqa: E402
import calib_live as CLV  # noqa: E402
from booksim import sim_day  # noqa: E402

W, OUTF = Path(sys.argv[1]), sys.argv[2]
LOCK = ("2024-11-01", "2025-02-28")
PRIMARY4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
            "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
SHORT = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
         "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "NM-ETF-late-dip-di-long": "NM-ETF"}
CONFIGS = ["BASE", "C1", "C2", "C3"]
NSES = {"FIT": 170, "CHECK": 276, "T2": 427}   # sessions per split (primshorts_1126 score_options)
T_BAR = 3.4
CELLS = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def cost_r(c, k, market_kind=False):
    px, kind = c[f"px_{k}"].to_numpy(float), c[f"kind_{k}"].to_numpy(int)
    gross = c.side * (px - c.entry)
    rg = gross / c.risk
    # shorts: LIVE-L; a confirmed/catastrophe exit (kind 1 in C1-C3) is charged as "stop" unless market_kind
    kd = np.where(kind == 2, "target", np.where(kind == 1, "market" if (market_kind and k != "BASE") else "stop", "market"))
    live = rg - CLV.predict_R(CELLS, c.entry.to_numpy(), c.risk.to_numpy(), kd)
    tier = np.where((np.abs(c.gap) >= 20) | (c.entry < 5), 3.0, 1.0)
    ec = (0.01 + c.entry * 1e-4) * tod_cost_mult(c.tod.to_numpy())
    xc = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where((kind == 1) & ~(market_kind and k != "BASE"), 0.02, 0.0)
    lr8 = (gross - tier * (ec + xc)) / c.risk
    return rg, np.where(c.side < 0, live, lr8)


def book(job):
    k, lo_on = job
    C = pd.read_parquet(W / "scored.parquet")
    PATH = np.load(W / "paths.npy", mmap_mode="r")
    taken_all = np.zeros(len(C), bool)
    rows = []
    for d, g in C.groupby("date", sort=True):
        si = g.si.to_numpy(); side = g.side.to_numpy(float); ent = g.entry.to_numpy(float); risk = g.risk.to_numpy(float)
        rr = g[f"r_{k}"].to_numpy(float); lc = (g[f"rg_{k}"] - g[f"r_{k}"]).to_numpy(float)
        em = g.em.to_numpy(int); xm = g[f"xm_{k}"].to_numpy(int); off = g.off.to_numpy(int); n = g.n.to_numpy(int)
        xm = np.maximum(xm, em)

        def markf(o, m):
            j = np.clip(m - em[o], 0, n[o] - 1)
            return side[o] * (PATH[off[o] + j] - ent[o]) / risk[o] - lc[o]
        R, tk, tot, tr = sim_day(si, pd.factorize(g.symbol)[0], side, ent, risk, lc, em, xm, rr, markf, 4, np.ones(4),
                                 np.full(4, lo_on))
        taken_all[g.index.to_numpy()] = tk
        row = dict(date=d, per=g.per.iloc[0], R=tot)
        for s in range(4):
            row[f"R{s}"] = R[s]; row[f"N{s}"] = int(tk[si == s].sum())
        rows.append(row)
    return job, pd.DataFrame(rows), taken_all


def clustered_t(x, dates):
    m = x.mean(); e = (x - m).groupby(dates).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(x)
    return float(m / se) if se > 0 else float("nan")


def daymetrics(d, nses):
    tot = float(d.sum()); best = float(d.max())
    pad = np.r_[d.to_numpy(), np.zeros(max(0, nses - len(d)))]
    roll = pd.Series(d.to_numpy()).rolling(20).sum().min() if len(d) >= 20 else float("nan")
    return {"R_per_session": round(tot / nses, 3), "wo_best_day": round((tot - best) / (nses - 1), 3),
            "best_day_share": round(best / tot, 3) if tot > 0 else None, "worst5": round(float(d.nsmallest(5).sum()), 1),
            "red_per_21": round(float((pad < 0).sum()) / nses * 21, 1), "floor20": round(float(roll), 1)}


if __name__ == "__main__":
    c = pd.read_parquet(W / "walk.parquet")
    no_locked(c.date.unique())
    c["si"] = c.setup.map({s: i for i, s in enumerate(PRIMARY4)})
    for k in CONFIGS:
        c[f"rg_{k}"], c[f"r_{k}"] = cost_r(c, k)
        if k != "BASE":
            _, c[f"rm_{k}"] = cost_r(c, k, market_kind=True)
    par = {}
    for p, g in c.groupby("per"):
        par[p] = {"lots": int(len(g)), "xm_match": round(float((g.xm_BASE == g.xm).mean()), 4),
                  "avgR_cand": round(float(g.r.mean()), 4), "avgR_base": round(float(g.r_BASE.mean()), 4)}
    print("parity", par)
    c = c[c.per.isin(["FIT", "CHECK", "T2"])]
    c = c.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
    no_locked(c.date.unique())
    c.to_parquet(W / "scored.parquet", index=False)
    jobs = [(k, True) for k in CONFIGS] + [("BASE", False)]
    BK, TK = {}, {}
    with Pool(3) as pool:
        for job, df, tk in pool.imap_unordered(book, jobs):
            BK[job], TK[job] = df, tk
            print(job, round(df.R.sum(), 1), flush=True)
    c = pd.read_parquet(W / "scored.parquet")
    base_taken = TK[("BASE", True)]
    res = {"parity": par, "configs": {}}
    for k in CONFIGS:
        e = {}
        for per in ("FIT", "CHECK", "T2"):
            bb = BK[("BASE", True)]; bb = bb[bb.per == per].set_index("date")
            bk = BK[(k, True)]; bk = bk[bk.per == per].set_index("date")
            m = (c.per == per).to_numpy() & base_taken
            x = c[m]
            dr = x[f"r_{k}"] - x.r_BASE
            z = {"book": daymetrics(bk.R, NSES[per]), "lots_per_session": round(sum(bk[f"N{s}"].sum() for s in range(4)) / NSES[per], 1),
                 "paired_lots": int(len(x)), "avgR_base": round(float(x.r_BASE.mean()), 4), "avgR_cfg": round(float(x[f"r_{k}"].mean()), 4)}
            if k != "BASE":
                z["dR_trade"] = round(float(dr.mean()), 4); z["t"] = round(clustered_t(dr, x.date), 2)
                drm = x[f"rm_{k}"] - x.r_BASE
                z["dR_trade_market_cost"] = round(float(drm.mean()), 4); z["t_market_cost"] = round(clustered_t(drm, x.date), 2)
                ps = {}
                for s, gs in x.groupby("setup"):
                    d_ = gs[f"r_{k}"] - gs.r_BASE
                    ps[SHORT[s]] = {"n": int(len(gs)), "dR": round(float(d_.mean()), 4), "t": round(clustered_t(d_, gs.date), 2),
                                    "base": round(float(gs.r_BASE.mean()), 4), "cfg": round(float(gs[f"r_{k}"].mean()), 4),
                                    "wo_best_day_cfg": round(float(gs.loc[gs.date != gs.groupby("date")[f"r_{k}"].sum().idxmax(), f"r_{k}"].mean()), 4),
                                    "stop_share_base": round(float((gs.kind_BASE == 1).mean()), 3),
                                    "stop_share_cfg": round(float((gs[f"kind_{k}"] == 1).mean()), 3)}
                z["per_setup"] = ps
                dd = (bk.R - bb.R.reindex(bk.index).fillna(0))
                tot = float(dd.sum())
                z["book_dR_session"] = round(tot / NSES[per], 3)
                z["book_t"] = round(float(dd.mean() / (dd.std(ddof=1) / math.sqrt(len(dd)))), 2)
                z["book_dR_best_day_share"] = round(float(dd.max() / tot), 3) if tot > 0 else None
                w5b, w5k = float(bb.R.nsmallest(5).sum()), float(bk.R.nsmallest(5).sum())
                z["worst5_base"], z["worst5_cfg"] = round(w5b, 1), round(w5k, 1)
                if per in ("CHECK", "T2"):
                    nimp = sum(v["dR"] > 0 for v in ps.values())
                    z["pass"] = {"dR_t": bool(z["dR_trade"] > 0 and z["t"] >= T_BAR), "setups_2of3": bool(nimp >= 3),
                                 "none_worse_003": bool(min(v["dR"] for v in ps.values()) >= -0.03),
                                 "worst5_le_5pct": bool(w5k >= 1.05 * w5b), "best_day_share_lt_50": bool(tot > 0 and dd.max() / tot < 0.5)}
            e[per] = z
        if k != "BASE":
            e["PASS"] = bool(all(all(e[p]["pass"].values()) for p in ("CHECK", "T2")))
        res["configs"][k] = e
    bo = BK[("BASE", False)]
    res["base_LO_off"] = {p: daymetrics(bo[bo.per == p].set_index("date").R, NSES[p]) for p in ("FIT", "CHECK", "T2")}
    json.dump(res, open(OUTF, "w"), indent=1)
    for k in CONFIGS[1:]:
        for p in ("FIT", "CHECK", "T2"):
            z = res["configs"][k][p]
            print(k, p, "dR", z["dR_trade"], "t", z["t"], "mkt", z["dR_trade_market_cost"], "book", z["book"]["R_per_session"],
                  "dbook", z["book_dR_session"], "w5", z["worst5_base"], z["worst5_cfg"], {s: v["dR"] for s, v in z["per_setup"].items()},
                  z.get("pass"))
        print(k, "PASS" if res["configs"][k]["PASS"] else "FAIL")
    for p in ("FIT", "CHECK", "T2"):
        print("BASE LO", p, res["configs"]["BASE"][p]["book"], "| LO off", res["base_LO_off"][p])
