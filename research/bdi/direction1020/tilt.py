"""Part B (PLAN.md): book tilt simulation. Entries from entries.py (live Primary + Testing 1 setups on the history2y lab
frames, production + time-of-day costs in, R = frame outcome). Signals from the lab context table (spy_fo, qqq_fo,
breadth at the 5-min bar close = live LabStrategy context). The book starts neutral (w = 1); from the checkpoint on,
the with-trend side and the against-trend side are re-weighted. 38 policies x 2 books = 76 configurations.
Train <= 2025-12-31, valid 2026-01-01..2026-10-07. Locked block absent (asserted).
Writes tilt_results.csv, tilt_by_setup.csv, tilt_out.txt. Usage: python tilt.py <scratch>.
Educational only - not financial advice."""
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
S = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "research/history2y"))
from lib import load_context, months, regimes  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
LOCK = ("2024-11-01", "2025-02-28")
N_CFG = 76
BAR = max(1.5, math.sqrt(2 * math.log(N_CFG)))
BAR_LINEAGE = max(1.5, math.sqrt(2 * math.log(2450 + 23 + N_CFG)))

E = pd.read_parquet(S / "entries.parquet")
assert not ((E.date >= LOCK[0]) & (E.date <= LOCK[1])).any()
ctx = pd.concat([load_context(m) for m in months()], ignore_index=True)
ctx["date"] = ctx.date.astype(str)
assert not ((ctx.date >= LOCK[0]) & (ctx.date <= LOCK[1])).any()
E = E[E.date <= "2026-10-07"].reset_index(drop=True)
E["s"] = np.where(E.side == "long", 1, -1)
E["split"] = np.where(E.date <= "2025-12-31", "train", "valid")
rg = regimes().reset_index(); rg["date"] = rg["date"].astype(str)
E = E.merge(rg[["date", "regime"]], on="date", how="left")
prim = {k for k, v in yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"].items()
        if isinstance(v, dict) and v.get("enabled")}
E["primary"] = E.setup.isin(prim)


def signal(name, C):
    """Day -> direction in {+1, -1, 0} decided at checkpoint tod C."""
    c = ctx[ctx.tod == C].set_index("date")
    if name.startswith("Q"):
        k = {"Q25": 0.25, "Q50": 0.50}[name]
        d = np.where(c.qqq_fo.abs() >= k, np.sign(c.qqq_fo), 0)
    elif name == "BR":
        d = np.where(c.breadth >= 0.60, 1, np.where(c.breadth <= 0.40, -1, 0))
    elif name == "K3":
        sg = np.sign(c.spy_fo)
        d = np.where((sg == np.sign(c.qqq_fo)) & (sg == np.sign(c.breadth - 0.5)) & (c.spy_fo.abs() >= 0.20), sg, 0)
    d = pd.Series(np.nan_to_num(d), index=c.index)
    return d


SIZ = {"M1": (1.5, 0.5), "M2": (1.0, 0.0)}


def weights(d_entry, s, siz):
    w_with, w_against = SIZ[siz]
    return np.where(d_entry == 0, 1.0, np.where(d_entry == s, w_with, w_against))


POL = {}
for sig in ("Q25", "Q50", "BR", "K3"):
    for C in (1000, 1015, 1030, 1100):
        for siz in ("M1", "M2"):
            POL[f"S-{sig}-{C}-{siz}"] = ("static", sig, [C], siz, 1)
for sig in ("Q25", "BR"):
    for siz in ("M1", "M2"):
        POL[f"D-{sig}-dyn-{siz}"] = ("dyn", sig, [1000, 1030, 1100, 1200, 1300], siz, 1)
for C in (1000, 1030):
    POL[f"F-Q50-{C}-M1-fade"] = ("static", "Q50", [C], "M1", -1)
assert len(POL) * 2 == N_CFG

SIGS = {}
def sig_of(sig, C):
    if (sig, C) not in SIGS:
        SIGS[(sig, C)] = signal(sig, C)
    return SIGS[(sig, C)]


def direction(X, kind, sig, Cs, flip):
    d = np.zeros(len(X))
    tod, date = X.tod.to_numpy(), X.date
    for C in Cs:                                            # later checkpoints overwrite earlier (dynamic)
        dc = date.map(sig_of(sig, C)).fillna(0).to_numpy()
        d = np.where(tod >= C, dc, d)
    return d * flip


def tday(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 0 else np.nan


def score(X, d, siz):
    r, s = X.r.to_numpy(), X.s.to_numpy()
    w = weights(d, s, siz); wf = weights(-d, s, siz)
    dl, dlf = (w - 1) * r, (wf - 1) * r
    days = X.date.to_numpy()
    Dd = pd.Series(dl).groupby(days).sum()
    Ex = pd.Series(0.5 * (dl - dlf)).groupby(days).sum()
    n = len(X)
    reg = X.regime.to_numpy()
    out = dict(n=n, days=len(Dd), par_exp=r.mean(), tilt_exp=(w * r).sum() / w.sum() if w.sum() > 0 else np.nan,
               exposure=w.mean(), reweighted=(d != 0).mean(), days_active=pd.Series(d != 0).groupby(days).any().mean(),
               delta=dl.sum() / n, t=tday(Dd), delta_ex_best=(Dd.sum() - Dd.max()) / n,
               random_delta=0.5 * (dl + dlf).sum() / n, excess=Ex.sum() / n, excess_t=tday(Ex))
    for k in ("up", "flat", "down"):
        m = reg == k
        out[f"d_{k}"] = dl[m].sum() / max(m.sum(), 1)
        out[f"par_{k}"] = r[m].mean() if m.any() else np.nan
    mo = pd.Series(dl).groupby(pd.Series(days).str[:7].to_numpy()).sum()
    out["months_pos"] = f"{int((mo > 0).sum())}/{len(mo)}"
    return out


if __name__ == "__main__":
    rows = []
    books = {"primary": E[E.primary].reset_index(drop=True), "pooled": E}
    lines = []
    P = lambda *x: lines.append(" ".join(str(y) for y in x))
    for bk, B in books.items():
        P(f"book {bk}: {len(B)} entries, setups {B.setup.nunique()}, short share {(B.s < 0).mean():.2f}, "
          f"train {(B.split == 'train').sum()} / valid {(B.split == 'valid').sum()}")
        for name, (kind, sig, Cs, siz, flip) in POL.items():
            d_all = direction(B, kind, sig, Cs, flip)
            for sp in ("train", "valid"):
                m = (B.split == sp).to_numpy()
                rows.append(dict(book=bk, policy=name, split=sp, **score(B[m], d_all[m], siz)))
    R = pd.DataFrame(rows)

    def neighbours(name):
        p = name.split("-")
        if p[0] != "S":
            return []
        cs = [1000, 1015, 1030, 1100]; i = cs.index(int(p[2]))
        return [f"S-{p[1]}-{cs[j]}-{p[3]}" for j in (i - 1, i + 1) if 0 <= j < len(cs)]

    verdict = {}
    for (bk, name), g in R.groupby(["book", "policy"]):
        tr, va = g[g.split == "train"].iloc[0], g[g.split == "valid"].iloc[0]
        nb = [R[(R.book == bk) & (R.policy == x) & (R.split == "valid")].delta.iloc[0] for x in neighbours(name)]
        checks = dict(delta_tr=tr.delta > 0, delta_va=va.delta > 0, t_va=va.t >= BAR, excess=(tr.excess > 0) and (va.excess > 0) and (va.excess_t >= 1.65),
                      up_down=(va.d_up > 0) and (va.d_down > 0), ex_best=va.delta_ex_best > 0, plateau=(len(nb) > 0 and all(x > 0 for x in nb)) or name[0] != "S")
        verdict[(bk, name)] = ("PASS" if all(checks.values()) else "fail: " + ",".join(k for k, v in checks.items() if not v))
    R["verdict"] = [verdict[(b, p)] for b, p in zip(R.book, R.policy)]
    R.round(5).to_csv(OUT / "tilt_results.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 500); pd.set_option("display.max_colwidth", 60)
    P(f"N {N_CFG}, bar {BAR:.2f}, lineage bar {BAR_LINEAGE:.2f}")
    W = R.pivot_table(index=["book", "policy"], columns="split", values=["delta", "t", "excess", "excess_t", "d_up", "d_down"]).round(4)
    W.columns = [f"{a}_{b}" for a, b in W.columns]
    W = W.join(R[R.split == "valid"].set_index(["book", "policy"])[["reweighted", "days_active", "exposure", "tilt_exp", "par_exp", "delta_ex_best", "months_pos", "verdict"]].round(4))
    P(W.to_string())
    # per setup, primary book, for the best valid policies (descriptive)
    bs = []
    for name in R[(R.book == "primary") & (R.split == "valid")].sort_values("t", ascending=False).policy.head(3):
        kind, sig, Cs, siz, flip = POL[name]
        d_all = direction(E, kind, sig, Cs, flip)
        E["_d"] = d_all
        for (st, sp), x in E.groupby(["setup", "split"]):
            w = weights(x._d.to_numpy(), x.s.to_numpy(), siz)
            bs.append(dict(policy=name, setup=st, primary=st in prim, split=sp, n=len(x), base=x.r.mean(), delta=((w - 1) * x.r).mean()))
    pd.DataFrame(bs).round(4).to_csv(OUT / "tilt_by_setup.csv", index=False)
    open(OUT / "tilt_out.txt", "w").write("\n".join(lines) + "\n\nEducational only - not financial advice.\n")
    print("\n".join(lines))
