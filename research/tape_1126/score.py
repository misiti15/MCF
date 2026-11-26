"""TAPE-1126 scoring (PREREG.md pass bars). Usage: python score.py OUT SIGW H2W > score_out.txt; writes OUT/score.json.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

OUT, SW, HW = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
LOCK = ("2024-11-01", "2025-02-28")
SG = np.load(SW / "sig.npz"); SD = SG["days"].astype(str); SPOS = {d: i for i, d in enumerate(SD)}
CTXS = ["BASE", "LO", "L3OUT", "LOL3OUT"]; JUDGE = ["BASE", "LOL3OUT"]; SPL = ["CHECK", "T2"]
NAMES = ["L3", "RW3", "RW5", "NM-ETF"]; NR = 20
res = {}


def load(ctx, book, cfg):
    p = OUT / f"day_{ctx}_{book}_{cfg}.parquet"
    if not p.exists():
        return None
    x = pd.read_parquet(p)
    assert not ((x.date >= LOCK[0]) & (x.date <= LOCK[1])).any()
    x["tot"] = x[[c for c in x.columns if c.startswith("R") and c[1:].isdigit()]].sum(1)
    return x.set_index("date")


def mets(s):
    s = s.sort_index()
    return dict(n=len(s), avg=s.mean(), tot=s.sum(), red_m=(s < 0).mean() * 21, w5=s.nsmallest(5).sum(),
                d10=int((s <= -10).sum()), floor20=s.rolling(20).sum().min())


def tstat(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 and d.std() > 0 else np.nan


def brake(ctx, book, rule):
    b = load(ctx, book, "base"); c = load(ctx, book, rule); k = load(ctx, book, rule + "c")
    rs = [load(ctx, book, f"{rule}r{i}") for i in range(NR)]; rs = [r for r in rs if r is not None]
    if b is None or c is None or not rs:
        return None
    rm = pd.concat([r.tot for r in rs], axis=1).mean(1)
    out = {}
    nset = len([x for x in b.columns if x.startswith("R") and x[1:].isdigit()])
    for sp in ["FIT"] + SPL:
        ix = b.index[b.per == sp]
        if not len(ix):
            continue
        d = c.tot[ix] - b.tot[ix]; dr = c.tot[ix] - rm[ix]
        out[sp] = dict(base=mets(b.tot[ix]), cfg=mets(c.tot[ix]), d_avg=d.mean(), d_yr=d.mean() * 252,
                       rand_avg=(rm[ix] - b.tot[ix]).mean(), const_avg=(k.tot[ix] - b.tot[ix]).mean(),
                       t_vs_rand=tstat(dr), t_vs_base=tstat(d), t_vs_const=tstat(c.tot[ix] - k.tot[ix]),
                       best_share=(d.max() / d.sum() if d.sum() > 0 else np.nan),
                       per_setup={f"R{s}": c[f"R{s}"][ix].sum() - b[f"R{s}"][ix].sum() for s in range(nset)},
                       lots_cut=int(b[[f"N{s}" for s in range(nset)]].loc[ix].sum().sum() -
                                    c[[f"N{s}" for s in range(nset)]].loc[ix].sum().sum()))
    out["pooled_setup"] = {f"R{s}": float(c[f"R{s}"].sum() - b[f"R{s}"].sum()) for s in range(nset)}
    return out


def overlay(x, inst):
    """hedge P&L per day for S3 runs: h = -4 - NB at the fire bar, H1 trade from that bar."""
    v = np.zeros(len(x))
    for j, (d, q, nb) in enumerate(zip(x.index, x.fire_q, x.fire_nb)):
        if q < 0:
            continue
        i = SPOS[d]; h = -4.0 - nb
        if h <= 0:
            continue
        rp = SG[inst + "_rp"][i, q]
        if not np.isfinite(rp):
            continue
        if inst == "IWM":
            h = h / SG["biw"][i]
        v[j] = h * 100 * rp
    return pd.Series(v, index=x.index)


def hedge_cmp(base, comb_fn, plac):
    out = {}
    for sp in ["FIT"] + SPL:
        ix = base.index[base.per == sp]
        if not len(ix):
            continue
        b = base.tot[ix]; c = comb_fn(ix)
        w5b, w5c = b.nsmallest(5).sum(), c.nsmallest(5).sum()
        imp = (w5c - w5b) / abs(w5b)
        pim = [(p(ix).nsmallest(5).sum() - w5b) / abs(w5b) for p in plac]
        wd10 = b.nsmallest(10).index; wd20 = b.nsmallest(20).index
        out[sp] = dict(base=mets(b), cfg=mets(c), w5_imp=imp, d_yr=(c - b).mean() * 252,
                       plac_p90=float(np.percentile(pim, 90)) if pim else np.nan,
                       plac_mean=float(np.mean(pim)) if pim else np.nan,
                       worst10=(c - b)[wd10].sum(), worst20=(c - b)[wd20].sum(),
                       plac_worst10=float(np.mean([(p(ix) - b)[wd10].sum() for p in plac])) if plac else np.nan,
                       passed=bool(imp >= 0.20 and (c - b).mean() * 252 >= -10 and pim and imp > np.percentile(pim, 90)))
    return out


def standalone(tr, key):
    out = {}
    for sp in ["FIT"] + SPL:
        t = tr[tr.per == sp]
        if not len(t):
            continue
        dd = t.groupby("date")[key].sum()
        out[sp] = dict(n=len(t), avg=t[key].mean(), wo_best=(t[key].sum() - dd.max()) / max(len(t) - 1, 1),
                       best_share=dd.max() / t[key].sum() if t[key].sum() > 0 else np.nan, day_t=tstat(dd), tot=t[key].sum())
    return out


if __name__ == "__main__":
    pers = pd.Series({d: ("FIT" if (d[:7] == "2024-10" or "2025-03" <= d[:7] <= "2025-09") else
                          "CHECK" if d >= "2025-10-01" else "T2") for d in SD})
    for ctx in CTXS:
        R = res.setdefault(ctx, {})
        for rule in ("S1", "S2"):
            R[rule] = brake(ctx, "P4", rule)
        base = load(ctx, "P4", "base")
        if base is None:
            continue
        # S3 + H1 (SPY / IWM)
        s3 = load(ctx, "P4", "S3")
        pls = [load(ctx, "P4", f"S3p{i}") for i in range(NR)]; pls = [p for p in pls if p is not None]
        for inst in ("SPY", "IWM"):
            if s3 is None:
                continue
            tot = s3.tot + overlay(s3, inst)
            plac = [(lambda ix, p=p: (p.tot + overlay(p, inst))[ix]) for p in pls]
            R["S3H1_" + inst] = hedge_cmp(base, lambda ix, tot=tot: tot[ix], plac)
            R["S3H1_" + inst]["fires"] = {sp: int(((s3.fire_q >= 0) & (s3.per == sp)).sum()) for sp in ["FIT"] + SPL}
            R["S3H1_" + inst]["hedge_R"] = {sp: float(overlay(s3, inst)[s3.per == sp].sum()) for sp in ["FIT"] + SPL}
            R["S3H1_" + inst]["lots_R"] = {sp: float((s3.tot - base.tot)[s3.per == sp].sum()) for sp in ["FIT"] + SPL}
            R["S3H1_" + inst]["per_setup"] = {f"R{s}": float(s3[f"R{s}"].sum() - base[f"R{s}"].sum()) for s in range(4) if f"R{s}" in s3}
        # H1 standalone (1R) and H2 add-on
        mk = SG["mkt"]; rng = np.random.default_rng(1126)
        for inst in ("SPY", "IWM"):
            r1 = SG[inst + "_r1"]
            rows = [(d, pers[d], r1[SPOS[d], int(np.argmax(mk[SPOS[d]]))]) for d in SD if mk[SPOS[d]].any()]
            tr = pd.DataFrame(rows, columns=["date", "per", "r"]).dropna()
            daily = tr.groupby("date").r.sum()
            plac = []
            for k in range(NR):
                pr = {}
                for sp in ["FIT"] + SPL:
                    nk = int((tr.per == sp).sum()); pool = base.index[base.per == sp]
                    for d in rng.choice(pool, size=min(nk, len(pool)), replace=False):
                        v = r1[SPOS[d], int(rng.integers(r1.shape[1]))]
                        pr[d] = v if np.isfinite(v) else 0.0
                plac.append(pd.Series(pr))
            pl_avg = {sp: float(np.nanmean([s[[d for d in s.index if pers[d] == sp]].mean() for s in plac])) for sp in ["FIT"] + SPL}
            R["H1_" + inst] = dict(stand=standalone(tr, "r"), plac_avg=pl_avg,
                                   book=hedge_cmp(base, lambda ix, daily=daily: base.tot[ix] + daily.reindex(ix).fillna(0),
                                                  [(lambda ix, s=s: base.tot[ix] + s.reindex(ix).fillna(0)) for s in plac]))
        h2 = pd.read_parquet(HW / "h2_trades.parquet"); q = pd.read_parquet(HW / "h2_control.parquet")
        d2 = h2.groupby("date").r.sum()
        cp = [(lambda ix, g=g: base.tot[ix] + g.groupby("date").r.sum().reindex(ix).fillna(0)) for _, g in q.groupby("draw")]
        R["H2"] = dict(stand=standalone(h2, "r"), ctl=standalone(q, "r"), r05=0.010,
                       book=hedge_cmp(base, lambda ix: base.tot[ix] + d2.reindex(ix).fillna(0), cp))
    # contenders standalone (S1)
    res["contenders"] = {f"C{i}": brake("BASE", f"C{i}", "S1") for i in range(2)}
    json.dump(res, open(OUT / "score.json", "w"), indent=1, default=float)
    print("written", OUT / "score.json")
