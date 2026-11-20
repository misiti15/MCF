"""Wave 2 packet: Friday review packet (W2 rerun on LR8 basis, trade R + account R, BAR2 / one-big-day / PBO / try-count)
+ Epoch 1 vs BASE1 + UNIT1 red-day decomposition of Primary.  Usage: python packet.py <worktree> <work_dir> <out_dir>
Educational only - not financial advice."""
import sys, re, json, sqlite3, math, itertools, yaml, numpy as np, pandas as pd
WT, WK, OUT = sys.argv[1:4]
sys.path.insert(0, WT)
from mcf.costs import cost_r_lr8, _report_cfg
from mcf.report.footrace import day_t, ADMITTED_1120
ACC = {"mcf-data": "primary", "mcf-data-testing": "testing", "mcf-data-testing2": "testing2",
       "mcf-data-explore1": "explore1", "mcf-data-livelab": "livelab", "mcf-data-testingd": "testingd",
       "mcf-data-testinge": "testinge", "mcf-data-testingf": "testingf", "mcf-data-gen": "gen",
       "mcf-data-graveyard": "graveyard"}
EQ = {"primary": 84883.40, "testing": 94680.51, "testing2": 92146.22, "explore1": 100266.73, "livelab": 100190.09,
      "testingd": 100188.97, "testinge": 99024.04, "testingf": 99974.85, "gen": 89646.45, "graveyard": 91417.92}
ARENA = ["testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen"]
asg = json.load(open(f"{WT}/docs/live/assignments.json")); LBL = asg["labels"]
cfg = _report_cfg()
T, S, SH = [], [], []
for b, a in ACC.items():
    c = sqlite3.connect(f"{WK}/j/{b}.db")
    t = pd.read_sql("select id,symbol,strategy,side,date,entry_time,entry,stop,target,exit,exit_reason,shares,pnl,pnl_adj,"
                    "r_multiple from trades where run_id=1 and exit_time is not null and date>='2026-10-06'", c)
    t["acct"] = a; T.append(t)
    s = pd.read_sql("select day as date, strategy, count(*) n from signals where run_id=1 group by 1,2", c); s["acct"] = a; S.append(s)
    if a == "primary":
        SH.append(pd.read_sql("select id,symbol,strategy,side,date,entry_time,entry,stop,target,exit,exit_reason,shares,pnl,"
                              "pnl_adj,r_multiple from trades where run_id=3 and exit_time is not null", c))
t = pd.concat(T, ignore_index=True); sig = pd.concat(S, ignore_index=True)
t = t[~t.date.between("2024-11-01", "2025-02-28")].reset_index(drop=True)
t["R"] = cost_r_lr8(t, cfg).astype(float).values
t = t[t.R.notna()].copy()
t["risk"] = (t.entry - t.stop).abs() * t.shares.abs()
t["usd"] = np.where(t.risk > 0, t.R * t.risk, t.pnl_adj)       # LR8 dollars
t["Rbook"] = np.where(t.pnl_adj.notna() & (t.risk > 0), t.pnl_adj / t.risk, t.r_multiple)
et = pd.to_datetime(t.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + et.dt.strftime("%H%M")
t["sds"] = t.symbol + "|" + t.date + "|" + t.side.astype(str)
t["acctR"] = t.usd / (t.acct.map(EQ) * 0.0025)
# Primary equity per day (prior close)
eh = json.load(open(f"{WT}/docs/live/equity_history.json"))["accounts"]["primary"]
pdays = sorted(t[t.acct == "primary"].date.unique())
book = t[t.acct == "primary"].groupby("date").pnl.sum()
eqp = {}
for d in pdays:
    prev = [x for x in sorted(eh) if x < d]
    if d <= "2026-11-05" and prev: eqp[d] = eh[prev[-1]]["equity_close"]
    else: eqp[d] = 84883.40 - book[(book.index >= d) & (book.index < "2026-11-19")].sum()
prim = t[t.acct == "primary"].copy(); prim["acctR"] = prim.usd / prim.date.map(eqp).mul(0.0025)
t.loc[prim.index, "acctR"] = prim.acctR
PM = asg["accounts"]["primary"]
el = pd.read_csv(f"{WK}/elig.csv"); el["acct"] = el.branch.map(ACC)
sd = sig[["acct", "strategy", "date"]].rename(columns={"strategy": "setup"})
act = pd.concat([el[["acct", "setup", "date"]], sd]).drop_duplicates()   # enabled snapshot day OR signal day
sigcount = sig.groupby("strategy").n.sum()
reps = json.load(open(f"{WT}/docs/live/arena_reps.json"))["setups"]
names = yaml.safe_load(open(f"{WT}/config/setup_names.yaml"))
def dname(s):
    base = re.sub(r"-WB\d+$", "", s); v = names.get(s) or names.get(base) or {}
    n = v.get("name", "") if isinstance(v, dict) else ""
    return (n + (" (WB)" if s != base and n else "")) or s

def stats(g, pref=""):
    if g.empty: return {pref + "n": 0}
    d = g.groupby("date").R.sum().sort_index(); dm = g.groupby("date").R.mean(); tot = d.sum(); bd = d.idxmax(); n = len(g)
    avg = g.R.mean()
    o = {pref + "n": n, pref + "sessions": d.size, pref + "totR": tot, pref + "avgR": avg,
         pref + "wo_best": g[g.date != bd].R.mean() if d.size > 1 else np.nan, pref + "best_day": bd,
         pref + "best_share": d.max() / tot if tot > 0 else np.nan, pref + "green_pct": (d > 0).mean(),
         pref + "last5R": d.iloc[-5:].sum(), pref + "t_day": day_t(dm),
         pref + "shrunk": n / (n + 150) * avg + 150 / (n + 150) * (-0.10),
         pref + "usd": g.usd.sum(), pref + "acctR": g.acctR.sum(), pref + "totRbook": g.Rbook.sum(),
         pref + "d1119": d.get("2026-11-19", np.nan)}
    if d.size >= 4:
        h = d.index[: d.size // 2]
        o[pref + "fit_avg"] = g[g.date.isin(h)].R.mean(); o[pref + "check_avg"] = g[~g.date.isin(h)].R.mean()
    return o

raw = open(f"{WT}/config/account_graveyard.yaml").read()
guest_home = {m.group(1): m.group(2) for m in re.finditer(r"- (\S+)\s+# GY-BENCH guest \(\w\) from ([A-Za-z ]+?),", raw)}
inv = {v: k for k, v in LBL.items()}
units = [(s, a) for a, L in asg["accounts"].items() for s in L]
rows = []
pm_sds_prim = set(prim[prim.strategy.isin(PM)].sds); pm_any = set(t[t.strategy.isin(PM)].sds)
pdaily = prim.groupby("date").acctR.sum()
for s, a in units:
    m = asg["setups"].get(s) or {}
    r = dict(setup=s, name=dname(s), account=LBL.get(a, a), acct=a, since=m.get("first_session"),
             tag="GY-BENCH guest" if s in guest_home else "")
    if a == "primary":
        g = prim[prim.strategy == s]
        adm = m["first_session"] if m.get("first_session") and "primary" not in (m.get("from") or []) else g.date.min()
        r["prim_since"] = adm; g = g[g.date >= adm]
        r.update(stats(g))
        r["active_days"] = act[(act.acct == "primary") & (act.setup == s) & (act.date >= adm)].date.nunique()
        other = prim[prim.strategy.isin([x for x in PM if x != s])]
        r.update(stats(g[~g.sds.isin(set(other.sds))], "no_"))
        r["overlap_pct"] = g.sds.isin(set(other.sds)).mean() if len(g) else np.nan
        r.update(stats(t[(t.strategy == s) & (t.acct != "primary")].drop_duplicates("k"), "arena_"))
    else:
        g = t[(t.strategy == s) & (t.acct != "primary")].drop_duplicates("k")
        r.update(stats(t[t.strategy == s].sort_values("acct").drop_duplicates("k"), "all_"))
        r.update(stats(g))
        r["active_days"] = act[(act.acct != "primary") & (act.setup == s)].date.nunique()
        r.update(stats(g[~g.sds.isin(pm_sds_prim)], "no_"))
        r.update(stats(g[~g.sds.isin(pm_any)], "nx_"))
        r["overlap_pct"] = 1 - (~g.sds.isin(pm_sds_prim)).sum() / len(g) if len(g) else np.nan
        cur = t[(t.strategy == s) & (t.acct == a)]
        r.update(stats(cur, "cur_"))
        r.update(stats(t[(t.strategy == s) & (t.acct == "graveyard")], "gy_"))
        dd = g.groupby("date").R.sum(); cm = dd.index.intersection(pdaily.index)
        r["corr_primary_acctR"] = np.corrcoef(dd[cm].values, pdaily[cm].values)[0, 1] if len(cm) >= 8 else np.nan
    r["signals"] = sigcount.get(s, 0); r["reps_active"] = (reps.get(s) or {}).get("active_days")
    rows.append(r)
R = pd.DataFrame(rows)
N = int((R.n.fillna(0) > 0).sum()); tbar = max(1.5, math.sqrt(2 * math.log(N))); R["t_bar"] = tbar

def bar2(x, p=""):
    f = []
    if not x.get(p + "n", 0) >= 30: f.append("n<30")
    if not x.get(p + "sessions", 0) >= 8: f.append("sess<8")
    if not x.get("active_days", 0) >= 15: f.append("active<15")
    key = "no_wo_best" if p == "" else p + "wo_best"
    if not (x.get(key, np.nan) > 0): f.append("nonov w/o best<=0")
    if not x.get(p + "green_pct", 0) >= 0.5: f.append("green<50%")
    if not (x.get(p + "best_share", np.nan) < 0.5): f.append("best>=50%")
    if not (x.get(p + "shrunk", -1) > 0): f.append("shrunk<=0")
    return ";".join(f)
cand = R.acct.isin(ARENA + ["testing"])
R["bar2_fails"] = np.where(cand, R.apply(bar2, axis=1), "")
R["bar2x_fails"] = np.where(cand, R.apply(lambda x: bar2(x, "nx_"), axis=1), "")
R["bar2"] = np.where(~cand, "", np.where(R.bar2_fails == "", "READY", np.where(R.bar2_fails.map(
    lambda f: set(f.split(";")) <= {"shrunk<=0", "active<15"}), "NEAR", "no")))
R["demote10"] = (R.acct == "primary") & (R.totR <= -10)
def fexit(x):
    if x.acct not in ARENA or x.get("n", 0) == 0: return ""
    s = x.setup; days = x.active_days or 0
    if s in ADMITTED_1120: return "exempt (11-20 admission)"
    if "-WB" in s and days < 15: return "exempt (young WB)"
    if days < 15 or x.n < 30: return ""
    if days and x.signals / days < 0.5: return "exempt (rare)"
    return "EXIT" if (x.avgR <= 0 and x.wo_best <= 0 and x.t_day <= -1.5) else ""
R["footrace_exit"] = R.apply(fexit, axis=1)
R["gy_grad"] = (R.acct == "graveyard") & (R.gy_sessions >= 15) & (R.gy_n >= 30) & (R.all_wo_best > 0) & (R.all_best_share < 0.5)
R.to_csv(f"{OUT}/scores.csv", index=False, float_format="%.4f")

# ---------------- PBO (CSCV S=8) for rankings: shrunk (BAR2), total R, raw avg R
pool = t[t.acct != "primary"].drop_duplicates("k")
cnt = pool.groupby("strategy").size(); keep = cnt[cnt >= 20].index
DS = sorted(pool.date.unique()); NS = len(DS)
M = pool[pool.strategy.isin(keep)].pivot_table(index="date", columns="strategy", values="R", aggfunc="sum").reindex(DS).fillna(0)
C = pool[pool.strategy.isin(keep)].pivot_table(index="date", columns="strategy", values="R", aggfunc="count").reindex(DS).fillna(0)
blocks = np.array_split(np.arange(NS), 8); pbo = {}
for metric in ("shrunk", "total", "avg"):
    lam = []; ob = []; om = []
    for comb in itertools.combinations(range(8), 4):
        ii = np.concatenate([blocks[k] for k in comb]); oo = np.setdiff1d(np.arange(NS), ii)
        si, so, ni, no = M.iloc[ii].sum(), M.iloc[oo].sum(), C.iloc[ii].sum(), C.iloc[oo].sum()
        if metric == "total": isv, oov = si, so
        elif metric == "avg":
            isv = (si / ni).where(ni >= 10); oov = (so / no).where(no >= 10)
        else:
            isv = (si + 150 * -0.10) / (ni + 150); oov = (so + 150 * -0.10) / (no + 150)
        ok = isv.notna() & oov.notna(); isv, oov = isv[ok], oov[ok]
        b = isv.idxmax(); w = oov.rank(pct=True)[b]; w = min(max(w, 1e-3), 1 - 1e-3)
        lam.append(np.log(w / (1 - w))); ob.append(so[b]); om.append(so.median())
    lam = np.array(lam)
    pbo[metric] = dict(setups=int(M.shape[1]), pbo=float(np.mean(lam <= 0)), med_oos_pct=float(np.median(1 / (1 + np.exp(-lam)))),
                       oos_totR_best=float(np.mean(ob)), oos_totR_median=float(np.mean(om)))
json.dump(pbo, open(f"{OUT}/pbo.json", "w"), indent=1)

# ---------------- Epoch 1 vs BASE1 (Primary run 3 shadow vs run 1 live)
sh = pd.concat(SH, ignore_index=True); sh = sh[sh.date >= "2026-11-17"].reset_index(drop=True)
sh["R"] = cost_r_lr8(sh, cfg).astype(float).values
sh["risk"] = (sh.entry - sh.stop).abs() * sh.shares.abs(); sh["usd"] = np.where(sh.risk > 0, sh.R * sh.risk, sh.pnl_adj)
sh["book"] = np.where(sh.strategy.str.startswith("BASE1:"), "BASE1", "of_live")
sh["setup"] = sh.strategy.str.replace("BASE1:", "", regex=False)
ep = sh.groupby(["date", "book", "setup"]).agg(n=("R", "size"), R=("R", "sum"), usd=("usd", "sum")).reset_index()
lv = prim[prim.date >= "2026-11-17"].groupby(["date", "strategy"]).agg(n=("R", "size"), R=("R", "sum"), usd=("usd", "sum")).reset_index()
lv["book"] = "live"; lv = lv.rename(columns={"strategy": "setup"})
ep = pd.concat([ep, lv]); ep["acctR"] = ep.usd / ep.date.map(lambda d: eqp.get(d, 84883.40) * 0.0025)
ep.to_csv(f"{OUT}/epoch1_base1.csv", index=False, float_format="%.3f")

# ---------------- UNIT1 red-day decomposition (Primary, run 1)
prim["bucket"] = pd.cut(prim.risk, [-1, 25, 75, 150, 1e9], labels=["<$25", "$25-75", "$75-150", ">=$150"])
D = prim.groupby("date").agg(n=("R", "size"), tradeR=("R", "sum"), acctR=("acctR", "sum"), usd=("usd", "sum"),
                             risk_med=("risk", "median")).reset_index()
D["eq"] = D.date.map(eqp); D["era"] = np.where(D.date < "2026-10-28", "pre-10-28", "post-10-28")
dec = []
for d, g in prim.groupby("date"):
    a = g.groupby("strategy").acctR.sum().sort_values(key=lambda x: -x.abs()); tr = g.groupby("strategy").R.sum()
    sign = np.sign(a.sum()); cum = 0; who = []
    # deciders: setups with the day's sign, largest first, until their sum alone exceeds the day's |acctR| net of the opposite side
    same = a[np.sign(a) == sign].sort_values(key=lambda x: -x.abs()); opp = a[np.sign(a) != sign].sum()
    for s2, v in same.items():
        cum += v; who.append(s2)
        if abs(cum + opp) > 0 and np.sign(cum + opp) == sign: break
    bk = g.groupby("bucket", observed=False).agg(R=("R", "sum"), aR=("acctR", "sum"), n=("R", "size"))
    dec.append(dict(date=d, deciders=";".join(who), n_setups=a.size,
                    **{f"aR_{s2}": v for s2, v in a.items()}, **{f"tR_{s2}": v for s2, v in tr.items()},
                    **{f"bR_{b}": bk.loc[b, "R"] for b in bk.index}, **{f"baR_{b}": bk.loc[b, "aR"] for b in bk.index},
                    **{f"bn_{b}": bk.loc[b, "n"] for b in bk.index}))
D = D.merge(pd.DataFrame(dec), on="date")
D.to_csv(f"{OUT}/primary_days.csv", index=False, float_format="%.3f")
print("N", N, "tbar", round(tbar, 2), "maxdate", t.date.max(), "rows", len(R)); print(json.dumps(pbo))
