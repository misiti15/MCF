from datetime import date

from mcf.data import earnings as E


def test_window_is_four_trading_days_each_side():
    w = E.window(date(2026, 10, 7), 4)
    assert w[0] == date(2026, 10, 1) and w[-1] == date(2026, 10, 13) and len(w) == 9


def test_blackout_from_calendar_and_cache(tmp_path):
    calls = []

    def get(url):
        calls.append(url)
        d = url.rsplit("=", 1)[1]
        return {"data": {"rows": [{"symbol": "GH"}] if d == "2026-10-09" else [{"symbol": "ZZZ"}]}}

    r = E.blackout(date(2026, 10, 7), ["GH", "TWLO"], 4, tmp_path, get=get, log=lambda *a: None)
    assert set(r["symbols"]) == {"GH"} and r["complete"] and r["source"] == "nasdaq"
    n = len(calls)
    E.blackout(date(2026, 10, 7), ["GH", "TWLO"], 4, tmp_path, get=get, log=lambda *a: None)
    assert len(calls) == n                       # second job of the day reuses the cached list


def test_blackout_falls_back_when_calendar_down(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "_alpaca_news", lambda syms, a, b: {"GH": ["2026-10-05"]})

    def down(url):
        raise OSError("blocked")

    r = E.blackout(date(2026, 10, 7), ["GH"], 4, tmp_path, get=down, log=lambda *a: None)
    assert r["source"] == "alpaca-news" and not r["complete"] and "GH" in r["symbols"]
