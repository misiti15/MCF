"""Check: the DEPLOYED WB4 module mask (+ spy_exit_pct) reproduces the UPDAY bench config (RW3 SW1 / RW5 W-Y4).
Run inside the bench dir: python verify_wb4.py rw3|rw5 <module path>. Educational only - not financial advice."""
import sys, importlib.util, numpy as np, pandas as pd
sys.path.insert(0, ".")
setup, mod_path = sys.argv[1], sys.argv[2]
import uplayer as U, load as L
if setup == "rw5":
    import sim2 as S, sim as BK; book = BK.book; import declup as D
    BENCH = D.ROUND2["W-Y4 WB3 + exit if SPY +0.40% since entry"] if "W-Y4 WB3 + exit if SPY +0.40% since entry" in D.ROUND2 else D.ROUND1["W-Y4 WB3 + exit if SPY +0.40% since entry"]
    DEP = dict(D.BASE, w=(1015, 1500), spyx=0.40)            # module carries cost/R + SPY gate; config window + spy_exit_pct
else:
    import sim_rw3 as S; book = S.book; import declup as D
    BENCH = D.ROUND2["SW1 WB3 gate swapped for WB5 recipe (Y1 + U15 end 12:00)"]
    DEP = dict(D.BASE, w=(1030, 1500), spyx=0.30)            # module carries ATR>=1.6% + up-day gate; config window + spy_exit_pct
spec = importlib.util.spec_from_file_location("m", mod_path); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
S1 = pd.read_parquet("spy1m_all.parquet"); S1.index = pd.DatetimeIndex(S1.index).tz_convert("America/New_York")
SPY, SPYC = U.spy_tables(S1)

def masked(c):
    """Apply the live module mask: spy_fo := SPY % since 09:50 with a 09:50 anchor row (spy_fo 0) per symbol-day."""
    c = c.copy(); c["spy_fo"] = c["spy950"]; c["_real"] = True
    anc = c[["symbol", "date"]].drop_duplicates().assign(tod=950, spy_fo=0.0, _real=False)
    for k in ("heat", "buyPressure", "rsi5", "gap", "rsi", "close", "atr_d"):
        anc[k] = 0.0 if k not in ("close", "atr_d") else 1.0
    x = pd.concat([c, anc], ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    m = M.mask(x)
    keep = x[np.asarray(m, bool) & x._real.to_numpy()]
    return keep.drop(columns=["spy_fo", "_real"])

CAND = {"replay": (U.add_spy(L.RF, SPY).sort_values(["symbol", "date", "tod"]).reset_index(drop=True), L.getA),
        "2y": (U.add_spy(L.C, SPY).sort_values(["symbol", "date", "tod"]).reset_index(drop=True), L.getB)}
for test, (cand, get) in CAND.items():
    b = book(U.trades(cand, BENCH, get, SPYC, S.signals), BENCH)
    d = book(U.trades(masked(cand), DEP, get, SPYC, S.signals), DEP)
    sb, sd = U.stats(b), U.stats(d)
    print(f"{setup} {test}: bench n{sb['trades']} avg {sb['avg']:+.4f} wo {sb['avg_wo_best']:+.4f} wd {sb['worst_day']:+.1f} | "
          f"deployed n{sd['trades']} avg {sd['avg']:+.4f} wo {sd['avg_wo_best']:+.4f} wd {sd['worst_day']:+.1f} | "
          f"d avg {sd['avg'] - sb['avg']:+.4f}  spyx exits {int((d.kind == 'spyx').sum())}")
