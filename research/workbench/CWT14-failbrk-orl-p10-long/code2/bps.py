from exits3 import *
def bps(t, sk, rf=0.30):
    R0 = rf * t.atr_d; fill = t.close + t.A_drift * R0 if "A_drift" in t else t.close
    return t.R * (fill - (t.close - sk * R0)) / fill * 1e4
P2 = P.assign(R=P.base_r)
P2["bp"] = P2.R * (P2.base_risk) * 1e4   # base_risk = risk/fill
out = []
for nm, t, sk in [("parent", P2, None), ("WB4", trades(c3, exitc="A"), 1.0), ("K-b S12", trades(c3, **base, exitc="S12"), 1.2),
                  ("C1+G3+S15", trades(c3, **base, exitc="S15"), 1.5), ("C1+G3+S20", trades(c3, **base, exitc="S20"), 2.0),
                  ("C1+G3 S10", trades(c3, **base, exitc="A"), 1.0), ("WB4+S20", trades(c3, exitc="S20"), 2.0)]:
    if sk: t = t.assign(bp=bps(t, sk))
    for tn in ("replay", "2y", "train", "valid"):
        x = period(t, TESTS[tn]); out.append(dict(cfg=nm, test=tn, n=len(x), avgR=x.R.mean(), bps=x.bp.mean(), day_bps_sum=x.groupby("date").bp.sum().mean()))
print(pd.DataFrame(out).round(3).pivot(index="cfg", columns="test", values=["avgR", "bps"]).to_string())
