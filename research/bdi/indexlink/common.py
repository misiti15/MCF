"""Shared loaders for the IX index-linkage study (NOTES.md). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE / "data"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402,F401

SECTOR = "XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS".split()
SPDR = "XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC".split()
W2ETFS = set(("ARKK ASHR BITO BOIL CONL DIA EEM EFA ETHA EWJ EWT EWY EWZ FBTC FXI GBTC GDX GDXJ GLD IBB IBIT IEMG IGV ITB "
              "IWF IWM IYR JETS KBE KRE KWEB LABD MDY MSTU MTUM NUGT NVDL OIH PSQ QID QQQ SCO SDS SLV SMH SOXL SOXS SOXX "
              "SPXL SPXS SPY SQQQ TLT TMF TNA TQQQ TSLL TZA UCO UNG UPRO USO UVXY VEA VNQ VUG VWO VXX XBI XHB XLB XLC XLE "
              "XLF XLI XLK XLP XLRE XLU XLV XLY XME XOP XRT").split())


def is_etf(sym: str, meta_etf: set | None = None) -> bool:
    return sym in W2ETFS or (meta_etf is not None and sym in meta_etf)


def meta():
    m = json.loads((DATA / "meta.json").read_text())
    m["dates"] = [pd.Timestamp(x).date() for x in m["dates"]]
    return m


def bars():
    m = meta()
    shape = tuple(m["shape"])
    C5 = np.memmap(DATA / "C5.f32", dtype=np.float32, mode="r", shape=shape)
    V5 = np.memmap(DATA / "V5.f32", dtype=np.float32, mode="r", shape=shape)
    return m, C5, V5, np.load(DATA / "O0.npy"), np.load(DATA / "CL.npy")


def etf1m():
    z = np.load(DATA / "etf1m.npz")
    return list(z["syms"]), {k: z[k] for k in ("open", "high", "low", "close", "volume")}


def ffill_rows(a):
    idx = np.where(np.isfinite(a), np.arange(a.shape[-1]), 0)
    np.maximum.accumulate(idx, axis=-1, out=idx)
    return np.take_along_axis(a, idx, axis=-1)


def hhmm(minutes_after_930_close):
    t = 570 + np.asarray(minutes_after_930_close)
    return (t // 60) * 100 + t % 60


def pit_betas(syms, dates, window=60, minn=30):
    """Point-in-time beta / corr of daily open-to-close returns to SPY and QQQ, previous `window` open sessions only."""
    d = lib.daily()
    d = d[d["open"] > 0]
    R = (pd.Series(((d["close"] / d["open"] - 1) * 100).to_numpy(), index=pd.MultiIndex.from_arrays([d["date"], d["symbol"]]))
         .unstack().reindex(index=dates, columns=syms).to_numpy(np.float64))
    adv = d.pivot_table(index="date", columns="symbol", values="adv20").reindex(index=dates, columns=syms).to_numpy()
    out = {k: np.full(R.shape, np.nan, np.float32) for k in ("beta_spy", "corr_spy", "beta_qqq", "corr_qqq")}
    si = {s: i for i, s in enumerate(syms)}
    for t in range(minn, len(dates)):
        Y = R[max(0, t - window):t]
        for ix in ("spy", "qqq"):
            x = Y[:, si[ix.upper()]]
            v = np.isfinite(Y) & np.isfinite(x)[:, None]
            n = v.sum(0)
            xx, yy = np.where(v, x[:, None], 0), np.where(v, Y, 0)
            sx, sy = xx.sum(0), yy.sum(0)
            nn = np.maximum(n, 1)
            cxy = (xx * yy).sum(0) - sx * sy / nn
            cxx = (xx ** 2).sum(0) - sx ** 2 / nn
            cyy = (yy ** 2).sum(0) - sy ** 2 / nn
            with np.errstate(invalid="ignore", divide="ignore"):
                b, c = cxy / cxx, cxy / np.sqrt(cxx * cyy)
            b[n < minn], c[n < minn] = np.nan, np.nan
            out[f"beta_{ix}"][t], out[f"corr_{ix}"][t] = b, c
    return out, R, adv
