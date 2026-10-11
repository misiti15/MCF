"""One pass over the 1-minute SIP cache (NOTES 1.1 / 1.3). Locked-block rows are dropped right after each load.
Outputs (git-ignored, data/):
  C5.f32, V5.f32  [symbol, session, 78]   5-minute close / volume, bar-close tod 09:35..16:00
  O0.f32, CL.f32  [symbol, session]       first 1-minute open, last 1-minute close
  etf1m.npz                               1-minute O/H/L/C/V [etf, session, 390] for the index / sector / macro ETFs
  leadlag.npz                             per symbol 1-minute lead-lag sums vs SPY / QQQ (lags 0..15), by split
  lltrade.npz                             ix-leadlag tradable test: per config x session sums, per config x symbol sums
  meta.json
Educational only - not financial advice."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = HERE / "data"
SECTOR = "XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS".split()
ETF1M = ["SPY", "QQQ", "IWM", "DIA"] + SECTOR + ["VXX", "UVXY", "TLT", "GLD", "USO", "UUP"]
W2ETFS = set(("ARKK ASHR BITO BOIL CONL DIA EEM EFA ETHA EWJ EWT EWY EWZ FBTC FXI GBTC GDX GDXJ GLD IBB IBIT IEMG IGV ITB "
              "IWF IWM IYR JETS KBE KRE KWEB LABD MDY MSTU MTUM NUGT NVDL OIH PSQ QID QQQ SCO SDS SLV SMH SOXL SOXS SOXX "
              "SPXL SPXS SPY SQQQ TLT TMF TNA TQQQ TSLL TZA UCO UNG UPRO USO UVXY VEA VNQ VUG VWO VXX XBI XHB XLB XLC XLE "
              "XLF XLI XLK XLP XLRE XLU XLV XLY XME XOP XRT").split())
LOCK = (np.datetime64("2024-11-01"), np.datetime64("2025-02-28"))
NM, NB = 390, 78
LAGS = 16


def main():
    syms = (ROOT / "research" / "lab_symbols.txt").read_text().split()
    dly = lib.daily()
    dates = sorted(set(dly["date"]))
    d64 = np.array([np.datetime64(str(x)) for x in dates])
    ND, NS = len(dates), len(syms)
    split = np.array([str(x) > "2025-12-31" for x in dates])            # False = train, True = valid
    adv = (dly.pivot_table(index="date", columns="symbol", values="adv20").reindex(index=dates, columns=syms)
           .to_numpy(np.float64))
    store = BarStore(ROOT / "data" / "cache_hist")

    def minutes(sym):
        if sym == "UUP":
            u = pd.read_parquet(DATA / "uup_1min.parquet").set_index("ts")
            df = u
        else:
            df = store.load(sym)
        if df.empty:
            return None
        day = df.index.tz_localize(None).normalize().to_numpy().astype("datetime64[D]")
        keep = ~((day >= LOCK[0]) & (day <= LOCK[1]))                    # locked block dropped first
        df, day = df[keep], day[keep]
        m = (df.index.hour * 60 + df.index.minute).to_numpy() - 570
        di = np.searchsorted(d64, day)
        ok = (m >= 0) & (m < NM) & (di < ND)
        ok[ok] &= d64[di[ok]] == day[ok]
        df, m, di = df[ok], m[ok], di[ok]
        out = {}
        for k in ("open", "high", "low", "close", "volume"):
            a = np.full((ND, NM), np.nan)
            a[di, m] = df[k].to_numpy(float)
            out[k] = a
        return out

    shape = (NS, ND, NB)
    C5 = np.memmap(DATA / "C5.f32", dtype=np.float32, mode="w+", shape=shape)
    V5 = np.memmap(DATA / "V5.f32", dtype=np.float32, mode="w+", shape=shape)
    C5[:] = np.nan
    V5[:] = np.nan
    O0 = np.full((NS, ND), np.nan, np.float32)
    CL = np.full((NS, ND), np.nan, np.float32)
    etf = {k: np.full((len(ETF1M), ND, NM), np.nan, np.float32) for k in ("open", "high", "low", "close", "volume")}

    def ffill(a):
        idx = np.where(np.isfinite(a), np.arange(a.shape[1])[None, :], 0)
        np.maximum.accumulate(idx, axis=1, out=idx)
        out = a[np.arange(a.shape[0])[:, None], idx]
        return out

    # index 1-minute log returns (forward-filled closes inside the session)
    idx_ret, idx_c = {}, {}
    for s in ("SPY", "QQQ"):
        mm = minutes(s)
        c = ffill(mm["close"])
        idx_c[s] = c
        r = np.full_like(c, np.nan)
        r[:, 1:] = np.log(c[:, 1:] / c[:, :-1])
        idx_ret[s] = r
    # lead-lag sums per symbol x index x lag x split: n, sx, sy, sxx, syy, sxy
    LL = np.zeros((NS, 2, LAGS, 2, 6))
    # tradable test: configs (index, k, h)
    cfgs = [(ix, k, h) for ix in ("SPY", "QQQ") for k in (1, 5) for h in (1, 5, 15)]
    thr = {1: 0.0010, 5: 0.0025}
    TD = np.zeros((len(cfgs), ND, 4))      # per session: n, sum net bps, sum gross bps, sum index continuation bps
    TS = np.zeros((len(cfgs), NS, 3))      # per symbol: n, sum net, sum gross
    msig = np.arange(19, 330)              # signal minute index: minute closes 09:50 .. 15:00
    close_hhmm = np.array([((570 + m + 1) // 60) * 100 + (570 + m + 1) % 60 for m in range(NM)])
    mult = tod_cost_mult(close_hhmm)
    sig = {}
    for c_i, (ix, k, h) in enumerate(cfgs):
        c = idx_c[ix]
        mv = np.log(c[:, msig] / c[:, msig - k])
        d = np.where(mv >= thr[k], 1.0, np.where(mv <= -thr[k], -1.0, 0.0))
        d[~np.isfinite(mv)] = 0
        cont = np.log(c[:, np.minimum(msig + h, NM - 1)] / c[:, msig]) * 1e4
        sig[c_i] = d
        TD[c_i, :, 3] = np.nansum(d * cont, axis=1)
    t0 = time.time()
    for j, s in enumerate(syms + (["UUP"] if "UUP" not in syms else [])):
        mm = minutes(s)
        if mm is None:
            continue
        if s in ETF1M:
            e = ETF1M.index(s)
            for k in etf:
                etf[k][e] = mm[k]
        if j >= NS:
            continue
        c = ffill(mm["close"])
        has = np.isfinite(mm["close"])
        anyday = has.any(1)
        # 5-minute arrays
        C5[j] = c[:, 4::5].astype(np.float32)
        v = np.nan_to_num(mm["volume"]).reshape(ND, NB, 5).sum(2)
        V5[j] = np.where(anyday[:, None], v, np.nan).astype(np.float32)
        o = mm["open"]
        first = np.argmax(np.isfinite(o), axis=1)
        O0[j] = np.where(anyday, o[np.arange(ND), first], np.nan)
        CL[j] = c[:, -1]
        # lead-lag (1-minute log returns; sessions independent)
        r = np.full_like(c, np.nan)
        r[:, 1:] = np.log(c[:, 1:] / c[:, :-1])
        for a, ix in enumerate(("SPY", "QQQ")):
            x0 = idx_ret[ix]
            for L in range(LAGS):
                y = r[:, 1 + L:]
                x = x0[:, 1:NM - L]
                ok = np.isfinite(x) & np.isfinite(y)
                for sp in (0, 1):
                    okk = ok & (split == bool(sp))[:, None]
                    xx, yy = x[okk], y[okk]
                    LL[j, a, L, sp] = (okk.sum(), xx.sum(), yy.sum(), (xx * xx).sum(), (yy * yy).sum(), (xx * yy).sum())
        # tradable lead-lag test (non-ETF, adv20 >= 95M point in time)
        if s not in W2ETFS:
            elig = (adv[:, j] >= 95e6) & anyday
            if elig.any():
                cost = (0.01 / c[:, msig] + 1e-4) * 1e4 * (mult[msig][None, :] + 1.0)
                for c_i, (ix, k, h) in enumerate(cfgs):
                    d = sig[c_i] * elig[:, None]
                    fwd = np.log(c[:, np.minimum(msig + h, NM - 1)] / c[:, msig]) * 1e4
                    g = d * fwd
                    use = (d != 0) & np.isfinite(g) & np.isfinite(cost)
                    g = np.where(use, g, 0.0)
                    net = np.where(use, g - cost, 0.0)
                    TD[c_i, :, 0] += use.sum(1)
                    TD[c_i, :, 1] += net.sum(1)
                    TD[c_i, :, 2] += g.sum(1)
                    TS[c_i, j] += (use.sum(), net.sum(), g.sum())
        if j % 100 == 0:
            print(j, s, round(time.time() - t0), flush=True)
    C5.flush()
    V5.flush()
    del C5, V5
    np.save(DATA / "O0.npy", O0)
    np.save(DATA / "CL.npy", CL)
    np.savez_compressed(DATA / "etf1m.npz", syms=np.array(ETF1M), **etf)
    np.savez_compressed(DATA / "leadlag.npz", LL=LL)
    np.savez_compressed(DATA / "lltrade.npz", TD=TD, TS=TS, cfgs=np.array([f"{a}_k{b}_h{c}" for a, b, c in cfgs]))
    (DATA / "meta.json").write_text(json.dumps({"shape": list(shape), "syms": syms, "dates": [str(x) for x in dates],
                                                "etf1m": ETF1M}))
    print("done", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
