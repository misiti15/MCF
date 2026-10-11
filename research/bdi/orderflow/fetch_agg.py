"""OF-A step A: download SIP trades + NBBO quotes per symbol-day (read-only Alpaca market data, REST), aggregate ON THE
FLY to 1-second records and 1-minute footprint summaries, keep only the aggregates (raw pages are never written).

Grid: seconds 0..23399 after 09:30:00 ET (regular session). Per symbol-day the day is cut into 30-minute windows; a
small thread pool (I/O only, one process) fetches trades and quotes of each window; quotes start 30 s early so the
prevailing NBBO is known at the window start (the overlap only sets state, it is not aggregated).

Trade filter (SIP condition codes, tapes A/B/C): excluded from volume, signing and prices = prints that are not
aggressive continuous-session trades: 1 4 5 6 7 8 9 A B C D G H K L M N O P Q R S T U V W X Z (stopped, derivatively
priced, re-opening / opening / closing prints, QCT, corrected close, acquisition, bunched, cash, distribution, price
variation, rule 155, sold last, official open/close, next day, prior reference, seller, split, form T / extended,
contingent, average price, cross, out of sequence). Kept: regular '@'/' ', 'E', 'F' (intermarket sweep, flagged),
'I' (odd lot, flagged and tallied separately), 'Y'. Off-exchange (TRF, exchange 'D') prints are kept and also
tallied separately (lit = exchange != 'D').

Signing: Lee-Ready with the prevailing NBBO (last quote with t <= trade t, no lag; SIP timestamps): price > mid buy,
< mid sell, = mid tick rule (sign of the last non-zero price change). Quote rule strict: p >= ask buy-aggressor,
p <= bid sell-aggressor. Quotes: crossed quotes (ask < bid) and zero sides dropped.

Large print: size >= the symbol's prior-session p99 trade size (kept trades); the first session (2026-09-11, a warmup
session not scored) uses the p99 of its own 09:30-10:00 window (documented approximation).
Sweep: trades in the same millisecond on >= 2 venues, all at/through the touch on one side (quote rule vs the NBBO
prevailing before the group's first print).
OFI: Cont-Kukanov-Stoikov (2014) event OFI on the NBBO, summed per second.

Usage: python fetch_agg.py [--case-only]. Resumable (skips existing files). Educational only - not financial advice.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SEC, MIN, FP = DATA / "sec", DATA / "min", DATA / "footprint"
META = DATA / "meta.jsonl"
URL = "https://data.alpaca.markets/v2/stocks/{sym}/{kind}"

# Pre-declared sample (NOTES.md 1.1): 40 symbols x 21 sessions (09-11 warmup + 20 scored).
SYMBOLS = ("SPY QQQ IWM XLF XLE SMH "                                   # ETFs (6)
           "AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO JPM LLY "           # mega caps (10)
           "CAT UNH XOM COST BA WMT HD GS NFLX ORCL "                    # large, diverse sectors (10)
           "DKNG AFRM ROKU CCL RBLX DAL "                                # mid caps (6)
           "SPCX AMD PLTR COIN MSTR SMCI HOOD MARA").split()            # high beta (8)
CASE_DAY = "2026-10-09"
CASE_SYMS = ("AAPL", "SPCX", "CAT", "TSLA", "SPY")
EXCL = set("1456789ABCDGHKLMNOPQRSTUVWXZ")
NSEC = 23400
WIN = 1800
THREADS = 10


def sessions() -> list[str]:
    d0, d1 = date(2026, 9, 11), date(2026, 10, 9)
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def t0_ns(day: str) -> int:
    """09:30 ET in UTC ns (EDT, UTC-4, for every session in the sample)."""
    return int(datetime.fromisoformat(day + "T13:30:00").replace(tzinfo=timezone.utc).timestamp()) * 1_000_000_000


_tls = __import__("threading").local()


def _session() -> requests.Session:
    if not hasattr(_tls, "s"):
        s = requests.Session()
        s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
                          "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
        _tls.s = s
    return _tls.s


def _iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def fetch(sym: str, kind: str, a_ns: int, b_ns: int) -> list[dict]:
    """All records of `kind` in [a, b). Read-only GET on the market-data host only."""
    out, tok, s = [], None, _session()
    while True:
        p = {"start": _iso(a_ns), "end": _iso(b_ns), "limit": 10000, "feed": "sip"}
        if tok:
            p["page_token"] = tok
        for attempt in range(8):
            try:
                r = s.get(URL.format(sym=sym, kind=kind), params=p, timeout=60)
                if r.status_code == 429:
                    time.sleep(2 + attempt * 2)
                    continue
                r.raise_for_status()
                j = r.json()
                break
            except (requests.RequestException, ValueError):
                time.sleep(2 + attempt * 3)
        else:
            raise RuntimeError(f"fetch failed {sym} {kind} {_iso(a_ns)}")
        out.extend(j.get(kind) or [])
        tok = j.get("next_page_token")
        if not tok:
            return out


def _ts(L) -> np.ndarray:
    return pd.to_datetime([d["t"] for d in L], format="ISO8601").as_unit("ns").asi8 if L else np.zeros(0, np.int64)


def parse_trades(L):
    t = _ts(L)
    p = np.fromiter((d["p"] for d in L), float, len(L))
    s = np.fromiter((d["s"] for d in L), float, len(L))
    x = np.array([d["x"] for d in L], dtype="U1") if L else np.zeros(0, "U1")
    cond = [d.get("c") or () for d in L]
    excl = np.fromiter((any(ch in EXCL for ch in c) for c in cond), bool, len(L))
    iso = np.fromiter(("F" in c for c in cond), bool, len(L))
    odd = np.fromiter(("I" in c for c in cond), bool, len(L))
    o = np.argsort(t, kind="stable")
    return t[o], p[o], s[o], x[o], excl[o], iso[o], odd[o]


def parse_quotes(L):
    t = _ts(L)
    bp = np.fromiter((d["bp"] for d in L), float, len(L))
    ap = np.fromiter((d["ap"] for d in L), float, len(L))
    bs = np.fromiter((d["bs"] for d in L), float, len(L))
    as_ = np.fromiter((d["as"] for d in L), float, len(L))
    ok = (bp > 0) & (ap > 0) & (ap >= bp)
    o = np.argsort(t[ok], kind="stable")
    return t[ok][o], bp[ok][o], ap[ok][o], bs[ok][o], as_[ok][o]


def agg_window(T, Q, t0: int, w0: int, w1: int, big_thr: float, want_fp: bool):
    """Aggregate one window [w0, w1) seconds. Returns (sec_df, min_df, fp_df|None)."""
    tt, p, s, x, excl, iso, odd = T
    qt, bp, ap, bs, as_ = Q
    n = w1 - w0
    out = {}
    # ---------------- quotes
    qsec = (qt - t0) // 1_000_000_000
    inwin = (qsec >= w0) & (qsec < w1)
    if len(qt) > 1:
        pb, pa, pbs, pas = np.r_[bp[0], bp[:-1]], np.r_[ap[0], ap[:-1]], np.r_[bs[0], bs[:-1]], np.r_[as_[0], as_[:-1]]
        e = (bp >= pb) * bs - (bp <= pb) * pbs - (ap <= pa) * as_ + (ap >= pa) * pas
        e[0] = 0.0
        mid = (bp + ap) / 2
        midchg = np.r_[False, mid[1:] != mid[:-1]]
    else:
        e = np.zeros(len(qt)); midchg = np.zeros(len(qt), bool)
    qi = qsec[inwin] - w0
    bc = lambda idx, w=None: np.bincount(idx, w, minlength=n)[:n]
    out["ofi"] = bc(qi, e[inwin])
    out["n_q"] = bc(qi)
    out["n_midchg"] = bc(qi, midchg[inwin].astype(float))
    # time-weighted spread / queue imbalance inside each second (state durations clipped to the second's end)
    nxt = np.r_[qt[1:], t0 + w1 * 1_000_000_000]
    send = t0 + (qsec + 1) * 1_000_000_000
    dt = (np.minimum(nxt, send) - qt).clip(min=0).astype(float)[inwin]
    spr = (ap - bp)[inwin]
    qimb = ((bs - as_) / np.maximum(bs + as_, 1e-9))[inwin]
    wsum = bc(qi, dt)
    with np.errstate(invalid="ignore", divide="ignore"):
        out["spread_tw"] = bc(qi, dt * spr) / wsum
        out["qimb_tw"] = bc(qi, dt * qimb) / wsum
    # end-of-second state: prevailing quote at each second's end (incl. seconds without updates)
    ends = t0 + (np.arange(w0, w1) + 1) * 1_000_000_000
    k = np.searchsorted(qt, ends, side="left") - 1
    okk = k >= 0
    kk = np.where(okk, k, 0)
    for nm, arr in (("bid", bp), ("ask", ap), ("bsz", bs), ("asz", as_)):
        out[nm] = np.where(okk, arr[kk], np.nan) if len(qt) else np.full(n, np.nan)
    # ---------------- trades
    keep = ~excl
    tt, p, s, x, iso, odd = tt[keep], p[keep], s[keep], x[keep], iso[keep], odd[keep]
    tsec = (tt - t0) // 1_000_000_000
    m = (tsec >= w0) & (tsec < w1)
    tt, p, s, x, iso, odd, tsec = tt[m], p[m], s[m], x[m], iso[m], odd[m], tsec[m]
    ti = tsec - w0
    if len(qt):
        j = np.searchsorted(qt, tt, side="right") - 1
        hasq = j >= 0
        jj = np.where(hasq, j, 0)
        b_, a_ = np.where(hasq, bp[jj], np.nan), np.where(hasq, ap[jj], np.nan)
    else:
        b_ = a_ = np.full(len(tt), np.nan)
    mid = (b_ + a_) / 2
    dp = np.sign(np.diff(p, prepend=p[0] if len(p) else 0.0))
    tick = pd.Series(np.where(dp != 0, dp, np.nan)).ffill().fillna(0.0).to_numpy()
    sign = np.where(p > mid, 1.0, np.where(p < mid, -1.0, tick))
    sign = np.where(np.isnan(mid), tick, sign)
    qb, qs = p >= a_, p <= b_
    big = s >= big_thr
    lit = x != "D"
    out["n_tr"] = bc(ti)
    out["vol"] = bc(ti, s)
    out["bvol"] = bc(ti, s * (sign > 0))
    out["svol"] = bc(ti, s * (sign < 0))
    out["bvol_q"] = bc(ti, s * qb)
    out["svol_q"] = bc(ti, s * qs)
    out["lit_b"] = bc(ti, s * (sign > 0) * lit)
    out["lit_s"] = bc(ti, s * (sign < 0) * lit)
    out["iso_b"] = bc(ti, s * iso * (sign > 0))
    out["iso_s"] = bc(ti, s * iso * (sign < 0))
    out["big_b"] = bc(ti, s * big * (sign > 0))
    out["big_s"] = bc(ti, s * big * (sign < 0))
    out["odd_vol"] = bc(ti, s * odd)
    out["dollar"] = bc(ti, s * p)
    maxs = np.zeros(n); np.maximum.at(maxs, ti, s) if len(ti) else None
    out["max_sz"] = maxs
    hi = np.full(n, -np.inf); lo = np.full(n, np.inf)
    if len(ti):
        np.maximum.at(hi, ti, p); np.minimum.at(lo, ti, p)
    out["px_hi"] = np.where(np.isfinite(hi), hi, np.nan)
    out["px_lo"] = np.where(np.isfinite(lo), lo, np.nan)
    first = np.full(n, np.nan); last = np.full(n, np.nan)
    if len(ti):
        u, fi = np.unique(ti, return_index=True)
        first[u] = p[fi]
        li = np.r_[fi[1:] - 1, len(ti) - 1]
        last[u] = p[li]
    out["px_first"], out["px_last"] = first, last
    # sweeps: same millisecond, >= 2 venues, all prints at/through the touch on one side (NBBO before the group)
    sw_b, sw_s = np.zeros(n), np.zeros(n)
    if len(tt):
        g = tt // 1_000_000
        df = pd.DataFrame({"g": g, "x": x, "s": s, "qb": qb, "qs": qs, "ti": ti})
        agg = df.groupby("g", sort=False).agg(nx=("x", "nunique"), n=("s", "size"), vol=("s", "sum"),
                                               allb=("qb", "all"), alls=("qs", "all"), ti=("ti", "first"))
        agg = agg[(agg.n >= 2) & (agg.nx >= 2)]
        bb = agg[agg.allb]; ss = agg[agg.alls & ~agg.allb]
        sw_b = bc(bb.ti.to_numpy(int), bb.vol.to_numpy(float))
        sw_s = bc(ss.ti.to_numpy(int), ss.vol.to_numpy(float))
    out["sweep_b"], out["sweep_s"] = sw_b, sw_s
    sec_df = pd.DataFrame(out)
    sec_df.insert(0, "sec", np.arange(w0, w1, dtype=np.int32))
    # ---------------- footprint per 1-minute bar
    mins, fp = [], None
    if len(tt):
        f = pd.DataFrame({"m": tsec // 60, "px": np.round(p, 2), "b": s * (sign > 0), "s": s * (sign < 0)})
        lv = f.groupby(["m", "px"], sort=True)[["b", "s"]].sum().reset_index()
        if want_fp:
            fp = lv.copy()
        for mm, g in lv.groupby("m", sort=True):
            b, sv, px = g.b.to_numpy(), g.s.to_numpy(), g.px.to_numpy()
            tot = b.sum() + sv.sum()
            if tot <= 0:
                continue
            d = b - sv
            # diagonal imbalances (footprint convention): buy at p vs sell at the next lower traded level, and sell
            # at p vs buy at the next higher traded level; ratio >= 3 with at least 1% of the bar's volume
            mn = 0.01 * tot
            bi = np.r_[False, (b[1:] >= 3 * np.maximum(sv[:-1], 1)) & (b[1:] >= mn)]
            si = np.r_[(sv[:-1] >= 3 * np.maximum(b[1:], 1)) & (sv[:-1] >= mn), False]

            def run(a):
                best = cur = 0
                for v in a:
                    cur = cur + 1 if v else 0
                    best = max(best, cur)
                return best
            k2 = min(2, len(px))
            poc = px[np.argmax(b + sv)]
            mins.append({"m": int(mm), "fp_levels": len(px), "fp_maxd": d.max() / tot, "fp_mind": d.min() / tot,
                         "fp_stack_b": run(bi), "fp_stack_s": run(si),
                         "fp_low_d": d[:k2].sum() / tot, "fp_high_d": d[-k2:].sum() / tot,
                         "fp_poc_pos": (poc - px[0]) / (px[-1] - px[0]) if px[-1] > px[0] else 0.5,
                         "fp_delta": d.sum() / tot})
    return sec_df, pd.DataFrame(mins), fp


def do_symbol_day(sym: str, day: str, big_thr: float | None, pool: ThreadPoolExecutor) -> dict:
    t0 = t0_ns(day)
    wins = [(w, min(w + WIN, NSEC)) for w in range(0, NSEC, WIN)]
    ft = {w: pool.submit(fetch, sym, "trades", t0 + w * 10**9, t0 + w1 * 10**9) for w, w1 in wins}
    fq = {w: pool.submit(fetch, sym, "quotes", t0 + (w - 30) * 10**9, t0 + w1 * 10**9) for w, w1 in wins}
    secs, mins, fps, ntr, nq, sizes = [], [], [], 0, 0, []
    want_fp = day == CASE_DAY and sym in CASE_SYMS
    for w, w1 in wins:
        Lt, Lq = ft[w].result(), fq[w].result()
        ntr += len(Lt); nq += len(Lq)
        T, Q = parse_trades(Lt), parse_quotes(Lq)
        del Lt, Lq
        keep = ~T[4]
        sz = T[2][keep]
        if big_thr is None:          # first session: p99 of its own first window (warmup session, not scored)
            big_thr = float(np.quantile(sz, 0.99)) if len(sz) else 1e18
        sizes.append(sz.astype(np.float32))
        a, b, c = agg_window(T, Q, t0, w, w1, big_thr, want_fp)
        secs.append(a); mins.append(b)
        if c is not None:
            fps.append(c)
        del T, Q
    sec = pd.concat(secs, ignore_index=True)
    for col in sec.columns:
        if col != "sec":
            sec[col] = sec[col].astype(np.float32)
    keep_rows = (sec.n_tr > 0) | (sec.n_q > 0)
    (SEC / sym).mkdir(parents=True, exist_ok=True)
    (MIN / sym).mkdir(parents=True, exist_ok=True)
    sec[keep_rows].to_parquet(SEC / sym / f"{day}.parquet", compression="zstd", index=False)
    mn = pd.concat(mins, ignore_index=True)
    mn.astype({c: np.float32 for c in mn.columns if c != "m"}).to_parquet(MIN / sym / f"{day}.parquet", compression="zstd", index=False)
    if fps:
        FP.mkdir(parents=True, exist_ok=True)
        pd.concat(fps, ignore_index=True).to_parquet(FP / f"{sym}_{day}.parquet", compression="zstd", index=False)
    allsz = np.concatenate(sizes) if sizes else np.zeros(0)
    return {"symbol": sym, "date": day, "n_trades_raw": ntr, "n_quotes_raw": nq,
            "n_trades_kept": int(len(allsz)), "big_thr_used": big_thr,
            "p99_size": float(np.quantile(allsz, 0.99)) if len(allsz) else None}


def main():
    case_only = "--case-only" in sys.argv
    DATA.mkdir(parents=True, exist_ok=True)
    done = {}
    if META.exists():
        for line in META.read_text().splitlines():
            r = json.loads(line)
            done[(r["symbol"], r["date"])] = r
    days = sessions()
    syms = list(CASE_SYMS) + ([] if case_only else [x for x in SYMBOLS if x not in CASE_SYMS])
    pool = ThreadPoolExecutor(THREADS)
    for sym in syms:
        prev_p99 = None
        for day in days:
            if (sym, day) in done:
                prev_p99 = done[(sym, day)]["p99_size"]
                continue
            free = os.statvfs(DATA).f_bavail * os.statvfs(DATA).f_frsize / 1e9
            if free < 1.2:
                print(f"STOP: free disk {free:.2f} GB", flush=True)
                return
            t = time.time()
            r = do_symbol_day(sym, day, prev_p99, pool)
            r["secs"] = round(time.time() - t, 1)
            prev_p99 = r["p99_size"]
            with open(META, "a") as f:
                f.write(json.dumps(r) + "\n")
            print(json.dumps(r), flush=True)


if __name__ == "__main__":
    main()
