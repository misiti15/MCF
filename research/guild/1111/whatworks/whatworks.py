"""WHATWORKS (descriptive, 0 configs; Lead lead-20261110-2300-3). Every live setup x account (7 journals, live paper run only,
to 11-10): positive after live paper costs AND avg w/o best day > 0 AND best-day share < 50% (n >= 20 trades, >= 5 days).
R = pnl_adj / (|entry - stop| x shares). Lab column: GEN screen valid exp_r from config (others: from Builder's bt lists).
Rule changes = ledger entries effective inside the setup's live window that name the setup or its account (or all).
    python whatworks.py <dir with mcf-data*.db>          Educational only - not financial advice."""
import sys, json, sqlite3, re, glob, os
import numpy as np, pandas as pd
DIR = sys.argv[1]; ROOT = "/home/user/MCF"
ACCT = {"mcf-data": "primary", "mcf-data-testing": "testing", "mcf-data-testing2": "testing2", "mcf-data-graveyard": "graveyard",
        "mcf-data-gen": "gen", "mcf-data-explore1": "explore1", "mcf-data-livelab": "livelab"}
rows = []
for p in sorted(glob.glob(f"{DIR}/mcf-data*.db")):
    acct = ACCT[os.path.basename(p)[:-3]]; c = sqlite3.connect(p)
    pid = [r[0] for r in c.execute("select id from runs where kind='paper'")]
    if not pid: continue
    t = pd.read_sql(f"select strategy, symbol, date, side, entry, stop, shares, pnl_adj from trades where run_id in ({','.join(map(str, pid))}) and pnl_adj is not null", c)
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t = t[(t.risk > 0) & (t.date <= "2026-11-10")]
    t["R"] = t.pnl_adj / t.risk; t["account"] = acct; rows.append(t)
T = pd.concat(rows, ignore_index=True)
print(f"live paper trades {len(T)} ({T.strategy.nunique()} setups, {T.account.nunique()} accounts, {T.date.min()}..{T.date.max()})")
# lab column for GEN setups (screen valid exp_r stored in config/account_gen.yaml)
lab = {}
try:
    import yaml
    for f in glob.glob(f"{ROOT}/config/account_*.yaml"):
        y = yaml.safe_load(open(f)) or {}
        for k, v in (y.get("strategies") or {}).items():
            sc = ((v or {}).get("gen") or {}).get("screen") or {}
            if "valid" in sc: lab[k] = f"screen valid {sc['valid'].get('exp_r'):+.3f} (n {sc['valid'].get('n')})"
except Exception as e:
    print("yaml read failed:", e)
L = [json.loads(l) for l in open(f"{ROOT}/research/ledger.jsonl")]
def changes(setup, acct, d0, d1):
    out = []
    for e in L:
        eff = str(e.get("effective") or e.get("date") or "")[:10]
        if not (d0 < eff <= d1): continue
        txt = json.dumps(e)
        if setup in txt or (re.search(rf"\b{acct}\b", txt, re.I) and not re.search(r"GEN-|CWT|MF\d|RW\d|NS\d|L3-", e.get("title", ""))):
            out.append(f"{eff} {e.get('id')}")
    return out
res = []
for (s, a), g in T.groupby(["strategy", "account"]):
    if len(g) < 20 or g.date.nunique() < 5: continue
    gd = g.groupby("date").R.sum(); tot = gd.sum(); b = gd.idxmax()
    wob = (tot - gd.max()) / max(1, len(g) - int((g.date == b).sum()))
    share = gd.max() / tot if tot > 0 else np.nan
    res.append(dict(setup=s, account=a, n=len(g), days=g.date.nunique(), avg_r=g.R.mean(), total_r=tot, wo_best=wob,
                    best_share=share, best_day=b, first=g.date.min(), last=g.date.max(),
                    long_share=float((g.side > 0).mean()), lab=lab.get(s, "(Builder: 2y lab avg R)")))
R = pd.DataFrame(res)
W = R[(R.avg_r > 0) & (R.wo_best > 0) & (R.best_share < 0.5)].sort_values("wo_best", ascending=False).copy()
W["rule_changes"] = [len(changes(s, a, f, l)) for s, a, f, l in zip(W.setup, W.account, W["first"], W["last"])]
print(f"setup x account rows with n >= 20 and >= 5 days: {len(R)}; positive: {int((R.avg_r > 0).sum())}; "
      f"+ w/o best day: {int(((R.avg_r > 0) & (R.wo_best > 0)).sum())}; + best-day share < 50%: {len(W)}")
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 60)
print(W[["setup", "account", "n", "days", "avg_r", "wo_best", "best_share", "total_r", "long_share", "first", "last", "rule_changes", "lab"]].round(3).to_string(index=False))
W.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatworks_live.csv"), index=False)
R.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatworks_all.csv"), index=False)
for s, a, f, l in zip(W.setup, W.account, W["first"], W["last"]):
    ch = changes(s, a, f, l)
    if ch: print(f"  {s} [{a}] rule changes in window: " + "; ".join(ch[:6]) + (" ..." if len(ch) > 6 else ""))
print("Educational only - not financial advice.")
