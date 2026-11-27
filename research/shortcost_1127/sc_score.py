"""SHORTCOST-1127 scoring of the history replay against the pre-registered bars. `python sc_score.py SCRATCH`.
Writes hist_score.json, hist_setups.csv. Educational only - not financial advice."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sc_common as C  # noqa: E402
S = sys.argv[1]
R = pd.read_pickle(os.path.join(S, "hist_res.pkl")); D, T, DAYS = R["D"], R["T"], R["DAYS"]
REAL = ["L3", "RW3", "RW5", "NMETF", "G05", "G07", "G37"]; RND = ["RND-G05", "RND-G07", "RND-G37"]
PERS = ["FIT", "CHECK", "T2"]; NSEED = 20


def daily(d, per, tags):
    x = d[(d.per == per) & d.tag.isin(tags)].groupby("date")["sum"].sum()
    return x.reindex(DAYS[per], fill_value=0.0)


def tagsum(d, per):
    g = d[d.per == per].groupby("tag")[["sum", "count"]].sum()
    return g


out, rows = {}, []
for basis in ("r_ll", "r_lr8"):
    for rule in ["R1", "R2", "R3", "R4"]:
        for per in PERS:
            base = daily(D[("BASE", -1, basis)], per, REAL); ru = daily(D[(rule, -1, basis)], per, REAL)
            o = {"base_R": float(base.sum()), "rule_R": float(ru.sum()), "sessions": len(base),
                 "base_per_session": float(base.mean()), "rule_per_session": float(ru.mean())}
            tb = T[("BASE", basis)]; tr = T[(rule, basis)]
            tb = tb[(tb.per == per) & tb.tag.isin(REAL)]; tr = tr[(tr.per == per) & tr.tag.isin(REAL)]
            o["base_avg"] = float(tb.r.mean()); o["rule_avg"] = float(tr.r.mean()); o["base_n"] = len(tb); o["rule_n"] = len(tr)
            bd = C.bestday(tr.r, tr.date); o["rule_avg_wo_best"] = bd["wo"]; o["rule_best_share"] = bd["share"]
            if basis == "r_ll":
                rnd = np.mean([daily(D[(rule, s, basis)], per, REAL).values for s in range(NSEED)], axis=0)
                rtot = [daily(D[(rule, s, basis)], per, REAL).sum() for s in range(NSEED)]
                diff = ru.values - rnd
                o.update(random_R=float(rnd.sum()), random_R_p90=float(np.percentile(rtot, 90)),
                         rule_pct_vs_random=float(np.mean(np.array(rtot) < ru.sum())),
                         gain_vs_random=float(diff.sum()), gain_t_day=C.day_t(diff),
                         gain_best_day_share=float(diff.max() / diff.sum()) if diff.sum() > 0 else None,
                         gain_wo_best_day=float(diff.sum() - diff.max()))
                # per setup
                for tg in REAL + RND:
                    b0 = tagsum(D[("BASE", -1, basis)], per); b1 = tagsum(D[(rule, -1, basis)], per)
                    rr = [tagsum(D[(rule, s, basis)], per) for s in range(NSEED)]
                    def g(t, k):
                        return float(t.loc[tg, k]) if tg in t.index else 0.0
                    rmean = np.mean([g(t, "sum") for t in rr]); rn = np.mean([g(t, "count") for t in rr])
                    tt = T[(rule, basis)]; tt = tt[(tt.per == per) & (tt.tag == tg)]
                    bdd = C.bestday(tt.r, tt.date)
                    rows.append(dict(rule=rule, per=per, setup=tg, base_n=g(b0, "count"), base_R=g(b0, "sum"),
                                     base_avg=g(b0, "sum") / max(g(b0, "count"), 1), rule_n=g(b1, "count"), rule_R=g(b1, "sum"),
                                     rule_avg=g(b1, "sum") / max(g(b1, "count"), 1), random_R=rmean,
                                     random_avg=rmean / max(rn, 1), gain_vs_random=g(b1, "sum") - rmean,
                                     rule_avg_wo_best=bdd["wo"], rule_best_share=bdd["share"]))
            out[f"{basis}|{rule}|{per}"] = o
P = pd.DataFrame(rows)
P["touched"] = (P.base_n != P.rule_n) | (P.base_R != P.rule_R)
P["d_avg"] = P.rule_avg - P.base_avg
P.round(4).to_csv(os.path.join(HERE, "hist_setups.csv"), index=False)
# bars
verdict = {}
live = json.load(open(os.path.join(HERE, "live_rules.json")))
for rule in ["R1", "R2", "R3", "R4"]:
    b = {}
    for per in ("CHECK", "T2"):
        o = out[f"r_ll|{rule}|{per}"]
        q = P[(P.rule == rule) & (P.per == per) & P.setup.isin(REAL) & P.touched]
        b[per] = dict(b1=o["rule_R"] > o["base_R"], b2=(o["gain_vs_random"] > 0) and (o["gain_t_day"] >= 2.0),
                      b3=(o["gain_wo_best_day"] > 0) and (o["gain_best_day_share"] is not None and o["gain_best_day_share"] < 0.5),
                      improve=int((q.gain_vs_random > 0).sum()), touched=len(q),
                      worst_d_avg=float(q.d_avg.min()) if len(q) else None)
    imp_both = set(P[(P.rule == rule) & (P.per == "CHECK") & P.setup.isin(REAL) & P.touched & (P.gain_vs_random > 0)].setup) & \
        set(P[(P.rule == rule) & (P.per == "T2") & P.setup.isin(REAL) & P.touched & (P.gain_vs_random > 0)].setup)
    tch = set(P[(P.rule == rule) & P.setup.isin(REAL) & P.touched & P.per.isin(["CHECK", "T2"])].setup)
    worst = min(b["CHECK"]["worst_d_avg"] or 0, b["T2"]["worst_d_avg"] or 0)
    b4 = (len(imp_both) >= 2 / 3 * len(tch)) and worst >= -0.02
    b5 = live[rule]["avg_kept"] >= live[rule]["avg_all"]
    ok = all(b[p][k] for p in ("CHECK", "T2") for k in ("b1", "b2", "b3")) and b4 and b5
    verdict[rule] = dict(bars=b, b4=b4, improve_both=sorted(imp_both), touched=sorted(tch), worst_d_avg=worst, b5_live=b5,
                         PASS=ok)
json.dump({"splits": out, "verdict": verdict}, open(os.path.join(HERE, "hist_score.json"), "w"), indent=1, default=float)
pd.set_option("display.width", 250)
for k, o in out.items():
    if k.startswith("r_ll"):
        print(k, {a: (round(v, 3) if isinstance(v, float) else v) for a, v in o.items()})
for k, o in out.items():
    if k.startswith("r_lr8"):
        print(k, {a: round(o[a], 3) for a in ("base_R", "rule_R", "base_avg", "rule_avg")})
for r, v in verdict.items():
    print(r, json.dumps(v, default=str))
print(P[P.per != "FIT"].round(3).to_string())
