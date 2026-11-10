"""stoplab prep: one row per live trade across all 7 accounts (+ what-if rows of signals blocked by a daily stop).

Usage: python research/stoplab/build_trades.py <journal_dir>
  <journal_dir>/<branch>.db = `git show origin/<branch>:journal.db` for the 7 mcf-data* branches.
Writes research/stoplab/trades.csv.gz, research/stoplab/setups.csv (inventory + lab-module status), counts.json.

R convention: live (run 1) R = pnl_adj / (|entry - stop| x shares) (costs + stop-slippage allowance in, the
dashboard convention); what-if (run 2) R = r_multiple (runner what-if simulate() with backtest costs).
Educational only - not financial advice.
"""
import json, re, sqlite3, sys
from pathlib import Path
import pandas as pd, yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
J = Path(sys.argv[1])
ACCTS = [("primary", "mcf-data", "default.yaml"), ("testing", "mcf-data-testing", "account_testing.yaml"),
         ("testing2", "mcf-data-testing2", "account_testing2.yaml"), ("gen", "mcf-data-gen", "account_gen.yaml"),
         ("graveyard", "mcf-data-graveyard", "account_graveyard.yaml"),
         ("explore1", "mcf-data-explore1", "account_explore1.yaml"), ("livelab", "mcf-data-livelab", "account_livelab.yaml")]
LATCH = "setup daily loss limit"
HALT = ("halted", "daily loss limit")
LOCKED = ("2024-11-01", "2025-02-28")


def et(s):
    return pd.to_datetime(s, utc=True, format="mixed").dt.tz_convert("America/New_York")


rows = []
for acct, br, _ in ACCTS:
    c = sqlite3.connect(J / f"{br}.db")
    t = pd.read_sql("select id, run_id, symbol, strategy setup, side, date, signal_time, entry_time, exit_time, entry, "
                    "stop, target, exit, exit_reason, r_multiple, mfe_r, mae_r, shares, pnl, pnl_adj, slip_bps, meta "
                    "from trades where run_id in (1, 2)", c)
    why = t.meta.fillna("").str.extract(r"why=(.*)$")[0]
    t["why"] = why.where(t.run_id == 2)
    t["whatif"] = t.run_id == 2
    t["blocked_latch"] = t.whatif & (t.why == LATCH)
    t["blocked_halt"] = t.whatif & t.why.isin(HALT)
    # keep every live trade + what-ifs of signals blocked only by a daily stop (setup latch or account halt);
    # other skip reasons (ETB, spread, lot cap, ...) would be skipped under any stop level.
    t = t[(t.run_id == 1) | t.blocked_latch | t.blocked_halt].copy()
    risk = (t.entry - t.stop).abs()
    t["risk_ps"] = risk
    t["R"] = (t.pnl_adj / (risk * t.shares)).where(t.run_id == 1, t.r_multiple)
    t["account"] = acct
    for col in ("signal_time", "entry_time", "exit_time"):
        t[col] = et(t[col])
    # what-if entry = the signal bar; live entry = the fill
    t["ent_hhmm"] = t.entry_time.dt.strftime("%H%M").astype(int)
    t["ext_hhmm"] = t.exit_time.dt.strftime("%H%M").astype(int)
    t["hold_min"] = (t.exit_time - t.entry_time).dt.total_seconds() / 60
    rows.append(t.drop(columns=["meta"]))
T = pd.concat(rows, ignore_index=True)
assert not T.date.between(*LOCKED).any()
T = T.sort_values(["account", "setup", "date", "entry_time", "id"]).reset_index(drop=True)
T["src_id"] = T.pop("id")
for col in ("signal_time", "entry_time", "exit_time"):
    T[col] = T[col].dt.strftime("%Y-%m-%d %H:%M:%S%z")
T.to_csv(HERE / "trades.csv.gz", index=False, compression="gzip")

# setup inventory from the 7 current configs (lab module present on disk?)
inv = []
for acct, _, f in ACCTS:
    cfg = yaml.safe_load((ROOT / "config" / f).read_text()) or {}
    for name, p in (cfg.get("strategies") or {}).items():
        if not isinstance(p, dict):
            continue
        mod = p.get("module")
        inv.append(dict(account=acct, setup=name, enabled=bool(p.get("enabled", True)), type=p.get("type"),
                        module=mod, module_exists=bool(mod and (ROOT / mod).exists())))
I = pd.DataFrame(inv)
L = T[~T.whatif].groupby(["account", "setup"]).agg(live_n=("R", "size"), live_sessions=("date", "nunique"),
                                                   first=("date", "min"), last=("date", "max"),
                                                   sumR=("R", "sum"), avgR=("R", "mean")).reset_index()
B = T[T.whatif].groupby(["account", "setup"]).agg(wi_latch=("blocked_latch", "sum"), wi_halt=("blocked_halt", "sum")).reset_index()
M = L.merge(B, on=["account", "setup"], how="outer").merge(I, on=["account", "setup"], how="left")
# lab status by setup name (any account's config)
lab = I[I.type.eq("lab") & I.module_exists].drop_duplicates("setup").set_index("setup").module
M["lab_module"] = M.setup.map(lab)
M["in_config"] = M.setup.isin(I.setup)
M.to_csv(HERE / "setups.csv", index=False)

cnt = {}
for acct, g in T.groupby("account"):
    lv = g[~g.whatif]
    cnt[acct] = dict(live_trades=int(len(lv)), setups=int(lv.setup.nunique()), sessions=int(lv.date.nunique()),
                     first=lv.date.min(), last=lv.date.max(), wi_latch=int(g.blocked_latch.sum()),
                     wi_halt=int(g.blocked_halt.sum()), live_null_mfe=int(lv.mfe_r.isna().sum()))
lv = T[~T.whatif]
cnt["all"] = dict(live_trades=int(len(lv)), setups=int(lv.setup.nunique()), setup_accounts=int(lv.groupby(["account", "setup"]).ngroups),
                  sessions=int(lv.date.nunique()), wi_latch=int(T.blocked_latch.sum()), wi_halt=int(T.blocked_halt.sum()),
                  setups_with_lab_module=int(M[M.live_n.notna()].drop_duplicates("setup").lab_module.notna().sum()))
(HERE / "counts.json").write_text(json.dumps(cnt, indent=1))
print(json.dumps(cnt, indent=1))
