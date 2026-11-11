"""CONFIRM (plan PLAN.md, frozen before any score). python limex.py > limex_out.txt     Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
HERE = Path(__file__).resolve().parent; NY = "America/New_York"
TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
SPLIT = pd.Timestamp("2025-09-30").date(); N_FAM = 1962; T90 = round(max(1.35, .9 * G.t_required(N_FAM)), 2)
SL, BP, SX = 0.01, 1e-4, 0.02; KS = (0.10, 0.25); NW = 10
POOL = ["MF3-open-flowsell-rsi5hi", "MF5-flowsell-vwapup-rsi5hi", "MF2-open-rsimidhi-flowsell-FD", "NS4-pm-vwap-reclaim-oversold-short",
        "GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long", "NS5-sma50-flush-oversold-long", "ST4-emadn-long-am-t1s05-FD",
        "RW7-gapdn-bounce-early-short-FD", "RW1-gapdn-bounce-flowsell-short-FD", "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD",
        "CWT09-gapdn-bounce-g5-lowerhalf-short", "GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short",
        "GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long"]
L = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
L = L[L.setup.isin(POOL)].copy(); L["date"] = pd.to_datetime(L.date).dt.date; L["tod"] = L.tod.astype(int); L["symbol"] = L.symbol.astype(str)
missing = sorted(set(POOL) - set(L.setup)); print(f"pool: {L.setup.nunique()} of {len(POOL)} setups have 2y lists (missing: {missing}); trades {len(L)}")
parts = []
for m in sorted(pd.to_datetime(L.date).dt.strftime("%Y-%m").unique()):
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "gap"]); f["tod"] = f.tod.astype(int); f["symbol"] = f.symbol.astype(str)
    parts.append(L[pd.to_datetime(L.date).dt.strftime("%Y-%m") == m].merge(f, on=["symbol", "date", "tod"], how="left"))
L = pd.concat(parts, ignore_index=True).dropna(subset=["close", "atr_d"])

def walk(o, h, l, c, i0, e, s, D, U):
    """from index i0 (inclusive), stop-first; -> (exit px, kind 0 flat / 1 stop / 2 target)"""
    stop, tgt = e - s * D, e + s * U
    for i in range(i0, len(c)):
        if i > i0 and s * (o[i] - stop) <= 0: return o[i], 1
        if (s > 0 and l[i] <= stop) or (s < 0 and h[i] >= stop): return stop, 1
        if (s > 0 and h[i] >= tgt) or (s < 0 and l[i] <= tgt): return tgt, 2
    return c[-1], 0

def net(e, xp, kd, s, R, dn, ecost, tier):
    xcost = (0.0 if kd == 2 else SL + xp * BP) + (SX if kd == 1 else 0.0)
    g = s * (xp - e) / R
    return (g - tier * (ecost + xcost) / R) / dn, g / dn

def walk2(o, h, l, c, i0, fill, s, stop, tgt):
    for i in range(i0, len(c)):
        if i > i0 and s * (o[i] - stop) <= 0: return o[i], 1, i
        if (s > 0 and l[i] <= stop) or (s < 0 and h[i] >= stop): return stop, 1, i
        if (s > 0 and h[i] >= tgt) or (s < 0 and l[i] <= tgt): return tgt, 2, i
    return c[-1], 0, len(c) - 1

def atr_res(fill, xp, kd, s, atr, ecost, tier):
    xcost = (0.0 if kd == 2 else SL + xp * BP) + (SX if kd == 1 else 0.0)
    return (s * (xp - fill) - tier * (ecost + xcost)) / atr

out = []
for sym, g in L.groupby("symbol"):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"; ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    df.index = pd.DatetimeIndex(df.index).tz_convert(NY); df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = df.index.hour * 60 + df.index.minute; df = df[(mm >= 570) & (mm < 955)]
    byd = {d: x for d, x in df.groupby(df.index.date)}
    for r in g.itertuples(index=False):
        x = byd.get(r.date)
        if x is None: continue
        m_ = (x.index.hour * 60 + x.index.minute).to_numpy(); t0 = r.tod // 100 * 60 + r.tod % 100
        j = int(np.searchsorted(m_, t0))
        if j >= len(m_): continue
        o, h, l, c = (x[k].to_numpy(float)[j:] for k in ("open", "high", "low", "close"))
        s = int(r.side); e = float(r.close); atr = float(r.atr_d); R = .25 * atr; up, dn = G.GEOMK[r.geom]; D, U = dn * R, up * R
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0; mult = float(G.tod_cost_mult(np.array([r.tod]))[0])
        eb = o[0]; xp, kd, _ = walk2(o, h, l, c, 0, eb, s, eb - s * D, eb + s * U)
        row = dict(setup=r.setup, date=r.date, side=s, B=atr_res(eb, xp, kd, s, atr, (SL + eb * BP) * mult, tier))
        for k in KS:
            for lab_, sd in (("C", s), ("M", -s)):               # C = signal side, M = mirror (opposite side)
                trig = e + sd * k * D
                hit = np.flatnonzero((h[:NW] >= trig) if sd > 0 else (l[:NW] <= trig))
                if not len(hit):
                    row[f"{lab_}{k}"], row[f"{lab_}{k}_t"], row[f"{lab_}{k}_w"] = 0.0, 0, 0; continue
                i = int(hit[0]); fill = max(trig, o[i]) if sd > 0 else min(trig, o[i])
                stop, tgt = (e - sd * D, e + sd * U)
                xp2, kd2, ix_ = walk2(o, h, l, c, i, fill, sd, stop, tgt)
                ec = (SL + fill * BP) * mult + SX
                row[f"{lab_}{k}"] = atr_res(fill, xp2, kd2, sd, atr, ec, tier); row[f"{lab_}{k}_t"] = 1
                row[f"{lab_}{k}_w"] = int(kd2 == 1 and ix_ - i <= 1); row[f"{lab_}{k}_sb"] = int(kd2 == 1 and ix_ == i)
        out.append(row)
X = pd.DataFrame(out); X.to_csv(HERE / "confirm_trades.csv.gz", index=False)
D_ = lib.daily(); S = D_[D_.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
print(f"signals walked {len(X)}; baseline (market) {X.B.mean():+.4f} ATR/signal; family N {N_FAM}, BAR90 {T90}")
tt = lambda s_: round(s_.mean() / (s_.std(ddof=1) / np.sqrt(len(s_))), 2) if len(s_) > 2 and s_.std() > 0 else None
rows = []
rng = np.random.default_rng(20261111)
X["sd"] = X.setup + "|" + X.date.astype(str)
for k in KS:
    c, mcol = f"C{k}", f"M{k}"; trg = (X[f"{c}_t"] == 1).to_numpy()
    tim = X.assign(x=np.where(trg, X[c] - X.B, 0.0)).groupby("date").x.sum()          # Amendment 1: timing part
    skp = X.assign(x=np.where(~trg, -X.B, 0.0)).groupby("date").x.sum()               # skip part
    B = X.B.to_numpy(); exs = {}
    for key, ii in X.groupby("sd").indices.items():                                     # random same-share skip per setup-day
        kk = int((~trg[ii]).sum())
        if kk == 0: continue
        rnd = np.mean([-B[rng.choice(ii, kk, replace=False)].sum() for _ in range(200)])
        d0 = X.date.iloc[ii[0]]; exs[d0] = exs.get(d0, 0.0) + (-B[ii][~trg[ii]].sum() - rnd)
    exs = pd.Series(exs).reindex(tim.index, fill_value=0.0)
    mir = X.assign(x=X[c] - X[mcol]).groupby("date").x.sum()
    dd = pd.Series(tim.index, index=tim.index); ty = tim.groupby(tim.index.map(dtype)).sum()
    per = X[trg].assign(x=X[c] - X.B).groupby("setup").x.mean()
    rows.append(dict(config=f"CONFIRM-k{k}", trig=round(trg.mean(), 3), C_net_atr_trig=round(X.loc[trg, c].mean(), 4),
                     B_on_trig=round(X.loc[trg, "B"].mean(), 4), B_on_untrig=round(X.loc[~trg, "B"].mean(), 4),
                     timing=round(tim.sum(), 1), timing_t=tt(tim), train=round(tim[dd <= SPLIT].sum(), 1), valid=round(tim[dd > SPLIT].sum(), 1),
                     valid_t=tt(tim[dd > SPLIT]), wo_best=round(tim.drop(tim.idxmax()).sum(), 1),
                     up=round(ty.get("up", 0), 1), down=round(ty.get("down", 0), 1), quiet=round(ty.get("quiet", 0), 1),
                     skip_part=round(skp.sum(), 1), skip_excess=round(exs.sum(), 1), skip_excess_t=tt(exs),
                     vs_mirror=round(mir.sum(), 1), vs_mirror_t=tt(mir), mirror_net_atr_trig=round(X.loc[X[f"{mcol}_t"] == 1, mcol].mean(), 4),
                     whipsaw=round(X.loc[trg, f"{c}_w"].mean(), 3), stop_in_trigger_bar=round(X.loc[trg, f"{c}_sb"].mean(), 3),
                     better=int((per > 0).sum()), worse=int((per < 0).sum())))
R = pd.DataFrame(rows)
R["pass"] = ((R.timing_t >= T90) & (R.train > 0) & (R.valid > 0) & (R.wo_best > 0) & (R.better > R.worse) & (R.C_net_atr_trig > 0)
             & (R.vs_mirror > 0) & (R.vs_mirror_t >= 2))
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40); print(R.to_string(index=False))
print("\nunits: ATR. timing = sum over triggered signals of (C - market entry); skip_part = -market R of untriggered signals;"
      "\nskip_excess = vs a random same-share skip per setup-day; vs_mirror = C - opposite-side trigger. R-unit reward/risk is lower by design.")
R.to_csv(HERE / "confirm_results.csv", index=False); print("Educational only - not financial advice.")
