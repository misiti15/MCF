"""refire1014 step 1: every qualifying decision bar of every live lab setup on the open two-year frames, with its
production-cost outcome. Pre-declaration: NOTES.md section 1. Educational only - not financial advice.

    python research/bdi/refire1014/scan.py        # -> $RF_SCR/hits.parquet, setups.json

Rows: setup key, symbol, date, tod, bar (decision-bar number of the day), r (production R; NaN = untradeable bar,
e.g. a structural stop on the wrong side). The locked block is never loaded (lib.load_month refuses it).
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.config import _merge  # noqa: E402
from mcf.research import gates  # noqa: E402

SCR = Path(os.environ.get("RF_SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/refire1014"))
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
ACCOUNTS = {"Primary": [], "Testing": ["account_testing.yaml"], "Testing 2": ["account_testing2.yaml"]}
LOCK = (pd.Timestamp(lib.LOCKED[0]).date(), pd.Timestamp(lib.LOCKED[1]).date())


# ------------------------------------------------------------------------------------------------ setups
def account_setups() -> list[dict]:
    """Enabled type: lab setups per account (merged as mcf.config does), unique by module/window/min_adv."""
    base = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())
    uniq: dict[tuple, dict] = {}
    for acct, files in ACCOUNTS.items():
        cfg = base
        for f in files:
            cfg = _merge(cfg, yaml.safe_load((ROOT / "config" / f).read_text()) or {})
        for name, p in (cfg.get("strategies") or {}).items():
            if p.get("type") != "lab" or not p.get("enabled", True):
                continue
            win = tuple(p.get("window") or (950, 1500))
            k = (p["module"], win, float(p.get("min_adv", 0.0)))
            if k not in uniq:
                uniq[k] = {"key": f"S{len(uniq):02d}", "name": name, "module": p["module"], "window": list(win),
                           "min_adv": float(p.get("min_adv", 0.0)), "r_atr_frac": float(p.get("r_atr_frac", 0.25)),
                           "accounts": []}
            uniq[k]["accounts"].append(acct)
    return list(uniq.values())


def load_mod(s):
    path = ROOT / s["module"]
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("rf_" + re.sub(r"\W", "_", s["name"]), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def family(s) -> str:
    mod = s["module"]
    if "/cwt/" in mod:
        return "cwt"
    if "reddit1012liq" in mod:
        return "liq"
    if "RW6G1" in s["name"]:
        return "rw6g1"
    return "frame"


# ------------------------------------------------------------------------------------------------ frames
def head_rows(f: pd.DataFrame, month: str, liq: bool) -> pd.DataFrame:
    """The 09:35-09:45 rows (headtail.parquet) for the symbol-days of frame f, as research/bdi/cwt/live/verify.py
    adds them; with liq also the day-constant / derived columns the LIQ sweep machine reads."""
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)), ("tod", "<", 950)])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    day = f.groupby(["symbol", "date"], sort=False).first().reset_index()
    ht = ht.merge(day[["symbol", "date", "atr_d", "adv20", "gap", "fromOpen", "close", "dist_pdh_atr", "dist_pdl_atr"]]
                  .rename(columns={"close": "c0", "fromOpen": "fo0", "dist_pdh_atr": "dh0", "dist_pdl_atr": "dl0"}),
                  on=["symbol", "date"], how="inner")
    h = pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"].astype(f["tod"].dtype),
                      "close": ht["c"].astype(float), "high": ht["h"].astype(float), "low": ht["l"].astype(float),
                      "vwapDistPct": (ht["c"] / ht["vwap"] - 1) * 100, "adv20": ht["adv20"]})
    if liq:
        atr = ht["atr_d"].to_numpy(float)
        dopen = ht["c0"].to_numpy(float) / (1 + ht["fo0"].to_numpy(float) / 100)
        pdh = ht["c0"].to_numpy(float) + ht["dh0"].to_numpy(float) * atr
        pdl = ht["c0"].to_numpy(float) - ht["dl0"].to_numpy(float) * atr
        c = ht["c"].to_numpy(float)
        h["atr_d"] = atr
        h["gap"] = ht["gap"].to_numpy(float)
        h["fromOpen"] = (c / dopen - 1) * 100
        h["dist_pdh_atr"] = (pdh - c) / atr
        h["dist_pdl_atr"] = (c - pdl) / atr
    return h


def with_head(f: pd.DataFrame, h: pd.DataFrame) -> pd.DataFrame:
    x = pd.concat([f, h], ignore_index=True)
    return x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def tail_rows(month: str) -> pd.DataFrame:
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)), ("tod", ">", 1500)])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    return ht.rename(columns={"h": "high", "l": "low", "c": "close"})[["symbol", "date", "tod", "high", "low", "close"]]


def bar_no(tod) -> np.ndarray:
    t = np.asarray(tod, int)
    return ((t // 100) * 60 + t % 100 - 9 * 60 - 30) // 5   # 09:35 close = 1, 09:50 = 4, 15:00 = 66


# ------------------------------------------------------------------------------------------------ outcomes
def fixed_r(df, idx, side, geom, r_frac):
    assert r_frac == 0.25, "frame outcomes are for R = 0.25 x ATR"
    return gates.prod_r(df[f"r_{side}_{geom}"].to_numpy(float)[idx], df[f"win_{side}_{geom}"].to_numpy(float)[idx],
                        df["close"].to_numpy(float)[idx], df["atr_d"].to_numpy(float)[idx], geom,
                        tod=df["tod"].to_numpy(float)[idx])


def structural_r(df, idx, m, side, tail) -> np.ndarray:
    """GEOM S on the 5-minute path (NOTES 1.3): stop first, gap-through fills at the open proxy, optional target,
    flat at the 15:55 close. R = structural risk."""
    s = 1 if side == "long" else -1
    sym, dat = df["symbol"].to_numpy(), df["date"].to_numpy()
    c, h, l, tod = (df[k].to_numpy(float) for k in ("close", "high", "low", "tod"))
    tl = {k: g for k, g in tail.groupby(["symbol", "date"], sort=False)}
    out = np.full(len(idx), np.nan)
    day_cache: dict = {}
    for j, i in enumerate(idx):
        px = c[i]
        a = i   # the symbol-day's rows, as the live frame (one symbol, today's bars) sees them
        while a > 0 and sym[a - 1] == sym[i] and dat[a - 1] == dat[i]:
            a -= 1
        if a not in day_cache:
            b = i
            while b + 1 < len(c) and sym[b + 1] == sym[i] and dat[b + 1] == dat[i]:
                b += 1
            day_cache.clear()
            day_cache[a] = df.iloc[a:b + 1].drop(columns=["symbol", "date"]).reset_index(drop=True)
        fd = day_cache[a]
        stop = float(m.stop_price(fd, i - a)) if hasattr(m, "stop_price") else np.nan
        if not np.isfinite(stop) or s * (px - stop) <= 0:
            continue
        tgt = None
        if hasattr(m, "target_price"):
            tgt = float(m.target_price(fd, i - a, stop))
            if not np.isfinite(tgt) or s * (tgt - px) <= 0:
                continue
        risk = abs(px - stop)
        k = i + 1
        ph, pl, pc = [], [], []
        while k < len(c) and sym[k] == sym[i] and dat[k] == dat[i]:
            ph.append(h[k]); pl.append(l[k]); pc.append(c[k]); k += 1
        t = tl.get((sym[i], dat[i]))
        if t is not None:
            t = t[t["tod"] <= 1555]
            ph += list(t["high"]); pl += list(t["low"]); pc += list(t["close"])
        prev, exit_px, kind = px, None, "timed"
        for bh, bl, bc in zip(ph, pl, pc):
            if not np.isfinite(bc):
                continue
            if s * (prev - stop) <= 0:
                exit_px, kind = prev, "stop"; break
            if (s == 1 and bl <= stop) or (s == -1 and bh >= stop):
                exit_px, kind = stop, "stop"; break
            if tgt is not None and ((s == 1 and bh >= tgt) or (s == -1 and bl <= tgt)):
                exit_px, kind = tgt, "target"; break
            prev = bc
        if exit_px is None:
            exit_px = prev if pc else px
        cost = (gates.SLIP_PS + px * gates.SLIP_BPS) * float(gates.tod_cost_mult([tod[i]])[0])
        if kind != "target":
            cost += gates.SLIP_PS + exit_px * gates.SLIP_BPS
        if kind == "stop":
            cost += gates.STOP_EXTRA
        out[j] = (s * (exit_px - px) - cost) / risk
    return out


# ------------------------------------------------------------------------------------------------ RW6G1 guard
def rw6_guard(m, days: pd.DataFrame) -> dict:
    """{(symbol, date): set of decision-bar tods blocked by the module's vwap_band_block}, on 5-minute bars rebuilt
    from the SIP 1-minute cache (bar close 09:35..), locked block dropped on read."""
    from mcf.data.store import BarStore

    store = BarStore(ROOT / "data" / "cache_hist")
    out = {}
    for sym, g in days.groupby("symbol"):
        want = set(g["date"])
        df = store.load(sym)
        if df is None or df.empty:
            continue
        df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
        dd = df.index.date
        keep = np.array([(d in want) and not (LOCK[0] <= d <= LOCK[1]) for d in dd])
        df = df[keep]
        for d, x in df.groupby(df.index.date):
            b = x.resample("5min", label="left", closed="left").agg(
                {"high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["close"])
            blk = m.vwap_band_block(b)
            end = b.index + pd.Timedelta(minutes=5)
            tods = end.hour * 100 + end.minute
            out[(sym, d)] = {int(tt) for tt, bb in zip(tods, blk) if bb}
    return out


def _guard_job(args):
    name, module, days = args
    m = load_mod({"name": name, "module": module})
    return rw6_guard(m, days)


# ------------------------------------------------------------------------------------------------ main
def month_hits(month: str, sts: list[dict]) -> tuple[list[pd.DataFrame], dict]:
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    fams = {family(s) for s in sts}
    fh_c = with_head(f, head_rows(f, month, liq=False)) if "cwt" in fams else None
    fh_l = with_head(f, head_rows(f, month, liq=True)) if "liq" in fams else None
    tail = tail_rows(month) if any(load_mod(s).GEOM == "S" for s in sts) else None
    rows, rw6days = [], {}
    for s in sts:
        m = load_mod(s)
        fam = family(s)
        df = {"cwt": fh_c, "liq": fh_l}.get(fam, f)
        lo, hi = s["window"]
        tod = df["tod"].to_numpy()
        base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (df["adv20"].fillna(0).to_numpy() >= s["min_adv"]) \
            & (df["atr_d"].to_numpy(float) > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            if fam == "rw6g1":
                orig = m.vwap_band_block
                m.vwap_band_block = lambda d, k=2.0: np.zeros(len(d), bool)   # base here, guard from rebuilt bars
                mk = np.asarray(m.mask(df), bool)
                m.vwap_band_block = orig
            else:
                mk = np.asarray(m.mask(df), bool)
        idx = np.flatnonzero(mk & base)
        if m.GEOM == "S":
            r = structural_r(df, idx, m, m.SIDE, tail)
        else:
            r = fixed_r(df, idx, m.SIDE, m.GEOM, s["r_atr_frac"])
        x = pd.DataFrame({"key": s["key"], "symbol": df["symbol"].to_numpy()[idx], "date": df["date"].to_numpy()[idx],
                          "tod": tod[idx].astype(int), "r": r})
        if fam == "rw6g1":
            rw6days[s["key"]] = x[["symbol", "date"]].drop_duplicates()
        rows.append(x)
    return rows, rw6days


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    sts = account_setups()
    for s in sts:
        m = load_mod(s)
        s["side"], s["geom"], s["family"] = m.SIDE, m.GEOM, family(s)
    json.dump(sts, open(SCR / "setups.json", "w"), indent=1)
    print(len(sts), "unique setups", flush=True)
    t0 = time.time()
    rows, rw6 = [], {}
    for mo in lib.months():
        assert mo not in lib.LOCKED_MONTHS
        r, d = month_hits(mo, sts)
        rows += r
        for k, v in d.items():
            rw6.setdefault(k, []).append(v)
        print(mo, round(time.time() - t0), flush=True)
    hits = pd.concat(rows, ignore_index=True)
    # RW6G1 guard on rebuilt bars
    jobs = []
    for k, parts in rw6.items():
        s = next(x for x in sts if x["key"] == k)
        days = pd.concat(parts, ignore_index=True).drop_duplicates()
        for sym_chunk in np.array_split(np.array(sorted(days["symbol"].unique())), 4):
            jobs.append((k, s["name"], s["module"], days[days["symbol"].isin(set(sym_chunk))]))
    with Pool(4) as p:
        res = p.map(_guard_job, [(n, mod, d) for _, n, mod, d in jobs])
    blocked = {}
    for (k, *_), g in zip(jobs, res):
        blocked.setdefault(k, {}).update(g)
    drop = np.zeros(len(hits), bool)
    for k, bl in blocked.items():
        sel = np.flatnonzero(hits["key"].to_numpy() == k)
        sub = hits.iloc[sel]
        for j, sym, d, tt in zip(sel, sub["symbol"], sub["date"], sub["tod"]):
            b = bl.get((sym, d))
            drop[j] = b is None or int(tt) in b     # no rebuilt bars -> no trade (the module fails safe)
    hits = hits[~drop].reset_index(drop=True)
    hits["bar"] = bar_no(hits["tod"])
    hits["date"] = pd.to_datetime(hits["date"])
    hits.to_parquet(SCR / "hits.parquet", index=False)
    print(hits.groupby("key").size().to_string(), flush=True)


if __name__ == "__main__":
    main()
