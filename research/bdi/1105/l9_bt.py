"""swing1105-L9 (research/bdi/swings/hypotheses.jsonl, pre-registered 2026-11-05 17:33 ET): ONE 2-year backtest.
Pool = every lab long setup entry at/after 10:00 (bt_lab1104 lists, costs in); class A = days SPY <= -1.00% from open at 10:00
(lab context spy_fo, tod 1000). Excess over the setup's own mean in the same split; day-clustered t; N = 5 tonight.
Usage: python l9_bt.py    Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib
from mcf.research.gates import t_required
N = 5; BAR = t_required(N); HERE = Path(__file__).resolve().parent; LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"
T = pd.concat([pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet"))], ignore_index=True)
T["date"] = T.date.astype(str); assert not T.date.between(LK0, LK1).any()
ctx = pd.concat([lib.load_context(m) for m in lib.months()], ignore_index=True); ctx["date"] = ctx.date.astype(str)
assert not ctx.date.between(LK0, LK1).any()
s10 = ctx[ctx.tod == 1000].set_index("date").spy_fo
dly = lib.daily(); dly = dly[dly.symbol == "SPY"].copy(); dly["date"] = dly.date.astype(str)
oc = (dly.set_index("date").close / dly.set_index("date").open - 1) * 100
L = T[(T.side == 1) & (T.tod >= 1000)].copy(); L["s10"] = L.date.map(s10); L["split"] = np.where(L.date < SPLIT, "train", "valid")
L["ex"] = L.r - L.groupby(["setup", "split"]).r.transform("mean"); L["fam"] = L.setup.str.split("-").str[0]; L["A"] = L.s10 <= -1.0
a, b = L[L.A], L[~L.A]
g = a.groupby("date").ex.agg(["sum", "size"]); mu = g["sum"].sum() / g["size"].sum(); G = len(g)
v = ((g["sum"] - mu * g["size"]) ** 2).sum() / g["size"].sum() ** 2 * G / max(G - 1, 1); t = mu / np.sqrt(v)
sp = {s: a[a.split == s].ex.mean() for s in ("train", "valid")}; spn = {s: int((a.split == s).sum()) for s in ("train", "valid")}
wob = (g["sum"].sum() - g["sum"].min()) / (g["size"].sum() - g.loc[g["sum"].idxmin(), "size"])   # without its most negative day (for a guard)
fam = a.groupby("fam").ex.agg(["size", "mean"]); worse = int((fam["mean"] > 0).sum())
ok = bool(sp["train"] <= -0.10 and sp["valid"] <= -0.10 and t <= -BAR and len(a) >= 300 and G >= 15 and worse <= len(fam) / 3 and wob <= -0.05)
P = [f"L9 deep-down-morning long veto: pool {len(L)} long entries >= 10:00 / {L.setup.nunique()} setups; qualifying days {G} "
     f"(SPY <= -1% at 10:00; their SPY o-c mean {oc.reindex(g.index).mean():+.2f}%, down >-0.25 share {(oc.reindex(g.index) < -0.25).mean():.0%})",
     f"  class A n {len(a)} raw {a.r.mean():+.3f}R, excess {mu:+.3f}R, day-t {t:+.2f} (bar {BAR:.2f}); class B raw {b.r.mean():+.3f}R",
     f"  train A excess {sp['train']:+.3f} (n {spn['train']}) | valid {sp['valid']:+.3f} (n {spn['valid']}); excess w/o worst day {wob:+.3f}",
     f"  families with class A {len(fam)}: helped (exA<0) {len(fam) - worse}, harmed {worse}: " + "; ".join(f"{k} {int(r['size'])} {r['mean']:+.3f}" for k, r in fam.sort_values('mean').iterrows()),
     f"  as a filter: keeps {1 - L.A.mean():.1%} of long entries; pool avg {L.r.mean():+.3f} -> {b.r.mean():+.3f}R",
     f"  PASS {ok}", "", "Educational only - not financial advice."]
print("\n".join(P)); (HERE / "l9_bt_out.txt").write_text("\n".join(P) + "\n")
pd.DataFrame([dict(lead="swing1105-L9", n_A=len(a), days=G, excess=mu, t=t, train=sp["train"], valid=sp["valid"], wob=wob, fam_harmed=worse, PASS=ok)]).to_csv(HERE / "l9_bt_results.csv", index=False)
