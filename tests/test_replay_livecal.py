"""Calibrated session replay (mcf/replay/livecal.py, research/replay_cal): live poll schedule with outages and late
bars, fitted spreads and in-bar fills on a synthetic session. Educational only - not financial advice."""

import json

import numpy as np
import pandas as pd

from mcf.replay import harness, livecal
from tests.test_replay import DAY, NY, _cfg, _session


def _bt(res):
    s = res["signals"]
    return {json.loads(i).get("bar_time") for i in s["info"]} if len(s) else set()


def _schedule(skip_from="09:58", skip_to="10:04", late_sym="AAA", late_at="11:01"):
    """A poll every minute at :20 with 4 s fetch, an outage skip_from..skip_to, and at late_at the symbol's newest bar
    not yet arrived (its last bar is two minutes old)."""
    out = []
    for t in pd.date_range(pd.Timestamp(f"{DAY} 09:30:20", tz=NY), pd.Timestamp(f"{DAY} 15:59:20", tz=NY), freq="1min"):
        if pd.Timestamp(f"{DAY} {skip_from}", tz=NY) <= t < pd.Timestamp(f"{DAY} {skip_to}", tz=NY):
            continue
        late = {}
        if t.strftime("%H:%M") == late_at:
            late[late_sym] = (t - pd.Timedelta(minutes=2)).strftime("%H%M")
        out.append((t, 4.0, late))
    return tuple(out)


def test_live_polls_outage_and_late_bars(tmp_path):
    bars, priors = _session()
    cfg = _cfg(tmp_path)
    sh = {s: (True, True) for s in bars}
    base = harness.run_session(cfg, DAY, bars, priors, spreads={}, shortable=sh, check=0, log=lambda m: None)
    cal = livecal.Calibrator({"polls": False}, "none", DAY)
    cal.polls = _schedule()
    res = harness.run_session(cfg, DAY, bars, priors, spreads={}, shortable=sh, check=0, log=lambda m: None, hook=cal)
    b0, b1 = _bt(base), _bt(res)
    assert "0959" in b0 and "0959" not in b1                    # the outage swallowed the 10:00 decision bar
    assert {"1059", "1259"} <= b1                                # other decisions unchanged
    assert cal.notes["hidden_bars"] >= 1                         # the late bar was hidden at its poll
    assert res["stats"]["polls"] <= len(cal.polls) + 2
    ts = pd.to_datetime(res["signals"]["ts"])
    assert (ts.dt.second >= 20).all()                            # decisions after the poll's fetch, not at :03


def test_fill_weight_and_spread_model():
    bars, _ = _session()
    df = pd.DataFrame({"fill": [10.06, 20.1], "open": [10.0, 20.0], "close": [10.1, 20.2], "side": [1, 1],
                       "half": [0.0, 0.0]})
    assert abs(livecal.fit_fill_weight(df) - 0.55) < 0.06
    x = livecal.spread_features(5e8, 50.0, np.array([50, 50.1, 49.9, 50, 1e4]), 10)
    assert len(x) == 6 and x[-1] == 1.0
    rows = pd.DataFrame({"lb": np.log(np.r_[np.full(60, 5.0), np.full(60, 20.0)]),
                         "x": [livecal.spread_features(a, 50.0, np.array([50, 50.1, 49.9, 50, 1e4]), 60)
                               for a in np.r_[np.full(60, 1e9), np.full(60, 1e7)]], "lmed": None})
    m = livecal.fit_spread_model(rows)
    assert "unknown" in m and m["unknown"][1] < 0                # wider spreads for thinner names
