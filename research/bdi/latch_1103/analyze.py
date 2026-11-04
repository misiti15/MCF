"""latch_1103 scoring of the pre-registered categorizers (PLAN.md) on the two-year trade lists (bt_all.py) and on live
(live.py). Usage: python analyze.py <scratch>  -> results.csv, splits.csv, live_cells.csv, setup_props.csv, counts.json,
out.txt here. Educational only - not financial advice."""
import json, math, os, re, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/MCF/research/history2y")
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
import lib  # noqa: E402
from latch import sim_day, next_loss_stats, LEVELS  # noqa: E402

S = Path(sys.argv[1]); TRAIN_END = "2026-02-28"
OUT = open(HERE / "out.txt", "w")
def P(*a):
    print(*a); print(*a, file=OUT, flush=True)

# ---------- setup-days ----------
bt = pd.concat([pd.read_parquet(f) for f in sorted((S / "bt").glob("sig_*.parquet"))], ignore_index=True)
bt["date"] = bt.date.astype(str)
d_ = pd.to_datetime(bt.date).dt.date
assert not ((d_ >= pd.Timestamp("2024-11-01").date()) & (d_ <= pd.Timestamp("2025-02-28").date())).any()
bt = bt.sort_values(["setup", "date", "tod", "symbol"], kind="mergesort").reset_index(drop=True)
bt["split"] = np.where(bt.date <= TRAIN_END, "train", "valid")
rows, pairs, ac = [], [], []
def caps(sym, en, ex, per_sym=3, per_setup=30):
    """Account caps (PLAN amendment 1): <= 3 open lots per symbol, <= 30 open positions per setup."""
    keep = np.zeros(len(en), bool)
    for i in range(len(en)):
        o = keep[:i] & (ex[:i] > en[i])
        if o.sum() < per_setup and (o & (sym[:i] == sym[i])).sum() < per_sym:
            keep[i] = True
    return keep
kept = []
for (su, d), g in bt.groupby(["setup", "date"], sort=False):
    k = caps(g.symbol.to_numpy(), g.tod.to_numpy(), g.xtod.to_numpy())
    g = g[k]; kept.append(g)
    r, en, ex = g.r.to_numpy(float), g.tod.to_numpy(), g.xtod.to_numpy()
    rec = dict(setup=su, date=d, side=int(g.side.iloc[0]), n=len(r), r_off=float(r.sum()))
    for L in LEVELS:
        rl, nb, tl = sim_day(r, en, ex, L)
        rec[f"d_{L}"] = rl - rec["r_off"]; rec[f"lat_{L}"] = tl is not None; rec[f"tl_{L}"] = tl if tl is not None else -1; rec[f"nb_{L}"] = nb or 0
    rows.append(rec)
    if d <= TRAIN_END:
        for c2, lj in next_loss_stats(r, en, ex):
            pairs.append((su, c2, lj))
        for i in range(len(r) - 1):
            ac.append((su, r[i], r[i + 1]))
bt = pd.concat(kept, ignore_index=True)
SD = pd.DataFrame(rows); SD["split"] = np.where(SD.date <= TRAIN_END, "train", "valid")
# control (PLAN amendment 2): the part of the delta NOT explained by the setup's own average R on that split
bt["split"] = np.where(bt.date <= TRAIN_END, "train", "valid")
MU = bt.groupby(["setup", "split"]).r.mean()
mu = MU.reindex(pd.MultiIndex.from_arrays([SD.setup, SD.split])).to_numpy()
for L in LEVELS:
    SD[f"x_{L}"] = SD[f"d_{L}"] + SD[f"nb_{L}"] * mu
SD.to_parquet(S / "setup_days.parquet")

# ---------- context (SPY vs open at latch time; session type) ----------
ctx = pd.concat([lib.load_context(m)[["date", "tod", "spy_fo"]] for m in lib.months() if m not in lib.LOCKED_MONTHS], ignore_index=True)
ctx["date"] = ctx.date.astype(str)
last = ctx.sort_values("tod").groupby("date").spy_fo.last()
tr_abs = last[last.index <= TRAIN_END].abs()
q1, q2 = tr_abs.quantile([1 / 3, 2 / 3])
stype = pd.Series(np.where(last.abs() >= q2, "trend", np.where(last.abs() <= q1, "quiet", "middle")), index=last.index)
CX = ctx.set_index(["date", "tod"]).spy_fo

# ---------- setup properties (TRAIN only) ----------
inv = pd.read_csv(HERE / "setups.csv")
tr = bt[bt.split == "train"]
props = tr.groupby("setup").agg(n_tr=("r", "size"), win=("r", lambda x: (x > 0).mean()), avg_r=("r", "mean"))
props["per_day"] = tr.groupby("setup").size() / tr.groupby("setup").date.nunique()
A = pd.DataFrame(ac, columns=["setup", "a", "b"])
props["rho"] = A.groupby("setup").apply(lambda g: g.a.corr(g.b) if len(g) >= 20 else np.nan)
props["n_ac"] = A.groupby("setup").size()
Pq = pd.DataFrame(pairs, columns=["setup", "c2", "lj"])
pl = tr.assign(l=tr.r < 0).groupby("setup").l.mean()
g2 = Pq[Pq.c2].groupby("setup").agg(n2=("lj", "size"), p2=("lj", "mean"))
props = props.join(g2).join(pl.rename("p_loss"))
props["excess2"] = np.where(props.n2 >= 20, props.p2 - props.p_loss, np.nan)
props["own_tr_d2"] = SD[SD.split == "train"].groupby("setup")["d_2.0"].sum()
props = props.join(inv.set_index("setup")[["account", "geom", "w_hi", "side"]])

FAM = {"MF", "RW", "NS", "ST", "CWT", "L3", "GEN"}
def family(n):
    p = re.match(r"[A-Za-z]+", n).group(0); p = "L3" if p == "L" else p
    return p if p in FAM else "other"
KW = [("reclaim", ["reclaim", "vwapx", "failbrk", "failed"]),
      ("fade", ["rsi5pop", "rsi5hi", "overbought", "oversold", "exhaustion", "fade", "bounce", "flush", "dip", "stretch",
                "rsimidhi", "rsi50dn", "ordn", "rsi5up", "up3", "-lh-", "backside"]),
      ("breakout", ["brk", "break", "slope", "emadn", "volspike", "flowsell", "coil", "flag", "thrust", "trend", "momentum", "vwaploss"])]
def style(n):
    s = n.lower()
    for k, ws in KW:
        if any(w in s for w in ws):
            return k
    return "other"
def geomc(g):
    return {"t1s05": "tgt>stop", "t05s1": "tgt<stop"}.get(g, "tgt=stop")
def wind(h):
    return "open-only" if h <= 1100 else ("full-day" if h >= 1400 else "mid")
C = pd.DataFrame(index=props.index)
C["side"] = np.where(props.side == "long", "long", "short")
C["family"] = [family(n) for n in props.index]
C["style"] = [style(n) for n in props.index]
C["freq"] = np.where(props.per_day >= 2.0, "high", "low")
C["geom"] = props.geom.map(geomc)
C["winrate"] = pd.cut(props.win, [-1, 0.45, 0.55, 2], right=False, labels=["<45%", "45-55%", ">=55%"]).astype(str)
C["window"] = props.w_hi.map(wind)
C["autocorr"] = np.where(props.rho.isna(), "n/a", np.where(props.rho > 0, "rho>0 (cluster)", "rho<=0"))
C["p_loss_2L"] = np.where(props.excess2.isna(), "n/a", np.where(props.excess2 > 0.05, "excess>+5pp", "excess<=+5pp"))
C["own_train"] = np.where(props.own_tr_d2 > 0, "latch helped on TRAIN", "latch hurt/neutral on TRAIN")
props.join(C, rsuffix="_cat").to_csv(HERE / "setup_props.csv")
P("setups with trades:", len(props), " setup-days:", len(SD), " trades:", len(bt))
P("TRAIN rho median", round(props.rho.median(), 3), " share rho>0", round((props.rho > 0).mean(), 2),
  " excess2 median", round(props.excess2.median(), 3))

# ---------- scoring ----------
def score(sd, L, split):
    x = sd[sd.split == split]
    if not len(x):
        return {}
    dcol = f"d_{L}"; per = x.groupby("date")[dcol].sum()
    dates = per.index
    m, s, n = per.mean(), per.std(ddof=1), len(per)
    tot = per.sum(); best = per.idxmax() if tot >= 0 else per.idxmin()
    wo = per.drop(best)
    px = x.groupby("date")[f"x_{L}"].sum() if f"x_{L}" in x else None
    xs = dict(xtot=round(px.sum(), 2), xt=round(px.mean() / px.std(ddof=1) * math.sqrt(n), 2) if px is not None and px.std() > 0 else np.nan) if px is not None else {}
    return dict(**xs, n_days=n, n_sd=len(x), n_latched=int(x[f"lat_{L}"].sum()), tot=round(tot, 2),
                per_sd=round(tot / len(x), 4), per_latched=round(tot / max(1, x[f"lat_{L}"].sum()), 3),
                per_day=round(m, 3), t=round(m / s * math.sqrt(n), 2) if s > 0 else np.nan,
                per_day_wo_best=round(wo.mean(), 3), best_share=round(per[best] / tot, 2) if tot else np.nan)

res = []
SDc = SD.rename(columns={"side": "sgn"}).join(C, on="setup")
SDc["spy_at_latch"] = "n/a"
for L in LEVELS:
    pass
def spy_rel(row, L):
    if not row[f"lat_{L}"]:
        return "not latched"
    tl = int(row[f"tl_{L}"]); tl = min(1500, max(950, tl - tl % 5))
    v = CX.get((row.date, tl), np.nan)
    if not np.isfinite(v):
        return "n/a"
    return "SPY against side" if v * row.sgn < 0 else "SPY with side"
for L in LEVELS:
    res.append(dict(cat="ALL", cell="all", L=L, **{f"{k}_{sp}": v for sp in ("train", "valid") for k, v in score(SDc, L, sp).items()}))
    for cat in C.columns:
        for cell, g in SDc.groupby(cat):
            res.append(dict(cat=cat, cell=cell, L=L, **{f"{k}_{sp}": v for sp in ("train", "valid") for k, v in score(g, L, sp).items()}))
    sp_ = SDc.apply(lambda r: spy_rel(r, L), axis=1)
    for cell in ("SPY against side", "SPY with side"):
        g = SDc[sp_ == cell]
        res.append(dict(cat="spy_at_latch", cell=cell, L=L, **{f"{k}_{sp}": v for sp in ("train", "valid") for k, v in score(g, L, sp).items()}))
    st_ = SDc.date.map(stype)
    for cell in ("trend", "middle", "quiet"):
        res.append(dict(cat="diag_session", cell=cell, L=L, **{f"{k}_{sp}": v for sp in ("train", "valid") for k, v in score(SDc[st_ == cell], L, sp).items()}))
    # reversal diagnostic: latched with SPY-vs-open sign opposite to the session's close sign
    lat = SDc[SDc[f"lat_{L}"]].copy()
    v = [CX.get((d, min(1500, max(950, int(t) - int(t) % 5))), np.nan) for d, t in zip(lat.date, lat[f"tl_{L}"])]
    rev = np.sign(np.asarray(v)) != np.sign(lat.date.map(last).to_numpy())
    for cell, g in (("reversal after latch", lat[rev]), ("no reversal", lat[~rev])):
        res.append(dict(cat="diag_reversal", cell=cell, L=L, **{f"{k}_{sp}": v for sp in ("train", "valid") for k, v in score(g, L, sp).items()}))
R = pd.DataFrame(res); R.to_csv(HERE / "results.csv", index=False)
N = int(len(R)); BAR = max(1.5, math.sqrt(2 * math.log(N)))
P(f"configurations N={N} (levels x cells incl. ALL and diagnostics); bar t >= {BAR:.2f}")

# ---------- split tests: per date, mean delta per active setup-day in X minus in Y ----------
spl = []
for L in LEVELS:
    for cat in list(C.columns) + ["spy_at_latch"]:
        if cat == "spy_at_latch":
            lab = SDc.apply(lambda r: spy_rel(r, L), axis=1)
        else:
            lab = SDc[cat]
        cells = [c for c in lab.unique() if c not in ("n/a", "not latched")]
        for i, a in enumerate(sorted(cells)):
            for b in sorted(cells)[i + 1:]:
              for met in ("d", "x"):
                row = dict(cat=cat, X=a, Y=b, L=L, metric=met)
                for sp in ("train", "valid"):
                    m = SDc.split == sp
                    pa = SDc[m & (lab == a)].groupby("date")[f"{met}_{L}"].mean()
                    pb = SDc[m & (lab == b)].groupby("date")[f"{met}_{L}"].mean()
                    dd = (pa - pb).dropna()
                    row[f"diff_{sp}"] = round(dd.mean(), 4) if len(dd) else np.nan
                    row[f"t_{sp}"] = round(dd.mean() / dd.std(ddof=1) * math.sqrt(len(dd)), 2) if len(dd) > 2 and dd.std() > 0 else np.nan
                    row[f"days_{sp}"] = len(dd)
                spl.append(row)
SPL = pd.DataFrame(spl); SPL.to_csv(HERE / "splits.csv", index=False)
N_ALL = N + int((SPL.metric == "d").sum()); BAR_ALL = max(1.5, math.sqrt(2 * math.log(N_ALL)))
P(f"with the pairwise split contrasts: N={N_ALL}; bar t >= {BAR_ALL:.2f}")

# ---------- live by category ----------
LV = pd.read_parquet(S / "live_days.parquet")
cfgs = {}
for f in ("default.yaml", "account_testing.yaml", "account_testing2.yaml", "account_graveyard.yaml", "account_gen.yaml"):
    for k, v in (yaml.safe_load(open(f"/home/user/MCF/config/{f}")).get("strategies") or {}).items():
        cfgs.setdefault(k, v)
LC = LV.join(C.drop(columns=["side"]), on="setup")
LC["side_c"] = np.where(LC.side == 1, "long", "short")
LC["family"] = [family(n) for n in LC.setup]; LC["style"] = [style(n) for n in LC.setup]
LC["window"] = [wind(int((cfgs.get(n, {}).get("window") or [950, 1500])[1])) for n in LC.setup]
LC["split"] = "live"
_m = LC.groupby(["account", "setup"]).r_off.sum() / LC.groupby(["account", "setup"]).n.sum()
_mu = _m.reindex(pd.MultiIndex.from_arrays([LC.account, LC.setup])).to_numpy()
for L in LEVELS:
    LC[f"x_{L}"] = LC[f"d_{L}"] + LC[f"nb_{L}"] * _mu
lres = []
for L in LEVELS:
    for cat in ["side_c", "family", "style", "freq", "geom", "winrate", "window", "autocorr", "p_loss_2L", "own_train"]:
        for cell, g in LC.groupby(cat):
            s = score(g, L, "live")
            lres.append(dict(cat=cat.replace("side_c", "side"), cell=cell, L=L, **s))
    for acct, g in LC.groupby("account"):
        lres.append(dict(cat="account", cell=acct, L=L, **score(g, L, "live")))
    lres.append(dict(cat="ALL", cell="all", L=L, **score(LC, L, "live")))
LR = pd.DataFrame(lres); LR.to_csv(HERE / "live_cells.csv", index=False)
json.dump(dict(N=N, bar=round(BAR, 2), N_with_contrasts=N_ALL, bar_with_contrasts=round(BAR_ALL, 2), levels=list(LEVELS), cells_per_level=int(N / len(LEVELS)),
               setups=int(len(props)), setup_days=int(len(SD)), live_setup_days=int(len(LV))), open(HERE / "counts.json", "w"), indent=1)

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
cols = ["cat", "cell", "L", "xtot_train", "xt_train", "xtot_valid", "xt_valid", "n_sd_train", "n_latched_train", "tot_train", "per_latched_train", "t_train", "per_day_wo_best_train", "best_share_train",
        "n_sd_valid", "n_latched_valid", "tot_valid", "per_latched_valid", "t_valid", "per_day_wo_best_valid", "best_share_valid"]
P(R.reindex(columns=cols).to_string(index=False))
P(SPL.to_string(index=False))
P(LR[["cat", "cell", "L", "xtot", "xt", "n_sd", "n_latched", "tot", "per_latched", "t", "per_day_wo_best", "best_share"]].to_string(index=False))
