"""Final side by side: parent, WB1..WB3, alternates, the sibling's WB5 parts. Educational only - not financial advice."""
import sys; sys.argv = ["x"]; sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/code")
exec(open("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/code/combo.py").read().split("C = {")[0])
reg = regimes(); g05 = lambda s: s.gap <= -0.5
L = {"parent": ({}, "A"), "WB1 stop 0.45 ATR": ({}, "S45"), "WB2 gap<=-0.5%": (dict(extra=g05), "A"),
     "WB3 stop 0.45 + gap<=-0.5% (rec.)": (dict(extra=g05), "S45"),
     "alt WB3 + reclaim>=0.05 ATR": (dict(extra=AND(g05, rc)), "S45"), "alt stop 0.60 + gap<=-0.5%": (dict(extra=g05), "S60"),
     "sibling WB5 parts (cost/R<=0.10, SPY>=-0.20% since 09:50, stop 0.45/target 0.15)": (dict(extra=AND(c10, g20)), "S45T15")}
rows = []
for nm, (kw, ex) in L.items():
    t = pick(s, **kw); t = t.assign(R=t[f"{ex}_r"], bp=bp(t, ex))
    for tn, rng in TESTS.items():
        a = period(t, rng).copy(); st = stats(a, "R"); pp = paired(a, period(P, rng), "R", "A_r")
        a["reg"] = a.date.map(reg.regime); dt = a.groupby("reg").R.mean()
        rows.append(dict(copy=nm, test=tn, **st, avg_win=a.R[a.R > 0].mean(), avg_loss=a.R[a.R <= 0].mean(), bps=a.bp.mean(),
                         d_parent=pp["diff"], t_parent=pp["t"], up=dt.get("up"), flat=dt.get("flat"), down=dt.get("down")))
D = pd.DataFrame(rows); D.to_csv(OUT + "final.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 40)
for tn in TESTS:
    print("=====", tn); print(D[D.test == tn].drop(columns="test").round(3).to_string(index=False))
