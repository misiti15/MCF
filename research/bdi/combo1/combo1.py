"""COMBO1 (owner 2026-11-03): the pre-registered family in PLAN.md (3 combinations x 2 exits = 6 configs; lineage N 15).
  U  top 500 by adv20 x ATR% (adv20 >= $95M)          S  top 150 of U by 09:30-09:35 $ volume / adv20
  C1 SCAN-PB      S, 09:45..10:15, |z| >= 0.50, side = sign(z), fade bar against the side
  C2 SCAN-PB-GRP  C1 + side x P >= 0.25, agree >= 0.6
  C3 LAG-OF-SCAN  U, >= 2 peers in S, side = sign(P), side x P >= 0.40, agree >= 0.7, side x z < side x P / 2,
                  09:40..09:50, fade bar against the side
  exits t1s1 | h1030H (SPY-hedged to 10:30); friction per trade = max(0.10R, production + 4.4 bps entry crossing).
Locked block 2024-11-01..2025-02-28 is absent from the open frame (asserted) and dropped from daily / o5 at load.
    python combo1.py <o5_hist.parquet>  > combo1_out.txt        Educational only - not financial advice."""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
from mcf.analytics import market_beta as MB
HERE = Path(__file__).resolve().parent
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(); SPLIT = pd.Timestamp("2025-09-30").date()
N_LINEAGE = 9 + 6; T90 = round(max(1.35, 0.9 * G.t_required(N_LINEAGE)), 2)
K, MINC, WIN, MINW = 10, 0.30, 120, 50
IDX = {"SPY", "QQQ", "IWM", "DIA"}

D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date; D = D[~((D.date >= LK0) & (D.date <= LK1))]
RET = D.pivot(index="date", columns="symbol", values="close").sort_index().pct_change(fill_method=None)
RET.loc[RET.index[RET.index > LK1][0]] = np.nan
spy = RET["SPY"]; BETAS = {}

def peer_table(end_excl):
    w = RET[RET.index < end_excl].tail(WIN)
    if len(w) < MINW: return {}
    w = w.loc[:, w.notna().mean() >= 0.9]; s = spy.reindex(w.index).fillna(0)
    beta = w.apply(lambda c: np.cov(c.fillna(0), s)[0, 1] / max(np.var(s), 1e-12)); BETAS[end_excl] = beta
    res = (w - np.outer(s, beta)).fillna(0).drop(columns=[c for c in IDX if c in w])
    C = np.corrcoef(res.to_numpy().T); np.fill_diagonal(C, -1); cols = res.columns.to_numpy(); out = {}
    for i, c in enumerate(cols):
        j = np.argsort(-C[i])[:K]; j = j[C[i, j] >= MINC]
        if len(j) >= 6: out[c] = list(cols[j])
    return out

O5 = pd.read_parquet(sys.argv[1]); O5["date"] = pd.to_datetime(O5["date"]).dt.date
O5 = O5[~((O5.date >= LK0) & (O5.date <= LK1))]
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "fromOpen", "adv20", "r_long_t1s1", "win_long_t1s1",
        "r_short_t1s1", "win_short_t1s1"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= LK0) & (F.date <= LK1)).any()
SPYF = F[F.symbol == "SPY"].set_index(["date", "tod"]).close
F = F[(F.adv20 >= 95e6) & (F.atr_d > 0)].copy()
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
# U and S, from data known at 09:35
r935 = F[F.tod == 935][["symbol", "date", "close", "atr_d", "adv20"]].copy()
r935["atr_pct"] = r935.atr_d / r935.close * 100; r935["score"] = r935.adv20 * r935.atr_pct
r935 = r935[~r935.symbol.isin(IDX)]
r935["u500"] = r935.groupby("date").score.rank(ascending=False, method="first") <= 500
r935 = r935.merge(O5[["symbol", "date", "o5_dvol"]], on=["symbol", "date"], how="left")
r935["o5r"] = r935.o5_dvol / r935.adv20
u = r935[r935.u500].copy(); u["scan"] = u.groupby("date").o5r.rank(ascending=False, method="first") <= 150
u.loc[u.o5r.isna(), "scan"] = False
F = F.merge(u[["symbol", "date", "atr_pct", "scan"]], on=["symbol", "date"], how="left")
F["inU"] = F.scan.notna(); F["scan"] = F.scan.fillna(False).astype(bool)
F["atr_pct"] = F.atr_pct.fillna(F.atr_d / F.close * 100)
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
F["zr"] = F.fromOpen / F.atr_pct; F["z"] = F.zr - F.groupby(["date", "tod"]).zr.transform("median")
F["prev_cl"] = F.groupby(["symbol", "date"]).close.shift(1)
# peers: P, agree, number of peers in S
F["P"] = np.nan; F["agree"] = np.nan; F["beta"] = np.nan; F["npS"] = 0.0
F["month"] = pd.to_datetime(F.date).dt.to_period("M")
scanset = set(zip(u.loc[u.scan, "symbol"], u.loc[u.scan, "date"]))
for m, fm in F.groupby("month"):
    st = m.to_timestamp().date(); peers = peer_table(st)
    if not peers: continue
    F.loc[fm.index, "beta"] = fm.symbol.map(BETAS[st]).to_numpy()
    zt = fm.pivot_table(index=["date", "tod"], columns="symbol", values="z"); Pm, Am = {}, {}
    for s, pl in peers.items():
        pl = [p for p in pl if p in zt.columns]
        if s not in zt.columns or len(pl) < 6: continue
        Z = zt[pl]; ok = Z.notna().sum(axis=1) >= 6; med = Z.median(axis=1).where(ok)
        ag = (np.sign(Z).eq(np.sign(med), axis=0) & Z.notna()).sum(axis=1) / Z.notna().sum(axis=1)
        Pm[s] = med; Am[s] = ag.where(ok)
    if not Pm: continue
    J = pd.concat([pd.DataFrame(Pm).stack().rename("P"), pd.DataFrame(Am).stack().rename("agree")], axis=1).reset_index()
    J.columns = ["date", "tod", "symbol", "P", "agree"]
    sub = fm[["symbol", "date", "tod"]].reset_index().merge(J, on=["symbol", "date", "tod"], how="left").set_index("index")
    F.loc[sub.index, "P"] = sub.P; F.loc[sub.index, "agree"] = sub.agree
    sd = fm[["symbol", "date"]].drop_duplicates()
    nps = {(s, d): sum((p, d) in scanset for p in peers.get(s, [])) for s, d in zip(sd.symbol, sd.date)}
    F.loc[fm.index, "npS"] = [nps.get((s, d), 0) for s, d in zip(fm.symbol, fm.date)]
F["bl"] = GD._blackout(F.symbol.to_numpy(), F.date.to_numpy())
elig = (~F.bl.to_numpy()) & F.inU.to_numpy() & ~F.symbol.isin(IDX).to_numpy()

# exits and costs
key = F.symbol.astype(str) + "|" + F.date.astype(str); rev = F.iloc[::-1]
nxt_lo = rev.groupby(key.iloc[::-1]).low.transform(lambda s: s.cummin().shift(1)).iloc[::-1].to_numpy()
nxt_hi = rev.groupby(key.iloc[::-1]).high.transform(lambda s: s.cummax().shift(1)).iloc[::-1].to_numpy()
last_cl = F.groupby(key).close.transform("last").to_numpy(); cl = F.close.to_numpy(); Rr = 0.25 * F.atr_d.to_numpy()
tod = F.tod.to_numpy(); mult = G.tod_cost_mult(tod)
spy_now = np.array([SPYF.get((d, t), np.nan) for d, t in zip(F.date, F.tod)])
spy_1030 = np.array([SPYF.get((d, 1030), np.nan) for d in F.date])
spy_dc = F.date.map(D[D.symbol == "SPY"].set_index("date").close).to_numpy(float)
win_x = {"h1030H": (spy_1030 / spy_now - 1) * 100, "t1s1": (spy_dc / spy_now - 1) * 100}   # SPY % move over the window
SPREAD_BPS = 4.4e-4; H, FR = {}, {}
b = np.nan_to_num(F.beta.to_numpy(), nan=1.0)
for side, sg in (("long", 1), ("short", -1)):
    # h1030H
    stopped = (nxt_lo <= cl - Rr) if sg > 0 else (nxt_hi >= cl + Rr)
    g = np.where(stopped, -1.0, sg * (last_cl - cl) / Rr)
    pc = (G.SLIP_PS + cl * G.SLIP_BPS) * (mult + 1) + np.where(stopped, G.STOP_EXTRA, 0) + SPREAD_BPS * cl * mult
    fr = np.maximum(0.10, pc / Rr)
    hedge = sg * b * (win_x["h1030H"] / 100) * cl / Rr
    hcost = 2 * np.abs(b) * cl * (0.01 / np.where(spy_now > 0, spy_now, np.nan) + G.SLIP_BPS) / Rr
    H[side + "_h1030H"] = np.where(np.isfinite(nxt_lo), g - fr - hedge - hcost, np.nan); FR[side + "_h1030H"] = fr + hcost
    # t1s1 (lab bracket; lab charged a flat 1c per side, removed to get gross)
    won = F[f"win_{side}_t1s1"].to_numpy(float) == 1
    gross = F[f"r_{side}_t1s1"].to_numpy(float) + 2 * G.SLIP_PS / Rr
    stop = (~won) & (gross <= -1 + 1e-6)
    pc = (G.SLIP_PS + cl * G.SLIP_BPS) * mult + np.where(won, 0, G.SLIP_PS + cl * G.SLIP_BPS) + np.where(stop, G.STOP_EXTRA, 0) + SPREAD_BPS * cl * mult
    fr = np.maximum(0.10, pc / Rr)
    H[side + "_t1s1"] = gross - fr; FR[side + "_t1s1"] = fr
DM = {k: pd.Series(np.where(elig, v, np.nan)).groupby([F.date.to_numpy(), tod]).transform("mean").to_numpy() for k, v in H.items()}

DD = D[D.symbol == "SPY"].set_index("date"); oc = (DD.close / DD.open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ALLD = np.array(sorted(F.date.unique())); NS_TR, NS_VA = int((ALLD <= SPLIT).sum()), int((ALLD > SPLIT).sum())
print(f"COMBO1: rows {len(F)}, dates {F.date.min()}..{F.date.max()} (locked absent), sessions train {NS_TR} / valid {NS_VA}; "
      f"U names/day {F[F.inU].groupby('date').symbol.nunique().mean():.0f}, S names/day {len(scanset) / u.date.nunique():.0f}; "
      f"N lineage {N_LINEAGE}: full bar {G.t_required(N_LINEAGE)}, BAR90 {T90}")

z, P, ag, npS = F.z.to_numpy(), F.P.to_numpy(), F.agree.to_numpy(), F.npS.to_numpy()
dcl = (F.close - F.prev_cl).to_numpy(); scan = F.scan.to_numpy()

def signals(combo):
    """(row index, side sign) of the first signal per symbol-day."""
    if combo in ("C1", "C2"):
        sg = np.sign(z)
        m = scan & (tod >= 945) & (tod <= 1015) & (np.abs(z) >= 0.50) & (sg * dcl < 0)
        if combo == "C2": m &= (sg * P >= 0.25) & (ag >= 0.6)
    else:
        sg = np.sign(P)
        m = (npS >= 2) & (tod >= 940) & (tod <= 950) & (sg * P >= 0.40) & (ag >= 0.7) & (sg * z < sg * P / 2) & (sg * dcl < 0)
    m &= elig & (sg != 0) & np.isfinite(dcl)
    idx = G.first_per_symbol_day(F.symbol.to_numpy(), F.date.to_numpy(), m)
    return idx, sg[idx]

def trades(combo, ex):
    idx, sg = signals(combo)
    pick = lambda d: np.where(sg > 0, d["long_" + ex][idx], d["short_" + ex][idx])
    t = pd.DataFrame({"date": F.date.to_numpy()[idx], "symbol": F.symbol.to_numpy()[idx], "tod": tod[idx], "sg": sg,
                      "r": pick(H), "dm": pick(DM), "fr": pick(FR), "spy_move": win_x[ex][idx]})
    t["ex"] = t.r - t.dm
    return t[np.isfinite(t.r)]

def score(name, t):
    s = G.summary(t); tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
    xs = G.summary(t[np.isfinite(t.ex)].assign(r=lambda x: x.ex))
    mk = MB.fit(MB.sums(t.spy_move, t.r))
    ty = t.groupby(t.date.map(dtype)).r.agg(["mean", "size"])
    mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean(); wf = float((mo > 0).mean())
    g = t.groupby("date").r.sum(); share = round(g.max() / g.sum(), 2) if g.sum() > 0 else None
    row = dict(config=name, n=s["n"], per_sess=round(s["n"] / (NS_TR + NS_VA), 2), avg_r=s.get("exp_r"), t=s.get("t"),
               ex_mkt=mk["exmkt_r"], beta=mk["beta"], wo_best=s.get("ex_best_day"), best_share=share,
               train=tr.get("exp_r"), valid=va.get("exp_r"), valid_t=va.get("t"),
               tr_ps=round(tr.get("n", 0) / NS_TR, 2), va_ps=round(va.get("n", 0) / NS_VA, 2),
               up=round(ty["mean"].get("up", np.nan), 3), down=round(ty["mean"].get("down", np.nan), 3),
               quiet=round(ty["mean"].get("quiet", np.nan), 3), n_up=int(ty["size"].get("up", 0)),
               n_down=int(ty["size"].get("down", 0)), n_quiet=int(ty["size"].get("quiet", 0)),
               wf_pos=round(wf, 2), dm_excess=xs.get("exp_r"), dm_t=xs.get("t"), friction=round(t.fr.mean(), 3),
               long_share=round(float((t.sg > 0).mean()), 2))
    row["bar90"] = bool((row["t"] or 0) >= T90 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0
                        and row["up"] > 0 and row["down"] > 0 and wf >= 0.54 and (row["dm_excess"] or -1) > 0)
    row["lane"] = bool((row["train"] if row["train"] is not None else -1) >= -0.02 and (row["valid"] if row["valid"] is not None else -1) >= -0.02
                       and 1.5 <= row["tr_ps"] <= 25 and 1.5 <= row["va_ps"] <= 25)
    return row

rows, TR = [], {}
for combo in ("C1", "C2", "C3"):
    for ex in ("t1s1", "h1030H"):
        nm = f"COMBO1-{ {'C1': 'SCAN-PB', 'C2': 'SCAN-PB-GRP', 'C3': 'LAG-OF-SCAN'}[combo]}-{ex}"
        t = trades(combo, ex); TR[nm] = t; rows.append(score(nm, t))
R = pd.DataFrame(rows); pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
print(R.to_string(index=False))
print("\nper_sess over all sessions; ex_mkt = BETA1 OLS on SPY's % move over the window (t1s1: entry -> SPY daily close, approx.);"
      "\nday type = SPY open-to-close (up > +0.25%, down < -0.25%, else quiet); friction = mean cost per trade in R (floor 0.10R).")
print(f"configs {len(R)} (lineage {N_LINEAGE}), BAR90 pass {int(R.bar90.sum())}, lane-gate pass {int(R.lane.sum())}")
R.to_csv(HERE / "combo1_results.csv", index=False)
print("Educational only - not financial advice.")
