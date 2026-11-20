"""Score the LPB grid: FIT for every config, CHECK once for the finalists + parent. Educational only."""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, "/home/user/MCF")
import bench10 as B
from grid import GRID, f32
W = Path(sys.argv[1])
C = pd.read_parquet(W / "cand_walked.parquet")
B.no_locked(C.date.unique())
C = C.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
spy = B.spy_t1(); days = pd.Series(spy.index); days = days[days <= C.date.max()]
h = B.half(days); NS = {"fit": int((h == "fit").sum()), "check": int((h == "check").sum())}
ETB = pd.Series(dtype=float)
PARENT = (1400, 0.12, -0.069, 20e6)

def trades(cfg):
    wlo, mh, ra, adv = cfg
    x = C[(C.tod >= wlo) & (C.mh >= f32(mh)) & (C.ra <= f32(ra)) & (C.adv20 >= adv)]
    x = x.drop_duplicates(["symbol", "date"], keep="first")          # first qualifying bar per symbol-day
    t = B.add_r(x)
    t["half"] = B.half(t.date)
    return B.book(t, B.TESTING_RULES, ETB)

def ci(t):
    m = t.r.mean(); e = (t.r - m).groupby(t.date).sum(); se = math.sqrt(float((e ** 2).sum())) / len(t)
    return m - 1.96 * se, m + 1.96 * se

def row(cfg, t, half):
    s = B.stats(t[t.half == half], NS[half], spy)
    lo, hi = ci(t[t.half == half]) if s["trades"] > 2 else (np.nan, np.nan)
    return {"wlo": cfg[0], "macd_hist": cfg[1], "ret3_atr": cfg[2], "adv": cfg[3] / 1e6, **{k: s.get(k) for k in (
        "trades", "trades_per_session", "sessions_traded", "win", "avg_r", "avg_r_wo_best_day", "best_day", "best_day_share",
        "total_r_per_session", "worst_day", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down")},
        "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}

N = len(GRID); BAR = max(1.5, math.sqrt(2 * math.log(N)))
T = {cfg: trades(cfg) for cfg in GRID}
fit = pd.DataFrame([row(c, T[c], "fit") for c in GRID])
fit.to_csv(W / "fit_all.csv", index=False)
p = fit[(fit.wlo == 1400) & (fit.macd_hist == 0.12) & (fit.ret3_atr == -0.069) & (fit.adv == 20)].iloc[0]
fin = fit[(fit.trades_per_session > p.trades_per_session) & (fit.avg_r >= p.ci_lo)
          & ~((fit.wlo == 1400) & (fit.macd_hist == 0.12) & (fit.ret3_atr == -0.069) & (fit.adv == 20))]
print("N", N, "bar", round(BAR, 2), "sessions", NS); print("PARENT FIT", p.to_dict())
pd.set_option("display.width", 250)
print(fit.sort_values("trades_per_session")[["wlo", "macd_hist", "ret3_atr", "adv", "trades", "trades_per_session", "avg_r",
      "ci_lo", "avg_r_wo_best_day", "best_day_share", "t_day_clustered", "worst_day"]].to_string(index=False))
print("FINALISTS on FIT:", len(fin))
chk_cfgs = [PARENT] + [(int(r.wlo), r.macd_hist, r.ret3_atr, r.adv * 1e6) for r in fin.itertuples()]
chk = pd.DataFrame([row(c, T[c], "check") for c in chk_cfgs])
# paired by day vs parent on CHECK
pt = T[PARENT]; pd_ = pt[pt.half == "check"].groupby("date").r.sum()
chkdays = days[h == "check"]
pair = []
for c in chk_cfgs:
    t = T[c]; d = t[t.half == "check"].groupby("date").r.sum()
    diff = (d.reindex(chkdays, fill_value=0) - pd_.reindex(chkdays, fill_value=0))
    pair.append((round(diff.mean(), 3), round(diff.mean() / (diff.std() / math.sqrt(len(diff))), 2) if diff.std() > 0 else None))
chk["paired_day_diff"] = [x[0] for x in pair]; chk["paired_t"] = [x[1] for x in pair]
chk.to_csv(W / "check_finalists.csv", index=False)
print("CHECK"); print(chk.to_string(index=False))
json.dump({"N": N, "bar": BAR, "sessions": NS}, open(W / "meta.json", "w"))
