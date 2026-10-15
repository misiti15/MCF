"""Housekeeping 2026-10-15 (research/bdi/nightly1015 H-3, H-4). Educational only — not financial advice.

H-3: SIP bars were missing for every symbol 12:57-14:10 ET and nothing flagged it. The runner now marks
     health.data_stale, pauses new entries (open brackets untouched) and alerts once per outage.
H-4: Testing 2 SYNA / XRT lots stayed open for hours after a partial target fill. They held shares (residual 2 of 7,
     1 of 10), so they stay open lots; health.partial_lots shows them, and a lot is released as soon as its own fills
     cover its whole quantity (also when an OCO sibling leg still reports an open state)."""
from types import SimpleNamespace as NS

import pandas as pd

from tests.test_lots import DAY, LeakyAlpaca, NY, _runner, _setups, _three_filled


class Fires:
    """A market long on the latest bar, every poll."""

    name = "A"

    def eligible(self, ctx):
        return True

    def signals(self, ctx):
        from mcf.strategies.base import Signal

        return [Signal(ctx.symbol, self.name, 1, len(ctx.bars) - 1, stop=9.0, target=12.0)]


def _bars(last_hhmm, syms=("XYZ", "ABC", "DEF")):
    idx = pd.date_range(pd.Timestamp("2026-10-13 09:30", tz=NY), pd.Timestamp(f"2026-10-13 {last_hhmm}", tz=NY),
                        freq="1min")
    b = pd.DataFrame({"open": 10.0, "high": 10.05, "low": 9.95, "close": 10.0, "volume": 1e5}, index=idx)
    return {s: b for s in syms}


def _poll(r, monkeypatch, hhmm, last_bar):
    now = pd.Timestamp(f"2026-10-13 {hhmm}:05", tz=NY)
    bars = _bars(last_bar)
    monkeypatch.setattr(r, "fetch", lambda now: bars)
    monkeypatch.setattr(r, "_contexts", lambda b, today: [NS(symbol="XYZ", bars=b["XYZ"], avg_dollar_volume=5e8)])
    r.step(now)
    r._sync_open()


def test_outage_pauses_entries_flags_health_and_alerts_once(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch, client=LeakyAlpaca(), strategies=[Fires()])
    alerts = []
    monkeypatch.setattr(r, "_alert", lambda subj, text: alerts.append(subj))
    _poll(r, monkeypatch, "12:57", "12:56")                       # fresh: one entry
    assert len(c.orders) == 1 and r.health["data_stale"] is None
    for hhmm in ("13:01", "13:05", "13:30", "14:10"):             # bars stop at 12:56 (2026-10-15 pattern)
        _poll(r, monkeypatch, hhmm, "12:56")
    # 13:01 is 5 min after the newest 12:56 bar -> not yet stale; 13:05 onwards stale
    st = r.health["data_stale"]
    assert st is not None and st["last_bar"].startswith("2026-10-13 12:56") and st["fresh"] == 0 and st["of"] == 3
    assert st["since"].startswith("2026-10-13 13:05") and st["polls"] == 3
    assert len(alerts) == 1 and len(c.orders) == 1                 # one alert per outage, no entries on stale bars
    assert r.journal.signals(r.run_id).query("status == 'skipped'").empty   # nothing marked/journaled while stale
    _poll(r, monkeypatch, "14:12", "14:11")                       # data resumes: entries evaluated again
    assert r.health["data_stale"] is None and len(r.health["data_outages"]) == 1
    o = r.health["data_outages"][0]
    assert o["minutes"] == 67.0 and o["until"].startswith("2026-10-13 14:12")
    assert len(c.orders) == 2 and len(alerts) == 1
    for hhmm in ("14:20", "14:25"):                               # a second outage alerts again, once
        _poll(r, monkeypatch, hhmm, "14:11")
    assert len(alerts) == 2


def test_no_stale_flag_right_after_open_or_with_most_symbols_fresh(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    early = pd.Timestamp("2026-10-13 09:32:05", tz=NY)
    assert not r._check_data(early, {})                           # nothing to judge yet
    now = pd.Timestamp("2026-10-13 13:30:05", tz=NY)
    bars = {**_bars("13:29", syms=[f"S{i}" for i in range(20)]), **_bars("12:00", syms=["OLD"])}
    assert not r._check_data(now, bars) and r.health["data_stale"] is None   # one thin symbol stale is normal
    assert r._check_data(now, _bars("13:20")) and r.health["data_stale"]["stale_min"] == 10.1


def test_alert_uses_email_path_only_with_smtp_secrets(tmp_path, monkeypatch):
    import mcf.report.brief as brief

    sent = []
    monkeypatch.setattr(brief, "send_email", lambda subj, text, html, to: sent.append((subj, to, text)))
    r, _ = _runner(tmp_path, monkeypatch)
    monkeypatch.delenv("MCF_SMTP_USER", raising=False)
    monkeypatch.delenv("MCF_SMTP_PASSWORD", raising=False)
    r._alert("s", "t")
    assert sent == []
    monkeypatch.setenv("MCF_SMTP_USER", "u")
    monkeypatch.setenv("MCF_SMTP_PASSWORD", "p")
    monkeypatch.setenv("MCF_EMAIL_TO", "x@example.com")
    r._alert("s", "t")
    assert sent[0][:2] == ("s", "x@example.com") and "not financial advice" in sent[0][2]
    monkeypatch.setattr(brief, "send_email", lambda *a: (_ for _ in ()).throw(OSError("smtp down")))
    r._alert("s", "t")                                            # never raises


def test_daily_review_reports_the_outage(tmp_path, monkeypatch):
    from mcf.report.daily_review import build_review

    r, _ = _runner(tmp_path, monkeypatch)
    h = {"data_outages": [{"since": "2026-10-15 13:05:05-04:00", "until": "2026-10-15 14:12:05-04:00",
                           "minutes": 67.0, "last_bar": "2026-10-15 12:56:00-04:00"}]}
    rv = build_review(r.journal, r.run_id, "2026-10-15", h)
    assert any("stale from 13:05 to 14:12" in f for f in rv["findings"])


# ---------------------------------------------------------------- H-4 partial target fills of sibling lots
def _target_rest(c, coid, px):
    """The remainder of a partly filled target leg fills: the leg is now filled for the whole lot."""
    o = c.by_coid(coid)
    leg = next(l for l in o.legs if l.order_type == "limit")
    done = float(leg.filled_qty)
    rest = float(o.filled_qty) - done
    leg.status, leg.filled_qty, leg.filled_at = "filled", o.filled_qty, c._t()
    leg.filled_avg_price = str((done * float(leg.filled_avg_price) + rest * px) / float(o.filled_qty))
    for l in o.legs:
        if l is not leg and l.status in {"new", "held", "accepted", "pending_new", "partially_filled"}:
            l.status = "canceled"
    c._net(o.symbol, -rest)


def test_sibling_partial_target_is_a_residual_lot_then_released_when_its_rest_fills(tmp_path, monkeypatch):
    """SYNA 2026-10-15: two sibling lots; one lot's target fills part (5 of 7) and keeps working."""
    r, c = _runner(tmp_path, monkeypatch, client=LeakyAlpaca())
    q = _three_filled(r, c)
    b = "mcf-B-XYZ-20261013-1000"
    n = q["B"] - 2
    c.part_fill(b, 12.0, n)
    r.reconcile(DAY)
    assert set(_setups(r)) == {"A", "B", "C"} and r.journal.trades(run_id=r.run_id).empty   # B still holds 2 shares
    pl = {p["strategy"]: p for p in r.health["partial_lots"]}
    assert set(pl) == {"B"} and pl["B"]["left"] == 2 and pl["B"]["qty"] == q["B"]
    _target_rest(c, b, 12.0)                                       # its remaining 2 shares fill later
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id)
    assert list(t.strategy) == ["B"] and t.iloc[0].shares == q["B"] and t.iloc[0].exit_reason == "target"
    assert set(_setups(r)) == {"A", "C"} and r.risk.open_lots() == 2 and r.health["partial_lots"] == []


def test_lot_released_when_target_filled_but_oco_sibling_not_yet_cancelled(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch, client=LeakyAlpaca())
    q = _three_filled(r, c)
    a = c.by_coid("mcf-A-XYZ-20261013-1000")
    c.hit(a.client_order_id, "target", 12.0)
    next(l for l in a.legs if l.order_type == "stop").status = "pending_cancel"   # OCO cancel still in flight
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id)
    assert list(t.strategy) == ["A"] and t.iloc[0].shares == q["A"] and t.iloc[0].exit_reason == "target"
    assert set(_setups(r)) == {"B", "C"} and r.risk.open_lots() == 2
