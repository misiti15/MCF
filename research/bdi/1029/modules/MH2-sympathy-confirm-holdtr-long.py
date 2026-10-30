"""MH2-sympathy-confirm-holdtr-long - Move Hunt 2026-10-29 precursor 2 (earnings sympathy). long a non-reporting peer (top-5 60-day return
correlation >= 0.5) of a company whose earnings reaction day gaps >= 4% in the long direction (sympathy.parquet).
Entry confirm. GEOM holdtr (stop 1R = 0.25 daily ATR, flat 15:55). ADV20 >= $95M. Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd
SIDE = "long"
GEOM = "holdtr"
WINDOW = (950, 1100)
MIN_ADV = 95e6
_T = pd.read_parquet(Path(__file__).resolve().parents[1] / "sympathy.parquet")
_K = set(zip(_T.loc[_T.dir == 1, "date"].astype(str), _T.loc[_T.dir == 1, "symbol"]))
LAYERS = ["earnings-sympathy peer, dir 1", "confirm"]


def mask(df) -> np.ndarray:
    key = df["date"].astype(str).to_numpy(object) + "|" + df["symbol"].astype(str).to_numpy(object)
    ks = {a + "|" + b for a, b in _K}
    m = np.fromiter((k in ks for k in key), bool, len(key))
    with np.errstate(invalid="ignore"):
        m &= (1 * df['fromOpen'].to_numpy(float) > 0) & (1 * df['vwapDistPct'].to_numpy(float) > 0)
    return np.asarray(m, dtype=bool)
