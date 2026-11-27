"""R3B step 1: assemble lab trade paths of the pool, costs (research LR8 + LR8-lab), gates, books -> booked.parquet.
Educational only - not financial advice. Locked block never read (asserted)."""
import sys
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import bench10 as B
P = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/"
HS = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/hsscale/work/"
COLS = ["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind", "xt"]
G29 = "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short"
G23 = "GEN-261023-06-RSI7le38-Ret15mge0p54-EMAdiffge0p29-LAM-SPYltm0p25-t1s05-short"
SRC = {  # short name -> (file stem, selector)
    "L3-fromopen": ("L2", "L3-gap-slope-fromopen-FD"), "RW3": ("L2", "RW3-gapdn-rsi5pop-flowsell-short-FD"),
    "RW5": ("L2", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"), "L3-lowdist": ("HS", "L3-gap-slope-lowdist-FD"),
    "L3-rsi5hi": ("HS", "L3-gap-slope-rsi5hi-FD"), "RW6": ("HS", "RW6-ns2-up3-short-FD"),
    "GEN-261029-06": ("S", G29), "GEN-261023-06": ("S", G23),
    "CWT09": ("R3B", "CWT09-gapdn-vwaploss-g10-short"), "CWT14": ("R3B", "CWT14-failbrk-orl-p10-long-WB5"),
    "NM-RWN4": ("R3B", "NM-RWN4-ns2-spyup05-notfri-short"), "NM-ETF": ("R3B", "NM-ETF-late-dip-di-long"),
    "B3": ("L3", "B3a"), "GEN-261019-02": ("L3", "A3"), "GEN-261027-01": ("L3", "A1"),
}
FILES = {"L2": P + "L2/work/trades_{}.parquet", "HS": HS + "trades_{}.parquet", "S": P + "S/work/trades_{}.parquet",
         "R3B": P + "R3B/work/trades_{}.parquet", "L3": P + "L3/work/trades_{}.parquet"}
HOME = {"L3-fromopen": "primary", "RW3": "primary", "RW5": "primary", "NM-ETF": "primary", "L3-lowdist": "testing",
        "L3-rsi5hi": "testing", "CWT09": "testing", "RW6": "livelab", "NM-RWN4": "testingf", "CWT14": "testingd"}
TOP10 = list(HOME)
LONGS = ["NM-ETF", "CWT14", "B3", "GEN-261019-02", "GEN-261027-01"]

def load(name, t):
    src, sel = SRC[name]
    d = pd.read_parquet(FILES[src].format(t))
    d = d[(d.cfg == sel) & (d.ctrl == 0)] if src == "L3" else d[d.setup == sel]
    d = d[COLS].copy(); d["setup"] = name; return d

def lr8lab(t):
    e = 1e-4 * t.entry
    x = np.where(t.kind == 1, np.maximum(0.02, 4e-4 * t.px), np.where(t.kind == 2, 0.0, np.maximum(0.01, 1e-4 * t.px)))
    borrow = np.where(t.side < 0, B.BORROW * t.entry, 0.0)
    return (t.side * (t.px - t.entry) - e - x - borrow) / t.risk

def main():
    etb = pd.read_parquet(P + "S/etb_rate.parquet").rate
    tt = pd.read_parquet(P + "G/gate.parquet")[["date", "T", "TT1", "src"]]
    so = pd.read_parquet(P + "R3B/spyopen.parquet")[["date", "T", "spyopen", "src"]]
    gate = tt[tt.src != "live"].drop(columns="src").merge(so[so.src != "LIVE"].drop(columns="src"), on=["date", "T"],
                                                          how="outer").drop_duplicates(["date", "T"])
    out = []
    for name in SRC:
        for t, lab in (("t1", None), ("t2", "T2")):
            d = load(name, t); d["date"] = d.date.astype(str)
            d = B.add_r(d)
            d["r8"] = lr8lab(d)
            d["half"] = B.half(d.date) if lab is None else "T2"
            d = d[d.half != "none"]
            B.no_locked(d.date.unique())
            d = d.merge(gate.rename(columns={"T": "tod"}), on=["date", "tod"], how="left")
            variants = [("", None)]
            if name in LONGS:
                variants = [("", None), ("+TT1", "TT1"), ("+SPYOPEN", "spyopen")]
            for suf, g in variants:
                x = d if g is None else d[d[g].fillna(False).astype(bool)]
                bk = B.book(x, B.TESTING_RULES, etb).assign(var=name + suf, base=name, gate=g or "", rules="testing")
                out.append(bk)
                if name in HOME and suf == "":
                    bh = B.book(x, B.BOOK[HOME[name]], etb).assign(var=name + "@home", base=name, gate="", rules=HOME[name])
                    out.append(bh)
    keep = ["var", "base", "gate", "rules", "symbol", "date", "tod", "side", "entry", "risk", "px", "kind", "em", "xm",
            "r", "r_gross", "r8", "half"]
    T = pd.concat(out, ignore_index=True)[keep]
    T.to_parquet(P + "R3B/booked.parquet")
    s = T.groupby(["var", "half"]).r.agg(["size", "mean"]).unstack()
    print(s.round(3).to_string())

if __name__ == "__main__":
    main()
