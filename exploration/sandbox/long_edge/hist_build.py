"""HIST-MOM build: does PRIOR-DAY / 5-DAY STRENGTH lift generic intraday longs in history (feature check, not a setup)?
Generic long at fixed times 10:30 / 12:00 / 13:30 (open of that bar), GEN geometry: stop = entry - 0.25 x ATR14 (daily,
from RTH bars), trail 1R once +1R (holdtr), flat at the 15:55 bar close (last bar on half days). Eligible: adv20 >= $20M,
price >= $5, ATR14 + 5 prior sessions present (reset at > 7-day holes). Locked block 2024-11-01..2025-02-28 never read
(pyarrow filter + assert, upday_1127 loader). Usage: python hist_build.py <scratch>. Educational only - not financial advice."""
import sys, os
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wtx_long_edge/research/upday_1127")
from up_build import load, walk, daily, SRC, no_locked  # noqa: E402
OUTD = sys.argv[1]; TIMES = {60: "10:30", 150: "12:00", 240: "13:30"}

def work(args):
    tag, sym = args
    try:
        b = load(SRC[tag] / f"{sym}.parquet")
    except Exception:
        return None
    if len(b) < 2000:
        return None
    D = daily(b)
    g5 = D.groupby("seg").c
    D["prev_ret"] = D.pc / g5.shift(2) - 1
    D["ret5"] = D.pc / g5.shift(6) - 1
    dates = b.index.date.astype(str); mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    o, h, l, c = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    starts = np.r_[0, np.flatnonzero(dates[1:] != dates[:-1]) + 1]; ends = np.r_[starts[1:], len(b)]
    rows = []
    for s, e in zip(starts, ends):
        d = dates[s]
        if d not in D.index: continue
        r = D.loc[d]
        if not (r.adv20 >= 2e7) or not np.isfinite(r.atr) or not np.isfinite(r.ret5) or not np.isfinite(r.prev_ret): continue
        m = mm[s:e]
        last = np.flatnonzero(m <= 385)
        if len(last) == 0: continue
        ie = s + last[-1]
        for tm, lab in TIMES.items():
            k = np.flatnonzero(m == tm)
            if len(k) == 0 or s + k[0] >= ie: continue
            i0 = s + k[0]; ent = o[i0]
            if ent < 5: continue
            risk = 0.25 * r.atr
            if risk <= 0.001 * ent: continue
            px, kind = walk(o, h, l, c, i0, ie, ent - risk, True)
            rows.append((tag, d, sym, lab, ent, risk, (px - ent) / risk, kind, r.prev_ret * 100, r.ret5 * 100,
                         r.atr / r.pc * 100, (o[s] / r.pc - 1) * 100, (ent / o[s] - 1) * 100))
    if not rows: return None
    x = pd.DataFrame(rows, columns=["src", "date", "sym", "t", "entry", "risk", "gross_r", "stopped", "prev_ret", "ret5",
                                    "atr_pct", "gap", "from_open"])
    no_locked(x.date.unique())
    return x

if __name__ == "__main__":
    jobs = [("t1", f[:-8]) for f in sorted(os.listdir(SRC["t1"])) if f.endswith(".parquet")]
    jobs += [("t2", f[:-8]) for f in sorted(os.listdir(SRC["t2"])) if f.endswith(".parquet")]
    out = []
    with Pool(max(1, os.cpu_count() - 1)) as p:
        for i, x in enumerate(p.imap_unordered(work, jobs, chunksize=8)):
            if x is not None: out.append(x)
            if i % 300 == 0: print(i, len(jobs), flush=True)
    X = pd.concat(out, ignore_index=True)
    for col in ["prev_ret", "ret5", "atr_pct", "gap", "from_open", "gross_r", "risk", "entry"]:
        X[col] = X[col].astype("float32")
    X.to_parquet(f"{OUTD}/hist.parquet"); print(len(X), X.date.min(), X.date.max())
