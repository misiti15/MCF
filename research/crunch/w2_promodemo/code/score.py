"""W2-promodemo: score every assigned setup against C3-BAR2 / -10R demotion / C3-EXIT100 / GY-LIFE graduation.
Live journals run_id 1; R after costs = pnl_adj/(|entry-stop| x shares); identical signals deduped.
Usage: python score.py <journal_dir> <worktree> <out_dir>.  Educational only - not financial advice."""
import sys, re, json, sqlite3, math, yaml, numpy as np, pandas as pd
J, WT, OUT = sys.argv[1:4]
ACC = {"mcf-data": "primary", "mcf-data-testing": "testing", "mcf-data-testing2": "testing2",
       "mcf-data-explore1": "explore1", "mcf-data-livelab": "livelab", "mcf-data-testingd": "testingd",
       "mcf-data-testinge": "testinge", "mcf-data-testingf": "testingf", "mcf-data-gen": "gen",
       "mcf-data-graveyard": "graveyard"}
asg = json.load(open(f"{WT}/docs/live/assignments.json")); LBL = asg["labels"]
names = yaml.safe_load(open(f"{WT}/config/setup_names.yaml"))
def dname(s):
    base = re.sub(r"-WB\d+$", "", s); v = names.get(s) or names.get(base) or {}
    n = v.get("name", "") if isinstance(v, dict) else ""
    return (n + (" (WB copy)" if s != base and n else "")) or s
T, S = [], []
for b, a in ACC.items():
    c = sqlite3.connect(f"{J}/{b}.db")
    t = pd.read_sql("select symbol,strategy,side,date,entry_time,entry,stop,shares,pnl_adj,r_multiple from trades "
                    "where run_id=1 and exit_time is not null", c); t["acct"] = a; T.append(t)
    s = pd.read_sql("select distinct day as date, strategy from signals where run_id=1", c); s["acct"] = a; S.append(s)
t = pd.concat(T, ignore_index=True); sig = pd.concat(S, ignore_index=True)
el = pd.read_csv(f"{J}/elig.csv"); el["acct"] = el.branch.map(ACC)  # per-session enabled setups from setups/<date>.json snapshots
t = t[~t.date.between("2024-11-01", "2025-02-28")]
risk = (t.entry - t.stop).abs() * t.shares.abs()
t["R"] = np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple); t = t[t.R.notna()].copy()
et = pd.to_datetime(t.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + et.dt.strftime("%H%M")
t["sds"] = t.symbol + "|" + t.date + "|" + t.side.astype(str)
prim = t[t.acct == "primary"]; PM = asg["accounts"]["primary"]
pdaily = prim.groupby("date").R.sum()
# guests -> home account
raw = open(f"{WT}/config/account_graveyard.yaml").read()
guest_home = {m.group(1): m.group(2) for m in re.finditer(r"- (\S+)\s+# GY-BENCH guest \(\w\) from ([A-Za-z ]+?),", raw)}
inv = {v: k for k, v in LBL.items()}; inv["Setup Generator"] = "gen"
gyc = yaml.safe_load(raw)["strategies"]
residents = [k for k, v in gyc.items() if k not in guest_home]  # 34 residents incl. GY-BENCH-benched and disabled (in arena)
units = [(s, a, "") for a, L in asg["accounts"].items() if a != "graveyard" for s in L]
units += [(s, "graveyard", "benched 11-18..11-24" if (gyc[s] or {}).get("benched") else
           ("off (in arena)" if (gyc[s] or {}).get("enabled") is False else "")) for s in residents]
units += [(s, inv.get(h, h), "GY-BENCH guest") for s, h in guest_home.items()]

def stats(g, sg_dates=None, pref=""):
    o = {}
    if g.empty: return {pref + "n": 0}
    d = g.groupby("date").R.sum().sort_index(); tot = d.sum(); bd = d.idxmax(); n = len(g)
    avg = g.R.mean(); sd = g.R.std(ddof=1) if n > 1 else np.nan
    o.update({pref + "n": n, pref + "sessions": d.size, pref + "totR": tot, pref + "avgR": avg,
              pref + "t": avg / sd * math.sqrt(n) if sd and sd > 0 else np.nan,
              pref + "wo_best": g[g.date != bd].R.mean() if d.size > 1 else np.nan,
              pref + "best_day": bd, pref + "best_share": d.max() / tot if tot > 0 else np.nan,
              pref + "green_pct": (d > 0).mean(), pref + "last5R": d.iloc[-5:].sum(),
              pref + "shrunk": n / (n + 150) * avg + 150 / (n + 150) * (-0.10)})
    if d.size >= 4:
        h = d.index[: d.size // 2]
        o[pref + "fit_avg"] = g[g.date.isin(h)].R.mean(); o[pref + "check_avg"] = g[~g.date.isin(h)].R.mean()
    if sg_dates is not None: o[pref + "signal_days"] = len(sg_dates)
    return o

rows = []
for s, a, tag in units:
    r = dict(setup=s, name=dname(s), account=LBL.get(a, a), acct=a, tag=tag,
             since=(asg["setups"].get(s, {}) or {}).get("first_session"))
    if a == "primary":
        g = prim[prim.strategy == s]
        m = asg["setups"].get(s) or {}
        # Primary admission = recorded move-in session, unless the move came from Primary itself (then first Primary trade)
        adm = m["first_session"] if m.get("first_session") and "primary" not in (m.get("from") or []) else g.date.min()
        r["prim_since"] = adm; r["prim_all_n"] = len(g); r["prim_all_totR"] = g.R.sum(); g = g[g.date >= adm]
        sd = set(sig[(sig.acct == "primary") & (sig.strategy == s)].date)
        r.update(stats(g, sd))
        r["active_days"] = el[(el.acct == "primary") & (el.setup == s) & (el.date >= r["prim_since"])].date.nunique()
        other = prim[prim.strategy.isin([x for x in PM if x != s])]
        no = g[~g.sds.isin(set(other.sds))]; r.update(stats(no, None, "no_"))
        r["corr_primary"] = np.nan  # member of Primary
        r["corr_rest_primary"] = (lambda d: np.corrcoef(d.values, other.groupby("date").R.sum().reindex(d.index).fillna(0).values)[0, 1]
                                  if d.size >= 8 else np.nan)(g.groupby("date").R.sum())
        r["overlap_pct"] = g.sds.isin(set(other.sds)).mean()
        # whole record outside Primary (testing history)
        wo = t[(t.strategy == s) & (t.acct != "primary")].drop_duplicates("k"); r.update(stats(wo, None, "arena_"))
    else:
        base = t[(t.strategy == s) & (t.acct != "primary")]
        if a != "graveyard": pass
        g = base.drop_duplicates("k")
        sd = set(sig[(sig.acct != "primary") & (sig.strategy == s)].date)
        r.update(stats(t[t.strategy == s].sort_values("acct").drop_duplicates("k"), None, "all_"))  # incl. any Primary stint
        r.update(stats(g, sd))
        r["active_days"] = el[(el.acct != "primary") & (el.setup == s)].date.nunique()
        no = g[~g.sds.isin(set(prim[prim.strategy.isin(PM)].sds))]; r.update(stats(no, None, "no_"))
        r["overlap_pct"] = 1 - len(no) / len(g) if len(g) else np.nan
        pm_any = set(t[t.strategy.isin(PM)].sds)
        r.update(stats(g[~g.sds.isin(pm_any)], None, "nx_"))
        d = g.groupby("date").R.sum(); cm = d.index.intersection(pdaily.index)
        r["corr_primary"] = np.corrcoef(d[cm].values, pdaily[cm].values)[0, 1] if len(cm) >= 8 else np.nan
        cur = t[(t.strategy == s) & (t.acct == a)]
        if r["since"] and not tag: cur = cur[cur.date >= r["since"]]
        r.update(stats(cur, None, "cur_"))
        gy = t[(t.strategy == s) & (t.acct == "graveyard")]; r.update(stats(gy, None, "gy_"))
    rows.append(r)
R = pd.DataFrame(rows)

def bar2(x):
    f = []
    if not x.get("n", 0) >= 30: f.append("n<30")
    if not x.get("sessions", 0) >= 8: f.append("sess<8")
    if not x.get("active_days", 0) >= 15: f.append("active<15")
    if not (x.get("no_wo_best", np.nan) > 0): f.append("nonov w/o best<=0")
    if not x.get("green_pct", 0) >= 0.5: f.append("green<50%")
    if not (x.get("best_share", np.nan) < 0.5): f.append("best>=50%")
    if not (x.get("shrunk", -1) > 0): f.append("shrunk<=0")
    return f
def bar2x(x):
    f = []
    if not x.get("nx_n", 0) >= 30: f.append("n<30")
    if not x.get("nx_sessions", 0) >= 8: f.append("sess<8")
    if not x.get("active_days", 0) >= 15: f.append("active<15")
    if not (x.get("nx_wo_best", np.nan) > 0): f.append("w/o best<=0")
    if not x.get("nx_green_pct", 0) >= 0.5: f.append("green<50%")
    if not (x.get("nx_best_share", np.nan) < 0.5): f.append("best>=50%")
    if not (x.get("nx_shrunk", -1) > 0): f.append("shrunk<=0")
    return f
R["bar2x_fails"] = R.apply(lambda x: ";".join(bar2x(x)) if x.acct != "primary" else "", axis=1)
R["bar2_fails"] = R.apply(lambda x: ";".join(bar2(x)), axis=1)
R["bar2"] = R.bar2_fails.map(lambda f: "READY" if not f else ("NEAR" if set(f.split(";")) <= {"shrunk<=0", "active<15"} else "no"))
R["exit100"] = (R.n >= 100) & (R.active_days >= 15) & (R.avgR <= -0.05) & (R.wo_best <= 0) & (R.acct.isin(
    ["testing", "testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen"]))
R["demote10"] = (R.acct == "primary") & (R.totR <= -10)
R["gy_grad"] = (R.acct == "graveyard") & (R.gy_sessions >= 15) & (R.gy_n >= 30) & (R.all_wo_best > 0) & (R.all_best_share < 0.5)

R = R[~((R.acct == "gen") & (R.n.fillna(0) < 10))]
N = len(R); tbar = max(1.5, math.sqrt(2 * math.log(N))); R["t_bar"] = tbar
R.to_csv(f"{OUT}/SCORES.csv", index=False, float_format="%.4f")
print("N scored", len(R), "t bar", round(tbar, 2), "max date", t.date.max())
print(R.groupby("account").size().to_dict())
