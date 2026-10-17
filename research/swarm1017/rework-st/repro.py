"""Reproduce parents (source window and FD) on the open history. Educational only - not financial advice."""
from common import PARENT, PGEOM, PSIDE, SRCWIN, WM, core, pick, score
import json
from mcf.research import gates
from research.history2y import lib
from common import trades
REG = lib.regimes()
out = {}
for p in PARENT:
    for w in (SRCWIN[p], "0950-1500"):
        for rf in (False, True):
            idx = pick(core(p, PARENT[p]) & WM[w], PSIDE[p], PGEOM[p], rf)
            sc = score(idx, p, PSIDE[p], PGEOM[p])
            reg = gates.regime_split(trades(idx, PSIDE[p], PGEOM[p]), REG)
            k = f"{p} {w} {'refire' if rf else 'first'}"
            out[k] = {**{a: round(b, 4) if isinstance(b, float) else b for a, b in sc.items()},
                      "up": reg["up"].get("exp_r"), "down": reg["down"].get("exp_r")}
            print(k, sc["n_all"], round(sc["exp_all"], 4), round(sc["t_all"], 2), "| tr", sc["n_tr"], round(sc["exp_tr"], 4),
                  "va", sc["n_va"], round(sc["exp_va"], 4), "xs", round(sc["xs_all"], 4), "up/dn", out[k]["up"], out[k]["down"])
json.dump(out, open("repro.json", "w"), indent=1)
