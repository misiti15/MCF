"""Synthetic intraday data for tests and demos. NOT for evaluating strategies."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .bars import TZ


def make_symbol(
    symbol: str,
    days: int = 60,
    start: str = "2025-01-02",
    price: float = 50.0,
    daily_vol: float = 0.02,
    seed: int | None = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed if seed is not None else abs(hash(symbol)) % 2**32)
    sessions = pd.bdate_range(start, periods=days)
    minutes = 390
    # U-shaped intraday volume profile
    x = np.linspace(-1, 1, minutes)
    vol_profile = 0.6 + 1.8 * x**2
    frames = []
    p = price
    for d in sessions:
        gap = rng.normal(0, daily_vol * 0.5)
        if rng.random() < 0.05:
            gap += rng.choice([-1, 1]) * rng.uniform(0.03, 0.08)
        p *= 1 + gap
        sigma = daily_vol / np.sqrt(minutes) * (1 + 3 * abs(gap) / daily_vol / 4)
        rets = rng.normal(0, sigma, minutes) * np.sqrt(vol_profile / vol_profile.mean())
        closes = p * np.exp(np.cumsum(rets))
        opens = np.concatenate([[p], closes[:-1]])
        spread = np.abs(rng.normal(0, sigma, minutes)) * closes
        highs = np.maximum(opens, closes) + spread
        lows = np.minimum(opens, closes) - spread
        base_vol = rng.lognormal(10, 0.3) * (1 + 5 * abs(gap) / daily_vol / 2)
        vols = (base_vol * vol_profile * rng.lognormal(0, 0.4, minutes)).round()
        idx = pd.date_range(f"{d.date()} 09:30", periods=minutes, freq="1min", tz=TZ)
        frames.append(
            pd.DataFrame(
                {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols},
                index=idx,
            )
        )
        p = closes[-1]
    return pd.concat(frames)


def make_universe(symbols: list[str], days: int = 60, **kw) -> dict[str, pd.DataFrame]:
    return {s: make_symbol(s, days=days, seed=i, **kw) for i, s in enumerate(symbols)}
