"""TAGS1 (owner yes 2026-11-18): journal-only would-skip tags. Each live and shadow trade of a session is tagged with
13 point-in-time conditions (the W4 12 + SPY-from-open at the decision) and the frozen candidate rules in rules.json.
No order, slot, latch or halt is touched: this reads the journals after the close and writes tags/<date>.csv.gz.
Scored ONCE after 20 fresh sessions (score.py). Point-in-time: only 1-minute bars that ENDED at or before the trade's
signal time are used; daily priors use prior days only.

    python research/tags1/tags1.py --date 2026-11-19 --jdir <dir with mcf-data*.db> [--bars <dir with 1min/1day packs>]

Without --bars the session's packs are streamed from the public bars-YYYY-MM release (store-bars) and deleted after use.
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RULES = json.loads((HERE / "rules.json").read_text())
ACCOUNTS = {"mcf-data": "primary", "mcf-data-testing": "testing", "mcf-data-testing2": "testing2",
            "mcf-data-explore1": "explore1", "mcf-data-livelab": "livelab", "mcf-data-testingd": "testingd",
            "mcf-data-testinge": "testinge", "mcf-data-testingf": "testingf", "mcf-data-gen": "gen",
            "mcf-data-graveyard": "graveyard"}
REL = "https://github.com/misiti15/MCF/releases/download"
LIVE_KINDS = frozenset({"paper", "live"})   # run kinds counted as live trades (TAGS1-WHATIF)
NY = "America/New_York"
ETF_RE = re.compile(r"\bETF\b|\bFund\b|ProShares|iShares|Direxion|SPDR|Invesco QQQ|\b[23]X\b|Leveraged|Ultra|Bull|Bear|"
                    r"Trust Series|ETN", re.I)


# ------------------------------------------------------------------------------------------------- inputs
def decisions(jdir: Path, day: str) -> pd.DataFrame:
    """Live (run kind paper/live) and shadow trades of `day` from every account journal present in `jdir`."""
    out = []
    for b, acct in ACCOUNTS.items():
        p = Path(jdir) / f"{b}.db"
        if not p.exists():
            continue
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            runs = pd.read_sql("SELECT id, kind FROM runs", c)
            t = pd.read_sql("SELECT * FROM trades WHERE date=?", c, params=[day])
        finally:
            c.close()
        if t.empty:
            continue
        kind = t.run_id.map(dict(zip(runs.id, runs.kind)))
        # TAGS1-WHATIF (owner yes 2026-11-21): only run kind paper/live is "live" and shadow is "shadow"; what-if,
        # backtest and reference runs are dropped (1,664 what-if rows were labelled live on 11-19 before this fix)
        t = t[kind.isin(LIVE_KINDS | {"shadow"})].copy()
        if t.empty:
            continue
        t["source"] = kind[t.index].map(lambda k: "shadow" if k == "shadow" else "live")
        t["acct"] = acct
        out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def priors(daily: pd.DataFrame) -> pd.DataFrame:
    """(symbol, day) -> pc, atr14, adv20, pday from daily bars (columns symbol, ts, open, high, low, close, volume);
    every value uses prior days only."""
    D = daily.copy()
    D["day"] = pd.to_datetime(D.ts, utc=True).dt.tz_convert(NY).dt.date.astype(str)
    D = D.drop_duplicates(["symbol", "day"], keep="last").sort_values(["symbol", "day"])
    g = D.groupby("symbol")
    D["pc"] = g.close.shift(1)
    D["tr"] = np.maximum(D.high, D.pc) - np.minimum(D.low, D.pc)
    D["atr14"] = D.groupby("symbol").tr.transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    D["dv"] = D.close * D.volume
    D["adv20"] = D.groupby("symbol").dv.transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    D["pday"] = (D.pc / g.close.shift(2) - 1) * 100
    return D.set_index(["symbol", "day"])[["pc", "atr14", "adv20", "pday"]]


# ------------------------------------------------------------------------------------------------- conditions
def conditions(dec: pd.DataFrame, m: pd.DataFrame, pri: pd.DataFrame, day: str, etf: set | None = None) -> pd.DataFrame:
    """The 13 point-in-time conditions per decision row (index kept). m = the session's 1-minute bars (symbol, ts = bar
    start UTC, open, high, low, close, volume) for the traded names + SPY."""
    etf = etf or set()
    m = m.copy()
    m["symbol"] = m.symbol.astype(str)
    m["ts"] = pd.to_datetime(m.ts, utc=True)
    m = m.sort_values(["symbol", "ts"])
    m["end"] = m.ts + pd.Timedelta(minutes=1)
    m["pv"] = (m.high + m.low + m.close) / 3 * m.volume
    g = m.groupby("symbol")
    m["cpv"], m["cv"] = g.pv.cumsum(), g.volume.cumsum()
    m["hh"], m["ll"] = g.high.cummax(), g.low.cummin()
    opens = g.open.first()
    t0 = pd.Timestamp(f"{day} 09:30", tz=NY).tz_convert("UTC")
    t10 = t0 + pd.Timedelta(minutes=30)
    spy = m[m.symbol == "SPY"].set_index("end")
    by = {s: x for s, x in m.groupby("symbol")}
    rows = {}
    for i, r in dec.iterrows():
        sig = pd.Timestamp(r.get("signal_time") or r.get("entry_time"))
        sig = sig.tz_convert("UTC") if sig.tzinfo else sig.tz_localize(NY).tz_convert("UTC")
        s = by.get(str(r.symbol))
        if s is None:
            continue
        s = s[s.end <= sig]
        if s.empty or r.symbol not in opens.index:
            continue
        last, op, side = s.iloc[-1], float(opens[r.symbol]), int(r.side)
        px = float(last.close)
        pc, atr, adv, pday = (pri.loc[(r.symbol, day)].values if (r.symbol, day) in pri.index else (np.nan,) * 4)
        sp10 = spy[spy.index <= min(sig, t10)]
        spn = spy[spy.index <= sig]
        so = float(opens["SPY"]) if "SPY" in opens.index else np.nan
        f30 = s[s.end <= t10]
        rng = (f30.high.max() - f30.low.min()) if len(f30) else (last.hh - last.ll)
        vw = last.cpv / last.cv if last.cv > 0 else px
        ok = bool(atr) and atr == atr
        rows[i] = dict(
            tod=(sig - t0).total_seconds() / 60, gap=(op / pc - 1) * 100 if pc == pc and pc else np.nan,
            spy10=(sp10.close.iloc[-1] / so - 1) * 100 if len(sp10) and so == so else np.nan,
            spy_now=(spn.close.iloc[-1] / so - 1) * 100 if len(spn) and so == so else np.nan,
            atr_pct=atr / pc * 100 if pc == pc and pc else np.nan, price=px,
            adv=np.log10(adv) if adv == adv and adv and adv > 0 else np.nan, etf=int(r.symbol in etf),
            withday=side * (px / op - 1) * 100, vwap=side * (px - vw) / atr if ok else np.nan,
            open=side * (px - op) / atr if ok else np.nan, pday=pday, or30=rng / atr if ok else np.nan)
    return pd.DataFrame.from_dict(rows, orient="index")


def _open_other(prim: pd.DataFrame) -> pd.Series:
    """Primary live rows: True when another Primary lot (any setup) on the same symbol was open at this row's entry."""
    out = pd.Series(False, index=prim.index)
    et = pd.to_datetime(prim.entry_time, utc=True, format="ISO8601")
    xt = pd.to_datetime(prim.exit_time, utc=True, format="ISO8601")
    for sym, g in prim.groupby("symbol"):
        for i in g.index:
            others = g.index[g.index != i]
            out[i] = bool(((et[others] < et[i]) & ((xt[others] > et[i]) | xt[others].isna())).any())
    return out


def tag_rules(dec: pd.DataFrame, cond: pd.DataFrame, rules: dict | None = None) -> pd.DataFrame:
    """Frozen would-skip / record tags (bool columns, one per rule) for each decision row."""
    R = (rules or RULES)["rules"]
    d = dec.join(cond, how="left")
    strat = d.strategy.astype(str)
    prim = d.acct.eq("primary") & d.source.eq("live")
    out = pd.DataFrame(index=d.index)
    out["FLAT25"] = prim & (d.spy_now.abs() < 0.25)
    st = R["STACK1_L3X"]["setups"]
    oth = pd.Series(False, index=d.index)
    if prim.any():
        oth.loc[prim] = _open_other(d[prim])
    out["STACK1_L3X"] = prim & strat.isin(st) & oth
    mf = R["MFGAP"]
    out["MFGAP"] = strat.str.startswith(mf["prefix"]) & d.side.eq(-1) & (d.gap >= mf["gap_min"])
    h = R["W4_HFL_VWAP"]
    out["W4_HFL_VWAP"] = strat.str.startswith(h["prefix"]) & (d.vwap > h["vwap_max"])
    n = R["W4_NS3_PDAY"]
    out["W4_NS3_PDAY"] = strat.str.startswith(n["prefix"]) & (d.pday > n["pday_max"])
    l3 = R["W4_L3_PM"]
    out["W4_L3_PM"] = strat.str.startswith(l3["prefix"]) & d.tod.between(l3["tod"][0], l3["tod"][1], inclusive="left")
    g2 = R["W4_RW3_GAP2"]
    out["W4_RW3_GAP2"] = strat.str.startswith(g2["prefix"]) & (d.gap < g2["gap_lt"])
    return out.fillna(False).astype(bool)


def build(dec: pd.DataFrame, m: pd.DataFrame, daily: pd.DataFrame, day: str, etf: set | None = None) -> pd.DataFrame:
    if dec.empty:
        return dec
    cond = conditions(dec, m, priors(daily), day, etf)
    tags = tag_rules(dec, cond)
    keep = [c for c in ("id", "run_id", "acct", "source", "strategy", "symbol", "side", "date", "signal_time",
                        "entry_time", "exit_time", "entry", "stop", "shares", "pnl", "pnl_adj", "r_multiple",
                        "exit_reason") if c in dec]
    return dec[keep].join(cond).join(tags)


# ------------------------------------------------------------------------------------------------- CLI
def _get(tag: str, name: str, out: str) -> None:
    subprocess.run(["curl", "-sSLf", "-o", out, f"{REL}/{tag}/{name}"], check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", required=True)
    ap.add_argument("--jdir", required=True)
    ap.add_argument("--bars", help="dir with 1min-<date>.parquet and 1day-<date>.parquet (else streamed from releases)")
    ap.add_argument("--universe", help="universe.csv (ETF flag); optional")
    ap.add_argument("--out", default=str(HERE / "tags"))
    a = ap.parse_args(argv)
    day = a.date
    if day < RULES["first_session"]:
        raise SystemExit("TAGS1 tags fresh sessions only (from %s)" % RULES["first_session"])
    dec = decisions(Path(a.jdir), day)
    if dec.empty:
        print(f"TAGS1 {day}: no trades")
        return
    tmp = None
    if a.bars:
        p1, pd1 = Path(a.bars) / f"1min-{day}.parquet", Path(a.bars) / f"1day-{day}.parquet"
    else:
        tmp = tempfile.mkdtemp(prefix="tags1-")
        p1, pd1 = Path(tmp) / f"1min-{day}.parquet", Path(tmp) / f"1day-{day}.parquet"
        _get(f"bars-{day[:7]}", p1.name, str(p1))
        _get(f"bars-{day[:7]}", pd1.name, str(pd1))
    syms = sorted(set(dec.symbol.astype(str)) | {"SPY"})
    m = pd.read_parquet(p1, filters=[("symbol", "in", syms)])
    daily = pd.read_parquet(pd1, filters=[("symbol", "in", syms)])
    etf = set()
    if a.universe and Path(a.universe).exists():
        u = pd.read_csv(a.universe)
        etf = set(u.symbol[u.get("name", pd.Series("", index=u.index)).fillna("").str.contains(ETF_RE)])
    if tmp:
        for p in (p1, pd1):
            try:
                os.remove(p)
            except OSError:
                pass
    out = build(dec, m, daily, day, etf)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    f = Path(a.out) / f"{day}.csv.gz"
    out.to_csv(f, index=False)
    flags = [c for c in RULES["rules"] if c in out]
    print(f"TAGS1 {day}: {len(out)} trades tagged -> {f}; would-skip counts " +
          ", ".join(f"{c} {int(out[c].sum())}" for c in flags))


if __name__ == "__main__":
    main()
