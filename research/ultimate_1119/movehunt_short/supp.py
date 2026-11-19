"""movehunt_short supplementary pass (pre-declared after the first-pass g1-g4 result, FIT HALF ONLY).

Why: in the first pass the fade candidates reach the 1R swing target often (swing 40-80%) but lose on the tight
0.25 x prior-day-ATR stop, because extended names carry far more intraday volatility than yesterday's ATR implies.
This pass re-scores the SAME candidate rows (first signal per symbol-day per combo, from build.py tables) plus a random
control sample with stops scaled to TODAY's point-in-time volatility:
  a15 = mean high-low range of the completed 15-minute blocks of the session so far (blocks from 09:30, PIT).
  D15/D30/D45: pure time exit (no stop/target) at the open of minute entry+N; R = net / R0 (R0 = 0.25 x prior dATR).
  G5: stop c + 1.0 a15, target 1x risk, cap 45      G6: stop c + 1.5 a15, target 1x risk, cap 45
  G7: stop above HOD (max(HOD, c) + 0.1 a15), target 1x risk, cap 45      G8: stop c + 1.0 a15, target 2x risk, cap 45
R for G5-G8 = net P/L / planned risk (stop - c) (planned, not fill-based, so tiny-risk fills cannot inflate R).
Costs as build.py (LR8 live model, short side). Locked block and check half are dropped on read.
Educational only - not financial advice.
"""
import glob, os, sys, numpy as np, pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
from build import CACHE, FEE_SEC, TAF, CAT, todmult, m2i, load_grid  # noqa

TMP = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mhs_tmp"
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
ROWS = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mhs_supp_rows.parquet"
COLS = ["date", "sym", "tod", "px", "adv_m", "r0pct", "gap", "ro_atr", "rl_atr", "dh_atr", "min_hod", "vwz", "rsi5", "blow", "ret5", "spy950", "spy30", "g1", "spyfo"]
GEO = ["D15", "D30", "D45", "G5", "G6", "G7", "G8"]


def combos(U):
    fnh = (U.min_hod >= 3) & (U.min_hod <= 30) & (U.dh_atr >= 0.25)
    return {
        "K1 ext: runup_open>=1.5ATR & rsi5>=80": (U.ro_atr >= 1.5) & (U.rsi5 >= 80),
        "K2 vwap: vwz>=2.5 & rsi5>=80": (U.vwz >= 2.5) & (U.rsi5 >= 80),
        "K3 failed new high & runup_lod>=2ATR": fnh & (U.rl_atr >= 2),
        "K4 blow-off lower high & runup_lod>=1.5ATR": (U.blow == 1) & (U.rl_atr >= 1.5),
        "K5 gapdn rsi5pop: gap<=-2 & runup_open>=1 & rsi5>=75": (U.gap <= -2) & (U.ro_atr >= 1) & (U.rsi5 >= 75),
        "K6 K5 & spy950<=+0.15": (U.gap <= -2) & (U.ro_atr >= 1) & (U.rsi5 >= 75) & (U.spy950 <= 0.15),
        "K7 K1 & spy950<=+0.15": (U.ro_atr >= 1.5) & (U.rsi5 >= 80) & (U.spy950 <= 0.15),
        "K8 K2 & ret5<0": (U.vwz >= 2.5) & (U.rsi5 >= 80) & (U.ret5 < 0),
        "K9 no-gap ext: |gap|<1 & runup_open>=2 & vwz>=2": (U.gap.abs() < 1) & (U.ro_atr >= 2) & (U.vwz >= 2),
        "K10 L3-like: gap<=-2.5 & runup_open>=1.5 & 10:15-13:00": (U.gap <= -2.5) & (U.ro_atr >= 1.5) & (U.tod >= 1015) & (U.tod <= 1300),
        "K11 K10 & spy950<=+0.15": (U.gap <= -2.5) & (U.ro_atr >= 1.5) & (U.tod >= 1015) & (U.tod <= 1300) & (U.spy950 <= 0.15),
        "K12 late ext: tod>=14:00 & runup_open>=1.5 & vwz>=2": (U.tod >= 1400) & (U.ro_atr >= 1.5) & (U.vwz >= 2),
        "K13 K1 & ret5<0 & spy30<=+0.1": (U.ro_atr >= 1.5) & (U.rsi5 >= 80) & (U.ret5 < 0) & (U.spy30 <= 0.1),
        "K15 gapup ext: gap>=3 & runup_open>=1 & rsi5>=80": (U.gap >= 3) & (U.ro_atr >= 1) & (U.rsi5 >= 80),
        "K16 gapup failed new high: gap>=3 & fnh": (U.gap >= 3) & fnh,
        "K17 gapup vwap stretch rolling: gap>=3 & vwz>=2 & ret5<0": (U.gap >= 3) & (U.vwz >= 2) & (U.ret5 < 0),
    }


def score_sym(args):
    sym, req = args  # req: DataFrame rows (date, tod) for this symbol
    df = load_grid(sym)
    res = []
    g = {str(d): gg for d, gg in df.groupby(df.index.date)}
    # prior-day ATR recomputed as build.py
    dd = df.groupby(df.index.date)
    dl = pd.DataFrame({"h": dd.high.max(), "l": dd.low.min(), "c": dd.close.last()})
    pc = dl.c.shift(1)
    tr = np.maximum(dl.h - dl.l, np.maximum((dl.h - pc).abs(), (dl.l - pc).abs()))
    atr = tr.shift(1).rolling(14, min_periods=10).mean()
    atr.index = [str(i) for i in atr.index]
    for d, sub in req.groupby("date"):
        gg = g.get(d)
        if gg is None or not np.isfinite(atr.get(d, np.nan)):
            continue
        mi = (gg.index.hour * 60 + gg.index.minute - 570).to_numpy()
        o = np.full(390, np.nan); h = o.copy(); l = o.copy(); c = o.copy()
        o[mi], h[mi], l[mi], c[mi] = gg.open, gg.high, gg.low, gg.close
        c = pd.Series(c).ffill().bfill().to_numpy()
        o = np.where(np.isnan(o), c, o); h = np.where(np.isnan(h), c, h); l = np.where(np.isnan(l), c, l)
        R0 = 0.25 * atr[d]
        lastc = m2i(1555)
        for T in sub.tod.astype(int).unique():
            k = m2i(T) - 1; e = k + 2; ct = c[k]; f = o[e]
            nb = (k + 1) // 15
            a15 = np.mean([h[b * 15:(b + 1) * 15].max() - l[b * 15:(b + 1) * 15].min() for b in range(nb)]) if nb else np.nan
            hod = h[:k + 1].max()
            ce = (0.01 + f * 1e-4) * todmult(T) + f * 1e-4 + FEE_SEC * f + CAT
            row = {"sym": sym, "date": d, "tod": int(T), "a15_R0": a15 / R0}
            for N in (15, 30, 45):
                j = min(e + N, lastc)
                xp = o[j]
                cx = 0.01 + xp * 1e-4 + max(0.01, 1e-4 * xp) + TAF + CAT
                row[f"D{N}"] = (f - xp - ce - cx) / R0
            for gn, stop, tk in (("G5", ct + a15, 1.0), ("G6", ct + 1.5 * a15, 1.0), ("G7", max(hod, ct) + 0.1 * a15, 1.0), ("G8", ct + a15, 2.0)):
                risk = stop - ct
                if not (np.isfinite(risk) and risk > 0):
                    row[gn] = np.nan; continue
                tgt = ct - tk * risk
                endi = min(e + 45, lastc)
                xp, kind = o[endi], "t"
                if f >= stop:
                    xp, kind = f, "s"
                else:
                    for j in range(e, endi):
                        if h[j] >= stop:
                            xp, kind = max(stop, o[j]), "s"; break
                        if l[j] <= tgt:
                            xp, kind = tgt, "w"; break  # conservative: target fill at the limit
                base = 0.01 + xp * 1e-4
                cx = TAF + CAT if kind == "w" else base + (max(0.02, 4e-4 * xp) if kind == "s" else max(0.01, 1e-4 * xp)) + TAF + CAT
                row[gn] = (f - xp - ce - cx) / risk
                row[gn + "w"] = int(kind == "w")
            res.append(row)
    return res


if __name__ == "__main__":
    x = pd.concat([pd.read_parquet(f, columns=COLS) for f in glob.glob(f"{TMP}/*.parquet")], ignore_index=True)
    U = x[(x.adv_m >= 20) & (x.r0pct >= 0.40)].reset_index(drop=True)
    C = combos(U)
    sel = []
    for nm, m in C.items():
        d = U[m].sort_values(["date", "sym", "tod"]).drop_duplicates(["date", "sym"]).copy()
        d["set"] = nm
        sel.append(d)
    ctrl = U.sample(40000, random_state=1119).copy(); ctrl["set"] = "CTRL random U1 bar"
    sel.append(ctrl)
    S = pd.concat(sel, ignore_index=True)
    req = S[["sym", "date", "tod"]].drop_duplicates()
    jobs = [(s, r) for s, r in req.groupby("sym")]
    print("rows", len(S), "unique", len(req), "syms", len(jobs), flush=True)
    out = []
    with Pool(4) as p:
        for i, r in enumerate(p.imap_unordered(score_sym, jobs, chunksize=8)):
            out.extend(r)
            if i % 200 == 0:
                print(i, len(out), flush=True)
    R = pd.DataFrame(out)
    S = S.merge(R, on=["sym", "date", "tod"], how="left")
    S.to_parquet(ROWS, index=False)  # ~13 MB, kept outside the repo
    print("saved", len(S))
