"""BDI 2026-10-27 per-account session review (owner 2026-10-27: one block per account). Inputs: per_trade_1027.csv
(this folder, from trades_bdi.py), skipped_1027.csv (skipped.py), research/bdi/nightly1027/trades.csv (journal rows).
Per account: P/L after costs, trades, win% vs break-even win% (avg loss R / (avg win R + avg loss R)), avg R, by side,
by entry hour, exit what-ifs, best / worst setups (display name + id), lots-per-setup clustering, skipped signals.
Usage: python accounts.py > accounts_out.txt     Educational only - not financial advice."""
import json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
NM = json.load(open(ROOT / "docs/live/setup_names.json"))
def nm(s):
    if s in NM: return NM[s]["name"]
    if s.endswith("-FD") and s[:-3] in NM: return NM[s[:-3]]["name"] + " (all day)"
    return "?"
P = pd.read_csv(HERE / "per_trade_1027.csv"); K = pd.read_csv(HERE / "skipped_1027.csv")
J = pd.read_csv(ROOT / "research/bdi/nightly1027/trades.csv")
P["hour"] = P.entry_t.str[:2]
pd.set_option("display.width", 250)
W = ["live", "be05", "t05", "t1", "trail", "hold", "sar", "reent", "opp"]
for a, lab in (("p", "Primary"), ("t1", "Testing 1"), ("t2", "Testing 2"), ("gy", "Graveyard"), ("gen", "Setup Generator")):
    x = P[P.acct == a]; win = x[x.live > 0]; los = x[x.live <= 0]
    aw, al = win.live.mean(), -los.live.mean()
    be = al / (aw + al)
    print(f"\n######## {lab} ({a}): n {len(x)}, P/L after costs ${x.pnl_adj.sum():.2f}, win {len(win)/len(x):.1%} vs break-even {be:.1%}"
          f" (avg win {aw:+.3f}R, avg loss -{al:.3f}R), avg R {x.live.mean():+.3f}, sum R {x.live.sum():+.1f}")
    print("-- by side");  print(x.groupby("side").agg(n=("live", "size"), win=("live", lambda v: (v > 0).mean()), avgR=("live", "mean"), pl=("pnl_adj", "sum")).round(3).to_string())
    print("-- by entry hour"); print(x.groupby("hour").agg(n=("live", "size"), avgR=("live", "mean"), pl=("pnl_adj", "sum"), hold=("hold", "mean"), opp=("opp", "mean")).round(3).to_string())
    print("-- exit what-ifs (sum R after costs)"); print(x[W].sum().round(1).to_string())
    print("-- by setup")
    g = x.groupby("setup").agg(n=("live", "size"), win=("live", lambda v: (v > 0).mean()), avgR=("live", "mean"), sumR=("live", "sum"), pl=("pnl_adj", "sum"),
                               t1=("t1", "sum"), trail=("trail", "sum"), hold=("hold", "sum"), never=("loss_type", lambda v: (v == "never_worked").sum()),
                               maxclus=("cluster", "max")).round(3).sort_values("pl")
    g.insert(0, "name", [nm(s)[:34] for s in g.index]); print(g.to_string())
    print("-- loss types"); print(x[x.live <= 0].groupby("loss_type").agg(n=("live", "size"), pl=("pnl_adj", "sum")).round(1).to_string())
    k = K[K.acct == a]
    if len(k):
        print("-- skipped signals replayed (R after costs)"); print(k.groupby("reason").R.agg(["size", "mean", "sum"]).round(3).to_string())
print("\nEducational only - not financial advice.")
