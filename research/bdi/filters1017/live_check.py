"""Live/paper journal check of K25 and SIR15. Educational only - not financial advice."""
import sys, sqlite3, glob, re, numpy as np, pandas as pd, yaml
S = sys.argv[1]; ROOT = "/home/user/MCF"
GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5), "t05s05": (0.5, 0.5)}
geom = {}
for f in glob.glob(f"{ROOT}/research/**/*.py", recursive=True):
    try: txt = open(f).read()
    except Exception: continue
    m = re.search(r'^GEOM = "(\w+)"', txt, re.M)
    if m and m.group(1) in GEOMK: geom[f.split("/")[-1][:-3]] = m.group(1)
for cf in glob.glob(f"{ROOT}/config/*.yaml"):
    try: st = (yaml.safe_load(open(cf)) or {}).get("strategies") or {}
    except Exception: continue
    for k, v in st.items():
        if isinstance(v, dict) and v.get("module"):
            mod = v["module"].split("/")[-1][:-3]
            if mod in geom: geom[k] = geom[mod]
bars = pd.concat([pd.read_parquet(f) for f in glob.glob(f"{S}/bars/*.parquet")])
bars.index = pd.to_datetime(bars.index)
if bars.index.tz is None: bars.index = bars.index.tz_localize("UTC")
bars.index = bars.index.tz_convert("America/New_York")
bars = bars.reset_index().rename(columns={bars.index.name or "index": "t"})
bars["d"] = bars["t"].dt.strftime("%Y-%m-%d")
bg = {k: g.set_index("t") for k, g in bars.groupby(["symbol", "d"])}
prim = [k for k, v in yaml.safe_load(open(f"{ROOT}/config/default.yaml"))["strategies"].items() if isinstance(v, dict) and v.get("enabled")]
rows = []
for acct, f in (("Primary", "p.db"), ("Testing1", "t1.db"), ("Testing2", "t2.db")):
    c = sqlite3.connect(f"{S}/{f}")
    t = pd.read_sql("select * from trades where run_id=1", c)
    s = pd.read_sql("select broker_order_id, ref_price, stop stop_sig, target target_sig, ts from signals where run_id=1", c)
    m = t.merge(s, on="broker_order_id", how="inner")
    m["acct"] = acct
    rows.append(m)
X = pd.concat(rows, ignore_index=True)
X["base"] = X["strategy"].str.replace(r"-FD$", "", regex=True)
g = X["strategy"].map(geom).fillna(X["base"].map(geom))
X["geom_known"] = g.notna()
X["DN"] = g.map(lambda x: GEOMK[x][1] if isinstance(x, str) else 1.0)
X["Rlab"] = (X["stop_sig"] - X["ref_price"]).abs() / X["DN"]
X["P"] = X["side"] * (X["entry"] - X["ref_price"]) / X["Rlab"]
X["K25"] = X["P"] >= 0.25
ts = pd.to_datetime(X["ts"], utc=True, format="ISO8601").dt.tz_convert("America/New_York")
X["bar_end"] = ts.dt.floor("5min")
hh = []
for i, r in X.iterrows():
    b = bg.get((r.symbol, r.date))
    if b is None: hh.append(np.nan); continue
    w = b[(b.index >= r.bar_end - pd.Timedelta(minutes=15)) & (b.index < r.bar_end)]
    hh.append(w["high"].max() if len(w) else np.nan)
X["hh15"] = hh
X["SIR"] = (X["side"] < 0) & (X["stop_sig"] < X["hh15"])
X["primary_now"] = X["strategy"].isin(prim)
X.to_parquet(f"{S}/live.parquet")
print("missing hh15 (shorts):", int(((X.side < 0) & X.hh15.isna()).sum()), "of", int((X.side < 0).sum()))
print("unknown geom:", X.loc[~X.geom_known, "strategy"].unique()[:50])

def summ(D, flag, label):
    a, b = D[D[flag]], D[~D[flag]]
    def st(x):
        if len(x) == 0: return "n 0"
        dd = x.groupby("date")["r_multiple"].sum(); n = len(x)
        se = np.sqrt(((dd - x.groupby("date").size() * x.r_multiple.mean()) ** 2).sum()) / n if len(dd) > 1 else np.nan
        return f"n {n}, avg R {x.r_multiple.mean():+.3f} (se {se:.3f}), sum R {x.r_multiple.sum():+.2f}, win {np.mean(x.r_multiple>0):.0%}, P/L adj ${x.pnl_adj.sum():+.2f}"
    print(f"  {label} {flag}: triggered {len(a)}/{len(D)} ({len(a)/max(1,len(D)):.1%}) | skipped -> {st(a)} | kept -> {st(b)}")

for acct in ("Primary", "Testing1", "Testing2"):
    D = X[X.acct == acct]
    print("==", acct, D.date.min(), D.date.max(), len(D))
    for lab, sub in (("since 10-14", D[D.date >= "2026-10-14"]), ("all", D)):
        summ(sub, "K25", lab)
        summ(sub[sub.side < 0], "SIR", lab + " shorts")
    if acct == "Primary":
        cur = D[D.primary_now & (D.date >= "2026-10-14")]
        print(" current Primary setups since 10-14:", len(cur))
        summ(cur, "K25", "cur"); summ(cur[cur.side < 0], "SIR", "cur shorts")
A = X
print("== ALL accounts pooled")
summ(A, "K25", "all"); summ(A[A.side < 0], "SIR", "all shorts")
print("P distribution (all):", A.P.describe().round(3).to_dict())
pd.set_option("display.width", 250)
cols = ["acct", "date", "symbol", "strategy", "side", "ref_price", "entry", "stop_sig", "P", "hh15", "exit_reason", "r_multiple", "pnl_adj"]
print(X[(X.acct == "Primary") & (X.date >= "2026-10-14") & (X.K25 | X.SIR)][cols + ["K25", "SIR"]].round(3).to_string())
