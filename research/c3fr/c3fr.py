"""C3FR (guild Builder, 2026-11-09): friction rework of COMBO1 C3 LAG-OF-SCAN. Plan: PLAN.md (frozen before scoring).
Signal = combo1.py C3 verbatim (open frame + o5 + daily); exits re-simulated on 5-minute bars built from the 1-minute
SIP cache, entry at the next bar's open. Grid: R in {0.50, 0.75, 1.00} x ATR_d  x  exit {B bracket +-1R flat 15:55,
T stop -1R else 11:00 close}; anchor R 0.25 B (parent, not a new config). Lineage N 21.
    python c3fr.py <o5_hist.parquet> > c3fr_out.txt
Locked block 2024-11-01..2025-02-28 dropped at every read (asserted). Educational only - not financial advice."""
import glob, os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD
HERE = Path(__file__).resolve().parent
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(); SPLIT = pd.Timestamp("2025-09-30").date()
N_LINEAGE = 15 + 6; T90 = round(max(1.35, 0.9 * G.t_required(N_LINEAGE)), 2)
K, MINC, WIN, MINW = 10, 0.30, 120, 50
IDX = {"SPY", "QQQ", "IWM", "DIA"}
SPREAD_BPS = 4.4e-4; FLOOR = 0.10
GRID = [(w, e) for e in ("B", "T") for w in (0.50, 0.75, 1.00)]
ANCHOR = (0.25, "B")

# ------------------------------------------------------------------ signal: combo1.py C3, unchanged
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date; D = D[~((D.date >= LK0) & (D.date <= LK1))]
RET = D.pivot(index="date", columns="symbol", values="close").sort_index().pct_change(fill_method=None)
RET.loc[RET.index[RET.index > LK1][0]] = np.nan
spy = RET["SPY"]


def peer_table(end_excl):
    w = RET[RET.index < end_excl].tail(WIN)
    if len(w) < MINW: return {}
    w = w.loc[:, w.notna().mean() >= 0.9]; s = spy.reindex(w.index).fillna(0)
    beta = w.apply(lambda c: np.cov(c.fillna(0), s)[0, 1] / max(np.var(s), 1e-12))
    res = (w - np.outer(s, beta)).fillna(0).drop(columns=[c for c in IDX if c in w])
    C = np.corrcoef(res.to_numpy().T); np.fill_diagonal(C, -1); cols = res.columns.to_numpy(); out = {}
    for i, c in enumerate(cols):
        j = np.argsort(-C[i])[:K]; j = j[C[i, j] >= MINC]
        if len(j) >= 6: out[c] = list(cols[j])
    return out


O5 = pd.read_parquet(sys.argv[1]); O5["date"] = pd.to_datetime(O5["date"]).dt.date
O5 = O5[~((O5.date >= LK0) & (O5.date <= LK1))]
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "fromOpen", "adv20"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= LK0) & (F.date <= LK1)).any()
F = F[(F.adv20 >= 95e6) & (F.atr_d > 0)].copy().sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
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
F["P"] = np.nan; F["agree"] = np.nan; F["npS"] = 0.0
F["month"] = pd.to_datetime(F.date).dt.to_period("M")
scanset = set(zip(u.loc[u.scan, "symbol"], u.loc[u.scan, "date"]))
for m, fm in F.groupby("month"):
    st = m.to_timestamp().date(); peers = peer_table(st)
    if not peers: continue
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
tod = F.tod.to_numpy(); z, P, ag, npS = F.z.to_numpy(), F.P.to_numpy(), F.agree.to_numpy(), F.npS.to_numpy()
dcl = (F.close - F.prev_cl).to_numpy()
sgP = np.sign(P)
m = (npS >= 2) & (tod >= 940) & (tod <= 950) & (sgP * P >= 0.40) & (ag >= 0.7) & (sgP * z < sgP * P / 2) & (sgP * dcl < 0)
m &= elig & (sgP != 0) & np.isfinite(dcl)
SIG = G.first_per_symbol_day(F.symbol.to_numpy(), F.date.to_numpy(), m)
print(f"C3 signals {len(SIG)} over {F.date.nunique()} sessions ({F.date.min()}..{F.date.max()}, locked absent)", flush=True)

# random baseline pool: every eligible U row at 09:40-09:50 (both sides scored)
POOL = np.flatnonzero(elig & (tod >= 940) & (tod <= 950) & np.isfinite(F.atr_d.to_numpy()))

# ------------------------------------------------------------------ 5-minute paths from the 1-minute cache
ENDS = np.arange(0, 76) * 5  # bar ends as minutes after 09:40 (09:40 .. 15:55)
END_TOD = np.array([(9 * 60 + 40 + e) // 60 * 100 + (9 * 60 + 40 + e) % 60 for e in ENDS])
need = F.iloc[np.union1d(SIG, POOL)][["symbol", "date"]].drop_duplicates()
need_by_sym = need.groupby("symbol").date.apply(set).to_dict()
CACHE = ROOT / "data/cache_hist/1Min"; TZ = "America/New_York"
TL0, TL1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
PATH = {}  # (symbol, date) -> array (76, 4) open/high/low/close of bars ending 09:40..15:55
for sym, dates in need_by_sym.items():
    p = CACHE / f"{sym}.parquet"
    if not p.exists(): continue
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= TL0) & (df.index < TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = df.index.hour * 60 + df.index.minute
    df = df[(mm >= 575) & (mm < 955)]; mm = df.index.hour * 60 + df.index.minute
    b = (mm - 575) // 5  # bar 0 = minutes 09:35-09:39 -> ends 09:40
    df = df.assign(_d=df.index.date, _b=b)
    df = df[df._d.isin(dates)]
    g = df.groupby(["_d", "_b"]).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
    for d, gd in g.groupby(level=0):
        a = np.full((76, 4), np.nan); bi = gd.index.get_level_values(1).to_numpy()
        a[bi] = gd[["o", "h", "l", "c"]].to_numpy()
        a = pd.DataFrame(a).ffill().to_numpy()   # a bar with no prints carries the last close level
        PATH[(sym, d)] = a
print(f"paths built: {len(PATH)} symbol-days", flush=True)

T1100 = int(np.flatnonzero(END_TOD == 1100)[0])


def sim(rows, sides, w, ex, chunk=50000):
    """Net R after costs per row (signal bar = row), entry at the next bar's open; vectorized. NaN when no path."""
    n = len(rows); out = np.full(n, np.nan); fr_out = np.full(n, np.nan); gross_out = np.full(n, np.nan)
    sy, dt, td, atr = F.symbol.to_numpy()[rows], F.date.to_numpy()[rows], tod[rows], F.atr_d.to_numpy()[rows]
    pos = {t: i for i, t in enumerate(END_TOD)}
    last = 75 if ex == "B" else T1100; IDXB = np.arange(76)
    for c0 in range(0, n, chunk):
        ks = np.arange(c0, min(n, c0 + chunk))
        have = np.array([(sy[k], dt[k]) in PATH for k in ks]); ks = ks[have]
        if not len(ks): continue
        A = np.stack([PATH[(sy[k], dt[k])] for k in ks]).astype(np.float64)
        O, H, L, C = A[..., 0], A[..., 1], A[..., 2], A[..., 3]
        j = np.array([pos[td[k]] + 1 for k in ks]); r_ = np.arange(len(ks))
        e = O[r_, j]; sg = np.asarray(sides, float)[ks]; R = w * atr[ks]
        stop = e - sg * R; tgt = e + sg * R
        valid = (IDXB[None, :] >= j[:, None]) & (IDXB[None, :] <= last)
        gap = (IDXB[None, :] > j[:, None]) & (sg[:, None] * (O - stop[:, None]) <= 0) & valid
        hit = np.where(sg[:, None] > 0, L <= stop[:, None], H >= stop[:, None]) & valid
        sany = gap | hit
        fs = np.where(sany.any(1), sany.argmax(1), 999)
        if ex == "B":
            th = np.where(sg[:, None] > 0, H >= tgt[:, None], L <= tgt[:, None]) & valid
            ft = np.where(th.any(1), th.argmax(1), 999)
        else:
            ft = np.full(len(ks), 999)
        is_stop = (fs < 999) & (fs <= ft); is_tgt = (~is_stop) & (ft < 999); is_time = ~is_stop & ~is_tgt
        fsc = np.minimum(fs, 75)
        xp = np.where(is_stop, np.where(gap[r_, fsc], O[r_, fsc], stop), np.where(is_tgt, tgt, C[:, last]))
        mult = G.tod_cost_mult(td[ks])          # entry cost at the signal bar's clock, as the parent
        pc = (G.SLIP_PS + e * G.SLIP_BPS) * mult + SPREAD_BPS * e * mult
        pc = pc + np.where(is_stop, G.SLIP_PS + e * G.SLIP_BPS + G.STOP_EXTRA, 0) + np.where(is_time, G.SLIP_PS + e * G.SLIP_BPS, 0)
        g = sg * (xp - e) / R; fr = pc / R
        ok = np.isfinite(e) & (e > 0) & np.isfinite(xp) & (R > 0)
        g[~ok] = np.nan
        gross_out[ks] = g; fr_out[ks] = fr; out[ks] = g - np.maximum(FLOOR, fr)
    return out, fr_out, gross_out


DD = D[D.symbol == "SPY"].set_index("date"); oc = (DD.close / DD.open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
ALLD = np.array(sorted(F.date.unique())); NS_TR, NS_VA = int((ALLD <= SPLIT).sum()), int((ALLD > SPLIT).sum())
print(f"sessions train {NS_TR} / valid {NS_VA}; lineage N {N_LINEAGE}: full bar {G.t_required(N_LINEAGE)}, BAR90 {T90}")

sig_side = sgP[SIG]
pool_d, pool_t = F.date.to_numpy()[POOL], tod[POOL]
rows = []; TRADES = {}
for w, ex in [ANCHOR] + GRID:
    r, fr, gr = sim(SIG, sig_side, w, ex)
    rl, _, _ = sim(POOL, np.ones(len(POOL)), w, ex); rs, _, _ = sim(POOL, -np.ones(len(POOL)), w, ex)
    pdm = pd.DataFrame({"date": pool_d, "tod": pool_t, "L": rl, "S": rs}).groupby(["date", "tod"])[["L", "S"]].mean()
    t = pd.DataFrame({"date": F.date.to_numpy()[SIG], "symbol": F.symbol.to_numpy()[SIG], "tod": tod[SIG], "sg": sig_side,
                      "r": r, "fr": fr, "gross": gr})
    key = list(zip(t.date, t.tod))
    t["dm"] = [pdm.loc[k, "L" if s > 0 else "S"] if k in pdm.index else np.nan for k, s in zip(key, t.sg)]
    t = t[np.isfinite(t.r)].copy(); t["ex"] = t.r - t.dm
    nm = f"C3FR-R{w:.2f}-{ex}" + ("(anchor)" if (w, ex) == ANCHOR else "")
    TRADES[nm] = t
    s = G.summary(t); tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
    xs = G.summary(t[np.isfinite(t.ex)].assign(r=lambda x: x.ex))
    nf = G.summary(t.assign(r=t.gross - t.fr))
    ty = t.groupby(t.date.map(dtype)).r.agg(["mean", "size"])
    mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean(); wf = float((mo > 0).mean())
    gd = t.groupby("date").r.sum(); share = round(gd.max() / gd.sum(), 2) if gd.sum() > 0 else None
    row = dict(config=nm, n=s["n"], per_sess=round(s["n"] / (NS_TR + NS_VA), 2), avg_r=s.get("exp_r"), t=s.get("t"),
               wo_best=s.get("ex_best_day"), best_share=share, gross=round(t.gross.mean(), 3), friction=round(t.fr.mean(), 3),
               nofloor_r=nf.get("exp_r"), train=tr.get("exp_r"), valid=va.get("exp_r"), valid_t=va.get("t"),
               tr_ps=round(tr.get("n", 0) / NS_TR, 2), va_ps=round(va.get("n", 0) / NS_VA, 2),
               up=round(ty["mean"].get("up", np.nan), 3), down=round(ty["mean"].get("down", np.nan), 3),
               quiet=round(ty["mean"].get("quiet", np.nan), 3), n_up=int(ty["size"].get("up", 0)),
               n_down=int(ty["size"].get("down", 0)), n_quiet=int(ty["size"].get("quiet", 0)),
               wf_pos=round(wf, 2), dm_excess=xs.get("exp_r"), dm_t=xs.get("t"), long_share=round(float((t.sg > 0).mean()), 2))
    row["bar90"] = bool((row["t"] or 0) >= T90 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0
                        and row["up"] > 0 and row["down"] > 0 and wf >= 0.54 and (row["dm_excess"] or -1) > 0
                        and (row["wo_best"] or -1) > 0 and row["tr_ps"] >= 1.5 and row["va_ps"] >= 1.5)
    rows.append(row); print(nm, "done", flush=True)

R = pd.DataFrame(rows); pd.set_option("display.width", 400); pd.set_option("display.max_columns", 50)
print(R.to_string(index=False))
print("\nentry = next 5-min bar open (1-min SIP cache); stop-first; friction floor 0.10R kept (nofloor_r is info only, never a pass);"
      "\nday type = SPY open-to-close (up > +0.25%, down < -0.25%, else quiet); dm_excess = vs mean of all eligible U names, same bar/side/R/exit.")
print(f"new configs {len(GRID)} (+1 anchor already counted; lineage {N_LINEAGE}), BAR90 pass {int(R.bar90.sum())}")
R.to_csv(HERE / "c3fr_results.csv", index=False)
pd.concat([v.assign(config=k) for k, v in TRADES.items()]).to_csv(HERE / "c3fr_trades.csv", index=False)
print("Educational only - not financial advice.")
