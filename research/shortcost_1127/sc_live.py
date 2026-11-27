"""SHORTCOST-1127 Part A: live cost map + live replay of the rules. `python sc_live.py SCRATCH` (SCRATCH holds the
primshorts_1126 live.parquet / exitbars.parquet and etb_rate.parquet). Writes live_map.json, live_rules.json,
live_setups.csv here. Educational only - not financial advice."""
import json, os, re, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "primshorts_1126"))
import sc_common as C  # noqa: E402
import calib_live as CL  # noqa: E402
S = sys.argv[1]
CL.L = S
t = CL.prep()
C.no_locked(t.date)
s = t.side
eng = np.where(s > 0, np.minimum(t.x_open, t.stop), np.maximum(t.x_open, t.stop))
eng = np.where(np.isnan(t.x_open), t.stop, eng)
xeng = np.where(t.kind == "stop", eng, np.where(t.kind == "market", t.x_open, t.target))
t["gross"] = s * (xeng - t.ref_price) / t.risk_ps
t["ll_cost"] = C.cost_kind(t.ref_price, t.risk_ps, t.kind)
t["net_ll"] = t.gross - t.ll_cost
t["net_real"] = t.gross - t.real_R
t["net_lr8"] = t.gross - t.res_R
t["cex"] = C.c_ex(t.ref_price, t.risk_ps)
etb = pd.read_parquet(os.path.join(S, "etb_rate.parquet")).rate
t["etb"] = np.where(s > 0, "long", np.where(t.symbol.map(etb).fillna(-1) >= 1.0, "ETB-always",
                    np.where(t.symbol.map(etb).fillna(-1) >= 0, "ETB-marginal", "ETB-unknown")))
t["sb"] = pd.cut(t.spread_bps, [-1, 10, 20, 35, 1e9], labels=["<10", "10-20", "20-35", "35+"]).astype(str)


def fam(x):
    if x.startswith("GEN-"):
        return "GEN-" + ("short" if x.endswith("short") else "long")
    m = re.match(r"[A-Za-z]+", x)
    head = m.group(0) if m else x
    if "_" in x.split("-")[0]:
        return x.split("-")[0]
    return head
t["fam"] = t.strategy.map(fam)
t["sidel"] = np.where(s > 0, "long", "short")
# clip the net-R outliers as calib_live does for its cost tables (winsorise 1/99 on gross); report raw too
lo, hi = t.gross.quantile([0.005, 0.995])
t["net_ll_w"] = t.gross.clip(lo, hi) - t.ll_cost
NG = t.account != "graveyard"


def tab(g):
    b = C.bestday(g.net_ll, g.date)
    return pd.Series({"n": len(g), "cost_ll": g.ll_cost.mean(), "cost_real": g.real_R.mean(), "cost_lr8": g.res_R.mean(),
                      "cex": g.cex.mean(), "gross": g.gross.mean(), "net_ll": g.net_ll.mean(), "net_ll_w": g.net_ll_w.mean(),
                      "net_real": g.net_real.mean(), "t_day": C.clustered_t(g.net_ll, g.date), "wo_best": b["wo"],
                      "best_share": b["share"]})


out = {"n_all": int(len(t)), "n_nongy": int(NG.sum()), "dates": [t.date.min(), t.date.max()]}
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
for col in ("pb", "sb", "tb", "etb", "wb"):
    x = t.groupby([col, "sidel"]).apply(tab).round(4)
    print("\n== by", col, "x side (all accounts)"); print(x.to_string())
    out[f"by_{col}"] = {f"{a}|{b}": v for (a, b), v in x.to_dict("index").items()}
x = t[NG].groupby(["pb", "sidel"]).apply(tab).round(4); print("\n== price x side, non-GY"); print(x.to_string())
out["by_pb_nongy"] = {f"{a}|{b}": v for (a, b), v in x.to_dict("index").items()}
x = t.groupby(["fam", "sidel"]).apply(tab).round(4); x = x[x.n >= 200].sort_values("cost_ll")
print("\n== family x side (n>=200)"); print(x.to_string())
out["by_fam"] = {f"{a}|{b}": v for (a, b), v in x.to_dict("index").items()}
# zones: price x width x side x tod, n >= 200
z = t.groupby(["pb", "wb", "sidel", "tb"]).apply(tab)
z = z[z.n >= 200].round(4).sort_values("cost_ll")
print("\n== zones price x width x side x tod (n>=200), cheapest first"); print(z.to_string())
out["zones"] = {"|".join(k): v for k, v in z.to_dict("index").items()}
z2 = t.groupby(["pb", "sb", "sidel"]).apply(tab); z2 = z2[z2.n >= 200].round(4).sort_values("cost_ll")
print("\n== price x spread x side (n>=200)"); print(z2.to_string())
out["zones_spread"] = {"|".join(k): v for k, v in z2.to_dict("index").items()}
# c_ex calibration on live (in-sample): decile of c_ex vs realised cost
t["cdec"] = pd.qcut(t.cex, 10, labels=False)
x = t.groupby(["cdec", "sidel"]).apply(tab).round(4); print("\n== c_ex decile x side"); print(x.to_string())
out["by_cex_decile"] = {f"{a}|{b}": v for (a, b), v in x.to_dict("index").items()}
json.dump(out, open(os.path.join(HERE, "live_map.json"), "w"), indent=1, default=float)

# ---------------- live replay of the rules (non-Graveyard; no slot refill)
asg = json.load(open(os.path.join(HERE, "..", "..", "docs", "live", "assignments.json")))
cur = {}
for a, lst in asg["accounts"].items():
    if a == "graveyard":
        continue
    for st in lst:
        cur.setdefault(st, []).append(asg["labels"].get(a, a))
L = t[NG].copy()
res, rows = {}, []
for r in C.RULES:
    sk = C.rule_skip(r, L.side, L.ref_price, L.risk_ps, L.cex, L.spread_bps)
    K = L[~sk]; Rm = L[sk]
    q = sk.mean()
    # per-day gain vs size-matched random (expected): kept_sum - (1 - q_setup) * all_sum, q per setup
    qs = pd.Series(sk, index=L.index).groupby(L.strategy).transform("mean")
    dd = (L.net_ll * (~sk) - L.net_ll * (1 - qs)).groupby(L.date).sum()
    bd = C.bestday(dd.values, dd.index)  # best-day share of gain
    res[r] = {"skipped_share": float(q), "n_kept": int(len(K)), "avg_all": float(L.net_ll.mean()),
              "avg_kept": float(K.net_ll.mean()), "avg_removed": float(Rm.net_ll.mean()) if len(Rm) else None,
              "avg_kept_real": float(K.net_real.mean()), "avg_removed_real": float(Rm.net_real.mean()) if len(Rm) else None,
              "gain_vs_random_R": float(dd.sum()), "gain_t_day": C.day_t(dd), "gain_best_day_share":
              float(dd.max() / dd.sum()) if dd.sum() > 0 else None, "gain_wo_best_day": float(dd.sum() - dd.max()),
              "short_avg_all": float(L[L.side < 0].net_ll.mean()), "short_avg_kept": float(K[K.side < 0].net_ll.mean())}
    print(r, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in res[r].items()}))
    for st, g in L.groupby("strategy"):
        if st not in cur:
            continue
        m = ~sk[L.strategy.values == st]
        gk = g[m]
        b0 = C.bestday(g.net_ll, g.date); b1 = C.bestday(gk.net_ll, gk.date) if len(gk) else {"wo": np.nan, "share": np.nan}
        rows.append(dict(rule=r, setup=st, account="/".join(cur[st]), side=int(g.side.iloc[0]), n=len(g), n_kept=int(m.sum()),
                         avg=g.net_ll.mean(), avg_kept=gk.net_ll.mean() if len(gk) else np.nan, tot=g.net_ll.sum(),
                         tot_kept=gk.net_ll.sum(), wo_best=b0["wo"], best_share=b0["share"], wo_best_kept=b1["wo"],
                         best_share_kept=b1["share"], avg_real=g.net_real.mean(),
                         avg_real_kept=gk.net_real.mean() if len(gk) else np.nan, sessions=g.date.nunique()))
P = pd.DataFrame(rows)
P["flip"] = (P.avg < 0) & (P.avg_kept > 0) & (P.n != P.n_kept)
P.round(4).to_csv(os.path.join(HERE, "live_setups.csv"), index=False)
json.dump(res, open(os.path.join(HERE, "live_rules.json"), "w"), indent=1, default=float)
for r in C.RULES:
    f = P[(P.rule == r) & P.flip]
    print(f"\n{r} flips (neg -> pos LIVE-L net, non-GY current setups):", len(f))
    print(f[["setup", "account", "n", "n_kept", "avg", "avg_kept", "wo_best_kept", "best_share_kept"]].round(3).to_string())
    a = P[(P.rule == r) & (P.n != P.n_kept)]
    print(r, "touched", len(a), "improve", int((a.avg_kept > a.avg).sum()), "worse", int((a.avg_kept < a.avg).sum()),
          "median d", round(float((a.avg_kept - a.avg).median()), 4))

# ---------------- same replay on the REALISED basis (fills; spread is in it, LIVE-L has no spread term): reported view
rr = {}
for r in C.RULES:
    sk = C.rule_skip(r, L.side, L.ref_price, L.risk_ps, L.cex, L.spread_bps)
    qs = pd.Series(sk, index=L.index).groupby(L.strategy).transform("mean")
    dd = (L.net_real * (~sk) - L.net_real * (1 - qs)).groupby(L.date).sum()
    rr[r] = {"avg_all_real": float(L.net_real.mean()), "avg_kept_real": float(L[~sk].net_real.mean()),
             "gain_vs_random_R": float(dd.sum()), "gain_t_day": C.day_t(dd),
             "gain_best_day_share": float(dd.max() / dd.sum()) if dd.sum() > 0 else None}
    print(r, "REALISED", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rr[r].items()})
json.dump(rr, open(os.path.join(HERE, "live_rules_real.json"), "w"), indent=1, default=float)
