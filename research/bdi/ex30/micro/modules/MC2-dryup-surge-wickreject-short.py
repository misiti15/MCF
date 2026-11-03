"""MC2-dryup-surge-wickreject-short - ex30/micro microstructure setup (BDI 2026-11-03, research/bdi/ex30/micro).
Volume dry-up then surge into rejection: three quiet bars (volumeRatio < 0.7), then a >= 2x volume bar whose upper
wick is at least half its range; short. Exploratory account candidate; see NOTES.md there.
Educational only - not financial advice."""
import numpy as np
import micro_lib as L

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1015, 1500)
LAYERS = [
    "each of the 3 previous bars volumeRatio < 0.7 (dry-up)",
    "this bar volumeRatio >= 2.0 (surge)",
    "upper_wick >= 0.5 (rejected)",
    "bar close 10:15-15:00 ET",
]


def mask(df, surge=2.0) -> np.ndarray:
    seg = L.segments(df)
    vr, tod = L.col(df, "volumeRatio"), L.col(df, "tod")
    with np.errstate(invalid="ignore"):
        dry = np.ones(len(df), bool)
        for j in (1, 2, 3):
            dry &= L.lag(vr, seg, j) < 0.7
        m = dry & (vr >= surge) & (L.col(df, "upper_wick") >= 0.5)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
