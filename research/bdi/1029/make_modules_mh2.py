"""Writes the 8 pre-registered MH2 earnings-sympathy modules (side x entry {at950, confirm} x GEOM {hold, holdtr}).
Peer table: sympathy.parquet (sympathy.py). Educational only - not financial advice."""
from pathlib import Path
T = '''"""{name} - Move Hunt 2026-10-29 precursor 2 (earnings sympathy). {side} a non-reporting peer (top-5 60-day return
correlation >= 0.5) of a company whose earnings reaction day gaps >= 4% in the {side} direction (sympathy.parquet).
Entry {entry}. GEOM {geom} (stop 1R = 0.25 daily ATR, flat 15:55). ADV20 >= $95M. Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd
SIDE = "{side}"
GEOM = "{geom}"
WINDOW = (950, {wend})
MIN_ADV = 95e6
_T = pd.read_parquet(Path(__file__).resolve().parents[1] / "sympathy.parquet")
_K = set(zip(_T.loc[_T.dir == {sg}, "date"].astype(str), _T.loc[_T.dir == {sg}, "symbol"]))
LAYERS = ["earnings-sympathy peer, dir {sg}", "{entry}"]


def mask(df) -> np.ndarray:
    key = df["date"].astype(str).to_numpy(object) + "|" + df["symbol"].astype(str).to_numpy(object)
    ks = {{a + "|" + b for a, b in _K}}
    m = np.fromiter((k in ks for k in key), bool, len(key))
    with np.errstate(invalid="ignore"):
        {cond}
    return np.asarray(m, dtype=bool)
'''
for side, sg in (("long", 1), ("short", -1)):
    for entry, wend, cond in (("at950", 950, "m &= df['tod'].to_numpy() == 950"),
                              ("confirm", 1100, f"m &= ({sg} * df['fromOpen'].to_numpy(float) > 0) & ({sg} * df['vwapDistPct'].to_numpy(float) > 0)")):
        for geom in ("hold", "holdtr"):
            name = f"MH2-sympathy-{entry}-{geom}-{side}"
            Path(f"modules/{name}.py").write_text(T.format(name=name, side=side, sg=sg, entry=entry, wend=wend, cond=cond, geom=geom))
print("8 MH2 modules")
