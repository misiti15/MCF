"""PREVAL 1107 step B: one row per setup from the live journals of all 7 accounts (run_id=1, closed trades, 10-06..11-06).
R after costs = pnl_adj / (|entry - stop| x shares). Pooled across homes; for setups with a non-Graveyard home the
Graveyard and Gen segments are left out (as the Team / nightly do). Also a Primary-only segment for Primary setups.
Columns: trades, sessions, avgR, w/o best day + best-day share (1 day >= 50%), green-day rate (session sum R > 0), worst
day (session sum R), last-10 (avg R of the last 10 trades), ex-market avg R (BETA1 sums merged across the 7 scorecards),
2y lab R (bt_lab1104 lists, 2024-10-01..2026-10-05 minus the locked block 2024-11-01..2025-02-28; else scorecard
expectation), REGX verdicts (trustworthy / weak / false over the setup's rated schemes).
Usage: python stats.py <scratch with p/t1/.../journal.db + reports/scorecard.json>   Educational only - not financial advice."""
import sys, json, sqlite3, glob
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from mcf.analytics import market_beta
from mcf import setup_names
from mcf.report.scorecard import _expected
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
AC = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "gen", "ex1": "explore1", "ll": "livelab"}
TAG = {"primary": "P", "testing": "T1", "testing2": "T2", "graveyard": "GY", "gen": "GEN", "explore1": "EX1", "livelab": "LL"}
A = json.load(open(ROOT / "docs/live/assignments.json"))["setups"]
rows = []
for a, lab in AC.items():
    t = pd.read_sql("select date, strategy, symbol, side, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj from trades "
                    "where run_id=1 and exit is not null", sqlite3.connect(S / a / "journal.db"))
    t["acct"] = lab; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T.to_csv(S / "all_trades.csv", index=False)
# ex-market (scorecard BETA1 sums), per account and merged
parts, parts_acct = {}, {}
for a, lab in AC.items():
    for r in json.load(open(S / a / "reports" / "scorecard.json"))["leaderboard"]:
        if r.get("mkt_n"):
            v = {k: r[k] for k in market_beta.KEYS}
            parts.setdefault(r["setup"], []).append((lab, v))
def exm(setup, accts):
    v = [x for l, x in parts.get(setup, []) if l in accts]
    if not v: return np.nan, np.nan
    f = market_beta.fit(market_beta.merge(v)) or {}
    return f.get("exmkt_r", np.nan), f.get("beta", np.nan)
# 2-year lab lists
LOCK = ("2024-11-01", "2025-02-28")
lab2 = pd.concat(pd.read_parquet(p, columns=["setup", "date", "r"]) for p in sorted(glob.glob(str(Path("/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet")))))
lab2["date"] = lab2.date.astype(str); lab2 = lab2[~lab2.date.between(*LOCK) & (lab2.date <= "2026-10-05")]
bt2 = lab2.groupby("setup").r.agg(["mean", "size"])
EXP = _expected()
BT_EXTRA = {"NM-ETF-late-dip-di-long": (0.25, "swarm1017 train +0.250R / valid +0.029R")}
reg = pd.read_csv(ROOT / "research/bdi/regx/table.csv")
def regx(s):
    g = reg[reg.setup == s]
    if not len(g): return "not rated"
    pit = g[~g.hindsight.astype(bool)].verdict.value_counts()
    d = g[g.scheme == "DASH"]
    dash = f"dash {d.verdict.iloc[0]} ({d.best.iloc[0]}>{d.worst.iloc[0]})" if len(d) else "dash -"
    return f"{dash}; PIT {int(pit.get('trustworthy', 0))}T/{int(pit.get('weak', 0))}W/{int(pit.get('false', 0))}F"
def card(s, g, accts):
    day = g.groupby("date").R.sum(); n = len(g); k = len(day); tot = g.R.sum()
    bd = day.idxmax(); bn = int((g.date == bd).sum())
    exb = (tot - day.max()) / (n - bn) if k >= 2 and n > bn else np.nan
    share = day.max() / tot if tot > 0 and k >= 2 else np.nan
    g2 = g.sort_values(["date", "entry_time"]); l10 = g2.R.tail(10)
    ex, beta = exm(s, accts)
    if s in bt2.index: bt, btn = bt2.loc[s, "mean"], int(bt2.loc[s, "size"])
    elif s in BT_EXTRA: bt, btn = BT_EXTRA[s][0], "swarm"
    elif EXP.get(s) is not None: bt, btn = EXP[s], "screen"
    else: bt, btn = np.nan, ""
    return dict(setup=s, name=setup_names.name(s), now=",".join(TAG.get(x, x) for x in A.get(s, {}).get("accounts", [])),
                seg="+".join(TAG[x] for x in sorted(set(g.acct))), trades=n, sessions=k, avgR=tot / n, totR=tot,
                exbest=exb, best_share=share, one_day=bool(share == share and share >= 0.5), best_day=bd,
                green=(day > 0).mean(), worst=day.min(), worst_day=day.idxmin(), last10=l10.mean(), last10_sum=l10.sum(),
                exmkt=ex, beta=beta, bt2y=bt, bt2y_n=btn, regx=regx(s),
                since1029=g[g.date >= "2026-10-29"].R.mean(), n1029=int((g.date >= "2026-10-29").sum()),
                d1105=day.get("2026-11-05", 0.0), d1106=day.get("2026-11-06", 0.0), last=g.date.max())
out = []
for s, g in T.groupby("strategy"):
    homes = set(g.acct)
    keep = homes - {"graveyard", "gen"} if homes - {"graveyard", "gen"} else homes
    gg = g[g.acct.isin(keep)]
    out.append(card(s, gg, keep))
    if "primary" in homes and len(homes) > 1:
        c = card(s, g[g.acct == "primary"], {"primary"}); c["setup"] = s + " [P only]"; out.append(c)
    if "graveyard" in homes and len(homes) > 1:
        c = card(s, g[g.acct == "graveyard"], {"graveyard"}); c["setup"] = s + " [GY only]"; out.append(c)
C = pd.DataFrame(out)
C.to_csv(OUT / "all_setups.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 320); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 44)
cols = ["setup", "now", "seg", "trades", "sessions", "avgR", "exbest", "best_share", "green", "worst", "last10", "exmkt", "beta", "bt2y", "regx"]
q = C[(C.trades >= 10) & ~C.seg.isin(["GEN"])].sort_values("avgR", ascending=False)
print(q[cols].head(60).round(3).to_string(index=False))
