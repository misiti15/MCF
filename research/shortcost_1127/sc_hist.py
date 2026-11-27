"""SHORTCOST-1127 Part B: history replay (FIT / CHECK / T2) of the cost-zone rules R1-R4 on bench10 candidate lots, home
account book (bench10.book), LIVE-L net R (headline) and LR8 (bench10 add_r), vs a size-matched random removal (20 seeds).
`python sc_hist.py SCRATCH` (SCRATCH holds trades_t1/t2.parquet and etb_rate.parquet). Writes hist_*.json/csv here.
Locked block asserted absent. Educational only - not financial advice."""
import json, os, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "ultimate_1119", "top10"))
import sc_common as C  # noqa: E402
import bench10 as B  # noqa: E402
S = sys.argv[1]
NSEED = 20
TAG = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
       "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "NM-ETF-late-dip-di-long": "NMETF",
       "GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short": "G05",
       "GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short": "G07",
       "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long": "G37",
       "RND-G05": "RND-G05", "RND-G07": "RND-G07", "RND-G37": "RND-G37"}
REAL = ["L3", "RW3", "RW5", "NMETF", "G05", "G07", "G37"]
HOME = {"L3": "primary", "RW3": "primary", "RW5": "primary", "NMETF": "primary"}
KN = {0: "market", 1: "stop", 2: "target"}


def period(d):
    d = pd.Series(d)
    fit = d.between("2024-10-01", "2024-10-31") | d.between("2025-03-01", "2025-09-30")
    return np.where(fit, "FIT", np.where(d.between("2025-10-01", "2026-11-04"), "CHECK",
                    np.where(d.between("2023-01-03", "2024-09-13"), "T2", "none")))


def load():
    x = pd.concat([pd.read_parquet(os.path.join(S, f"{f}.parquet")) for f in ("trades_t1", "trades_t2")], ignore_index=True)
    x["date"] = x.date.astype(str)
    C.no_locked(x.date.unique()); B.no_locked(x.date.unique())
    x["tag"] = x.setup.map(TAG)
    x = x[x.tag.notna()]
    x = B.add_r(x)                      # r = LR8 net, r_gross
    x["r_lr8"] = x.r
    x["ll_cost"] = C.cost_kind(x.entry, x.risk, x.kind.map(KN))
    x["r_ll"] = x.r_gross - x.ll_cost
    x["cex"] = C.c_ex(x.entry, x.risk)
    x["per"] = period(x.date)
    x = x[x.per != "none"].reset_index(drop=True)
    return x


X = load()
ETB = pd.read_parquet(os.path.join(S, "etb_rate.parquet")).rate
DAYS = {p: sorted(X[X.per == p].date.unique()) for p in ("FIT", "CHECK", "T2")}


def run_book(lots, basis):
    """book every setup separately (own home rules), basis = r column used by the latch and scored."""
    out = []
    for tg, g in lots.groupby("tag"):
        g = g.copy(); g["r"] = g[basis]
        rules = B.BOOK[HOME.get(tg, "testing")]
        b = B.book(g, rules, ETB)
        if len(b):
            out.append(b[["tag", "date", "per", "r", "symbol"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["tag", "date", "per", "r", "symbol"])


def job(args):
    rule, seed, basis = args
    L = X
    if rule == "BASE":
        keep = np.ones(len(L), bool)
    else:
        sk = C.rule_skip(rule, L.side.values, L.entry.values, L.risk.values, L.cex.values)
        if seed < 0:
            keep = ~sk
        else:
            rng = np.random.default_rng(1000 + seed)
            keep = np.ones(len(L), bool)
            for (tg, p), idx in L.groupby(["tag", "per"]).indices.items():
                q = sk[idx].mean(); k = int(round(q * len(idx)))
                if k:
                    keep[rng.choice(idx, k, replace=False)] = False
    b = run_book(L[keep], basis)
    day = b.groupby(["tag", "per", "date"]).r.agg(["sum", "count"]).reset_index()
    return rule, seed, basis, day, b if seed < 0 else None


if __name__ == "__main__":
    jobs = [("BASE", -1, "r_ll"), ("BASE", -1, "r_lr8")]
    for r in ["R1", "R2", "R3", "R4"]:
        jobs += [(r, -1, "r_ll"), (r, -1, "r_lr8")] + [(r, s, "r_ll") for s in range(NSEED)]
    with Pool(2) as p:
        res = p.map(job, jobs)
    D = {(r, s, b): d for r, s, b, d, _ in res}
    T = {(r, b): t for r, s, b, _, t in res if s < 0}
    pd.to_pickle({"D": D, "T": T, "DAYS": DAYS}, os.path.join(S, "hist_res.pkl"))
    # skip shares (candidate lots) per setup x split
    q = {}
    for r in ["R1", "R2", "R3", "R4"]:
        sk = C.rule_skip(r, X.side.values, X.entry.values, X.risk.values, X.cex.values)
        q[r] = pd.Series(sk).groupby([X.tag, X.per]).mean().round(4).to_dict()
    json.dump({f"{r}|{a}|{b}": v for r, d in q.items() for (a, b), v in d.items()}, open(os.path.join(HERE, "hist_skipshare.json"), "w"), indent=0)
    print("done", len(res))
