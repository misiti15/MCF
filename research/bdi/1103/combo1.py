"""COMBO1 (owner 2026-11-03, top of research/queue.jsonl): combine the small positives found this week into one opening
setup and test whether together they clear costs:
  (1) smaller universe  top 500 names per day by adv20 x ATR% (eu1103/universe; adv20 >= $95M)
  (2) 09:35 mover scan  top 150 of those by the 09:35 bar's volumeRatio (eu1103/preopen ranked by opening 5-min $ volume /
                        adv20; that column is not in the opening frame, volumeRatio is the declared proxy)
  (3) peer laggards     MH4 (bdi/1102): residual-correlation peers (top 10, corr >= 0.30, trailing 120 non-locked
                        sessions before the month), group move P = median peer z >= 0.40 ATR ex-market with agree >= 0.7,
                        own z < P/2 (has not followed yet); first of 09:40 / 09:45 / 09:50; side = the group's side
  (4) fade timing       optional: the signal bar closes AGAINST the trade (red bar for a long, green for a short), the
                        short-term reversal timing that is the book's only positive line (eu1103 Q1)
Exits: t1s1 lab bracket (production costs, tod entry multiplier) | h1030H = stop 0.25 ATR, else out at the 10:30 close,
       SPY-hedged (minus beta x SPY's move over the same window, in R; hedge leg costs 1c + 1 bps per side on beta x
       notional) - the both-directions / QDAY form.
Configs (declared before scoring): side 2 x fade 2 x exit 2 = 8, + the two-sided book (long + short, fade on,
h1030H) = 9. Train <= 2025-09-30, valid after. Locked block 2024-11-01..2025-02-28 absent from the open frame (asserted)
and dropped from the daily table before the peer / beta tables are built.
Pass (Testing): BAR90 t >= 0.9 x max(1.5, sqrt(2 ln N_tonight)), train AND valid > 0, positive on SPY up, down AND
quiet days (QDAY), walk-forward >= 54% positive months. Light lane gate (night1102 LL1): train and valid >= -0.02R and
1.5-25 trades / session. Day-matched excess (all eligible names, same date + bar + side + exit) reported.
Usage: python combo1.py <N_tonight> > combo1_out.txt     Educational only - not financial advice."""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
HERE = Path(__file__).resolve().parent
NT = int(sys.argv[1]) if len(sys.argv) > 1 else 9
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(); SPLIT = pd.Timestamp("2025-09-30").date()
K, MINC, WIN, MINW = 10, 0.30, 120, 50
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date; D = D[~((D.date >= LK0) & (D.date <= LK1))]
RET = D.pivot(index="date", columns="symbol", values="close").sort_index().pct_change(fill_method=None)
RET.loc[RET.index[RET.index > LK1][0]] = np.nan                     # no return across the dropped block
spy = RET["SPY"]; BETAS = {}

def peer_table(end_excl):
    w = RET[RET.index < end_excl].tail(WIN)
    if len(w) < MINW: return {}
    w = w.loc[:, w.notna().mean() >= 0.9]; s = spy.reindex(w.index).fillna(0)
    beta = w.apply(lambda c: np.cov(c.fillna(0), s)[0, 1] / max(np.var(s), 1e-12)); BETAS[end_excl] = beta
    res = (w - np.outer(s, beta)).fillna(0).drop(columns=[c for c in ("SPY", "QQQ", "IWM", "DIA") if c in w])
    C = np.corrcoef(res.to_numpy().T); np.fill_diagonal(C, -1); cols = res.columns.to_numpy(); out = {}
    for i, c in enumerate(cols):
        j = np.argsort(-C[i])[:K]; j = j[C[i, j] >= MINC]
        if len(j) >= 6: out[c] = list(cols[j])
    return out

COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "fromOpen", "adv20", "volumeRatio",
        "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= LK0) & (F.date <= LK1)).any()
SPYF = F[F.symbol == "SPY"].set_index(["date", "tod"]).close
F = F[(F.adv20 >= 95e6) & (F.atr_d > 0)].copy()
F["atr_pct"] = F.atr_d / F.close * 100
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
F["zr"] = F.fromOpen / F.atr_pct; F["z"] = F.zr - F.groupby(["date", "tod"]).zr.transform("median")
F["P"] = np.nan; F["agree"] = np.nan; F["beta"] = np.nan
F["month"] = pd.to_datetime(F.date).dt.to_period("M")
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
F["bl"] = GD._blackout(F.symbol.to_numpy(), F.date.to_numpy())
# (1) universe + (2) scan, both from data known at 09:35
r935 = F[F.tod == 935].copy(); r935["score"] = r935.adv20 * r935.atr_pct
r935["u500"] = r935.groupby("date").score.rank(ascending=False, method="first") <= 500
r935["scan"] = r935[r935.u500].groupby("date").volumeRatio.rank(ascending=False, method="first") <= 150
r935["scan"] = r935.scan.fillna(False).astype(bool)
key935 = set(zip(r935.loc[r935.scan, "symbol"], r935.loc[r935.scan, "date"]))
F["scan"] = [(s, d) in key935 for s, d in zip(F.symbol, F.date)]
F["prev_cl"] = F.groupby(["symbol", "date"]).close.shift(1)
# exits
key = F.symbol.astype(str) + "|" + F.date.astype(str); rev = F.iloc[::-1]
nxt_lo = rev.groupby(key.iloc[::-1]).low.transform(lambda s: s.cummin().shift(1)).iloc[::-1].to_numpy()
nxt_hi = rev.groupby(key.iloc[::-1]).high.transform(lambda s: s.cummax().shift(1)).iloc[::-1].to_numpy()
last_cl = F.groupby(key).close.transform("last").to_numpy(); cl = F.close.to_numpy(); Rr = 0.25 * F.atr_d.to_numpy()
spy_now = np.array([SPYF.get((d, t), np.nan) for d, t in zip(F.date, F.tod)]); spy_1030 = np.array([SPYF.get((d, 1030), np.nan) for d in F.date])
spy_mv = (spy_1030 / spy_now - 1)                                   # SPY return entry bar -> 10:30
mult = G.tod_cost_mult(F.tod.to_numpy()); H = {}
for side, sg in (("long", 1), ("short", -1)):
    stopped = (nxt_lo <= cl - Rr) if sg > 0 else (nxt_hi >= cl + Rr)
    g = np.where(stopped, -1.0, sg * (last_cl - cl) / Rr)
    c = (G.SLIP_PS + cl * G.SLIP_BPS) * (mult + 1) + np.where(stopped, G.STOP_EXTRA, 0)
    b = np.nan_to_num(F.beta.to_numpy(), nan=1.0)
    hedge = sg * b * spy_mv * cl / Rr; hcost = 2 * np.abs(b) * cl * (0.01 / np.where(spy_now > 0, spy_now, np.nan) + G.SLIP_BPS) / Rr
    H[side + "_h1030H"] = np.where(np.isfinite(nxt_lo), g - c / Rr - hedge - hcost, np.nan)
    H[side + "_t1s1"] = G.prod_r(F[f"r_{side}_t1s1"].to_numpy(), F[f"win_{side}_t1s1"].to_numpy(), cl, F.atr_d.to_numpy(), "t1s1", tod=F.tod.to_numpy())
    H[side + "_spy"] = sg * b * spy_mv * cl / Rr
elig = ~F.bl.to_numpy(); DM = {}
for k, v in H.items():
    DM[k] = pd.Series(np.where(elig, v, np.nan)).groupby([F.date.to_numpy(), F.tod.to_numpy()]).transform("mean").to_numpy()
DD = D[D.symbol == "SPY"].set_index("date"); oc = (DD.close / DD.open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
s10 = SPYF.xs(1000, level="tod") / SPYF.xs(935, level="tod")        # proxy: SPY 10:00 close vs 09:35 close (open not in frame)
N = NT; tfull = G.t_required(N); t90 = round(max(1.35, 0.9 * tfull), 2)
print(f"COMBO1: rows {len(F)}, dates {F.date.min()}..{F.date.max()} (locked absent), scan names/day {r935.scan.sum() / r935.date.nunique():.0f}; "
      f"N tonight {N}: full bar {tfull}, BAR90 {t90}")

def sig(side, fade):
    sg = 1 if side == "long" else -1
    Pv, z = F.P.to_numpy() * sg, F.z.to_numpy() * sg
    m = (Pv >= 0.40) & (F.agree.to_numpy() >= 0.7) & F.tod.isin([940, 945, 950]).to_numpy() & (z < Pv / 2) & F.scan.to_numpy() & elig
    if fade: m &= (sg * (F.close - F.prev_cl)).to_numpy() < 0
    return G.first_per_symbol_day(F.symbol.to_numpy(), F.date.to_numpy(), m)

def book(parts):
    return pd.concat(parts, ignore_index=True)

def trades(side, fade, ex):
    idx = sig(side, fade); hk = f"{side}_{ex}"
    t = pd.DataFrame({"date": F.date.to_numpy()[idx], "symbol": F.symbol.to_numpy()[idx], "tod": F.tod.to_numpy()[idx], "side": side,
                      "r": H[hk][idx], "ex": H[hk][idx] - DM[hk][idx], "spyR": H[f"{side}_spy"][idx]})
    return t[np.isfinite(t.r) & np.isfinite(t.ex)]

def score(name, t):
    s = G.summary(t); tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT]); xs = G.summary(t.assign(r=t.ex))
    ty = t.groupby(t.date.map(dtype)).r.mean(); s10m = t.groupby(np.where(t.date.map(s10) >= 1, "SPY>=open@10", "SPY<open@10")).r.mean()
    mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean(); wf = float((mo > 0).mean())
    g = t.groupby("date").r.sum(); share = round(g.max() / g.sum(), 2) if g.sum() > 0 else None
    row = dict(config=name, n=s["n"], per_day=round(s["n"] / max(1, s.get("days", 1)), 1), exp_r=s.get("exp_r"), t=s.get("t"),
               ex_best_day=s.get("ex_best_day"), best_day_share=share, train=tr.get("exp_r"), valid=va.get("exp_r"), valid_t=va.get("t"),
               up=round(ty.get("up", np.nan), 3), down=round(ty.get("down", np.nan), 3), quiet=round(ty.get("quiet", np.nan), 3),
               above10=round(s10m.get("SPY>=open@10", np.nan), 3), below10=round(s10m.get("SPY<open@10", np.nan), 3), wf_pos=round(wf, 2),
               dm_excess=xs.get("exp_r"), dm_t=xs.get("t"), spyR=round(t.spyR.mean(), 3))
    row["bar90"] = bool((row["t"] or 0) >= t90 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0 and min(row["up"], row["down"], row["quiet"]) > 0 and wf >= 0.54)
    row["lane"] = bool((row["train"] or -1) >= -0.02 and (row["valid"] or -1) >= -0.02 and 1.5 <= row["per_day"] <= 25)
    return row

rows = []
for side in ("long", "short"):
    for fade in (False, True):
        for ex in ("t1s1", "h1030H"):
            rows.append(score(f"COMBO1-{side}-{'fade' if fade else 'any'}-{ex}", trades(side, fade, ex)))
rows.append(score("COMBO1-both-fade-h1030H", book([trades("long", True, "h1030H"), trades("short", True, "h1030H")])))
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(R.drop(columns=["spyR"]).to_string(index=False))
print("\nday type = SPY open-to-close (up > +0.25%, down < -0.25%, else quiet); 'above10' = SPY 10:00 close >= 09:35 close (proxy).")
print(f"configs {len(R)}, BAR90 pass {int(R.bar90.sum())}, lane-gate pass {int(R.lane.sum())}")
R.to_csv(HERE / "combo1_results.csv", index=False)
print("Educational only - not financial advice.")
