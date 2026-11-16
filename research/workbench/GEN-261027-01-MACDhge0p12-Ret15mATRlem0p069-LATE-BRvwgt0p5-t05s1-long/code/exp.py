"""Mechanic GEN-261027-01: screen. Every config scored with the identical engine on the 2y backtest (train / valid / all,
up / flat / down sessions) and the replay of the live sessions; paired by day vs the parent; counted (one row = one config).
Usage: python exp.py <configs.json>. Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
import lib
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d"); REG = reg.set_index("date").regime
def norm(v):
    return {k: (tuple(tuple(e) for e in x) if k in ("extra", "conds") else (tuple(x) if isinstance(x, list) else x)) for k, x in v.items()}
def score(name, v, base2, baseR):
    t2 = trades(C2, P2, v); tr = trades(RC, RP, v)
    s2 = stats(t2); sr = stats(tr)
    T = t2[t2.date <= "2025-12-31"].r; V = t2[t2.date > "2025-12-31"].r
    rg = t2.date.map(REG)
    p2 = paired(t2, base2, DAYS2) if base2 is not None else (0, 0); pr = paired(tr, baseR, DAYSR) if baseR is not None else (0, 0)
    return t2, tr, dict(cfg=name, n2=s2["n"], T=round(T.mean(), 3), V=round(V.mean(), 3), nV=len(V), avg2=s2["avg"], wob2=s2["wobest"],
                worst2=s2["worst"], win2=s2["win"], aw2=s2["avgw"], al2=s2["avgl"], up=round(t2.r[rg == "up"].mean(), 3),
                flat=round(t2.r[rg == "flat"].mean(), 3), down=round(t2.r[rg == "down"].mean(), 3), hold2=s2["hold"], pd2=p2[0], dt2=p2[1],
                nR=sr.get("n"), avgR=sr.get("avg"), wobR=sr.get("wobest"), worstR=sr.get("worst"), pdR=pr[0], dtR=pr[1])
if __name__ == "__main__":
    CF = json.loads(open(sys.argv[1]).read())
    base2, baseR, row = score("parent", {}, None, None)
    rows = [row]; print(" ".join(f"{k}={v}" for k, v in row.items()), flush=True)
    for name, v in CF.items():
        _, _, row = score(name, norm(v), base2, baseR); rows.append(row)
        print(" ".join(f"{k}={v}" for k, v in row.items()), flush=True)
    pd.DataFrame(rows).to_csv(OUT + sys.argv[1].split("/")[-1].replace(".json", ".csv"), index=False)
