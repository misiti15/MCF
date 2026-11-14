"""MOMSIDE scorer (PLAN.md frozen 2026-11-14 before any score). Steps:
  python momside.py --selftest            synthetic: planted aligned effect recovered, null ~0 (reads no real outcome)
  python momside.py --fetch               daily closes 2023-09-01..2026-11-13 (after 16:05 ET / weekends only)
  python momside.py --score               the ONE score (refuses unless PLAN.md is committed)
Educational only - not financial advice."""
import os, subprocess, sys, time
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; R = HERE.parent; ROOT = Path("/home/user/MCF")
DATA = HERE / "data"; TR_END, VA_END = "2025-09-30", "2026-10-07"; LB0, LB1 = "2024-11-01", "2025-02-28"
CFG = {"C1": (3, 8, False, 252), "C2": (2, 9, False, 252), "C3": (3, 8, True, 252), "C4": (3, 8, False, 126)}
# (low decile max, high decile min, longs only, lookback sessions: 252 = 12-1, 126 = 6-1 [Amendment 1])


def momentum(px: pd.DataFrame, dates, lb: int = 252) -> pd.DataFrame:
    """px: index = session dates (str, sorted), columns = symbols, values = close. Returns (date x symbol) decile table
    for each trade date: 12-1 from sessions strictly before D, NaN if the window touches the locked block or < 253 prior."""
    sess = np.array(px.index); out = {}
    blk = (sess >= LB0) & (sess <= LB1)
    for D in dates:
        i = int(np.searchsorted(sess, D, side="left"))          # sessions strictly before D: sess[:i]
        if i - lb < 0:
            continue
        lo, hi = i - lb, i - 1                                   # window [D_-lb, D_-1]
        assert lo >= 0
        if blk[lo:hi + 1].any():
            continue
        m = px.iloc[i - 21] / px.iloc[i - lb] - 1
        m = m.dropna()
        if len(m) < 50:
            continue
        out[D] = np.ceil(m.rank(method="first") / len(m) * 10).clip(1, 10)
    return pd.DataFrame(out).T


def tag(B, dec, cfg):
    lo, hi, longs_only, _lb = CFG[cfg]
    d = np.array([dec.at[x, s] if (x in dec.index and s in dec.columns) else np.nan for x, s in zip(B.date, B.symbol)], float)
    side = B.side.to_numpy()
    counter = ((side > 0) & (d <= lo)) | (((side < 0) & (d >= hi)) if not longs_only else False)
    return counter & np.isfinite(d), np.isfinite(d)


def score(B, skip, col):
    """REGSW-2 score_one: excess of skipping `skip` vs a same-count random skip within setup-day, per day."""
    Rv = B[col].to_numpy(float); sd = (B.setup + "|" + B.date).to_numpy()
    k = pd.Series(skip.astype(float)).groupby(sd).transform("sum").to_numpy()
    n = pd.Series(1.0, index=range(len(B))).groupby(sd).transform("sum").to_numpy()
    tot = pd.Series(Rv).groupby(sd).transform("sum").to_numpy()
    delta = -Rv * skip; ctrl = -(k / n) * tot / np.where(k > 0, k, 1) * skip
    days = sorted(B.date.unique())
    ex = pd.Series(delta - ctrl).groupby(B.date.to_numpy()).sum().reindex(days, fill_value=0.0)
    t = ex.mean() / (ex.std(ddof=1) / np.sqrt(len(ex))) if len(ex) > 2 and ex.std() > 0 else np.nan
    return dict(excess=ex.sum(), t=t, wo_best=ex.sum() - ex.max(), best_share=ex.max() / ex.sum() if ex.sum() > 0 else np.nan,
                skip_share=skip.mean(), skipped_avg=Rv[skip].mean() if skip.any() else np.nan, kept_avg=Rv[~skip].mean())


def selftest():
    rng = np.random.default_rng(1); rows = []
    syms = [f"S{i}" for i in range(300)]; dates = [f"2026-0{m}-{d:02d}" for m in (3, 4, 5) for d in range(1, 29)]
    dec = pd.DataFrame(rng.integers(1, 11, (len(dates), len(syms))), index=dates, columns=syms).astype(float)
    for planted in (0.30, 0.0):
        rows = []
        for D in dates:
            for st in ("A", "B", "C"):
                for _ in range(20):
                    s = syms[rng.integers(300)]; side = 1 if rng.random() < .5 else -1; dd = dec.at[D, s]
                    al = (side > 0 and dd >= 8) or (side < 0 and dd <= 3); co = (side > 0 and dd <= 3) or (side < 0 and dd >= 8)
                    r = rng.normal(-0.05, 1) + (planted if al else -planted if co else 0)
                    rows.append(dict(setup=st, date=D, symbol=s, side=side, gross=r))
        B = pd.DataFrame(rows); skip, _ = tag(B, dec, "C1"); res = score(B, skip, "gross")
        print(f"selftest planted {planted}: excess {res['excess']:+.1f} t {res['t']:+.2f} skip share {res['skip_share']:.2f}")
        assert (res["t"] > 5) if planted else (abs(res["t"]) < 3)
    # point-in-time + locked restart unit check
    sess = [str(d.date()) for d in pd.bdate_range("2023-09-01", "2026-06-30")]
    px = pd.DataFrame({"X": np.arange(len(sess), dtype=float) + 100}, index=sess)
    dq = momentum(pd.concat([px] + [px.rename(columns={"X": f"Y{i}"}) * (1 + i / 100) for i in range(60)], axis=1),
                  ["2024-10-15", "2025-06-02", "2026-03-02", "2026-06-01"])
    print("selftest dates with a decile (2025-06-02 must be absent: its window touches the block; 2026-03-02's window starts after it):", list(dq.index))
    assert "2025-06-02" not in dq.index and "2024-10-15" in dq.index and "2026-06-01" in dq.index
    d6 = momentum(pd.concat([px] + [px.rename(columns={"X": f"Y{i}"}) * (1 + i / 100) for i in range(60)], axis=1),
                  ["2025-06-02", "2025-09-15", "2026-03-02"], lb=126)
    print("selftest 6-1 dates (2025-06-02 absent: touches the block; 2025-09-15 present):", list(d6.index))
    assert "2025-06-02" not in d6.index and "2025-09-15" in d6.index
    print("selftest ok. Educational only - not financial advice.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    if "--score" in sys.argv:
        st = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "PLAN.md"], capture_output=True, text=True).stdout
        assert not st.strip(), "PLAN.md must be committed before the score"
        sys.exit("score step: implemented in the scoring run (fetch first)")
    if "--fetch" in sys.argv:
        sys.exit("fetch step: implemented in the scoring run")
