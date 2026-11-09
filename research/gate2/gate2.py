"""GATE2 (guild Builder, plan PLAN.md frozen 2026-11-09 before any score): trade WITH the held side on pullbacks.
  reading  first 5-min bar close 10:30..13:00 with |SPY fo| >= X -> side s, time Tc
  trigger  bars after Tc (closes <= 14:30): own move M = s*(extreme - open) >= 0.25 ATR, retrace >= RET*M, still s-side
  entry    next bar open; stop own open - s*0.10 ATR; skip R < 0.10 ATR; exit E1 15:55 close | E2 BE at +1R, trail 1R from +2R
  sets     I-ETF SPY/QQQ/IWM; I-HB top-500 adv20 x ATR% (adv20 >= $95M) with 60d beta >= 1.2, blackout + index out
  controls C1 random bar after Tc (same instrument/day/side, paired); C2 same-minute random I-HB name (paired)
  sizing   3 configs on bt_lab1104 lists (x1.5 when the reading favours the side, x0.5 otherwise)
Lineage N 123 (GATE1 112 + 11) -> BAR90 2.79. Locked block 2024-11-01..2025-02-28 dropped at every read (asserted).
    python gate2.py > gate2_out.txt        Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
from mcf.research.generator import data as GD
HERE = Path(__file__).resolve().parent
TZ = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
SPLIT = pd.Timestamp("2025-09-30").date(); LIVE0 = pd.Timestamp("2026-10-06").date()
N_LINEAGE = 112 + 11; T_FULL = G.t_required(N_LINEAGE); T90 = round(max(1.35, 0.9 * T_FULL), 2)
IDX = {"SPY", "QQQ", "IWM", "DIA"}; ETF = ["SPY", "QQQ", "IWM"]
SPREAD_BPS = 4.4e-4; RNG = np.random.default_rng(20261109)
END_MIN = 570 + 5 * np.arange(1, 79)                     # bar ends 09:35 .. 16:00 (78 bars)
END_TOD = END_MIN // 60 * 100 + END_MIN % 60
I = {t: i for i, t in enumerate(END_TOD)}
I1030, I1300, I1430, I1555 = I[1030], I[1300], I[1430], I[1555]
GRID = [("I-ETF", .30, .40, "E1"), ("I-ETF", .50, .40, "E1"), ("I-ETF", .30, .60, "E1"), ("I-ETF", .30, .40, "E2"),
        ("I-HB", .30, .40, "E1"), ("I-HB", .50, .40, "E1"), ("I-HB", .30, .60, "E1"), ("I-HB", .30, .40, "E2")]

# ------------------------------------------------------------------ daily: ATR, adv20, beta, U, blackout
Dd = lib.daily()                                          # locked block removed
Dd = Dd.sort_values(["symbol", "date"]).reset_index(drop=True)
assert not ((Dd.date >= LK0) & (Dd.date <= LK1)).any()
pc = Dd.groupby("symbol").close.shift(1)
tr = np.maximum(Dd.high - Dd.low, np.maximum((Dd.high - pc).abs(), (Dd.low - pc).abs()))
Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
Dd["ret"] = Dd.close / pc - 1
SPYD = Dd[Dd.symbol == "SPY"].set_index("date")
Dd["spy_ret"] = Dd.date.map(SPYD.ret)
def _beta(g):
    x, y = g.spy_ret.shift(1), g.ret.shift(1)
    cov = (x * y).rolling(60, min_periods=40).mean() - x.rolling(60, min_periods=40).mean() * y.rolling(60, min_periods=40).mean()
    return cov / x.rolling(60, min_periods=40).var(ddof=0)
Dd["beta"] = Dd.groupby("symbol", group_keys=False).apply(_beta)
Dd["score"] = Dd.adv20 * Dd.atr / pc
cand = Dd[(Dd.adv20 >= 95e6) & (Dd.atr > 0) & ~Dd.symbol.isin(IDX)].copy()
cand["rk"] = cand.groupby("date").score.rank(ascending=False, method="first")
U = cand[cand.rk <= 500].copy()
U["bl"] = GD._blackout(U.symbol.to_numpy(), U.date.to_numpy())
HB = U[(U.beta >= 1.2) & ~U.bl][["symbol", "date", "atr"]]
ETFD = Dd[Dd.symbol.isin(ETF)][["symbol", "date", "atr"]].dropna()
dtype = pd.Series(np.where(SPYD.close / SPYD.open - 1 > .0025, "up", np.where(SPYD.close / SPYD.open - 1 < -.0025, "down", "quiet")),
                  index=SPYD.index)

# ------------------------------------------------------------------ 5-minute bars from the 1-minute cache
CACHE = ROOT / "data/cache_hist/1Min"
def bars(sym, dates):
    p = CACHE / f"{sym}.parquet"
    if not p.exists(): return {}
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= TL0) & (df.index < TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = df.index.hour * 60 + df.index.minute
    df = df[(mm >= 570) & (mm < 960)]; mm = df.index.hour * 60 + df.index.minute
    df = df.assign(_d=df.index.date, _b=(mm - 570) // 5)
    df = df[df._d.isin(dates)]
    out = {}
    g = df.groupby(["_d", "_b"]).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
    for d, gd in g.groupby(level=0):
        a = np.full((78, 4), np.nan, np.float32); a[gd.index.get_level_values(1)] = gd[["o", "h", "l", "c"]].to_numpy()
        if np.isnan(a[0, 0]): continue                     # no 09:30 print -> no reliable open
        c = pd.Series(a[:, 3]).ffill().to_numpy(); miss = np.isnan(a[:, 0])
        a[miss, 0] = a[miss, 1] = a[miss, 2] = c[miss]; a[:, 3] = c
        out[d] = a
    return out

need = pd.concat([HB, ETFD]).groupby("symbol").date.apply(set).to_dict()
PATH = {}
for k, (sym, ds_) in enumerate(need.items()):
    for d, a in bars(sym, ds_).items(): PATH[(sym, d)] = a
    if k % 200 == 0: print(f"bars {k}/{len(need)}", flush=True)
ATR = {(s, d): a for s, d, a in pd.concat([HB, ETFD])[["symbol", "date", "atr"]].itertuples(index=False)}
DATES = sorted(d for (s, d) in PATH if s == "SPY")
print(f"paths {len(PATH)}; SPY sessions {len(DATES)} ({DATES[0]}..{DATES[-1]}, locked absent)", flush=True)

def reading(X):
    """date -> (side, index of the confirming bar)."""
    out = {}
    for d in DATES:
        a = PATH[("SPY", d)]; fo = a[:, 3] / a[0, 0] - 1
        hit = np.flatnonzero(np.abs(fo[I1030:I1300 + 1]) >= X / 100)
        if len(hit): out[d] = (int(np.sign(fo[I1030 + hit[0]])), I1030 + int(hit[0]))
    return out

def trigger(a, s, ic, atr, ret):
    """first trigger bar index after ic (close <= 14:30) or -1."""
    o = a[0, 0]; ext = np.maximum.accumulate(a[:, 1]) if s > 0 else np.minimum.accumulate(a[:, 2])
    M = s * (ext - o); c = a[:, 3]
    ok = (M >= .25 * atr) & (s * (ext - c) >= ret * M) & (s * (c - o) > 0)
    ok[:ic + 1] = False; ok[I1430 + 1:] = False
    h = np.flatnonzero(ok)
    return int(h[0]) if len(h) else -1

def trade(a, s, ib, atr, ex):
    """signal bar ib -> (net R, gross R, kind) with entry at bar ib+1 open; None if R too small / no bar."""
    j = ib + 1
    if j > I1555: return None
    e = float(a[j, 0]); stop0 = a[0, 0] - s * .10 * atr; R = s * (e - stop0)
    if not np.isfinite(e) or R < .10 * atr: return None
    stop = stop0; best = e; kind, xp = "time", float(a[I1555, 3])
    for i in range(j, I1555 + 1):
        o, h, l, c = a[i]
        if i > j and s * (o - stop) <= 0: kind, xp = "stop", float(o); break
        if (s > 0 and l <= stop) or (s < 0 and h >= stop): kind, xp = "stop", float(stop); break
        if ex == "E2":                                       # update on the close, active from the next bar
            best = max(best, c) if s > 0 else min(best, c); run = s * (best - e) / R
            if run >= 2: stop = best - s * R
            elif run >= 1: stop = e if s * (e - stop) > 0 else stop
    mult = G.tod_cost_mult(np.array([END_TOD[ib]]))[0]
    cost = (G.SLIP_PS + e * G.SLIP_BPS) * mult + SPREAD_BPS * e * mult + G.SLIP_PS + e * G.SLIP_BPS + (G.STOP_EXTRA if kind == "stop" else 0)
    g = s * (xp - e) / R
    return g - cost / R, g, kind

rows, ALLT = [], []
NS = len(DATES); NS_TR = sum(d <= SPLIT for d in DATES); NS_VA = NS - NS_TR
print(f"sessions {NS} (train {NS_TR} / valid {NS_VA}); N lineage {N_LINEAGE}: full bar {T_FULL}, BAR90 {T90} (new-lineage-only N 11: {G.t_required(11)})")
HBd = HB.groupby("date").symbol.apply(list).to_dict()
for inst, X, RET, ex in GRID:
    rd = reading(X); T = []
    for d, (s, ic) in rd.items():
        syms = ETF if inst == "I-ETF" else HBd.get(d, [])
        for sym in syms:
            a = PATH.get((sym, d)); atr = ATR.get((sym, d))
            if a is None or not atr or not np.isfinite(atr): continue
            ib = trigger(a, s, ic, atr, RET)
            if ib < 0: continue
            res = trade(a, s, ib, atr, ex)
            if res is None: continue
            # C1: random bar after the reading, same instrument/day/side, still s-side at the signal close
            okb = [b for b in range(ic + 1, I1430 + 1) if s * (a[b, 3] - a[0, 0]) > 0]
            c1 = trade(a, s, int(RNG.choice(okb)), atr, ex) if okb else None
            # C2: same minute, random other I-HB name the same day
            c2 = None
            if inst == "I-HB":
                others = [o for o in syms if o != sym and (o, d) in PATH]
                if others:
                    o = others[int(RNG.integers(len(others)))]; c2 = trade(PATH[(o, d)], s, ib, ATR[(o, d)], ex)
            T.append(dict(date=d, symbol=sym, side=s, tod=int(END_TOD[ib]), r=res[0], gross=res[1], kind=res[2],
                          c1=c1[0] if c1 else np.nan, c2=c2[0] if c2 else np.nan))
    t = pd.DataFrame(T); nm = f"GATE2-{inst}-X{X:.2f}-RET{RET:.2f}-{ex}"
    if not len(t):
        rows.append(dict(config=nm, n=0)); continue
    t["config"] = nm; ALLT.append(t)
    s_ = G.summary(t); tr_, va_ = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT]); lv = G.summary(t[t.date >= LIVE0])
    x1 = G.summary(t.dropna(subset=["c1"]).assign(r=lambda x: x.r - x.c1))
    x2 = G.summary(t.dropna(subset=["c2"]).assign(r=lambda x: x.r - x.c2)) if inst == "I-HB" else {}
    ty = t.groupby(t.date.map(dtype)).r.agg(["mean", "size"])
    mo = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
    gd = t.groupby("date").r.sum(); share = round(gd.max() / gd.sum(), 2) if gd.sum() > 0 else None
    row = dict(config=nm, n=s_["n"], days=s_["days"], per_sess=round(s_["n"] / NS, 2), avg_r=s_["exp_r"], t=s_.get("t"),
               gross=round(t.gross.mean(), 3), wo_best=s_.get("ex_best_day"), best_share=share, worst_day=round(gd.min(), 2),
               train=tr_.get("exp_r"), valid=va_.get("exp_r"), valid_t=va_.get("t"), live_n=lv.get("n", 0), live=lv.get("exp_r"),
               up=round(ty["mean"].get("up", np.nan), 3), down=round(ty["mean"].get("down", np.nan), 3),
               quiet=round(ty["mean"].get("quiet", np.nan), 3), n_up=int(ty["size"].get("up", 0)),
               n_down=int(ty["size"].get("down", 0)), n_quiet=int(ty["size"].get("quiet", 0)),
               wf_pos=round(float((mo > 0).mean()), 2), c1_ex=x1.get("exp_r"), c1_t=x1.get("t"),
               c2_ex=x2.get("exp_r"), c2_t=x2.get("t"), stops=round(float((t.kind == "stop").mean()), 2),
               reading_days=len(rd), long_share=round(float((t.side > 0).mean()), 2))
    row["bar90"] = bool((row["t"] or 0) >= T90 and (row["c1_t"] or 0) >= T90 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0
                        and row["up"] > 0 and row["down"] > 0 and row["wf_pos"] >= .54 and (row["wo_best"] or -1) > 0
                        and (inst == "I-ETF" or row["per_sess"] >= 1.5))
    rows.append(row); print(nm, "done", flush=True)

# ------------------------------------------------------------------ sizing-by-reading (phase 2, bt_lab1104 lists)
BT = ROOT / "research/history2y/data/bt_lab1104"
SZ = [("L3-gap-slope-fromopen-FD", -1, +1), ("ST7-rsi50dn-long-pm-t1s1-FD", +1, -1), ("NM-AR-AM-gapdown-capitulation-long", +1, -1)]
if BT.exists():
    L = pd.concat(pd.read_parquet(p) for p in sorted(BT.glob("sig_*.parquet")))
    L["date"] = pd.to_datetime(L["date"]).dt.date
    assert not ((L.date >= LK0) & (L.date <= LK1)).any()
    rd = reading(.30)
    for setup, side, want in SZ:
        t = L[(L.setup == setup)].copy()
        if not len(t): rows.append(dict(config=f"GATE2-SIZE-{setup}", n=0)); continue
        st = t.date.map(lambda d: rd.get(d, (0, 999))); sgn = st.map(lambda x: x[0]); icx = st.map(lambda x: x[1])
        tix = t.tod.map(lambda x: I.get(int(x), 999))
        fav = (sgn == want) & (icx < tix)                   # reading confirmed on a bar closed before the entry bar
        t["r"] = (np.where(fav, 1.5, .5) - 1) * t.r          # weighted minus unweighted
        s_ = G.summary(t); tr_, va_ = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
        rows.append(dict(config=f"GATE2-SIZE-{setup}", n=s_["n"], avg_r=s_["exp_r"], t=s_.get("t"), train=tr_.get("exp_r"),
                         valid=va_.get("exp_r"), valid_t=va_.get("t"), fav_share=round(float(fav.mean()), 2),
                         bar90=bool((s_.get("t") or 0) >= T90 and (tr_.get("exp_r") or -1) > 0 and (va_.get("exp_r") or -1) > 0)))
else:
    print("bt_lab1104 lists absent: sizing configs NOT scored (still counted in N)")

R = pd.DataFrame(rows); pd.set_option("display.width", 420); pd.set_option("display.max_columns", 60)
print(R.to_string(index=False))
print("\nentry next 5-min bar open (1-min SIP cache); stop own open -0.10 ATR, stop-first, gaps fill at the open; costs production + 4.4bp spread;"
      "\nc1 = excess over a random post-reading bar (same instrument/day/side), c2 = over a same-minute random I-HB name; day type = SPY o-c +-0.25%;"
      "\nsizing rows: avg_r/t are weighted-minus-unweighted per trade.")
print(f"configs 11 (lineage {N_LINEAGE}), BAR90 pass {int(R.bar90.fillna(False).sum())}")
R.to_csv(HERE / "gate2_results.csv", index=False)
if ALLT: pd.concat(ALLT).to_csv(HERE / "gate2_trades.csv", index=False)
print("Educational only - not financial advice.")
