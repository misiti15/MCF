"""Intraday tracker (owner 2026-11-05): each poll record carries a marked-to-market snapshot ("mtm") built from state the
runner already holds; it never changes a trading decision and never raises; mcf.report.intraday rebuilds the day's R
curve from the snapshots (or from the journal + bars for older days). Educational only - not financial advice."""
import gzip
import json
import os

import pandas as pd

import mcf.execution.runner as R
from mcf.report import intraday as I
from test_lots import NY, FakeAlpaca, _runner
from test_lots import Fires as _Fires
from test_lots import _poll


def _orders(c):
    return [(o.client_order_id, o.symbol, o.side, str(o.qty)) for o in c.orders]


def _session(r, monkeypatch, c):
    _poll(r, monkeypatch, "1006")                         # 10:05 bar -> lot 1
    c.fill(c.orders[0].client_order_id, 10.0)
    _poll(r, monkeypatch, "1007")
    _poll(r, monkeypatch, "1121")                         # 11:20 bar -> lot 2
    _poll(r, monkeypatch, "1122")


def test_snapshot_logging_does_not_change_orders(tmp_path, monkeypatch):
    out = {}
    for on in (False, True):
        d = tmp_path / str(on)
        d.mkdir()
        r, c = _runner(d, monkeypatch, client=FakeAlpaca(), strategies=[_Fires("A", at={"1005", "1120"})])
        r.poll_log_dir = str(d / "polls") if on else None
        _session(r, monkeypatch, c)
        sig = r.journal.signals(r.run_id)[["symbol", "strategy", "side", "status", "reason", "qty"]]
        out[on] = (_orders(c), sig.to_dict("records"), {k: sorted(v) for k, v in r.lots.items()})
        if on:
            recs = [json.loads(x) for x in r._poll_buf]
            assert all("mtm" in x for x in recs) and not any("mtm_err" in x for x in recs)
            last = recs[-1]["mtm"]
            assert last["nl"] == 2 and last["ns"] == 0 and len(last["pos"]) == 2
            sym, setup, side, entry, px, ur, frac = last["pos"][0]
            assert (sym, setup, side, frac) == ("XYZ", "A", 1, 1.0)
            assert entry == 10.0 and px == 10.0 and ur == 0.0      # bars close at 10.0, stop 9.0 -> 0R
            assert last["idx"] == {"SPY": None, "QQQ": None, "IWM": None}   # not in this runner's bars
    assert out[True] == out[False]


def test_snapshot_errors_are_swallowed(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch, client=FakeAlpaca(), strategies=[_Fires("A", at={"1005"})])
    r.poll_log_dir = str(tmp_path / "polls")
    monkeypatch.setattr(R, "mtm_snapshot", lambda *a, **k: 1 / 0)
    _poll(r, monkeypatch, "1006")
    rec = json.loads(r._poll_buf[-1])
    assert rec["mtm_err"] == "ZeroDivisionError" and "got" in rec       # the poll record itself is still logged
    assert len(c.orders) == 1                                           # and trading went on
    monkeypatch.setattr(r, "_mtm_snapshot", lambda bars: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(R, "poll_record", lambda *a, **k: 1 / 0)
    _poll(r, monkeypatch, "1007")                                       # never raises


def test_mtm_snapshot_math_and_index():
    idx = pd.date_range(pd.Timestamp("2026-10-13 09:30", tz=NY), periods=31, freq="1min")
    b = lambda o, c: pd.DataFrame({"open": o, "high": c, "low": o, "close": [o] * 30 + [c]}, index=idx)
    lots = {"XYZ": {"L1": {"strategy": "A", "side": 1, "qty": 100, "order_id": "o1"},
                    "L2": {"strategy": "B", "side": -1, "qty": 10, "order_id": "o2", "left": 5, "orig_qty": 10}}}
    snap = R.mtm_snapshot(lots, {"L1": (10.0, 9.0), "L2": (10.0, 11.0)}, {"XYZ": b(10.0, 12.0), "SPY": b(500.0, 505.0)},
                          1.5, {"A": 1.5, "B": 0.0}, {"o1": 10.5})
    p1, p2 = snap["pos"]
    assert p1[3] == 10.5 and p1[5] == round((12 - 10.5) / 1.5, 3)          # the fill price when known
    assert p2[5] == round(-1 * (12 - 10) / 1 * 0.5, 3) and p2[6] == 0.5
    assert snap["ur"] == round(p1[5] + p2[5], 3) and snap["rr"] == 1.5 and snap["rs"] == {"A": 1.5}
    assert snap["nl"] == 1 and snap["ns"] == 1 and snap["net"] == round(12 * 100 - 12 * 5)
    assert snap["idx"]["SPY"] == [505.0, 1.0] and snap["idx"]["QQQ"] is None


def _write_fixture(sd, day):
    recs = []
    for i, (t, rr, pos) in enumerate([
            ("10:00:05", 0.0, []),
            ("10:01:05", 0.0, [["XYZ", "A", 1, 10.0, 10.5, 0.5, 1.0]]),
            ("10:02:05", 0.0, [["XYZ", "A", 1, 10.0, 11.0, 1.0, 1.0], ["ABC", "B", -1, 20.0, 20.5, -0.5, 1.0]]),
            ("10:03:05", 1.2, [["ABC", "B", -1, 20.0, 19.0, 1.0, 1.0]]),
            ("10:04:05", 1.2, [])]):
        recs.append({"t": t, "got": 2, "mtm": {"rr": rr, "rs": {}, "ur": round(sum(p[5] for p in pos), 3), "pos": pos,
                                                "nl": sum(p[2] == 1 for p in pos), "ns": sum(p[2] == -1 for p in pos),
                                                "net": 0, "gross": 0, "idx": {"SPY": [500.0, 0.1 * i], "QQQ": None,
                                                                              "IWM": None}}})
    d = sd / "polls" / day
    d.mkdir(parents=True)
    with gzip.open(d / "100500.jsonl.gz", "wt") as f:
        f.write("\n".join(json.dumps(x) for x in recs) + "\n")


def test_reader_rebuilds_curve_from_snapshots(tmp_path):
    day = "2026-10-13"
    _write_fixture(tmp_path, day)
    res = I.build(day, "primary", 1, state_dir=str(tmp_path), out=str(tmp_path / "out" / "p.png"), log=lambda *a: None)
    assert res["source"] == "snapshots" and os.path.exists(res["png"]) and os.path.exists(res["csv"])
    c = res["curve"]
    at = lambda hhmm: c.loc[pd.Timestamp(f"{day} {hhmm}", tz=NY)]
    assert at("10:01")["total_r"] == 0.0 and at("10:02")["total_r"] == 0.5
    assert at("10:03")["total_r"] == 0.5 and at("10:04")["total_r"] == 2.2 and at("10:05")["total_r"] == 1.2
    assert at("15:59")["total_r"] == 1.2 and at("10:05")["spy_pct"] == 0.4
    ev = res["events"]
    assert list(zip(ev.kind, ev.symbol)) == [("entry", "XYZ"), ("entry", "ABC"), ("exit", "XYZ"), ("exit", "ABC")]
    txt = open(res["csv"]).read()
    assert "source: snapshots" in txt and "Educational only" in txt and "+A:XYZ:L" in txt


def test_reader_falls_back_to_journal_and_bars():
    day = "2026-10-13"
    t = pd.DataFrame([{"symbol": "XYZ", "strategy": "A", "side": 1, "entry": 10.0, "stop": 9.0,
                       "entry_time": "2026-10-13 14:00:00+00:00", "exit_time": "2026-10-13 14:10:00+00:00",
                       "r_multiple": 0.9}])
    idx = pd.date_range(pd.Timestamp(f"{day} 09:30", tz=NY), periods=390, freq="1min")
    bars = {"XYZ": pd.DataFrame({"open": 10.0, "close": 11.0}, index=idx)}
    c, ev, src = I.curve_from_journal(t, day, 1, bars)
    assert src == "journal+bars" and len(ev) == 2
    assert c.loc[pd.Timestamp(f"{day} 10:05", tz=NY), "total_r"] == 1.0          # open: (11 - 10) / 1
    assert c.loc[pd.Timestamp(f"{day} 10:10", tz=NY), "total_r"] == 0.9          # booked R from the exit minute
    c2, _, src2 = I.curve_from_journal(t, day, 5, {})
    assert src2 == "journal (no bars: realized only)" and c2["total_r"].iloc[-1] == 0.9
