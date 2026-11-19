"""Round-5 FRESH harness (FRESH_PLAN.md sec. 2.4-2.6, 5, 7): ONE streaming pass that scores ALL 8 frozen rules
(R1 BOOK-EM 32e, R2 leg E, R3 leg M, R4 ST7-FD bench, R5 NM-ETF bench, R6 ST7-base chassis, H-V1, H-V2) from the
FROZEN code. This file is a thin wrapper: it imports the frozen files and calls their own functions
(ULT-32 month_job / book / dissect_sel / chain, hunt.py month_job / select, ULT-28 walk + cost_R, bench.py month_job /
walk_all / cost_r, ULT-23 stats). The only overrides (plan sec. 2.5) are:
  * DATA / CACHE paths (B28.CACHE, bench.CACHE -> the 1-minute source of the run);
  * the frame source: research.history2y.lib.load_month / load_context are replaced, inside the worker processes only,
    by the symbol's frame streamed from its 1-minute bars (same build as research/history2y/build_frames.one_chunk:
    daily_table -> adv20, setup_lab.build(resample 5min), merge adv20 on date) plus spy_fo / qqq_fo / qqq_vwap from the
    SPY / QQQ frames (mcf.strategies.lab_context.context_from_frames; breadth columns are NOT built);
  * the half definitions (FRESH, FRESH-1, FRESH-2) and the SPY day-type table (from the run's own SPY bars);
  * blackout_set(): the same code with the date range 2022-10-03..2024-10-31 and the extended holiday list;
  * the holiday list (ULT-28 NYSE_HOLIDAYS + the 2022-2023 NYSE holidays), cross-checked against SPY's bar dates;
  * bench.py: the 5-minute headtail cross-check column is removed (HT -> an empty table) and SETUPS is narrowed to the
    two benchmark rules scored here (ST7-FD, NM-ETF); every other setup is simply not run.
No threshold, window, exit, cost, refire, cap or universe parameter is changed (asserted against the freeze files).

Random control (diagnostic, not a pass condition): the frozen random_control() draws per selected trade, which needs
the 1-minute bars AFTER the cross-symbol selection - impossible once streamed bars are deleted. So every candidate
symbol-session gets two pre-drawn random decision bars per (rule window, side) - deterministic from
sha256("1119|sym|date|lo-hi|k") - walked on the same chassis during the stream; the k-th trade of a symbol-session
(k = 0, 1) is paired with draw k. Bench rules get the same, walked by bench.py walk1 (entry at the random bar's close).

Stages
    python fresh_bt.py guards                     # every guard, PASS/FAIL table (no data read)
    python fresh_bt.py parity WORK [--workers 3]  # 2025-10 from data/cache_hist (open data) vs the earlier pipelines
                                                  #   -> round5/PARITY_2025-10.json (must PASS before any fresh byte)
    python fresh_bt.py stream [--workers 3] [--stop-utc 2026-11-19T13:15] [--batch 25]
                                                  # FRESH download + stream -> /home/user/MCF/data/cache_fresh/rows/
    python fresh_bt.py score                      # ONCE -> round5/fresh_once.json (+ fresh_trades.csv.gz)
    python fresh_bt.py score-dry WORK             # the scorer's code path on the parity rows (no fresh data)
Educational only - not financial advice. Alpaca keys only from ALPACA_API_KEY / ALPACA_SECRET_KEY (never printed or
logged; they live only in request headers inside download_fresh.fetch_bars)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys
import time
from datetime import date, datetime, timedelta, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent              # research/ultimate_1119/round5
U1119 = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(U1119 / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "the locked block is never read"

FRESH_OUT = Path("/home/user/MCF/data/cache_fresh")
HIST_1MIN = Path("/home/user/MCF/data/cache_hist/1Min")
WARM0, FRESH0, FRESH1_END, FRESH2_0, FRESH_END = "2022-10-03", "2023-01-03", "2023-12-29", "2024-01-02", "2024-09-13"
DL_END = "2024-09-14"                                # exclusive (T00:00Z)
BO_RANGE_FRESH = ("2022-10-03", "2024-10-31")
LOCK = ("2024-11-01", "2025-02-28")
EXTRA_HOL = ("2022-11-24 2022-12-26 2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04 "
             "2023-09-04 2023-11-23 2023-12-25").split()
PARITY_MONTH = ("2025-10-01", "2025-10-31")
PARITY_WARM0 = "2025-07-01"                          # 3-month warm-up, like the fresh 2022-10-03..2022-12-30
PARITY_FILE = HERE / "PARITY_2025-10.json"
ONCE_FILE = HERE / "fresh_once.json"
MIN_FREE_GB = 1.0
FWD = ("win_", "r_long", "r_short")
ST7, NM = "ST7-rsi50dn-long-pm-t1s1-FD", "NM-ETF-late-dip-di-long"
HV = {"H-V1": "X-r0.75-t05s1", "H-V2": "K-EQB-k0.2-t1s1"}
CFG32E = {"adv": 500e6, "rmax": 30.0, "d_on": False}
TOL = 1e-6
M_RULES = 8
WINS = {"E": (1400, 1500), "M": (1015, 1500), "S7": (950, 1500)}
RULE_WIN = {"E": "E", "M": "M", "D": "E", "X": "E", "K": "M", "ST7base": "S7"}


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def free_gb() -> float:
    return shutil.disk_usage("/home/user").free / 1e9


# ===================================================================== guards (no data read)
def guards(fresh_mode: bool = False) -> list[tuple[str, bool, str]]:
    out = []
    want = (HERE / "FRESH_PLAN.sha256").read_text().split()[0]
    have = sha(HERE / "FRESH_PLAN.md")
    out.append(("FRESH_PLAN.md sha256 == FRESH_PLAN.sha256", want == have, f"{have[:16]} vs {want[:16]}"))
    core = json.loads((HERE / "FREEZE_CORE.json").read_text())
    bad = [k for k, v in core["files"].items() if sha(ROOT / v["path"]) != v["sha256"]]
    out.append(("FREEZE_CORE hashes", not bad, f"{len(core['files']) - len(bad)}/{len(core['files'])} match {bad}"))
    fh = HERE / "FREEZE_HUNT.json"
    if not fh.exists():
        out.append(("FREEZE_HUNT.json exists", False, "missing"))
        return out
    H = json.loads(fh.read_text())
    bad = [k for k, v in H["files"].items() if sha(ROOT / v["path"]) != v["sha256"]]
    out.append(("FREEZE_HUNT hashes (H5V files + deps + FREEZE_VOLUME + FREEZE_CORE)", not bad,
                f"{len(H['files']) - len(bad)}/{len(H['files'])} match {bad}"))
    tb = max(1.5, math.sqrt(2 * math.log(H["M"])))
    out.append(("FREEZE_HUNT M = 8, t bar 2.039, H3..H6 empty",
                H["M"] == M_RULES and abs(H["t_bar"] - 2.039) < 1e-9 and abs(tb - H["t_bar_exact"]) < 1e-12
                and all(H["slots"][k] is None for k in ("H3", "H4", "H5", "H6")), f"M={H['M']} t={H['t_bar']}"))
    out.append(("FREEZE_HUNT written before any fresh data", not H["fresh_data_exists_at_freeze"]
                and not H["cache_fresh_exists_at_freeze"], H["frozen_utc"]))
    if FRESH_OUT.exists():
        fz = datetime.strptime(H["frozen_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        mt = [p.stat().st_mtime for p in FRESH_OUT.rglob("*") if p.is_file()]
        out.append(("FREEZE_HUNT timestamp < first fresh file mtime", (min(mt) > fz) if mt else True,
                    f"{len(mt)} files"))
    out.append(("MCF_HIST_ALLOW_LOCKED unset", not os.environ.get("MCF_HIST_ALLOW_LOCKED"), ""))
    out.append((f"disk free >= {MIN_FREE_GB} GB", free_gb() >= MIN_FREE_GB, f"{free_gb():.2f} GB"))
    if fresh_mode:
        ok, why = parity_ok()
        out.append(("parity check PASS with this exact harness + plan", ok, why))
    return out


def parity_ok() -> tuple[bool, str]:
    if not PARITY_FILE.exists():
        return False, "PARITY_2025-10.json missing"
    P = json.loads(PARITY_FILE.read_text())
    if not P.get("PASS"):
        return False, "parity FAILED"
    for k, p in P["pins"].items():
        if sha(ROOT / p["path"]) != p["sha256"]:
            return False, f"{k} changed since the parity run"
    return True, f"parity {P['run_utc']}"


def print_guards(g):
    for name, ok, det in g:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {det}")
    return all(ok for _, ok, _ in g)


# ===================================================================== frozen code (imported only after guards)
FZ: dict = {}


def load_frozen():
    if FZ:
        return FZ
    s = importlib.util.spec_from_file_location("h5vhunt", HERE / "hunt_volume" / "hunt.py")
    HUNT = importlib.util.module_from_spec(s)
    sys.modules["h5vhunt"] = HUNT
    s.loader.exec_module(HUNT)
    B32, B28 = HUNT.B32, HUNT.B28
    B28.EXITS = {"T": (1.0, 1.0), "H": (0.5, 1.0), "X": (None, 2.0)}   # ULT-32/bt.py's set (hunt.py narrows to T, H;
    B28.MS = (0.25,)                                                     # T / H walk results are identical either way)
    s = importlib.util.spec_from_file_location("benchfz", U1119 / "benchmark" / "bench.py")
    BENCH = importlib.util.module_from_spec(s)
    sys.modules["benchfz"] = BENCH
    s.loader.exec_module(BENCH)
    BENCH.SETUPS = [(ST7, "default.yaml"), (NM, "default.yaml")]
    import tempfile
    ht = Path(tempfile.mkdtemp(prefix="fresh_bt_ht_")) / "headtail_empty.parquet"      # 5-min cross-check removed
    pd.DataFrame({"symbol": pd.Series([], dtype=str), "date": pd.Series([], dtype="datetime64[ns]"),
                  "tod": pd.Series([], dtype="int64"), "h": pd.Series([], dtype=float),
                  "l": pd.Series([], dtype=float), "c": pd.Series([], dtype=float)}).to_parquet(ht)
    BENCH.HT = ht
    import research.history2y.build_frames as BF
    import research.history2y.lib as LIB
    s = importlib.util.spec_from_file_location("dlfresh", HERE / "download_fresh.py")
    DL = importlib.util.module_from_spec(s)
    s.loader.exec_module(DL)
    H5V = HUNT.load_mod()
    FZ.update(HUNT=HUNT, B32=B32, B28=B28, B23=B28.B23, BENCH=BENCH, BF=BF, LIB=LIB, DL=DL, H5V=H5V)
    # ---- parameter asserts against the freeze files (no rule change possible through this harness)
    H = json.loads((HERE / "FREEZE_HUNT.json").read_text())
    for hid, name in HV.items():
        leg, p = HUNT.configs()[name]
        c = H["candidates"][hid]
        assert leg == c["leg"] and p == c["exact_parameters"] and H5V.P[leg] == p, (hid, p, H5V.P[leg])
    c32 = {k: v for k, v in B32.configs()["32e"].items() if k != "label"}
    assert c32 == CFG32E, c32
    assert B32.DAY_CAP == 30 and HUNT.DAY_CAP == 30 and B28.MS == (0.25,)
    assert B32.dissect_configs()["ST7-base"]["win"] == (950, 1500) and B32.dissect_configs()["ST7-base"]["exit"] == "T"
    inv = {r["setup"]: r for r in BENCH.inventory()}
    assert inv[ST7]["min_adv"] == 95e6 and (inv[ST7]["w_lo"], inv[ST7]["w_hi"]) == (950, 1500)
    assert inv[NM]["min_adv"] == 95e6 and (inv[NM]["w_lo"], inv[NM]["w_hi"]) == (1400, 1500)
    return FZ


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def hhmm(x):
    x = np.asarray(x, int)
    return (x // 60) * 100 + x % 60


def sessions(a: str, b: str) -> list[str]:
    m28 = load_frozen()["B28"].load_mod()
    hol = set(m28.NYSE_HOLIDAYS) | set(EXTRA_HOL)
    d, e, out = date.fromisoformat(a), date.fromisoformat(b), []
    while d <= e:
        if d.weekday() < 5 and d.isoformat() not in hol:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def blackout_set(lo: str, hi: str, extra_hol: bool = True):
    """ULT-32/bt.py blackout_set() with only the date range and the holiday list as parameters."""
    F = load_frozen()
    B23 = F["B23"]
    m28 = F["B28"].load_mod()
    e = pd.read_parquet(F["B28"].EARN)
    d = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    e = e[(d >= lo) & (d <= hi)].copy()
    B23.no_locked(pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d").unique())
    sess = np.array(sessions(lo, hi) if extra_hol else m28.sessions(lo, hi))
    rep = d[e.index].to_numpy()
    rep_i = np.searchsorted(sess, rep, "left")
    rd_i = np.where(e.session.to_numpy() == "amc", np.searchsorted(sess, rep, "right"), rep_i)
    out = set()
    for sym, a, b in zip(e.symbol.astype(str), rep_i, rd_i):
        for k in range(min(a, b) - 4, max(a, b) + 5):
            if 0 <= k < len(sess):
                out.add((sym, sess[k]))
    return out


def spy_days_from_bars(b: pd.DataFrame, thr: float = 0.30) -> pd.DataFrame:
    """benchmark/stats.py spy_days() on the run's own SPY bars (09:30 open -> last-minute close, +-0.30%)."""
    b = b.copy()
    b["date"] = b.index.date.astype(str)
    g = b.groupby("date").agg(o=("open", "first"), c=("close", "last"))
    g["ret"] = (g.c / g.o - 1) * 100
    g["type"] = np.where(g.ret >= thr, "up", np.where(g.ret <= -thr, "down", "flat"))
    return g


# ===================================================================== bar sources
def hist_bars(sym: str) -> pd.DataFrame:
    """Parity source: data/cache_hist 1-minute bars 2025-07-01..2025-10-31 (pyarrow filter; the locked block is never
    read - the filter starts 4 months after it)."""
    import pyarrow.dataset as pads
    p = HIST_1MIN / f"{sym}.parquet"
    if not p.exists():
        return pd.DataFrame()
    tz = "America/New_York"
    fld = pads.field("__index_level_0__")
    lo, hi = pd.Timestamp(PARITY_WARM0, tz=tz), pd.Timestamp("2025-11-01", tz=tz)
    assert lo > pd.Timestamp(LOCK[1], tz=tz)
    b = pads.dataset(str(p), format="parquet").to_table(filter=(fld >= lo) & (fld < hi)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b.index.name = None
    b = b.sort_index()
    d = b.index.date.astype(str)
    assert (not len(d)) or (min(d) >= PARITY_WARM0 and max(d) <= PARITY_MONTH[1])
    return b


def fresh_bars(sym: str) -> pd.DataFrame:
    """FRESH source: download_fresh.fetch_bars (SIP, adjustment=split, RTH, BarStore format), range-guarded; the bars
    are written to cache_fresh/1Min (the walk reads them there) and deleted after the batch walk unless retained;
    the daily table (download_fresh.daily_table) is always kept."""
    F = load_frozen()
    df = F["DL"].fetch_bars(sym, WARM0, DL_END)
    if df.empty:
        return df
    d = df.index.date.astype(str)
    assert min(d) >= WARM0 and max(d) <= FRESH_END, "fresh range guard"
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    p = FRESH_OUT / "1Min" / f"{sym}.parquet"
    tmp = p.with_suffix(".tmp")
    df.to_parquet(tmp)
    tmp.replace(p)
    dp = FRESH_OUT / "daily" / f"{sym}.parquet"
    tmp = dp.with_suffix(".tmp")
    F["DL"].daily_table(df, sym).to_parquet(tmp)
    tmp.replace(dp)
    return df


# ===================================================================== frames (build_frames.one_chunk logic)
def frame_from_bars(sym: str, df: pd.DataFrame, keep_from: str, keep_to: str):
    BF = load_frozen()["BF"]
    d5 = BF.resample(df, "5min")
    if len(d5) < 300:                    # setup_lab.build skips these (and would fail on an empty concat)
        return None
    dd = BF.daily_table(df, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return None
    x = x.reset_index(names="ts")
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["adv20"] = x["adv20"].astype("float32")
    ds = x["date"].astype(str)
    x = x[(ds >= keep_from) & (ds <= keep_to)]
    return x if len(x) else None


def context_table(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """spy_fo / qqq_fo / qqq_vwap per (date, tod) = mcf.strategies.lab_context.context_from_frames on the SPY / QQQ
    frames (the ETF's own fromOpen / vwapDistPct; build_frames.build_context casts float32). No breadth."""
    from mcf.strategies.lab_context import context_from_frames
    df = pd.concat([f[["symbol", "date", "tod", "fromOpen", "vwapDistPct"]] for f in frames], ignore_index=True)
    out = context_from_frames(df)
    out = out[["date", "tod", "spy_fo", "qqq_fo", "qqq_vwap"]].copy()
    out["date"] = pd.to_datetime(out["date"].astype(str)).dt.date
    for c in ("spy_fo", "qqq_fo", "qqq_vwap"):
        out[c] = out[c].astype("float32")
    return out


def lib_frame(x: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """What lib.load_month(month, context=True) returns, for one symbol's streamed frame (forward columns dropped)."""
    f = x[[c for c in x.columns if not c.startswith(FWD)]].copy()
    assert not any(c.startswith(FWD) for c in f.columns)
    f["date"] = pd.to_datetime(f["date"].astype(str)).dt.date
    f = f.merge(ctx, on=["date", "tod"], how="left")
    assert not any(c.startswith("breadth") for c in f.columns)
    return f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


# ===================================================================== per-symbol worker
WCTX: dict = {}


def _rtod(sym, d, win, k):
    lo, hi = WINS[win]
    h = hashlib.sha256(f"1119|{sym}|{d}|{lo}-{hi}|{k}".encode()).digest()
    slots = np.arange(m2(lo), m2(hi) + 1, 5)
    return int(hhmm(slots[int.from_bytes(h[:8], "big") % len(slots)]))


def random_rows(f, s32, sh, sb, inv):
    """Pre-drawn random decision bars (2 per symbol-session x window x side) for the chassis and the bench rules."""
    sess_atr = f.groupby(f["date"].astype(str)).agg(atr_d=("atr_d", "first"), adv20=("adv20", "first"))
    want = set()
    if len(s32):
        for col, win in (("legE", "E"), ("legM", "M"), ("legD", "E"), ("st7", "S7")):
            for d in s32.loc[s32[col].astype(bool), "date"].unique():
                want.add((d, win, 1))
    if len(sh):
        for hid, name in HV.items():
            fl = load_frozen()["HUNT"].flag(name)
            leg = name.split("-")[0]
            side = -1 if leg == "X" else 1
            for d in sh.loc[sh[fl].fillna(False).astype(bool) & (sh.side == side), "date"].unique():
                want.add((d, RULE_WIN[leg], side))
    sym = str(f["symbol"].iloc[0])
    rr = []
    for d, win, side in sorted(want):
        if d not in sess_atr.index:
            continue
        for k in (0, 1):
            rr.append({"symbol": sym, "date": d, "win": win, "k": k, "side": side, "evt": 0, "tod": _rtod(sym, d, win, k),
                       "atr_d": float(sess_atr.loc[d, "atr_d"]), "close": np.nan,
                       "adv20": float(sess_atr.loc[d, "adv20"])})
    r32 = pd.DataFrame(rr)
    # bench: entry at the random bar's close (frame row), R = 0.25 x atr_d, same setup / geom / side
    rb = []
    if len(sb):
        fk = f.assign(dstr=f["date"].astype(str)).set_index(["dstr", "tod"])
        fk = fk[~fk.index.duplicated()]
        for (setup, d), g in sb.groupby(["setup", "date"]):
            st = inv[setup]
            win = (max(950, st["w_lo"]), min(1500, st["w_hi"]))
            WINS[f"B:{win[0]}-{win[1]}"] = win
            for k in (0, 1):
                t = _rtod(sym, d, f"B:{win[0]}-{win[1]}", k)
                if (d, t) not in fk.index:
                    continue
                row = fk.loc[(d, t)]
                rb.append({"setup": setup, "side": int(g.side.iloc[0]), "geom": g.geom.iloc[0], "symbol": sym, "date": d,
                           "tod": t, "entry": float(row["close"]), "R": 0.25 * float(row["atr_d"]),
                           "gap": float(row["gap"]), "x5": t, "k5": 0, "px5": float(row["close"]), "k": k})
    return r32, pd.DataFrame(rb)


def sym_job(args):
    sym, mode, ctx_path, tmp_root, stop_iso = args
    F = load_frozen()
    if mode == "fresh":
        if stop_iso and datetime.now(timezone.utc) >= datetime.fromisoformat(stop_iso).replace(tzinfo=timezone.utc):
            return sym, "stopped", None
        if free_gb() < MIN_FREE_GB:
            return sym, "stopped_disk", None
        try:
            bars = fresh_bars(sym)
        except Exception as e:  # noqa: BLE001  (keys live only in request headers; never in the message)
            return sym, f"failed: {type(e).__name__}: {str(e)[:120]}", None
        keep = (FRESH0, FRESH_END)
    else:
        bars = hist_bars(sym)
        keep = PARITY_MONTH
    if bars.empty:
        return sym, "empty", None
    x = frame_from_bars(sym, bars, *keep)
    if x is None:
        return sym, "no_frame", None
    if ctx_path not in WCTX:
        WCTX.clear()
        WCTX[ctx_path] = pd.read_parquet(ctx_path)
        WCTX[ctx_path]["date"] = pd.to_datetime(WCTX[ctx_path]["date"].astype(str)).dt.date
    f = lib_frame(x, WCTX[ctx_path])
    ds = f["date"].astype(str)
    assert ds.min() >= keep[0] and ds.max() <= keep[1]
    # ---- frame source override (this worker process only), then the FROZEN month jobs
    LIB = F["LIB"]
    LIB.load_month = lambda month, columns=None, context=False: (f if columns is None else f[columns]).copy()
    LIB.load_context = lambda month: WCTX[ctx_path][["date", "tod"]].copy()
    _, s32, _ = F["B32"].month_job("STREAM")
    _, sh, em, _ = F["HUNT"].month_job("STREAM")
    etb = F["B28"].etb_set()
    sh = sh[(sh.side > 0) | sh.symbol.isin(etb)].reset_index(drop=True)        # hunt.py: shorts easy-to-borrow only
    td = Path(tmp_root) / f"sb_{sym}"
    td.mkdir(parents=True, exist_ok=True)
    _, n = F["BENCH"].month_job(("2023-01", str(td)))
    sb = pd.read_parquet(td / "sig_2023-01.parquet") if n else pd.DataFrame()
    shutil.rmtree(td, ignore_errors=True)
    inv = {r["setup"]: r for r in F["BENCH"].inventory()}
    r32, rb = random_rows(f, s32, sh, sb, inv)
    for t in (s32, sh, sb, r32, rb):
        if len(t):
            dd = t["date"].astype(str)
            assert dd.min() >= keep[0] and dd.max() <= keep[1]
    return sym, "ok", {"s32": s32, "sh": sh, "em": em, "sb": sb, "r32": r32, "rb": rb, "n_frame": len(f),
                       "frame_dates": sorted(set(ds))}


# ===================================================================== batch walk (main process; frozen walks)
def walk_batch(res: list, cache_dir: Path, bdir: Path, tag: str):
    F = load_frozen()
    B28, BENCH = F["B28"], F["BENCH"]
    B28.CACHE = cache_dir
    BENCH.CACHE = cache_dir
    bdir.mkdir(parents=True, exist_ok=True)
    cat = lambda k: pd.concat([r[k] for r in res if r is not None and len(r[k])], ignore_index=True) \
        if any(r is not None and len(r[k]) for r in res) else pd.DataFrame()
    out = {}
    s32 = cat("s32")
    if len(s32):
        s32["side"], s32["evt"] = 1, 0                                   # ULT-32/bt.py walk stage
        out["w32"] = B28.walk(s32)
    sh = cat("sh")
    if len(sh):
        sh["evt"] = 0                                                    # hunt.py walk stage
        out["wh"] = B28.walk(sh)
    r32 = cat("r32")
    if len(r32):
        out["wr32"] = B28.walk(r32, random=True)
    out["em"] = cat("em")
    for k in ("sb", "rb"):
        t = cat(k)
        if not len(t):
            continue
        d = bdir / f"{k}_{tag}"
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        for s, g in t.groupby("symbol"):
            g.reset_index(drop=True).to_parquet(d / f"sig_{s}.parquet")
        BENCH.walk_all(d)                                                # bench.py walk1 + cost_r (r1)
        out["w" + k] = pd.read_parquet(d / "trades.parquet")
        shutil.rmtree(d, ignore_errors=True)
    for k, t in out.items():
        if len(t):
            p = bdir / k
            p.mkdir(exist_ok=True)
            t.to_parquet(p / f"{tag}.parquet")
    return out


def load_rows(rdir: Path) -> dict:
    out = {}
    for k in ("w32", "wh", "wr32", "wsb", "wrb", "em"):
        ps = sorted((rdir / k).glob("*.parquet")) if (rdir / k).exists() else []
        out[k] = pd.concat([pd.read_parquet(p) for p in ps], ignore_index=True) if ps else pd.DataFrame()
    return out


# ===================================================================== selection of all 8 rules (frozen code)
def select_rules(rows: dict, bo: set) -> dict:
    F = load_frozen()
    B32, HUNT = F["B32"], F["HUNT"]
    S = rows["w32"].copy()
    S["blackout"] = [(a, b) in bo for a, b in zip(S.symbol, S.date)]
    t1 = B32.book(S, CFG32E)
    out = {"R1": t1, "R2": t1[t1.leg == "E"], "R3": t1[t1.leg == "M"],
           "R6": B32.dissect_sel(S, B32.dissect_configs()["ST7-base"]).assign(leg="ST7base"),
           "_R1_uncapped": B32.book(S, CFG32E, cap=0), "_R1_no_blackout": B32.book(S, CFG32E, blackout=False),
           "_32f": B32.book(S, B32.configs()["32f"])}
    Hs = rows["wh"].copy()
    Hs["blackout"] = [(a, b) in bo for a, b in zip(Hs.symbol, Hs.date)]
    for hid, name in HV.items():
        out[hid] = HUNT.select(Hs, name)
        out["_" + hid + "_uncapped"] = HUNT.select(Hs, name, cap=0)
    tb = rows["wsb"]
    if not len(tb):
        tb = pd.DataFrame({c: pd.Series([], dtype=d) for c, d in (("setup", str), ("symbol", str), ("date", str),
                           ("tod", "int64"), ("geom", str), ("side", "int64"), ("r1", float), ("k1", float),
                           ("x1", float))})
    for rid, st in (("R4", ST7), ("R5", NM)):
        t = tb[tb.setup == st].copy()
        t["r"] = t["r1"]
        t["kd"] = t["k1"]
        t["hold"] = np.where(t.x1 >= 0, m2(t.x1.fillna(0)) - m2(t.tod), np.nan) if len(t) else []
        t["exit"] = t["geom"] if len(t) else []
        t["leg"] = rid
        out[rid] = t
    return out


# ===================================================================== statistics (ULT-23 stats) + random pairing
def rand_pair(rid: str, t: pd.DataFrame, rows: dict) -> dict | None:
    if not len(t):
        return None
    t = t.sort_values(["symbol", "date", "tod"], kind="mergesort").copy()
    t["k"] = t.groupby(["symbol", "date"]).cumcount()
    if rid in ("R4", "R5"):
        R = rows["wrb"]
        if not len(R):
            return None
        R = R.assign(r=R["r1"])
        key = ["symbol", "date", "setup", "k"]
        m = t[["symbol", "date", "setup", "k", "r"]].merge(R[key + ["r"]], on=key, how="left", suffixes=("", "_rnd"))
    else:
        R = rows["wr32"]
        if not len(R):
            return None
        leg = t["leg"].astype(str).to_numpy()
        t["win"] = [RULE_WIN[x] for x in leg]
        t["side_"] = t["side"] if "side" in t else 1
        t["rcol"] = np.where(t["exit"].astype(str).to_numpy() == "T", "r25T", "r25H")
        RR = R.rename(columns={"side": "side_"})
        m = t[["symbol", "date", "win", "side_", "k", "r", "rcol"]].merge(
            RR[["symbol", "date", "win", "side_", "k", "r25T", "r25H"]], on=["symbol", "date", "win", "side_", "k"],
            how="left")
        m["r_rnd"] = np.where(m.rcol == "T", m.r25T, m.r25H)
    ok = m.r.notna() & m.r_rnd.notna()
    if not ok.any():
        return {"random_n": 0}
    return {"random_avg_r": round(float(m.r_rnd[ok].mean()), 4),
            "signal_minus_random": round(float(m.r[ok].mean() - m.r_rnd[ok].mean()), 4), "random_n": int(ok.sum()),
            "random_missing": int((~ok).sum())}


def rule_stats(t: pd.DataFrame, n: int, halves: dict) -> dict:
    B23 = load_frozen()["B23"]
    o = B23.stats(t, n)
    for hn, (a, b, nn) in halves.items():
        x = t[(t.date >= a) & (t.date <= b) & t.r.notna()]
        o[f"{hn}_trades"] = int(len(x))
        o[f"{hn}_avg_r"] = round(float(x.r.mean()), 4) if len(x) else None
        o[f"{hn}_r_per_session"] = round(float(x.r.sum()) / nn, 4) if nn else None
    return o


# ===================================================================== parity (2025-10, open data)
def cmp_trades(a: pd.DataFrame, b: pd.DataFrame, ra="r", rb="r", extra=()) -> dict:
    k = ["symbol", "date", "tod", *extra]
    A = a[k + [ra]].copy()
    B = b[k + [rb]].copy()
    for X in (A, B):
        X["date"] = X["date"].astype(str)
        X["tod"] = X["tod"].astype(int)
    m = A.merge(B, on=k, how="outer", suffixes=("_h", "_ref"), indicator=True)
    both = m[m._merge == "both"]
    ca, cb = (ra + "_h", rb + "_ref") if ra == rb else (ra, rb)
    d = (both[ca] - both[cb]).abs()
    nan_mis = int((both[ca].isna() != both[cb].isna()).sum())
    mx = float(d.max()) if len(d) and d.notna().any() else 0.0
    return {"n_harness": int(len(A)), "n_reference": int(len(B)), "matched": int(len(both)),
            "only_harness": m.loc[m._merge == "left_only", k].astype(str).values.tolist()[:10],
            "only_reference": m.loc[m._merge == "right_only", k].astype(str).values.tolist()[:10],
            "max_abs_r_diff": mx, "nan_mismatch": nan_mis,
            "PASS": bool(len(A) == len(B) == len(both) and mx <= TOL and nan_mis == 0)}


def run_stream(syms, mode, ctx_path, work: Path, workers: int, batch: int, cache_dir: Path, stop_iso=None,
               state=None, state_path=None, retained=None):
    tmp = work / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    rdir = work / "rows"
    rdir.mkdir(parents=True, exist_ok=True)
    statuses, buf, frame_dates = {}, [], set()
    bi = (state or {}).get("batches", 0)

    def flush():
        nonlocal buf, bi
        if not buf:
            return
        walk_batch([r for _, _, r in buf], cache_dir, rdir, f"b{bi:04d}")
        for s, st, _ in buf:
            if mode == "fresh" and s not in retained:
                p = FRESH_OUT / "1Min" / f"{s}.parquet"
                if p.exists():
                    p.unlink()
        bi += 1
        if state is not None:
            state["done"] += [s for s, st, _ in buf]
            state["batches"] = bi
            state["status"].update({s: st for s, st, _ in buf})
            state_path.write_text(json.dumps(state, indent=1))
        buf = []

    stopped = False
    with Pool(workers) as pool:
        for s, st, r in pool.imap_unordered(sym_job, [(s, mode, str(ctx_path), str(tmp), stop_iso) for s in syms]):
            statuses[s] = st
            if st == "ok":
                frame_dates |= set(r["frame_dates"])
                buf.append((s, st, r))
            elif st.startswith("stopped"):
                stopped = True
            elif state is not None:
                state["status"][s] = st
            if len(buf) >= batch:
                flush()
            if mode == "fresh" and free_gb() < MIN_FREE_GB:
                print("DISK GUARD: free < 1.0 GB, stopping", flush=True)
                stopped = True
                pool.terminate()
                break
            if len(statuses) % 50 == 0:
                print(f"{len(statuses)}/{len(syms)} symbols ({free_gb():.2f} GB free)", flush=True)
    flush()
    return statuses, frame_dates, stopped


def build_ctx(mode: str, work: Path):
    """SPY + QQQ first: frames -> context table; SPY day types; SPY bar dates for the calendar check."""
    keep = (FRESH0, FRESH_END) if mode == "fresh" else PARITY_MONTH
    src = fresh_bars if mode == "fresh" else hist_bars
    fr, spyb = [], None
    for s in ("SPY", "QQQ"):
        b = src(s)
        assert not b.empty, f"{s} has no bars"
        if s == "SPY":
            spyb = b
        fr.append(frame_from_bars(s, b, *keep))
    ctx = context_table(fr)
    p = work / "ctx.parquet"
    ctx.to_parquet(p)
    sd = spy_days_from_bars(spyb)
    sd = sd[(sd.index >= keep[0]) & (sd.index <= keep[1])]
    sd.to_parquet(work / "spy_days.parquet")
    return p, sd


def cmd_parity(work: Path, workers: int):
    g = guards()
    assert print_guards(g), "guards failed - parity not run"
    F = load_frozen()
    B32, B28, HUNT, BENCH, B23 = F["B32"], F["B28"], F["HUNT"], F["BENCH"], F["B23"]
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    R = {"note": "Educational only - not financial advice. FRESH harness parity check on 2025-10 (open data, "
                 "data/cache_hist). Harness: 1-minute bars -> streamed frames -> frozen month jobs -> frozen walks -> "
                 "frozen selection. References: the earlier pipelines' outputs.", "run_utc": utc(),
         "fresh_data_exists": FRESH_OUT.exists(), "checks": {}}
    # ---------------- reference A: the frozen ULT-32 / hunt pipelines on the stored lab frames (unpatched lib)
    _, s_ref, _ = B32.month_job("2025-10")
    bo2 = B32.blackout_set()
    s_ref["blackout"] = [(a, b) in bo2 for a, b in zip(s_ref.symbol, s_ref.date)]
    s_ref["side"], s_ref["evt"] = 1, 0
    B28.CACHE = HIST_1MIN
    BENCH.CACHE = HIST_1MIN
    w_ref = B28.walk(s_ref)
    _, h_ref, _, _ = HUNT.month_job("2025-10")
    etb = B28.etb_set()
    h_ref = h_ref[(h_ref.side > 0) | h_ref.symbol.isin(etb)].reset_index(drop=True)
    h_ref["evt"] = 0
    wh_ref = B28.walk(h_ref)
    ref = select_rules({"w32": w_ref, "wh": wh_ref, "wsb": pd.DataFrame(columns=["setup", "r1", "k1", "x1", "tod",
                                                                                  "geom"])}, bo2)
    print("reference built", round(time.time() - t0), "s", flush=True)
    # ---------------- harness: streamed frames from 1-minute bars (same code path as FRESH)
    ctx_p, sd = build_ctx("parity", work)
    syms = (HERE / "symbols_download_all.txt").read_text().split()
    for first in ("QQQ", "SPY"):
        syms.remove(first); syms.insert(0, first)
    rdir = work / "rows"
    shutil.rmtree(rdir, ignore_errors=True)
    st, fdates, _ = run_stream(syms, "parity", ctx_p, work, workers, 25, HIST_1MIN)
    rows = load_rows(rdir)
    bo_h = blackout_set("2024-08-01", "2026-12-31", extra_hol=False)
    har = select_rules(rows, bo_h)
    print("harness built", round(time.time() - t0), "s", flush=True)
    C = R["checks"]
    C["blackout_set_equal_to_ULT32_blackout_set"] = {"PASS": bo_h == bo2, "n": len(bo2)}
    bo_hx = blackout_set("2024-08-01", "2026-12-31", extra_hol=True)
    C["blackout_set_with_extra_holidays_same_on_2024_26"] = {"PASS": bo_hx == bo2}
    cal = sessions(*PARITY_MONTH)
    C["calendar_2025_10_vs_SPY_bar_dates"] = {"PASS": cal == sorted(sd.index.tolist()) == sorted(fdates),
                                              "n": len(cal)}
    sref = __import__("stats").spy_days()
    sref = sref[(sref.index >= PARITY_MONTH[0]) & (sref.index <= PARITY_MONTH[1])]
    C["spy_day_types_vs_benchmark_stats"] = {"PASS": bool((sref["type"] == sd.loc[sref.index, "type"]).all()
                                                          and len(sref) == len(sd))}
    # signal-row parity (supersets), before selection
    for nm, a, b in (("ULT-32 superset rows", rows["w32"], w_ref), ("H5V superset rows", rows["wh"], wh_ref)):
        a = a.assign(date=a.date.astype(str))
        b = b.assign(date=b.date.astype(str))
        k = ["symbol", "date", "tod"] + (["side"] if "side" in a else [])
        ma = a[k + ["r25T", "r25H"]].merge(b[k + ["r25T", "r25H"]], on=k, how="outer", indicator=True)
        both = ma[ma._merge == "both"]
        dd = max(float((both.r25T_x - both.r25T_y).abs().max() or 0), float((both.r25H_x - both.r25H_y).abs().max() or 0)) \
            if len(both) else 0.0
        C[nm] = {"n_harness": len(a), "n_reference": len(b), "matched": len(both), "max_abs_diff_T_H": dd,
                 "PASS": bool(len(a) == len(b) == len(both) and dd <= TOL)}
    # rule trades
    C["R1 BOOK-EM 32e vs frozen ULT-32 pipeline"] = cmp_trades(har["R1"], ref["R1"], extra=("leg",))
    C["R2 leg E"] = cmp_trades(har["R2"], ref["R2"])
    C["R3 leg M"] = cmp_trades(har["R3"], ref["R3"])
    C["R6 ST7-base vs frozen ULT-32 dissect_sel"] = cmp_trades(har["R6"], ref["R6"])
    st32 = pd.read_csv(U1119 / "round4" / "ULT-32" / "check_trades.csv.gz")
    st32 = st32[st32.date.str[:7] == "2025-10"]
    C["reference reproduces stored ULT-32 check_trades (32f, 2025-10)"] = cmp_trades(ref["_32f"], st32, extra=("leg",))
    C["harness 32f vs stored ULT-32 check_trades (2025-10)"] = cmp_trades(har["_32f"], st32, extra=("leg",))
    bw = pd.read_parquet(ROOT.parent / "bench_w" / "trades.parquet") if (ROOT.parent / "bench_w" / "trades.parquet").exists() \
        else None
    assert bw is not None, "benchmark pipeline output (scratchpad/bench_w/trades.parquet) missing"
    bw = bw[bw.date.astype(str).str[:7] == "2025-10"]
    C["R4 ST7-FD vs benchmark pipeline trades.parquet"] = cmp_trades(har["R4"], bw[bw.setup == ST7].assign(r=lambda x: x.r1))
    C["R5 NM-ETF vs benchmark pipeline trades.parquet"] = cmp_trades(har["R5"], bw[bw.setup == NM].assign(r=lambda x: x.r1))
    hv = pd.read_csv(HERE / "hunt_volume" / "check_trades.csv.gz")
    hv = hv[hv.date.str[:7] == "2025-10"]
    C["H-V1 vs stored H5V check_trades (2025-10)"] = cmp_trades(har["H-V1"], hv[hv.leg == "X"])
    C["H-V2 vs stored H5V check_trades (2025-10)"] = cmp_trades(har["H-V2"], hv[hv.leg == "K"])
    C["H-V1 vs frozen hunt pipeline"] = cmp_trades(har["H-V1"], ref["H-V1"])
    C["H-V2 vs frozen hunt pipeline"] = cmp_trades(har["H-V2"], ref["H-V2"])
    rq = {k: v for k, v in C.items()}
    R["symbols"] = {"requested": len(syms), "ok": sum(v == "ok" for v in st.values()),
                    "not_ok": {k: v for k, v in st.items() if v != "ok"}}
    R["required"] = ["R1 BOOK-EM 32e vs frozen ULT-32 pipeline", "R2 leg E", "R3 leg M",
                     "R4 ST7-FD vs benchmark pipeline trades.parquet", "R5 NM-ETF vs benchmark pipeline trades.parquet",
                     "R6 ST7-base vs frozen ULT-32 dissect_sel",
                     "reference reproduces stored ULT-32 check_trades (32f, 2025-10)",
                     "H-V1 vs stored H5V check_trades (2025-10)", "H-V2 vs stored H5V check_trades (2025-10)",
                     "blackout_set_equal_to_ULT32_blackout_set", "blackout_set_with_extra_holidays_same_on_2024_26",
                     "calendar_2025_10_vs_SPY_bar_dates", "spy_day_types_vs_benchmark_stats"]
    R["PASS"] = all(rq[k]["PASS"] for k in R["required"])
    R["random_pairing_smoke"] = {rid: rand_pair(rid, har[rid], rows) for rid in ("R1", "R4", "R5", "R6", "H-V1", "H-V2")}
    pins = {"fresh_bt.py": HERE / "fresh_bt.py", "FRESH_PLAN.md": HERE / "FRESH_PLAN.md",
            "FREEZE_HUNT.json": HERE / "FREEZE_HUNT.json", "FREEZE_CORE.json": HERE / "FREEZE_CORE.json",
            "download_fresh.py": HERE / "download_fresh.py", "mcf/research/heat.py": ROOT / "mcf" / "research" / "heat.py",
            "data/universe.csv (ETB flag)": ROOT / "data" / "universe.csv",
            "symbols_download_all.txt": HERE / "symbols_download_all.txt"}
    R["pins"] = {k: {"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for k, p in pins.items()}
    R["seconds"] = round(time.time() - t0)
    for k, v in C.items():
        print(("PASS" if v["PASS"] else "FAIL"), k, {kk: v[kk] for kk in v if kk != "PASS"}, flush=True)
    PARITY_FILE.write_text(json.dumps(R, indent=1, default=str))
    print("PARITY", "PASS" if R["PASS"] else "FAIL", flush=True)
    return R


# ===================================================================== FRESH stream
def cmd_stream(workers: int, stop_iso: str, batch: int):
    g = guards(fresh_mode=True)
    assert print_guards(g), "REFUSED: a guard failed - no fresh byte fetched"
    load_frozen()
    me = sha(HERE / "fresh_bt.py")
    sp = FRESH_OUT / "stream_state.json"
    if sp.exists():
        state = json.loads(sp.read_text())
        assert state["harness_sha256"] == me, "harness changed since the stream started"
    else:
        assert (not FRESH_OUT.exists()) or not any(FRESH_OUT.iterdir()), \
            "cache_fresh exists and is not empty, with no stream state: refusing (plan sec. 7)"
        (FRESH_OUT / "1Min").mkdir(parents=True, exist_ok=True)
        (FRESH_OUT / "daily").mkdir(parents=True, exist_ok=True)
        state = {"note": "Educational only - not financial advice.", "started_utc": utc(), "harness_sha256": me,
                 "done": [], "status": {}, "batches": 0}
        sp.write_text(json.dumps(state, indent=1))
    retained = set((HERE / "symbols_retained.txt").read_text().split())
    if not (FRESH_OUT / "ctx.parquet").exists():
        ctx_p, sd = build_ctx("fresh", FRESH_OUT)
        cal = sessions(WARM0, FRESH_END)
        spy_all = sorted(str(x) for x in pd.read_parquet(FRESH_OUT / "daily" / "SPY.parquet")["date"])
        assert spy_all == cal, f"calendar mismatch vs SPY bar dates: {sorted(set(cal) ^ set(spy_all))[:10]}"
        assert len([d for d in cal if d >= FRESH0]) == 427
    ctx_p = FRESH_OUT / "ctx.parquet"
    syms = [s for s in (HERE / "symbols_download_all.txt").read_text().split() if s not in set(state["done"])]
    for first in ("QQQ", "SPY"):
        if first in syms:
            syms.remove(first); syms.insert(0, first)
    st, _, stopped = run_stream(syms, "fresh", ctx_p, FRESH_OUT, workers, batch, FRESH_OUT / "1Min", stop_iso,
                                state, sp, retained)
    state["last_run_utc"] = utc()
    state["complete"] = (not stopped) and set(state["done"]) | {k for k, v in state["status"].items()
                                                                 if v in ("empty", "no_frame") or v.startswith("failed")} \
        >= set((HERE / "symbols_download_all.txt").read_text().split())
    sp.write_text(json.dumps(state, indent=1))
    shutil.rmtree(FRESH_OUT / "tmp", ignore_errors=True)
    print("stream", "COMPLETE" if state["complete"] else "PARTIAL (resume with the same command)", flush=True)


# ===================================================================== score (once)
def score(rows: dict, days: list[str], spyd: pd.DataFrame, bo: set, halves: dict, check_ref: dict) -> dict:
    F = load_frozen()
    F["B23"].SPY = spyd                                       # SPY day types of the scored window
    tr = select_rules(rows, bo)
    n = len(days)
    tb = max(1.5, math.sqrt(2 * math.log(M_RULES)))
    st7 = rule_stats(tr["R4"], n, halves)
    out = {"M": M_RULES, "t_bar": round(tb, 3), "sessions": n, "rules": {}}
    names = {"R1": "BOOK-EM (ULT-32 32e)", "R2": "leg E", "R3": "leg M", "R4": "ST7-FD (bench)",
             "R5": "NM-ETF-late-dip (bench)", "R6": "ST7-base (chassis)", "H-V1": "leg X short", "H-V2": "leg K long"}
    for rid in names:
        o = rule_stats(tr[rid], n, halves)
        o["name"] = names[rid]
        o["random"] = rand_pair(rid, tr[rid], rows)
        chk = check_ref[rid]
        bars = {"avg_r_gt_0.0836": (o.get("avg_r") or -9) > 0.0836,
                "wo_best_day_gt_0.0734": (o.get("avg_r_wo_best_day") or -9) > 0.0734,
                "r_per_session_gt_0": (o.get("total_r_per_session") or -9) > 0,
                f"t_ge_{tb:.3f}": (o.get("t_day_clustered") or -9) >= tb, "positive_on_check_half": chk > 0}
        o["bar"] = bars
        o["BEATS"] = all(bars.values())
        o["beats_ST7FD_fresh_avg_r"] = (o.get("avg_r") or -9) > (st7.get("avg_r") or 9)
        f1, f2 = o.get("FRESH-1_avg_r"), o.get("FRESH-2_avg_r")
        o["sign_flip_FRESH1_FRESH2"] = bool(f1 is not None and f2 is not None and np.sign(f1) != np.sign(f2))
        out["rules"][rid] = o
    out["R1_uncapped_trades"] = int(tr["_R1_uncapped"].r.notna().sum())
    out["R1_capped_trades"] = int(tr["R1"].r.notna().sum())
    for hid in HV:
        out[f"{hid}_uncapped_trades"] = int(tr[f"_{hid}_uncapped"].r.notna().sum())
    out["R1_no_blackout"] = {k: v for k, v in rule_stats(tr["_R1_no_blackout"], n, halves).items()
                             if k in ("trades", "avg_r", "avg_r_wo_best_day")}
    return out, tr


CHECK_REF = {"R1": 0.115, "R2": 0.110, "R3": 0.124, "R4": 0.084, "R5": 0.052, "R6": 0.094, "H-V1": 0.105, "H-V2": 0.187}


def cmd_score(dry_work: Path | None):
    if dry_work is None:
        g = guards(fresh_mode=True)
        assert print_guards(g), "guards failed"
        assert not ONCE_FILE.exists(), "FRESH is scored ONCE per rule (fresh_once.json exists)"
        state = json.loads((FRESH_OUT / "stream_state.json").read_text())
        assert state.get("complete"), "the stream is not complete"
        assert state["harness_sha256"] == sha(HERE / "fresh_bt.py")
        rows = load_rows(FRESH_OUT / "rows")
        days = [d for d in sessions(WARM0, FRESH_END) if d >= FRESH0]
        assert len(days) == 427
        spyd = pd.read_parquet(FRESH_OUT / "spy_days.parquet")
        bo = blackout_set(*BO_RANGE_FRESH)
        halves = {"FRESH-1": (FRESH0, FRESH1_END, len([d for d in days if d <= FRESH1_END])),
                  "FRESH-2": (FRESH2_0, FRESH_END, len([d for d in days if d >= FRESH2_0]))}
    else:
        load_frozen()
        rows = load_rows(dry_work / "rows")
        days = sessions(*PARITY_MONTH)
        spyd = pd.read_parquet(dry_work / "spy_days.parquet")
        bo = blackout_set("2024-08-01", "2026-12-31", extra_hol=False)
        halves = {"P-1": ("2025-10-01", "2025-10-15", len([d for d in days if d <= "2025-10-15"])),
                  "P-2": ("2025-10-16", "2025-10-31", len([d for d in days if d >= "2025-10-16"]))}
    for k in ("w32", "wh", "wsb"):
        assert len(rows[k]), f"no {k} rows"
        dd = rows[k]["date"].astype(str)
        assert dd.min() >= days[0] and dd.max() <= days[-1]
    o, tr = score(rows, days, spyd, bo, halves, CHECK_REF)
    o["note"] = "Educational only - not financial advice."
    o["scored_utc"] = utc()
    o["harness_sha256"] = sha(HERE / "fresh_bt.py")
    o["window"] = f"{days[0]}..{days[-1]}"
    keep = ["symbol", "date", "tod", "leg", "exit", "r", "kd", "hold"]
    allt = pd.concat([t.assign(rule=rid)[["rule"] + [c for c in keep if c in t]] for rid, t in tr.items()
                      if not rid.startswith("_")], ignore_index=True)
    if dry_work is None:
        ONCE_FILE.write_text(json.dumps(o, indent=1, default=float))
        allt.to_csv(HERE / "fresh_trades.csv.gz", index=False)
    else:
        (dry_work / "score_dry.json").write_text(json.dumps(o, indent=1, default=float))
    for rid, r in o["rules"].items():
        print(rid, r["name"], r.get("trades"), r.get("avg_r"), r.get("avg_r_wo_best_day"), r.get("t_day_clustered"),
              "BEATS" if r["BEATS"] else "-", flush=True)
    return o


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["guards", "parity", "stream", "score", "score-dry"])
    ap.add_argument("work", nargs="?")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--stop-utc", default="2026-11-19T13:15")
    a = ap.parse_args()
    if a.stage == "guards":
        sys.exit(0 if print_guards(guards(fresh_mode=True)) else 1)
    elif a.stage == "parity":
        r = cmd_parity(Path(a.work), a.workers)
        sys.exit(0 if r["PASS"] else 1)
    elif a.stage == "stream":
        cmd_stream(min(a.workers, 4), a.stop_utc, a.batch)
    elif a.stage == "score":
        cmd_score(None)
    else:
        cmd_score(Path(a.work))
