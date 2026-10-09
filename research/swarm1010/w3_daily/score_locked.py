"""ONE-TIME lead scoring of the W3 finalists on the rule-19 locked block (trades ENTERED 2024-11-01..2025-02-28),
costs as study.py (1c + 1 bps per side). Educational only - not financial advice.
    python research/swarm1010/w3_daily/score_locked.py"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
src = (HERE / "study.py").read_text().split('if __name__ == "__main__":')[0]
src = src.replace('LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")',
                  'LOCK_A, LOCK_B = pd.Timestamp("1900-01-01"), pd.Timestamp("1900-01-02")  # lead: no blanking')
g = {"__name__": "w3study", "__file__": str(HERE / "study.py")}
exec(compile(src, "study.py", "exec"), g)
A, B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
dates = g["dates"]
out = {}


def report(name, t):
    ed = dates[t.ei.to_numpy()]
    t = t[(ed >= A) & (ed <= B)].copy()
    b = g["bench"](t) if "bench" in g else None
    r = t["net"].to_numpy()
    d = pd.Series(r).groupby(dates[t.i.to_numpy()]).agg(["sum", "size"])
    mu = r.mean(); se = np.sqrt(((d["sum"] - d["size"] * mu) ** 2).sum()) / len(r)
    res = {"n": int(len(r)), "net_bps": round(mu * 1e4, 1), "t_day_clustered": round(mu / se, 2), "win_rate": round(float((r > 0).mean()), 3)}
    try:
        res["excess_bps"] = round(float((t["net"] - b).mean()) * 1e4, 1) if b is not None else None
    except Exception:
        pass
    out[name] = res
    print(name, res, flush=True)


above = (g["C"] > g["sma200"]).to_numpy()
s = above & (g["rsi3"] < 5).to_numpy()
report("F2_rsi3_5_O_SMA5_L", g["make_trades"](s, 1, "O", "SMA5", elig=g["ELIG200"]))
s2 = g["xs_decile"](g["ret5"], g["ELIG200"], False)
report("F3_rev5_bot_k20_L", g["make_trades"](s2, 1, "C", "K", k=20, elig=g["ELIG200"]))
spy = g["C"]["SPY"]
out["_context"] = {"SPY_return_block_pct": round(float(spy[(spy.index >= A) & (spy.index <= B)].iloc[-1] / spy[(spy.index >= A)].iloc[0] - 1) * 100, 2)}
json.dump(out, open(HERE / "locked.json", "w"), indent=1)
