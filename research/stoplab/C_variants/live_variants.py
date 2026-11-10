"""stoplab C (stop variants) on LIVE trades, replayed on 1-min bars.

C-open : open-loss latch. Per (account, setup, date): block new entries once realised R (journal r_multiple of trades
         that exited at/before the entry second) + open marked R (last completed 1-min close before the entry, gross)
         <= -k, latched; k in {2,3,4}. Compared with the realised-only latch at the same k (the live rule at k=2) and
         with no latch. Sequence = live trades + run-2 what-ifs blocked by the setup daily stop (as A1). Halt what-ifs
         excluded. Only units whose rows all have 1-min bars (date <= 2026-11-04, symbol cached).
C1     : time-in-trade stop: at N minutes after entry, exit at that bar's close if the best R so far (1-min highs/lows
         after the entry bar) < b. N in {15,30,60,90}, b in {0, 0.25, 0.5}.
C2     : give-back stop: once peak R (1-min highs/lows) >= m, exit when price gives back g of the peak
         (level = entry + side*risk*peak*(1-g)); m in {0.5, 1.0}, g in {0.5, 0.7, 1.0 (=break-even)}.
C1/C2 only ever EXIT EARLIER than the live trade, so a trade whose trigger does not fire before its live exit keeps its
live R exactly (pnl_adj basis). A fired trade gets R_live + side*(px_var - live exit)/risk - (1c + 1bps)/risk
(conservative: live flattens carry no extra exit cost in pnl_adj). Scale-out rows excluded. Partial entry/exit minutes
are not used for triggers (approximation). Educational only - not financial advice.
"""
import math, re, sys, json
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
BARS = Path("/home/user/MCF/data/cache_hist/1Min")
LAST_BAR = "2026-11-04"
LOCK = ("2024-11-01", "2025-02-28")
NS_, BS_ = (15, 30, 60, 90), (0.0, 0.25, 0.5)
MS_, GS_ = (0.5, 1.0), (0.5, 0.7, 1.0)
KS_ = (2.0, 3.0, 4.0)
OUT = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); OUT.append(s)

T = pd.read_csv(HERE.parent / "trades.csv.gz")
assert not ((T.date >= LOCK[0]) & (T.date <= LOCK[1])).any()
to_s = lambda c: ((pd.to_datetime(T[c], utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")).astype("int64")
T["ent_s"], T["ext_s"] = to_s("entry_time"), to_s("exit_time")
T = T[~T.whatif | T.blocked_latch].copy()          # halt what-ifs out of the main run
T = T[np.isfinite(T.R)].copy()
T["RL"] = T.r_multiple.where(np.isfinite(T.r_multiple), T.R)

FAM8 = {"MF", "RW", "NS", "ST", "CWT", "L3", "GEN"}
def fam8(n):
    p = re.match(r"[A-Za-z]+", n).group(0); p = "L3" if p == "L" else p
    if n.startswith("NM-MF"): p = "MF"
    if n.startswith("NM-RW"): p = "RW"
    if n.startswith("NM1-cwt"): p = "CWT"
    return p if p in FAM8 else "other"
LM = pd.read_csv(HERE.parent / "lab_modules.csv")
GEO = dict(zip(LM.setup, LM.geom.astype(str).str.extract(r"([A-Za-z0-9+]+)")[0]))
def geom(s):
    g = GEO.get(s)
    if isinstance(g, str): return g
    m = re.search(r"-(t\d+s\d+|hold|holdtr)(-|$)", s)
    return m.group(1) if m else "?"

live_all = T[~T.whatif]
SPL = {}
for su, g in live_all.groupby("setup"):
    ds = sorted(g.date.unique()); k = math.ceil(0.6 * len(ds)); SPL[su] = (set(ds[:k]), len(ds))
T["split"] = [("choose" if d in SPL.get(s, (set(), 0))[0] else "validate") for s, d in zip(T.setup, T.date)]
T["fam"] = T.setup.map(fam8); T["geom"] = T.setup.map(geom)

have = {p.stem for p in BARS.glob("*.parquet")}
T["bars_ok"] = (T.date <= LAST_BAR) & T.symbol.isin(have)

# ---------------- bars ----------------
BAR = {}
need = T[T.bars_ok].groupby("symbol").date.apply(set)
for sym, dates in need.items():
    b = pd.read_parquet(BARS / f"{sym}.parquet", columns=["open", "high", "low", "close"])
    ts = b.index.as_unit("s").asi8 if hasattr(b.index, "as_unit") else b.index.asi8 // 10**9
    sel = np.zeros(len(ts), bool)
    for dt in dates:
        a0 = pd.Timestamp(dt, tz="America/New_York"); lo, hi = a0.value // 10**9, (a0 + pd.Timedelta(days=1)).value // 10**9
        sel[np.searchsorted(ts, lo):np.searchsorted(ts, hi)] = True
    b = b[sel]; ts = ts[sel]
    BAR[sym] = (ts, b.open.to_numpy(float), b.high.to_numpy(float), b.low.to_numpy(float), b.close.to_numpy(float))
P(f"bars loaded for {len(BAR)} symbols")

def path(sym, ent_s, ext_s):
    ts, o, h, l, c = BAR[sym]
    e0 = (ent_s // 60) * 60 + 60
    a = np.searchsorted(ts, e0, side="left"); b = np.searchsorted(ts, ext_s - 60, side="right")
    return ts[a:b], o[a:b], h[a:b], l[a:b], c[a:b]

# ============ C1 / C2 per-trade replay ============
L = T[~T.whatif & T.bars_ok & ~T.exit_reason.astype(str).str.startswith("scaled") & (T.risk_ps > 0)].copy()
P(f"\n=== C1/C2 per-trade: {len(L)} live rows replayed of {int((~T.whatif).sum())} live rows "
  f"({int((~T.whatif & ~T.bars_ok).sum())} after 11-04 or uncached symbol, "
  f"{int((~T.whatif & T.bars_ok & T.exit_reason.astype(str).str.startswith('scaled')).sum())} scale-out) ===")
CONF = [f"T{n}_b{b}" for n in NS_ for b in BS_] + [f"G_m{m}_g{g}" for m in MS_ for g in GS_]
res = {c: np.zeros(len(L)) for c in CONF}; fired = {c: np.zeros(len(L), bool) for c in CONF}
pmfe = np.full(len(L), np.nan); npath = np.zeros(len(L), int)
Ls = L.symbol.to_numpy(); Le = L.entry.to_numpy(float); Lx = L["exit"].to_numpy(float); Lsd = L.side.to_numpy(float)
Lr = L.risk_ps.to_numpy(float); LR = L.R.to_numpy(float); Les = L.ent_s.to_numpy(); Lxs = L.ext_s.to_numpy()
for i in range(len(L)):
    ts, o, h, l, c = path(Ls[i], Les[i], Lxs[i]); s = Lsd[i]; e = Le[i]; r = Lr[i]
    npath[i] = len(ts)
    for cname in CONF: res[cname][i] = LR[i]
    if not len(ts): continue
    fav = (h - e) / r if s > 0 else (e - l) / r      # best R within each bar
    adv = (l - e) / r if s > 0 else (e - h) / r      # worst R within each bar
    best = np.maximum.accumulate(fav); pmfe[i] = best[-1]
    def fill(px): return LR[i] + s * (px - Lx[i]) / r - (0.01 + 1e-4 * px) / r
    end = ts + 60
    for n in NS_:
        k = np.searchsorted(end, Les[i] + n * 60, side="left")
        if k >= len(ts): continue
        for b in BS_:
            if best[k] < b:
                cn = f"T{n}_b{b}"; res[cn][i] = fill(c[k]); fired[cn][i] = True
    prev = np.r_[-np.inf, best[:-1]]                 # peak from earlier bars only
    for m in MS_:
        arm = prev >= m
        if not arm.any(): continue
        for g in GS_:
            lvl_r = prev * (1 - g)                   # R level that triggers
            hit = arm & (adv <= lvl_r)
            if hit.any():
                k = int(np.argmax(hit)); lv = e + s * r * lvl_r[k]
                px = min(o[k], lv) if s > 0 else max(o[k], lv)
                cn = f"G_m{m}_g{g}"; res[cn][i] = fill(px); fired[cn][i] = True
ok = np.isfinite(pmfe) & L.mfe_r.notna().to_numpy()
P(f"path check: {int((npath > 0).sum())} rows have >=1 full bar inside the trade; journal mfe_r vs 1-min path MFE "
  f"(rows with both, n={int(ok.sum())}): corr {np.corrcoef(pmfe[ok], L.mfe_r.to_numpy()[ok])[0,1]:.3f}, "
  f"median |d| {np.median(np.abs(pmfe[ok] - L.mfe_r.to_numpy()[ok])):.3f}R, path <= journal in "
  f"{np.mean(pmfe[ok] <= L.mfe_r.to_numpy()[ok] + 0.02):.1%} (path skips the partial entry/exit minutes)")
for c in CONF:
    L[f"R_{c}"] = res[c]; L[f"f_{c}"] = fired[c]
L["path_mfe"] = pmfe; L["n_bars"] = npath
keep = ["account", "setup", "fam", "geom", "symbol", "date", "split", "side", "entry", "stop", "exit", "exit_reason",
        "hold_min", "R", "mfe_r", "mae_r", "path_mfe", "n_bars"] + [f"R_{c}" for c in CONF] + [f"f_{c}" for c in CONF]
L[keep].to_csv(HERE / "trades_c12.csv.gz", index=False)

def tstat(x):
    x = np.asarray(x, float); return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan

rows = []; persetup = []
for c in CONF:
    d = L[f"R_{c}"] - L.R
    dd = d.groupby(L.date).sum(); v = L.split == "validate"
    dv = d[v].groupby(L.date[v]).sum()
    ps = d.groupby(L.setup).sum(); n_s = L.groupby("setup").size(); ps20 = ps[n_s >= 20]
    psv = d[v].groupby(L.setup[v]).sum(); psv = psv[psv.index.isin(ps20.index)]
    rows.append(dict(config=c, n=len(L), fired=int(L[f"f_{c}"].sum()), fired_pct=L[f"f_{c}"].mean(),
                     R_base=L.R.sum(), d_all=d.sum(), d_per_trade=d.mean(), d_per_fired=d[L[f"f_{c}"]].mean(),
                     d_choose=d[~v].sum(), d_validate=d[v].sum(), t_validate=tstat(dv), t_all=tstat(dd),
                     d_wo_best_day=d.sum() - dd.max(), best_day_share=(dd.max() / d.sum() if d.sum() > 0 else np.nan),
                     setups20=len(ps20), up=int((ps20 > 0).sum()), down=int((ps20 < 0).sum()),
                     sum_up=ps20[ps20 > 0].sum(), sum_down=ps20[ps20 < 0].sum(), worst_setup=ps20.min(),
                     v_up=int((psv > 0).sum()), v_down=int((psv < 0).sum())))
    for su, g in L.groupby("setup"):
        dg = d[g.index]
        persetup.append(dict(config=c, setup=su, fam=g.fam.iloc[0], geom=g.geom.iloc[0], n=len(g), sessions=g.date.nunique(),
                             R_base=g.R.sum(), d=dg.sum(), d_choose=dg[g.split == "choose"].sum(),
                             d_validate=dg[g.split == "validate"].sum(), fired=int(g[f"f_{c}"].sum())))
G = pd.DataFrame(rows); PS = pd.DataFrame(persetup)
G.to_csv(HERE / "C12_global.csv", index=False); PS.to_csv(HERE / "C12_per_setup.csv", index=False)
fmt = lambda df: df.to_string(index=False, float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.1f}")
P(fmt(G[["config", "fired", "fired_pct", "d_all", "d_per_fired", "d_choose", "d_validate", "t_validate",
         "d_wo_best_day", "best_day_share", "setups20", "up", "down", "sum_up", "sum_down", "worst_setup", "v_up", "v_down"]]))
P(f"baseline live R on the replayed rows: {L.R.sum():,.1f} (n {len(L)}, avg {L.R.mean():+.3f})")

# by family and by geometry (all sessions)
fam_rows = []
for c in CONF:
    d = L[f"R_{c}"] - L.R
    for key in ("fam", "geom"):
        for k2, g in L.groupby(key):
            ps = d[g.index].groupby(g.setup).sum()
            fam_rows.append(dict(config=c, by=key, group=k2, n=len(g), setups=len(ps), d=d[g.index].sum(),
                                 d_validate=d[g.index][g.split == "validate"].sum(),
                                 setups_up=int((ps > 0).sum()), setups_down=int((ps < 0).sum()),
                                 R_up=ps[ps > 0].sum(), R_down=ps[ps < 0].sum()))
F = pd.DataFrame(fam_rows); F.to_csv(HERE / "C12_by_family_geom.csv", index=False)

# per-setup choice: best of {none} + CONF on CHOOSE (setups with >= 5 sessions, >= 20 trades), scored on VALIDATE
pc = []
for su, g in PS.groupby("setup"):
    if g.sessions.iloc[0] < 5 or g.n.iloc[0] < 20: continue
    b = g.loc[g.d_choose.idxmax()]
    ch = b.config if b.d_choose > 0 else "none"
    pc.append(dict(setup=su, fam=b.fam, geom=b.geom, n=b.n, sessions=b.sessions, R_base=b.R_base, choice=ch,
                   d_choose=max(b.d_choose, 0.0), d_validate=(b.d_validate if ch != "none" else 0.0)))
PC = pd.DataFrame(pc); PC.to_csv(HERE / "C12_per_setup_choice.csv", index=False)
chosen = PC[PC.choice != "none"]
P(f"\nper-setup choice (18 variants + none, >=5 sessions & >=20 replayed trades): {len(PC)} setups, {len(chosen)} pick a "
  f"variant on CHOOSE; on VALIDATE {int((chosen.d_validate > 0).sum())} improve / {int((chosen.d_validate < 0).sum())} worsen, "
  f"sum {chosen.d_validate.sum():+.1f}R (gain {chosen.d_validate[chosen.d_validate > 0].sum():+.1f}, loss "
  f"{chosen.d_validate[chosen.d_validate < 0].sum():+.1f})")

# ============ C-open: open-loss latch ============
U = T[T.bars_ok].copy()
okU = U.groupby(["account", "setup", "date"]).bars_ok.transform("all")
allU = T.groupby(["account", "setup", "date"]).ngroups
P(f"\n=== C-open latch: units with bars {U.groupby(['account','setup','date']).ngroups} of {allU} "
  f"(rows {len(U)} incl. {int(U.whatif.sum())} latch what-ifs) ===")
def mark(sym, t):
    ts, o, h, l, c = BAR[sym]
    k = np.searchsorted(ts, t - 60, side="right") - 1
    return None if k < 0 else c[k]
cf = [("off", None, None)] + [(f"real{k}", "real", k) for k in KS_] + [(f"open{k}", "open", k) for k in KS_]
units = []
for (ac, su, dt), g in U.sort_values(["ent_s", "ext_s"]).groupby(["account", "setup", "date"], sort=False):
    sy = g.symbol.to_numpy(); en = g.entry.to_numpy(float); sd = g.side.to_numpy(float)
    rp = np.abs(en - g.stop.to_numpy(float)); es = g.ent_s.to_numpy(); xs = g.ext_s.to_numpy()
    RL = g.RL.to_numpy(float); R = g.R.to_numpy(float); wi = g.whatif.to_numpy()
    rec = dict(account=ac, setup=su, date=dt, split=g.split.iloc[0], fam=g.fam.iloc[0], n_rows=len(g), n_whatif=int(wi.sum()))
    miss = False
    for name, kind, k in cf:
        taken = []; tot = 0.0; nblk = 0; latched = False
        for i in range(len(g)):
            if kind is not None and not latched:
                real = sum(RL[j] for j in taken if xs[j] <= es[i])
                val = real
                if kind == "open":
                    for j in taken:
                        if xs[j] > es[i] and rp[j] > 0:
                            px = mark(sy[j], es[i])
                            if px is None: miss = True; continue
                            val += sd[j] * (px - en[j]) / rp[j]
                if val <= -k: latched = True
            if latched: nblk += 1; continue
            taken.append(i); tot += R[i]
        rec[f"R_{name}"] = tot; rec[f"blk_{name}"] = nblk
    rec["miss_mark"] = miss
    units.append(rec)
UN = pd.DataFrame(units); UN.to_csv(HERE / "units_open_latch.csv.gz", index=False)
mu = T[~T.whatif & (T.split == "choose")].groupby("setup").R.mean()
UN["mu"] = UN.setup.map(mu).fillna(0.0)
lr = []
for name, kind, k in cf:
    for ref in (["off"] + ([f"real{k}"] if kind == "open" else [])):
        if name == ref: continue
        d = UN[f"R_{name}"] - UN[f"R_{ref}"]; v = UN.split == "validate"
        dblk = UN[f"blk_{name}"] - UN[f"blk_{ref}"]
        exc = d - dblk * (-UN.mu)                    # blocking a trade 'saves' -mu on average
        dd = d.groupby(UN.date).sum(); dv = d[v].groupby(UN.date[v]).sum()
        ps = d.groupby(UN.setup).sum()
        lr.append(dict(config=name, vs=ref, R=UN[f"R_{name}"].sum(), R_ref=UN[f"R_{ref}"].sum(), d=d.sum(),
                       d_choose=d[~v].sum(), d_validate=d[v].sum(), t_validate=tstat(dv), extra_blocked=int(dblk.sum()),
                       excess_d=exc.sum(), excess_d_validate=exc[v].sum(), d_wo_best_day=d.sum() - dd.max(),
                       setups_changed=int((ps != 0).sum()), up=int((ps > 0).sum()), down=int((ps < 0).sum()),
                       sum_up=ps[ps > 0].sum(), sum_down=ps[ps < 0].sum(), worst_setup=ps.min()))
LT = pd.DataFrame(lr); LT.to_csv(HERE / "C_open_latch.csv", index=False)
P(fmt(LT))
P(f"units with a missing mark: {int(UN.miss_mark.sum())}")
acc = UN.groupby("account")[[f"R_{n}" for n, _, _ in cf]].sum()
P("by account (R):"); P(acc.to_string(float_format=lambda v: f"{v:,.1f}"))
acc.to_csv(HERE / "C_open_latch_by_account.csv")
fo = []
for k in KS_:
    d = UN[f"R_open{k}"] - UN[f"R_real{k}"]
    for f_, g in UN.groupby("fam"):
        ps = d[g.index].groupby(g.setup).sum()
        fo.append(dict(k=k, fam=f_, d=d[g.index].sum(), setups_up=int((ps > 0).sum()), setups_down=int((ps < 0).sum()),
                       R_up=ps[ps > 0].sum(), R_down=ps[ps < 0].sum()))
pd.DataFrame(fo).to_csv(HERE / "C_open_latch_by_family.csv", index=False)
(HERE / "live_out.txt").write_text("\n".join(OUT) + "\n")
