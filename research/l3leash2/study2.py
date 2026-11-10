"""L3LEASH-2 (owner 2026-11-10 ~13:30 ET "L3LEASH-2 yes"): re-run the L3LEASH leash family on a lab universe restricted to
names that were shortable + easy-to-borrow, since live only shorts those (913+ Primary L3 signals skipped "not shortable/ETB").
Research only - no config / setup / exit change.

Pre-declared before any restricted score was read:
  ETB source  Alpaca `shortable and easy_to_borrow` - exactly what live checks (AlpacaBroker.can_short, runner.py
              "not shortable/ETB" skip). History of the flags = every committed morning universe.csv on mcf-data /
              mcf-data-testing / mcf-data-testing2 (git log, built ~08:45-09:30 ET, 2026-10-07..11-09, 22 days).
              Alpaca keeps no history, so for TRAIN / VALID the flags must be carried back in time (proxy).
  E90 (main)  keep a lab trade when its symbol was shortable+ETB on >= 90% of the snapshot days it appeared in.
              Symbols never seen in a snapshot are dropped (unknown).
  E100        sensitivity, base only: ETB on 100% of snapshot days.
  FWD-day     sensitivity, base only, FWD split only: that day's own flag (latest snapshot <= day; 10-06 uses 10-07).
  Leashes     K01-K12 exactly as research/l3leash/study.py (same weights, same -2R latch, caps, costs), re-scored on the
              E90 base for the main setup and every sister (sisters restricted the same way).
  Pass rule   unchanged: VALID and FWD each red-day cut >= 20%, green give-up <= 10%, dR >= 0; TRAIN dR >= 0; no sister
              worse by > 5% of |its base R| in VALID. Paired VALID day-t bar now uses N = 24 (12 L3LEASH + 12 here):
              sqrt(2 ln 24) = 2.52 (N 12 bar 2.23 also shown).
Configs counted here: 12 leashes + 2 proxy sensitivities (E100, FWD-day) = 14 (lineage total 26).

Usage: python research/l3leash2/study2.py <scratch>
  needs <scratch>/j/{primary,testing,testing2}.db (git show origin/mcf-data[-testing|-testing2]:journal.db) and
  <scratch>/live_compass.parquet + live_spy.parquet (python research/l3leash/live_compass.py <scratch>).
Locked block 2024-11-01..2025-02-28 never read (filtered at load and asserted). Educational only - not financial advice."""
import glob, importlib.util, io, math, sqlite3, subprocess, sys
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


# ------------------------------------------------------------------ 1. ETB flag history from git (universe.csv snapshots)
def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout


snaps = []
for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
    for h in git("log", "--format=%H", f"origin/{br}", "--", "universe.csv").split():
        u = pd.read_csv(io.StringIO(git("show", f"{h}:universe.csv")), usecols=["symbol", "shortable", "easy_to_borrow", "built_at"])
        snaps.append(u)
U = pd.concat(snaps).drop_duplicates(["symbol", "built_at"])
U["day"] = pd.to_datetime(U.built_at, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
U["ok"] = (U.shortable.astype(bool) & U.easy_to_borrow.astype(bool)).astype(float)
DF = U.groupby(["day", "symbol"]).ok.mean().reset_index()
SDAYS = sorted(DF.day.unique())
FLAG = {(r.day, r.symbol): r.ok >= 0.5 for r in DF.itertuples()}
RATE = DF.groupby("symbol").ok.mean()
RATE_H1 = DF[DF.day <= "2026-10-23"].groupby("symbol").ok.mean()
p("# L3LEASH-2 - study output (Educational only - not financial advice)\n")
p(f"## 1. ETB flag history: {len(SDAYS)} snapshot days {SDAYS[0]}..{SDAYS[-1]}, {DF.symbol.nunique():,} symbols, "
  f"conflicting same-day flags across branches: {int(((DF.ok > 0) & (DF.ok < 1)).sum())}")


def day_flag(d, s):
    pr = [x for x in SDAYS if x <= d] or SDAYS[:1]
    return FLAG.get((pr[-1], s), np.nan)


# ------------------------------------------------------------------ 2. validate against live signal decisions
sig = []
for acct, db in (("Primary", "primary"), ("Testing1", "testing"), ("Testing2", "testing2")):
    c = sqlite3.connect(S / "j" / f"{db}.db")
    s = pd.read_sql("select day, symbol, strategy, status, reason from signals where side=-1", c); s["acct"] = acct; sig.append(s)
sig = pd.concat(sig, ignore_index=True)
sig["nsh"] = sig.reason.fillna("").str.contains("not shortable")
# a symbol-day counts as 'passed the ETB check' when any of its signals got past it (traded or skipped later for another reason)
sd = sig.groupby(["acct", "day", "symbol", "strategy"]).agg(nsh=("nsh", "max"), past=("nsh", lambda v: (~v).any())).reset_index()
sd = sd[sd.nsh != sd.past]                 # unambiguous symbol-days only
sd["live_etb"] = sd.past
sd["flag_day"] = [day_flag(d, s) for d, s in zip(sd.day, sd.symbol)]
sd["E90"] = sd.symbol.map(RATE) >= 0.9
sd["E100"] = sd.symbol.map(RATE) >= 0.999
sd["E90_h1"] = sd.symbol.map(RATE_H1) >= 0.9
sd["known"] = sd.symbol.isin(RATE.index)
vrows = []
for scope, m in (("L3-fromopen signals", sd.strategy == MAIN), ("all short signals", sd.strategy == sd.strategy)):
    for col, mm in (("same-day snapshot flag", m), ("E90 (symbol rate >= 90%)", m), ("E100", m),
                    ("E90 from 10-07..10-23 only, scored on live 10-26..11-10 (out of time)", m & (sd.day >= "2026-10-26"))):
        c = {"same-day snapshot flag": "flag_day", "E90 (symbol rate >= 90%)": "E90", "E100": "E100"}.get(col, "E90_h1")
        x = sd[mm & sd[c].notna() & ((c != "E90_h1") | sd.symbol.isin(RATE_H1.index))]
        pr = x[c].astype(bool); y = x.live_etb
        vrows.append(dict(scope=scope, proxy=col, symbol_days=len(x), agree=(pr == y).mean(), live_etb_share=y.mean(),
                          proxy_etb_share=pr.mean(), etb_called_not=int((y & ~pr).sum()), not_called_etb=int((~y & pr).sum())))
VAL = pd.DataFrame(vrows); VAL.to_csv(HERE / "etb_validation.csv", index=False, float_format="%.4f")
p("\n## 2. Proxy validation vs live decisions (symbol-days; live_etb = got past the ETB check)")
p(VAL.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

# ------------------------------------------------------------------ 3. compass + SPY (as L3LEASH)
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
LC = pd.read_parquet(S / "live_compass.parquet")
LC["T"] = LC["T"].str[:2].astype(int) * 60 + LC["T"].str[3:].astype(int)
LC["W60"] = LC.w60.map({"UP-confirmed": 2, "leaning up": 1, "neutral": 0, "leaning down": -1, "DOWN-confirmed": -2}).fillna(0)
WL = LC.pivot(index="date", columns="T", values="W60")
comp_rows = lambda Wm: {d: (np.array(Wm.columns, int), Wm.loc[d].fillna(0).values.astype(int)) for d in Wm.index}
CH = comp_rows(W); CLV = comp_rows(WL)


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
        D[day] = dict(o=float(b.open.values[k][0]), c=C)
    return D


SPY = spy_days(pd.read_parquet(ROOT / "data/cache_hist/1Min/SPY.parquet")[["open", "high", "low", "close"]])
for d, g in pd.read_parquet(S / "live_spy.parquet").groupby("date"):
    if d not in SPY:
        SPY.update(spy_days(g[["open", "high", "low", "close"]]))
assert not any(LOCK[0] <= d <= LOCK[1] for d in SPY)


def spy_fo(d, e):
    x = SPY.get(d)
    if x is None:
        return np.nan
    return x["c"][min(max(e - 571, 0), 389)] / x["o"] - 1


def comp_feats(df, CHm):
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
    if cfg in ("B0", "K12"):
        return np.ones(len(df))
    if cfg == "K01":
        return np.where(w == 2, 0.0, 1.0)
    if cfg in ("K02", "K03"):
        return np.where(w == 2, 0.0 if cfg == "K02" else 0.5, np.where(pre, 0.5, 1.0))
    if cfg in ("K04", "K05", "K06"):
        return np.where(e < dict(K04=630, K05=645, K06=675)[cfg], 0.5, 1.0)
    if cfg == "K07":
        return np.where(w == 2, 0.0, np.where(e < 630, 0.5, 1.0))
    th = 0.20 if cfg in ("K08", "K10") else 0.40
    return np.where(fo >= th, 0.0 if cfg in ("K08", "K09") else 0.5, 1.0)


def sim_day(g, wt, cfg, caps=True):
    e = g.e.values; x = g.x.values; r = g.r.values; sym = g.symbol.values; upso = g.upso.values
    took = np.zeros(len(g)); open_ = []; real = 0.0
    for i in range(len(g)):
        still = []
        for (xx, s, rc) in open_:
            if xx <= e[i]:
                real += rc
            else:
                still.append((xx, s, rc))
        open_ = still
        lim = -1.0 if (cfg == "K12" and upso[i]) else -2.0
        if real <= lim + 1e-12 or wt[i] <= 0:
            continue
        if caps and (len(open_) >= 30 or sum(1 for o in open_ if o[1] == sym[i]) >= 3):
            continue
        took[i] = wt[i]; open_.append((x[i], sym[i], wt[i] * r[i]))
    return took


def run(df, cfgs=CFG, caps=True):
    df = df.sort_values(["setup", "date", "e", "x"]).reset_index(drop=True)
    res = {}
    for cfg in cfgs:
        wt = weights(df, cfg); took = np.zeros(len(df))
        for _, idx in df.groupby(["setup", "date"]).indices.items():
            took[idx] = sim_day(df.iloc[idx], wt[idx], cfg, caps)
        res[cfg] = took
    return df, res


# ------------------------------------------------------------------ 4. lab trades, restricted
T0 = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/*.parquet"))))
T0 = T0[T0.setup.isin(SETUPS)].copy()
T0 = T0[~T0.date.between(*LOCK)]
assert not T0.date.between(*LOCK).any() and (T0.side == -1).all()
T0["e"] = (T0.tod // 100) * 60 + T0.tod % 100
T0["x"] = (T0.xtod // 100) * 60 + T0.xtod % 100
T0["split"] = T0.date.map(split)
T0 = T0[T0.split != "LIVE"].reset_index(drop=True)
T0["rate"] = T0.symbol.map(RATE)
T0["E90"] = T0.rate >= 0.9
T0["E100"] = T0.rate >= 0.999
T0["Eday"] = [sp == "FWD" and day_flag(d, s) == True for d, s, sp in zip(T0.date, T0.symbol, T0.split)]  # noqa: E712
w, pre, upso, ok = comp_feats(T0, CH)
T0["w60"], T0["pre"], T0["upso"], T0["has_c"] = w, pre, upso, ok
T0["spy_fo"] = [spy_fo(d, e) for d, e in zip(T0.date.values, T0.e.values)]
cov = T0.groupby("setup").agg(trades=("r", "size"), syms=("symbol", "nunique"), unknown=("rate", lambda v: v.isna().mean()),
                              E90=("E90", "mean"), E100=("E100", "mean"))
p("\n## 3. Lab coverage by setup (share of lab trades kept by each proxy; unknown = symbol never in a snapshot -> dropped)")
p(cov.to_string(float_format=lambda v: f"{v:.3f}"))

# base under each universe (B0 only) - all setups
bases = {}
for uni in ("ALL", "E90", "E100", "NOT-E90", "Eday"):
    sub = T0 if uni == "ALL" else (T0[~T0.E90] if uni == "NOT-E90" else T0[T0[uni]])
    if uni == "Eday":
        sub = sub[sub.split == "FWD"]
    d_, r_ = run(sub, ["B0"])
    d_["took"] = r_["B0"]; bases[uni] = d_

T, RES = run(T0[T0.E90].copy())

# ------------------------------------------------------------------ 5. live trades (already ETB-only by construction)
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
L = L[L.date <= "2026-11-09"]                       # 11-10 is in progress / in-sample: left to the shadow scoreboard
w, pre, upso, ok = comp_feats(L, CLV)
L["w60"], L["pre"], L["upso"], L["has_c"] = w, pre, upso, ok
L["spy_fo"] = [spy_fo(d, int(e)) for d, e in zip(L.date.values, L.e.values)]
L["setup"] = L.account + ":" + L.setup
L["split"] = "LIVE"
L["in_lab_universe"] = L.symbol.isin(set(T0.symbol))
p(f"\nlive trades {len(L)}; share whose symbol is in the lab universe: {L.in_lab_universe.mean():.1%}; "
  f"live trades with r_run1 (Primary {int(((L.account == 'Primary') & (L.run_id == 1)).sum())}, what-ifs "
  f"{int(((L.account == 'Primary') & (L.run_id == 2)).sum())}, Testing1 {int((L.account == 'Testing1').sum())})")
L, RESL = run(L, caps=False)

# ------------------------------------------------------------------ 6. restricted base vs live (avg R, win rate)
cmp = []
for uni, d_ in bases.items():
    for s in SETUPS:
        for sp in ("TRAIN", "VALID", "FWD"):
            g = d_[(d_.setup == s) & (d_.split == sp) & (d_.took > 0)]
            if not len(g):
                continue
            dayR = g.groupby("date").r.sum()
            cmp.append(dict(universe=uni, setup=s, split=sp, trades=len(g), days=g.date.nunique(), R=g.r.sum(), avgR=g.r.mean(),
                            win=(g.r > 0).mean(), day_t=dayR.mean() / (dayR.std(ddof=1) / math.sqrt(len(dayR))) if len(dayR) > 2 else np.nan,
                            avgR_wo_best=(g.r.sum() - dayR.max()) / (len(g) - (g.date == dayR.idxmax()).sum()) if len(dayR) > 1 else np.nan,
                            best_share=dayR.max() / g.r.sum() if g.r.sum() > 0 else np.nan))
for acct in ("Primary", "Testing1"):
    m = (L.setup == f"{acct}:{MAIN}") & (RESL["B0"] > 0)
    g = L[m]; dayR = g.groupby("date").r.sum()
    cmp.append(dict(universe="LIVE (sim -2R latch)", setup=f"{acct}:{MAIN}", split="LIVE", trades=len(g), days=g.date.nunique(), R=g.r.sum(),
                    avgR=g.r.mean(), win=(g.r > 0).mean(), day_t=dayR.mean() / (dayR.std(ddof=1) / math.sqrt(len(dayR))),
                    avgR_wo_best=(g.r.sum() - dayR.max()) / (len(g) - (g.date == dayR.idxmax()).sum()),
                    best_share=dayR.max() / g.r.sum() if g.r.sum() > 0 else np.nan))
CMP = pd.DataFrame(cmp); CMP.to_csv(HERE / "bases.csv", index=False, float_format="%.4f")
p("\n## 4. Base (B0, -2R latch, caps, costs) by universe vs live")
for s in [MAIN, SIS[0], SIS[2], SIS[3]]:
    p(f"\n### {s}")
    p(CMP[CMP.setup == s].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
p("\n### live")
p(CMP[CMP.split == "LIVE"].to_string(index=False, float_format=lambda v: f"{v:.3f}"))

# same-days check: lab E90 vs live on the live days (FWD overlap)
ov = []
for acct in ("Primary", "Testing1"):
    g = L[(L.setup == f"{acct}:{MAIN}") & (RESL["B0"] > 0)]
    days = sorted(g.date.unique())
    lb = bases["E90"]; lb = lb[(lb.setup == MAIN) & (lb.took > 0) & lb.date.isin(days)]
    lbA = bases["ALL"]; lbA = lbA[(lbA.setup == MAIN) & (lbA.took > 0) & lbA.date.isin(days)]
    ov.append(dict(account=acct, days=f"{len([d for d in days if d <= '2026-11-04'])} lab-overlap days of {len(days)}",
                   live_R=g[g.date <= "2026-11-04"].r.sum(), live_n=int((g.date <= "2026-11-04").sum()),
                   lab_E90_R=lb.r.sum(), lab_E90_n=len(lb), lab_ALL_R=lbA.r.sum(), lab_ALL_n=len(lbA),
                   symbol_day_overlap=len(set(zip(g.date, g.symbol)) & set(zip(lb.date, lb.symbol))) / max(1, len(set(zip(g.date, g.symbol))))))
OV = pd.DataFrame(ov)
p("\n## 4b. Same days, lab vs live (L3-fromopen, days <= 11-04)")
p(OV.to_string(index=False, float_format=lambda v: f"{v:.2f}"))


# ------------------------------------------------------------------ 7. metrics / verdict (as L3LEASH)
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
        best = day.max(); nb = int((tk[g.date.values == day.idxmax()] > 0).sum()) if len(day) else 0
        rows.append(dict(setup=setup, split=sp, cfg=cfg, days=len(day), trades=n, R=tot, R_per_trade=tot / n if n else np.nan,
                         win=float((rr[tk > 0] > 0).mean()) if n else np.nan, day_t=dt, dR=tot - bday.sum(), pair_t=pt,
                         red_base=bday.loc[red].sum(), red_removed=day.loc[red].sum() - bday.loc[red].sum(),
                         green_base=bday.loc[grn].sum(), green_given=bday.loc[grn].sum() - day.loc[grn].sum(),
                         green_days=int((day > 0).sum()), worst_day=day.min(), worst5=day.nsmallest(5).sum(),
                         best_share=best / tot if tot > 0 else np.nan,
                         avgR_wo_best=(tot - best) / (n - nb) if n - nb > 0 else np.nan))
    return rows


M = []
for s in SETUPS:
    for sp in ("TRAIN", "VALID", "FWD"):
        M += metrics(T, RES, s, sp)
for s in L.setup.unique():
    M += metrics(L, RESL, s, "LIVE")
M = pd.DataFrame(M)
M["red_removed_pct"] = M.red_removed / M.red_base.abs() * 100
M["green_given_pct"] = M.green_given / M.green_base.abs() * 100
M.to_csv(HERE / "configs.csv", index=False, float_format="%.4f")
cols = ["cfg", "trades", "R", "R_per_trade", "win", "day_t", "dR", "pair_t", "red_base", "red_removed_pct", "green_base",
        "green_given_pct", "green_days", "worst_day", "worst5", "best_share", "avgR_wo_best"]
for s in [MAIN]:
    for sp in ("TRAIN", "VALID", "FWD"):
        p(f"\n## {s} E90 - {sp}")
        p(M[(M.setup == s) & (M.split == sp)][cols].to_string(index=False, float_format=lambda v: f"{v:.2f}"))
for s in sorted(L.setup.unique()):
    p(f"\n## {s} - LIVE (<= 11-09)")
    p(M[(M.setup == s) & (M.split == "LIVE")][cols].to_string(index=False, float_format=lambda v: f"{v:.2f}"))

BAR12 = math.sqrt(2 * math.log(12)); BAR = math.sqrt(2 * math.log(24))
p(f"\n## Pass rule (unchanged): VALID and FWD red cut >= 20%, green give-up <= 10%, dR >= 0; TRAIN dR >= 0; sisters VALID none "
  f"worse > 5% of |base R|. Paired VALID t bar N 24: {BAR:.2f} (N 12: {BAR12:.2f}).")
ver = []
for cfg in CFG[1:]:
    g = {sp: M[(M.setup == MAIN) & (M.split == sp) & (M.cfg == cfg)].iloc[0] for sp in ("TRAIN", "VALID", "FWD")}
    c1 = all(g[sp].red_removed_pct >= 20 and g[sp].green_given_pct <= 10 and g[sp].dR >= 0 for sp in ("VALID", "FWD"))
    c2 = g["TRAIN"].dR >= 0
    sv = M[(M.setup.isin(SIS)) & (M.split == "VALID") & (M.cfg == cfg)]
    sb = M[(M.setup.isin(SIS)) & (M.split == "VALID") & (M.cfg == "B0")].set_index("setup").R
    worse = sv[sv.dR < -0.05 * sv.setup.map(sb).abs()]
    sf = M[(M.setup.isin(SIS)) & (M.split == "FWD") & (M.cfg == cfg)]
    lv = {a: M[(M.setup == f"{a}:{MAIN}") & (M.cfg == cfg)].dR.sum() for a in ("Primary", "Testing1")}
    ver.append(dict(cfg=cfg, name=NAME[cfg], **{f"{sp}_dR": g[sp].dR for sp in ("TRAIN", "VALID", "FWD")},
                    **{f"{sp}_red_rm%": g[sp].red_removed_pct for sp in ("TRAIN", "VALID", "FWD")},
                    **{f"{sp}_green_gv%": g[sp].green_given_pct for sp in ("TRAIN", "VALID", "FWD")},
                    VALID_pair_t=g["VALID"].pair_t, FWD_pair_t=g["FWD"].pair_t,
                    sis_valid_better=int((sv.dR > 0).sum()), sis_valid_worse=int((sv.dR < 0).sum()), sis_valid_dR=sv.dR.sum(),
                    sis_valid_worse_gt5=len(worse), sis_fwd_better=int((sf.dR > 0).sum()), sis_fwd_worse=int((sf.dR < 0).sum()),
                    sis_fwd_dR=sf.dR.sum(), live_primary_dR=lv["Primary"], live_testing1_dR=lv["Testing1"],
                    PASS=bool(c1 and c2 and len(worse) == 0), t_over_bar=bool(g["VALID"].pair_t >= BAR)))
V = pd.DataFrame(ver); V.to_csv(HERE / "verdict.csv", index=False, float_format="%.3f")
p(V.to_string(index=False, float_format=lambda v: f"{v:.1f}"))

p("\n## Sisters (E90): dR vs own E90 base per setup (TRAIN / VALID / FWD)")
for cfg in CFG[1:]:
    x = M[(M.setup.isin(SIS)) & (M.cfg == cfg)].pivot(index="setup", columns="split", values="dR")
    p(f"{cfg} {NAME[cfg]}: " + "; ".join(f"{SHORT[s]} T {r.TRAIN:+.1f} V {r.VALID:+.1f} F {r.FWD:+.1f}"
                                          for s, r in x[["TRAIN", "VALID", "FWD"]].iterrows()))
p("\nsister E90 base R: " + "; ".join(
    f"{SHORT[s]} T {M[(M.setup == s) & (M.split == 'TRAIN') & (M.cfg == 'B0')].R.iloc[0]:+.0f} / V "
    f"{M[(M.setup == s) & (M.split == 'VALID') & (M.cfg == 'B0')].R.iloc[0]:+.0f} / F {M[(M.setup == s) & (M.split == 'FWD') & (M.cfg == 'B0')].R.iloc[0]:+.0f}"
    for s in SIS))

# base L3 E90 by SPY day type (diagnostic)
g = T[(T.setup == MAIN)].copy(); g["took"] = RES["B0"][g.index]; g = g[g.took > 0]
dd = g.groupby("date").agg(R=("r", "sum"), split=("split", "first")).reset_index()
dd["oc"] = dd.date.map(lambda d: (SPY[d]["c"][-1] / SPY[d]["o"] - 1) * 100 if d in SPY else np.nan)
dd["type"] = np.where(dd.oc > 0.25, "SPY up", np.where(dd.oc < -0.25, "SPY down", "flat"))
for uni in ("ALL", "E90", "Eday"):
    b_ = bases[uni]; b_ = b_[(b_.setup == MAIN) & (b_.split == "FWD") & (b_.took > 0)].groupby("date").r.agg(["sum", "size"])
    p(f"\n## one-big-day: {uni} FWD base L3-fromopen top 3 days: " + "; ".join(f"{d} {r['sum']:+.1f}R ({int(r['size'])})"
                                                                            for d, r in b_.sort_values("sum").tail(3)[::-1].iterrows()))
p("\n## diag E90 base day R by SPY day type (open->close +-0.25%)")
p(dd.groupby(["split", "type"]).R.agg(["size", "sum", "mean", lambda v: (v < 0).mean()]).to_string(float_format=lambda v: f"{v:.2f}"))
(HERE / "study_out.txt").write_text("\n".join(out) + "\n\nEducational only - not financial advice.\n")
