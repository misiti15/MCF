"""REPS3 - frozen forecast of setup-days/week per account for the 11-12 roster (owner restructure c64d75df0, effective 11-12),
from PRE-11-12 rates only, so the unlocks (halt 120R -> 300R, Gen x1.8 / 300 slots / cap 150, Graveyard x1.6, Testing A full
universe, cap 10 -> 30 in Testing B-F) can be scored against it after >= 5 sessions (score.py, later).
Per enabled setup: p_day = live submitted-day share 10-20..11-10 (>= 5 active sessions; REPS2), else lab
1 - exp(-0.193 x lab trades/day) (REPS2 fit), else 'unknown' (no rate; counted separately).
    python -I forecast.py <MCF root> <reps2_setups.csv> > forecast_out.txt        Educational only - not financial advice."""
import sys, glob, json, math, yaml, pandas as pd
ROOT, R2 = sys.argv[1], sys.argv[2]
live = pd.read_csv(R2, index_col=0); live = live[live.active >= 5]
lab = {k: v["per_day"] for k, v in json.load(open(f"{ROOT}/research/bdi/playingtime/expected_rates.json"))["setups"].items()}
NAME = {"default": "Primary", "testing": "On Deck", "testing2": "Testing A", "explore1": "Testing B", "livelab": "Testing C",
        "testingd": "Testing D", "testinge": "Testing E", "testingf": "Testing F", "gen": "Gen", "graveyard": "Graveyard"}
rows = []
for f in sorted(glob.glob(f"{ROOT}/config/account_*.yaml")) + [f"{ROOT}/config/default.yaml"]:
    key = f.split("/")[-1].replace("account_", "").replace(".yaml", "")
    for k, v in ((yaml.safe_load(open(f)) or {}).get("strategies") or {}).items():
        if not (v or {}).get("enabled", True): continue
        if k in live.index: p, src = float(live.loc[k, "p_day"]), "live"
        elif k in lab: p, src = 1 - math.exp(-0.193 * lab[k]), "lab"
        else: p, src = float("nan"), "unknown"
        rows.append(dict(account=NAME.get(key, key), setup=k, p_day=p, src=src))
F = pd.DataFrame(rows); F.to_csv("forecast_setups.csv", index=False)
print("REPS3 forecast (frozen before 11-12 open). setup-days/week = 5 x sum p_day over setups with a rate.")
g = F.groupby("account")
T = pd.DataFrame({"setups": g.size(), "with_rate": g.p_day.count(), "unknown": g.src.apply(lambda s: (s == "unknown").sum()),
                  "fc_setup_days_wk": 5 * g.p_day.sum(), "median_per_slot": 5 * g.p_day.median()})
print(T.round(2).to_string()); print(f"TOTAL forecast {5 * F.p_day.sum():.1f} setup-days/week on {F.p_day.count()} rated setups "
                                      f"(+{int((F.src == 'unknown').sum())} unrated)")
print("Baseline 10-20..11-10 (REPS2): ~482 setup-days/week. Educational only - not financial advice.")
