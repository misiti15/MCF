import json, numpy as np, pandas as pd
R = json.load(open("rescore.json"))
TOP = [k for k, v in R.items() if v["group"] == "a_top10"]
M = ("res", "cal", "cal2")
bench = {}
for m in M:
    for h in ("fit", "check", "T2"):
        for k in ("avg_r", "avg_r_wo_best_day", "total_r_per_session"):
            v = [R[s][m][h].get(k) for s in TOP]; v = [x for x in v if x is not None]
            bench[(m, h, k)] = (float(np.median(v)), float(max(v)), TOP[int(np.argmax([R[s][m][h].get(k) if R[s][m][h].get(k) is not None else -9 for s in TOP]))])
print("top10 n =", len(TOP))
for m in M:
    print(m, {h: {k: tuple(round(x, 4) if isinstance(x, float) else x for x in bench[(m, h, k)]) for k in ("avg_r", "avg_r_wo_best_day")} for h in ("check", "T2")})
def beats(s, m):
    c, t2 = R[s][m]["check"], R[s][m]["T2"]
    g = lambda d, k: d.get(k) if d.get(k) is not None else -9
    best = all(g(c, k) > bench[(m, "check", k)][1] for k in ("avg_r", "avg_r_wo_best_day")) and \
           all(g(t2, k) > bench[(m, "T2", k)][1] for k in ("avg_r", "avg_r_wo_best_day")) and g(c, "total_r_per_session") > 0 and g(t2, "total_r_per_session") > 0
    med = all(g(c, k) > bench[(m, "check", k)][0] for k in ("avg_r", "avg_r_wo_best_day")) and all(g(t2, k) > bench[(m, "T2", k)][0] for k in ("avg_r", "avg_r_wo_best_day"))
    return ("BEATS" if (best and R[s]["tier_" + m] == "A") else "-"), ("std" if med else "-")
rows = []
for s, v in R.items():
    r = {"setup": s, "grp": v["group"][0]}
    for m in M:
        f, c, t2 = v[m]["fit"], v[m]["check"], v[m]["T2"]
        r[m] = f"{f.get('avg_r', float('nan')):+.3f} / {c.get('avg_r', float('nan')):+.3f} ({c.get('avg_r_wo_best_day') if c.get('avg_r_wo_best_day') is not None else float('nan'):+.3f}) / {t2.get('avg_r', float('nan')):+.3f}"
        r["T_" + m] = v["tier_" + m]
        b, st = beats(s, m); r["B_" + m] = b + "," + st
    r["chk_n/sess"] = v["res"]["check"].get("trades_per_session"); r["chk_t_res"] = v["res"]["check"].get("t_day_clustered"); r["chk_t_cal"] = v["cal"]["check"].get("t_day_clustered")
    r["dcost_chk"] = round((v["cal"]["check"].get("avg_cost") or np.nan) - (v["res"]["check"].get("avg_cost") or np.nan), 3)
    r["lt20"] = v["res"]["check"].get("entry_lt20_share"); r["stop_bps"] = v["res"]["check"].get("med_stop_bps")
    rows.append(r)
df = pd.DataFrame(rows)
pd.set_option("display.width", 400); pd.set_option("display.max_colwidth", 60)
print(df.to_string(index=False))
df.to_csv("table.csv", index=False)
