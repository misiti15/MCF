"""Pass over the 1,226 lab symbols (one process): signals + exits for A1-A9 and the same-time control sample.

    python research/bdi/cwt/test_a/run.py [--limit N] [--symbols A,B]
Writes research/bdi/cwt/test_a/data/ (git-ignored). Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import families as F  # noqa: E402
from a5 import a5_symbol, daily_context  # noqa: E402
from engine import HOLIDAYS, ROOT, Sym, control_outcomes  # noqa: E402

OUT = HERE / "data"
EARN = ROOT / "research" / "bdi" / "earnings" / "data" / "earnings_yf.parquet"
CTL_P = 0.03


def earn_flags(s: Sym, er: pd.DataFrame) -> dict:
    black = np.zeros(s.D, bool)
    eday = np.zeros(s.D, bool)
    if er is not None and len(er):
        rep = er["date"].to_numpy().astype("datetime64[D]")
        for i in range(s.D):
            n = np.abs(np.busday_count(s.dnum[i], rep, holidays=HOLIDAYS))
            black[i] = bool((n <= 4).any())
        react = []
        for dt, ses in zip(rep, er["session"].to_numpy()):
            if ses in ("bmo", "dmh"):
                react.append(np.busday_offset(dt, 0, roll="forward", holidays=HOLIDAYS))
            elif ses == "amc":
                react.append(np.busday_offset(dt, 1, roll="forward", holidays=HOLIDAYS))
        eday = np.isin(s.dnum, np.array(react, dtype="datetime64[D]"))
    return {"black": black, "eday": eday}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--symbols", default="")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    syms = [x.strip() for x in (ROOT / "research" / "lab_symbols.txt").read_text().split() if x.strip()]
    if a.symbols:
        syms = a.symbols.split(",")
    if a.limit:
        syms = syms[: a.limit]
    er = pd.read_parquet(EARN, columns=["symbol", "date", "session"])
    er = er[(er["date"] >= "2024-08-01") & (er["date"] <= "2026-11-30")]
    er_by = {k: g for k, g in er.groupby("symbol")}
    ctx = daily_context()
    ctx_by = {k: g for k, g in ctx.groupby("symbol")}
    spy = Sym("SPY")
    spy_ctx = ctx_by["SPY"].set_index("date")
    cal = sorted(pd.read_parquet(ROOT / "research" / "history2y" / "data" / "daily.parquet", columns=["date"])["date"].astype(str).unique())
    cal = [c for c in cal if c >= "2024-10-01" and not ("2024-11-01" <= c <= "2025-02-28")]
    cpos = {c: i for i, c in enumerate(cal)}
    ctl_sum = np.zeros((len(cal), 66, 2, 4))
    ctl_n = np.zeros((len(cal), 66, 2, 4))
    parts, a5_parts, desc, a5_ctl = [], [], [], {}
    t0 = time.time()
    for n, sym in enumerate(syms):
        try:
            s = Sym(sym)
        except Exception as ex:  # noqa: BLE001
            print(f"skip {sym}: {ex}", flush=True)
            continue
        if s.D < 30:
            continue
        rows: list = []
        ef = earn_flags(s, er_by.get(sym))
        F.a1(s, rows)
        F.a2(s, rows, desc)
        F.a3(s, rows)
        F.a4(s, rows)
        F.a6(s, rows)
        F.a7(s, rows, ef)
        F.a8(s, rows, ef)
        F.a9(s, rows, ef)
        if rows:
            r = pd.DataFrame(rows, columns=["cid", "d", "m0", "side", "r", "exit"])
            r["symbol"] = sym
            r["date"] = s.dates[r["d"].to_numpy()]
            r["ext"] = s.ext[r["d"].to_numpy()].astype("float32")
            r["price"] = s.open_d[r["d"].to_numpy()].astype("float32")
            r["gap"] = s.gap[r["d"].to_numpy()].astype("float32")
            r["blackout"] = ef["black"][r["d"].to_numpy()]
            parts.append(r.drop(columns=["d"]).astype({"cid": "int16", "m0": "int16", "side": "int8", "r": "float32"}))
        # A5
        if sym in ctx_by:
            r5: list = []
            a5_symbol(s, ctx_by[sym], spy, spy_ctx, r5, a5_ctl)
            if r5:
                x = pd.DataFrame(r5, columns=["ci", "d", "side", "r", "gross"])
                x["symbol"] = sym
                x["date"] = s.dates[x["d"].to_numpy()]
                a5_parts.append(x.drop(columns=["d"]))
        # same-time control sample
        for d in np.flatnonzero(s.ok):
            if s.dates[d] not in cpos:
                continue
            if zlib.crc32(f"{sym}|{s.dates[d]}".encode()) % 1000 >= CTL_P * 1000:
                continue
            o = control_outcomes(s, d)
            ok = np.isfinite(o)
            ctl_sum[cpos[s.dates[d]]] += np.where(ok, o, 0)
            ctl_n[cpos[s.dates[d]]] += ok
        if n % 50 == 0:
            print(f"{n}/{len(syms)} {sym} {time.time() - t0:.0f}s trades {sum(len(p) for p in parts)}", flush=True)
    tr = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    tr.to_parquet(OUT / "trades.parquet", index=False)
    if a5_parts:
        pd.concat(a5_parts, ignore_index=True).to_parquet(OUT / "a5_trades.parquet", index=False)
    pd.DataFrame([(k[0], k[1], float(np.mean(v)), len(v)) for k, v in a5_ctl.items()],
                 columns=["date", "H", "gross_long", "n"]).to_parquet(OUT / "a5_ctl.parquet", index=False)
    pd.DataFrame(desc, columns=["symbol", "date", "gap", "close_below_open", "hod_tod"]).to_parquet(OUT / "a2_desc.parquet", index=False)
    np.savez_compressed(OUT / "controls.npz", s=ctl_sum, n=ctl_n, dates=np.array(cal))
    pd.DataFrame(F.CONFIGS).to_csv(OUT / "configs.csv", index=False)
    print(f"done {len(syms)} symbols, {len(tr)} trades, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
