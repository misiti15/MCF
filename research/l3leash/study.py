"""L3LEASH (owner 2026-11-10): can a leash cut the BAD (up-market) days of Gap-Down Recovery Fade (all day)
`L3-gap-slope-fromopen-FD` without giving up its good days? Research only - no config / setup / exit change.

Pre-declared family (12 configs, written before any score was read; see NOTES.md):
  K01 BLOCK        no new entry while the W60 compass at the latest 15-min mark <= entry reads UP-confirmed
  K02 SCALE0       0.5x before the day's first confirmation; 1x DOWN-confirmed or unconfirmed after it; 0x UP-confirmed
  K03 SCALEH       same, 0.5x while UP-confirmed
  K04 RAMP1030     0.5x for entries before 10:30, 1x after
  K05 RAMP1045     0.5x before 10:45
  K06 RAMP1115     0.5x before 11:15
  K07 RAMP1030+BLK K04 and K01 together
  K08 SPYSKIP20    skip the entry when SPY is >= +0.20% from its open (1-min bar closed by the entry)
  K09 SPYSKIP40    skip when SPY >= +0.40%
  K10 SPYHALF20    0.5x when SPY >= +0.20%
  K11 SPYHALF40    0.5x when SPY >= +0.40%
  K12 UPLATCH1     per-setup daily stop -1R (instead of -2R) once the compass has read UP-confirmed at any mark today
Every variant (and the base B0) keeps the -2R per-setup daily stop (realised R, latched), the live caps that the lab can
model (<= 3 lots per symbol, <= 30 open positions per setup) and production costs (bt_lab1104 r).

Data: bt_lab1104 2-year lab trade lists (refire chains, production costs); W60 compass backfill = ECG1 / state15 logic
(SPY/QQQ/IWM 1-min cache + lab breadth_open); SPY from-open from the 1-min cache. Locked block 2024-11-01..2025-02-28 is
never read (filtered at load and asserted). LIVE = journals (Primary run 1 + latch what-ifs, Testing 1 run 1) with the
production compass recomputed by live_compass.py.
Usage: python study.py <scratch>   (needs <scratch>/j/{primary,testing}.db and live_compass.py outputs)
Educational only - not financial advice."""
import glob, importlib.util, math, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent; S = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
MAIN = "L3-gap-slope-fromopen-FD"
SIS = ["L3-gap-slope-rsi5hi-FD", "L3-gap-slope-lowdist-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
       "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD",
       "MF4-h40-open-flowsell"]
SETUPS = [MAIN] + SIS
SHORT = {MAIN: "L3-fromopen-FD", SIS[0]: "L3-rsi5hi-FD", SIS[1]: "L3-lowdist-FD", SIS[2]: "RW3-FD", SIS[3]: "RW5-FD",
         SIS[4]: "MF2-FD", SIS[5]: "MF4-FD", SIS[6]: "MF4"}
CFG = ["B0", "K01", "K02", "K03", "K04", "K05", "K06", "K07", "K08", "K09", "K10", "K11", "K12"]
NAME = dict(B0="base (-2R latch)", K01="BLOCK on UP-conf", K02="SCALE 0.5 pre-conf / 0 UP", K03="SCALE 0.5 pre-conf / 0.5 UP",
            K04="RAMP 0.5x < 10:30", K05="RAMP 0.5x < 10:45", K06="RAMP 0.5x < 11:15", K07="RAMP<10:30 + BLOCK",
            K08="SPY>=+0.20% skip", K09="SPY>=+0.40% skip", K10="SPY>=+0.20% half", K11="SPY>=+0.40% half",
            K12="-1R latch after UP-conf")
out = []


def p(*a):
    out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)


def split(d):
    return "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else ("FWD" if d <= "2026-11-04" else "LIVE"))


# ------------------------------------------------------------------ W60 compass history (ECG1 code, state15.hist)
spec = importlib.util.spec_from_file_location("state15", ROOT / "research/bdi/hc1/state15.py")
a0 = sys.argv; sys.argv = ["x", str(S)]; s15 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s15); sys.argv = a0
st = s15.hist().dropna(subset=["fo"]).sort_values(["date", "T"]).reset_index(drop=True)
st = st[~st.date.between(*LOCK)]
sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
st["s"] = sg(st.fo)
base = st.s + sg(st.vw) + np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0)) + \
    np.where((st.s == sg(st.qqq_fo)) & (st.s == sg(st.iwm_fo)), st.s, 0)
piv = st.pivot(index="date", columns="T", values="s")
pW = np.zeros(len(st), int); nm = np.zeros(len(st), int)
for T in sorted(st["T"].unique()):
    mk = [t for t in piv.columns if T - 60 < t <= T]
    sub = piv[mk]; same = sub.eq(sub[T], axis=0).all(axis=1) & (sub[T] != 0)
    i = (st["T"] == T).values
    pW[i] = np.where(same.reindex(st.date[i]).values, piv[T].reindex(st.date[i]).values, 0); nm[i] = len(mk)
v = base.values + pW
st["W60"] = np.where((v >= 4) & (pW == 1) & (nm >= 2), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pW == -1) & (nm >= 2), -2,
                     np.where(v <= -2, -1, 0))))
W = st.pivot(index="date", columns="T", values="W60")

# live compass (production compute) for the live sessions
LC = pd.read_parquet(S / "live_compass.parquet")
LC["T"] = LC["T"].str[:2].astype(int) * 60 + LC["T"].str[3:].astype(int)
LC["W60"] = LC.w60.map({"UP-confirmed": 2, "leaning up": 1, "neutral": 0, "leaning down": -1, "DOWN-confirmed": -2}).fillna(0)
WL = LC.pivot(index="date", columns="T", values="W60")


def comp_rows(Wm):
    """date -> (marks array, readings array)"""
    return {d: (np.array(Wm.columns, int), Wm.loc[d].fillna(0).values.astype(int)) for d in Wm.index}


CH = comp_rows(W); CLV = comp_rows(WL)

# ------------------------------------------------------------------ SPY 1-min (history cache + live fetch)
def spy_days(b):
    b = b.copy(); b.index = pd.to_datetime(b.index)
    if b.index.tz is None:
        b.index = b.index.tz_localize("America/New_York")
    b = b.tz_convert("America/New_York")
    m = b.index.hour * 60 + b.index.minute
    b = b[(m >= 570) & (m < 960)]
    m = (b.index.hour * 60 + b.index.minute).values - 570
    d = b.index.strftime("%Y-%m-%d").values
    D = {}
    for day in pd.unique(d):
        if LOCK[0] <= day <= LOCK[1]:
            continue
        k = d == day; mm = m[k]
        C = np.full(390, np.nan); C[mm] = b.close.values[k]; C = pd.Series(C).ffill().values
        H = np.full(390, np.nan); H[mm] = b.high.values[k]
        L = np.full(390, np.nan); L[mm] = b.low.values[k]
        D[day] = dict(o=float(b.open.values[k][0]), c=C, h=H, l=L, last=int(mm.max()))
    return D


SPY = spy_days(pd.read_parquet(ROOT / "data/cache_hist/1Min/SPY.parquet")[["open", "high", "low", "close"]])
ls = pd.read_parquet(S / "live_spy.parquet")
for d, g in ls.groupby("date"):
    if d not in SPY:
        SPY.update(spy_days(g[["open", "high", "low", "close"]]))
assert not any(LOCK[0] <= d <= LOCK[1] for d in SPY)


def spy_fo(d, e):
    x = SPY.get(d)
    if x is None:
        return np.nan
    i = min(max(e - 571, 0), 389)
    return x["c"][i] / x["o"] - 1


# ------------------------------------------------------------------ 1. hypothesis check
p("# L3LEASH - study output (Educational only - not financial advice)\n")
p("## 1. Hypothesis: SPY up from its open at 10:30 / 11:00 / 11:15 -> how much further by the close?")
full = {d: x for d, x in SPY.items() if x["last"] >= 385 and d <= "2026-11-09"}
hy = []
for d, x in full.items():
    for T in (630, 660, 675):
        i = T - 571; pT = x["c"][i]; fo = pT / x["o"] - 1
        cl = x["c"][-1]
        hy.append(dict(date=d, split=split(d) if d <= "2026-11-04" else "LIVE", T=T, fo=fo * 100, rest=(cl / pT - 1) * 100,
                       maxup=(np.nanmax(x["h"][i + 1:]) / pT - 1) * 100, maxdn=(np.nanmin(x["l"][i + 1:]) / pT - 1) * 100,
                       oc=(cl / x["o"] - 1) * 100))
H = pd.DataFrame(hy); H.to_csv(HERE / "hypothesis_days.csv", index=False)
hrows = []
for T in (630, 660, 675):
    for grp, cond in (("up >0", lambda h: h.fo > 0), ("up >=+0.20%", lambda h: h.fo >= 0.20), ("up >=+0.40%", lambda h: h.fo >= 0.40),
                      ("down <0 (mirror)", lambda h: h.fo < 0), ("all days", lambda h: h.fo == h.fo)):
        for sp in ("ALL", "TRAIN", "VALID", "FWD+LIVE"):
            h = H[H["T"] == T]
            if sp == "FWD+LIVE":
                h = h[h.split.isin(["FWD", "LIVE"])]
            elif sp != "ALL":
                h = h[h.split == sp]
            h = h[cond(h)]
            if not len(h):
                continue
            r = h.rest if not grp.startswith("down") else -h.rest      # mirror: further move in the morning direction
            hrows.append(dict(T=f"{T // 60}:{T % 60:02d}", group=grp, split=sp, n=len(h), mean=r.mean(), p10=r.quantile(.1),
                              p25=r.quantile(.25), median=r.median(), p75=r.quantile(.75), p90=r.quantile(.9),
                              further=(r > 0).mean(), further_gt25=(r > 0.25).mean(), further_gt50=(r > 0.5).mean(),
                              back_lt_m25=(r < -0.25).mean(),
                              crosses_open=((h.oc < 0) if not grp.startswith("down") else (h.oc > 0)).mean() if grp != "all days" else np.nan,
                              max_further=(h.maxup if not grp.startswith("down") else -h.maxdn).mean(),
                              max_against=(-h.maxdn if not grp.startswith("down") else h.maxup).mean()))
HY = pd.DataFrame(hrows); HY.to_csv(HERE / "hypothesis.csv", index=False, float_format="%.3f")
p(HY[HY.split == "ALL"].to_string(index=False, float_format=lambda v: f"{v:.2f}"))
p("\n(by split for 'up >0' and 'up >=+0.20%')")
p(HY[HY.group.isin(["up >0", "up >=+0.20%"]) & (HY.split != "ALL")].to_string(index=False, float_format=lambda v: f"{v:.2f}"))

# ------------------------------------------------------------------ trades
T = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/*.parquet"))))
T = T[T.setup.isin(SETUPS)].copy()
T = T[~T.date.between(*LOCK)]
assert not T.date.between(*LOCK).any() and (T.side == -1).all()
T["e"] = (T.tod // 100) * 60 + T.tod % 100
T["x"] = (T.xtod // 100) * 60 + T.xtod % 100
T["split"] = T.date.map(split)
T = T.reset_index(drop=True)


def comp_feats(df, CHm):
    """per trade: W60 at the latest mark <= entry, first-confirmation flag before entry, any UP-conf so far."""
    w = np.zeros(len(df), int); pre = np.ones(len(df), bool); upso = np.zeros(len(df), bool); ok = np.zeros(len(df), bool)
    for i, (d, e) in enumerate(zip(df.date.values, df.e.values)):
        c = CHm.get(d)
        if c is None:
            continue
        mk, r = c; k = mk <= e
        ok[i] = True
        if not k.any():
            continue
        rr = r[k]
        w[i] = rr[-1]; pre[i] = not (np.abs(rr) == 2).any(); upso[i] = (rr == 2).any()
    return w, pre, upso, ok


def weights(df, cfg):
    w = df.w60.values; pre = df.pre.values; e = df.e.values; fo = df.spy_fo.values * 100
    one = np.ones(len(df))
    if cfg in ("B0", "K12"):
        return one
    if cfg == "K01":
        return np.where(w == 2, 0.0, 1.0)
    if cfg in ("K02", "K03"):
        up = 0.0 if cfg == "K02" else 0.5
        return np.where(w == 2, up, np.where(pre, 0.5, 1.0))
    if cfg in ("K04", "K05", "K06"):
        cut = dict(K04=630, K05=645, K06=675)[cfg]
        return np.where(e < cut, 0.5, 1.0)
    if cfg == "K07":
        return np.where(w == 2, 0.0, np.where(e < 630, 0.5, 1.0))
    if cfg in ("K08", "K09", "K10", "K11"):
        th = 0.20 if cfg in ("K08", "K10") else 0.40
        lo = 0.0 if cfg in ("K08", "K09") else 0.5
        return np.where(fo >= th, lo, 1.0)
    raise ValueError(cfg)


def sim_day(g, wt, cfg, caps=True):
    """g: one setup-day sorted by entry. Returns per-trade taken weight (0 = not taken)."""
    e = g.e.values; x = g.x.values; r = g.r.values; sym = g.symbol.values; upso = g.upso.values
    took = np.zeros(len(g)); open_ = []                      # (exit, sym, Rcontrib)
    real = 0.0
    for i in range(len(g)):
        still = []
        for (xx, s, rc) in open_:
            if xx <= e[i]:
                real += rc
            else:
                still.append((xx, s, rc))
        open_ = still
        lim = -1.0 if (cfg == "K12" and upso[i]) else -2.0
        if real <= lim + 1e-12:
            continue
        if wt[i] <= 0:
            continue
        if caps and (len(open_) >= 30 or sum(1 for o in open_ if o[1] == sym[i]) >= 3):
            continue
        took[i] = wt[i]
        open_.append((x[i], sym[i], wt[i] * r[i]))
    return took


def run(df, caps=True):
    """df with columns setup,date,e,x,r,symbol,w60,pre,upso,spy_fo -> dict cfg -> per-trade taken weight"""
    df = df.sort_values(["setup", "date", "e", "x"]).reset_index(drop=True)
    res = {}
    for cfg in CFG:
        wt = weights(df, cfg)
        took = np.zeros(len(df))
        for _, idx in df.groupby(["setup", "date"]).indices.items():
            took[idx] = sim_day(df.iloc[idx], wt[idx], cfg, caps)
        res[cfg] = took
    return df, res


w, pre, upso, ok = comp_feats(T, CH)
T["w60"], T["pre"], T["upso"], T["has_c"] = w, pre, upso, ok
T["spy_fo"] = [spy_fo(d, e) for d, e in zip(T.date.values, T.e.values)]
p(f"\nlab trades {len(T):,} ({T.setup.nunique()} setups); compass coverage {T.has_c.mean():.1%}; SPY coverage {T.spy_fo.notna().mean():.1%}")
T, RES = run(T)

# ------------------------------------------------------------------ live trades
L = []
for acct, db in (("Primary", "primary"), ("Testing1", "testing")):
    c = sqlite3.connect(S / "j" / f"{db}.db")
    t = pd.read_sql("select run_id, symbol, strategy setup, date, entry_time, exit_time, entry, stop, shares, pnl_adj, r_multiple, meta "
                    "from trades where strategy=? and run_id in (1,2)", c, params=(MAIN,))
    why = t.meta.fillna("").str.extract(r"why=(.*)$")[0]
    t = t[(t.run_id == 1) | ((acct == "Primary") & (why == "setup daily loss limit"))].copy()
    t["r"] = np.where(t.run_id == 1, t.pnl_adj / ((t.entry - t.stop).abs() * t.shares), t.r_multiple)
    for col, k in (("entry_time", "e"), ("exit_time", "x")):
        ts = pd.to_datetime(t[col], utc=True, format="mixed").dt.tz_convert("America/New_York")
        t[k] = ts.dt.hour * 60 + ts.dt.minute + ts.dt.second / 60
    t["account"] = acct
    L.append(t.dropna(subset=["r", "x"]))
L = pd.concat(L, ignore_index=True)
L["e"] = L.e.astype(float)
w, pre, upso, ok = comp_feats(L, CLV)
L["w60"], L["pre"], L["upso"], L["has_c"] = w, pre, upso, ok
L["spy_fo"] = [spy_fo(d, int(e)) for d, e in zip(L.date.values, L.e.values)]
L["setup"] = L.account + ":" + L.setup
L["split"] = np.where(L.date == "2026-11-10", "LIVE-11-10 (partial, in-sample)", "LIVE")
p(f"live trades {len(L)} (Primary run1 {int(((L.account == 'Primary') & (L.run_id == 1)).sum())}, Primary latch what-ifs "
  f"{int(((L.account == 'Primary') & (L.run_id == 2)).sum())}, Testing1 {int((L.account == 'Testing1').sum())}); compass coverage {L.has_c.mean():.1%}")
L, RESL = run(L, caps=False)


# ------------------------------------------------------------------ metrics
def metrics(df, res, setup, sp):
    m = (df.setup == setup) & (df.split == sp)
    if not m.any():
        return []
    g = df[m]; idx = np.where(m)[0]
    bday = pd.Series(res["B0"][idx] * g.r.values).groupby(g.date.values).sum()
    red = bday[bday < 0].index; grn = bday[bday > 0].index
    rows = []
    for cfg in CFG:
        tk = res[cfg][idx]; rr = tk * g.r.values
        day = pd.Series(rr).groupby(g.date.values).sum().reindex(bday.index).fillna(0)
        n = int((tk > 0).sum()); tot = day.sum()
        dt = day.mean() / (day.std(ddof=1) / math.sqrt(len(day))) if len(day) > 2 and day.std() > 0 else np.nan
        dl = day - bday
        pt = dl.mean() / (dl.std(ddof=1) / math.sqrt(len(dl))) if len(dl) > 2 and dl.std() > 0 else np.nan
        best = day.max(); bshare = best / tot if tot > 0 else np.nan
        nb = int((tk[g.date.values == day.idxmax()] > 0).sum()) if len(day) else 0
        rows.append(dict(setup=setup, split=sp, cfg=cfg, days=len(day), trades=n, size_units=round(tk.sum(), 1), R=tot,
                         R_per_trade=tot / n if n else np.nan, R_per_unit=tot / tk.sum() if tk.sum() else np.nan, day_t=dt,
                         dR=tot - bday.sum(), pair_t=pt,
                         red_days=len(red), red_R=day.loc[red].sum(), red_base=bday.loc[red].sum(),
                         red_removed=day.loc[red].sum() - bday.loc[red].sum(),
                         green_days_base=len(grn), green_R=day.loc[grn].sum(), green_base=bday.loc[grn].sum(),
                         green_given=bday.loc[grn].sum() - day.loc[grn].sum(),
                         green_days=int((day > 0).sum()), worst_day=day.min(), worst5=day.nsmallest(5).sum(),
                         best_day=best, best_share=bshare,
                         avgR_wo_best=(tot - best) / (n - nb) if n - nb > 0 else np.nan))
    return rows


M = []
for s in SETUPS:
    for sp in ("TRAIN", "VALID", "FWD"):
        M += metrics(T, RES, s, sp)
for s in L.setup.unique():
    for sp in L.split.unique():
        M += metrics(L, RESL, s, sp)
M = pd.DataFrame(M)
M["red_removed_pct"] = M.red_removed / M.red_base.abs() * 100
M["green_given_pct"] = M.green_given / M.green_base.abs() * 100
M.to_csv(HERE / "configs.csv", index=False, float_format="%.4f")
cols = ["cfg", "trades", "R", "R_per_trade", "day_t", "dR", "pair_t", "red_base", "red_removed", "red_removed_pct",
        "green_base", "green_given", "green_given_pct", "green_days", "worst_day", "worst5", "best_share", "avgR_wo_best"]
fmt = lambda v: f"{v:.2f}"
for s in [MAIN]:
    for sp in ("TRAIN", "VALID", "FWD"):
        p(f"\n## {s} - {sp}")
        p(M[(M.setup == s) & (M.split == sp)][cols].to_string(index=False, float_format=fmt))
for s in sorted(L.setup.unique()):
    for sp in sorted(L.split.unique()):
        x = M[(M.setup == s) & (M.split == sp)]
        if len(x):
            p(f"\n## {s} - {sp}")
            p(x[cols].to_string(index=False, float_format=fmt))

# ------------------------------------------------------------------ pass rule (pre-declared)
BAR = max(1.5, math.sqrt(2 * math.log(12)))
p(f"\n## Pass rule (pre-declared): VALID and FWD each: red-day R removed >= 20% of base red-day loss, green-day R given up "
  f"<= 10%, total dR >= 0; TRAIN dR >= 0; sisters (VALID): none worse by > 5% of |its base R|. Bar for the paired VALID day-t "
  f"(N 12): {BAR:.2f} (reported).")
ver = []
for cfg in CFG[1:]:
    g = {sp: M[(M.setup == MAIN) & (M.split == sp) & (M.cfg == cfg)].iloc[0] for sp in ("TRAIN", "VALID", "FWD")}
    c1 = all(g[sp].red_removed_pct >= 20 and g[sp].green_given_pct <= 10 and g[sp].dR >= 0 for sp in ("VALID", "FWD"))
    c2 = g["TRAIN"].dR >= 0
    sv = M[(M.setup.isin(SIS)) & (M.split == "VALID") & (M.cfg == cfg)]
    sb = M[(M.setup.isin(SIS)) & (M.split == "VALID") & (M.cfg == "B0")].set_index("setup").R
    worse = sv[sv.dR < -0.05 * sv.setup.map(sb).abs()]
    sf = M[(M.setup.isin(SIS)) & (M.split == "FWD") & (M.cfg == cfg)]
    ver.append(dict(cfg=cfg, name=NAME[cfg], **{f"{sp}_dR": g[sp].dR for sp in ("TRAIN", "VALID", "FWD")},
                    **{f"{sp}_red_rm%": g[sp].red_removed_pct for sp in ("TRAIN", "VALID", "FWD")},
                    **{f"{sp}_green_gv%": g[sp].green_given_pct for sp in ("TRAIN", "VALID", "FWD")},
                    VALID_pair_t=g["VALID"].pair_t,
                    sis_valid_better=int((sv.dR > 0).sum()), sis_valid_worse=int((sv.dR < 0).sum()),
                    sis_valid_dR=sv.dR.sum(), sis_valid_worse_gt5=len(worse),
                    sis_fwd_better=int((sf.dR > 0).sum()), sis_fwd_worse=int((sf.dR < 0).sum()), sis_fwd_dR=sf.dR.sum(),
                    PASS=bool(c1 and c2 and len(worse) == 0)))
V = pd.DataFrame(ver); V.to_csv(HERE / "verdict.csv", index=False, float_format="%.3f")
p(V.to_string(index=False, float_format=lambda v: f"{v:.1f}"))

# sisters per config, per split
p("\n## Sisters: dR vs base per setup (TRAIN / VALID / FWD)")
for cfg in CFG[1:]:
    x = M[(M.setup.isin(SIS)) & (M.cfg == cfg) & M.split.isin(["TRAIN", "VALID", "FWD"])].pivot(index="setup", columns="split", values="dR")
    p(f"{cfg} {NAME[cfg]}: " + "; ".join(f"{SHORT[s]} T {r.TRAIN:+.0f} V {r.VALID:+.0f} F {r.FWD:+.0f}"
                                          for s, r in x[["TRAIN", "VALID", "FWD"]].iterrows()))

# ------------------------------------------------------------------ diagnostics (not configs): base L3 by entry window x SPY state
g = T[(T.setup == MAIN)].copy(); g["took"] = RES["B0"][g.index]; g = g[g.took > 0]
g["win"] = pd.cut(g.e, [0, 630, 660, 720, 840, 1000], right=False, labels=["<10:30", "10:30-11", "11-12", "12-14", ">=14"])
g["spy"] = pd.cut(g.spy_fo * 100, [-99, -0.2, 0.2, 0.4, 99], right=False, labels=["SPY<=-0.2", "flat", "+0.2..0.4", ">=+0.4"])
g["comp"] = np.where(g.w60 == 2, "UP-conf", np.where(g.w60 == -2, "DOWN-conf", "unconf"))
for sp in ("TRAIN", "VALID", "FWD"):
    x = g[g.split == sp]
    p(f"\n## diag {MAIN} base trades {sp}: avg R (n) by entry window x SPY from open")
    p(x.pivot_table(index="win", columns="spy", values="r", aggfunc=lambda v: f"{v.mean():+.3f} ({len(v)})", observed=False).to_string())
    p(x.pivot_table(index="win", columns="comp", values="r", aggfunc=lambda v: f"{v.mean():+.3f} ({len(v)})", observed=False).to_string())
# SPY day type for L3 base day R
dd = g.groupby("date").agg(R=("r", "sum"), split=("split", "first")).reset_index()
dd["oc"] = dd.date.map(lambda d: (SPY[d]["c"][-1] / SPY[d]["o"] - 1) * 100 if d in SPY else np.nan)
dd["type"] = np.where(dd.oc > 0.25, "SPY up", np.where(dd.oc < -0.25, "SPY down", "flat"))
p("\n## diag base day R by SPY day type (open->close +-0.25%)")
p(dd.groupby(["split", "type"]).R.agg(["size", "sum", "mean", lambda v: (v < 0).mean()]).to_string(float_format=lambda v: f"{v:.2f}"))
dd.to_csv(HERE / "l3_base_days.csv", index=False, float_format="%.4f")
(HERE / "study_out.txt").write_text("\n".join(out) + "\n\nEducational only - not financial advice.\n")
