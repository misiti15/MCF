"""ex30/gen2: grammar + beam-search setup generator with a regime-maximin fitness (PLAN.md, committed before this ran).
Harness primitives are an independent pandas implementation (group shifts); the modules use modules/gen2_lib.py (numpy).
Costs: gates.prod_r (production + time-of-day entry), first qualifying bar per symbol-day (= gates.lab_trades).
The rule-19 locked block (2024-11..2025-02) is never loaded (asserted).

    python gen.py <scratch>   -> candidates.csv.gz, results.csv, parity.csv, picks.json here; trades in <scratch>
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(HERE / "modules")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
VALID_END = "2026-09-15"
if os.environ.get("GEN2_SMOKE"):   # debugging only: one month each, outputs discarded (numbers never read)
    TRAIN, VALID = ["2025-06"], ["2026-09"]
for m in TRAIN + VALID:
    assert m not in lib.LOCKED_MONTHS and m in lib.months(), m
ADV = 95e6
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "vwapDistPct", "volumeRatio", "volumeSurge",
        "upper_wick", "lower_wick", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr", "dist_round_atr",
        "fromOpen", "gap", "rsi", "rsi5", "macdPct", "flow3", "flow9prev", "bull_div", "bear_div", "pricePosition",
        "sma20_dist_pct", "sma20_slope_pct", "heat", "buyPressure"] + \
       [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05")]
SIDES, GEOMS = ("long", "short"), ("t1s1", "t05s1", "t1s05")
SG = [(s, g) for s in SIDES for g in GEOMS]
WINS = {"W1": (1000, 1130), "W2": (1130, 1400), "W3": (1000, 1500)}
TRIG = ["vwup", "vwdn", "hod", "lod", "volsurge", "bulldiv", "beardiv", "uwick", "lwick", "rsi5up", "rsi5dn", "macdup",
        "macddn", "flowup", "flowdn", "wide", "inside", "round", "dry"]
CTX = ["fo_up", "fo_dn", "fo_flat", "gap_up", "gap_dn", "gap_flat", "pp_hi", "pp_lo", "d20_hi", "d20_lo", "slope_up",
       "slope_dn", "abv_pdh", "blw_pdl", "inside_pd", "rsi_hi", "rsi_lo", "vr_lo", "vs_hi", "heat_hi", "heat_lo", "bp_hi",
       "bp_lo", "vol_hi", "vol_lo", "vw_up", "vw_dn", "spy_up", "spy_dn", "spy_flat", "br_hi", "br_lo", "br_mid", "rs_up",
       "rs_dn"]
PRIMS = TRIG + CTX
BIT = {p: np.uint64(1) << np.uint64(i) for i, p in enumerate(PRIMS)}
UP_TRIG = {"vwup", "hod", "bulldiv", "lwick", "rsi5up", "macdup", "flowup"}
HARD = {("vwup", "short"), ("vwup", "long"), ("rsi5up", "long"), ("rsi5up", "short"), ("flowdn", "short"),
        ("hod", "short"), ("lod", "long"), ("volsurge", "long"), ("volsurge", "short")}
SOFT = {("vwdn", "long"), ("lod", "short"), ("bulldiv", "short"), ("beardiv", "short"), ("uwick", "long"),
        ("uwick", "short"), ("lwick", "long")}


def excluded(trig, ctxs, side):
    if (trig, side) in HARD:
        return True
    if ("blw_pdl" in ctxs and side == "long") or ("abv_pdh" in ctxs and side == "short"):
        return True
    if "gap_dn" in ctxs and side == "short" and trig in UP_TRIG:
        return True
    return False


# ------------------------------------------------------------------------------------------------ harness primitives (pandas)
def prims(df):
    g = df.groupby(["symbol", "date"], sort=False)
    L = lambda k: g[k].shift(1)  # noqa: E731
    rng = (df.high - df.low) / df.atr_d
    o = df.close / (1 + df.fromOpen / 100)
    fo = (df.close - o) / df.atr_d
    vwa = (df.close - df.close / (1 + df.vwapDistPct / 100)) / df.atr_d
    P = {
        "vwup": (df.vwapDistPct > 0) & (L("vwapDistPct") <= 0), "vwdn": (df.vwapDistPct < 0) & (L("vwapDistPct") >= 0),
        "hod": df.dist_hod_atr <= 0.01, "lod": df.dist_lod_atr <= 0.01, "volsurge": df.volumeSurge >= 2.0,
        "bulldiv": df.bull_div == 1, "beardiv": df.bear_div == 1,
        "uwick": (df.upper_wick >= 0.6) & (rng >= 0.10), "lwick": (df.lower_wick >= 0.6) & (rng >= 0.10),
        "rsi5up": (df.rsi5 >= 30) & (L("rsi5") < 30), "rsi5dn": (df.rsi5 <= 70) & (L("rsi5") > 70),
        "macdup": (df.macdPct > 0) & (L("macdPct") <= 0), "macddn": (df.macdPct < 0) & (L("macdPct") >= 0),
        "flowup": (df.flow3 >= 0.3) & (df.flow9prev <= -0.1), "flowdn": (df.flow3 <= -0.3) & (df.flow9prev >= 0.1),
        "wide": rng >= 0.18, "inside": (df.high <= L("high")) & (df.low >= L("low")),
        "round": df.dist_round_atr <= 0.02, "dry": df.volumeRatio <= 0.3,
        "fo_up": fo >= 0.5, "fo_dn": fo <= -0.5, "fo_flat": fo.abs() <= 0.2,
        "gap_up": df.gap >= 1.0, "gap_dn": df.gap <= -1.0, "gap_flat": df.gap.abs() <= 0.3,
        "pp_hi": df.pricePosition >= 0.85, "pp_lo": df.pricePosition <= 0.15,
        "d20_hi": df.sma20_dist_pct >= 0.8, "d20_lo": df.sma20_dist_pct <= -0.8,
        "slope_up": df.sma20_slope_pct >= 0.3, "slope_dn": df.sma20_slope_pct <= -0.3,
        "abv_pdh": df.dist_pdh_atr < 0, "blw_pdl": df.dist_pdl_atr < 0,
        "inside_pd": (df.dist_pdh_atr > 0) & (df.dist_pdl_atr > 0),
        "rsi_hi": df.rsi >= 70, "rsi_lo": df.rsi <= 30, "vr_lo": df.volumeRatio <= 0.6, "vs_hi": df.volumeSurge >= 1.5,
        "heat_hi": df.heat >= 25, "heat_lo": df.heat <= -25, "bp_hi": df.buyPressure >= 0.3, "bp_lo": df.buyPressure <= -0.3,
        "vol_hi": df.atr_d / df.close >= 0.045, "vol_lo": df.atr_d / df.close <= 0.017,
        "vw_up": vwa >= 0.5, "vw_dn": vwa <= -0.5,
        "spy_up": df.spy_fo >= 0.3, "spy_dn": df.spy_fo <= -0.3, "spy_flat": df.spy_fo.abs() <= 0.15,
        "br_hi": df.breadth >= 0.70, "br_lo": df.breadth <= 0.30, "br_mid": (df.breadth >= 0.42) & (df.breadth <= 0.58),
        "rs_up": df.fromOpen - df.spy_fo >= 1.5, "rs_dn": df.fromOpen - df.spy_fo <= -1.5,
    }
    return {k: v.fillna(False).to_numpy(bool) for k, v in P.items()}


def spy_daytype():
    b = pd.read_parquet(ROOT / "data" / "cache_hist" / "1Min" / "SPY.parquet")
    b.index = pd.to_datetime(b.index).tz_convert("America/New_York")
    b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())]
    gg = b.groupby(b.index.date)
    o2c = (gg.close.last() / gg.open.first() - 1) * 100
    s = pd.Series(np.where(o2c >= 0.25, 0, np.where(o2c <= -0.25, 1, 2)), index=o2c.index)   # 0 up 1 down 2 quiet
    d = pd.Series(s.index.astype(str), index=s.index)
    return s[~((d >= "2024-11-01") & (d <= "2025-02-28"))]


DT = spy_daytype()
DTN = ("up", "down", "quiet")


def load(mo, split):
    df = lib.load_month(mo, columns=COLS, context=True)
    df = df[np.nan_to_num(df.adv20.to_numpy(float)) >= ADV]
    if split == "VALID":
        df = df[df["date"].astype(str) <= VALID_END]
    df = df.reset_index(drop=True)
    return df.astype({c: "float64" for c in COLS[2:] + ["spy_fo", "breadth"]})


def build(months, split, keep_frame=None):
    """Compact arrays: rows in 10:00-15:00 where any trigger fires. Also day-matched control means."""
    parts, ctrl, frame = [], [], None
    sd0 = 0
    for mo in months:
        t0 = time.time()
        df = load(mo, split)
        P = prims(df)
        tod = df.tod.to_numpy(float)
        inw = (tod >= 1000) & (tod <= 1500)
        bits = np.zeros(len(df), np.uint64)
        for p in PRIMS:
            bits[P[p]] |= BIT[p]
        anyt = np.zeros(len(df), bool)
        for t in TRIG:
            anyt |= P[t]
        R = {}
        for s, gm in SG:
            rr = df[f"r_{s}_{gm}"].to_numpy(float)
            ok = np.isfinite(rr) & (df.atr_d.to_numpy(float) > 0)
            r = np.full(len(df), np.nan)
            r[ok] = G.prod_r(rr[ok], df[f"win_{s}_{gm}"].to_numpy(float)[ok], df.close.to_numpy(float)[ok],
                             df.atr_d.to_numpy(float)[ok], gm, tod=tod[ok])
            R[(s, gm)] = r
        dates = pd.to_datetime(df["date"]).dt.date.to_numpy()
        for w, (a, b) in WINS.items():
            wm = (tod >= a) & (tod <= b)
            for s, gm in SG:
                ok = wm & np.isfinite(R[(s, gm)])
                c = pd.Series(R[(s, gm)][ok]).groupby(dates[ok]).mean()
                ctrl.append(pd.DataFrame({"date": c.index, "ctrl": c.values, "side": s, "geom": gm, "win": w}))
        key = df.symbol.astype(str).to_numpy() + "|" + df.date.astype(str).to_numpy()
        sd = np.cumsum(np.r_[True, key[1:] != key[:-1]]) + sd0
        sd0 = sd.max() + 1
        k = inw & anyt
        parts.append(dict(bits=bits[k], sd=sd[k].astype(np.int64), tod=tod[k].astype(np.int16),
                          date=dates[k], sym=df.symbol.to_numpy()[k],
                          **{f"{s}_{gm}": R[(s, gm)][k].astype(np.float32) for s, gm in SG}))
        if keep_frame == mo:
            frame = (df, P)
        print(split, mo, len(df), int(k.sum()), f"{time.time() - t0:.0f}s", flush=True)
        del df, P
    D = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    D["dt"] = pd.Series(D["date"]).map(DT).fillna(-1).astype(np.int8).to_numpy()
    D["sessions"] = len(set(D["date"]))
    D["trig_idx"] = {t: np.flatnonzero((D["bits"] & BIT[t]) != 0) for t in TRIG}
    D["win"] = {w: (D["tod"] >= a) & (D["tod"] <= b) for w, (a, b) in WINS.items()}
    return D, pd.concat(ctrl, ignore_index=True), frame


def first_idx(D, trig, ctxs, side, geom, win):
    sub = D["trig_idx"][trig]
    need = np.uint64(0)
    for c in ctxs:
        need |= BIT[c]
    r = D[f"{side}_{geom}"][sub]
    m = D["win"][win][sub] & np.isfinite(r)
    if need:
        m &= (D["bits"][sub] & need) == need
    ii = sub[m]
    if not len(ii):
        return ii
    s = D["sd"][ii]
    return ii[np.r_[True, s[1:] != s[:-1]]]


def stats(D, ii, side, geom):
    r = D[f"{side}_{geom}"][ii].astype(float)
    dt = D["dt"][ii]
    n = len(r)
    out = {"n": n, "tps": n / D["sessions"], "avg": r.mean() if n else np.nan}
    for k, nm in enumerate(DTN):
        x = r[dt == k]
        out[f"n_{nm}"] = len(x)
        out[f"r_{nm}"] = x.mean() if len(x) else np.nan
    return out


def fitness(st, nconds, pen):
    mins = min(st["r_up"], st["r_down"], st["r_quiet"]) if min(st["n_up"], st["n_down"], st["n_quiet"]) >= 30 else np.nan
    return mins - 0.01 * nconds - pen


def search(D):
    rows, seen = [], set()

    def ev(trig, ctxs, side, geom, win, stage):
        key = (trig, frozenset(ctxs), side, geom, win)
        if key in seen or excluded(trig, ctxs, side):
            return None
        seen.add(key)
        ii = first_idx(D, trig, ctxs, side, geom, win)
        st = stats(D, ii, side, geom)
        pen = 0.02 if (trig, side) in SOFT else 0.0
        f0 = fitness(st, 1 + len(ctxs), pen)
        rows.append(dict(stage=stage, trig=trig, ctx="+".join(sorted(ctxs)), side=side, geom=geom, win=win,
                         F_raw=f0, F=f0 if 1.5 <= st["tps"] <= 25 else np.nan, **st))
        return rows[-1]

    t0 = time.time()
    for trig in TRIG:
        for side, geom in SG:
            for win in WINS:
                ev(trig, (), side, geom, win, "A")
                for c in CTX:
                    ev(trig, (c,), side, geom, win, "A")
    A = pd.DataFrame(rows)
    print("stage A", len(A), f"{time.time() - t0:.0f}s", flush=True)
    beam = A[(A.tps >= 1.5) & A.F_raw.notna()].sort_values("F_raw", ascending=False).head(300)
    for b in beam.itertuples():
        base = tuple(x for x in b.ctx.split("+") if x)
        for c in CTX:
            if c not in base:
                ev(b.trig, base + (c,), b.side, b.geom, b.win, "B")
    C = pd.DataFrame(rows)
    print("stage B", len(C) - len(A), f"{time.time() - t0:.0f}s", flush=True)
    return C


def ctxs_of(row):
    return tuple(x for x in row["ctx"].split("+") if x)


def shortlist(D, C, k=30):
    E = C[C.F.notna()].sort_values("F", ascending=False)
    kept, sets = [], []
    for _, r in E.iterrows():
        ii = first_idx(D, r.trig, ctxs_of(r), r.side, r.geom, r.win)
        s = set(D["sd"][ii].tolist())
        if all(len(s & q) / len(s | q) < 0.30 for q in sets):
            kept.append(r); sets.append(s)
        if len(kept) >= k:
            break
    return pd.DataFrame(kept).reset_index(drop=True)


def trades(D, r, split, ctrl):
    ii = first_idx(D, r["trig"], ctxs_of(r), r["side"], r["geom"], r["win"])
    t = pd.DataFrame({"date": D["date"][ii], "symbol": D["sym"][ii], "tod": D["tod"][ii],
                      "r": D[f"{r['side']}_{r['geom']}"][ii].astype(float), "dt": D["dt"][ii]})
    c = ctrl[(ctrl.side == r["side"]) & (ctrl.geom == r["geom"]) & (ctrl.win == r["win"])][["date", "ctrl"]]
    t = t.merge(c, on="date", how="left")
    t["split"] = split
    return t


def summ(t, pre):
    s = G.summary(t[["date", "r"]])
    ex = t.assign(x=t.r - t.ctrl)
    gx = ex.groupby("date").x.agg(["sum", "size"])
    mu = ex.x.mean()
    se = np.sqrt(((gx["sum"] - gx["size"] * mu) ** 2).sum()) / len(ex)
    g = t.groupby("date").r.sum()
    out = {f"{pre}_n": s["n"], f"{pre}_avg_r": s["exp_r"], f"{pre}_t": s["t"], f"{pre}_ex_best": s["ex_best_day"],
           f"{pre}_best_share": round(g.max() / g.sum(), 2) if g.sum() != 0 else None,
           f"{pre}_vs_rand": round(mu, 4), f"{pre}_vs_rand_t": round(mu / se, 2) if se > 0 else None}
    for k, nm in enumerate(DTN):
        x = t.r[t.dt == k]
        out[f"{pre}_{nm}"] = round(x.mean(), 4) if len(x) else None
        out[f"{pre}_n_{nm}"] = len(x)
    return out


def name_of(i, r):
    c = "-".join(ctxs_of(r)) or "bare"
    return f"G2-{i + 1}-{r['trig']}-{c}-{r['win']}-{r['geom']}-{r['side']}".replace("_", "")


MOD = '''"""{name} - ex30/gen2 grammar-generated setup (BDI 2026-11-03, research/bdi/ex30/gen2).
Rule: {words}
Found by the gen2 beam search (regime-maximin fitness on TRAIN only); see research/bdi/ex30/gen2/NOTES.md.
Needs lab context columns (YAML `context: {ctxcols}`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import gen2_lib as L

SIDE = "{side}"
GEOM = "{geom}"
WINDOW = {window}
CONTEXT = {ctxcols}
RULE = {rule}
LAYERS = {layers}


def mask(df) -> np.ndarray:
    return L.mask_rule(df, RULE, WINDOW)
'''
WORDS = {
    "vwup": "close crosses above session VWAP (previous bar at/below)", "vwdn": "close crosses below session VWAP",
    "hod": "close within 0.01 ATR of the high of day", "lod": "close within 0.01 ATR of the low of day",
    "volsurge": "5-bar volume >= 2x the prior 15-bar mean", "bulldiv": "new 20-bar low with RSI above its 20-bar min + 5",
    "beardiv": "new 20-bar high with RSI below its 20-bar max - 5", "uwick": "upper wick >= 60% of a bar >= 0.10 ATR",
    "lwick": "lower wick >= 60% of a bar >= 0.10 ATR", "rsi5up": "RSI(5) crosses up through 30",
    "rsi5dn": "RSI(5) crosses down through 70", "macdup": "MACD % crosses above 0", "macddn": "MACD % crosses below 0",
    "flowup": "3-bar signed flow >= +0.3 after the prior 9 bars <= -0.1", "flowdn": "3-bar signed flow <= -0.3 after the prior 9 bars >= +0.1",
    "wide": "5-minute bar range >= 0.18 daily ATR", "inside": "inside bar (high <= previous high, low >= previous low)",
    "round": "close within 0.02 ATR of a round number", "dry": "bar volume <= 0.3x its 20-bar mean",
    "fo_up": "up >= 0.5 ATR from today's open", "fo_dn": "down >= 0.5 ATR from today's open", "fo_flat": "within 0.2 ATR of today's open",
    "gap_up": "gap >= +1%", "gap_dn": "gap <= -1%", "gap_flat": "gap within +-0.3%",
    "pp_hi": "close in the top 15% of the 20-bar range", "pp_lo": "close in the bottom 15% of the 20-bar range",
    "d20_hi": ">= 0.8% above the 20-bar SMA", "d20_lo": ">= 0.8% below the 20-bar SMA",
    "slope_up": "20-bar SMA rising >= 0.3% over 5 bars", "slope_dn": "20-bar SMA falling >= 0.3% over 5 bars",
    "abv_pdh": "above the prior-day high", "blw_pdl": "below the prior-day low", "inside_pd": "inside the prior-day range",
    "rsi_hi": "RSI(14) >= 70", "rsi_lo": "RSI(14) <= 30", "vr_lo": "bar volume <= 0.6x its 20-bar mean",
    "vs_hi": "5-bar volume >= 1.5x the prior 15-bar mean", "heat_hi": "heat >= 25", "heat_lo": "heat <= -25",
    "bp_hi": "19-bar buy pressure >= +0.3", "bp_lo": "19-bar buy pressure <= -0.3",
    "vol_hi": "daily ATR >= 4.5% of price", "vol_lo": "daily ATR <= 1.7% of price",
    "vw_up": ">= 0.5 ATR above VWAP", "vw_dn": ">= 0.5 ATR below VWAP",
    "spy_up": "SPY >= +0.3% from its open", "spy_dn": "SPY <= -0.3% from its open", "spy_flat": "SPY within +-0.15% of its open",
    "br_hi": "breadth (share above VWAP) >= 70%", "br_lo": "breadth <= 30%", "br_mid": "breadth 42-58%",
    "rs_up": "stock from open - SPY from open >= +1.5 pts", "rs_dn": "stock from open - SPY from open <= -1.5 pts",
}
CTXCOL = {"spy_up": ["spy_fo"], "spy_dn": ["spy_fo"], "spy_flat": ["spy_fo"], "rs_up": ["spy_fo"], "rs_dn": ["spy_fo"],
          "br_hi": ["breadth"], "br_lo": ["breadth"], "br_mid": ["breadth"]}


def write_module(name, r):
    rule = [r["trig"], *ctxs_of(r)]
    w = WINS[r["win"]]
    cc = sorted({c for p in rule for c in CTXCOL.get(p, [])})
    layers = [WORDS[p] for p in rule] + [f"bar close {w[0] // 100}:{w[0] % 100:02d}-{w[1] // 100}:{w[1] % 100:02d} ET"]
    words = f"{r['side'].upper()} at the bar close when " + "; ".join(WORDS[p] for p in rule) + \
        f"; bar close {w[0]}-{w[1]} ET; exit {r['geom']}"
    (HERE / "modules" / f"{name}.py").write_text(MOD.format(name=name, words=words, side=r["side"], geom=r["geom"],
                                                            window=tuple(w), ctxcols=cc, rule=rule, layers=layers))
    return words


def parity(frame, picks):
    df, P = frame
    tod = df.tod.to_numpy(float)
    adv = np.nan_to_num(df.adv20.to_numpy(float)) >= ADV
    out = {}
    for name, r in picks:
        spec = importlib.util.spec_from_file_location("m" + str(abs(hash(name))), HERE / "modules" / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        w = WINS[r["win"]]
        a = (tod >= w[0]) & (tod <= w[1]) & adv
        for p in [r["trig"], *ctxs_of(r)]:
            a &= P[p]
        b = np.asarray(mod.mask(df), bool) & adv
        out[name] = dict(harness=int(a.sum()), module=int(b.sum()), both=int((a & b).sum()))
    return out


def main():
    t0 = time.time()
    DTR, CTR, _ = build(TRAIN, "TRAIN")
    NTR = DTR["sessions"]
    C = search(DTR)
    C.round(5).to_csv(HERE / "candidates.csv.gz", index=False)
    print("configs evaluated", len(C), "eligible", int(C.F.notna().sum()), f"{time.time() - t0:.0f}s", flush=True)
    SL = shortlist(DTR, C)
    picks, trig_seen = [], set()
    for i, r in SL.iterrows():
        if r.trig not in trig_seen and len(picks) < 5:
            picks.append(i); trig_seen.add(r.trig)
    TT = [trades(DTR, r, "TRAIN", CTR) for _, r in SL.iterrows()]
    del DTR
    DVA, CVA, frame = build(VALID, "VALID", keep_frame="2026-09")
    names = {}
    for j, i in enumerate(picks):
        r = SL.loc[i]
        names[i] = name_of(j, r)
        SL.loc[i, "words"] = write_module(names[i], r)
    par = parity(frame, [(names[i], SL.loc[i]) for i in picks])
    print("parity", par, flush=True)
    pd.DataFrame(par).T.to_csv(HERE / "parity.csv")
    del frame
    res, alltr = [], []
    for i, r in SL.iterrows():
        tv = trades(DVA, r, "VALID", CVA)
        tt = TT[i]
        row = dict(rank=i + 1, delivered=i in picks, name=names.get(i, ""), trig=r.trig, ctx=r.ctx, side=r.side,
                   geom=r.geom, win=r.win, F_train=round(r.F, 4), words=r.get("words", ""))
        row.update(summ(tt, "train")); row.update(summ(tv, "valid"))
        both = pd.concat([tt, tv])
        row["tps"] = round(len(both) / (DVA["sessions"] + NTR), 2)
        row.update({f"all_{nm}": round(both.r[both.dt == k].mean(), 4) for k, nm in enumerate(DTN)})
        if i in picks:
            par_ok = par[names[i]]["harness"] == par[names[i]]["module"] == par[names[i]]["both"]
            row["parity"] = par_ok
            row["gate_pass"] = bool(row["train_avg_r"] >= -0.02 and row["valid_avg_r"] >= -0.02 and 1.5 <= row["tps"] <= 25 and par_ok)
            alltr.append(both.assign(setup=names[i]))
        res.append(row)
    R = pd.DataFrame(res)
    R.to_csv(HERE / "results.csv", index=False)
    pd.concat(alltr).to_parquet(S / "trades.parquet", index=False)
    json.dump({"configs_evaluated": int(len(C)), "eligible": int(C.F.notna().sum()), "train_sessions": int(NTR),
               "valid_sessions": int(DVA["sessions"]), "picks": [names[i] for i in picks]},
              open(HERE / "picks.json", "w"), indent=1)
    if os.environ.get("GEN2_SMOKE"):
        print("smoke ok", len(R), R.columns.tolist()); return
    print(R[["rank", "delivered", "trig", "ctx", "side", "geom", "win", "F_train", "train_avg_r", "valid_avg_r", "tps"]].to_string())
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
