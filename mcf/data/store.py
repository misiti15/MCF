"""Local parquet cache: data/cache/<timeframe>/<SYMBOL>.parquet."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .bars import normalize


class BarStore:
    def __init__(self, root: str | Path, timeframe: str = "1Min"):
        self.dir = Path(root) / timeframe
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, symbol: str) -> Path:
        return self.dir / f"{symbol.upper().replace('/', '_')}.parquet"

    def symbols(self) -> list[str]:
        return sorted(p.stem for p in self.dir.glob("*.parquet"))

    def load(self, symbol: str, start=None, end=None) -> pd.DataFrame:
        p = self.path(symbol)
        if not p.exists():
            return pd.DataFrame()
        df = pd.read_parquet(p)
        if start is not None:
            df = df[df.index >= pd.Timestamp(start, tz=df.index.tz)]
        if end is not None:
            df = df[df.index < pd.Timestamp(end, tz=df.index.tz)]
        return df

    def save(self, symbol: str, df: pd.DataFrame) -> None:
        df = normalize(df)
        existing = self.load(symbol)
        if not existing.empty:
            df = pd.concat([existing, df])
            df = df[~df.index.duplicated(keep="last")].sort_index()
        df.to_parquet(self.path(symbol))

    def load_many(self, symbols, start=None, end=None) -> dict[str, pd.DataFrame]:
        out = {}
        for s in symbols:
            df = self.load(s, start, end)
            if not df.empty:
                out[s] = df
        return out

    @classmethod
    def from_csv_dir(cls, csv_dir: str | Path, root: str | Path, timeframe="1Min") -> "BarStore":
        """Import CSVs (one per symbol, timestamp column first) e.g. exported MarcoFlow data."""
        store = cls(root, timeframe)
        for p in Path(csv_dir).glob("*.csv"):
            df = pd.read_csv(p, index_col=0, parse_dates=True)
            store.save(p.stem, df)
        return store
