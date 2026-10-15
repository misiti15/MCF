"""EOD per-trade charts (owner 2026-10-15): best 3 / worst 5, 3-minute candles 09:00-16:00 ET, inline CID images.
Synthetic bars only, no network. Educational only - not financial advice."""

from email.message import EmailMessage

import numpy as np
import pandas as pd

from mcf.journal import Journal
from mcf.report import eod, trade_charts

DAY = "2026-10-06"
NY = "America/New_York"


def _bars(seed=0):
    idx = pd.date_range(f"{DAY} 04:00", f"{DAY} 19:59", freq="1min", tz=NY)   # Alpaca 1-min incl. extended hours
    rng = np.random.default_rng(seed)
    c = 50 + np.cumsum(rng.normal(0, 0.03, len(idx)))
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.02, "low": np.minimum(o, c) - 0.02, "close": c,
                         "volume": rng.integers(100, 5000, len(idx)).astype(float)}, index=idx)


def _journal(tmp_path, n=10):
    j = Journal(tmp_path / "j.db")
    rid = j.get_or_create_run("paper", "MCF Update (live paper)")
    base = dict(strategy="MF4-h40-open-flowsell", date=DAY, signal_time=f"{DAY}T10:00:00-04:00", exit_reason="target",
                mae_r=None, mfe_r=None, success=1, shares=10, meta="")
    rows = []
    for i in range(n):
        pct = (i - 4) * 0.5   # 4 losers, 1 flat, 5 winners
        side = -1 if i % 2 else 1
        entry = 50.0
        rows.append(dict(base, symbol=f"T{i}", side=side, entry_time=f"{DAY}T10:{10 + i:02d}:17-04:00", entry=entry,
                         stop=entry - side * 0.5, target=entry + side * 1.0, exit_time=f"{DAY}T1{1 + i % 4}:41:05-04:00",
                         exit=entry * (1 + side * pct / 100), r_multiple=pct / 1.0, pnl=pct * 5))
    j.add_trades(rid, pd.DataFrame(rows))
    return j, rid


def test_pick_ranks_best3_by_gain_and_worst5_by_loss(tmp_path):
    j, rid = _journal(tmp_path)
    tr = j.trades(run_id=rid)
    w, l = trade_charts.pick(tr)
    assert list(w["symbol"]) == ["T9", "T8", "T7"]
    assert list(l["symbol"]) == ["T0", "T1", "T2", "T3"]   # only 4 losers exist; flat trade excluded
    assert (l["pct"] < 0).all() and (w["pct"] > 0).all()


def test_window_includes_premarket_in_3min_steps():
    w = trade_charts.window(_bars(), DAY)
    assert w.index[0] == pd.Timestamp(f"{DAY} 09:00", tz=NY)
    assert w.index[-1] == pd.Timestamp(f"{DAY} 15:57", tz=NY)
    assert len(w) == 140 and (w.index < pd.Timestamp(f"{DAY} 09:30", tz=NY)).sum() == 10
    assert set(w.index.to_series().diff().dropna()) == {pd.Timedelta(minutes=3)}


def test_chart_png_and_trade_times_inside_plot(tmp_path):
    j, rid = _journal(tmp_path)
    tr = j.trades(run_id=rid)
    row = tr.iloc[9].copy()
    png = trade_charts.chart(_bars(), row, DAY)
    assert png[:4] == b"\x89PNG" and len(png) < 150_000
    import struct
    wpx, hpx = struct.unpack(">II", png[16:24])
    assert (wpx, hpx) == (900, 500)
    lo, hi = pd.Timestamp(f"{DAY} 09:00", tz=NY), pd.Timestamp(f"{DAY} 16:00", tz=NY)
    assert lo <= row["entry_time"] <= hi and lo <= row["exit_time"] <= hi


def test_no_bars_means_note_not_failure(tmp_path):
    j, rid = _journal(tmp_path)
    tr = j.trades(run_id=rid)
    assert trade_charts.chart(None, tr.iloc[0], DAY) is None
    rep = eod.build(j, rid, DAY, None, chart_bars={})
    assert "Chart unavailable" in rep["html"] and rep["charts"] == []


def test_email_html_references_inline_images_and_saves_files(tmp_path):
    j, rid = _journal(tmp_path)
    bars = {f"T{i}": _bars(i) for i in range(10) if i != 2}   # T2 (a loser) has no bars
    rep = eod.build(j, rid, DAY, None, chart_bars=bars)
    assert len(rep["charts"]) == 3 + 3
    for c in rep["charts"]:
        assert f'src="cid:{c["cid"][1:-1]}"' in rep["html"] and c["png"][:4] == b"\x89PNG"
    assert rep["html"].count("Chart unavailable") == 1 and "Educational only" in rep["html"]
    assert "Worst 5 trades (by % lost)" in rep["html"] and "Top 3 winning trades (by % gained)" in rep["html"]
    # the SMTP message carries every image as a related part with a matching Content-ID
    msg = EmailMessage()
    msg.set_content(rep["text"])
    msg.add_alternative(rep["html"], subtype="html")
    msg.get_payload()[1].add_related(rep["png"], "image", "png", cid=rep["cid"])
    for c in rep["charts"]:
        msg.get_payload()[1].add_related(c["png"], "image", "png", cid=c["cid"], filename=c["name"])
    cids = {p["Content-ID"] for p in msg.walk() if p.get_content_maintype() == "image"}
    assert {c["cid"] for c in rep["charts"]} <= cids
    eod.save(rep, tmp_path / "reports", DAY)
    page = (tmp_path / "reports" / f"{DAY}.html").read_text()
    for c in rep["charts"]:
        assert (tmp_path / "reports" / "charts" / DAY / c["name"]).exists() and f"charts/{DAY}/{c['name']}" in page
    assert "cid:" not in page


def test_send_attaches_charts(monkeypatch, tmp_path):
    j, rid = _journal(tmp_path)
    rep = eod.build(j, rid, DAY, None, chart_bars={"T9": _bars()})
    sent = {}

    class FakeSMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, *a):
            pass

        def send_message(self, m):
            sent["m"] = m

    monkeypatch.setenv("MCF_SMTP_USER", "u@example.com")
    monkeypatch.setenv("MCF_SMTP_PASSWORD", "x")
    monkeypatch.setattr(eod.smtplib, "SMTP_SSL", FakeSMTP)
    assert eod.send(rep, "to@example.com", DAY)
    cids = {p["Content-ID"] for p in sent["m"].walk() if p.get_content_maintype() == "image"}
    assert rep["charts"][0]["cid"] in cids and rep["cid"] in cids
