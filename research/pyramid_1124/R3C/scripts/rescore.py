"""R3C: re-score benchmark, gap-down family and Pyramid finalists with the research (bench10 add_r) and the
live-calibrated cost model (cells.json). Educational only - not financial advice."""
import sys, os, json
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
os.chdir(INBOX)
import bench10 as B
H = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/R3C/"
P = H + "../"
CELLS = json.load(open(H + "cells.json")); CELLS2 = json.load(open(H + "cells2.json"))
sys.path.insert(0, H)
import calib as CB
PBL = ["5-10", "10-20", "20-50", "50-100", "100+"]; TBL = ["<1030", "1030-1200", "1200-1400", ">=1400"]
U = pd.read_csv("/home/user/MCF/data/universe.csv")
ETB_U = pd.Series(np.where(U.easy_to_borrow.astype(str) == "True", 1.0, 0.0), index=U.symbol)
ETB_R = pd.read_parquet(H + "etb_rate.parquet").rate
TEST, PRIM = B.TESTING_RULES, B.BOOK["primary"]

def cal_ps(price, tod, kind, side):
    price = np.asarray(price, float)
    pb = pd.cut(price, [-1e9, 10, 20, 50, 100, 1e12], labels=PBL, right=False).astype(str)
    tb = pd.cut(np.asarray(tod, float), [0, 1030, 1200, 1400, 2400], labels=TBL, right=False).astype(str)
    kd = np.where(kind == 2, "target", np.where(kind == 1, "stop", "market"))
    ek = pd.Series(np.char.add(np.char.add(pb.astype(str), "|"), tb.astype(str)))
    e = ek.map({k: v[0] for k, v in CELLS["entry"].items()}).to_numpy(float)
    e = np.where(np.isnan(e), pd.Series(pb).map(CELLS["entry_pb"]).to_numpy(float), e)
    xk = pd.Series(np.char.add(np.char.add(pb.astype(str), "|"), kd.astype(str)))
    x = xk.map({k: v[0] for k, v in CELLS["exit"].items()}).to_numpy(float)
    xf = np.array([CELLS["exit_pb"].get(a, {}).get(b, np.nan) for a, b in zip(pb, kd)]) if np.isnan(x).any() else x
    x = np.where(np.isnan(x), xf, x)
    return (e + x) * price / 1e4 + np.where(np.asarray(side) < 0, B.BORROW * price, 0.0)

def both(t):
    t = B.add_r(t)
    t["date"] = t.date.astype(str)
    gross = t.side * (t.px - t.entry)
    t["r_res"] = t.r
    t["cost_res"] = t.r_gross - t.r
    t["r_cal"] = (gross - cal_ps(t.entry.to_numpy(), t.tod.to_numpy(), t.kind.to_numpy(), t.side.to_numpy())) / t.risk
    t["cost_cal"] = t.r_gross - t.r_cal
    kd = np.where(t.kind == 2, "target", np.where(t.kind == 1, "stop", "market"))
    t["r_cal2"] = (gross - CB.predict2_ps(CELLS, CELLS2, t.entry.to_numpy(), t.tod.to_numpy(), kd, t.side.to_numpy(), t.risk.to_numpy())) / t.risk
    return t

SPY1 = B.spy_t1()
D1 = [d for d in SPY1.index if d <= "2026-11-04"]; H1 = B.half(pd.Series(D1))
SPY2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); SPY2.index = SPY2.index.astype(str)
SPY2 = SPY2[(SPY2.index >= B.T2_LO) & (SPY2.index <= B.T2_HI)]["type"]
SES = {"fit": [d for d, h in zip(D1, H1) if h == "fit"], "check": [d for d, h in zip(D1, H1) if h == "check"], "T2": list(SPY2.index)}
SPY = {"fit": SPY1, "check": SPY1, "T2": SPY2}

def score_sets(sets, rules, etb):
    """sets: {fit, check, T2} -> raw rows already through both(); returns {model: {half: stats}} + booked frames"""
    out, bk = {}, {}
    for m in ("res", "cal", "cal2"):
        out[m], bk[m] = {}, {}
        for h in ("fit", "check", "T2"):
            x = sets[h]
            if x is None or not len(x): out[m][h] = {"trades": 0}; continue
            b = B.book(x.assign(r=x["r_" + m]), rules, etb)
            s = B.stats(b, len(SES[h]), SPY[h])
            if len(b):
                w, l = b.r[b.r > 0], b.r[b.r <= 0]
                s["be_win"] = round(float(-l.mean() / (w.mean() - l.mean())), 3) if len(w) and len(l) else None
                s["avg_cost"] = round(float((b.r_gross - b.r).mean()), 4)
                s["entry_lt20_share"] = round(float((b.entry < 20).mean()), 3)
                s["med_entry"] = round(float(b.entry.median()), 2)
                s["med_stop_bps"] = round(float((b.risk / b.entry * 1e4).median()), 1)
            out[m][h] = s; bk[m][h] = b
    return out, bk

def split_t1(t1, t2):
    t1 = t1.copy(); t1["half"] = B.half(t1.date)
    return {"fit": t1[t1.half == "fit"], "check": t1[t1.half == "check"], "T2": t2}

# ------------------------------------------------------------------------------------------- candidate registry
def reg():
    R = {}
    l2 = both(pd.read_parquet(P + "L2/work/trades_t1.parquet")), both(pd.read_parquet(P + "L2/work/trades_t2.parquet"))
    hs = both(pd.read_parquet(P + "../hsscale/work/trades_t1.parquet")), both(pd.read_parquet(P + "../hsscale/work/trades_t2.parquet"))
    mw = (both(pd.read_parquet(H + "w/trades_t1.parquet")), both(pd.read_parquet(H + "w/trades_t2.parquet"))) if os.path.exists(H + "w/trades_t2.parquet") else None
    def bs(src, name, alias=None):
        a, b = src
        return split_t1(a[a.setup == name], b[b.setup == name])
    BM = [("L3-fromopen", l2, "L3-gap-slope-fromopen-FD", PRIM), ("RW3-FD", l2, "RW3-gapdn-rsi5pop-flowsell-short-FD", PRIM),
          ("L3-lowdist", hs, "L3-gap-slope-lowdist-FD", TEST), ("RW5-FD", l2, "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", PRIM),
          ("L3-rsi5hi", hs, "L3-gap-slope-rsi5hi-FD", TEST), ("RW6-FD", hs, "RW6-ns2-up3-short-FD", B.BOOK["livelab"]),
          ("NM-RWN4", mw, "NM-RWN4-ns2-spyup05-notfri-short", B.BOOK["testingf"]),
          ("CWT14-orl-WB5", mw, "CWT14-failbrk-orl-p10-long-WB5", B.BOOK["testingd"]),
          ("NM-ETF-late-dip", l2, "C4bench", PRIM), ("CWT09-g10", mw, "CWT09-gapdn-vwaploss-g10-short", TEST)]
    for nm, src, s, rules in BM:
        if src is None: continue
        R[nm] = dict(group="a_top10", sets=bs(src, s), rules=rules, etb=ETB_R)
    R["RW7-FD"] = dict(group="b_gapdown", sets=bs(hs, "RW7-gapdn-bounce-early-short-FD"), rules=TEST, etb=ETB_R)
    # S
    sw = both(pd.read_parquet(P + "S/work/trades_t1.parquet")), both(pd.read_parquet(P + "S/work/trades_t2.parquet"))
    for nm, s in (("S:GEN-261029-06", "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short"),
                  ("S:GEN-261023-06", "GEN-261023-06-RSI7le38-Ret15mge0p54-EMAdiffge0p29-LAM-SPYltm0p25-t1s05-short"),
                  ("S:ST5", "ST5-pdbrkup-short-mid-t05s1-FD")):
        R[nm] = dict(group="c_pyramid", sets=bs(sw, s), rules=TEST, etb=ETB_R)
    # L2
    for s in ("C1a", "C2a", "C3a", "C4a"):
        R["L2:" + s] = dict(group="c_pyramid", sets=bs(l2, s), rules=TEST, etb=ETB_R)
    del l2, hs, mw, sw
    # L1 + G gate
    G = pd.read_parquet(P + "G/gate.parquet")[["date", "T", "TT1"]].drop_duplicates(["date", "T"]).rename(columns={"T": "tod"})
    G["date"] = G.date.astype(str)
    def gate(x): return x.merge(G, on=["date", "tod"], how="left")
    l1 = {k: gate(both(pd.read_parquet(P + f"L1/trades_{k}.parquet"))) for k in ("fit", "check", "t2")}
    def l1s(cfg, geo, kd):
        return {h: l1[f][(l1[f].cfg == cfg) & (l1[f].geo == geo) & (l1[f].kind_ == kd)] for h, f in (("fit", "fit"), ("check", "check"), ("T2", "t2"))}
    for c in ("C1_D1_G2", "C2_S03_G2", "C3_V25_G2"):
        cfg, geo = c.rsplit("_", 1)
        R["L1:" + c] = dict(group="c_pyramid", sets=l1s(cfg, geo, "sig"), rules=TEST, etb=ETB_U)
    def g1(sets): return {h: x[x.TT1.fillna(False).astype(bool)] for h, x in sets.items()}
    R["G:C3+TT1"] = dict(group="c_pyramid", sets=g1(l1s("C3_V25", "G2", "sig")), rules=TEST, etb=ETB_U)
    R["G:NM-ETF+TT1"] = dict(group="c_pyramid", sets=g1(l1s("NM-ETF-late-dip-di-long", "P", "prim")), rules=TEST, etb=ETB_U)
    del l1
    # L3
    a, b = gate(both(pd.read_parquet(P + "L3/work/trades_t1.parquet"))), gate(both(pd.read_parquet(P + "L3/work/trades_t2.parquet")))
    for c in ("A1", "A1t", "A2", "A2t", "A3", "A3t", "B1a", "B2b", "B3a"):
        st = split_t1(a[(a.cfg == c) & (a.ctrl == 0)], b[(b.cfg == c) & (b.ctrl == 0)])
        R["L3:" + c] = dict(group="c_pyramid", sets=st, rules=TEST, etb=pd.Series(1.0, index=pd.concat([a.symbol, b.symbol]).unique()))
    for c, nm in (("A1", "G:A1(GEN-261027-01)+TT1"), ("A3", "G:A3(GEN-261019-02)+TT1"), ("B3a", "G:B3+TT1")):
        st = split_t1(a[(a.cfg == c) & (a.ctrl == 0)], b[(b.cfg == c) & (b.ctrl == 0)])
        R[nm] = dict(group="c_pyramid", sets=g1(st), rules=TEST, etb=ETB_U)
    # E
    e1, e2 = both(pd.read_parquet(P + "E/trades_T1.parquet")), both(pd.read_parquet(P + "E/trades_T2.parquet"))
    for c in ("E1_X3_G2", "E2_G10_G2", "E3_S03_G2"):
        cfg, geo = c.rsplit("_", 1)
        st = split_t1(e1[(e1.cfg == cfg) & (e1.geo == geo) & (e1.kind_ == "sig")], e2[(e2.cfg == cfg) & (e2.geo == geo) & (e2.kind_ == "sig")])
        R["E:" + c] = dict(group="c_pyramid", sets=st, rules=TEST, etb=ETB_U)
    return R

def tier(s):
    f, c, t2 = s["fit"], s["check"], s["T2"]
    g = lambda d, k: d.get(k) if d.get(k) is not None else float("nan")
    A = (g(f, "avg_r") > 0 and g(c, "avg_r") > 0 and g(c, "avg_r_wo_best_day") > 0 and g(t2, "avg_r") > -0.02
         and g(c, "t_day_clustered") >= 1.5 and g(c, "trades_per_session") >= 1.0)
    if A: return "A"
    if g(f, "avg_r") > 0 and g(c, "avg_r") > -0.02: return "B"
    return "FAIL"

if __name__ == "__main__":
    R = reg()
    res = {}
    for nm, d in R.items():
        o, _ = score_sets(d["sets"], d["rules"], d["etb"])
        o["group"] = d["group"]; o["tier_res"] = tier(o["res"]); o["tier_cal"] = tier(o["cal"]); o["tier_cal2"] = tier(o["cal2"])
        res[nm] = o
        f = lambda m, h, k: o[m][h].get(k)
        print(f"{nm:28s} {d['group']:10s} | res fit {f('res','fit','avg_r')} chk {f('res','check','avg_r')} T2 {f('res','T2','avg_r')} [{o['tier_res']}]"
              f" | cal fit {f('cal','fit','avg_r')} chk {f('cal','check','avg_r')} T2 {f('cal','T2','avg_r')} [{o['tier_cal']}] | cal2 fit {f('cal2','fit','avg_r')} chk {f('cal2','check','avg_r')} T2 {f('cal2','T2','avg_r')} [{o['tier_cal2']}]", flush=True)
    json.dump(res, open(H + "rescore.json", "w"), indent=1, default=float)
