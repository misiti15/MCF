"""pod-cal-tom-vwap-pullback-stock-long - Turn-of-month window: intraday VWAP pullback long in uptrending liquid
stocks (LONG).

Source: turn-of-the-month effect (Lakonishok and Smidt 1988; Ogden 1990, 'Turn-of-month evaluations of liquid
profits and stock returns', Journal of Finance 45(4)), commonly cited on systematic-trading podcasts. Not verified
against a specific episode (web blocked this run).
URL: https://doi.org/10.1111/j.1540-6261.1990.tb02427.x
VARIANT of backlog sw-w3-calendar-near ('Daily: turn of month / day of week / index overnight on SPY, QQQ, IWM, EW';
failed: about 20 events per split, t <= 1.2), a daily close-to-close TOM trade on index ETFs only. Stated changes:
(a) intraday entries on a pullback trigger; (b) a stock universe (adv20 >= $50M, ETFs included) which multiplies the
event count; (c) a breadth gate.

Rules (plain English, LONG):
  Date gate: the last trading day of the month and the first 3 trading days of the next (NYSE calendar hard-coded
  below; a published schedule, no lookahead).
  1. Bar close 10:00-13:00.
  2. vwapDistPct between -0.30 and +0.10 (a pullback to VWAP).
  3. sma20_slope_pct > 0.
  4. rsi5 <= 35.
  5. breadth >= 0.50.
  Universe: adv20 >= $50M. Entry: bar close. GEOM t1s1 (R = 0.25 x atr_d), flat 15:55.
  Costs per config/default.yaml (applied by the scorer). No tweak made.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t1s1"
WINDOW = (1000, 1300)
MIN_ADV = 50e6
CONTEXT = ["breadth"]
LAYERS = ["TOM: last trading day of the month + first 3 of the next", "vwapDistPct in [-0.30, 0.10]",
          "sma20_slope_pct > 0", "rsi5 <= 35", "breadth >= 0.50", "adv20 >= $50M", "10:00-13:00", "t1s1"]

HOLIDAYS = ["2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19", "2024-07-04",
            "2024-09-02", "2024-11-28", "2024-12-25",
            "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19",
            "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01"]


def _tom_dates():
    hol = set(pd.to_datetime(HOLIDAYS).date)
    days = pd.Series([d for d in pd.bdate_range("2024-01-01", "2027-01-31").date if d not in hol])
    ym = days.map(lambda d: (d.year, d.month))
    rank_fwd = days.groupby(ym).cumcount()                                   # 0 = first trading day of the month
    rank_back = days.groupby(ym).cumcount(ascending=False)                  # 0 = last trading day of the month
    return set(days[(rank_fwd <= 2) | (rank_back == 0)])


GATE = _tom_dates()


def mask(df) -> np.ndarray:
    if not len(df) or "breadth" not in df:
        return np.zeros(len(df), dtype=bool)
    f = lambda k: df[k].to_numpy(float)
    tod = f("tod")
    dt = pd.to_datetime(df["date"]).dt.date.to_numpy()
    with np.errstate(invalid="ignore"):
        vd = f("vwapDistPct")
        m = np.isin(dt, list(GATE))
        m &= (vd >= -0.30) & (vd <= 0.10)
        m &= f("sma20_slope_pct") > 0
        m &= f("rsi5") <= 35
        m &= f("breadth") >= 0.50
        m &= f("adv20") >= MIN_ADV
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
