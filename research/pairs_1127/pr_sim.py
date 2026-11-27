"""PAIRS-1127 simulator (PREREG.md): sector-ETF hedge, prior-60-session beta, residual z, 28 configs, costs on both legs.
Usage: python pr_sim.py DATADIR OUTDIR. Writes trades.pkl + paths.npz (scratch, not committed).
Educational only - not financial advice."""
from __future__ import annotations
import json, re, sys
from datetime import date
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

LOCK_A, LOCK_B = date(2024, 11, 1), date(2025, 2, 28)
ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH"]
ETF_RE = re.compile(r"\bETFs?\b|\bETN\b|\bFund\b|iShares|ProShares|Direxion|SPDR|Invesco QQQ|GraniteShares|Tradr|"
                    r"Defiance|T-Rex|Leverage Shares|\b[23]X\b|UltraPro|Ultra(?:Short)? |Grayscale|Bitcoin|Ether(?:eum)? |Trust\b", re.I)
NB = 78
CELLS = json.load(open(Path(__file__).resolve().parents[1] / "primshorts_1126" / "cells_live.json"))
SEC_FROM = date(2026, 4, 4); SEC_BP = 20.60 / 1e6 * 1e4
# configs
CFG = []
for base in ("OPEN", "R60"):
    for k in (2.5, 3.0, 4.0):
        for xm in ("full", "half"):
            for hold in ("60", "EOD"):
                CFG.append(dict(base=base, k=k, x=0.0 if xm == "full" else 0.5 * k, xm=xm, hold=hold, top=500))
for base in ("OPEN", "R60"):
    for k in (3.0, 4.0):
        CFG.append(dict(base=base, k=k, x=0.5 * k, xm="half", hold="EOD", top=200))
for i, c in enumerate(CFG):
    c["id"] = f"P{i+1:02d}"
    c["name"] = f"{c['base']}-k{c['k']}-{c['xm']}-{c['hold']}-T{c['top']}"
assert len(CFG) == 28

DATA = None; CAL = None; EARR = None; TOPRANK = None; SYMIDX = None


def pbucket(p):
    return "5-10" if p < 10 else "10-20" if p < 20 else "20-50" if p < 50 else "50-100" if p < 100 else "100+"


def load(sym):
    z = np.load(DATA / f"{sym}.npz")
    C = z["C"].astype(np.float64); O1 = z["O1"].astype(np.float64); O2 = z["O2"].astype(np.float64)
    return C, O1, O2, z["dv"], z["nmin"]


def ffill_day(C, O1, O2):
    # forward-fill closes within the day; missing opens take the previous close
    C = pd.DataFrame(C).ffill(axis=1).to_numpy()
    prevc = np.c_[np.full(len(C), np.nan), C[:, :-1]]
    O1 = np.where(np.isnan(O1), prevc, O1); O2 = np.where(np.isnan(O2), O1, O2)
    return C, O1, O2


def rets(C, O1):
    r = np.empty_like(C)
    r[:, 0] = np.log(C[:, 0] / O1[:, 0])
    r[:, 1:] = np.log(C[:, 1:] / C[:, :-1])
    return r


def work(sym):
    try:
        return _work(sym)
    except Exception as ex:  # noqa: BLE001
        print("ERR", sym, ex, flush=True)
        return None


def _work(sym):
    C, O1, O2, dv, nmin = load(sym)
    D = len(CAL)
    full = (np.isfinite(C).sum(1) >= 74) & np.isfinite(O1[:, 0])
    C, O1, O2 = ffill_day(C, O1, O2)
    r = rets(C, O1)
    r[~full] = np.nan
    si = SYMIDX[sym]
    rank = TOPRANK[si]                     # rank per day (1 = top), 9999 if not eligible
    # per-ETF daily stats
    E = len(ETFS)
    Sxy = np.zeros((D, E)); Sxx = np.zeros((D, E)); Syy = np.zeros((D, E)); Nn = np.zeros((D, E))
    for e in range(E):
        re_ = EARR[e]["r"]
        ok = np.isfinite(r) & np.isfinite(re_)
        a = np.where(ok, r, 0); b = np.where(ok, re_, 0)
        Sxy[:, e] = (a * b).sum(1); Sxx[:, e] = (b * b).sum(1); Syy[:, e] = (a * a).sum(1); Nn[:, e] = ok.sum(1)
    valid = np.nonzero(full)[0]
    out = []; paths = []
    if len(valid) < 52:
        return None
    cs = [np.cumsum(np.r_[np.zeros((1, E)), X[valid]], 0) for X in (Sxy, Sxx, Syy, Nn)]
    for p in range(50, len(valid)):
        d = valid[p]
        if rank[d] > 500:
            continue
        lo = max(0, p - 60)
        sxy, sxx, syy, nn = [c[p] - c[lo] for c in cs]
        corr = sxy / np.sqrt(sxx * syy)
        e = int(np.nanargmax(corr))
        if not corr[e] >= 0.30:
            continue
        beta = float(np.clip(sxy[e] / sxx[e], 0.2, 3.0))
        sig = float(np.sqrt(max(syy[e] - 2 * beta * sxy[e] + beta * beta * sxx[e], 1e-12) / nn[e]))
        ER = EARR[e]
        if not ER["full"][d]:
            continue
        rr = r[d] - beta * ER["r"][d]
        X = np.cumsum(rr)
        zo = X / (sig * np.sqrt(np.arange(1, NB + 1)))
        z6 = np.full(NB, np.nan); z6[12:] = (X[12:] - X[:-12]) / (sig * np.sqrt(12))
        P1 = np.log(O1[d]) - beta * np.log(ER["O1"][d])
        P2 = np.log(O2[d]) - beta * np.log(ER["O2"][d])
        pS = O1[d]; pE = ER["O1"][d]
        if not (np.isfinite(P1).all() and np.isfinite(P2).all()):
            continue
        dd = CAL[d]
        sec = SEC_BP if dd >= SEC_FROM else 0.0
        paths.append((d, si, rank[d], P1.astype(np.float32)))
        for c in CFG:
            if rank[d] > c["top"]:
                continue
            z = zo if c["base"] == "OPEN" else z6
            k = c["k"]
            js = np.nonzero(np.abs(z[5:66]) > k)[0]
            if not len(js):
                continue
            j = 5 + js[0]
            s = 1.0 if z[j] > 0 else -1.0   # residual sign; stock side = -s
            a = j + 1
            nref = (j + 1) if c["base"] == "OPEN" else 12
            W = 2 * sig * np.sqrt(nref) * 1e4
            b_ = 77; kind = "eod"
            last = 76 if c["hold"] == "EOD" else min(76, a + 11)
            for jj in range(a, last + 1):
                zz = s * z[jj]
                if zz >= k + 2:
                    b_ = jj + 1; kind = "stop"; break
                if zz <= c["x"]:
                    b_ = jj + 1; kind = "rev"; break
            else:
                if c["hold"] != "EOD" and a + 12 <= 77:
                    b_ = min(77, a + 12); kind = "time"
            side = -s
            g1 = side * (P1[b_] - P1[a]) * 1e4
            g2 = side * (P2[b_] - P2[a]) * 1e4
            px = pS[a]; pe = pE[a]
            ek = "stop" if kind == "stop" else "market"
            ca, cb = CELLS[f"{pbucket(px)}|{ek}"][:2]
            stockL = ca + cb * W
            etfL = beta * 2 * (0.01 / pe * 1e4 + 1.0)
            stockL8 = 1.0 + (max(0.02 / px * 1e4, 4.0) if kind == "stop" else max(0.01 / px * 1e4, 1.0))
            etfL8 = beta * (1.0 + (max(0.02 / pe * 1e4, 4.0) if kind == "stop" else max(0.01 / pe * 1e4, 1.0)))
            fee = sec * (1 + beta)
            out.append((c["id"], d, sym, ETFS[e], side, beta, sig, W, j, a, b_, kind, px, g1, g2,
                        stockL + etfL + fee, stockL8 + etfL8 + fee, 4.0 * (1 + beta), stockL, etfL))
    return out, paths


def _init(data, cal, earr, toprank, symidx):
    global DATA, CAL, EARR, TOPRANK, SYMIDX
    DATA, CAL, EARR, TOPRANK, SYMIDX = data, cal, earr, toprank, symidx


def main(datadir, outdir):
    data = Path(datadir); out = Path(outdir)
    cal = [date.fromisoformat(x) for x in np.load(data / "_cal.npy")]
    assert not any(LOCK_A <= x <= LOCK_B for x in cal)
    D = len(cal)
    earr = []
    for e in ETFS:
        C, O1, O2, dv, nmin = load_g(data, e)
        full = (np.isfinite(C).sum(1) >= 74) & np.isfinite(O1[:, 0])
        C, O1, O2 = ffill_day(C, O1, O2)
        r = rets(C, O1); r[~full] = np.nan
        earr.append(dict(r=r, O1=O1, O2=O2, full=full))
    u = pd.read_csv("/home/user/MCF/data/universe.csv")
    etfname = set(u.symbol[u.name.fillna("").str.contains(ETF_RE)])
    syms = sorted(p.stem for p in data.glob("*.npz") if not p.stem.startswith("_"))
    hard = set(ETFS) | {"SPY", "QQQ", "IWM", "DIA", "TQQQ", "SQQQ", "SPXL", "SPXS", "SOXL", "SOXS", "TLT", "GLD", "SLV",
                        "UVXY", "VXX", "TNA", "TZA", "XBI", "KRE", "XOP", "GDX", "ARKK", "EEM", "EFA", "HYG", "LQD", "VOO", "IVV", "VTI"}
    stocks = [s for s in syms if s not in etfname and s not in hard]
    print("stocks", len(stocks), "excluded", len(syms) - len(stocks), flush=True)
    # liquidity rank per day: prior-20-session avg dollar volume, prior close >= $5
    ADV = np.full((len(stocks), D), np.nan); PC = np.full((len(stocks), D), np.nan)
    for i, s in enumerate(stocks):
        z = np.load(data / f"{s}.npz")
        dv = z["dv"].astype(float); dv[z["nmin"] < 200] = np.nan
        C = z["C"]
        lastc = pd.DataFrame(C).ffill(axis=1).iloc[:, -1].to_numpy()
        ADV[i] = pd.Series(dv).shift(1).rolling(20, min_periods=15).mean().to_numpy()
        PC[i] = pd.Series(lastc).shift(1).to_numpy()
    score = np.where((PC >= 5) & np.isfinite(ADV), ADV, -1)
    order = (-score).argsort(0); rank = np.empty_like(order); rank[order, np.arange(D)[None, :]] = np.arange(1, len(stocks) + 1)[:, None]
    rank = np.where(score > 0, rank, 9999)
    symidx = {s: i for i, s in enumerate(stocks)}
    trades = []; paths = []
    with Pool(4, initializer=_init, initargs=(data, cal, earr, rank, symidx)) as pool:
        for n, res in enumerate(pool.imap_unordered(work, stocks, chunksize=8)):
            if res:
                trades += res[0]; paths += res[1]
            if n % 200 == 0:
                print(n, len(trades), flush=True)
    cols = ["cfg", "d", "sym", "etf", "side", "beta", "sig", "W", "jdec", "a", "b", "kind", "px", "g1", "g2",
            "costL", "cost8", "stressadd", "stockL", "etfL"]
    df = pd.DataFrame(trades, columns=cols)
    df["date"] = [cal[i] for i in df.d]
    df.to_pickle(out / "trades.pkl")
    np.savez_compressed(out / "paths.npz", d=np.array([p[0] for p in paths]), si=np.array([p[1] for p in paths]),
                        rank=np.array([p[2] for p in paths]), P=np.stack([p[3] for p in paths]))
    json.dump(CFG, open(out / "cfg.json", "w"))
    print("done", len(df), len(paths), flush=True)


def load_g(data, sym):
    z = np.load(data / f"{sym}.npz")
    return z["C"].astype(np.float64), z["O1"].astype(np.float64), z["O2"].astype(np.float64), z["dv"], z["nmin"]


if __name__ == "__main__":
    DATA = Path(sys.argv[1])
    main(sys.argv[1], sys.argv[2])
