"""night1102/simple step 1: enabled setups per account, condition counts, live paper record 10-06..11-02.
Educational only - not financial advice. Live = paper fills (rule 7). avg R = pnl_adj / $ risk (|entry-stop| x shares)."""
import json, os, re, sqlite3, sys, ast
from pathlib import Path
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[4]
J = Path(sys.argv[1])  # dir with <branch>.db
OUT = Path(__file__).parent
ACC = {"primary": ("mcf-data", None), "testing": ("mcf-data-testing", "account_testing.yaml"),
       "testing2": ("mcf-data-testing2", "account_testing2.yaml"), "graveyard": ("mcf-data-graveyard", "account_graveyard.yaml"),
       "gen": ("mcf-data-gen", "account_gen.yaml")}
os.chdir(ROOT); sys.path.insert(0, str(ROOT))
from mcf.config import load_config


def count_conditions(spec):
    """Conditions = entry rules in the module (LAYERS minus window lines; TRIGGER+FILTERS when present) + YAML
    prefilter / context terms. Window/time-of-day lines are counted separately (n_time)."""
    mod = spec.get("module")
    info = {"module": mod, "n_layers": None, "n_time": 0, "kind": spec.get("type")}
    if not mod or not (ROOT / mod).exists():
        return info
    src = (ROOT / mod).read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return info
    vals = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                vals[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    lay = vals.get("LAYERS") or []
    timeish = [l for l in lay if re.search(r"(full day|bar close \d|window|\d\d:\d\d-\d\d:\d\d|ET\b)", str(l), re.I)
               and not re.search(r"(RSI|VWAP|gap|below|above|down|up )", str(l).split("ET")[0][:12])]
    if "TRIGGER" in vals:
        n = 1 + len(vals.get("FILTERS") or [])
    elif "CONDS" in vals:
        n = len(vals["CONDS"])
    else:
        n = len(lay) - len(timeish) if lay else None
        if lay and len(lay) == 1 and re.match(r"^[A-Z]\d", str(lay[0])):
            n = None  # packed config id (CWT): counted by hand in the report
    extra = 0
    if spec.get("prefilter"):
        extra += len(str(spec["prefilter"]).split(","))
    if spec.get("context"):
        extra += len(spec["context"]) if isinstance(spec["context"], (list, dict)) else 1
    info.update(n_layers=None if n is None else n + extra, n_time=len(timeish), layers=" | ".join(map(str, lay))[:300])
    return info


rows = []
for acct, (br, f) in ACC.items():
    os.environ["MCF_ACCOUNT"] = acct
    cfg = load_config()
    for name, spec in (cfg.get("strategies") or {}).items():
        spec = spec or {}
        if not spec.get("enabled", True):
            continue
        rows.append({"account": acct, "setup": name, **count_conditions(spec), "window": str(spec.get("window")),
                     "refire": bool(spec.get("refire")), "min_adv": spec.get("min_adv")})
en = pd.DataFrame(rows)

tr = []
for acct, (br, f) in ACC.items():
    c = sqlite3.connect(J / f"{br}.db")
    t = pd.read_sql("select symbol,strategy,side,date,entry,stop,shares,pnl_adj,r_multiple,exit_reason from trades "
                    "where run_id=1 and date>='2026-10-06' and date<='2026-11-02'", c)
    t["account"] = acct
    tr.append(t)
tr = pd.concat(tr)
tr["risk"] = (tr.entry - tr.stop).abs() * tr.shares
tr = tr[(tr.risk > 0) & tr.pnl_adj.notna()]
tr["R"] = tr.pnl_adj / tr.risk
tr.to_csv(OUT / "live_trades_1006_1102.csv.gz", index=False)

lb = json.load(open(ROOT / "docs/live/leaderboard.json"))
exp = {}
for a, L in lb["accounts"].items():
    for r in L:
        exp.setdefault(r["setup"], r.get("expected_r"))


def stats(g):
    R = g.R.to_numpy()
    d = g.groupby("date").R.sum()
    best = d.idxmax() if len(d) else None
    wob = g[g.date != best].R.mean() if len(d) > 1 else np.nan
    dm = g.groupby("date").R.mean()
    t = dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm))) if len(dm) > 2 and dm.std() > 0 else np.nan
    return pd.Series({"n": len(R), "sessions": g.date.nunique(), "avg_r": R.mean(), "win": (R > 0).mean(),
                      "total_r": R.sum(), "avg_r_wo_best": wob, "best_share": d.max() / R.sum() if R.sum() > 0 else np.nan,
                      "t_day": t, "first": g.date.min(), "last": g.date.max()})


ls = tr.groupby(["account", "strategy"]).apply(stats).reset_index().rename(columns={"strategy": "setup"})
m = en.merge(ls, on=["account", "setup"], how="left")
m["expected_r"] = m.setup.map(exp)
m["gap_live_minus_bt"] = m.avg_r - m.expected_r
m.to_csv(OUT / "census.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 40)
print("enabled setups:", len(m), m.account.value_counts().to_dict())
print(m.sort_values("n", ascending=False)[["account", "setup", "n_layers", "n_time", "n", "sessions", "avg_r", "win",
                                           "avg_r_wo_best", "expected_r", "first"]].head(40).to_string())
