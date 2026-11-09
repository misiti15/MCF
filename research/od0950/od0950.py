"""OD0950 (guild Builder; definition pre-declared on the board builder-20261109-0820-3, 2026-11-09 08:20 ET, before any
score): is the 09:35-start opening move still worth joining at 09:50?
 (A) Move Hunt movers: tradable 09:35-decision movers in research/bdi/moves/moves.csv that are lab symbols: move left
     from the 09:50 close to the best price by the recorded extreme / by 15:55 (daily ATR units), adverse excursion
     before it.
 (B) 2-year control: every lab symbol-day, z = (09:50 close - open) / ATR; side = sign(z); deciles of |z|. Entry at the
     09:50 minute open (next bar), stop 0.5 ATR (= 1R), exits 11:30 close (X1130) and 15:55 close (X1555); production
     costs (1c + 1bp x tod mult + 4.4bp spread x mult on entry; exit 1c + 1bp; stop +2c; 3x tier for price < $5).
 Kill line: movers < 0.8 ATR left (median) OR the control's net R <= 0 in the movers' deciles. 2 control configs.
Locked block 2024-11-01..2025-02-28 dropped at read (asserted). Educational only - not financial advice.
    python od0950.py > od0950_out.txt"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
HERE = Path(__file__).resolve().parent
TZ = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
SPLIT = pd.Timestamp("2025-09-30").date(); SPREAD = 4.4e-4
SYMS = (ROOT / "research/lab_symbols.txt").read_text().split()
if os.environ.get("OD_SMOKE"): SYMS = SYMS[:int(os.environ["OD_SMOKE"])]   # smoke test only
MV = pd.read_csv(ROOT / "research/bdi/moves/moves.csv")
MV = MV[(MV.set == "tradable") & (MV.decision == "09:35")].copy()
MV["date"] = pd.to_datetime(MV.date).dt.date
mvkeys = {(s, d): (side, ext) for s, d, side, ext in zip(MV.symbol, MV.date, MV.side, MV.extreme)}

def hm(t): return int(t[:2]) * 60 + int(t[3:5])

rows, mov = [], []
for k, sym in enumerate(SYMS):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): continue
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= TL0) & (df.index < TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); df = df[(mm >= 570) & (mm < 960)]
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); d_ = df.index.date
    g = df.groupby(d_)
    day = pd.DataFrame({"o": g.open.first(), "h": g.high.max(), "l": g.low.min(), "c": g.close.last()})
    day.index = pd.Index(day.index)
    pc = day.c.shift(1); gap = pd.Series(pd.to_datetime(day.index)).diff().dt.days.to_numpy() > 5
    pc[gap] = np.nan
    tr = np.maximum(day.h - day.l, np.maximum((day.h - pc).abs(), (day.l - pc).abs()))
    atr = tr.shift(1).rolling(14, min_periods=10).mean()
    O, H, L, C = (df[c].to_numpy(float) for c in ("open", "high", "low", "close"))
    starts = np.r_[0, np.flatnonzero(d_[1:] != d_[:-1]) + 1]; ends = np.r_[starts[1:], len(d_)]
    for a, b in zip(starts, ends):
        d = d_[a]; A = atr.get(d, np.nan)
        if not np.isfinite(A) or A <= 0 or mm[a] != 570: continue
        m = mm[a:b]; i950 = np.searchsorted(m, 590)          # first minute at/after 09:50 = entry minute
        if i950 >= len(m) or m[i950] > 595 or i950 == 0: continue
        o, c0 = O[a], C[a + i950 - 1]; z = (c0 - o) / A; s = 1 if z > 0 else -1 if z < 0 else 0
        if s == 0: continue
        e = O[a + i950]; R = 0.5 * A; stop = e - s * R
        hh, ll, cc, oo = H[a + i950:b], L[a + i950:b], C[a + i950:b], O[a + i950:b]; mx = m[i950:]
        res = {}
        for name, xm in (("X1130", 690), ("X1555", 955)):
            j = np.searchsorted(mx, xm, side="right") - 1
            if j < 0: continue
            hit = np.where(s > 0, ll[:j + 1] <= stop, hh[:j + 1] >= stop)
            if hit.any():
                q = int(np.argmax(hit)); xp = oo[q] if (q > 0 and s * (oo[q] - stop) <= 0) else stop; kind = 1
            else:
                xp = cc[j]; kind = 0
            tier = 3.0 if e < 5 else 1.0; mult = float(G.tod_cost_mult(np.array([950]))[0])
            cost = tier * ((G.SLIP_PS + e * G.SLIP_BPS) * mult + SPREAD * e * mult + G.SLIP_PS + xp * G.SLIP_BPS + (G.STOP_EXTRA if kind else 0))
            res[name] = s * (xp - e) / R - cost / R
        rows.append((sym, d, s, z, res.get("X1130", np.nan), res.get("X1555", np.nan)))
        if (sym, d) in mvkeys:
            side, ext = mvkeys[(sym, d)]; sm = 1 if side == "long" else -1
            je = np.searchsorted(mx, hm(ext), side="right") - 1
            fav = lambda j: (np.max(hh[:j + 1]) - c0) if sm > 0 else (c0 - np.min(ll[:j + 1]))
            if je >= 0:
                k_ = int(np.argmax(hh[:je + 1]) if sm > 0 else np.argmin(ll[:je + 1]))
                adv = (c0 - np.min(ll[:k_ + 1])) if sm > 0 else (np.max(hh[:k_ + 1]) - c0)
                mov.append(dict(symbol=sym, date=d, side=side, z=round(z, 2), same_side=bool(sm == s), left_to_ext=fav(je) / A,
                                left_to_1555=fav(len(mx) - 1) / A, adverse_before=adv / A, ext=ext))
    if k % 200 == 0: print(f"{k}/{len(SYMS)}", flush=True)

T = pd.DataFrame(rows, columns=["symbol", "date", "side", "z", "X1130", "X1555"])
T["absz"] = T.z.abs(); T["dec"] = pd.qcut(T.absz, 10, labels=False)
cuts = T.groupby("dec").absz.agg(["min", "max"]).round(3)
M = pd.DataFrame(mov)
print(f"control symbol-days {len(T)} ({T.date.min()}..{T.date.max()}, locked absent); movers matched {len(M)} of {len(MV)} "
      f"(non-lab symbols missing: {len(MV) - len(M)})")
if len(M):
    M["dec"] = np.searchsorted(cuts["max"].to_numpy()[:-1], M.z.abs().to_numpy(), side="left")
    print("\n(A) movers from 09:50 (ATR units):")
    print(M[["left_to_ext", "left_to_1555", "adverse_before"]].describe(percentiles=[.25, .5, .75]).round(2).to_string())
    print(f"movers whose 09:50 z already points the mover's way: {M.same_side.mean():.0%}; decile counts {M.dec.value_counts().sort_index().to_dict()}")
print("\n(B) control by |z| decile (net R, stop 0.5 ATR = 1R; t day-clustered):")
out = []
for dec, g in T.groupby("dec"):
    for x in ("X1130", "X1555"):
        s_ = G.summary(g.assign(r=g[x]).dropna(subset=["r"])); tr_ = G.summary(g[g.date <= SPLIT].assign(r=g[x]).dropna(subset=["r"]))
        va_ = G.summary(g[g.date > SPLIT].assign(r=g[x]).dropna(subset=["r"]))
        out.append(dict(dec=dec, absz_lo=cuts.loc[dec, "min"], absz_hi=cuts.loc[dec, "max"], exit=x, n=s_["n"], avg_r=s_["exp_r"], t=s_.get("t"),
                        wo_best=s_.get("ex_best_day"), train=tr_.get("exp_r"), valid=va_.get("exp_r"),
                        long=round(g[g.side > 0][x].mean(), 4), short=round(g[g.side < 0][x].mean(), 4)))
O_ = pd.DataFrame(out); print(O_.to_string(index=False))
if len(M):
    md = sorted(M.dec.unique()); w = M.dec.value_counts(normalize=True)
    for x in ("X1130", "X1555"):
        sub = O_[(O_.exit == x) & O_.dec.isin(md)]
        print(f"control net R in the movers' deciles, weighted by mover share ({x}): {float((sub.set_index('dec').avg_r * w).sum()):+.4f}")
    print(f"KILL LINE: median left_to_ext {M.left_to_ext.median():.2f} ATR (needs >= 0.8) and control net R above (needs > 0)")
O_.to_csv(HERE / "od0950_control.csv", index=False); M.to_csv(HERE / "od0950_movers.csv", index=False)
print("configs: 2 control exits (X1130, X1555); descriptive measurement, not a setup. Educational only - not financial advice.")
