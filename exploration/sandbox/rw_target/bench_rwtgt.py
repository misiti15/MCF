"""RW-TGT125 re-check on the bench (T1 = FIT + CHECK from research/history2y frames, T2 = 2023-01-03..2024-09-13 from
data/cache_fresh). Wraps research/ultimate_1119/top10/bench10.py unchanged (signals, 1-minute walk) with SETUPS limited
to RW3-FD / RW5-FD. Each signal is walked four times on the same 1-minute bars:
  p_raw  target 1.00x, round(x,2)-free prices (as bench10 / shorts_autopsy rw_t125.py)
  v_raw  target 1.25x, unrounded
  p      target 1.00x with the 11-20 rounding rule (stop to the cent away from price, target toward entry)
  v      target 1.25x with the same rounding rule
Target 1.25x = entry + side x 1.25 x |parent target - entry| (entry = signal close on the bench, so = outsider/WAVE2 Y1).
Locked block 2024-11-01..2025-02-28 is never read (bench10 asserts on every load).
cwd = repo checkout. Usage: python bench_rwtgt.py WORK sig1|walk1|t2
Educational only - not financial advice."""
import sys
from pathlib import Path
from multiprocessing import Pool
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

RW = ("RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD")
B.SETUPS = [s for s in B.SETUPS if s[0] in RW]
ARMS = {"p_raw": (1.0, False), "v_raw": (1.25, False), "p": (1.0, True), "v": (1.25, True)}


def rnd(x, side):
    # 11-20 rule: shorts round UP (stop away from price, target toward entry), longs round DOWN
    return np.where(side < 0, np.ceil(np.round(x * 100, 6)) / 100, np.floor(np.round(x * 100, 6)) / 100)


def walk_all(T, b):
    out = None
    for arm, (m, r) in ARMS.items():
        X = T.copy()
        X["tgt"] = X.entry + X.side * m * (X.tgt - X.entry).abs()
        if r:
            X["stop"] = rnd(X.stop.to_numpy(float), X.side.to_numpy())
            X["tgt"] = rnd(X.tgt.to_numpy(float), X.side.to_numpy())
        a = pd.DataFrame(B.walk_trades(X, b), columns=["i", f"px_{arm}", f"kind_{arm}", f"xt_{arm}"]).set_index("i")
        out = a if out is None else out.join(a)
    return out


def walk1_job(args):
    sym, T = args
    return walk_all(T, B.hist_bars(sym))


def t2_job(sym):
    # bench10.t2_job with the walk swapped for walk_all (frame build and signals unchanged)
    import research.history2y.build_frames as BF
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, "short", None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, "noframe", None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, "nodays", None
    if "ctx" not in B.WCTX:
        c = pd.read_parquet(B.FRESH / "ctx.parquet")
        c["date"] = c["date"].astype(str)
        B.WCTX["ctx"] = c
    f = x.drop(columns=["ts"]).merge(B.WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    h = B.head_rows_from_1min(sym, b)
    fx = B.with_head(f, h) if len(h) else f
    inv = B.inventory()
    mods = {st["setup"]: B.load_mod(st["setup"], st["module"]) for st in inv}
    o = B.signals(f, fx, inv, mods)
    if not len(o):
        return sym, "ok", o
    return sym, "ok", o.join(walk_all(o, b))


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(3) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif st == "walk1":
        sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("sig1_*.parquet"))], ignore_index=True)
        B.no_locked(sig["date"].unique())
        jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
        with Pool(3) as p:
            res = pd.concat(list(p.imap_unordered(walk1_job, jobs, chunksize=4)))
        sig.join(res).to_parquet(W / "trades_t1.parquet")
        print(len(sig), "T1 signals")
    elif st == "t2":
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
        out, stt = [], {}
        with Pool(3) as p:
            for sym, s, o in p.imap_unordered(t2_job, syms):
                stt[s] = stt.get(s, 0) + 1
                if o is not None and len(o):
                    out.append(o)
        pd.concat(out, ignore_index=True).to_parquet(W / "trades_t2.parquet")
        print("T2", stt)
