"""PRE1 borrow / short-volume recorder: offline (mocked Alpaca + FINRA). Educational only - not financial advice."""

import csv
import gzip
import io
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

from mcf.data import borrow_record as br

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 3, 14, 8, tzinfo=timezone.utc)      # 09:08 ET (EST)

ASSETS = [
    {"symbol": "AAA", "exchange": "NASDAQ", "tradable": True, "shortable": True, "easy_to_borrow": True,
     "borrow_status": "easy_to_borrow", "marginable": True, "margin_requirement_short": "30",
     "maintenance_margin_requirement": 30, "attributes": ["has_options"]},
    {"symbol": "HTB", "exchange": "NYSE", "tradable": True, "shortable": True, "easy_to_borrow": False,
     "borrow_status": "hard_to_borrow", "marginable": True, "margin_requirement_short": "100",
     "maintenance_margin_requirement": 100, "attributes": []},
    {"symbol": "EPD", "exchange": "NYSE", "tradable": True, "shortable": False, "easy_to_borrow": False,
     "marginable": True, "attributes": ["ptp_no_exception"]},
    {"symbol": "OTCX", "exchange": "OTC", "tradable": True, "shortable": False},           # dropped: exchange
    {"symbol": "BRK.B", "exchange": "NYSE", "tradable": True, "shortable": True},         # dropped: dot
    {"symbol": "ABCDW", "exchange": "NASDAQ", "tradable": True, "shortable": False},      # dropped: warrant
    {"symbol": "NOTR", "exchange": "NYSE", "tradable": False, "shortable": False},        # dropped: not tradable
]
FINRA = ("Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
         "20261102|AAA|1000|10|2500|B,Q,N\n20261102|HTB|700|0|900|Q,N\n20261102|ZZZ|1|0|2|N\n3\n")
CAL = [{"date": "2026-10-30"}, {"date": "2026-11-02"}, {"date": "2026-11-03"}]


def _get(calls, cal=CAL, assets=ASSETS):
    def get(path, params=None):
        calls.append(path)
        return {"/calendar": cal, "/assets": assets}[path]
    return get


def _uni(tmp_path):
    p = tmp_path / "universe.csv"
    p.write_text("symbol,tier,adv_rank,built_at\nAAA,core,1,2026-11-02T13:47:23+00:00\n")
    return str(p)


def _read(path):
    with gzip.open(path, "rt") as f:
        return list(csv.DictReader(f))


def test_records_flags_finra_and_index(tmp_path):
    calls, urls = [], []
    st = tmp_path / "state"
    res = br.record(str(st), _uni(tmp_path), now=NOW, get=_get(calls),
                    fetch=lambda u: (urls.append(u), (200, FINRA))[1])
    assert calls == ["/calendar", "/assets"]                       # read-only GETs only
    assert urls == ["https://cdn.finra.org/equity/regsho/daily/CNMSshvol20261102.txt"]   # prior session
    rows = {r["symbol"]: r for r in _read(st / "borrow" / "2026-11-03.csv.gz")}
    assert set(rows) == {"AAA", "HTB", "EPD"}
    assert list(_read(st / "borrow" / "2026-11-03.csv.gz")[0]) == br.COLUMNS
    a, h, e = rows["AAA"], rows["HTB"], rows["EPD"]
    assert (a["shortable"], a["easy_to_borrow"], a["in_universe"], a["tier"], a["adv_rank"]) == ("1", "1", "1", "core", "1")
    assert (a["short_volume"], a["short_exempt_volume"], a["total_volume"], a["finra_market"]) == ("1000", "10", "2500", "B,Q,N")
    assert (h["easy_to_borrow"], h["borrow_status"], h["margin_req_short"], h["in_universe"]) == ("0", "hard_to_borrow", "100", "0")
    assert (e["ptp"], e["shortable"], e["total_volume"]) == ("1", "0", "")
    idx = [json.loads(x) for x in (st / "borrow" / "index.jsonl").read_text().splitlines()]
    assert idx == [res]
    assert res["finra_status"] == "ok" and res["finra_date"] == "2026-11-02" and res["finra_matched"] == 2
    assert res["rows"] == 3 and res["universe_rows"] == 1 and res["universe_built_at"].startswith("2026-11-02")
    assert "Educational only" in (st / "README.md").read_text()


def test_monday_prior_session_skips_weekend_and_missing_finra_still_records(tmp_path):
    urls = []
    now = datetime(2026, 11, 2, 14, 10, tzinfo=timezone.utc)
    res = br.record(str(tmp_path), None, now=now, get=_get([], cal=CAL[:2]), fetch=lambda u: (urls.append(u), (404, ""))[1])
    assert urls[0].endswith("CNMSshvol20261030.txt")
    assert res["finra_status"] == "missing" and res["finra_rows"] == 0 and res["universe_built_at"] is None
    rows = _read(tmp_path / "borrow" / "2026-11-02.csv.gz")
    assert len(rows) == 3 and all(r["total_volume"] == "" and r["in_universe"] == "0" for r in rows)


def test_finra_network_error_is_not_fatal(tmp_path):
    res = br.record(str(tmp_path), None, now=NOW, get=_get([]), fetch=lambda u: (0, "URLError"))
    assert res["finra_status"] == "error URLError" and res["rows"] == 3


def test_holiday_window_and_idempotent_skips(tmp_path):
    calls = []
    # market holiday: calendar has no row for today -> no asset call, no file
    res = br.record(str(tmp_path), None, now=NOW, get=_get(calls, cal=CAL[:2]), fetch=lambda u: (200, FINRA))
    assert "not a market day" in res["skipped"] and calls == ["/calendar"]
    assert not (tmp_path / "borrow").exists()
    # outside the ET window (EST off-season cron line = 08:08 ET): nothing called at all
    calls.clear()
    res = br.record(str(tmp_path), None, now=datetime(2026, 11, 3, 13, 8, tzinfo=timezone.utc), get=_get(calls))
    assert "outside" in res["skipped"] and calls == []
    # weekend
    assert "outside" in br.record(str(tmp_path), None, now=datetime(2026, 11, 7, 14, 8, tzinfo=timezone.utc),
                                  get=_get(calls))["skipped"]
    # second run the same day is a no-op
    br.record(str(tmp_path), None, now=NOW, get=_get([]), fetch=lambda u: (200, FINRA))
    calls.clear()
    res = br.record(str(tmp_path), None, now=NOW, get=_get(calls), fetch=lambda u: (200, FINRA))
    assert "already recorded" in res["skipped"] and calls == []
    assert len((tmp_path / "borrow" / "index.jsonl").read_text().splitlines()) == 1


def test_calendar_down_assumes_market_day_and_prev_weekday(tmp_path):
    def get(path, params=None):
        if path == "/calendar":
            raise OSError("down")
        return ASSETS
    urls = []
    now = datetime(2026, 11, 2, 14, 10, tzinfo=timezone.utc)      # Monday
    res = br.record(str(tmp_path), None, now=now, get=get, fetch=lambda u: (urls.append(u), (200, FINRA))[1])
    assert res["calendar"] == "unreachable" and urls[0].endswith("20261030.txt")


def test_empty_asset_list_fails_loudly(tmp_path):
    with pytest.raises(RuntimeError):
        br.record(str(tmp_path), None, now=NOW, get=_get([], assets=[]), fetch=lambda u: (200, FINRA))
    assert not (tmp_path / "borrow" / "2026-11-03.csv.gz").exists()


def test_parse_finra_ignores_header_trailer_and_garbage():
    assert br.parse_finra("<html>nope</html>") == {}
    d = br.parse_finra(FINRA)
    assert set(d) == {"AAA", "HTB", "ZZZ"}


def test_gzip_is_deterministic(tmp_path):
    rows = br.build_rows(br.candidate_flags(ASSETS), br.parse_finra(FINRA), {})
    a, b = tmp_path / "a.csv.gz", tmp_path / "b.csv.gz"
    br.write_gz_csv(a, rows)
    br.write_gz_csv(b, rows)
    assert a.read_bytes() == b.read_bytes()


def test_no_secret_reaches_disk_or_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ALPACA_API_KEY", "PKSECRETKEYID")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "VERYSECRETVALUE")
    seen = {}

    class R(io.BytesIO):
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=0):
        seen.setdefault("hdr", dict(req.header_items()))
        if "calendar" in req.full_url:
            return R(json.dumps(CAL).encode())
        if "assets" in req.full_url:
            assert req.get_method() == "GET"
            return R(json.dumps(ASSETS).encode())
        return R(FINRA.encode())

    monkeypatch.setattr(br.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(br, "datetime", type("D", (), {"now": staticmethod(lambda tz=None: NOW)}))
    assert br.main(["--state-dir", str(tmp_path), "--ignore-window"]) == 0
    assert "VERYSECRETVALUE" in json.dumps(seen["hdr"])          # sent as a header only
    blob = capsys.readouterr().out + "".join(p.read_bytes().decode("latin-1") for p in tmp_path.rglob("*")
                                             if p.is_file() and p.suffix != ".gz")
    blob += "".join(gzip.decompress(p.read_bytes()).decode() for p in tmp_path.rglob("*.gz"))
    assert "VERYSECRETVALUE" not in blob and "PKSECRETKEYID" not in blob


def test_workflow_is_one_short_job_off_the_peaks():
    wf = yaml.safe_load((ROOT / ".github/workflows/borrow-record.yml").read_text())
    jobs = wf["jobs"]
    assert list(jobs) == ["record"] and jobs["record"]["timeout-minutes"] <= 5
    assert "strategy" not in jobs["record"]                      # no matrix: one runner
    assert jobs["record"]["env"]["STATE_BRANCH"] == "mcf-data-borrow"
    crons = [c["cron"] for c in wf[True]["schedule"]]
    assert crons == ["8 13,14 * * 1-5"]
    # 13:08 / 14:08 UTC -> 08:08 / 09:08 / 10:08 ET across EST/EDT: none in 09:30-09:50 or 14:30-14:40
    for hhmm in ("0808", "0908", "1008"):
        assert not ("0930" <= hhmm < "0950" or "1430" <= hhmm < "1440")
    assert "borrow" not in (ROOT / ".github/workflows/trade.yml").read_text()
    text = (ROOT / ".github/workflows/borrow-record.yml").read_text()
    assert "run: pip" not in text and "Educational only" in text
