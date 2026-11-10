"""Blocks C and E (PLAN.md) on the 2-year lab trade lists (bt_lab1104, production costs, locked block absent) with entry-bar
features from the lab frames (dist_lod_atr / dist_hod_atr; QQQ distance from its low) and the lab context table (SPY
from-open % at the entry bar).
C (FB1 rework, lineage 4 -> 8): guard shorts near the session low only when SPY from-open >= -0.25% (C1 0.15 ATR, C2 0.10,
  C3 0.25, C4 C1 + QQQ within 0.15 ATR of its low). Delta = R of the guarded trades removed vs their setup mean (excess).
E (new lineage sat1107-range-extreme, N = 4): range-tape extremes, first entry per symbol-day: E1a/b longs within 0.15 / 0.25
  ATR of the low, E2a/b shorts within 0.15 / 0.25 ATR of the high, |SPY from-open| <= 0.25%; baseline = first same-side lab
  entry per symbol-day in the same tape.
Usage: python c_e.py      Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib
from mcf.research import gates as G
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; SPLIT = "2025-09-01"
T = pd.concat([pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet"))], ignore_index=True)
T["date"] = T.date.astype(str); assert not T.date.between(*lib.LOCKED).any()
F, C = [], []
for m in lib.months():
    f = lib.load_month(m, columns=["symbol", "date", "tod", "dist_lod_atr", "dist_hod_atr"]); f["date"] = f.date.astype(str); F.append(f)
    c = lib.load_context(m)[["date", "tod", "spy_fo"]]; c["date"] = c.date.astype(str); C.append(c)
F = pd.concat(F, ignore_index=True); C = pd.concat(C, ignore_index=True)
Q = F[F.symbol == "QQQ"][["date", "tod", "dist_lod_atr"]].rename(columns={"dist_lod_atr": "q_lod"})
T = T.merge(F, on=["symbol", "date", "tod"], how="left").merge(Q, on=["date", "tod"], how="left").merge(C, on=["date", "tod"], how="left")
dly = lib.daily(); dly["date"] = dly.date.astype(str); spy = dly[dly.symbol == "SPY"].set_index("date")
oc = (spy.close / spy.open - 1) * 100
T["dtype"] = T.date.map(pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index))
REG = G.session_regimes(dly[["date", "open", "close"]]); T["reg"] = T.date.map(REG.regime)
T["split"] = np.where(T.date < SPLIT, "train", "valid")
T["ex"] = T.r - T.groupby(["setup", "split"]).r.transform("mean"); T["fam"] = T.setup.str.split("-").str[0]
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
pr(f"trades {len(T)}, setups {T.setup.nunique()}, sessions {T.date.nunique()} {T.date.min()}..{T.date.max()} (locked block absent); "
   f"coverage dist {T.dist_lod_atr.notna().mean():.1%}, spy_fo {T.spy_fo.notna().mean():.1%}")
dt = lambda x: (np.mean(x) / np.std(x, ddof=1) * np.sqrt(len(x))) if len(x) > 2 and np.std(x, ddof=1) > 0 else np.nan

# ---------------- Block C
BAR_C = G.t_required(8); S_ = T[T.side == -1].copy(); rows = []
CFG = {"C1 dist_lod<=0.15 & SPY fo>=-0.25%": (S_.dist_lod_atr <= 0.15) & (S_.spy_fo >= -0.25),
       "C2 dist_lod<=0.10 & SPY fo>=-0.25%": (S_.dist_lod_atr <= 0.10) & (S_.spy_fo >= -0.25),
       "C3 dist_lod<=0.25 & SPY fo>=-0.25%": (S_.dist_lod_atr <= 0.25) & (S_.spy_fo >= -0.25),
       "C4 C1 & QQQ dist_lod<=0.15": (S_.dist_lod_atr <= 0.15) & (S_.spy_fo >= -0.25) & (S_.q_lod <= 0.15)}
for name, A in CFG.items():
    A = A.fillna(False).to_numpy(); x = S_.assign(dv=np.where(A, -S_.ex, 0.0))
    res = {}
    for sp in ("train", "valid"):
        y = x[x.split == sp]; d = y.groupby("date").dv.sum(); res[sp] = (d.sum(), dt(d.to_numpy()), int(A[(x.split == sp).to_numpy()].sum()))
    fam = x[A].groupby("fam").ex.agg(["size", "mean"]); helped = int((fam["mean"] < 0).sum()); harmed = int((fam["mean"] > 0).sum())
    sfx = x[A].groupby("setup").ex.sum(); s_help, s_harm = int((sfx < 0).sum()), int((sfx > 0).sum())
    byd = x.groupby("dtype").dv.sum(); byr = x.groupby("reg").dv.sum()
    top = S_.r >= S_.r.quantile(0.9); keep_top = 1 - A[top.to_numpy()].mean()
    ok = res["valid"][1] >= BAR_C and res["train"][0] > 0 and harmed <= 2 * helped and not (byr.get("up", 0) < 0 and byr.get("down", 0) < 0)
    rows.append(dict(config=name, blocked=int(A.sum()), share=A.mean(), blocked_raw=S_.r[A].mean(), blocked_ex=S_.ex[A].mean(),
                     train_d=res["train"][0], train_t=res["train"][1], valid_d=res["valid"][0], valid_t=res["valid"][1],
                     spy_up=byd.get("up", 0), spy_down=byd.get("down", 0), spy_quiet=byd.get("quiet", 0), reg_up=byr.get("up", 0), reg_down=byr.get("down", 0),
                     fam_helped=helped, fam_harmed=harmed, setups_helped=s_help, setups_harmed=s_harm,
                     setups_harmed_R=sfx[sfx > 0].sum() * -1, setups_helped_R=sfx[sfx < 0].sum() * -1, keep_top=keep_top, passes=bool(ok)))
DC = pd.DataFrame(rows); DC.round(4).to_csv(HERE / "c_results.csv", index=False)
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
pr(f"\n## Block C (FB1 rework; bar {BAR_C:.2f}, N 8; delta = R gained by removing the guarded shorts, vs setup mean)\n" + DC.round(3).to_string())

# ---------------- Block E
B90 = max(1.35, 0.9 * G.t_required(4)); rows = []
tape = T.spy_fo.abs() <= 0.25
def first(df): return df.sort_values(["date", "symbol", "tod"]).drop_duplicates(["date", "symbol"])
EC = {"E1a long dist_lod<=0.15": (1, T.dist_lod_atr <= 0.15), "E1b long dist_lod<=0.25": (1, T.dist_lod_atr <= 0.25),
      "E2a short dist_hod<=0.15": (-1, T.dist_hod_atr <= 0.15), "E2b short dist_hod<=0.25": (-1, T.dist_hod_atr <= 0.25)}
for name, (sd, cond) in EC.items():
    base = first(T[(T.side == sd) & tape]); k = first(T[(T.side == sd) & tape & cond.fillna(False)])
    s = G.summary(k[["date", "r"]]); rg = G.regime_split(k[["date", "r"]], REG)
    wf = G.walk_forward(k[["date", "r"]], exclude_months=lib.LOCKED_MONTHS); dty = k.groupby("dtype").r.mean()
    g = k.groupby("date").r.sum(); share = g.max() / g.sum() if g.sum() > 0 else np.nan
    sb = G.summary(base[["date", "r"]])
    ok = (s.get("t") or -9) >= B90 and rg["pass"] and (wf["share_positive"] or 0) >= 0.54 and s["exp_r"] > sb["exp_r"]
    rows.append(dict(config=name, n=s["n"], days=s["days"], per_sess=s["n"] / max(1, T.date.nunique()), exp_r=s["exp_r"], t=s["t"], wo_best=s["ex_best_day"],
                     best_share=share, train=k[k.split == "train"].r.mean(), valid=k[k.split == "valid"].r.mean(),
                     reg_up=rg["up"].get("exp_r"), reg_flat=rg["flat"].get("exp_r"), reg_down=rg["down"].get("exp_r"),
                     spy_up=dty.get("up"), spy_down=dty.get("down"), spy_quiet=dty.get("quiet"), wf=wf["share_positive"],
                     baseline=sb["exp_r"], excess=s["exp_r"] - sb["exp_r"], passes=bool(ok)))
DE = pd.DataFrame(rows); DE.round(4).to_csv(HERE / "e_results.csv", index=False)
pr(f"\n## Block E (range-tape extremes; Testing bar t >= {B90:.2f}, N 4; first entry per symbol-day; baseline = same side, same tape)\n" + DE.round(3).to_string())
pr("\nEducational only - not financial advice."); (HERE / "ce_out.txt").write_text("\n".join(P) + "\n")
