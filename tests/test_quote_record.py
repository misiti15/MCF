"""Recorded live quotes (owner 2026-11-17 "Yes if it enhances our replay efficiency"): every journaled decision records
the quote it used (no extra API call), a recording failure never touches the trade path, and the calibrated replay
prefers the recorded quote over the spread model. Educational only - not financial advice."""

import gzip
import json
from types import SimpleNamespace as NS

import pandas as pd

import mcf.execution.runner as R
from mcf.replay import harness, livecal
from mcf.strategies.base import Signal
from tests.test_outage import NOW, _xc_runner
from tests.test_replay import DAY, NY, _cfg, _session


class _Client:
    def __init__(self, bid, ask):
        self.bid, self.ask, self.calls = bid, ask, 0

    def get_stock_latest_quote(self, req):
        self.calls += 1
        s = req.symbol_or_symbols
        return {s: NS(bid_price=self.bid, ask_price=self.ask, bid_size=3, ask_size=7,
                      timestamp=(NOW - pd.Timedelta(seconds=2)).tz_convert("UTC").to_pydatetime())}


def _runner(tmp_path, monkeypatch, bid=9.99, ask=10.01):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, bid, ask)
    q = _Client(bid, ask)
    r._quote = R.PaperRunner._quote.__get__(r)                 # the real quote fetch, on a stub data client
    r._client = lambda: q
    r.quote_log_dir = str(tmp_path / "quotes")
    return r, c, ctx, q


def _go(r, ctx, sym="XYZ", strat="A", stop=9.0):
    r._enter(Signal(sym, strat, 1, 10, stop=stop, target=12.0), 10.0, (sym, strat), ctx, NOW)
    return r.journal.signals(r.run_id).iloc[-1]


def _read(tmp_path):
    out = []
    for p in sorted((tmp_path / "quotes" / str(NOW.date())).glob("*.jsonl.gz")):
        out += [json.loads(x) for x in gzip.decompress(p.read_bytes()).decode().splitlines()]
    return out


def test_records_traded_and_skipped_without_extra_calls(tmp_path, monkeypatch):
    r, c, ctx, q = _runner(tmp_path, monkeypatch)
    assert _go(r, ctx).status == "submitted"
    assert q.calls == 1                                          # one quote per entry, as before
    r.risk.check = lambda sig, px: (False, "max trades")         # a skip before any quote fetch
    assert _go(r, ctx, "QQQ", "B").status == "skipped"
    assert q.calls == 1
    del r.risk.check
    s = _go(r, ctx, "ABC", "C", stop=9.99)                       # spread 2c of a 1c stop: skipped on the quote
    assert s.status == "skipped" and "stop distance" in s.reason
    assert r.flush_quote_log(NOW, force=True)
    recs = _read(tmp_path)
    assert [x["status"] for x in recs] == ["submitted", "skipped", "skipped"]
    a, b, k = recs
    assert a["bid"] == 9.99 and a["ask"] == 10.01 and a["bs"] == 3 and a["az"] == 7 and a["bps"] == 20.0
    assert pd.Timestamp(a["qts"]) == NOW - pd.Timedelta(seconds=2) and pd.Timestamp(a["t"]) == NOW
    assert b["bid"] is None and b["why"] == "max trades"
    assert k["bid"] == 9.99 and "stop distance" in k["why"]


def test_recording_failure_never_touches_the_trade(tmp_path, monkeypatch):
    r, c, ctx, q = _runner(tmp_path, monkeypatch)
    r._quote_buf = None                                          # every append now raises
    s = _go(r, ctx)
    assert s.status == "submitted" and len(c.orders) == 1
    r2, c2, ctx2, _ = _runner(tmp_path / "b", monkeypatch)
    r2.quote_log_dir = None                                      # recording off: same decision
    assert _go(r2, ctx2).status == "submitted" and len(c2.orders) == 1
    assert r2._quote_buf == []


def test_parse_quotes_keys_by_symbol_and_decision_second():
    lines = [json.dumps({"t": "2026-11-18T10:00:20.512+00:00", "sym": "AAA", "bid": 9.9, "ask": 10.1,
                         "qts": "2026-11-18T10:00:19+00:00", "bps": 200.0}),
             json.dumps({"t": "2026-11-18T10:01:20+00:00", "sym": "AAA", "bid": None}), "not json"]
    q = livecal.parse_quotes(lines)
    assert list(q) == [("AAA", pd.Timestamp("2026-11-18T10:00:20+00:00").value)]
    assert q[next(iter(q))][3] == 200.0


def test_livecal_prefers_recorded_quotes(tmp_path):
    from tests.test_replay_livecal import _schedule

    bars, priors = _session()
    cfg = _cfg(tmp_path)
    sh = {s: (True, True) for s in bars}
    sched = _schedule(skip_from="15:00", skip_to="15:01", late_at="15:30")

    def run(recorded):
        cal = livecal.Calibrator({"polls": False, "recorded_quotes": False}, "none", DAY)
        cal.polls, cal.recorded = sched, recorded
        res = harness.run_session(cfg, DAY, bars, priors, spreads={}, shortable=sh, check=0, log=lambda m: None,
                                  hook=cal)
        return res, cal

    base, cal0 = run({})
    assert cal0.notes["quotes_real"] == 0 and cal0.notes["quote_records"] == 0
    sub = base["signals"][base["signals"].status == "submitted"]
    assert len(sub)
    row = sub.iloc[0]
    t = pd.Timestamp(row["ts"]).tz_convert(NY).floor("s")
    px = float(row["ref_price"])
    wide = {(row["symbol"], t.value): (px * 0.97, px * 1.03, None, 600.0)}   # live saw a 600 bps spread
    res, cal = run(wide)
    s = res["signals"]
    hit = s[(s.symbol == row["symbol"]) & (s.strategy == row["strategy"]) & (pd.to_datetime(s.ts) == row["ts"])]
    assert len(hit) and hit.iloc[0].status == "skipped" and "spread" in hit.iloc[0].reason
    assert cal.notes["quotes_real"] >= 1 and cal.notes["quotes_modelled"] >= 1
