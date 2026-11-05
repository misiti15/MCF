"""GATE1: score the 62 pre-registered gates (PLAN.md) on TRAIN / VALID (2-year lab lists) and LIVE (paper journals).
Usage: python gate.py <scratch>. Writes gates.csv, allowed_states.csv. Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
N = 62; BAR = max(1.5, math.sqrt(2 * math.log(N)))
MINN = {"side": 500, "fs": 200, "setup": 60}
S = Path(sys.argv[1])
T = pd.read_parquet(S / "trades.parquet")
T = T[T.w.isin(["TRAIN", "VALID", "LIVE"])].reset_index(drop=True)
T["bk"] = np.where(T.w == "LIVE", np.where(T.acct.isin(["primary", "testing", "testing2"]), "LIVE_PT", "LIVE_GG"), T.w)


def configs():
    for unit in ["side", "fs", "setup"]:
        for start in [600, 630, 660]:
            for k in [1, 2]:
                for res in [0.0, 0.5]:
                    yield dict(kind="learn", unit=unit, start=start, k=k, res=res)
    for mode in ["strict", "lenient"]:
        for start in [600, 630, 660]:
            for k in [1, 2]:
                for res in [0.0, 0.5]:
                    yield dict(kind="dir", unit=mode, start=start, k=k, res=res)
    for res in [0.0, 0.5]:
        yield dict(kind="reg1", unit="side", start=600, k=1, res=res)


ALLOWED = []


def weights(c):
    elig = (T.m >= c["start"]) & T.cp.notna()
    s = T["st" if c["k"] == 1 else "st2"]
    if c["kind"] == "reg1":
        ok = np.where(T.side < 0, T.fo10 >= 0, T.fo10 < 0)
    elif c["kind"] == "dir":
        ok = (T.side * s == 1) if c["unit"] == "strict" else (T.side * s != -1)
    else:
        u = T[c["unit"]].astype(str)
        tr = T[elig & (T.w == "TRAIN")]
        g = tr.groupby([u[tr.index], s[tr.index]]).agg(n=("r", "size"), d=("date", "nunique"), a=("r", "mean")).reset_index()
        g.columns = ["u", "s", "n", "d", "a"]
        g["ok"] = (g.a > 0) & (g.n >= MINN[c["unit"]]) & (g.d >= 15)
        al = g[g.ok].groupby("u").s.apply(set).to_dict()
        al = {k: v for k, v in al.items() if len(v) < 3}
        for k_, v in al.items():
            ALLOWED.append(dict(cfg=name(c), u=k_, allowed=",".join({1: "UP", -1: "DOWN", 0: "MIXED"}[x] for x in sorted(v))))
        key = list(zip(u, s))
        gated = u.isin(al.keys())
        ok = np.array([(uu not in al) or (ss in al[uu]) for uu, ss in key])
        ok = ok | ~gated.values
    return np.where(elig & ~np.asarray(ok, bool), c["res"], 1.0)


def name(c):
    return f'{c["kind"]}:{c["unit"]}@{c["start"]//60}:{c["start"]%60:02d}/k{c["k"]}/{"off" if c["res"]==0 else "half"}'


def stats(df, w):
    r = df.r.values; wr = w * r
    day = pd.Series(wr).groupby(df.date.values).sum(); base = pd.Series(r).groupby(df.date.values).sum()
    dd = day - base
    mu = df.groupby("setup").r.transform("mean").values      # excess control: dropped scored vs setup's own mean
    ex = pd.Series((1 - w) * (mu - r)).groupby(df.date.values).sum()
    t = lambda x: x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 and x.std() > 0 else np.nan
    best = day.idxmax(); kept = w.sum(); kb = w[df.date.values == best].sum()
    cum = day.sort_index().cumsum(); mdd = (cum - cum.cummax()).min()
    tot = wr.sum()
    dt = pd.Series(wr).groupby(df.dtype.values).sum()
    return dict(totR=round(tot, 1), avgR=round(tot / kept, 4) if kept else np.nan, kept=round(kept / len(df), 3),
                avg_wo_best=round((tot - day.max()) / (kept - kb), 4) if kept > kb else np.nan,
                best_share=round(day.max() / tot, 2) if tot > 0 else np.nan, green=round((day > 0).mean(), 3),
                maxDD=round(mdd, 1), delta=round(dd.sum(), 1), t=round(t(dd), 2), ex=round(ex.sum(), 1), ex_t=round(t(ex), 2),
                R_up=round(dt.get("up", 0), 1), R_down=round(dt.get("down", 0), 1), R_quiet=round(dt.get("quiet", 0), 1), days=len(day))


rows = []
base_w = np.ones(len(T))
for c in [None] + list(configs()):
    w = base_w if c is None else weights(c)
    nm = "no-gate" if c is None else name(c)
    for bk in ["TRAIN", "VALID", "LIVE_PT", "LIVE_GG"]:
        i = (T.bk == bk).values
        rows.append(dict(cfg=nm, book=bk, **stats(T[i], w[i])))
    i = (T.w == "LIVE").values
    rows.append(dict(cfg=nm, book="LIVE_ALL", **stats(T[i], w[i])))
R = pd.DataFrame(rows); R.to_csv(HERE / "gates.csv", index=False)
pd.DataFrame(ALLOWED).to_csv(HERE / "allowed_states.csv", index=False)
W = R.pivot_table(index="cfg", columns="book", values=["t", "delta", "ex_t"]).round(2)
W.columns = [f"{a}_{b}" for a, b in W.columns]
W["pass"] = (W.t_VALID >= BAR) & (W.delta_TRAIN > 0) & (W.delta_LIVE_ALL > 0) & (W.ex_t_VALID >= 1.0)
W = W.sort_values("t_VALID", ascending=False); W.to_csv(HERE / "gates_summary.csv")
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 100)
print("bar", round(BAR, 2)); print(W[["delta_TRAIN", "t_TRAIN", "delta_VALID", "t_VALID", "ex_t_TRAIN", "ex_t_VALID", "delta_LIVE_ALL", "t_LIVE_ALL", "delta_LIVE_PT", "t_LIVE_PT", "pass"]].to_string())
