"""Score the 87 pre-declared configurations (PLAN.md) on the open history superset (build.py). Writes results.csv (every
configuration, counted), candidates.csv (the PLAN candidate rule + every reported check) and scan_out.txt.
Usage: python scan.py <scratch_hist>. Educational only - not financial advice."""
import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research import gates as G  # noqa: E402
from research.history2y import lib  # noqa: E402

SCR = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
S = pd.read_parquet(SCR / "superset.parquet")
B = pd.read_parquet(SCR / "base.parquet")
S["date"] = pd.to_datetime(S.date).dt.date
B["date"] = pd.to_datetime(B.date).dt.date
GEOS = [c[2:] for c in S.columns if c.startswith("R_")]
S = S.merge(B.rename(columns={f"R_{g}": f"B_{g}" for g in GEOS}), on=["date", "tod"], how="left")
S = S.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
assert not ((S.date.astype(str) >= "2024-11-01") & (S.date.astype(str) <= "2025-02-28")).any()
dstr = S.date.astype(str).to_numpy()
TRAIN = dstr < "2026-01-01"
dcode, dates = pd.factorize(S.date)
ND = len(dates)
symday = pd.factorize(S.symbol.astype(str) + "|" + S.date.astype(str))[0]
tod = S.tod.to_numpy(int)
barix = ((tod // 100) * 60 + tod % 100 - 570) // 5
bdates = B.date.astype(str)
NSESS = {"tr": int((bdates < "2026-01-01").groupby(B.date).first().sum()), "va": int((bdates >= "2026-01-01").groupby(B.date).first().sum())}
NSESS["all"] = NSESS["tr"] + NSESS["va"]
col = lambda k: S[k].to_numpy(float)  # noqa: E731
heat, bp, rsi5, gap, vw, fo, adv = (col(k) for k in ("heat", "buyPressure", "rsi5", "gap", "vwapDistPct", "fromOpen", "adv20"))
qqq, spy, brd, brdo = col("qqq_fo"), col("spy_fo"), col("breadth"), col("breadth_open")
REG = lib.regimes()
reg = S.date.map(REG["regime"]).to_numpy()
dl = lib.daily()
qd = dl[dl.symbol == "QQQ"].set_index("date")
qday = (qd.close / qd.open - 1) * 100
qdc = S.date.map(qday).to_numpy(float)


def W(a, b):
    return (tod >= a) & (tod < b) if b < 1500 else (tod >= a) & (tod <= b)


with np.errstate(invalid="ignore"):
    CORE = (heat <= -30) & (bp < -0.25) & (rsi5 > 70)
    K = {"win1100-1500": W(1100, 1500), "win1015-1500": W(1015, 1500), "qqq<0": qqq < 0, "spy<0": spy < 0, "gap<=0": gap <= 0,
         "vwap<0": vw < 0, "adv>=350M": adv >= 350e6, "bpband": bp > -0.5}
    FD, WW = W(950, 1500), W(950, 1100)
    cfgs = []  # (name, block, mask, geom, refire)
    cfgs += [("P-W", "P", CORE & WW, "t1s1", False), ("P-FD", "P", CORE & FD, "t1s1", False)]
    for a, b in [(950, 1015), (1015, 1100), (1100, 1300), (1300, 1500), (1100, 1500), (1015, 1500)]:
        cfgs.append((f"win{a}-{b}", "A", CORE & W(a, b), "t1s1", False))
    ctx = {"qqq<0": qqq < 0, "qqq<-0.25": qqq < -0.25, "spy<0": spy < 0, "breadth<0.5": brd < 0.5, "breadth_open<0.5": brdo < 0.5,
           "qqq<0&spy<0": (qqq < 0) & (spy < 0)}
    for k, v in ctx.items():
        cfgs.append((f"FD {k}", "B", CORE & FD & v, "t1s1", False))
    for k in ("qqq<0", "spy<0", "breadth_open<0.5"):
        cfgs.append((f"W {k}", "B", CORE & WW & ctx[k], "t1s1", False))
    base_nr = (heat <= -30) & (bp < -0.25)
    th = {"rsi5>60": (heat <= -30) & (bp < -0.25) & (rsi5 > 60), "rsi5>80": base_nr & (rsi5 > 80),
          "bp<-0.35": (heat <= -30) & (bp < -0.35) & (rsi5 > 70), "bp<-0.15": (heat <= -30) & (bp < -0.15) & (rsi5 > 70),
          "bpband": CORE & (bp > -0.5), "heat<=-40": (heat <= -40) & (bp < -0.25) & (rsi5 > 70)}
    for k, v in th.items():
        cfgs.append((f"FD {k}", "C", v & FD, "t1s1", False))
    for k, v in {"gap<=0": gap <= 0, "gap<1": gap < 1, "vwap<0": vw < 0, "fo<0": fo < 0}.items():
        cfgs.append((f"FD {k}", "D", CORE & FD & v, "t1s1", False))
    for k, v in {"adv>=200M": adv >= 200e6, "adv>=350M": adv >= 350e6, "adv>=1B": adv >= 1e9}.items():
        cfgs.append((f"FD {k}", "E", CORE & FD & v, "t1s1", False))
    for g in ("t05s1", "t1s05", "t05s05", "hold", "holdtr", "r0.1875", "r0.375", "r0.5", "ts30", "ts60"):
        cfgs.append((f"FD {g}", "F", CORE & FD, g, False))
    for g in ("t05s1", "t05s05", "holdtr"):
        cfgs.append((f"W {g}", "F", CORE & WW, g, False))
    cfgs.append(("FD refire", "G", CORE & FD, "t1s1", True))
    for a, b in itertools.combinations(K, 2):
        if a.startswith("win") and b.startswith("win"):
            continue
        m = CORE & K[a] & K[b]
        if not (a.startswith("win") or b.startswith("win")):
            m &= FD
        cfgs.append((f"{a} & {b}", "H", m, "t1s1", False))
    for a in K:
        for g in ("t05s1", "holdtr"):
            m = CORE & K[a] & (FD if not a.startswith("win") else True)
            cfgs.append((f"{a} & {g}", "H", m, g, False))
assert len(cfgs) == 87, len(cfgs)
N = len(cfgs)
BAR = max(1.5, math.sqrt(2 * math.log(N)))
BAR_LIN = math.sqrt(2 * math.log(133_904 + N))


def pick(m, g, refire):
    m = m & np.isfinite(S[f"R_{g}"].to_numpy(float))
    idx = np.flatnonzero(m)
    if not len(idx):
        return idx
    k = symday[idx]
    if not refire:
        return idx[np.r_[True, k[1:] != k[:-1]]]
    bi = barix[idx]
    newrun = np.r_[True, (k[1:] != k[:-1]) | (bi[1:] - bi[:-1] != 1)]
    rid = np.cumsum(newrun) - 1
    off = np.arange(len(idx)) - np.flatnonzero(newrun)[rid]
    return idx[off % 2 == 0]


def dstat(r, d):
    n = len(r)
    if n < 2:
        return n, (float(r.mean()) if n else np.nan), np.nan
    mu = r.mean()
    gs = np.bincount(d, weights=r, minlength=ND)
    gn = np.bincount(d, minlength=ND)
    se = np.sqrt(((gs - gn * mu) ** 2).sum()) / n
    return n, float(mu), float(mu / se) if se > 0 else np.nan


rows, IDX = [], {}
for name, blk, m, g, rf in cfgs:
    idx = pick(m, g, rf)
    IDX[name] = (idx, g)
    r = S[f"R_{g}"].to_numpy(float)[idx]
    ex = r - S[f"B_{g}"].to_numpy(float)[idx]
    d, tr = dcode[idx], TRAIN[idx]
    o = {"config": name, "block": blk, "geom": g, "refire": rf}
    for lab, sel in (("tr", tr), ("va", ~tr), ("all", np.ones(len(idx), bool))):
        n, mu, t = dstat(r[sel], d[sel])
        _, xm, xt = dstat(ex[sel], d[sel])
        o.update({f"n_{lab}": n, f"exp_{lab}": mu, f"t_{lab}": t, f"xs_{lab}": xm, f"xt_{lab}": xt,
                  f"tpd_{lab}": n / NSESS[lab]})
    for k in ("up", "flat", "down"):
        s = reg[idx] == k
        o[f"exp_{k}"] = float(r[s].mean()) if s.any() else np.nan
        o[f"n_{k}"] = int(s.sum())
    o["exp_qqqday_up"] = float(r[qdc[idx] > 0].mean()) if (qdc[idx] > 0).any() else np.nan
    o["exp_qqqday_dn"] = float(r[qdc[idx] <= 0].mean()) if (qdc[idx] <= 0).any() else np.nan
    if len(idx):
        dd = pd.Series(r).groupby(d).sum()
        o["exp_ex_best_day"] = float((r.sum() - dd.max()) / (len(r) - (d == dd.idxmax()).sum()))
        tdf = pd.DataFrame({"date": S.date.to_numpy()[idx], "r": r})
        wf = G.walk_forward(tdf, exclude_months=lib.LOCKED_MONTHS)
        o["wf_share"] = wf.get("share_positive", np.nan)
    rows.append(o)
R = pd.DataFrame(rows)
P = R.set_index("config").loc[["P-W", "P-FD"]]
ptr, pva = P.exp_tr.max(), P.exp_va.max()
R["beats_parents"] = (R.exp_tr > ptr) & (R.exp_va > pva)
R["pos_tr_va"] = (R.exp_tr > 0) & (R.exp_va > 0)

# neighbours (PLAN)
NB = {"win950-1015": ["win1015-1100"], "win1015-1100": ["win950-1015", "win1100-1300"], "win1100-1300": ["win1015-1100", "win1300-1500"],
      "win1300-1500": ["win1100-1300"], "win1100-1500": ["win1015-1500", "win1100-1300", "win1300-1500"],
      "win1015-1500": ["win1100-1500", "P-FD"],
      "FD qqq<0": ["FD qqq<-0.25", "FD spy<0", "FD qqq<0&spy<0"], "FD qqq<-0.25": ["FD qqq<0"], "FD spy<0": ["FD qqq<0", "FD qqq<0&spy<0"],
      "FD qqq<0&spy<0": ["FD qqq<0", "FD spy<0"], "FD breadth<0.5": ["FD breadth_open<0.5"], "FD breadth_open<0.5": ["FD breadth<0.5"],
      "W qqq<0": ["W spy<0"], "W spy<0": ["W qqq<0"], "W breadth_open<0.5": ["W qqq<0"],
      "FD rsi5>60": ["P-FD"], "FD rsi5>80": ["P-FD"], "FD bp<-0.35": ["P-FD"], "FD bp<-0.15": ["P-FD"], "FD bpband": ["FD bp<-0.35", "P-FD"],
      "FD heat<=-40": ["P-FD"], "FD gap<=0": ["FD gap<1"], "FD gap<1": ["FD gap<=0", "P-FD"], "FD vwap<0": ["FD fo<0"], "FD fo<0": ["FD vwap<0"],
      "FD adv>=200M": ["FD adv>=350M", "P-FD"], "FD adv>=350M": ["FD adv>=200M", "FD adv>=1B"], "FD adv>=1B": ["FD adv>=350M"],
      "FD t05s1": ["FD t05s05"], "FD t05s05": ["FD t05s1"], "FD t1s05": ["FD t05s05"], "FD hold": ["FD holdtr"], "FD holdtr": ["FD hold"],
      "FD r0.1875": ["P-FD"], "FD r0.375": ["FD r0.5", "P-FD"], "FD r0.5": ["FD r0.375"], "FD ts30": ["FD ts60"], "FD ts60": ["FD ts30"],
      "W t05s1": ["W t05s05"], "W t05s05": ["W t05s1"], "W holdtr": ["W t05s1"], "FD refire": ["P-FD"]}
KN = {"win1100-1500": "win1100-1500", "win1015-1500": "win1015-1500", "qqq<0": "FD qqq<0", "spy<0": "FD spy<0", "gap<=0": "FD gap<=0",
      "vwap<0": "FD vwap<0", "adv>=350M": "FD adv>=350M", "bpband": "FD bpband", "t05s1": "FD t05s1", "holdtr": "FD holdtr"}
for c in R.config:
    if " & " in c:
        a, b = c.split(" & ")
        NB[c] = [KN[a], KN[b]]
pos = dict(zip(R.config, R.pos_tr_va))
R["plateau"] = [np.mean([pos.get(x, False) for x in NB.get(c, [])]) if NB.get(c) else np.nan for c in R.config]
R["candidate"] = R.pos_tr_va & R.beats_parents & (R.t_va >= 1.5) & (R.n_va >= 100) & (R.plateau >= 0.5)
R["clears_study_bar"] = R.candidate & (R.t_all >= BAR)
R["clears_lineage_bar"] = R.candidate & (R.t_all >= BAR_LIN)
R.to_csv(HERE / "results.csv", index=False, float_format="%.4f")

# de-duplicate candidates by trade overlap
C = R[R.candidate].sort_values(["exp_va", "t_va"], ascending=False)
keep = []
for c in C.config:
    s = set(IDX[c][0])
    if all(len(s & set(IDX[k][0])) / max(1, min(len(s), len(IDX[k][0]))) <= 0.6 for k in keep):
        keep.append(c)
C["dedup_keep"] = C.config.isin(keep)
C.to_csv(HERE / "candidates.csv", index=False, float_format="%.4f")
# sanity: simulator t1s1 vs frame outcome + prod_r on the parent FD
i = IDX["P-FD"][0]
chk = f"sanity P-FD: sim t1s1 {np.nanmean(S.R_t1s1.to_numpy()[i]):+.4f}R vs frame+prod_r {np.nanmean(S.prod_t1s1.to_numpy()[i]):+.4f}R (n {len(i)})"
show = ["config", "geom", "n_tr", "exp_tr", "t_tr", "n_va", "exp_va", "t_va", "t_all", "tpd_va", "xs_all", "xt_all", "exp_up", "exp_flat",
        "exp_down", "wf_share", "plateau", "candidate"]
txt = [f"configs {N} | study bar {BAR:.2f} | lineage bar {BAR_LIN:.2f} | sessions tr {NSESS['tr']} va {NSESS['va']}", chk,
       "\nALL (sorted by valid exp):", R.sort_values("exp_va", ascending=False)[show].round(3).to_string(index=False),
       "\nCANDIDATES:", C[show + ["dedup_keep", "clears_study_bar", "clears_lineage_bar"]].round(3).to_string(index=False)]
(HERE / "scan_out.txt").write_text("Educational only - not financial advice.\n" + "\n".join(txt) + "\n")
print("\n".join(txt))
