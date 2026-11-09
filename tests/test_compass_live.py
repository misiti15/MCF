"""Market Compass (live) (owner "Compass live: yes", 2026-11-09): compute on a fixed synthetic session, point-in-time,
idempotent catch-up, the workflow and the dashboard card. Display only. Educational only — not financial advice."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from mcf.report import compass_live as cl

ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-11-06"
NAMES = [f"N{i}" for i in range(10)]


def _bars(path_pct, vol=1000.0):
    """1-minute bars 09:30..15:59 whose close walks linearly through the % path given at (minute, pct) knots."""
    idx = pd.date_range(f"{DAY} 09:30", f"{DAY} 15:59", freq="1min", tz=cl.NY)
    m = idx.hour * 60 + idx.minute
    kx, ky = zip(*path_pct)
    c = 100 * (1 + np.interp(m, kx, ky) / 100)
    o = np.r_[100.0, c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.01, "low": np.minimum(o, c) - 0.01, "close": c,
                         "volume": vol}, index=idx)


def sample():
    up = [(570, 0), (600, 0.4), (630, 0.6), (720, 0.8), (960, 1.0)]       # SPY: steady up day
    b = {"SPY": _bars(up), "QQQ": _bars(up), "IWM": _bars([(570, 0), (600, -0.1), (640, 0.2), (960, 0.5)])}
    for i, n in enumerate(NAMES):                                            # 7 of 10 names up, 3 down
        b[n] = _bars([(570, 0), (960, 0.5 if i < 7 else -0.5)])
    return b


def test_compute_fixed_sample():
    rows = cl.compute(sample(), DAY, pd.Timestamp(f"{DAY} 16:05", tz=cl.NY), NAMES)
    by = {r["T"]: r for r in rows}
    assert [r["T"] for r in rows][:3] == ["09:45", "10:00", "10:15"] and rows[-1]["T"] == "15:45" and len(rows) == 25
    r = by["09:45"]                       # 1 mark: never confirmed, low confidence, breadth 0.5 by convention
    assert r["w60_low_conf"] == 1 and r["breadth_open"] == 0.5 and r["breadth_n"] == 0
    assert r["w60"] in ("leaning up", "mixed") and r["c30"] == "" and r["checkpoint"] == ""
    assert by["10:00"]["checkpoint"] == "" and by["10:00"]["c30"] == "leaning up"    # no persist3 at 10:00
    r = by["10:30"]
    assert r["checkpoint"] == "UP" and r["checkpoint_at"] == "10:30"
    assert r["c30"] == "UP-confirmed" and r["w60"] == "UP-confirmed"
    assert r["agreement"] == "all up" and r["v_agree"] == 1 and r["breadth_open"] == 0.7
    assert r["votes"] == 5 and r["gate1_state"] == "UP"
    assert by["10:00"]["agreement"] == "mixed"                                           # IWM still below its open
    assert abs(by["10:30"]["spy_fo"] - 0.006) < 2e-4


def test_checkpoint_needs_030pct_and_holds_between_checkpoints():
    b = sample()
    b["SPY"] = _bars([(570, 0), (630, 0.2), (660, -0.35), (960, -0.4)])
    by = {r["T"]: r for r in cl.compute(b, DAY, pd.Timestamp(f"{DAY} 16:05", tz=cl.NY), NAMES)}
    assert by["10:30"]["checkpoint"] == "UNCONFIRMED"
    assert by["10:45"]["checkpoint"] == "UNCONFIRMED" and by["10:45"]["checkpoint_at"] == "10:30"
    assert by["11:00"]["checkpoint"] == "DOWN"


def test_point_in_time_only():
    """A mark computed at 11:20 with the bars so far equals the same mark computed after the close (no look-ahead)."""
    full = sample()
    cut = pd.Timestamp(f"{DAY} 11:20", tz=cl.NY)
    part = {k: v[v.index < cut] for k, v in full.items()}
    early = cl.compute(part, DAY, cut, NAMES)
    late = {r["T"]: r for r in cl.compute(full, DAY, pd.Timestamp(f"{DAY} 16:05", tz=cl.NY), NAMES)}
    assert [r["T"] for r in early] == ["09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15"]
    for r in early:
        a = {k: v for k, v in r.items() if k not in ("computed_at", "backfilled")}
        b = {k: v for k, v in late[r["T"]].items() if k not in ("computed_at", "backfilled")}
        assert a == b, r["T"]
    # a mark is only computed once its last bar has closed (mark + 1 min)
    assert [r["T"] for r in cl.compute(full, DAY, pd.Timestamp(f"{DAY} 09:45", tz=cl.NY), NAMES)] == []
    assert [r["T"] for r in cl.compute(full, DAY, pd.Timestamp(f"{DAY} 09:46", tz=cl.NY), NAMES)] == ["09:45"]


def test_update_idempotent_catch_up(tmp_path):
    calls = []

    def fake(day, syms, now, log=print):
        calls.append(now)
        return {k: v[v.index < now] for k, v in sample().items()}

    t1 = pd.Timestamp(f"{DAY} 10:16", tz=cl.NY)
    assert cl.update(tmp_path, DAY, t1, bars_fn=fake, names=NAMES, log=lambda *_: None) == 3
    assert cl.update(tmp_path, DAY, t1, bars_fn=fake, names=NAMES, log=lambda *_: None) == 0
    assert len(calls) == 1                                                   # nothing due -> no data request
    t2 = pd.Timestamp(f"{DAY} 11:31", tz=cl.NY)                              # missed 10:30..11:15 runs -> caught up
    assert cl.update(tmp_path, DAY, t2, bars_fn=fake, names=NAMES, log=lambda *_: None) == 5
    rows = cl.read_rows(tmp_path / "compass" / f"{DAY}.csv")
    assert [r["T"] for r in rows] == ["09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30"]
    assert [r["backfilled"] for r in rows] == ["1", "1", "0", "1", "1", "1", "1", "0"]   # > 10 min late = backfilled
    assert list(rows[0]) == cl.COLS
    j = json.loads((tmp_path / "compass" / "latest.json").read_text())
    assert j["date"] == DAY and j["asof"] == "11:30" and j["phase"] == "intraday" and len(j["timeline"]) == 8
    assert j["label"] == "Display only — not a trading signal" and j["disclaimer"] == "Educational only — not financial advice."
    assert isinstance(j["latest"]["spy_fo"], float) and j["latest"]["checkpoint"] == "UP"


def test_no_rows_before_the_first_mark(tmp_path):
    n = cl.update(tmp_path, DAY, pd.Timestamp(f"{DAY} 09:40", tz=cl.NY), bars_fn=lambda *a, **k: {}, names=NAMES,
                  log=lambda *_: None)
    assert n == 0 and not (tmp_path / "compass").exists()


def test_display_only_no_trading_imports():
    src = (ROOT / "mcf/report/compass_live.py").read_text()
    for bad in ("execution", "submit_order", "TradingClient", "config/", "paper-api"):
        assert bad not in src, bad
    assert "store._fetch_bars" in src                   # read-only market-data GET helper


def test_workflow():
    w = yaml.safe_load((ROOT / ".github/workflows/compass.yml").read_text())
    on = w[True] if True in w else w["on"]
    crons = [c["cron"] for c in on["schedule"]]
    assert crons == ["45 13 * * 1-5", "0,15,30,45 14-20 * * 1-5", "0 21 * * 1-5"] and "workflow_dispatch" in on
    job = w["jobs"]["record"]
    assert job["timeout-minutes"] <= 10 and w["concurrency"]["group"] == "compass"
    assert job["env"]["ALPACA_API_KEY"] == "${{ secrets.ALPACA_API_KEY }}"
    text = (ROOT / ".github/workflows/compass.yml").read_text()
    assert "TZ=America/New_York" in text and "0945" in text and "mcf.report.compass_live" in text and "--push" in text
    assert "echo \"$ALPACA" not in text and "echo $ALPACA" not in text        # never print secrets
    assert "trade.yml" not in text.split("name: compass")[1]


def test_dashboard_card():
    html = (ROOT / "docs/live/index.html").read_text()
    i = html.index('id="cmp-card"')
    card = html[i:i + 9000]
    assert "Market Compass (live)" in card and "Display only — not a trading signal" in card
    assert "Educational only — not financial advice" in card
    assert '"mcf-data-compass/"' in card and '"compass/latest.json"' in card
    assert html.index('id="team-card"') < i < html.index('id="live"')
