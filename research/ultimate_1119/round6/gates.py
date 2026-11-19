"""Round 6: point-in-time market-state gates for BOOK-EM and ST7-FD, leave-one-window-out (round6/PLAN.md).
    python gates.py BENCH_TRADES_PARQUET W2_BOOKEM_CSV
Writes round6/gates.json and round6/trades_features.csv.gz. Locked block 2024-11-01..2025-02-28 never read.
Educational only - not financial advice."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent
U = HERE.parent
FRESH_DAILY = "/home/user/MCF/data/cache_fresh/daily.parquet"
H2Y_DAILY = "/home/user/MCF/research/history2y/data/daily.parquet"
SPY_FRESH = "/home/user/MCF/data/cache_fresh/1Min/SPY.parquet"
SPY_HIST = "/home/user/MCF/data/cache_hist/1Min/SPY.parquet"
L0, L1 = dt.date(2024, 11, 1), dt.date(2025, 2, 28)
TZ = "America/New_York"
N_JOB = 1882
TBAR = max(1.5, math.sqrt(2 * math.log(N_JOB)))
SESS = {"W1": 427, "W2": 170, "W3": 276}


def no_locked(dates):
    d = pd.to_datetime(pd.Series(list(dates))).dt.date
    assert not ((d >= L0) & (d <= L1)).any(), "locked row"


def window(d: pd.Series) -> np.ndarray:
    s = d.astype(str)
    w1 = (s >= "2023-01-03") & (s <= "2024-09-13")
    w2 = ((s >= "2024-10-01") & (s <= "2024-10-31")) | ((s >= "2025-03-01") & (s <= "2025-09-30"))
    w3 = (s >= "2025-10-01") & (s <= "2026-11-04")
    return np.where(w1, "W1", np.where(w2, "W2", np.where(w3, "W3", "")))


# ------------------------------------------------------------------ trades
def load_trades(bench_pq, w2_csv):
    fr = pd.read_csv(U / "round5" / "fresh_trades.csv.gz")
    fr = fr[fr.r.notna()]
    a = fr[fr.rule == "R1"][["symbol", "date", "tod", "leg", "r"]].assign(book="BOOK-EM")
    b = fr[fr.rule == "R4"][["symbol", "date", "tod", "r"]].assign(book="ST7-FD", leg="ST7")
    half = b.date.isin(["2023-07-03", "2023-11-24", "2024-07-03"]) & (b.tod >= 1255)
    print("ST7-FD W1 early-close rows dropped:", int(half.sum()), round(float(b[half].r.sum()), 2))
    b = b[~half]
    c = pd.read_csv(w2_csv)[["symbol", "date", "tod", "leg", "r"]].assign(book="BOOK-EM")
    e = pd.read_csv(U / "round4" / "ULT-32" / "check_trades.csv.gz")
    e = e[e.leg.isin(["E", "M"])][["symbol", "date", "tod", "leg", "r"]].assign(book="BOOK-EM")
    bt = pd.read_parquet(bench_pq)
    bt = bt[bt.setup == "ST7-rsi50dn-long-pm-t1s1-FD"].rename(columns={"r1": "r"})
    bt["date"] = pd.to_datetime(bt.date).dt.strftime("%Y-%m-%d")
    bt = bt[bt.r.notna()][["symbol", "date", "tod", "r"]].assign(book="ST7-FD", leg="ST7")
    T = pd.concat([a, b, c, e, bt], ignore_index=True)
    T["date"] = T.date.astype(str)
    T["win"] = window(T.date)
    assert (T.win != "").all()
    no_locked(T.date.unique())
    return T


# ------------------------------------------------------------------ daily features
def read_daily():
    f = ds.field("date")
    x = pd.read_parquet(FRESH_DAILY, columns=["symbol", "date", "open", "close", "adv20"])
    x["date"] = pd.to_datetime(x.date).dt.strftime("%Y-%m-%d")
    x = x[x.date <= "2024-09-13"]
    y = ds.dataset(H2Y_DAILY).to_table(filter=(f < L0) | (f > L1),
                                       columns=["symbol", "date", "open", "close", "adv20"]).to_pandas()
    y["date"] = pd.to_datetime(y.date).dt.strftime("%Y-%m-%d")
    y = y[y.date >= "2024-09-16"]
    d = pd.concat([x, y], ignore_index=True)
    no_locked(d.date.unique())
    return d


def daily_features(d: pd.DataFrame) -> pd.DataFrame:
    sess = sorted(d[d.symbol == "SPY"].date.unique())
    seg = pd.Series((pd.Index(sess) > "2024-10-31").astype(int), index=sess)
    piv = d.pivot_table(index="date", columns="symbol", values="close").reindex(sess)
    advp = d.pivot_table(index="date", columns="symbol", values="adv20").reindex(sess)
    op = d[d.symbol == "SPY"].set_index("date").open.reindex(sess)
    segv = seg.to_numpy()
    n = len(sess)

    def ok(i, L):          # prior L sessions (i-L .. i-1) all in day i's segment
        return i - L >= 0 and segv[i - L] == segv[i]

    spy, vxx = piv["SPY"].to_numpy(), piv["VXX"].to_numpy()
    R = piv.pct_change(fill_method=None).clip(-0.5, 0.5).to_numpy()
    C = piv.to_numpy()
    A = advp.to_numpy()
    out = []
    for i in range(n):
        o = {"date": sess[i]}
        if ok(i, 21):
            r = np.diff(np.log(spy[i - 21:i]))
            o["rv20"] = float(np.std(r, ddof=1) * math.sqrt(252) * 100)
        if ok(i, 20):
            o["tr20"] = float(spy[i - 1] / np.mean(spy[i - 20:i]) - 1) * 100
        if ok(i, 50):
            o["tr50"] = float(spy[i - 1] / np.mean(spy[i - 50:i]) - 1) * 100
        if ok(i, 2):
            o["ret1"] = float(spy[i - 1] / spy[i - 2] - 1) * 100
            o["disp"] = float(np.nanstd(R[i - 1][(A[i - 1] >= 95e6)], ddof=1) * 100)
        if ok(i, 6):
            o["ret5"] = float(spy[i - 1] / spy[i - 6] - 1) * 100
        if ok(i, 10):
            o["vxx10"] = float(vxx[i - 1] / np.nanmean(vxx[i - 10:i]) - 1) * 100
        if ok(i, 21):
            m = A[i - 1] >= 95e6
            ma = np.nanmean(C[i - 20:i], axis=0)
            v = C[i - 1][m] > ma[m]
            k = ~np.isnan(C[i - 1][m]) & ~np.isnan(ma[m])
            o["breadth20"] = float(v[k].mean())
        if ok(i, 1):
            o["gap"] = float(op.iloc[i] / spy[i - 1] - 1) * 100
        o["dow"] = pd.Timestamp(sess[i]).dayofweek
        out.append(o)
    return pd.DataFrame(out).set_index("date")


# ------------------------------------------------------------------ intraday SPY state
def spy_minutes():
    f = pd.read_parquet(SPY_FRESH)
    f.index = pd.DatetimeIndex(f.index).tz_convert(TZ)
    f = f[(f.index.date >= dt.date(2023, 1, 3)) & (f.index.date <= dt.date(2024, 9, 13))]
    fld = ds.field("__index_level_0__")
    h = ds.dataset(SPY_HIST).to_table(filter=(fld < pd.Timestamp("2024-11-01", tz=TZ)) |
                                      (fld >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in h.columns:
        h = h.set_index("__index_level_0__")
    h.index = pd.DatetimeIndex(h.index).tz_convert(TZ)
    h = h[h.index.date >= dt.date(2024, 9, 16)]
    m = pd.concat([f, h])
    m = m[(m.index.hour * 100 + m.index.minute >= 930) & (m.index.hour * 100 + m.index.minute < 1600)]
    no_locked(set(m.index.date))
    m["date"] = m.index.strftime("%Y-%m-%d")
    m["mn"] = m.index.hour * 60 + m.index.minute
    return m[["date", "mn", "open", "close"]]


def m2(t):
    t = np.asarray(t)
    return (t // 100) * 60 + t % 100


def intraday(T, m):
    g = {d: x for d, x in m.groupby("date")}
    fo, s30 = np.full(len(T), np.nan), np.full(len(T), np.nan)
    for j, (d, tod) in enumerate(zip(T.date.to_numpy(), T.tod.to_numpy())):
        x = g.get(d)
        if x is None:
            continue
        mn = x.mn.to_numpy()
        dec = m2(tod) + 5                       # decision-bar close (frames are left-labelled 5-min bars)
        o930 = x.open.to_numpy()[0] if mn[0] == 570 else np.nan
        i = np.searchsorted(mn, dec, "left") - 1          # last minute bar starting before the decision time
        k = np.searchsorted(mn, dec - 30, "left") - 1
        if i >= 0:
            fo[j] = (x.close.to_numpy()[i] / o930 - 1) * 100
            if k >= 0:
                s30[j] = (x.close.to_numpy()[i] / x.close.to_numpy()[k] - 1) * 100
    T["spy_fo"], T["spy30"] = fo, s30
    return T


# ------------------------------------------------------------------ scoring
def st(t, nses):
    if len(t) == 0:
        return {"n": 0}
    day = t.groupby("date").r.sum()
    avg = float(t.r.mean())
    dev = (t.r - avg).groupby(t.date).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(t)
    best = day.idxmax()
    tot = float(t.r.sum())
    return {"n": int(len(t)), "per_sess": round(len(t) / nses, 3), "avg_r": round(avg, 4),
            "wo_best": round(float(t.loc[t.date != best, "r"].mean()), 4) if (t.date != best).any() else None,
            "best_share": round(float(day.max()) / tot, 3) if tot > 0 else None,
            "t": round(avg / se, 2) if se > 0 else None, "total_r": round(tot, 2)}


FEATS = ["rv20", "tr20", "tr50", "ret1", "ret5", "vxx10", "disp", "breadth20", "gap", "spy_fo", "spy30"]
FRACS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def configs(g, train):
    if g == "dow":
        return [("drop", k, None) for k in range(5)]
    v = train[g].dropna().to_numpy()
    out = []
    for dr in ("low", "high"):
        for f in FRACS:
            out.append((dr, f, float(np.quantile(v, f if dr == "low" else 1 - f))))
    return out


def keep(x, g, cfg):
    dr, f, thr = cfg
    if g == "dow":
        return x["dow"] != f
    return x[g] <= thr if dr == "low" else x[g] >= thr


def run(T):
    res = {"n_job": N_JOB, "t_bar": round(TBAR, 3), "books": {}}
    for book in ("BOOK-EM", "ST7-FD"):
        B = T[T.book == book]
        rb = {"ungated": {w: st(B[B.win == w], SESS[w]) for w in SESS}, "gates": {}}
        rb["ungated"]["pooled"] = st(B, sum(SESS.values()))
        for g in FEATS + ["dow"]:
            K = B[B[g].notna()]
            gr = {"nan_trades": {w: int(((B.win == w) & B[g].isna()).sum()) for w in SESS}, "rot": {}}
            held = []
            for H in SESS:
                tr = K[K.win != H]
                trw = [w for w in SESS if w != H]
                best, bkey = None, None
                for cfg in configs(g, tr):
                    kk = tr[keep(tr, g, cfg)]
                    a = [kk[kk.win == w].r.mean() if (kk.win == w).any() else -9 for w in trw]
                    key = (min(a), cfg[1] if g != "dow" else 0)
                    if bkey is None or key > bkey:
                        best, bkey = cfg, key
                ho = K[K.win == H]
                kh = ho[keep(ho, g, best)]
                held.append(kh)
                s = st(kh, SESS[H])
                s["kept_share"] = round(len(kh) / max(len(ho), 1), 3)
                s["ungated_known"] = st(ho, SESS[H])
                s["delta_vs_ungated"] = round(s.get("avg_r", 0) - s["ungated_known"].get("avg_r", 0), 4) if s["n"] else None
                s["train_min_avg_r"] = round(float(bkey[0]), 4)
                s["cfg"] = {"dir": best[0], "frac_or_dow": best[1], "thr": None if best[2] is None else round(best[2], 4)}
                if book == "BOOK-EM":
                    s["by_leg"] = {L: st(kh[kh.leg == L], SESS[H]).get("avg_r") for L in ("E", "M")}
                    s["by_leg_ungated"] = {L: st(ho[ho.leg == L], SESS[H]).get("avg_r") for L in ("E", "M")}
                gr["rot"][H] = s
            P = pd.concat(held)
            gr["pooled_heldout"] = st(P, sum(SESS.values()))
            r = gr["rot"]
            c1 = all(r[w]["n"] and r[w]["avg_r"] > 0 for w in SESS)
            c2 = all(r[w]["n"] and (r[w]["wo_best"] or -1) > 0 for w in SESS)
            c3 = all(r[w]["kept_share"] >= 0.4 for w in SESS)
            c4 = (gr["pooled_heldout"].get("t") or -9) >= TBAR
            gr["pass"] = {"all3_pos": c1, "all3_wo_best_pos": c2, "kept40": c3, "t_bar": c4,
                          "PROMISING": bool(c1 and c2 and c3 and c4)}
            rb["gates"][g] = gr
        res["books"][book] = rb
    return res


if __name__ == "__main__":
    T = load_trades(sys.argv[1], sys.argv[2])
    D = daily_features(read_daily())
    T = T.join(D, on="date")
    T = intraday(T, spy_minutes())
    T.round(5).to_csv(HERE / "trades_features.csv.gz", index=False)
    print(T.groupby(["book", "win"]).r.agg(["size", "mean"]))
    print(T[FEATS].isna().groupby(T.win).sum())
    out = run(T)
    (HERE / "gates.json").write_text(json.dumps(out, indent=1))
    for book, rb in out["books"].items():
        print(book, {w: (v["n"], v["avg_r"]) for w, v in rb["ungated"].items()})
        for g, gr in rb["gates"].items():
            r = gr["rot"]
            print(f" {g:10s}", " | ".join(f"{w}: {r[w]['avg_r']:+.3f} wob {r[w]['wo_best']} keep {r[w]['kept_share']:.2f} "
                                          f"{r[w]['cfg']['dir']}{r[w]['cfg']['frac_or_dow']}" for w in SESS),
                  "| pooled", gr["pooled_heldout"]["avg_r"], "t", gr["pooled_heldout"]["t"], gr["pass"]["PROMISING"])
