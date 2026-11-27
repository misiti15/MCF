"""RESID-MAP-1127 scorer: 20 cells (4 checkpoints x 5 residual features), decile long-short net of LR8 (PREREG.md).

Usage: python research/residmap_1127/rm_score.py ROWS.parquet OUT_DIR   (rows from rm_build.py)
Writes OUT_DIR/cells.json, cells.csv, days.parquet. Educational only - not financial advice."""

from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf import costs as C  # noqa: E402

LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
NOTIONAL = 10_000.0
FEATS = ["F1_RGAP", "F2_RINTRA", "F3_RLAST5", "F4_RZ", "F5_RPREV"]
BAR_T = 2.45


def split_of(d: pd.Series) -> pd.Series:
    s = pd.Series("", index=d.index)
    s[(d >= "2024-10-01") & (d <= "2024-10-31")] = "FIT"
    s[(d >= "2025-03-01") & (d <= "2025-09-30")] = "FIT"
    s[(d >= "2025-10-01") & (d <= "2026-11-04")] = "CHECK"
    s[(d >= "2023-01-01") & (d <= "2024-09-30")] = "T2"
    return s


def lr8_cost_bps(side: int, entry: np.ndarray, exit_: np.ndarray, days: pd.Series, model: dict) -> np.ndarray:
    """Round-trip LR8 cost (market entry, market exit) of a $NOTIONAL lot, in bps of entry notional (mirrors
    costs.lot_costs; checked against it on a sample in main)."""
    qty = NOTIONAL / entry
    ent = float(model.get("entry_bps", 1.0)) * 1e-4 * entry * qty
    mkt = np.maximum(float(model.get("market_exit_min_per_share", 0.01)),
                     float(model.get("market_exit_bps", 1.0)) * 1e-4 * exit_) * qty
    f = model.get("fees") or {}
    ds = pd.Series(days.dt.strftime("%Y-%m-%d").to_numpy())
    u = {d: (C.rate_on(f.get("sec_per_million"), d).get("rate", 0.0),
             float(C.rate_on(f.get("taf"), d).get("per_share", 0.0)),
             float(C.rate_on(f.get("taf"), d).get("max_per_trade", math.inf)),
             float(C.rate_on(f.get("cat"), d).get("per_share_side", 0.0))) for d in ds.unique()}
    sec, taf_ps, taf_mx, cat = (ds.map(lambda d, i=i: u[d][i]).to_numpy(float) for i in range(4))
    sell_px = exit_ if side == 1 else entry
    fees = sec * qty * sell_px / 1e6 + np.minimum(qty * taf_ps, taf_mx) + cat * 2 * qty
    return (ent + mkt + fees) / NOTIONAL * 1e4


def livel_bps(price: np.ndarray, cells: dict) -> np.ndarray:
    pb = pd.cut(price, [0, 5, 10, 20, 50, 100, np.inf], labels=["<5", "5-10", "10-20", "20-50", "50-100", "100+"],
                right=False).astype(str)
    return np.array([cells.get(f"{b}|market", cells["*|market"])[0] for b in pb])


def features(df: pd.DataFrame) -> pd.DataFrame:
    spy = df[df.sym == "SPY"].set_index(["d", "cp"])
    x = df[df.sym != "SPY"].join(spy[["o", "pc", "p5", "c1", "c2", "entry", "exit"]], on=["d", "cp"], rsuffix="_s")
    L = np.log
    x["F1_RGAP"] = L(x.o / x.c1) - L(x.o_s / x.c1_s)
    x["F2_RINTRA"] = L(x.pc / x.o) - L(x.pc_s / x.o_s)
    x["F3_RLAST5"] = L(x.pc / x.p5) - L(x.pc_s / x.p5_s)
    x["F4_RZ"] = x.rsum / (x.rsd * np.sqrt(x.nr))
    x["F5_RPREV"] = L(x.c1 / x.c2) - L(x.c1_s / x.c2_s)
    x["ret"] = x.exit / x.entry - 1.0
    x["spy_ret"] = x.exit_s / x.entry_s - 1.0
    x = x[(x.c1 >= 5) & (x.dv1 >= 5e6) & np.isfinite(x.ret) & (x.entry > 0)]
    return x


def stats(v: pd.Series) -> dict:
    v = v.dropna()
    n = len(v)
    if n < 3:
        return {"n": n}
    tot = v.sum()
    best = v.max()
    return {"n": n, "mean": v.mean(), "t": v.mean() / v.std(ddof=1) * math.sqrt(n),
            "wo_best": (tot - best) / (n - 1), "best_share": (best / tot) if tot > 0 else None,
            "red21": (v < 0).mean() * 21, "worst5": v.nsmallest(5).sum(),
            "floor20": v.rolling(20).sum().min()}


def main(rows: str, out: str):
    Path(out).mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(rows)
    assert not ((df.d >= LOCK_A) & (df.d <= LOCK_B)).any(), "locked block in rows"
    x = features(df)
    x["split"] = split_of(x.d)
    x = x[x.split != ""]
    model = C.live_model({"costs": __import__("mcf.config", fromlist=["load_config"]).load_config().get("costs")})
    assert model, "LR8 model missing"
    x["cL"] = lr8_cost_bps(1, x.entry.to_numpy(), x.exit.to_numpy(), x.d, model)
    x["cS"] = lr8_cost_bps(-1, x.entry.to_numpy(), x.exit.to_numpy(), x.d, model)
    # parity with costs.lot_costs on a sample
    for _, r in x.sample(20, random_state=1).iterrows():
        for side, col in ((1, "cL"), (-1, "cS")):
            q = NOTIONAL / r.entry
            ref = C.lot_costs(side, r.entry, q, [(q, r.exit, "flatten")], None, r.d.strftime("%Y-%m-%d"), model)["total"]
            assert abs(ref / NOTIONAL * 1e4 - r[col]) < 1e-6, (ref, r[col])
    cells_ll = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))
    x["cLL"] = livel_bps(x.entry.to_numpy(), cells_ll)
    x["r_bps"] = x.ret * 1e4
    res, days_all = [], []
    for cp in ["0945", "1030", "1200", "1400"]:
        xc = x[x.cp == cp]
        for f in FEATS:
            z = xc[np.isfinite(xc[f])][["d", "split", "sym", f, "r_bps", "cL", "cS", "cLL", "spy_ret"]].copy()
            cnt = z.groupby("d").sym.transform("size")
            z = z[cnt >= 100]
            pct = z.groupby("d")[f].rank(pct=True, method="first")
            z["q"] = np.minimum(np.ceil(pct * 10) - 1, 9).clip(0, 9)
            g = z.groupby(["d", "q"]).agg(r=("r_bps", "mean"), cL=("cL", "mean"), cS=("cS", "mean"),
                                          cLL=("cLL", "mean"), n=("sym", "size")).reset_index()
            top, bot = g[g.q == 9].set_index("d"), g[g.q == 0].set_index("d")
            dd = pd.DataFrame({"gross": top.r - bot.r, "n_top": top.n, "n_bot": bot.n})
            meta = z.groupby("d").agg(split=("split", "first"), spy=("spy_ret", "first"))
            dd = dd.join(meta)
            sgn = 1 if dd[dd.split == "FIT"].gross.mean() > 0 else -1
            if sgn == 1:
                cost, costLL = top.cL + bot.cS, top.cLL + bot.cLL
            else:
                cost, costLL = top.cS + bot.cL, top.cLL + bot.cLL
            dd["net"] = sgn * dd.gross - cost
            dd["net_ll"] = sgn * dd.gross - costLL
            dd["cell"] = f"{cp}_{f}"
            days_all.append(dd.reset_index())
            r = {"cell": f"{cp}_{f}", "cp": cp, "feat": f, "sign": sgn,
                 "names_per_decile": float(dd.n_top.mean()), "cost_bps": float(cost.mean())}
            for sp in ["FIT", "CHECK", "T2"]:
                v = dd[dd.split == sp]
                st = stats(v.net)
                r.update({f"{sp}_{k}": val for k, val in st.items()})
                r[f"{sp}_gross"] = float(sgn * v.gross.mean())
                r[f"{sp}_net_ll"] = float(v.net_ll.mean())
                r[f"{sp}_up"] = float(v[v.spy > 0].net.mean())
                r[f"{sp}_dn"] = float(v[v.spy <= 0].net.mean())
            oos = dd[dd.split.isin(["CHECK", "T2"])].net
            r["OOS_t"] = float(oos.mean() / oos.std(ddof=1) * math.sqrt(len(oos)))
            r["OOS_mean"] = float(oos.mean())
            gq = g.merge(meta[["split"]], left_on="d", right_index=True)
            dm = gq[gq.split == "CHECK"].groupby("q").r.mean()
            r["CHECK_mono"] = float(pd.Series(dm.values).corr(pd.Series(range(len(dm))), method="spearman")) * sgn
            dmt = gq[gq.split == "T2"].groupby("q").r.mean()
            r["T2_mono"] = float(pd.Series(dmt.values).corr(pd.Series(range(len(dmt))), method="spearman")) * sgn
            r["CHECK_deciles"] = [round(float(v), 1) for v in dm.values]
            ok = (all(r.get(f"{s}_mean", -1) > 0 for s in ["FIT", "CHECK", "T2"]) and r["OOS_t"] >= BAR_T
                  and all((r.get(f"{s}_wo_best") or -1) > 0 and (r.get(f"{s}_best_share") or 1) < 0.5
                          for s in ["CHECK", "T2"])
                  and all(r[f"{s}_up"] > 0 and r[f"{s}_dn"] > 0 for s in ["CHECK", "T2"]))
            r["PASS"] = bool(ok)
            res.append(r)
            print(f"{r['cell']:16s} s{sgn:+d} gross F/C/T {r['FIT_gross']:7.1f} {r['CHECK_gross']:7.1f} {r['T2_gross']:7.1f}"
                  f" | net {r['FIT_mean']:7.1f} {r['CHECK_mean']:7.1f} {r['T2_mean']:7.1f} | OOS t {r['OOS_t']:6.2f}"
                  f" | LL C/T {r['CHECK_net_ll']:7.1f} {r['T2_net_ll']:7.1f} | mono {r['CHECK_mono']:+.2f} {r['T2_mono']:+.2f}"
                  f" | {'PASS' if ok else ''}", flush=True)
    pd.DataFrame(res).to_csv(Path(out) / "cells.csv", index=False)
    json.dump(res, open(Path(out) / "cells.json", "w"), indent=1, default=float)
    pd.concat(days_all).to_parquet(Path(out) / "days.parquet")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
