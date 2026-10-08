"""BDI 2026-10-08: article indicator rules, faithful then layered (grid pre-declared in NOTES.md section 0).
Train/valid only. First qualifying bar per symbol-day, lab outcomes, production haircut (2 x 1 bps x price + 2c) / R.
Writes results.csv and plateau.csv next to this file. Educational only - not financial advice."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
GEOMS = ["t1s1", "t05s1", "t1s05"]
WINDOWS = {"am": (950, 1130), "pm": (1130, 1500), "all": (950, 1500)}
WIN_NB = {"am": ["all"], "pm": ["all"], "all": ["am", "pm"]}
FRAME = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "volumeRatio", "fromOpen", "vwapDistPct"] + \
        [f"r_{s}_{g}" for s in ("long", "short") for g in GEOMS]


def prep(split):
    fr = pd.read_parquet(f"research/setups2/data/{split}.parquet", columns=FRAME)
    fr["date"] = pd.to_datetime(fr["date"]).dt.date
    lo, hi = fr.date.min(), fr.date.max()
    ft = pd.read_parquet(HERE / "data" / "feat.parquet", filters=[("date", ">=", lo), ("date", "<=", hi)])
    ft = ft.drop(columns=["close"])
    fr["tod"] = fr["tod"].astype("int16")
    fr["symbol"] = fr["symbol"].astype(str)
    df = fr.merge(ft, on=["symbol", "date", "tod"], how="left")
    del fr, ft
    df = df.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    key = df.symbol.to_numpy() + "|" + df.date.astype(str).to_numpy()
    sid = pd.factorize(key)[0]
    R = 0.25 * df.atr_d.to_numpy(float)
    hair = (2 * df.close.to_numpy(float) * 1e-4 + 0.02) / R
    out = {(s, g): df[f"r_{s}_{g}"].to_numpy(float) - hair for s in ("long", "short") for g in GEOMS}
    dates = df.date.astype(str).to_numpy()
    return df, sid, dates, out


# ------------------------------------------------------------------ triggers: name -> (param grid, default index, fn)
def _x_up(a, ap):
    return (a > 0) & (ap <= 0)


def T(df):
    c = lambda k: df[k].to_numpy(float)
    close, low, high = c("close"), c("low"), c("high")
    t = {}

    def macd(s, p):
        h, hp = c(f"macdh_{p[0]}_{p[1]}_{p[2]}"), c(f"macdh_{p[0]}_{p[1]}_{p[2]}_prev")
        return _x_up(s * h, s * hp)
    t["macdx"] = ([(8, 17, 9), (12, 26, 9), (5, 35, 5)], 1, macd)

    def bbt(s, p):
        n, k = p
        return (c(f"bbz_lo_{n}") <= -k) if s > 0 else (c(f"bbz_hi_{n}") >= k)
    t["bbtouch"] = ([(20, 2.0), (15, 2.0), (30, 2.0), (20, 1.5), (20, 2.5)], 0, bbt)

    def sq(s, q):
        return (c("bbw_pctl_prev") <= q) & (s * c("bbz_c_20") > 2)
    t["squeeze"] = ([0.1, 0.2, 0.3], 1, sq)

    def stoch(s, p):
        n, lv = p
        k, d, kp, dp = c(f"stk_{n}"), c(f"std_{n}"), c(f"stk_{n}_prev"), c(f"std_{n}_prev")
        if s > 0:
            return (k > d) & (kp <= dp) & (kp < lv)
        return (k < d) & (kp >= dp) & (kp > 100 - lv)
    t["stochx"] = ([(14, 20), (9, 20), (21, 20), (14, 15), (14, 25)], 0, stoch)

    def dmi(s, p):
        n, thr = p
        return (c(f"adx_{n}") >= thr) & _x_up(s * c(f"dmi_{n}"), s * c(f"dmi_{n}_prev"))
    t["dmix"] = ([(14, 25), (10, 25), (20, 25), (14, 20), (14, 30)], 0, dmi)

    t["obvdiv"] = ([None], 0, lambda s, p: c("obv_bull") > 0 if s > 0 else c("obv_bear") > 0)

    def emx(s, p):
        return _x_up(s * c(f"ema_{p[0]}_{p[1]}"), s * c(f"ema_{p[0]}_{p[1]}_prev"))
    t["emax"] = ([(5, 13), (9, 21), (13, 34)], 1, emx)
    t["smax"] = ([None], 0, lambda s, p: _x_up(s * c("sma_20_50"), s * c("sma_20_50_prev")))

    def rsx(s, lv):
        r, rp = c("rsi14"), c("rsi14_prev")
        return ((r > lv) & (rp <= lv)) if s > 0 else ((r < 100 - lv) & (rp >= 100 - lv))
    t["rsix"] = ([25, 30, 35], 1, rsx)
    t["vwapx"] = ([None], 0, lambda s, p: _x_up(s * c("vwapd"), s * c("vwapd_prev")))
    cp = c("close_prev")
    t["pivx"] = ([None], 0, lambda s, p: _x_up(s * (close - c("piv_p")), s * (cp - c("piv_p"))))
    # level touch-and-hold: long = S1 bounce, short = R1 rejection
    t["s1r1hold"] = ([None], 0, lambda s, p: ((low <= c("piv_s1")) & (close > c("piv_s1"))) if s > 0
                     else ((high >= c("piv_r1")) & (close < c("piv_r1"))))
    t["r1s1break"] = ([None], 0, lambda s, p: _x_up(close - c("piv_r1"), cp - c("piv_r1")) if s > 0
                      else _x_up(c("piv_s1") - close, c("piv_s1") - cp))

    def fib(s, f):
        hod, lod, up = c("hod"), c("lod"), c("upleg")
        rng = hod - lod
        if s > 0:
            lv = hod - f * rng
            return (up > 0) & (rng > 0) & (low <= lv) & (close > lv)
        lv = lod + f * rng
        return (up < 1) & (rng > 0) & (high >= lv) & (close < lv)
    t["fib"] = ([0.5, 0.618, 0.786], 1, fib)
    t["aroonx"] = ([14, 25, 50], 1, lambda s, n: _x_up(s * c(f"aroon_{n}"), s * c(f"aroon_{n}_prev")))

    def ichi(s, p):
        top, bot, tp, bp, tk = c("ichi_top"), c("ichi_bot"), c("ichi_top_prev"), c("ichi_bot_prev"), c("ichi_tk")
        if s > 0:
            return (close > top) & (cp <= tp) & (tk > 0)
        return (close < bot) & (cp >= bp) & (tk < 0)
    t["ichix"] = ([None], 0, ichi)
    t["tkx"] = ([None], 0, lambda s, p: _x_up(s * c("ichi_tk"), s * c("ichi_tk_prev")))
    return t


def F(df):
    c = lambda k: df[k].to_numpy(float)
    close = c("close")
    f = {
        "adx25": ([25, 20, 30], 0, lambda s, p: c("adx_14") >= p),
        "adxlo": ([20, 15, 25], 0, lambda s, p: c("adx_14") < p),
        "vwap_with": ([None], 0, lambda s, p: s * c("vwapDistPct") > 0),
        "vwap_against": ([None], 0, lambda s, p: s * c("vwapDistPct") < 0),
        "dsma20_with": ([None], 0, lambda s, p: s * (close - c("d_sma20")) > 0),
        "dsma20_against": ([None], 0, lambda s, p: s * (close - c("d_sma20")) < 0),
        "drsi_with": ([50, 45, 55], 0, lambda s, p: s * (c("d_rsi14") - p) > 0),
        "vol15": ([1.5, 1.25, 2.0], 0, lambda s, p: c("volumeRatio") >= p),
        "obv_with": ([None], 0, lambda s, p: s * c("obv_slope") > 0),
        "macdh_with": ([None], 0, lambda s, p: s * c("macdh_12_26_9") > 0),
        "ema_with": ([None], 0, lambda s, p: s * c("ema_9_21") > 0),
        "open_with": ([None], 0, lambda s, p: s * c("fromOpen") > 0),
    }
    return f


BAD = {frozenset(("vwap_with", "vwap_against")), frozenset(("dsma20_with", "dsma20_against"))}


class Scorer:
    def __init__(self, split):
        self.df, self.sid, self.dates, self.out = prep(split)
        self.tod = self.df.tod.to_numpy()
        ud = np.array(sorted(set(self.dates)))
        self.half = ud[len(ud) // 2]
        self.win = {w: (self.tod >= a) & (self.tod <= b) for w, (a, b) in WINDOWS.items()}
        self.T, self.F = T(self.df), F(self.df)
        self.cache = {}
        self.base = {}
        for w, m in self.win.items():
            for (s, g), r in self.out.items():
                x = r[m & np.isfinite(r)]
                self.base[(s, g, w)] = float(x.mean())

    def trig(self, name, side, pi=None):
        k = ("T", name, side, pi)
        if k not in self.cache:
            grid, d, fn = self.T[name]
            with np.errstate(invalid="ignore"):
                self.cache[k] = np.asarray(fn(side, grid[d if pi is None else pi]), bool)
        return self.cache[k]

    def filt(self, name, side, pi=None):
        k = ("F", name, side, pi)
        if k not in self.cache:
            grid, d, fn = self.F[name]
            with np.errstate(invalid="ignore"):
                self.cache[k] = np.asarray(fn(side, grid[d if pi is None else pi]), bool)
        return self.cache[k]

    def idx(self, trig_m, filts, w):
        i = np.flatnonzero(trig_m & self.win[w])
        for fm in filts:
            i = i[fm[i]]
        return i

    def score(self, i, side, geom):
        r = self.out[(side, geom)][i]
        ok = np.isfinite(r)
        i, r = i[ok], r[ok]
        if len(i) == 0:
            return None
        _, first = np.unique(self.sid[i], return_index=True)
        i, r = i[first], r[first]
        n = len(r)
        if n < 2:
            return None
        d = pd.Series(r).groupby(self.dates[i]).agg(["sum", "size"])
        mu = r.mean()
        se = np.sqrt(((d["sum"] - d["size"] * mu) ** 2).sum()) / n
        best = d["sum"].idxmax()
        keep = self.dates[i] != best
        h1, h2 = r[self.dates[i] < self.half], r[self.dates[i] >= self.half]
        return {"n": n, "days": len(d), "exp": mu, "t": mu / se if se > 0 else 0.0,
                "exbest": r[keep].mean() if keep.any() else np.nan,
                "h1": h1.mean() if len(h1) else np.nan, "h2": h2.mean() if len(h2) else np.nan,
                "green": float((d["sum"] > 0).mean())}


TRIGS = ["macdx", "bbtouch", "squeeze", "stochx", "dmix", "obvdiv", "emax", "smax", "rsix", "vwapx", "pivx",
         "s1r1hold", "r1s1break", "fib", "aroonx", "ichix", "tkx"]
FILTS = ["adx25", "adxlo", "vwap_with", "vwap_against", "dsma20_with", "dsma20_against", "drsi_with", "vol15",
         "obv_with", "macdh_with", "ema_with", "open_with"]


def grid():
    combos = [()] + [(f,) for f in FILTS] + [p for p in itertools.combinations(FILTS, 2) if frozenset(p) not in BAD]
    for tr in TRIGS:
        for s in (1, -1):
            for fs in combos:
                fam = "F" if not fs else ("L1" if len(fs) == 1 else "L2")
                for w in WINDOWS:
                    yield fam, tr, s, s, fs, w
                    if not fs:
                        yield "C", tr, s, -s, fs, w      # contrarian: trigger of side s, traded on side -s


def row(S, tr, ts, side, fs, w, g, tpi=None, fpi=None):
    fpi = fpi or {}
    i = S.idx(S.trig(tr, ts, tpi), [S.filt(f, side, fpi.get(f)) for f in fs], w)
    sd = "long" if side > 0 else "short"
    r = S.score(i, sd, g)
    return r, S.base[(sd, g, w)]


if __name__ == "__main__":
    import sys
    S = {sp: Scorer(sp) for sp in ("train", "valid")}
    print("loaded", {k: len(v.df) for k, v in S.items()}, flush=True)
    for sp, s in S.items():   # coverage of the new columns
        cov = s.df[["macdh_12_26_9", "bbw_pctl", "adx_14", "ichi_top", "piv_p", "d_sma20", "d_sma50", "d_rsi14"]].notna().mean()
        print(sp, cov.round(3).to_dict(), flush=True)
    rows, n_cfg, n_unscored = [], 0, 0
    for fam, tr, ts, side, fs, w in grid():
        for g in GEOMS:
            n_cfg += 1
            a, ba = row(S["train"], tr, ts, side, fs, w, g)
            if a is None or a["n"] < 60:
                n_unscored += 1
                continue
            b, bb = row(S["valid"], tr, ts, side, fs, w, g)
            rec = {"family": fam, "trigger": tr, "trigger_side": "long" if ts > 0 else "short",
                   "side": "long" if side > 0 else "short", "filters": "+".join(fs), "window": w, "geom": g,
                   "tr_n": a["n"], "tr_days": a["days"], "tr_exp": a["exp"], "tr_t": a["t"], "tr_exbest": a["exbest"],
                   "tr_h1": a["h1"], "tr_h2": a["h2"], "tr_base": ba, "tr_edge": a["exp"] - ba}
            if b is not None:
                rec.update({"va_n": b["n"], "va_days": b["days"], "va_exp": b["exp"], "va_t": b["t"],
                            "va_exbest": b["exbest"], "va_green": b["green"], "va_base": bb, "va_edge": b["exp"] - bb})
            rows.append(rec)
        if n_cfg % 3000 == 0:
            print(n_cfg, flush=True)
    r = pd.DataFrame(rows)
    r["pre_gate"] = ((r.tr_exp > 0) & (r.va_exp > 0) & (r.va_n >= 30) & (r.va_t >= 1.5) & (r.tr_h1 > 0) & (r.tr_h2 > 0)
                     & (r.tr_edge > 0) & (r.va_edge > 0))
    # ---------------------------------------------------------------- plateau for every pre-gate passer
    pl = []
    n_nb = 0
    for k, x in r[r.pre_gate].iterrows():
        ts = 1 if x.trigger_side == "long" else -1
        side = 1 if x.side == "long" else -1
        fs = tuple(f for f in x.filters.split("+") if f)
        nbs = []
        grid_t, d, _ = S["train"].T[x.trigger]
        nbs += [("trig", pi, {}, x.window) for pi in range(len(grid_t)) if pi != d]
        for f in fs:
            gf, df_, _ = S["train"].F[f]
            nbs += [(f, None, {f: pi}, x.window) for pi in range(len(gf)) if pi != df_]
        nbs += [("window", None, {}, w2) for w2 in WIN_NB[x.window]]
        tr_e, va_e = [], []
        for lab, tpi, fpi, w2 in nbs:
            n_nb += 1
            a, _ = row(S["train"], x.trigger, ts, side, fs, w2, x.geom, tpi, fpi)
            b, _ = row(S["valid"], x.trigger, ts, side, fs, w2, x.geom, tpi, fpi)
            tr_e.append(a["exp"] if a else np.nan)
            va_e.append(b["exp"] if b else np.nan)
            pl.append({"cfg": k, "nb": f"{lab}:{tpi if tpi is not None else fpi or w2}", "tr_n": a["n"] if a else 0,
                       "tr_exp": tr_e[-1], "va_n": b["n"] if b else 0, "va_exp": va_e[-1]})
        tr_e, va_e = np.array(tr_e), np.array(va_e)
        r.loc[k, "nb_n"] = len(nbs)
        r.loc[k, "nb_tr_mean"] = np.nanmean(tr_e)
        r.loc[k, "nb_va_mean"] = np.nanmean(va_e)
        r.loc[k, "nb_va_pos"] = np.nanmean(va_e > 0)
    r["plateau"] = (r.get("nb_tr_mean", 0) > 0) & (r.get("nb_va_mean", 0) > 0) & (r.get("nb_va_pos", 0) >= 2 / 3)
    r["finalist_gate"] = r.pre_gate & r.plateau
    r.to_csv(HERE / "results.csv", index=False, float_format="%.4f")
    pd.DataFrame(pl).to_csv(HERE / "plateau.csv", index=False, float_format="%.4f")
    summ = {"declared": n_cfg, "unscored_train_n_lt_60": n_unscored, "scored": len(r), "plateau_neighbours": n_nb,
            "total_incl_plateau": n_cfg + n_nb, "pre_gate": int(r.pre_gate.sum()), "finalist_gate": int(r.finalist_gate.sum())}
    (HERE / "counts.json").write_text(json.dumps(summ, indent=1))
    print(summ)
