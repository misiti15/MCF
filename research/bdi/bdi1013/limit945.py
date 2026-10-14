"""Part A step 1 (PLAN.md): per eligible symbol-day, the 09:45 dip features and the net R of every entry variant
(MKT / 24 LIM / 24 CHASE) x 3 exits on 1-minute bars, production costs in. Open two-year history only: the locked
block is refused by lib.load_month and its 1-minute cache rows are dropped right after each read.
Output (scratch, not the repo): <out>/limit945.npz.   python limit945.py <out_dir>
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
import lib  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research import gates  # noqa: E402

LOCK = (np.datetime64("2024-11-01"), np.datetime64("2025-02-28"))
NM = 390
M0, MX = 15, 384                       # 09:45 minute (first after the 09:45 close), 15:54 minute (15:55 bar close)
SP, BP, SX = gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA
FEE_BP = 0.5e-4                        # filled-limit entry: fee proxy only
EXITS = {"t1s05": (1.0, 0.5), "t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}
OFFS = [("b0", 0.0, 0.0), ("b5", 5e-4, 0.0), ("b10", 10e-4, 0.0), ("b20", 20e-4, 0.0), ("a05", 0.0, 0.05), ("a10", 0.0, 0.10)]
VALS = [1, 3, 5, 10]
ENTRIES = ["MKT"] + [f"{p}-{o}-v{v}" for p in ("LIM", "CHASE") for o, _, _ in OFFS for v in VALS]
DATES = sorted(set(lib.daily()["date"]))
D64 = np.array([np.datetime64(str(x)) for x in DATES])
ND = len(DATES)


def tod_end(minute):
    m = 570 + minute + 1
    return (m // 60) * 100 + m % 60


def minutes(store, sym):
    df = store.load(sym)
    if df is None or df.empty:
        return None
    day = df.index.tz_localize(None).normalize().to_numpy().astype("datetime64[D]")
    keep = ~((day >= LOCK[0]) & (day <= LOCK[1]))                     # locked block dropped first
    df, day = df[keep], day[keep]
    m = (df.index.hour * 60 + df.index.minute).to_numpy() - 570
    di = np.searchsorted(D64, day)
    ok = (m >= 0) & (m < NM) & (di < ND)
    ok[ok] &= D64[di[ok]] == day[ok]
    df, m, di = df[ok], m[ok], di[ok]
    out = {}
    for k in ("open", "high", "low", "close", "volume"):
        a = np.full((ND, NM), np.nan)
        a[di, m] = df[k].to_numpy(float)
        out[k] = a
    return out


def sim(O, H, L, C, px, R, ext, stop_from, both_from, entry_cost, up, dn):
    """Long exits on minutes M0..MX. Stop checked from `stop_from`, target from `both_from` (per row). Returns net R."""
    n = len(px)
    stop, tgt = px - dn * R, px + up * R
    idx = np.arange(M0, MX + 1)[None, :]
    Lw, Hw, Ow = L[:, M0:MX + 1], H[:, M0:MX + 1], O[:, M0:MX + 1]
    with np.errstate(invalid="ignore"):
        hs = (Lw <= stop[:, None]) & (idx >= stop_from[:, None])
        ht = (Hw >= tgt[:, None]) & (idx >= both_from[:, None])
    big = Lw.shape[1] + 1
    fs = np.where(hs.any(1), np.argmax(hs, 1), big)
    ft = np.where(ht.any(1), np.argmax(ht, 1), big)
    stopped = (fs <= ft) & (fs < big)
    won = ft < fs
    rows = np.arange(n)
    fsc = np.minimum(fs, big - 2)
    o_s = Ow[rows, fsc]
    in_fill_min = (fsc + M0) < both_from                                  # stop in the fill minute: at the stop price
    xs = np.where(in_fill_min, stop, np.fmin(o_s, stop))
    xp = np.where(stopped, xs, np.where(won, tgt, C[:, MX]))
    cost = entry_cost + np.where(won, 0.0, SP + xp * BP) + np.where(stopped, SX, 0.0)
    net = (xp - px) / R - np.where(ext, 3.0, 1.0) * cost / R
    net[~np.isfinite(px)] = np.nan
    return net


def work(args):
    sym, sess, atr, gap = args
    mn = minutes(BarStore(ROOT / "data" / "cache_hist"), sym)
    n = len(sess)
    res = {"MKTR": None}
    if mn is None:
        return sym, None
    O, H, L, C, V = (mn[k][sess] for k in ("open", "high", "low", "close", "volume"))
    have = np.isfinite(C[:, :M0]).any(1) & np.isfinite(C[:, M0:MX + 1]).any(1)
    Cf = pd.DataFrame(C).ffill(axis=1).bfill(axis=1).to_numpy()
    miss = ~np.isfinite(C)
    O, H, L, C = (np.where(miss, Cf, x) for x in (O, H, L, C))
    V = np.nan_to_num(V)
    o0 = O[:, 0]
    c945 = C[:, M0 - 1]
    vb = V[:, :15].reshape(n, 3, 5).sum(2)
    capd = vb[:, 2] <= 0.5 * vb.max(1)
    pc = o0 / (1 + gap / 100)
    R = 0.25 * atr
    out = {"have": have, "o0": o0, "c945": c945, "pc": pc, "capd": capd}
    nets = np.full((len(ENTRIES), len(EXITS), n), np.nan, np.float32)
    fillmin = np.full((len(OFFS), len(VALS)), -1, int)
    fills = np.full((len(OFFS) * len(VALS), n), -1, np.int16)
    ext_m = (np.abs(gap) >= 20) | (c945 < 5)
    mkt_cost = (SP + c945 * BP) * float(gates.tod_cost_mult(945))
    for j, (ex, (up, dn)) in enumerate(EXITS.items()):
        nets[0, j] = sim(O, H, L, C, c945, R, ext_m, np.full(n, M0), np.full(n, M0), mkt_cost, up, dn)
    e = 1
    nv = len(OFFS) * len(VALS)
    for oi, (on, bp, a) in enumerate(OFFS):
        lim = np.round(c945 * (1 - bp) - a * atr, 2)
        through = L[:, M0:M0 + 10] <= (lim - 0.01)[:, None] + 1e-9
        for vi, v in enumerate(VALS):
            t = through[:, :v]
            got = t.any(1)
            fm = np.where(got, M0 + np.argmax(t, 1), -1)
            fills[oi * len(VALS) + vi] = fm
            ext = (np.abs(gap) >= 20) | (lim < 5)
            lim_cost = lim * FEE_BP
            px = np.where(got, lim, np.nan)
            for j, (ex, (up, dn)) in enumerate(EXITS.items()):
                r_lim = sim(O, H, L, C, px, R, ext, np.where(got, fm, M0), np.where(got, fm + 1, M0), lim_cost, up, dn)
                nets[e, j] = r_lim
                # CHASE: unfilled -> market at the close of the last valid minute
                cm = M0 + v - 1
                pch = C[:, cm]
                ext_c = (np.abs(gap) >= 20) | (pch < 5)
                ch_cost = (SP + pch * BP) * float(gates.tod_cost_mult(tod_end(cm)))
                r_ch = sim(O, H, L, C, pch, R, ext_c, np.full(n, cm + 1), np.full(n, cm + 1), ch_cost, up, dn)
                nets[e + nv, j] = np.where(got, r_lim, r_ch)
            e += 1
    bad = ~have | ~np.isfinite(R) | (R <= 0)
    nets[:, :, bad] = np.nan
    out["nets"] = nets
    out["fills"] = fills
    return sym, out


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    sidx = {d: i for i, d in enumerate(DATES)}
    parts = []
    for m in lib.months():
        assert m not in lib.LOCKED_MONTHS
        f = lib.load_month(m, ["symbol", "date", "tod", "atr_d", "adv20", "gap"])
        f = f[(f.tod == 950) & (f.adv20 >= 95e6) & (f.atr_d > 0)]
        parts.append(f)
    F = pd.concat(parts, ignore_index=True)
    F["symbol"] = F["symbol"].astype(str)
    F["sess"] = F["date"].map(sidx)
    F = F.dropna(subset=["sess"]).sort_values(["symbol", "sess"]).reset_index(drop=True)
    F["sess"] = F["sess"].astype(int)
    print("eligible symbol-days", len(F), flush=True)
    jobs = [(s, g.sess.to_numpy(), g.atr_d.to_numpy(float), g.gap.to_numpy(float)) for s, g in F.groupby("symbol", sort=True)]
    res = {}
    with Pool(4) as p:
        for i, (sym, r) in enumerate(p.imap_unordered(work, jobs, chunksize=2)):
            res[sym] = r
            if i % 100 == 0:
                print("sym", i, len(jobs), flush=True)
    keys = ["have", "o0", "c945", "pc", "capd"]
    A = {k: [] for k in keys + ["nets", "fills"]}
    for sym, g in F.groupby("symbol", sort=True):
        r, n = res[sym], len(g)
        if r is None:
            A["have"].append(np.zeros(n, bool)); A["capd"].append(np.zeros(n, bool))
            for k in ("o0", "c945", "pc"):
                A[k].append(np.full(n, np.nan))
            A["nets"].append(np.full((len(ENTRIES), len(EXITS), n), np.nan, np.float32))
            A["fills"].append(np.full((len(OFFS) * len(VALS), n), -1, np.int16))
            continue
        for k in keys:
            A[k].append(r[k])
        A["nets"].append(r["nets"]); A["fills"].append(r["fills"])
    Z = {k: np.concatenate(v, axis=-1) for k, v in A.items()}
    F[["symbol", "date", "sess", "atr_d", "adv20", "gap"]].assign(date=lambda x: pd.to_datetime(x.date)).to_parquet(out / "days.parquet", index=False)
    np.savez(out / "limit945.npz", entries=np.array(ENTRIES), exits=np.array(list(EXITS)), **Z)
    print("done", Z["nets"].shape, flush=True)


if __name__ == "__main__":
    main()
