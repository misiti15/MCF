"""mcf.research.timeframes: multi-timeframe frames and harness (synthetic, fast). Educational only - not financial advice."""
import numpy as np
import pandas as pd
import pytest

from mcf.data.bars import resample
from mcf.research import timeframes as tf
from mcf.research.setup_lab import build


def _bars(n_days=18, seed=0, start="2025-03-03"):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, periods=n_days)
    idx = pd.DatetimeIndex(np.concatenate([pd.date_range(f"{d.date()} 09:30", periods=390, freq="1min").values for d in days]))
    idx = idx.tz_localize("America/New_York")
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.0015, len(idx))))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.001, len(c)))
    l = np.minimum(o, c) * (1 - rng.uniform(0, 0.001, len(c)))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": rng.integers(100, 5000, len(c)).astype(float)},
                        index=idx)


def test_five_minute_frame_is_setup_lab_build():
    b = _bars()
    x = tf.build_tf_frame(b, 5, "AAA")
    ref = build({"AAA": resample(b, "5min")}, log=lambda *_: None)
    assert len(x) == len(ref) > 0
    pd.testing.assert_frame_equal(x[ref.columns], ref)


@pytest.mark.parametrize("m", [1, 3, 10, 15])
def test_tod_is_true_bar_close(m):
    x = tf.build_tf_frame(_bars(), m, "AAA")
    end = x.index + pd.Timedelta(minutes=m)
    assert (x["tod"].to_numpy() == end.hour * 100 + end.minute).all()
    assert x["tod"].between(950, 1500).all()
    assert (x.index.minute % m == 0).all()                         # bars aligned to the 09:30 grid


def _write_root(tmp_path, m=3):
    parts = []
    for i, s in enumerate(("AAA", "BBB")):
        x = tf.build_tf_frame(_bars(seed=i), m, s).reset_index(drop=True)
        x["adv20"] = np.float32(1e8)
        parts.append(x)
    x = pd.concat(parts, ignore_index=True)
    for mo, g in x.groupby(pd.to_datetime(x["date"]).dt.strftime("%Y-%m")):
        p = tmp_path / f"{m}min" / f"month={mo}"
        p.mkdir(parents=True)
        g.to_parquet(p / "part-000.parquet", index=False)
    (tmp_path / "symbols.txt").write_text("AAA\nBBB\n")
    (tmp_path / "symbols_core.txt").write_text("AAA\n")
    return x


class _Mod:
    SIDE, GEOM = "long", "t1s1"

    @staticmethod
    def mask(df):
        return df["rsi"].to_numpy(float) > 0


def test_run_module_tf_first_bar_window_and_baseline(tmp_path):
    x = _write_root(tmp_path, 3)
    t = tf.run_module_tf(_Mod, 3, window=(1000, 1400), root=tmp_path)
    assert len(t) and t["tod"].between(1000, 1400).all()
    assert not t.duplicated(["symbol", "date"]).any()               # one trade per symbol-day
    first = x[(x.tod >= 1000) & (x.rsi > 0) & x.r_long_t1s1.notna()].groupby(["symbol", "date"])["tod"].min()
    got = t.set_index(["symbol", "date"])["tod"]
    assert (got.sort_index().to_numpy() == first.loc[got.sort_index().index].to_numpy()).all()
    assert np.isfinite(t["ctrl"]).all() and np.allclose(t["excess"], t["r"] - t["ctrl"])
    assert set(t["split"]) == {"train"} and (t["minutes"] == 3).all()
    core = tf.run_module_tf(_Mod, 3, window=(1000, 1400), root=tmp_path, symbols="core")
    assert set(core["symbol"]) == {"AAA"}
    assert tf.run_module_tf(_Mod, 3, split="valid", root=tmp_path).empty


def test_locked_block_refused(tmp_path):
    with pytest.raises(PermissionError):
        tf.load_tf(1, "2024-12", root=tmp_path)
    assert "2025-01" not in tf.split_months("open", ["2024-10", "2025-01", "2025-03"])


def test_summarize_reports_gates(tmp_path):
    _write_root(tmp_path, 15)
    t = tf.run_module_tf(_Mod, 15, root=tmp_path)
    dates = sorted(set(t["date"]))
    reg = pd.DataFrame({"regime": (["up", "flat", "down"] * len(dates))[: len(dates)]}, index=dates)
    s = tf.summarize(t, n_tries=20, regime_table=reg)
    assert s["t_required"] == pytest.approx(max(1.5, np.sqrt(2 * np.log(20))), abs=1e-3)
    assert {"overall", "by_split", "random_same_minute", "regime", "regime_pass", "walk_forward", "verdict"} <= set(s)
    assert s["overall"]["n"] == len(t)
