"""W2 market-neutral study: shared constants and loaders (see NOTES.md section 1). Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE / "data"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

SECTOR = "XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS".split()
ETFS = set(("ARKK ASHR BITO BOIL CONL DIA EEM EFA ETHA EWJ EWT EWY EWZ FBTC FXI GBTC GDX GDXJ GLD IBB IBIT IEMG IGV ITB "
            "IWF IWM IYR JETS KBE KRE KWEB LABD MDY MSTU MTUM NUGT NVDL OIH PSQ QID QQQ SCO SDS SLV SMH SOXL SOXS SOXX "
            "SPXL SPXS SPY SQQQ TLT TMF TNA TQQQ TSLL TZA UCO UNG UPRO USO UVXY VEA VNQ VUG VWO VXX XBI XHB XLB XLC XLE "
            "XLF XLI XLK XLP XLRE XLU XLV XLY XME XOP XRT").split())
TODS = np.array([(9 * 60 + 35 + 5 * i) // 60 * 100 + (9 * 60 + 35 + 5 * i) % 60 for i in range(77)])  # 935..1555
LOCKED = lib.LOCKED


def tod_index(tod):
    t = np.asarray(tod, int)
    return ((t // 100) * 60 + t % 100 - (9 * 60 + 35)) // 5


def open_dates() -> list:
    return sorted(set(lib.daily()["date"]))


def symbols() -> list[str]:
    return (ROOT / "research" / "lab_symbols.txt").read_text().split()


def bars():
    """Dense 5-min arrays (built by build_bars.py): dict C, H, L [sym, day, bar] float32 (memmap), syms, dates."""
    meta = pd.read_json(DATA / "bars_meta.json", typ="series")
    shape = tuple(meta["shape"])
    out = {k: np.memmap(DATA / f"bars_{k}.f32", dtype=np.float32, mode="r", shape=shape) for k in ("C", "H", "L")}
    out["syms"] = list(meta["syms"])
    out["dates"] = [pd.Timestamp(x).date() for x in meta["dates"]]
    return out
