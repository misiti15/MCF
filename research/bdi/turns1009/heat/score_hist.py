"""Part 3: does MarcoFlow's heat (V0 port, V2 as-run) anticipate turns, and what is its after-cost expectancy?
Lineage heat2-orig, N = 100 pre-declared configurations (HEAT.md section 2). Open two-year history only (lib.py; the
locked block is never loaded). One process, month by month. Writes results/orig_*.csv.
Educational only - not financial advice."""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402
from research.history2y.lib import daily, load_month, months, regimes  # noqa: E402

COMP = ["volumeHeat", "rsiHeat", "momentumHeat", "priceActionHeat", "trendHeat", "macdHeat", "vwapHeat"]
COMP_AR = [c + "_ar" for c in COMP + ["candleHeat"]]
REFS = {"SPY", "QQQ", "IWM", "DIA"}
import os
MODE = os.environ.get("HEAT_MODE", "R")   # "R": 1R = 0.25 x daily ATR (section 2); "P": 0.5% of price (amendment A1)
TAG = "" if MODE == "R" else "P_"
TRAIN_END = "2025-12"          # months <= this are train, later are valid
RES = HERE / "results"
V2DIR = HERE / "data" / "v2"
FCOLS = ["symbol", "date", "ts", "tod", "close", "high", "low", "atr_d", "heat", *COMP,
         "r_long_t1s1", "r_short_t1s1", "win_long_t1s1", "win_short_t1s1"]


def split_of(month: str) -> str:
    return "train" if month <= TRAIN_END else "valid"


# ----------------------------------------------------------------------------------------------- frame prep
def daily_table() -> pd.DataFrame:
    """Previous-day OHLC and the close 5 sessions before, per symbol-date (open history only; a prior day more than
    7 calendar days back - e.g. across the locked block - is set to NaN)."""
    d = daily()[["symbol", "date", "open", "high", "low", "close"]].sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    out = pd.DataFrame({"symbol": d.symbol, "date": d.date, "pO": g.open.shift(1), "pH": g.high.shift(1),
                        "pL": g.low.shift(1), "pC": g.close.shift(1), "pC5": g.close.shift(6)})
    gap = (pd.to_datetime(d.date) - pd.to_datetime(g.date.shift(1))).dt.days
    out.loc[gap > 7, ["pO", "pH", "pL", "pC", "pC5"]] = np.nan
    return out


def pct_outcomes(df: pd.DataFrame, pct: float = 0.005) -> dict:
    """Amendment A1 trade P: +-pct of the entry close, first touch on later 5-minute bars of the same session in the
    frame (both in one bar = loss), else exit at the session's last frame bar. Gross, in units of pct x close."""
    c, h, l = (df[k].to_numpy(float) for k in ("close", "high", "low"))
    key = df.symbol.astype(str).to_numpy() + df.date.astype(str).to_numpy()
    b = np.flatnonzero(np.r_[True, key[1:] != key[:-1], True])
    out = {k: np.full(len(df), np.nan) for k in ("r_long", "r_short", "win_long", "win_short")}
    for a, z in zip(b[:-1], b[1:]):
        cc, hh, ll = c[a:z], h[a:z], l[a:z]
        m = z - a
        rr = pct * cc
        later = np.triu(np.ones((m, m), bool), 1)
        for side, nm in ((1, "long"), (-1, "short")):
            up, dn = cc + side * rr, cc - side * rr
            hu = ((hh[None, :] >= up[:, None]) if side == 1 else (ll[None, :] <= up[:, None])) & later
            hd = ((ll[None, :] <= dn[:, None]) if side == 1 else (hh[None, :] >= dn[:, None])) & later
            big = m + 1
            fu = np.where(hu.any(1), np.argmax(hu, 1), big)
            fd = np.where(hd.any(1), np.argmax(hd, 1), big)
            won = fu < fd
            lost = (fd <= fu) & (fd < big)
            out[f"r_{nm}"][a:z] = np.where(won, 1.0, np.where(lost, -1.0, side * (cc[-1] - cc) / rr))
            out[f"win_{nm}"][a:z] = won.astype(float)
    return out



def prep(month: str, extra: list[str] | None = None) -> pd.DataFrame:
    df = load_month(month, FCOLS + [c for c in (extra or []) if c not in FCOLS])
    v2 = ds.dataset(str(V2DIR / f"month={month}"), format="parquet").to_table().to_pandas()
    df = df.merge(v2.drop(columns=["heat_v0"]), on=["symbol", "ts"], how="left")
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    for c in ["heat_v1", "heat_v2", "candleHeat", *COMP_AR]:
        df[c] = df[c].astype("float32")
    df["trade_ok"] = ~df.symbol.isin(REFS) & np.isfinite(df.r_long_t1s1) & (df.atr_d > 0)
    if MODE == "P":
        po = pct_outcomes(df)
    for side in ("long", "short"):
        if MODE == "P":
            df[f"pr_{side}"] = gates.prod_r(po[f"r_{side}"], po[f"win_{side}"], df["close"], 0.02 * df["close"], "t1s1",
                                            tod=df["tod"]).astype("float32")
        else:
            df[f"pr_{side}"] = gates.prod_r(df[f"r_{side}_t1s1"], df[f"win_{side}_t1s1"], df["close"], df["atr_d"], "t1s1",
                                            tod=df["tod"]).astype("float32")
        ok = df.trade_ok
        ctrl = df[ok].groupby(["date", "tod"])[f"pr_{side}"].mean().rename(f"ctrl_{side}")
        df = df.merge(ctrl, left_on=["date", "tod"], right_index=True, how="left")
    g = df.groupby(["symbol", "date"], sort=False)
    R = 0.25 * df.atr_d if MODE == "R" else 0.005 * df.close
    sh = lambda col, k: g[col].shift(k)
    hp = pd.concat([sh("high", k) for k in range(1, 5)], axis=1)
    lp = pd.concat([sh("low", k) for k in range(1, 5)], axis=1)
    hn = pd.concat([sh("high", -k) for k in range(1, 7)], axis=1)
    ln = pd.concat([sh("low", -k) for k in range(1, 7)], axis=1)
    elig = hp.notna().all(axis=1) & hn.notna().all(axis=1)
    top = elig & (df.high >= hp.max(axis=1)) & (df.high >= hn.max(axis=1)) & (df.high - lp.min(axis=1) >= R) & \
        (df.high - ln.min(axis=1) >= R)
    bot = elig & (df.low <= lp.min(axis=1)) & (df.low <= ln.min(axis=1)) & (hp.max(axis=1) - df.low >= R) & \
        (hn.max(axis=1) - df.low >= R)
    df["elig"] = elig.to_numpy()
    df["top"], df["bot"] = top.to_numpy(), bot.to_numpy()
    g = df.groupby(["symbol", "date"], sort=False)
    df["top_c"] = (top | g["top"].shift(1).fillna(False).astype(bool)).to_numpy()   # turn at i or i-1
    df["bot_c"] = (bot | g["bot"].shift(1).fillna(False).astype(bool)).to_numpy()
    for v, col in (("v0", "heat"), ("v2", "heat_v2")):
        df[f"d3_{v}"] = (df[col] - g[col].shift(3)).astype("float32")
        r = g[col].rolling(6, min_periods=1)
        df[f"max6_{v}"] = r.max().reset_index(level=[0, 1], drop=True).astype("float32")
        df[f"min6_{v}"] = r.min().reset_index(level=[0, 1], drop=True).astype("float32")
    df["bull_v0"] = (df[COMP] > 2).sum(axis=1).astype("int8")
    df["bear_v0"] = (df[COMP] < -2).sum(axis=1).astype("int8")
    df["bull_v2"] = (df[COMP_AR] > 2).sum(axis=1).astype("int8")
    df["bear_v2"] = (df[COMP_AR] < -2).sum(axis=1).astype("int8")
    return df


# ----------------------------------------------------------------------------------------------- configs
def configs():
    out = []
    for v, col in (("v0", "heat"), ("v2", "heat_v2")):
        for T in (20, 30, 40, 50):
            out.append((f"H1-{v}-fade{T}-short", "short", lambda d, c=col, T=T: d[c] >= T))
            out.append((f"H1-{v}-fade{T}-long", "long", lambda d, c=col, T=T: d[c] <= -T))
            out.append((f"H2-{v}-follow{T}-short", "short", lambda d, c=col, T=T: d[c] <= -T))
            out.append((f"H2-{v}-follow{T}-long", "long", lambda d, c=col, T=T: d[c] >= T))
        for D in (15, 25, 35):
            out.append((f"H3-{v}-chg{D}-short", "short", lambda d, v=v, D=D: d[f"d3_{v}"] <= -D))
            out.append((f"H3-{v}-chg{D}-long", "long", lambda d, v=v, D=D: d[f"d3_{v}"] >= D))
        for T in (30, 40):
            for D in (10, 20):
                out.append((f"H4-{v}-roll{T}_{D}-short", "short",
                            lambda d, v=v, c=col, T=T, D=D: (d[f"max6_{v}"] >= T) & (d[c] <= d[f"max6_{v}"] - D)))
                out.append((f"H4-{v}-roll{T}_{D}-long", "long",
                            lambda d, v=v, c=col, T=T, D=D: (d[f"min6_{v}"] <= -T) & (d[c] >= d[f"min6_{v}"] + D)))
        for A in (5, 6, 7):
            out.append((f"H5-{v}-agree{A}-fade-short", "short", lambda d, v=v, A=A: d[f"bull_{v}"] >= A))
            out.append((f"H5-{v}-agree{A}-fade-long", "long", lambda d, v=v, A=A: d[f"bear_{v}"] >= A))
            out.append((f"H5-{v}-agree{A}-follow-short", "short", lambda d, v=v, A=A: d[f"bear_{v}"] >= A))
            out.append((f"H5-{v}-agree{A}-follow-long", "long", lambda d, v=v, A=A: d[f"bull_{v}"] >= A))
    return out


# ----------------------------------------------------------------------------------------------- accumulation
class Acc:
    def __init__(self):
        self.days = []      # config, date, n, sum_r, n_pos, sum_ex
        self.turns = []     # config, month, tod, n_sig, hits, called
        self.base = []      # month, tod, side, n_elig, hits, events

    def add_trades(self, name, df, mask, side):
        m = np.asarray(mask, bool) & df.trade_ok.to_numpy()
        idx = gates.first_per_symbol_day(df.symbol.to_numpy(), df.date.to_numpy(), m)
        if not len(idx):
            return
        r = df[f"pr_{side}"].to_numpy(float)[idx]
        ex = r - df[f"ctrl_{side}"].to_numpy(float)[idx]
        t = pd.DataFrame({"date": df.date.to_numpy()[idx], "r": r, "ex": ex})
        a = t.groupby("date").agg(n=("r", "size"), sum_r=("r", "sum"), n_pos=("r", lambda x: (x > 0).sum()),
                                  sum_ex=("ex", "sum")).reset_index()
        a.insert(0, "config", name)
        self.days.append(a)

    def add_turns(self, name, month, df, mask, side):
        ev = "top" if side == "short" else "bot"
        m = np.asarray(mask, bool) & df.trade_ok.to_numpy()
        e = m & df.elig.to_numpy()
        g = pd.DataFrame({"tod": df.tod.to_numpy()[e], "hit": df[f"{ev}_c"].to_numpy()[e]}).groupby("tod")["hit"].agg(["size", "sum"])
        nxt = pd.Series(m).groupby([df.symbol.to_numpy(), df.date.to_numpy()]).shift(-1).fillna(False).astype(bool).to_numpy()
        called = int((df[ev].to_numpy() & df.trade_ok.to_numpy() & (m | nxt)).sum())
        g = g.reset_index().rename(columns={"size": "n_sig", "sum": "hits"})
        g["config"], g["month"], g["called"] = name, month, 0
        if len(g):
            g.loc[g.index[0], "called"] = called
        self.turns.append(g)

    def add_base(self, month, df):
        ok = df.trade_ok & df.elig
        for side, ev in (("short", "top"), ("long", "bot")):
            g = df[ok].groupby("tod").agg(n_elig=(f"{ev}_c", "size"), hits=(f"{ev}_c", "sum"), events=(ev, "sum")).reset_index()
            g["month"], g["side"] = month, side
            self.base.append(g)
        for side in ("long", "short"):   # all-bar baseline expectancy
            r = df.loc[df.trade_ok, f"pr_{side}"]
            self.base.append(pd.DataFrame({"month": [month], "side": [side], "tod": [-1], "n_elig": [len(r)],
                                           "hits": [float(r.sum())], "events": [0]}))


# ----------------------------------------------------------------------------------------------- MarcoFlow DB signals
def db_signals() -> pd.DataFrame:
    c = sqlite3.connect(ROOT / "data" / "marcoflow.sqlite")
    o = pd.read_sql("select observedAt, symbol, heat from SignalObservation where source='live'", c)
    o["t"] = pd.to_datetime(o.observedAt, format="ISO8601").dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    o["month"] = o.t.dt.strftime("%Y-%m")
    return o


def db_trades(acc: Acc, month: str, df: pd.DataFrame, obs: pd.DataFrame):
    o = obs[obs.month == month].copy()
    if not len(o):
        return
    f = df[["symbol", "ts"]].copy()
    f["end"] = (f.ts + pd.Timedelta(minutes=5)).astype("datetime64[ns, America/New_York]")
    f["row"] = np.arange(len(df))
    o["t"] = o.t.astype("datetime64[ns, America/New_York]")
    m = pd.merge_asof(o.sort_values("t"), f.sort_values("end"), left_on="t", right_on="end", by="symbol",
                      direction="forward", tolerance=pd.Timedelta(minutes=5)).dropna(subset=["row"])
    m = m[m.end.dt.date == m.t.dt.date]
    rows, heat = m.row.astype(int).to_numpy(), m.heat.to_numpy()
    for lo, hi in ((30, 40), (40, 50), (50, 60), (60, 101)):
        sel = (np.abs(heat) >= lo) & (np.abs(heat) < hi)
        for mode in ("follow", "fade"):
            for side in ("long", "short"):
                want = heat > 0 if (side == "long") == (mode == "follow") else heat < 0
                mask = np.zeros(len(df), bool)
                mask[rows[sel & want]] = True
                name = f"DB-{lo}_{hi if hi < 101 else 'up'}-{mode}-{side}"
                acc.add_trades(name, df, mask, side)
                acc.add_turns(name, month, df, mask, side)


# ----------------------------------------------------------------------------------------------- stats
def summarise(days: pd.DataFrame, reg: pd.DataFrame) -> dict:
    n = days.n.sum()
    if n == 0:
        return {"n": 0}
    mu = days.sum_r.sum() / n
    se = np.sqrt(((days.sum_r - days.n * mu) ** 2).sum()) / n
    b = days.sum_r.idxmax()
    out = {"n": int(n), "days": len(days), "win": round(days.n_pos.sum() / n, 4), "exp_r": round(mu, 4),
           "t": round(mu / se, 2) if se > 0 else None, "excess": round(days.sum_ex.sum() / n, 4),
           "ex_best_day": round((days.sum_r.sum() - days.sum_r[b]) / max(1, n - days.n[b]), 4)}
    rg = days.date.map(reg.regime)
    for k in ("up", "down"):
        d = days[rg.to_numpy() == k]
        out[f"exp_{k}"] = round(d.sum_r.sum() / d.n.sum(), 4) if d.n.sum() else None
        out[f"n_{k}"] = int(d.n.sum())
    mon = pd.to_datetime(days.date).dt.strftime("%Y-%m")
    mm = days.groupby(mon)[["sum_r", "n"]].sum()
    ms = sorted(mm.index)
    folds = [m for i, m in enumerate(ms) if i >= 3 and mm.loc[m, "n"] >= 10]
    out["wf_share"] = round(np.mean([mm.loc[m, "sum_r"] > 0 for m in folds]), 3) if folds else None
    return out


def main():
    RES.mkdir(exist_ok=True)
    acc, obs, cfgs = Acc(), db_signals(), configs()
    t0 = time.time()
    for month in months():
        df = prep(month)
        acc.add_base(month, df)
        for name, side, fn in cfgs:
            mask = fn(df).to_numpy()
            acc.add_trades(name, df, mask, side)
            acc.add_turns(name, month, df, mask, side)
        db_trades(acc, month, df, obs)
        print(month, len(df), f"{time.time() - t0:.0f}s", flush=True)
        del df
    days = pd.concat(acc.days, ignore_index=True)
    turns = pd.concat(acc.turns, ignore_index=True)
    base = pd.concat(acc.base, ignore_index=True)
    days.to_csv(RES / (TAG + "orig_days.csv.gz"), index=False)
    turns.to_csv(RES / (TAG + "orig_turns.csv"), index=False)
    base.to_csv(RES / (TAG + "orig_base.csv"), index=False)
    report(days, turns, base)


def report(days, turns, base):
    reg = regimes()
    days["date"] = pd.to_datetime(days.date).dt.date
    days["split"] = np.where(pd.to_datetime(days.date).dt.strftime("%Y-%m") <= TRAIN_END, "train", "valid")
    turns["split"] = np.where(turns.month <= TRAIN_END, "train", "valid")
    b = base[base.tod >= 0]
    rows = []
    n_cfg = days.config.nunique()
    for cfg, d in days.groupby("config"):
        side = "short" if cfg.endswith("short") else "long"
        rec = {"config": cfg, "side": side}
        for sp, dd in [("all", d)] + list(d.groupby("split")):
            s = summarise(dd.reset_index(drop=True), reg)
            rec.update({f"{sp}_{k}": v for k, v in s.items()})
        tname = cfg if not cfg.startswith("DB-") else cfg
        tt = turns[turns.config == tname]
        if len(tt):
            bb = b[b.side == side].groupby("tod")[["n_elig", "hits"]].sum()
            rate = bb.hits / bb.n_elig
            g = tt.groupby("tod")[["n_sig", "hits"]].sum()
            exp_hits = (g.n_sig * rate.reindex(g.index).fillna(rate.mean())).sum()
            rec["turn_n"] = int(g.n_sig.sum())
            rec["turn_hit"] = round(g.hits.sum() / max(1, g.n_sig.sum()), 4)
            rec["turn_base"] = round(exp_hits / max(1, g.n_sig.sum()), 4)
            rec["turn_lift"] = round(g.hits.sum() / exp_hits, 3) if exp_hits > 0 else None
            rec["turn_recall"] = round(tt.called.sum() / b[b.side == side].events.sum(), 4)
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values("all_exp_r")
    out.to_csv(RES / (TAG + "orig_summary.csv"), index=False)
    ab = base[base.tod == -1].copy()
    ab["split"] = np.where(ab.month <= TRAIN_END, "train", "valid")
    print("all-bar baseline exp (prod R):", ab.groupby(["side", "split"]).apply(lambda x: round(x.hits.sum() / x.n_elig.sum(), 4)).to_dict())
    tb = b.groupby("side")[["n_elig", "hits", "events"]].sum()
    print("turn base rates (turn at i or i-1, eligible bars):", (tb.hits / tb.n_elig).round(4).to_dict(), "events", tb.events.to_dict())
    print("configs:", n_cfg, "t_required:", gates.t_required(200 if MODE == 'P' else 100))
    cols = ["config", "all_n", "all_exp_r", "all_t", "all_excess", "train_exp_r", "valid_exp_r", "all_exp_up", "all_exp_down",
            "all_wf_share", "all_ex_best_day", "turn_hit", "turn_base", "turn_lift", "turn_recall"]
    with pd.option_context("display.width", 250, "display.max_rows", 200):
        print(out[[c for c in cols if c in out]].to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report(pd.read_csv(RES / (TAG + "orig_days.csv.gz")), pd.read_csv(RES / (TAG + "orig_turns.csv")), pd.read_csv(RES / (TAG + "orig_base.csv")))
    else:
        main()
