"""OF-A systematic test (NOTES 1.3-1.4), one symbol at a time (one process, low RAM):
  ic.parquet        per (symbol, day, feature, horizon): Spearman IC and incremental IC (beyond r10/r60/r300)
  lift.parquet      per (symbol, day, feature): swing-start counts for p90 / p10 flags and all sampled seconds
  lines.parquet     per (line, symbol, day): n, sums of primary / secondary / hedged P/L (bps), wins
Usage: python scan.py [SYM ...]. Educational only - not financial advice."""
from __future__ import annotations

import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

import of_lib as L
from mcf.research.gates import tod_cost_mult

OUT = L.DATA / "scan"
SIG = ["dlt60", "dlt300", "ofi60", "qimb10", "big60", "sweep30", "burst10", "absorb60", "cvd_div300", "fp_stack"]
PSIG = ["r60", "r300"]
QS = {"p99": 0.99, "p999": 0.999}
EXITS = {"E1": (0.005, 0.0025, 1800), "E2": (0.005, 0.005, 1800), "E3": (None, None, 300), "E4": (None, None, 900)}
CONF = {"dlt60": 0.8, "ofi60": 0.8, "sweep30": 0.9, "absorb60": 0.9, "qimb10": 0.8}
HOR = (10, 60, 300, 900)
END = 23370                                   # 15:59:30
COOL = 60
SAMPLE = np.arange(L.W0, 22500, 5)            # 09:50:00 .. 15:44:55
QLIST = sorted({0.001, 0.01, 0.1, 0.2, 0.8, 0.9, 0.99, 0.999})


def betas(b1: pd.DataFrame, sym: str) -> dict:
    x = b1[b1.symbol.isin([sym, "SPY"])].pivot_table(index="t", columns="symbol", values="close")
    r = np.log(x).diff()
    r["date"] = r.index.date.astype(str)
    r = r[r.date == r.date.shift(1)]
    dates = sorted(r.date.unique())
    out = {}
    for d in L.DAYS:
        i = dates.index(d)
        g = r[r.date.isin(dates[max(0, i - 20):i])].dropna()
        out[d] = float(np.clip(np.cov(g[sym], g["SPY"])[0, 1] / np.var(g["SPY"], ddof=1), 0, 3)) if sym != "SPY" else 1.0
    return out


class Day:
    def __init__(self, raw: pd.DataFrame, spy: pd.DataFrame, beta: float):
        self.bid, self.ask = raw.bid.to_numpy(float), raw.ask.to_numpy(float)
        self.mid = (self.bid + self.ask) / 2
        self.smid = spy.mid.to_numpy(float)
        self.sspr = (spy.ask - spy.bid).to_numpy(float)
        self.beta = beta

    def trade(self, s: int, side: int, ex: str):
        """Decision at the end of second s. Returns (exit_sec, r_primary, r_secondary, r_hedged) in bps."""
        e = s + 2
        up, dn, H = EXITS[ex]
        last = min(e + H, END)
        if side == 1:
            E = self.ask[e]
            ent = E * (1 + 1e-4)
        else:
            E = self.bid[e]
            ent = E * (1 - 1e-4)
        kind, x = "time", last
        if up is not None:
            T, S = E * (1 + side * up), E * (1 - side * dn)
            near = self.bid[e + 1:last + 1] if side == 1 else self.ask[e + 1:last + 1]
            ht = np.flatnonzero(side * (near - T) >= 0)
            hs = np.flatnonzero(side * (near - S) <= 0)
            it = ht[0] if len(ht) else 10**9
            is_ = hs[0] if len(hs) else 10**9
            if is_ <= it and is_ < 10**9:
                kind, x = "stop", e + 1 + is_
            elif it < 10**9:
                kind, x = "tgt", e + 1 + it
        if kind == "tgt":
            px, fx = T, x
        else:
            fx = min(x + 1, len(self.bid) - 1)
            raw = self.bid[fx] if side == 1 else self.ask[fx]
            px = (raw - side * (0.02 if kind == "stop" else 0.0)) * (1 - side * 1e-4)
        r1 = side * (px / ent - 1) * 1e4 if side == 1 else (1 - px / ent) * 1e4
        # secondary: mid-to-mid, production cost model with time-of-day entry multiplier
        Me = self.mid[e]
        Mx = T if kind == "tgt" else self.mid[fx]
        hh, mm = divmod(570 + e // 60, 60)
        cost = (0.01 + Me * 1e-4) * float(tod_cost_mult([hh * 100 + mm])[0]) + \
               (0.0 if kind == "tgt" else 0.01 + Mx * 1e-4) + (0.02 if kind == "stop" else 0.0)
        r2 = (side * (Mx / Me - 1) - cost / Me) * 1e4
        sret = self.smid[fx] / self.smid[e] - 1
        hc = self.beta * ((self.sspr[e] + self.sspr[fx]) / 2 / self.smid[e] + 2e-4)
        r3 = r1 - (side * self.beta * sret + hc) * 1e4
        return fx, r1, r2, r3


def run_line(day: Day, cand: np.ndarray, side: int, ex: str, acc: list, key: tuple):
    """cand: sorted decision seconds (already inside the entry window). Non-overlapping, 60 s cooldown."""
    n = s1 = s2 = s3 = w = 0.0
    free, i = -1, 0
    while True:
        i = np.searchsorted(cand, free, side="left")
        if i >= len(cand):
            break
        s = int(cand[i])
        fx, r1, r2, r3 = day.trade(s, side, ex)
        n += 1; s1 += r1; s2 += r2; s3 += r3; w += r1 > 0
        free = fx + COOL
    if n:
        acc.append(key + (int(n), s1, s2, s3, int(w)))


def window(mask: np.ndarray) -> np.ndarray:
    idx = np.flatnonzero(mask)
    return idx[(idx >= L.W0) & (idx <= L.W1)]


def ic_rows(sym, d, F: pd.DataFrame, mid: np.ndarray, out: list):
    lm = np.log(mid)
    t = SAMPLE
    cols = L.FLOW + L.PRICE
    X = F.iloc[t][cols].to_numpy(float)
    R = X.copy()
    ok_rows = np.isfinite(X).all(axis=1)
    rk = pd.DataFrame(X[ok_rows]).rank().to_numpy()
    base = np.column_stack([np.ones(ok_rows.sum()), rk[:, -3:]])
    resid_f = rk - base @ np.linalg.lstsq(base, rk, rcond=None)[0]
    for h in HOR:
        y = lm[t + h] - lm[t]
        y = y[ok_rows]
        if np.nanstd(y) == 0:
            continue
        ry = pd.Series(y).rank().to_numpy()
        ry_res = ry - base @ np.linalg.lstsq(base, ry, rcond=None)[0]
        for j, c in enumerate(cols):
            a = rk[:, j]
            ic = np.corrcoef(a, ry)[0, 1] if a.std() > 0 else np.nan
            ir = np.corrcoef(resid_f[:, j], ry_res)[0, 1] if j < len(cols) - 3 and resid_f[:, j].std() > 1e-9 else np.nan
            out.append((sym, d, c, h, ic, ir))
    del R


def swing_labels(mid: np.ndarray, t: np.ndarray, up=0.005, dn=0.0025, H=1800):
    pad = np.concatenate([mid, np.full(H + 1, mid[-1])])
    V = sliding_window_view(pad[1:], H)[t]            # mid[t+1 .. t+H]
    r = V / mid[t][:, None] - 1
    res = []
    for side in (1, -1):
        a = side * r >= up
        b = side * r <= -dn
        fa = np.where(a.any(1), a.argmax(1), 10**9)
        fb = np.where(b.any(1), b.argmax(1), 10**9)
        res.append((fa < fb) & (fa < 10**9))
    return res


def scan_symbol(sym: str, b1: pd.DataFrame, sigs: pd.DataFrame, spy_raw: dict):
    t0 = time.time()
    raws, feats, stats = {}, {}, []
    for i, d in enumerate(L.DAYS):
        raw = L.load_day(sym, d)
        if raw is None:
            raise RuntimeError(f"missing {sym} {d}")
        st = L.day_stats(raw)
        ref = L.ref_stats(stats if stats else [st])
        feats[d] = L.features(raw, ref)
        raws[d] = raw[["bid", "ask", "mid"]].copy()
        stats.append(st)
    beta = betas(b1, sym)
    ics, lifts, lines = [], [], []
    cols = SIG + PSIG + list(CONF)
    for i, d in enumerate(L.DAYS[1:], start=1):
        prior = pd.concat([feats[x].iloc[L.W0:L.W1 + 1] for x in L.DAYS[:i]])
        qv = {c: prior[c].quantile(QLIST).to_numpy() for c in set(cols + L.SIGNED)}
        Q = lambda c, q: qv[c][QLIST.index(q)]
        F = feats[d]
        mid = raws[d].mid.to_numpy()
        ic_rows(sym, d, F, mid, ics)
        Lb, Sb = swing_labels(mid, SAMPLE)
        for c in L.SIGNED:
            v = F[c].to_numpy()[SAMPLE]
            hi, lo = v >= Q(c, 0.9), v <= Q(c, 0.1)
            lifts.append((sym, d, c, len(v), int(Lb.sum()), int(Sb.sum()), int(hi.sum()), int((hi & Lb).sum()),
                          int(lo.sum()), int((lo & Sb).sum()), int((hi & Sb).sum()), int((lo & Lb).sum())))
        day = Day(raws[d], spy_raw[d], beta[d])
        # flow and price-only signals
        for c in SIG + PSIG:
            v = F[c].to_numpy()
            kind = "flow" if c in SIG else "price"
            for qn, q in QS.items():
                hi, lo = window(v >= Q(c, q)), window(v <= Q(c, round(1 - q, 3)))
                for mode in ("follow", "fade"):
                    lng, sht = (hi, lo) if mode == "follow" else (lo, hi)
                    for ex in EXITS:
                        run_line(day, lng, 1, ex, lines, (f"{kind}|{c}|{mode}|{qn}|{ex}", sym, d, "long"))
                        run_line(day, sht, -1, ex, lines, (f"{kind}|{c}|{mode}|{qn}|{ex}", sym, d, "short"))
        # bar setups, bare and with flow confirmation within 60 s of the bar close
        g = sigs[sigs.date == d] if len(sigs) else sigs
        for setup in ("c3b", "c6"):
            for side, sname in ((1, "long"), (-1, "short")):
                bc = np.sort((g.loc[g[f"{setup}_{sname}"], "m"].to_numpy(int) + 1) * 60) if len(g) else np.zeros(0, int)
                bc = bc[(bc >= L.W0) & (bc <= L.W1)]
                for ex in EXITS:
                    run_line(day, bc, side, ex, lines, (f"setup|{setup}|bare|-|{ex}", sym, d, sname))
                for cf, q in CONF.items():
                    v = F[cf].to_numpy()
                    ok = v >= Q(cf, q) if side == 1 else v <= Q(cf, round(1 - q, 3))
                    ent = []
                    for s0 in bc:
                        k = np.flatnonzero(ok[s0:s0 + 61])
                        if len(k) and s0 + k[0] <= L.W1:
                            ent.append(s0 + k[0])
                    ent = np.unique(np.array(ent, int))
                    for ex in EXITS:
                        run_line(day, ent, side, ex, lines, (f"setup|{setup}|conf_{cf}|-|{ex}", sym, d, sname))
        # random baseline: 10 random decision seconds per symbol-day and side
        rng = np.random.default_rng(zlib.crc32(f"{sym}|{d}".encode()))
        for side, sname in ((1, "long"), (-1, "short")):
            cand = np.sort(rng.integers(L.W0, L.W1 + 1, 10))
            for ex in EXITS:
                run_line(day, cand, side, ex, lines, (f"random|-|-|-|{ex}", sym, d, sname))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(ics, columns=["symbol", "date", "feature", "h", "ic", "ic_resid"]).to_parquet(OUT / f"ic_{sym}.parquet", index=False)
    pd.DataFrame(lifts, columns=["symbol", "date", "feature", "n", "L", "S", "n_hi", "L_hi", "n_lo", "S_lo", "S_hi", "L_lo"]).to_parquet(OUT / f"lift_{sym}.parquet", index=False)
    pd.DataFrame(lines, columns=["line", "symbol", "date", "side", "n", "sum_r", "sum_r2", "sum_rh", "wins"]).to_parquet(OUT / f"lines_{sym}.parquet", index=False)
    print(sym, round(time.time() - t0, 1), "s", len(lines), "line-days", flush=True)


def main():
    syms = sys.argv[1:] or [s for s in L.SYMBOLS]
    b1 = L.bars1m()
    atr = L.daily_atr(b1)["atr_d"]
    spy_raw = {d: L.load_day("SPY", d)[["bid", "ask", "mid"]] for d in L.DAYS}
    for sym in syms:
        if (OUT / f"lines_{sym}.parquet").exists():
            continue
        if not all((L.SEC / sym / f"{d}.parquet").exists() for d in L.DAYS):
            print("skip (not downloaded)", sym)
            continue
        sigs = L.signatures_1m(b1[b1.symbol == sym], atr)
        scan_symbol(sym, b1, sigs, spy_raw)


if __name__ == "__main__":
    main()
