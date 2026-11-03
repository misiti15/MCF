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


HAND = {  # loop kernels / packed config ids / classic strategies, counted from their code (see NOTES.md)
    "B1-": 3, "B2-": 4, "B3-": 2, "B4-parta": 3, "B4-partb": 3, "B5-": 3, "A7 ": 3, "LIQ-": 3, "pdl1030-regime": 4}
CLASSIC = {"intraday_momentum": 2, "orb20_a": 2, "heat_fade_short": 1, "heat_fade_long": 1, "heat_fade_short-FD": 1,
           "heat_fade_long-FD": 1}
TIME = re.compile(r"^\s*(full day|window|bar close|\d{1,2}:\d\d|tod )", re.I)
UNIV = re.compile(r"^\s*ADV\b", re.I)
EXIT = re.compile(r"^\s*(wide stop|exit|stop )", re.I)


def count_conditions(spec, name):
    """Entry conditions = module LAYERS lines that are not a time window, an ADV floor or an exit note
    (TRIGGER + FILTERS / CONDS when the module has them); packed CWT / LIQ ids, heat scores and classic strategies by hand.
    n_time = window lines, lowvol in a B3 id adds 1."""
    mod = spec.get("module")
    info = {"module": mod, "n_cond": CLASSIC.get(name.split("@")[0]), "n_time": 0, "kind": spec.get("type") or "classic",
            "count_src": "hand" if name in CLASSIC else None, "layers": None}
    if name.startswith("IDX"):
        info.update(n_cond=2, count_src="hand")
    if not mod or not (ROOT / mod).exists():
        return info
    vals = {}
    for node in ast.parse((ROOT / mod).read_text()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                vals[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    lay = [str(x) for x in (vals.get("LAYERS") or [])]
    info["layers"] = " | ".join(lay)[:300]
    info["n_time"] = sum(bool(TIME.match(l)) for l in lay)
    if "TRIGGER" in vals:
        info.update(n_cond=1 + len(vals.get("FILTERS") or []), count_src="TRIGGER+FILTERS")
    elif "CONDS" in vals:
        info.update(n_cond=len(vals["CONDS"]), count_src="CONDS")
    elif len(lay) == 1 and any(lay[0].startswith(k) for k in HAND):
        k = next(k for k in HAND if lay[0].startswith(k))
        info.update(n_cond=HAND[k] + ("lowvol" in lay[0]), count_src="hand")
    elif lay:
        info.update(n_cond=sum(not (TIME.match(l) or UNIV.match(l) or EXIT.match(l)) for l in lay), count_src="LAYERS")
    return info


rows = []
for acct, (br, f) in ACC.items():
    os.environ["MCF_ACCOUNT"] = acct
    cfg = load_config()
    for name, spec in (cfg.get("strategies") or {}).items():
        spec = spec or {}
        if not spec.get("enabled", True):
            continue
        rows.append({"account": acct, "setup": name, **count_conditions(spec, name), "window": str(spec.get("window")),
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
# whole live record per setup name across all accounts (setups that moved keep one record)
SESS = sorted(tr.date.unique())
la = tr.groupby("strategy").apply(stats).reset_index().rename(columns={"strategy": "setup"})
la["sessions_since_first"] = la["first"].map(lambda d: sum(x >= d for x in SESS))
la["per_session"] = la.n / la.sessions_since_first
m = m.merge(la[["setup", "n", "avg_r", "per_session", "avg_r_wo_best", "t_day"]].add_suffix("_all").rename(
    columns={"setup_all": "setup"}), on="setup", how="left")
m.to_csv(OUT / "census.csv", index=False)

from scipy.stats import spearmanr
print("\n== condition count vs live (setups with >= 10 live trades, whole record across accounts) ==")
u = m.drop_duplicates("setup")
q = u[(u.n_all >= 10) & u.n_cond.notna()]
for y in ("avg_r_all", "per_session_all", "gap_live_minus_bt"):
    z = q[q[y].notna()]
    rho, p = spearmanr(z.n_cond, z[y])
    print(f"{y:22s} n_setups {len(z):3d}  spearman rho {rho:+.3f}  p {p:.3f}")
g = q.assign(k=q.n_cond.clip(upper=6)).groupby("k").agg(setups=("setup", "size"), trades=("n_all", "sum"),
    mean_setup_avg_r=("avg_r_all", "mean"), median_per_session=("per_session_all", "median"),
    mean_gap=("gap_live_minus_bt", "mean"), gap_n=("gap_live_minus_bt", "count"))
tw = tr.merge(u[["setup", "n_cond"]], left_on="strategy", right_on="setup")
g["trade_weighted_avg_r"] = tw.assign(k=tw.n_cond.clip(upper=6)).groupby("k").R.mean()
print(g.round(3).to_string())
print("by count source:", u.count_src.value_counts(dropna=False).to_dict())
print("enabled setups:", len(u), "with a count:", int(u.n_cond.notna().sum()), "with >= 10 live trades:", len(q))
gx = q[~q.setup.str.startswith("GEN")]
for y in ("avg_r_all", "per_session_all"):
    rho, p = spearmanr(gx.n_cond, gx[y]); print(f"non-GEN {y}: n {len(gx)} rho {rho:+.3f} p {p:.3f}")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 40)
print("enabled setups:", len(m), m.account.value_counts().to_dict())
print(m.sort_values("n", ascending=False)[["account", "setup", "n_cond", "n_time", "n", "sessions", "avg_r", "n_all", "avg_r_all", "per_session_all",
                                           "expected_r"]].head(40).to_string())
