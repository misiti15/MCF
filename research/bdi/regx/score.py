"""REGX scoring (PLAN.md rules, fixed before scoring). Reads <scratch>/trades.parquet; writes table.csv, cells.csv,
summary_scheme.csv, summary_famside.csv, dash_live.csv, special_mf.csv next to this file.
Usage: python score.py <scratch>. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
SCH = ["DASH", "OC25", "VWAP", "COMP", "DAYT", "VOL", "BRD", "SECT"]
HIND = {"DASH", "OC25"}
DIRN = {"Bull": 1, "Bear": -1, "up": 1, "down": -1, "above": 1, "below": -1, "trend-up": 1, "trend-down": -1,
        "strong": 1, "weak": -1, "offense": 1, "defense": -1}
ELIG = {"TRAIN": (30, 10), "VALID": (30, 5), "LIVE": (10, 3)}
B = 1000
T = pd.read_parquet(S / "trades.parquet")
live = T[T.w == "LIVE"]
cnt = live.groupby("setup").size()
SETUPS = sorted(cnt[cnt >= 30].index)
accts = live.groupby("setup").acct.agg(lambda x: ",".join(sorted(set(x))))


def cellstats(x, s):
    x = x[x[s].notna()]
    out = {}
    for c, g in x.groupby(s):
        ds = g.groupby("date").r.sum()
        tot = ds.sum(); bd = ds.idxmax()
        rest = g[g.date != bd]
        out[c] = dict(n=len(g), days=g.date.nunique(), avg=g.r.mean(), wo_bd=rest.r.mean() if len(rest) else np.nan,
                      bd_share=(ds.max() / tot) if tot > 0 else np.nan, bd=bd)
    return out


def boot(x, s, b, w, seed=1105):
    """day-cluster bootstrap of avg(cell b) - avg(cell w); returns spread, se, t."""
    x = x[x[s].isin([b, w])]
    days = np.array(sorted(x.date.unique())); D = len(days)
    if D < 3:
        return np.nan, np.nan, np.nan
    di = pd.Index(days)
    def arr(c, f):
        g = x[x[s] == c].groupby("date").r.agg(f)
        a = np.zeros(D); a[di.get_indexer(g.index)] = g.values; return a
    sb, nb, sw, nw = arr(b, "sum"), arr(b, "size"), arr(w, "sum"), arr(w, "size")
    sp = sb.sum() / nb.sum() - sw.sum() / nw.sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, D, (B, D)); C = np.zeros((B, D)); np.add.at(C, (np.repeat(np.arange(B), D), idx.ravel()), 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        bs = (C @ sb) / (C @ nb) - (C @ sw) / (C @ nw)
    se = np.nanstd(bs)
    return sp, se, (sp / se if se > 0 else np.nan)


def elig(st, w):
    n, d = ELIG[w]
    return {c: v for c, v in st.items() if v["n"] >= n and v["days"] >= d}


rows, cellrows = [], []
for su in SETUPS:
    X = T[T.setup == su]
    side = X.side.mode().iloc[0]; fam = X.fam.iloc[0]
    has2y = (X.w == "TRAIN").sum() > 0
    for s in SCH:
        W = {w: X[X.w == w] for w in ["TRAIN", "VALID", "LIVE"]}
        st = {w: cellstats(W[w], s) for w in W}
        for w in st:
            for c, v in st[w].items():
                cellrows.append(dict(setup=su, scheme=s, w=w, cell=c, **{k: v[k] for k in ["n", "days", "avg", "wo_bd", "bd_share", "bd"]}))
        fitw = "TRAIN" if has2y else "LIVE"
        e = elig(st[fitw], fitw)
        r = dict(setup=su, side=side, fam=fam, accts=accts[su], live_n=int(cnt[su]), scheme=s, hindsight=s in HIND,
                 source="2-year TRAIN" if has2y else "live only")
        if len(e) < 2:
            r.update(verdict="weak", reason=f"too few eligible {fitw} cells ({len(e)})"); rows.append(r); continue
        best = max(e, key=lambda c: e[c]["avg"]); worst = min(e, key=lambda c: e[c]["avg"])
        r.update(best=best, worst=worst)
        for w in ["TRAIN", "VALID", "LIVE"]:
            ew = elig(st[w], w)
            for tag, c in (("best", best), ("worst", worst)):
                v = st[w].get(c)
                r[f"{w}_{tag}_avg"] = v["avg"] if v else np.nan
                r[f"{w}_{tag}_n"] = v["n"] if v else 0
                r[f"{w}_{tag}_wo_bd"] = v["wo_bd"] if v else np.nan
                r[f"{w}_{tag}_bd_share"] = v["bd_share"] if v else np.nan
            ok = best in ew and worst in ew
            r[f"{w}_ok"] = ok
            if ok:
                sp, se, t = boot(W[w], s, best, worst)
                r[f"{w}_spread"], r[f"{w}_t"] = sp, t
                r[f"{w}_spread_wo_bd"] = st[w][best]["wo_bd"] - st[w][worst]["wo_bd"]
            com = [c for c in e if c in ew]
            if len(com) >= 3 and w != fitw:
                r[f"{w}_spearman"] = spearmanr([e[c]["avg"] for c in com], [ew[c]["avg"] for c in com]).statistic
        # verdict
        if not has2y:
            r.update(verdict="weak", reason="live only (in-sample, no 2-year list)")
        else:
            tt, vok, lok = r.get("TRAIN_t", np.nan), r["VALID_ok"], r["LIVE_ok"]
            vs, vt = r.get("VALID_spread", np.nan), r.get("VALID_t", np.nan)
            ls, lt = r.get("LIVE_spread", np.nan), r.get("LIVE_t", np.nan)
            if vok and vs <= 0:
                r.update(verdict="false", reason="flips on VALID")
            elif lok and ls < 0 and lt <= -1.0 and not (vok and vt >= 1.0):
                r.update(verdict="false", reason="live contradicts (t<=-1), VALID not significant")
            elif tt >= 2.0 and vok and vt >= 1.0 and r["VALID_spread_wo_bd"] > 0 and (not lok or ls > 0):
                r.update(verdict="trustworthy", reason="TRAIN t>=2, VALID t>=1 (w/o best day too), live agrees" if lok else
                         "TRAIN t>=2, VALID t>=1 (w/o best day too), live cells too thin")
            else:
                why = []
                if not (tt >= 2.0): why.append(f"TRAIN t {tt:.2f}<2")
                if not vok: why.append("VALID cells thin")
                elif not (vt >= 1.0): why.append(f"VALID t {vt:.2f}<1")
                elif not (r["VALID_spread_wo_bd"] > 0): why.append("VALID carried by one day")
                if lok and ls <= 0: why.append("live disagrees")
                r.update(verdict="weak", reason="; ".join(why))
        r["dir_best"] = DIRN.get(best, 0)
        rows.append(r)

TB = pd.DataFrame(rows)
# flip between schemes (directional TRAIN/fit best cells)
fl = TB[TB.dir_best.fillna(0) != 0].groupby("setup").dir_best.agg(lambda x: (x > 0).any() and (x < 0).any())
TB["flip"] = TB.setup.map(fl).fillna(False)
# one-day flags
TB["one_day"] = (TB.get("VALID_best_bd_share") >= 0.5) | (TB.get("LIVE_best_bd_share") >= 0.5)
TB.to_csv(HERE / "table_full.csv", index=False)
cols = ["setup", "side", "fam", "accts", "live_n", "scheme", "hindsight", "source", "best", "worst",
        "TRAIN_best_avg", "TRAIN_worst_avg", "TRAIN_best_n", "TRAIN_worst_n", "TRAIN_t",
        "VALID_best_avg", "VALID_worst_avg", "VALID_best_n", "VALID_worst_n", "VALID_t", "VALID_spearman",
        "VALID_best_wo_bd", "VALID_worst_wo_bd", "VALID_best_bd_share",
        "LIVE_best_avg", "LIVE_worst_avg", "LIVE_best_n", "LIVE_worst_n", "LIVE_t", "LIVE_best_wo_bd", "LIVE_best_bd_share",
        "flip", "one_day", "verdict", "reason"]
for c in cols:
    if c not in TB: TB[c] = np.nan
TB[cols].round(3).to_csv(HERE / "table.csv", index=False)
pd.DataFrame(cellrows).round(4).to_csv(HERE / "cells.csv", index=False)

# summaries
def summ(g):
    v = g[g.source == "2-year TRAIN"]
    rated = v[v.best.notna()]
    return pd.Series(dict(rated=len(rated), trustworthy=(rated.verdict == "trustworthy").sum(), weak=(rated.verdict == "weak").sum(),
                          false=(rated.verdict == "false").sum(),
                          valid_tested=rated.VALID_ok.sum(), valid_pos=(rated.VALID_spread > 0).sum(),
                          valid_pos_share=(rated.VALID_spread > 0).sum() / max(rated.VALID_ok.sum(), 1),
                          live_tested=rated.LIVE_ok.sum(), live_pos=(rated.LIVE_spread > 0).sum(),
                          live_pos_share=(rated.LIVE_spread > 0).sum() / max(rated.LIVE_ok.sum(), 1),
                          med_valid_spearman=rated.VALID_spearman.median(), med_live_spearman=rated.LIVE_spearman.median(),
                          med_train_t=rated.TRAIN_t.median(), med_valid_t=rated.VALID_t.median()))
ss = TB.groupby("scheme").apply(summ).sort_values(["valid_pos_share", "med_valid_spearman"], ascending=False)
ss.round(3).to_csv(HERE / "summary_scheme.csv")
TB["famside"] = TB.fam + "/" + TB.side
fs = TB.groupby(["famside", "scheme"]).apply(summ).reset_index()
fs.round(3).to_csv(HERE / "summary_famside.csv", index=False)
sd = TB.groupby(["side", "scheme"]).apply(summ).reset_index()
sd.round(3).to_csv(HERE / "summary_side.csv", index=False)

# dashboard labels scored live
dj = json.loads(Path("/home/user/MCF/docs/live/regimes.json").read_text())["setups"]
dl = []
for su in SETUPS:
    if su not in dj: continue
    x = live[live.setup == su]; st = cellstats(T[(T.setup == su) & (T.w == "LIVE")], "DASH")
    b, w = dj[su]["best"], dj[su]["worst"]
    gb, gw = st.get(b), st.get(w)
    dl.append(dict(setup=su, dash_best=b, dash_worst=w, dash_class=dj[su]["class"],
                   live_best_avg=gb["avg"] if gb else np.nan, live_best_n=gb["n"] if gb else 0, live_best_days=gb["days"] if gb else 0,
                   live_worst_avg=gw["avg"] if gw else np.nan, live_worst_n=gw["n"] if gw else 0, live_worst_days=gw["days"] if gw else 0,
                   **{f"live_{c}": round(st[c]["avg"], 3) for c in st}, **{f"live_{c}_n": st[c]["n"] for c in st}))
DL = pd.DataFrame(dl); DL["holds"] = DL.live_best_avg > DL.live_worst_avg
DL.round(3).to_csv(HERE / "dash_live.csv", index=False)

# special look
sp = T[T.setup.isin(["MF4-h40-open-flowsell-FD", "MF2-open-rsimidhi-flowsell-FD"]) & T.date.isin(["2026-11-04", "2026-11-05"])]
sp[["setup", "acct", "date", "m", "r"] + SCH].to_csv(HERE / "special_mf.csv", index=False)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
print(len(SETUPS), "setups;", (TB.source == "2-year TRAIN").groupby(TB.setup).first().sum(), "with 2-year")
print(TB.groupby(["source", "verdict"]).size())
print(ss.round(3))
print(sd.round(3).to_string())
print("dash live holds:", DL.holds.sum(), "of", len(DL), "| both cells n>=10:", ((DL.live_best_n >= 10) & (DL.live_worst_n >= 10)).sum(),
      DL[(DL.live_best_n >= 10) & (DL.live_worst_n >= 10)].holds.sum())
