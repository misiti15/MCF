"""Crypto price-action anatomy (description only, NO strategy search). research/crypto_found/ANATOMY.md.

Data: Alpaca 1-min cache, clean signal bars only (mcf.crypto.exec1m.clean_traded: Amendment-1 bad-print filter,
then traded minutes, volume > 0). FIT + CHECK only (2021-01-01 .. 2026-05-25): the loader clips at the LOCKED
start; MCF_CRYPTO_ALLOW_LOCKED is never set here. Every threshold below is a fixed, round, a-priori definition
(2 sigma, 3 sigma, 2/3/5 %, 50 % wick), not fitted; no entry/exit rule is scored.
Stage 1 (prep) writes 15-min bars per pair to a scratch dir; stage 2 (analyze) builds the tables + charts.
Usage: python research/crypto_found/anatomy.py --scratch DIR [--prep] [--out research/crypto_found]
Educational only — not financial advice.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
assert os.environ.get("MCF_CRYPTO_ALLOW_LOCKED") != "1", "LOCKED must stay sealed for this study"
from mcf.crypto import data as D
from mcf.crypto.costs import CostModel
from mcf.crypto.exec1m import clean_traded
from mcf.crypto.splits import LOCKED_START

END = pd.Timestamp(LOCKED_START, tz="UTC")
REGIMES = {"2021 bull": ("2021-01-01", "2022-01-01"), "2022 bear": ("2022-01-01", "2023-01-01"),
           "2023-24 recov/bull": ("2023-01-01", "2025-01-01"), "2025-26": ("2025-01-01", "2026-05-26")}
SESS = [("Asia 00-08", 0, 8), ("EU 08-13:30", 8, 13.5), ("US 13:30-20", 13.5, 20), ("Late 20-24", 20, 24)]


# ----------------------------------------------------------------------------- stage 1: prep
def prep(scratch: Path) -> pd.DataFrame:
    scratch.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in D.PAIRS:
        raw = D.load_bars(p)
        if raw.empty:
            continue
        s = clean_traded(raw)
        s = s[s.index < END]
        dv1 = s["vw"].fillna(s["c"]) * s["v"]
        q = pd.DataFrame({"o": s["o"].resample("15min").first(), "h": s["h"].resample("15min").max(),
                          "l": s["l"].resample("15min").min(), "c": s["c"].resample("15min").last(),
                          "v": s["v"].resample("15min").sum(), "dv": dv1.resample("15min").sum(),
                          "nm": s["c"].resample("15min").count()}).dropna(subset=["o"])
        q.astype("float32").to_parquet(scratch / f"{p}_15m.parquet")
        dd = dv1.resample("1D").sum()
        dd = dd[dd.index >= s.index[0].floor("D")]
        yrs = {}
        for y in range(2021, 2027):
            a = max(pd.Timestamp(f"{y}-01-01", tz="UTC"), s.index[0])
            b = min(pd.Timestamp(f"{y + 1}-01-01", tz="UTC"), END)
            if b > a:
                yrs[f"tr{y}"] = round(((s.index >= a) & (s.index < b)).sum() / ((b - a).total_seconds() / 60), 3)
        rows.append(dict(pair=p, first=str(s.index[0].date()), days=len(dd), med_dv=float(dd.median()),
                         med_dv_2025=float(dd[dd.index >= "2025-01-01"].median()), **yrs))
        print(p, len(s), f"{dd.median():,.0f}", flush=True)
    liq = pd.DataFrame(rows).sort_values("med_dv", ascending=False)
    liq.to_csv(scratch / "liquidity.csv", index=False)
    return liq


# ----------------------------------------------------------------------------- helpers
def bars(q: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample 15-min clean bars to `rule` on a full grid; `ok` = the bucket had a real trade."""
    g = pd.DataFrame({"o": q["o"].resample(rule).first(), "h": q["h"].resample(rule).max(),
                      "l": q["l"].resample(rule).min(), "c": q["c"].resample(rule).last(),
                      "dv": q["dv"].resample(rule).sum(), "nm": q["nm"].resample(rule).sum()})
    g["ok"] = g["c"].notna()
    return g


def fwd(c: pd.Series, k: int) -> pd.Series:
    """log return from bar t close to bar t+k close (both real; NaN otherwise)."""
    return np.log(c.shift(-k) / c)


def tstat_day(x: pd.Series) -> tuple[float, float, int]:
    """Day-weighted mean (mean of per-UTC-day means, so one mania day cannot dominate) and its t."""
    x = x.dropna()
    if len(x) < 10:
        return np.nan, np.nan, len(x)
    d = x.groupby(x.index.floor("D")).mean()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 else np.nan
    return float(d.mean()), float(t), len(x)


def bps(x) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x * 1e4:+.0f}"


def regime_of(ix: pd.DatetimeIndex) -> np.ndarray:
    out = np.full(len(ix), "", dtype=object)
    for k, (a, b) in REGIMES.items():
        out[(ix >= pd.Timestamp(a, tz="UTC")) & (ix < pd.Timestamp(b, tz="UTC"))] = k
    return out


def session_of(ix: pd.DatetimeIndex) -> np.ndarray:
    h = ix.hour + ix.minute / 60
    wk = ix.dayofweek >= 5
    out = np.where(h < 8, "Asia", np.where(h < 13.5, "EU", np.where(h < 20, "US", "Late")))
    return np.where(wk, "Weekend", out)


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def costs(top: list[str]) -> dict:
    tk, mk = CostModel(), CostModel.maker()
    return {p: {"taker": tk.round_trip(p, 2026), "maker": mk.round_trip(p, 2026),
                "taker25": tk.round_trip(p, 2025)} for p in top}


# ----------------------------------------------------------------------------- stage 2: analyze
def load(scratch: Path, top: list[str]) -> dict:
    Q = {p: pd.read_parquet(scratch / f"{p}_15m.parquet").astype("float64") for p in top}
    H = {}
    for p, q in Q.items():
        h = bars(q, "1h")
        h["r"] = np.log(h["c"] / h["c"].shift(1))
        sd = h["r"].rolling(720, min_periods=200).std().shift(1)     # trailing 30-day sigma, no look-ahead
        h["z"] = h["r"] / sd
        H[p] = h
    return {"Q": Q, "H": H}


def vol_tables(Q, H, top, C):
    a, b = [], []
    for p in top:
        q = Q[p]
        d = bars(q, "1D")
        rd = np.log(d["c"] / d["c"].shift(1))
        row = {"coin": p, "daily σ %": f"{rd.std() * 100:.1f}"}
        for lab, rule in (("1h", "1h"), ("4h", "4h"), ("1d", "1D")):
            g = bars(q, rule)
            pc = g["c"].shift(1)
            tr = pd.concat([g["h"] - g["l"], (g["h"] - pc).abs(), (g["l"] - pc).abs()], axis=1).max(axis=1)
            row[f"ATR {lab} %"] = f"{(tr / g['c']).median() * 100:.2f}"
        rng = (d["h"] / d["l"] - 1).dropna()
        row["day range med / p90 %"] = f"{rng.median() * 100:.1f} / {rng.quantile(.9) * 100:.1f}"
        row["RT cost taker / maker %"] = f"{C[p]['taker'] * 100:.2f} / {C[p]['maker'] * 100:.2f}"
        row["ATR4h / taker cost"] = f"{float(row['ATR 4h %']) / (C[p]['taker'] * 100):.1f}"
        a.append(row)
        rb = {"coin": p}
        for k in (1, 4, 12):
            g = bars(q, f"{k}h")
            r = np.log(g["c"] / g["c"].shift(1)).dropna().abs()
            for x in (0.02, 0.03, 0.05):
                rb[f"{k}h≥{int(x * 100)}%"] = f"{(r >= np.log1p(x)).mean() * 100:.1f}"
        b.append(rb)
    return pd.DataFrame(a), pd.DataFrame(b)


def tod(H, top):
    """Hour-of-day profile: per coin volume share, relative |r|, mean/median r; pooled = mean over coins."""
    per = []
    for p in top:
        h = H[p]
        x = pd.DataFrame({"hr": h.index.hour, "dv": h["dv"], "ar": h["r"].abs(), "r": h["r"]}, index=h.index)
        g = x.groupby("hr")
        per.append(pd.DataFrame({"coin": p, "vs": g["dv"].sum() / x["dv"].sum(), "rv": g["ar"].mean() / x["ar"].mean(),
                                 "mr": g["r"].mean(), "md": g["r"].median()}))
    per = pd.concat(per)
    pooled = per.groupby(level=0)[["vs", "rv", "mr", "md"]].mean()
    # day-clustered t of the pooled (coin-averaged) hourly return
    R = pd.concat({p: H[p]["r"] for p in top}, axis=1).mean(axis=1)
    t = {hr: tstat_day(R[R.index.hour == hr])[1] for hr in range(24)}
    pooled["t"] = pd.Series(t)
    btc = per[per["coin"] == "BTC"]
    pooled["btc_mr"] = btc["mr"]
    return pooled, per, R


def windows_table(H, Q, top):
    """Weekend/weekday, sessions, funding hours, Friday 08 UTC expiry: |1h r| ratio and mean 1h r (pooled)."""
    A = pd.concat({p: H[p]["r"] for p in top}, axis=1)
    base = A.abs().stack().mean()
    ix = A.index
    hr, dow = ix.hour, ix.dayofweek
    last_fri = (dow == 4) & ((ix + pd.Timedelta(days=7)).month != ix.month)
    # funding resets at 00/08/16 UTC: the hour starting at the reset and the hour before it
    fund = np.isin(hr, [23, 0, 7, 8, 15, 16])
    masks = {
        "Weekday (Mon-Fri)": dow < 5, "Weekend (Sat-Sun)": dow >= 5,
        "Asia 00-08 wkday": (hr < 8) & (dow < 5), "EU 08-13 wkday": (hr >= 8) & (hr < 13) & (dow < 5),
        "US 13-20 wkday": (hr >= 13) & (hr < 20) & (dow < 5), "Late 20-24 wkday": (hr >= 20) & (dow < 5),
        "Funding ±1h (23,00,07,08,15,16)": fund, "Other hours": ~fund,
        "Fri 07-09 (Deribit expiry)": (dow == 4) & np.isin(hr, [7, 8]),
        "Mon-Thu 07-09": (dow < 4) & np.isin(hr, [7, 8]),
        "Last Fri of month 07-09": last_fri & np.isin(hr, [7, 8]),
    }
    dvt = pd.concat({p: H[p]["dv"] for p in top}, axis=1)
    rows = []
    for k, m in masks.items():
        sub = A[m]
        s = sub.stack()
        mean, t, n = tstat_day(s.reset_index(level=1, drop=True))
        rows.append({"window (UTC)": k, "|1h r| vs all": f"{s.abs().mean() / base:.2f}",
                     "$vol share": f"{dvt[m].sum().sum() / dvt.sum().sum() * 100:.0f}%" if m.mean() < .99 else "—",
                     "hours share": f"{m.mean() * 100:.0f}%", "mean 1h r bps (t)": f"{bps(mean)} ({t:.1f})", "n": n})
    return pd.DataFrame(rows)


def dow_table(Q, top):
    rows = {}
    for p in top:
        d = bars(Q[p], "1D")
        rd = np.log(d["c"] / d["c"].shift(1))
        rows[p] = pd.DataFrame({"r": rd, "dv": d["dv"], "dow": d.index.dayofweek})
    X = pd.concat(rows)
    g = X.groupby("dow")
    tt = {k: tstat_day(v["r"].droplevel(0))[1] for k, v in g}
    out = pd.DataFrame({"mean bps": g["r"].mean() * 1e4, "t": pd.Series(tt), "σ %": g["r"].std() * 100,
                        "$vol share %": g["dv"].sum() / X["dv"].sum() * 100})
    out.index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return out


def autocorr(Q, top, regimes=False):
    out = {}
    for p in top:
        row = {}
        for lab, rule in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"), ("1d", "1D")):
            g = bars(Q[p], rule)
            r = np.log(g["c"] / g["c"].shift(1))
            if regimes:
                reg = regime_of(r.index)
                for k in REGIMES:
                    m = reg == k
                    row[(lab, k)] = r[m].autocorr(1)
            else:
                row[lab] = r.autocorr(1)
                row[lab + " n"] = int(pd.concat([r, r.shift(1)], axis=1).dropna().shape[0])
        out[p] = row
    return pd.DataFrame(out).T


def big_moves(H, top, zmin=2.0):
    """1h |z| >= zmin (trailing 30-day sigma): forward 1/4/12h log return from that hour's close, signed by the
    move's direction (+ = continuation)."""
    ev = []
    for p in top:
        h = H[p]
        m = h["z"].abs() >= zmin
        e = pd.DataFrame({"coin": p, "dir": np.sign(h.loc[m, "r"]), "z": h.loc[m, "z"]}, index=h.index[m])
        for k in (1, 4, 12):
            e[f"f{k}"] = fwd(h["c"], k)[m] * e["dir"]
        e["f1_4"] = np.log(h["c"].shift(-4) / h["c"].shift(-1))[m] * e["dir"]   # skips the first hour (bounce)
        e["sess"] = session_of(e.index)
        e["reg"] = regime_of(e.index)
        ev.append(e)
    return pd.concat(ev)


def baseline_fwd(H, top):
    """Unconditional mean forward return (long), for the same horizons."""
    out = {}
    for k in (1, 4, 12):
        out[k] = pd.concat([fwd(H[p]["c"], k) for p in top]).mean()
    return out


def asia_breakout(H, top):
    rows = []
    for p in top:
        h = H[p]
        for day, g in h.groupby(h.index.floor("D")):
            a = g[g.index.hour < 8]
            if a["ok"].sum() < 6:
                continue
            hi, lo = a["h"].max(), a["l"].min()
            s = g[(g.index.hour >= 8) & (g.index.hour < 20) & g["ok"]]
            if len(s) < 6:
                continue
            up = s.index[s["h"] > hi]
            dn = s.index[s["l"] < lo]
            tu = up[0] if len(up) else None
            td = dn[0] if len(dn) else None
            first = None
            if tu is not None and (td is None or tu < td):
                first, lvl, sg = tu, hi, 1
            elif td is not None and (tu is None or td < tu):
                first, lvl, sg = td, lo, -1
            both = tu is not None and td is not None
            if first is None:
                rows.append({"coin": p, "day": day, "brk": 0, "both": both})
                continue
            close20 = s["c"].iloc[-1]
            after = s[s.index >= first]
            mfe = (after["h"].max() / lvl - 1) if sg > 0 else (1 - after["l"].min() / lvl)
            rows.append({"coin": p, "day": day, "brk": sg, "both": both, "rng": hi / lo - 1,
                         "ret": sg * np.log(close20 / lvl), "beyond": (close20 - lvl) * sg > 0, "mfe": mfe})
    return pd.DataFrame(rows)


def cme_gap(H, top):
    rows = []
    for p in top:
        h = H[p]
        c = h["c"].ffill(limit=1)     # last trade, at most 1 hour stale
        fris = h.index[(h.index.dayofweek == 4) & (h.index.hour == 20)]      # hour 20:00-21:00 close = 21:00
        for f in fris:
            sun = f + pd.Timedelta(days=2, hours=2)                           # Sun 22:00-23:00 bar close = 23:00
            if sun not in c.index or not (np.isfinite(c.get(f, np.nan)) and np.isfinite(c.get(sun, np.nan))):
                continue
            pf, ps = c[f], c[sun]
            gap = ps / pf - 1
            nxt = h[(h.index > sun) & (h.index <= sun + pd.Timedelta(hours=48))]
            if nxt["ok"].sum() < 12:
                continue
            mirror = ps * (1 + gap)                                           # same distance, other side
            r = {"coin": p, "t": f, "gap": gap, "reg": regime_of(pd.DatetimeIndex([f]))[0]}
            for hz in (24, 48):
                w = nxt[nxt.index <= sun + pd.Timedelta(hours=hz)]
                if gap > 0:
                    r[f"fill{hz}"] = w["l"].min() <= pf
                    r[f"mir{hz}"] = w["h"].max() >= mirror
                else:
                    r[f"fill{hz}"] = w["h"].max() >= pf
                    r[f"mir{hz}"] = w["l"].min() <= mirror
            rows.append(r)
    return pd.DataFrame(rows)


def round_numbers(H, top):
    """Touches from below / above of round levels (multiples of 10^(floor(log10 p) - 1)) vs control levels at
    +0.37 step (not round). Outcome: share of 4h-later closes beyond the level (break held) and mean signed
    return from the level to that close."""
    rows = []
    for p in top:
        h = H[p]
        pc = h["c"].shift(1)
        step = 10.0 ** (np.floor(np.log10(pc)) - 1)
        f4 = h["c"].shift(-4)
        for kind, off in (("round", 0.0), ("control", 0.37)):
            # first level above the previous close
            lv_up = (np.floor((pc / step) - off) + 1 + off) * step
            lv_dn = (np.ceil((pc / step) - off) - 1 + off) * step
            up = (h["h"] >= lv_up) & (lv_up > pc)
            dn = (h["l"] <= lv_dn) & (lv_dn < pc)
            for side, m, lv, sg in (("from below", up, lv_up, 1), ("from above", dn, lv_dn, -1)):
                m = m & f4.notna()
                rr = sg * np.log(f4[m] / lv[m])
                rows.append({"coin": p, "kind": kind, "side": side, "n": int(m.sum()),
                             "held": float((rr > 0).mean()), "ret": float(rr.mean()),
                             "dist": float(((lv[m] - pc[m]).abs() / pc[m]).mean())})
    return pd.DataFrame(rows)


def wicks(H, top):
    ev = []
    for p in top:
        h = H[p]
        rng = h["h"] - h["l"]
        lw = (np.minimum(h["o"], h["c"]) - h["l"]) / rng.where(rng > 0)
        m = (h["z"] <= -3)
        e = pd.DataFrame({"coin": p, "wick": lw[m] >= 0.5, "z": h["z"][m]}, index=h.index[m])
        for k in (1, 4, 12):
            e[f"f{k}"] = fwd(h["c"], k)[m]
        e["reg"] = regime_of(e.index)
        ev.append(e)
    return pd.concat(ev)


def cross(Q, H, top):
    """Beta / corr of 1h and 1d returns to BTC by BTC regime (daily close above / below its SMA50, known at the
    previous day's close), plus lead-lag correlations at 1h and 4h."""
    bd = bars(Q["BTC"], "1D")["c"]
    up = (bd > bd.rolling(50, min_periods=50).mean()).shift(1)
    rows, ll = [], []
    for lab, rule in (("1h", "1h"), ("4h", "4h")):
        B = bars(Q["BTC"], rule)["c"]
        rb = np.log(B / B.shift(1))
        for p in top:
            if p == "BTC":
                continue
            A = bars(Q[p], rule)["c"]
            ra = np.log(A / A.shift(1))
            X = pd.DataFrame({"a": ra, "b": rb, "b1": rb.shift(1), "a1": ra.shift(1)})
            reg = up.reindex(X.index.floor("D")).to_numpy()
            X["up"] = reg
            if lab == "1h":
                r = {"coin": p}
                for nm, msk in (("BTC up-trend", X["up"] == True), ("BTC down-trend", X["up"] == False)):
                    Y = X[msk][["a", "b"]].dropna()
                    r[f"β {nm}"] = Y["a"].cov(Y["b"]) / Y["b"].var()
                    r[f"ρ {nm}"] = Y["a"].corr(Y["b"])
                rows.append(r)
            Y = X.dropna(subset=["a", "b1"])
            Z = X.dropna(subset=["b", "a1"])
            ll.append({"coin": p, "tf": lab, "ρ(alt_t, btc_t-1)": Y["a"].corr(Y["b1"]),
                       "ρ(btc_t, alt_t-1)": Z["b"].corr(Z["a1"]), "ρ(alt_t, alt_t-1)": X["a"].autocorr(1)})
    return pd.DataFrame(rows), pd.DataFrame(ll)


def btc_lead_events(H, top):
    """After a BTC 1h |z| >= 2 hour, the alt's NEXT 1h / 4h log return signed by BTC's direction; split by whether
    the alt already moved >= half of BTC's move in that same hour ('lagging' alts did not)."""
    hb = H["BTC"]
    m = hb["z"].abs() >= 2
    rows = []
    for p in top:
        if p == "BTC":
            continue
        h = H[p]
        e = pd.DataFrame({"dir": np.sign(hb["r"][m]), "br": hb["r"][m]})
        e["ar"] = h["r"].reindex(e.index)
        for k in (1, 4):
            e[f"f{k}"] = fwd(h["c"], k).reindex(e.index) * e["dir"]
        e["lag"] = (e["ar"] * e["dir"]) < 0.5 * e["br"].abs()
        e["nm"] = h["nm"].reindex(e.index)            # alt traded minutes in the BTC shock hour
        e["coin"] = p
        rows.append(e)
    return pd.concat(rows)


def eth_btc(Q):
    e, b = bars(Q["ETH"], "1D")["c"], bars(Q["BTC"], "1D")["c"]
    r = (e / b).dropna()
    out = []
    for k, (a, z) in REGIMES.items():
        s = r[(r.index >= a) & (r.index < z)]
        if len(s) < 30:
            continue
        r30 = np.log(s / s.shift(30))
        out.append({"regime": k, "ETH/BTC start→end": f"{s.iloc[0]:.4f}→{s.iloc[-1]:.4f}",
                    "change %": f"{(s.iloc[-1] / s.iloc[0] - 1) * 100:+.0f}",
                    "days above SMA50 %": f"{((s > s.rolling(50).mean()).iloc[50:].mean()) * 100:.0f}",
                    "ρ(30d, next 30d)": f"{r30.corr(r30.shift(-30)):+.2f}"})
    return pd.DataFrame(out), r


def spy(Q, top):
    """SPY 1-min (equity cache) RTH: per day open->close and the crypto log return over the same UTC window."""
    fs = [ROOT / "data" / "cache_fresh" / "1Min" / "SPY.parquet", ROOT / "data" / "cache_hist" / "1Min" / "SPY.parquet"]
    alt = Path("/home/user/MCF/data")
    fs += [alt / "cache_fresh" / "1Min" / "SPY.parquet", alt / "cache_hist" / "1Min" / "SPY.parquet"]
    parts = [pd.read_parquet(f) for f in fs if f.exists()]
    s = pd.concat(parts)
    s.index = s.index.tz_convert("UTC")
    s = s[~s.index.duplicated()].sort_index()
    s = s[s.index < END]
    d = s.groupby(s.index.floor("D")).agg(t0=("open", lambda x: x.index[0]), t1=("close", lambda x: x.index[-1]),
                                          o=("open", "first"), c=("close", "last"))
    d["spy"] = np.log(d["c"] / d["o"])
    c60 = s["close"].groupby(s.index.floor("D")).apply(lambda x: x.iloc[59] if len(x) > 60 else np.nan)
    d["spy1"] = np.log(c60 / d["o"])
    d = d[(d["t1"] - d["t0"]) >= pd.Timedelta(hours=6)]
    rows = []
    for p in top:
        # crypto price at the window edges: last trade at/before t0 and t1 (15-min grid, stale <= 30 min)
        c = Q[p]["c"].resample("15min").last().ffill(limit=2)
        x0 = c.reindex((d["t0"] - pd.Timedelta(minutes=15)).dt.floor("15min")).to_numpy()
        x1 = c.reindex(d["t1"].dt.floor("15min")).to_numpy()
        cr = pd.Series(np.log(x1 / x0), index=d.index)
        X = pd.DataFrame({"spy": d["spy"], "cr": cr}).dropna()
        r = {"coin": p, "days": len(X), "ρ RTH": X["spy"].corr(X["cr"]),
             "β RTH": X["spy"].cov(X["cr"]) / X["spy"].var()}
        for k in ("2023", "2024", "2025"):
            Y = X[X.index.year == int(k)]
            r[f"ρ {k}"] = Y["spy"].corr(Y["cr"])
        dn, upd = X[X["spy"] <= -0.01], X[X["spy"] >= 0.01]
        r["crypto on SPY ≤ -1% days bps"] = dn["cr"].mean()
        r["crypto on SPY ≥ +1% days bps"] = upd["cr"].mean()
        r["n ≤-1/≥+1"] = f"{len(dn)}/{len(upd)}"
        # does SPY's first RTH hour lead crypto's rest of the session? (14:30 -> close, same UTC window)
        xm = c.reindex((d["t0"] + pd.Timedelta(minutes=45)).dt.floor("15min")).to_numpy()
        s1 = d["spy1"]
        Z = pd.DataFrame({"s1": s1, "rest": np.log(x1 / xm)}, index=d.index).dropna()
        r["ρ(SPY 1st hr, crypto rest)"] = Z["s1"].corr(Z["rest"])
        rows.append(r)
    return pd.DataFrame(rows), d


def f2(x, d=2):
    return "—" if x is None or not np.isfinite(x) else f"{x:+.{d}f}"


def analyze(scratch: Path, out: Path) -> None:
    liq = pd.read_csv(scratch / "liquidity.csv")
    top = liq["pair"].head(10).tolist()
    C = costs(top)
    L = load(scratch, top)
    Q, H = L["Q"], L["H"]
    T = []          # (title, markdown)
    res = {"top": top}

    # coverage + liquidity
    cov = []
    for p in top:
        h = H[p]
        r = {"coin": p, "med daily $ vol": f"{liq.set_index('pair').loc[p, 'med_dv']:,.0f}",
             "since 2025": f"{liq.set_index('pair').loc[p, 'med_dv_2025']:,.0f}"}
        for k, (a, b) in REGIMES.items():
            s = h["ok"][(h.index >= a) & (h.index < b)]
            r[f"hrs traded {k}"] = f"{s.mean() * 100:.0f}%" if len(s) else "—"
        cov.append(r)
    T.append(("Top 10 + traded-hour coverage", md(pd.DataFrame(cov))))

    va, vb = vol_tables(Q, H, top, C)
    T.append(("Volatility", md(va)))
    T.append(("Move frequency (% of non-overlapping windows with |close-close| ≥ X)", md(vb)))

    pooled, per, R = tod(H, top)
    res["tod"] = pooled
    blk = pooled.copy()
    blk["blk"] = blk.index // 3
    g = blk.groupby("blk")
    tb = pd.DataFrame({"hours UTC": [f"{3 * i:02d}-{3 * i + 3:02d}" for i in range(8)],
                       "$vol share %": [f"{v * 100:.1f}" for v in g["vs"].sum()],
                       "rel |1h r|": [f"{v:.2f}" for v in g["rv"].mean()],
                       "mean 1h r bps": [bps(v) for v in g["mr"].mean()],
                       "median bps": [bps(v) for v in g["md"].mean()],
                       "t (day-clust)": [f"{tstat_day(R[R.index.hour // 3 == i])[1]:+.1f}" for i in range(8)],
                       "BTC mean bps": [bps(v) for v in g["btc_mr"].mean()]})
    T.append(("Time of day (pooled top 10, 3-h blocks)", md(tb)))
    hrs = pooled.sort_values("t")
    T.append(("Hour extremes", md(pd.DataFrame({"hour": hrs.index, "mean bps": [bps(v) for v in hrs["mr"]],
                                                   "t": [f"{v:+.1f}" for v in hrs["t"]]}).iloc[[0, 1, 2, -3, -2, -1]])))
    T.append(("Windows", md(windows_table(H, Q, top))))
    dw = dow_table(Q, top)
    T.append(("Day of week (daily 00 UTC close-close, pooled)", md(dw.round(2).reset_index())))

    # structure
    ac = autocorr(Q, top)
    T.append(("Lag-1 autocorrelation", md(ac.map(lambda v: f"{v:+.3f}" if isinstance(v, float) else v)
                                           .reset_index().rename(columns={"index": "coin"}))))
    acr = autocorr(Q, top, regimes=True)
    acr_m = acr.astype(float).median()
    T.append(("Autocorr by regime (median over coins)",
              md(acr_m.unstack().map(lambda v: f"{v:+.3f}").reset_index().rename(columns={"index": "tf"}))))

    bm = big_moves(H, top)
    base = baseline_fwd(H, top)
    rows = []
    for (nm, m) in (("all", bm.index == bm.index), ("up moves", bm["dir"] > 0), ("down moves", bm["dir"] < 0)):
        e = bm[m]
        r = {"set": nm, "n": len(e)}
        for k in (1, 4, 12):
            mu, t, _ = tstat_day(e[f"f{k}"])
            r[f"+{k}h signed bps (t)"] = f"{bps(mu)} ({t:+.1f})"
            r[f"+{k}h cont %"] = f"{(e[f'f{k}'].dropna() > 0).mean() * 100:.0f}"
            r[f"+{k}h median"] = bps(e[f"f{k}"].median())
        rows.append(r)
    for s_ in ("Asia", "EU", "US", "Late", "Weekend"):
        for d_, lab in ((1, "up"), (-1, "down")):
            e = bm[(bm["sess"] == s_) & (bm["dir"] == d_)]
            r = {"set": f"{s_} {lab}", "n": len(e)}
            for k in (1, 4, 12):
                mu, t, _ = tstat_day(e[f"f{k}"])
                r[f"+{k}h signed bps (t)"] = f"{bps(mu)} ({t:+.1f})"
                r[f"+{k}h cont %"] = f"{(e[f'f{k}'].dropna() > 0).mean() * 100:.0f}"
            rows.append(r)
    T.append(("After a ≥2σ 1h move (signed: + = continuation)", md(pd.DataFrame(rows))))
    T.append(("Unconditional long fwd bps", str({k: bps(v) for k, v in base.items()})))
    rr = []
    for k in REGIMES:
        for d_, lab in ((1, "up"), (-1, "down")):
            e = bm[(bm["reg"] == k) & (bm["dir"] == d_)]
            mu4, t4, _ = tstat_day(e["f4"])
            mu12, t12, _ = tstat_day(e["f12"])
            rr.append({"regime": k, "dir": lab, "n": len(e), "+4h bps (t)": f"{bps(mu4)} ({t4:+.1f})",
                       "+12h bps (t)": f"{bps(mu12)} ({t12:+.1f})"})
    T.append(("2σ moves by regime", md(pd.DataFrame(rr))))
    rows = []
    for p in top:
        e = bm[(bm["coin"] == p) & (bm["dir"] < 0)]
        mu, t, _ = tstat_day(-e["f4"])
        mu2, t2, _ = tstat_day(-e["f1_4"])
        rows.append({"coin": p, "n down ≥2σ": len(e), "bounce +4h bps (t)": f"{bps(mu)} ({t:+.1f})",
                     "median": bps(-e["f4"].median()), "bounce h+1→h+4 bps (t)": f"{bps(mu2)} ({t2:+.1f})",
                     "taker / maker cost bps": f"{C[p]['taker'] * 1e4:.0f} / {C[p]['maker'] * 1e4:.0f}"})
    T.append(("Down-shock bounce per coin (long side)", md(pd.DataFrame(rows))))
    res["bm"] = bm

    ab = asia_breakout(H, top)
    ab["reg"] = regime_of(pd.DatetimeIndex(ab["day"]))
    rows = []
    for k in ["all"] + list(REGIMES):
        a = ab if k == "all" else ab[ab["reg"] == k]
        b_ = a[a["brk"] != 0]
        for d_, lab in ((1, "up"), (-1, "down")):
            e = b_[b_["brk"] == d_].set_index("day")
            mu, t, _ = tstat_day(e["ret"])
            rows.append({"regime": k, "first break": lab, "days": len(a), "break %": f"{len(e) / len(a) * 100:.0f}",
                         "both sides %": f"{a['both'].mean() * 100:.0f}" if d_ == 1 else "",
                         "Asia range med %": f"{e['rng'].median() * 100:.1f}",
                         "level→20:00 bps (t)": f"{bps(mu)} ({t:+.1f})",
                         "close beyond %": f"{e['beyond'].astype(float).mean() * 100:.0f}",
                         "median bps": bps(e["ret"].median()),
                         "MFE med %": f"{e['mfe'].median() * 100:.1f}"})
    T.append(("Asia-range (00-08) breakouts, 08-20 UTC", md(pd.DataFrame(rows))))

    cg = cme_gap(H, top)
    rows = []
    for coinset, sub in (("BTC", cg[cg["coin"] == "BTC"]), ("ETH", cg[cg["coin"] == "ETH"]), ("top 10", cg)):
        for lo, hi, lab in ((0, .005, "<0.5%"), (.005, .02, "0.5-2%"), (.02, 9, "≥2%")):
            e = sub[(sub["gap"].abs() >= lo) & (sub["gap"].abs() < hi)]
            if not len(e):
                continue
            rows.append({"coins": coinset, "|gap|": lab, "n": len(e), "fill 24h %": f"{e['fill24'].mean() * 100:.0f}",
                         "mirror 24h %": f"{e['mir24'].mean() * 100:.0f}", "fill 48h %": f"{e['fill48'].mean() * 100:.0f}",
                         "mirror 48h %": f"{e['mir48'].mean() * 100:.0f}"})
    T.append(("CME weekend gap (Fri 21:00 → Sun 23:00 UTC)", md(pd.DataFrame(rows))))
    rows = []
    for k in REGIMES:
        e = cg[(cg["reg"] == k) & (cg["gap"].abs() >= .005)]
        rows.append({"regime": k, "n (|gap|≥0.5%)": len(e), "fill 24h %": f"{e['fill24'].mean() * 100:.0f}",
                     "mirror 24h %": f"{e['mir24'].mean() * 100:.0f}"})
    T.append(("CME gap by regime", md(pd.DataFrame(rows))))

    rn = round_numbers(H, top)
    g = rn.groupby(["kind", "side"]).apply(lambda x: pd.Series({
        "n": int(x["n"].sum()), "held 4h %": f"{np.average(x['held'], weights=x['n']) * 100:.1f}",
        "level→+4h bps": bps(np.average(x["ret"], weights=x["n"])),
        "dist from prev close %": f"{np.average(x['dist'], weights=x['n']) * 100:.2f}"}), include_groups=False)
    T.append(("Round-number touches (hourly)", md(g.reset_index())))

    wk = wicks(H, top)
    rows = []
    for nm, e in (("≤-3σ, lower wick ≥50%", wk[wk["wick"]]), ("≤-3σ, no long wick", wk[~wk["wick"]])):
        r = {"1h drop": nm, "n": len(e)}
        for k in (1, 4, 12):
            mu, t, _ = tstat_day(e[f"f{k}"])
            r[f"+{k}h bps (t)"] = f"{bps(mu)} ({t:+.1f})"
            r[f"+{k}h med"] = bps(e[f"f{k}"].median())
        r["+12h up %"] = f"{(e['f12'].dropna() > 0).mean() * 100:.0f}"
        rows.append(r)
    maj = wk["coin"].isin(["BTC", "ETH"])
    for nm, e in [("all ≤-3σ, BTC+ETH", wk[maj]), ("all ≤-3σ, 8 alts", wk[~maj])] + \
            [(f"all ≤-3σ, {k}", wk[wk["reg"] == k]) for k in REGIMES]:
        r = {"1h drop": nm, "n": len(e)}
        for k in (4, 12):
            mu, t, _ = tstat_day(e[f"f{k}"])
            r[f"+{k}h bps (t)"] = f"{bps(mu)} ({t:+.1f})"
            r[f"+{k}h med"] = bps(e[f"f{k}"].median())
        rows.append(r)
    T.append(("Flush + wick (1h z ≤ -3)", md(pd.DataFrame(rows).fillna(""))))

    # cross-asset
    cb, ll = cross(Q, H, top)
    T.append(("Beta / corr to BTC, 1h returns, by BTC regime", md(cb.round(2))))
    T.append(("Lead-lag", md(ll.groupby("tf")[["ρ(alt_t, btc_t-1)", "ρ(btc_t, alt_t-1)", "ρ(alt_t, alt_t-1)"]]
                             .median().round(3).reset_index())))
    T.append(("Lead-lag per coin", md(ll.round(3))))
    be = btc_lead_events(H, top)
    rows = []
    act = be["nm"] >= 15
    for nm, e in (("all alts", be), ("alt lagged (moved < ½ BTC)", be[be["lag"]]), ("alt kept up", be[~be["lag"]]),
                  ("lagged, alt traded ≥15 min that hour", be[be["lag"] & act]),
                  ("lagged, alt traded <15 min (stale print)", be[be["lag"] & ~act])):
        r = {"after BTC ≥2σ hour": nm, "n": int(e["f1"].notna().sum())}
        for k in (1, 4):
            mu, t, _ = tstat_day(e[f"f{k}"])
            r[f"alt +{k}h signed bps (t)"] = f"{bps(mu)} ({t:+.1f})"
        rows.append(r)
    T.append(("BTC shock → alt next hours", md(pd.DataFrame(rows))))
    eb, ratio = eth_btc(Q)
    T.append(("ETH/BTC", md(eb)))
    sp, _ = spy(Q, top)
    sp2 = sp.copy()
    for c_ in sp2.columns:
        if "bps" in c_:
            sp2[c_] = sp2[c_].map(bps)
        elif c_.startswith(("ρ", "β")):
            sp2[c_] = sp2[c_].map(lambda v: f"{v:+.2f}")
    T.append(("SPY RTH vs crypto same window", md(sp2)))

    # regime stability of time-of-day / weekend
    rows = []
    A = pd.concat({p: H[p]["r"] for p in top}, axis=1)
    reg = regime_of(A.index)
    prof = {}
    for k in REGIMES:
        S = A[reg == k]
        ab_ = S.abs()
        wkend = ab_[S.index.dayofweek >= 5].stack().mean() / ab_[S.index.dayofweek < 5].stack().mean()
        hr = S.index.hour
        us = ab_[(hr >= 13) & (hr < 20) & (S.index.dayofweek < 5)].stack().mean() / ab_.stack().mean()
        prof[k] = S.mean(axis=1).groupby(hr).mean()
        rows.append({"regime": k, "weekend/weekday |1h r|": f"{wkend:.2f}", "US-hours |1h r| vs all": f"{us:.2f}",
                     "mean 1h r bps (all hrs)": bps(S.stack().mean())})
    P = pd.DataFrame(prof)
    T.append(("Regime: weekend / US hours", md(pd.DataFrame(rows))))
    T.append(("Corr of 24-h mean-return profiles across regimes", md(P.corr().round(2).reset_index())))
    res["prof"] = P

    with open(scratch / "tables.md", "w") as f:
        f.writelines(f"\n### {t_}\n{m_}\n" for t_, m_ in T)
    charts(out, pooled, per, vb, C, top, ratio, bm, P)
    print((scratch / "tables.md").read_text())


# ----------------------------------------------------------------------------- charts
SURF, INK, INK2, BLUE, ORANGE, RED = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#eb6834", "#e34948"


def _ax(ax, title):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="y", color="#e4e3df", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", color=INK, fontsize=10)


def charts(out, pooled, per, vb, C, top, ratio, bm, P):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    note = "Educational only — not financial advice. Alpaca clean traded bars, 2021-01..2026-05-25 (FIT+CHECK)."
    # 1 hour-of-day
    fig, axs = plt.subplots(3, 1, figsize=(8, 7.5), sharex=True, facecolor=SURF)
    x = np.arange(24)
    axs[0].bar(x, pooled["vs"] * 100, color=BLUE, width=0.8)
    _ax(axs[0], "Share of daily $ volume by UTC hour (%, mean of top-10 coins)")
    axs[1].bar(x, pooled["rv"], color=BLUE, width=0.8)
    axs[1].axhline(1, color=INK2, lw=0.8)
    _ax(axs[1], "Mean |1h return| relative to the coin's all-hours mean")
    axs[2].bar(x, pooled["mr"] * 1e4, color=[BLUE if v >= 0 else ORANGE for v in pooled["mr"]], width=0.8)
    axs[2].axhline(0, color=INK2, lw=0.8)
    _ax(axs[2], "Mean 1h return, bps (taker round trip ≈ 55-100 bps; maker ≈ 45-70)")
    for a in axs:
        for h in (13.5, 20):
            a.axvline(h - 0.5, color=INK2, lw=0.6, ls=":")
    axs[2].set_xticks(x)
    axs[2].set_xlabel("UTC hour (dotted: US equity session 13:30-20:00)", color=INK2, fontsize=8)
    fig.text(0.01, 0.005, note, fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out / "hour_profile.png", dpi=200, facecolor=SURF)
    plt.close(fig)
    # 2 move frequency vs cost
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=SURF)
    w = 0.38
    xi = np.arange(len(top))
    v2 = vb["4h≥2%"].astype(float).to_numpy()
    v5 = vb["4h≥5%"].astype(float).to_numpy()
    ax.bar(xi - w / 2, v2, w, color=BLUE, label="|4h move| ≥ 2%")
    ax.bar(xi + w / 2, v5, w, color=ORANGE, label="|4h move| ≥ 5%")
    for i, p in enumerate(top):
        ax.text(i, max(v2[i], v5[i]) + 0.8, f"cost {C[p]['taker'] * 100:.2f}%", ha="center", fontsize=6.5, color=INK2)
    ax.set_xticks(xi, top)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK)
    _ax(ax, "% of 4-hour windows with a close-to-close move ≥ 2% / ≥ 5% (label: taker round-trip cost)")
    fig.text(0.01, 0.005, note, fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out / "move_frequency.png", dpi=200, facecolor=SURF)
    plt.close(fig)
    # 3 ETH/BTC
    fig, ax = plt.subplots(figsize=(8, 3.4), facecolor=SURF)
    ax.plot(ratio.index, ratio.values, color=BLUE, lw=1.5)
    ax.plot(ratio.index, ratio.rolling(50).mean().values, color=ORANGE, lw=1.2, label="50-day mean")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK)
    _ax(ax, "ETH/BTC daily ratio (Alpaca clean closes)")
    fig.text(0.01, 0.005, note, fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / "eth_btc.png", dpi=200, facecolor=SURF)
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    a = ap.parse_args(argv)
    sc = Path(a.scratch)
    if a.prep or not (sc / "liquidity.csv").exists():
        prep(sc)
    analyze(sc, Path(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
