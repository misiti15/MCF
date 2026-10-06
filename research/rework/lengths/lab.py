"""Global indicator-length sweep over the setups2 candidates (rework key: lengths). Train/valid only.

Educational only -- not financial advice.

    python research/rework/lengths/lab.py <frame.parquet>      # frame from build.py

(a) the live exhaustion_short rule (volume_flip_1) and its t05s1 twin (volume_flip_2) with short-RSI / RSI(div) /
    fast-SMA / ATR lengths swapped (full factorial);
(b) every failed setups2 candidate with each of its length slots swapped (full factorial over the slots it uses);
(c) global settings: one (RSI, fast SMA, slow SMA, ATR) set applied to all candidates at once (pooled).
Thresholds are kept exactly as in research/setups2/candidates/*.py; only the lengths move.
Stats: first qualifying bar per symbol-day; day-clustered t (research/reddit_bt/common.metrics); ex-best-day;
baseline = same side, same exit, same date and same 5-min bar close, random symbol (exact expectation).
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
TRAIN_END = pd.Timestamp("2026-08-25").date()
LEVELS = {"rsis": [3, 5, 7, 10], "rsi": [7, 10, 14, 21], "fast": [10, 20, 50], "slow": [20, 50, 100], "atr": [10, 14, 20]}
BASE = {"rsis": 5, "rsi": 14, "fast": 20, "slow": 50, "atr": 14}


def _ok_setting(s):
    return not ("fast" in s and "slow" in s and s["fast"] >= s["slow"])


# ---------------------------------------------------------------- candidates (thresholds unchanged)
def m_volume_flip(a, s):
    return ((a[f"rsis_{s['rsis']}"] > 90) & (a[f"smad_{s['fast']}"] > 1.0) & (a[f"bear_div_{s['rsi']}"] > 0)
            & (a["tod"] >= 1300) & (a["tod"] <= 1500))


def m_obos_levels(a, s):
    A = s["atr"]
    dpl, atr = a[f"dpl_{A}"], a[f"atr_{A}"]
    pdl = a["close"] - dpl * atr
    with np.errstate(invalid="ignore"):
        return ((a[f"rsi_{s['rsi']}"] < 25) & (a["low"] <= pdl) & (dpl > 0) & (dpl <= 0.2)
                & (a["lower_wick"] >= 0.5) & (a["tod"] <= 1130))


def m_trend_pullback(a, s):
    with np.errstate(invalid="ignore"):
        return ((a["fromOpen"] < -0.5) & (a["vwapDistPct"] < 0) & (a[f"smad_{s['slow']}"] < 0)
                & (a[f"smad_{s['fast']}"] > 0) & (a["tod"] <= 1030))


def m_win_geometry_1(a, s):
    with np.errstate(invalid="ignore"):
        return (a["gap"] < -0.445) & (a[f"smad_{s['slow']}"] > 2.19) & (a["tod"] > 1299)


def m_win_geometry_2(a, s):
    with np.errstate(invalid="ignore"):
        return (a["macdPct"] > 0.399) & (a[f"dph_{s['atr']}"] > 0.95) & (a["flow3"] > 0.376)


def m_win_geometry_3(a, s):
    with np.errstate(invalid="ignore"):
        return (a["macdPct"] < -1.06) & (a[f"rsiSlope_{s['rsi']}"] > 23.7) & (a["momentum"] > 0.569)


# name: (mask fn, side, geom, length slots used; "atr" always (it sets R))
CANDS = {
    "volume_flip_1": (m_volume_flip, "short", "t1s1", ["rsis", "rsi", "fast", "atr"]),
    "volume_flip_2": (m_volume_flip, "short", "t05s1", ["rsis", "rsi", "fast", "atr"]),
    "obos_levels_1": (m_obos_levels, "short", "t1s1", ["rsi", "atr"]),
    "trend_pullback_1": (m_trend_pullback, "short", "t05s1", ["fast", "slow", "atr"]),
    "trend_pullback_2": (m_trend_pullback, "short", "t1s05", ["fast", "slow", "atr"]),
    "trend_pullback_3": (m_trend_pullback, "short", "t1s1", ["fast", "slow", "atr"]),
    "win_geometry_1": (m_win_geometry_1, "short", "t1s1", ["slow", "atr"]),
    "win_geometry_2": (m_win_geometry_2, "short", "t1s1", ["atr"]),
    "win_geometry_3": (m_win_geometry_3, "long", "t05s1", ["rsi", "atr"]),
}


def grid(keys):
    out = []
    for vals in itertools.product(*[LEVELS[k] for k in keys]):
        s = dict(zip(keys, vals))
        if _ok_setting(s):
            out.append(s)
    return out


def neighbours(s, keys):
    out = []
    for k in keys:
        lv = LEVELS[k]
        i = lv.index(s[k])
        for j in (i - 1, i + 1):
            if 0 <= j < len(lv):
                t = dict(s, **{k: lv[j]})
                if _ok_setting(t):
                    out.append(t)
    return out


def tag(s):
    return ",".join(f"{k}{v}" for k, v in s.items())


# ---------------------------------------------------------------- scoring
class Split:
    def __init__(self, df):
        self.a = {c: df[c].to_numpy() for c in df.columns if c not in ("symbol", "date", "ts")}
        self.date = df["date"].to_numpy()
        self.dcode = pd.factorize(df["date"])[0].astype(np.int64)
        self.key = df["symbol"].cat.codes.to_numpy().astype(np.int64) * 1000 + self.dcode
        self.slot = self.dcode * 2400 + df["tod"].to_numpy().astype(np.int64)
        self._base = {}

    def rowbase(self, col):
        """Mean outcome of all symbols at the same date and bar close: the random-symbol control."""
        if col not in self._base:
            r = self.a[col].astype(np.float64)
            ok = np.isfinite(r)
            s = pd.Series(r[ok]).groupby(self.slot[ok]).mean()
            self._base[col] = pd.Series(self.slot).map(s).to_numpy()
        return self._base[col]

    def trades(self, mask, col):
        r = self.a[col]
        idx = np.flatnonzero(np.asarray(mask, bool) & np.isfinite(r))
        if len(idx):
            _, first = np.unique(self.key[idx], return_index=True)
            idx = np.sort(idx[first])
        return idx

    def stats(self, mask, side, geom, A):
        col = f"r_{side}_{geom}_a{A}"
        idx = self.trades(mask, col)
        if len(idx) < 2:
            return {"n": int(len(idx))}
        r = self.a[col][idx].astype(np.float64)
        w = self.a[f"win_{side}_{geom}_a{A}"][idx].astype(np.float64)
        d = self.dcode[idx]
        t = pd.DataFrame({"d": d, "r": r})
        daily = t.groupby("d")["r"].agg(["sum", "size"])
        dm = (daily["sum"] - daily["size"] * r.mean()).to_numpy()
        se = float(np.sqrt((dm ** 2).sum()) / len(r)) if len(daily) > 1 else float("nan")
        best = daily["sum"].idxmax()
        ex = (daily["sum"].sum() - daily.loc[best, "sum"]) / max(1, len(r) - daily.loc[best, "size"])
        base = float(np.nanmean(self.rowbase(col)[idx]))
        gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
        return {"n": int(len(r)), "days": int(len(daily)), "win": round(float(w.mean()), 4), "exp_r": round(float(r.mean()), 4),
                "t": round(float(r.mean() / se), 2) if se > 0 else None, "pf": round(float(gw / gl), 3) if gl > 0 else None,
                "green_days": round(float((daily["sum"] > 0).mean()), 3), "ex_best_day": round(float(ex), 4),
                "base": round(base, 4), "edge": round(float(r.mean()) - base, 4), "_r": r, "_d": d}


def clean(m):
    return {k: v for k, v in m.items() if not k.startswith("_")}


def main(path):
    cols = None
    df = pd.read_parquet(path, columns=cols)
    df["symbol"] = df["symbol"].astype("category")
    sp = {"train": Split(df[df["date"] <= TRAIN_END]), "valid": Split(df[df["date"] > TRAIN_END])}
    info = {k: {"rows": int(len(v.date)), "days": int(len(set(v.dcode)))} for k, v in sp.items()}
    del df
    rows, cache = [], {}

    def ev(name, s):
        k = (name, tag(s))
        if k not in cache:
            fn, side, geom, keys = CANDS[name]
            cache[k] = {sn: fn_stats(sp[sn], fn, side, geom, s) for sn in sp}
        return cache[k]

    def fn_stats(S, fn, side, geom, s):
        full = dict(BASE, **s)
        return S.stats(fn(S.a, full), side, geom, full["atr"])

    # (a)+(b): per-candidate full factorial over its own length slots
    for name, (fn, side, geom, keys) in CANDS.items():
        for s in grid(keys):
            res = ev(name, s)
            nb = [ev(name, t)["valid"].get("exp_r", np.nan) for t in neighbours(s, keys)]
            nbt = [ev(name, t)["train"].get("exp_r", np.nan) for t in neighbours(s, keys)]
            rows.append({"part": "a" if name.startswith("volume_flip") else "b", "candidate": name, "side": side, "geom": geom,
                         "setting": s, "is_base": all(s[k] == BASE[k] for k in s),
                         "train": clean(res["train"]), "valid": clean(res["valid"]),
                         "plateau_valid_mean": round(float(np.nanmean(nb)), 4) if nb else None,
                         "plateau_valid_all_pos": bool(np.all(np.array(nb) > 0)) if nb else None,
                         "plateau_train_mean": round(float(np.nanmean(nbt)), 4) if nbt else None,
                         "n_neighbours": len(nb)})
    n_unique = len(cache)
    # (c): global settings, rsis kept at 5 (the short-RSI slot is swept in (a))
    glob = []
    gkeys = ["rsi", "fast", "slow", "atr"]
    for s in grid(gkeys):
        out = {"setting": s}
        for sn in sp:
            rs, per = [], {}
            for name, (fn, side, geom, keys) in CANDS.items():
                m = ev(name, {k: (5 if k == "rsis" else s[k]) for k in keys})[sn]
                per[name] = m.get("exp_r")
                if m.get("n", 0) >= 2:
                    rs.append(pd.DataFrame({"r": m["_r"], "d": m["_d"]}))
            t = pd.concat(rs)
            daily = t.groupby("d")["r"].agg(["sum", "size"])
            dm = (daily["sum"] - daily["size"] * t.r.mean()).to_numpy()
            se = float(np.sqrt((dm ** 2).sum()) / len(t))
            out[sn] = {"n": int(len(t)), "exp_r": round(float(t.r.mean()), 4), "t": round(float(t.r.mean() / se), 2),
                       "n_cands_pos": int(sum(1 for v in per.values() if v is not None and v > 0)), "per_candidate": per}
        glob.append(out)
    configs = n_unique + len(glob)
    res = {"educational": "Educational only -- not financial advice.", "splits": info, "configs_tried": configs,
           "unique_candidate_settings": n_unique, "global_settings": len(glob), "levels": LEVELS, "base": BASE,
           "rows": rows, "global": glob}
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=str))
    print("configs", configs, info)


if __name__ == "__main__":
    main(sys.argv[1])
