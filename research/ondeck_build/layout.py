"""ONDECK build 2026-11-11: the proposed layout (On Deck = testing, Testing A = testing2, Testing B = explore1,
Testing C = livelab) and the move list, from docs/live/assignments.json (TEAM-6 state) + roster.csv.
Writes moves.csv, layout.csv. Educational only - not financial advice."""
import json
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
A = json.load(open(ROOT / "docs/live/assignments.json"))["accounts"]
C = pd.read_csv(HERE / "candidates.csv").set_index("setup")
P = pd.read_csv(HERE / "setup_peaks.csv").set_index("strategy")
LAB = {"testing": "On Deck", "testing2": "Testing A", "explore1": "Testing B", "livelab": "Testing C"}
ROSTER = list(pd.read_csv(HERE / "roster.csv").setup)
PROTECTED = {"MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "L3-gap-slope-rsi5hi-FD", "MF4-h40-open-flowsell",
             "NS1-rsidip-rsi5pop-long"}  # rule 20, demoted from Primary 11-11, protected to ~11-25
# On Deck leavers (fail OD-IN) -> testing area; busy full-universe records go to B / C (cap lifted 10 -> 30, ODX-4)
TO = {"L3-gap-slope-rsi5hi-FD": "explore1", "MF4-h40-open-flowsell-FD": "explore1", "NS1-rsidip-rsi5pop-long-FD": "explore1",
      "NS4-pm-vwap-reclaim-oversold-short-FD": "explore1", "CWT05-flush-m05-v3-long": "explore1",
      "MF2-open-rsimidhi-flowsell-FD": "livelab", "MF1-945-flowsell-vwapup": "livelab", "NS3-failed-vwap-reclaim-short": "livelab",
      "exhaustion_short": "livelab", "intraday_momentum": "livelab"}
DUP_OFF = {"MF5-flowsell-vwapup-rsi5hi": "testing2", "exhaustion_short-FD": "testing2"}  # one home each (ROT-A 5-6)
home = {}
for a in ("testing", "testing2", "explore1", "livelab"):
    for s in A[a]: home.setdefault(s, []).append(a)
new, mv = {}, []
for s, hs in home.items():
    if s in ROSTER: dst = "testing"
    elif s in DUP_OFF: dst = DUP_OFF[s]
    elif s in TO: dst = TO[s]
    else: dst = hs[0]
    new[s] = dst
    for h in hs:
        if h != dst:
            mv.append(dict(setup=s, name=C.loc[s, "name"] if s in C.index else s, frm=LAB[h], to=LAB[dst],
                           kind="dual-home fix (switch off in On Deck)" if s in DUP_OFF else ("into On Deck (OD-IN)" if dst == "testing" else "out of On Deck (fails OD-IN)"),
                           protected=s in PROTECTED, sessions=C.loc[s, "sessions"] if s in C.index else None,
                           trades=C.loc[s, "trades"] if s in C.index else None, shrunk=C.loc[s, "shrunk"] if s in C.index else None))
M = pd.DataFrame(mv).sort_values(["kind", "to", "setup"]); M.to_csv(HERE / "moves.csv", index=False, float_format="%.3f")
L = pd.DataFrame([dict(setup=s, account=LAB[a], side=C.loc[s, "side"], sessions=C.loc[s, "sessions"], trades=C.loc[s, "trades"],
                       ent_ps=C.loc[s, "ent_ps"], peak_p90=P.peak_p90.get(s)) for s, a in new.items()])
L = L.sort_values(["account", "sessions", "trades"]); L.to_csv(HERE / "layout.csv", index=False, float_format="%.2f")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(M.to_string(index=False))
print(L.groupby("account").agg(setups=("setup", "size"), entries_ps=("ent_ps", "sum"), p90_sum=("peak_p90", "sum")).round(1))
print(L.groupby(["account", "side"]).size().unstack(fill_value=0))
assert len(new) == 72
