"""GATE2 C1m addendum (Skeptic skeptic-20261109-1915/1916, Lead lead-20261109-1910-2): REPORTING ONLY, no new configs
(N stays 123). Re-uses gate2.py verbatim for data, reading, trigger and trade (exec of its top half), then for the 8
setup configs prints:
  (1) C1's own avg R and gross R (the original random-bar control);
  (2) C1m = a random bar after the reading on the same instrument / day / side, MATCHED to the signal bar on
      distance from the instrument's own open (s*(close-open)/ATR buckets 0-.25/.25-.5/.5-.75/.75-1/1-1.5/1.5+) and on
      the 30-minute entry-time bucket; excess over C1m in R and in ATR units ((net exit - entry)/ATR, cost included);
  (3) the same excesses on held vs failed-hold days (SPY close vs open on the reading's side).
Pass reading fixed by Skeptic before the run: excess over C1m in ATR units t >= 2.79 -> timing real; else GATE2 closed.
    python gate2_c1m.py > gate2_c1m_out.txt          Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
src = (HERE / "gate2.py").read_text()
exec(compile(src[:src.index("rows, ALLT = [], []")], "gate2_top", "exec"))    # data, reading(), trigger(), trade()

RNG2 = np.random.default_rng(20261110)
DB = np.array([0.25, 0.5, 0.75, 1.0, 1.5])


def tb(i): return (int(END_MIN[i]) - 570) // 30


def r_atr(res, a, s, ib, atr):
    """net result in ATR units: net R x R / ATR (R = entry - stop distance)."""
    j = ib + 1; e = float(a[j, 0]); R = s * (e - (a[0, 0] - s * .10 * atr))
    return res[0] * R / atr


rows = []
HBd = HB.groupby("date").symbol.apply(list).to_dict()
for inst, X, RET, ex in GRID:
    rd = reading(X); T = []
    for d, (s, ic) in rd.items():
        held = np.sign(SPYD.close[d] - SPYD.open[d]) == s
        for sym in (ETF if inst == "I-ETF" else HBd.get(d, [])):
            a = PATH.get((sym, d)); atr = ATR.get((sym, d))
            if a is None or not atr or not np.isfinite(atr): continue
            ib = trigger(a, s, ic, atr, RET)
            if ib < 0: continue
            res = trade(a, s, ib, atr, ex)
            if res is None: continue
            o = a[0, 0]; dist = lambda b: np.searchsorted(DB, s * (a[b, 3] - o) / atr)
            okb = [b for b in range(ic + 1, I1430 + 1) if s * (a[b, 3] - o) > 0]
            c1 = None
            if okb:                                                   # original C1 (fresh draw, own seed)
                b1 = int(RNG2.choice(okb)); c1 = trade(a, s, b1, atr, ex); c1b = b1
            mb = [b for b in okb if b != ib and dist(b) == dist(ib) and tb(b) == tb(ib)]
            cm = None
            if mb:
                bm = int(RNG2.choice(mb)); cm = trade(a, s, bm, atr, ex); cmb = bm
            T.append(dict(date=d, held=held, r=res[0], g=res[1], ra=r_atr(res, a, s, ib, atr),
                          c1=c1[0] if c1 else np.nan, c1g=c1[1] if c1 else np.nan,
                          cm=cm[0] if cm else np.nan, cma=r_atr(cm, a, s, cmb, atr) if cm else np.nan))
    t = pd.DataFrame(T); nm = f"GATE2-{inst}-X{X:.2f}-RET{RET:.2f}-{ex}"
    m = t.dropna(subset=["cm"])
    def S(df, col): return G.summary(df.assign(r=df[col])) if len(df) else {}
    xr, xa = S(m.assign(x=m.r - m.cm), "x"), S(m.assign(x=m.ra - m.cma), "x")
    hx, fx = S(m[m.held].assign(x=m.ra - m.cma), "x"), S(m[~m.held].assign(x=m.ra - m.cma), "x")
    c1 = t.dropna(subset=["c1"])
    rows.append(dict(config=nm, n=len(t), avg_r=round(t.r.mean(), 4), c1_avg=round(c1.c1.mean(), 4), c1_gross=round(c1.c1g.mean(), 4),
                     sig_gross=round(t.g.mean(), 4), n_c1m=len(m), c1m_avg=round(m.cm.mean(), 4),
                     ex_c1m_r=xr.get("exp_r"), ex_c1m_r_t=xr.get("t"), ex_c1m_atr=xa.get("exp_r"), ex_c1m_atr_t=xa.get("t"),
                     ex_atr_held=hx.get("exp_r"), ex_atr_held_t=hx.get("t"), ex_atr_failed=fx.get("exp_r"), ex_atr_failed_t=fx.get("t"),
                     timing_real=bool((xa.get("t") or 0) >= T90)))
    print(nm, "done", flush=True)
R = pd.DataFrame(rows); pd.set_option("display.width", 400); pd.set_option("display.max_columns", 40)
print(R.to_string(index=False))
print(f"\nreporting only (N stays {N_LINEAGE}); timing_real = excess over C1m in ATR units, day-clustered t >= {T90}.")
R.to_csv(HERE / "gate2_c1m_results.csv", index=False)
print("Educational only - not financial advice.")
