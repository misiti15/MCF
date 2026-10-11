"""OF-A report: aggregate scan outputs -> ic_summary.csv, lift_summary.csv, results_lines.csv, gate tally (stdout).
Gates pre-declared in NOTES 1.4. Educational only - not financial advice."""
from __future__ import annotations

import glob
import math
from pathlib import Path

import numpy as np
import pandas as pd

import of_lib as L

HERE = Path(__file__).resolve().parent
SCAN = L.DATA / "scan"
N_TRIES = 676
T_REQ = round(max(1.5, math.sqrt(2 * math.log(N_TRIES))), 2)


def load(kind: str) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(SCAN / f"{kind}_*.parquet")))], ignore_index=True)


def ic_summary(ic: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (f, h), g in ic.groupby(["feature", "h"]):
        for col in ("ic", "ic_resid"):
            d = g.groupby("date")[col].mean().dropna()
            if len(d) < 3:
                continue
            rows.append(dict(feature=f, h=h, kind=col, mean=round(d.mean(), 4), t=round(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))), 2),
                             days_pos=round((d > 0).mean(), 2), n_days=len(d), h1=round(d[d.index.isin(L.H1)].mean(), 4),
                             h2=round(d[d.index.isin(L.H2)].mean(), 4)))
    return pd.DataFrame(rows)


def lift_summary(lf: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for f, g in lf.groupby("feature"):
        d = g.groupby("date")[["n", "L", "S", "n_hi", "L_hi", "n_lo", "S_lo"]].sum()
        for side, a, b, nf in (("long", "L_hi", "L", "n_hi"), ("short", "S_lo", "S", "n_lo")):
            base = d[b] / d["n"]
            rate = d[a] / d[nf].replace(0, np.nan)
            diff = (rate - base).dropna()
            pb, pr = d[b].sum() / d["n"].sum(), d[a].sum() / max(1, d[nf].sum())
            rows.append(dict(feature=f, side=side, base=round(pb, 4), rate_flag=round(pr, 4), lift=round(pr / pb, 2) if pb else None,
                             flagged_share=round(d[nf].sum() / d["n"].sum(), 3),
                             t_diff=round(diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff))), 2) if len(diff) > 2 else None))
    return pd.DataFrame(rows)


def stats(g: pd.DataFrame, col: str, reg: pd.Series) -> dict:
    d = g.groupby("date").agg(n=("n", "sum"), s=(col, "sum"))
    n = d.n.sum()
    if n == 0:
        return {}
    mu = d.s.sum() / n
    se = math.sqrt(((d.s - d.n * mu) ** 2).sum()) / n if len(d) > 1 else float("nan")
    best = d.s.idxmax()
    out = dict(n=int(n), days=len(d), exp=round(mu, 2), t=round(mu / se, 2) if se > 0 else None,
               ex_best=round((d.s.sum() - d.s[best]) / max(1, n - d.n[best]), 2), busiest=round(d.n.max() / n, 3))
    for k in ("up", "down", "flat"):
        dd = d[d.index.map(reg) == k]
        out[f"exp_{k}"] = round(dd.s.sum() / dd.n.sum(), 2) if dd.n.sum() else None
        out[f"n_{k}"] = int(dd.n.sum())
    for k, days in (("h1", L.H1), ("h2", L.H2)):
        dd = d[d.index.isin(days)]
        out[f"exp_{k}"] = round(dd.s.sum() / dd.n.sum(), 2) if dd.n.sum() else None
    return out


def lines_summary(ln: pd.DataFrame, reg: pd.Series) -> pd.DataFrame:
    rows = []
    for line, g in ln.groupby("line"):
        kind, feat, mode, q, ex = line.split("|")
        for col, lab in (("sum_r", "primary"), ("sum_rh", "hedged"), ("sum_r2", "secondary")):
            s = stats(g, col, reg)
            if not s:
                continue
            s.update(line=line, kind=kind, feature=feat, mode=mode, q=q, exit=ex, cost=lab,
                     win=round(g.wins.sum() / g.n.sum(), 3),
                     exp_long=round(g[g.side == "long"][col].sum() / max(1, g[g.side == "long"].n.sum()), 2),
                     exp_short=round(g[g.side == "short"][col].sum() / max(1, g[g.side == "short"].n.sum()), 2))
            rows.append(s)
    r = pd.DataFrame(rows)
    # price-only comparator: the better of r60 / r300 with the same mode, q, exit and cost line
    pr = r[r.kind == "price"].groupby(["mode", "q", "exit", "cost"]).exp.max().rename("price_best_exp")
    r = r.join(pr, on=["mode", "q", "exit", "cost"])
    bare = r[(r.kind == "setup") & (r["mode"] == "bare")].set_index(["feature", "exit", "cost"]).exp.rename("bare_exp")
    r = r.join(bare, on=["feature", "exit", "cost"])
    def gate(x):
        f = []
        if not (x.exp > 0): f.append("exp<=0")
        if (x.t or 0) < T_REQ: f.append(f"t<{T_REQ}")
        if x.n < 150: f.append("n<150")
        if not ((x.exp_up or -1) > 0 and (x.exp_down or -1) > 0): f.append("regime")
        if not (x.ex_best > 0): f.append("ex_best")
        if x.busiest > 0.10: f.append("busiest>10%")
        if not ((x.exp_h1 or -1) > 0 and (x.exp_h2 or -1) > 0): f.append("halves")
        if x.kind == "flow" and not (x.exp > (x.price_best_exp if pd.notna(x.price_best_exp) else -1e9)): f.append("<=price-only")
        if x.kind == "setup" and x["mode"] != "bare" and not (x.exp > x.bare_exp): f.append("<=bare")
        return ";".join(f) if f else "PASS"
    r["gates"] = r.apply(gate, axis=1)
    return r


def main():
    b1 = L.bars1m()
    reg = L.regimes(b1)
    ic, lf, ln = load("ic"), load("lift"), load("lines")
    ic = ic[ic.date.isin(L.SCORED)]
    ics, lfs = ic_summary(ic), lift_summary(lf)
    ics.to_csv(HERE / "ic_summary.csv", index=False)
    lfs.to_csv(HERE / "lift_summary.csv", index=False)
    r = lines_summary(ln, reg)
    r.to_csv(HERE / "results_lines.csv", index=False)
    pd.set_option("display.width", 250)
    print("symbols:", ln.symbol.nunique(), "regimes:", reg.value_counts().to_dict(), "T_REQ", T_REQ)
    print(ics[ics.kind == "ic"].pivot(index="feature", columns="h", values="t").to_string())
    print(ics[ics.kind == "ic"].pivot(index="feature", columns="h", values="mean").to_string())
    print(ics[ics.kind == "ic_resid"].pivot(index="feature", columns="h", values="t").to_string())
    print(ics[ics.kind == "ic_resid"].pivot(index="feature", columns="h", values="mean").to_string())
    print(lfs.to_string())
    p = r[r.cost == "primary"]
    print("tries counted (lines):", r[r.kind != "random"].groupby("cost").size().to_dict())
    print(p.gates.value_counts().head(20))
    cols = ["line", "n", "exp", "t", "exp_up", "exp_down", "exp_h1", "exp_h2", "ex_best", "busiest", "win", "price_best_exp", "gates"]
    print(p.sort_values("t", ascending=False)[cols].head(30).to_string())
    print(r[(r.cost == "hedged")].sort_values("t", ascending=False)[cols].head(15).to_string())
    print(r[r.kind.isin(["random", "setup"])].sort_values(["cost", "line"])[cols + ["cost", "bare_exp"]].to_string())


if __name__ == "__main__":
    main()
