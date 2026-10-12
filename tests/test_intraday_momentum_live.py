"""Regression 2026-10-12: intraday_momentum never produced a live signal (Primary Oct 6-9, Testing Oct 12) although the
first-30-minute move cleared 0.25% on most days. generate() needed a bar AFTER the 15:29 decision bar to exist, so
the signal only appeared once the 15:30 bar had closed (15:31 poll) -- and the live runner acts only on signals whose
bar is the latest completed bar, so it was dropped every day. Backtests (full-day bars) were unaffected."""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from mcf.config import load_config
from mcf.data.bars import TZ
from mcf.execution import runner as R
from mcf.strategies.base import DayContext
from mcf.strategies.setups import IntradayMomentum

DAY = "2026-10-06"


def _bars(up=True):
    idx = pd.date_range(f"{DAY} 09:30", f"{DAY} 15:59", freq="1min", tz=TZ)
    p = np.full(len(idx), 100.0)
    p[20:] = 100.6 if up else 99.4            # +-0.6% vs prev close 100 by the 09:59 bar
    o = np.concatenate([[p[0]], p[:-1]])
    return pd.DataFrame({"open": o, "high": np.maximum(o, p) + 0.01, "low": np.minimum(o, p) - 0.01,
                         "close": p, "volume": 1e5}, index=idx)


def _strat():
    cfg = load_config()
    return IntradayMomentum(**{k: v for k, v in cfg["strategies"]["intraday_momentum"].items() if k != "enabled"})


def _ctx(bars):
    return DayContext("SPY", pd.Timestamp(DAY).date(), bars, prev_close=100.0, prev_high=101.0, prev_low=99.0,
                      atr=0.8, avg_dollar_volume=3e10)


def test_backtest_signal_unchanged():
    s = _strat()
    bars = _bars()
    sig = s.signals(_ctx(bars))
    assert len(sig) == 1 and sig[0].side == 1
    assert bars.index[sig[0].bar_index].strftime("%H:%M") == "15:29"   # enters at the 15:30 open, as before


def test_no_signal_before_entry_time():
    s = _strat()
    bars = _bars()
    for cut in ("10:30", "14:00", "15:28"):        # completed bars up to (not incl.) the cut minute
        assert s.signals(_ctx(bars[bars.index < pd.Timestamp(f"{DAY} {cut}", tz=TZ)])) == []


class _Broker:
    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return {}


def test_live_runner_enters_at_1530(tmp_path, monkeypatch):
    cfg = load_config()
    cfg["strategies"]["intraday_momentum"]["enabled"] = True
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    full = _bars(up=False)
    pri = {"SPY": SimpleNamespace(prev_close=100.0, prev_high=101.0, prev_low=99.0, atr=0.8, adv=3e10,
                                  avg_cum=None, avg_move=None)}
    r = R.PaperRunner(cfg, [_strat()], pri, dry_run=True, broker=_Broker())
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    entered = []
    monkeypatch.setattr(r, "_log", lambda sig, status, why, ref, now, *a, **k: entered.append((now, status, sig)))
    for m in pd.date_range(f"{DAY} 15:00:05", f"{DAY} 15:54:05", freq="1min", tz=TZ):   # one poll a minute
        monkeypatch.setattr(r, "fetch", lambda now: {"SPY": full[full.index < now.floor("1min")]})
        r.step(m)
    assert len(entered) == 1
    now, status, sig = entered[0]
    assert status == "dry_run" and sig.side == -1 and now.strftime("%H:%M") == "15:30"
