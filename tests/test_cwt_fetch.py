"""Offline tests for the Chat With Traders transcript collector (research/bdi/cwt/actions/fetch_cwt.py).
Network is mocked throughout. Educational only - not financial advice."""
import importlib.util
import json
from pathlib import Path

import pytest

_P = Path(__file__).resolve().parents[1] / "research/bdi/cwt/actions/fetch_cwt.py"
_spec = importlib.util.spec_from_file_location("fetch_cwt", _P)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>Chat With Traders</title>
<item><title>Ep 250: Opening range breakouts with Jane Doe</title>
 <itunes:episode>250</itunes:episode><pubDate>Tue, 05 Jan 2021 10:00:00 +0000</pubDate>
 <itunes:duration>01:05:30</itunes:duration>
 <enclosure url="https://chtbl.com/track/AB12/traffic.libsyn.com/cwt/ep250.mp3" type="audio/mpeg" length="1"/>
 <link>https://chatwithtraders.com/ep-250-jane-doe/</link><guid>g250</guid>
 <content:encoded><![CDATA[<p>Jane trades the open.</p><p><a href="https://chatwithtraders.com/transcripts/250">Read the transcript</a>
 &middot; <a href="https://www.youtube.com/watch?v=AbCdEfGhIjK">Watch</a></p>]]></content:encoded></item>
<item><title>042 | John Smith - Fading gaps</title><pubDate>Mon, 01 Feb 2016 10:00:00 +0000</pubDate>
 <itunes:duration>3900</itunes:duration><enclosure url="https://traffic.libsyn.com/cwt/ep42.mp3" type="audio/mpeg"/>
 <description>Gap fades.</description></item>
<item><title>Bonus: Q&amp;A live session</title><pubDate>Mon, 01 Mar 2021 10:00:00 +0000</pubDate>
 <enclosure url="https://traffic.libsyn.com/cwt/bonus.mp3" type="audio/mpeg"/></item>
</channel></rss>"""


def test_parse_rss_fields():
    eps = C.parse_rss(RSS, "feedA")
    e = {x["key"]: x for x in eps}
    a = e["ep250"]
    assert a["number"] == 250 and a["date"] == "2021-01-05" and a["duration_sec"] == 3930
    assert a["guest"] == "Jane Doe" and a["youtube_ids"] == ["AbCdEfGhIjK"]
    assert "Jane trades the open." in a["notes"]
    assert any("transcript" in lk["text"].lower() for lk in a["links"])
    b = e["ep042"]
    assert b["guest"] == "John Smith" and b["duration_sec"] == 3900
    assert any(k.startswith("x20210301-bonus") for k in e)


@pytest.mark.parametrize("title,num", [("Ep 42: X", 42), ("042 | John", 42), ("Episode 7 - Foo", 7),
                                       ("Linda Raschke | Chat With Traders Ep. 251", 251), ("#88: Bar", 88),
                                       ("Trading in 2020: lessons", None), ("Bonus: Q&A", None)])
def test_parse_number(title, num):
    assert C.parse_number(title) == num


def test_parse_guest_variants():
    assert C.parse_guest("Ep 12: Building a systematic edge w/ Kevin Davey") == "Kevin Davey"
    assert C.parse_guest("120: Linda Raschke – Momentum and mean reversion") == "Linda Raschke"
    assert C.parse_guest("How to trade the open") == ""


def test_merge_episodes_prefers_richer_record():
    a = C.parse_rss(RSS, "feedA")
    b = [dict(x, audio_url="", notes="", feeds=["feedB"]) for x in a]
    m = {x["key"]: x for x in C.merge_episodes([b, a])}
    assert m["ep250"]["audio_url"].endswith("ep250.mp3") and set(m["ep250"]["feeds"]) == {"feedA", "feedB"}


def test_build_episode_list_uses_itunes_feed_and_survives_dead_feeds():
    def get(url, binary=False):
        if "itunes.apple.com/search" in url:
            return json.dumps({"results": [
                {"collectionName": "Chat With Traders", "feedUrl": "https://feed.example/rss", "collectionId": 1,
                 "trackCount": 300},
                {"collectionName": "Other show", "feedUrl": "https://other/rss"}]})
        if url == "https://feed.example/rss":
            return RSS
        raise OSError("403")
    eps, rep = C.build_episode_list(get)
    assert len(eps) == 3 and rep[0] == {"feed": "https://feed.example/rss", "episodes": 3}
    assert all("other" not in r["feed"] for r in rep)
    assert any("error" in r for r in rep)


def test_itunes_lookup_fallback_when_no_rss():
    def get(url, binary=False):
        if "search" in url:
            return json.dumps({"results": [{"collectionName": "Chat With Traders", "collectionId": 9}]})
        if "lookup" in url:
            return json.dumps({"results": [{"wrapperType": "track"},
                                           {"wrapperType": "podcastEpisode", "trackName": "Ep 300: A B with Cee Dee",
                                            "releaseDate": "2024-01-02T00:00:00Z", "trackTimeMillis": 3_600_000,
                                            "episodeUrl": "https://x/300.mp3"}]})
        raise OSError("403")
    eps, rep = C.build_episode_list(get)
    assert [e["key"] for e in eps] == ["ep300"] and eps[0]["duration_sec"] == 3600
    assert rep[-1]["feed"] == "itunes-lookup"


def test_unwrap_tracking():
    assert C.unwrap_tracking("https://chtbl.com/track/AB12/traffic.libsyn.com/cwt/a.mp3") == \
        "https://traffic.libsyn.com/cwt/a.mp3"
    assert C.unwrap_tracking("https://dts.podtrac.com/redirect.mp3/pdst.fm/e/traffic.megaphone.fm/X.mp3") == \
        "https://traffic.megaphone.fm/X.mp3"
    assert C.unwrap_tracking("https://traffic.libsyn.com/a.mp3") == "https://traffic.libsyn.com/a.mp3"


VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000 align:start position:0%
welcome<00:00:00.500><c> to</c><c> the</c><c> show</c>

00:00:02.000 --> 00:00:02.010
welcome to the show

00:00:02.010 --> 00:00:05.000
welcome to the show
today<00:00:03.000><c> we</c><c> talk</c><c> gaps</c>

00:02:05.000 --> 00:02:07.000
>> so the opening range &amp; VWAP
"""


def test_vtt_dedupes_rollup_captions():
    segs = C.vtt_to_segments(VTT)
    assert [t for _, t in segs] == ["welcome to the show", "today we talk gaps", ">> so the opening range & VWAP"]
    txt = C.segments_to_text(segs)
    assert txt.startswith("[00:00:00] welcome to the show today we talk gaps") and "\n\n[00:02:05] >> so" in txt


def test_list_youtube_parses_and_reports_block():
    def run(cmd, timeout=600):
        url = cmd[-1]
        if url.endswith("/videos") and "@chatwithtraders" in url:
            return 0, json.dumps({"entries": [{"id": "AbCdEfGhIjK", "title": "Ep 250 Jane Doe", "duration": 3900},
                                              {"id": "ZZZZZZZZZZZ", "title": "short clip", "duration": 50}]}), ""
        return 1, "", "ERROR: [youtube] Sign in to confirm you're not a bot"
    vids, rep = C.list_youtube(run)
    assert len(vids) == 2 and rep[0]["videos"] == 2
    assert any(r.get("error", "").startswith("BLOCKED") for r in rep)


def test_match_youtube_number_notes_and_title():
    eps = [{"key": "ep001", "number": 1, "title": "Ep 1: Trend following with Alice Brown", "guest": "Alice Brown",
            "duration_sec": 3600, "youtube_ids": []},
           {"key": "ep002", "number": 2, "title": "Ep 2: Scalping futures", "guest": "", "duration_sec": 3600,
            "youtube_ids": ["NotesVid123"]},
           {"key": "x20200101-x", "number": None, "title": "Special: Risk management roundtable", "guest": "",
            "duration_sec": 4000, "youtube_ids": []}]
    vids = [{"id": "Vid00000001", "title": "Alice Brown on trend following | Ep 1", "duration": 3650},
            {"id": "Vid00000003", "title": "Risk Management Roundtable (special)", "duration": 4100},
            {"id": "Clip0000001", "title": "Alice Brown on trend following clip", "duration": 120}]
    C.match_youtube(eps, vids)
    assert eps[0]["youtube_id"] == "Vid00000001" and eps[0]["youtube_match"] == "number"
    assert eps[1]["youtube_id"] == "NotesVid123"
    assert eps[2]["youtube_id"] == "Vid00000003" and eps[2]["youtube_match"].startswith("title")


def test_captions_ytdlp_prefers_manual_and_detects_block(tmp_path):
    vid = "AbCdEfGhIjK"

    def run_ok(cmd, timeout=600):
        (tmp_path / f"{vid}.en-orig.vtt").write_text(VTT)
        (tmp_path / f"{vid}.en-US.vtt").write_text(VTT.replace("welcome", "hello"))
        return 0, json.dumps({"id": vid, "subtitles": {"en-US": []}, "automatic_captions": {"en-orig": []}}), ""
    segs, kind = C.captions_ytdlp(vid, str(tmp_path), run_ok)
    assert kind == "youtube-manual" and segs[0][1] == "hello to the show"

    def run_block(cmd, timeout=600):
        return 1, "", "ERROR: [youtube] AbCdEfGhIjK: Sign in to confirm you’re not a bot."
    with pytest.raises(C.Blocked):
        C.captions_ytdlp(vid, str(tmp_path / "none"), run_block)

    def run_none(cmd, timeout=600):
        return 0, json.dumps({"id": vid}), ""
    (tmp_path / "empty").mkdir()
    with pytest.raises(C.NoCaptions):
        C.captions_ytdlp(vid, str(tmp_path / "empty"), run_none)


def test_site_transcript_from_link_and_page():
    words = " ".join(["word"] * 1600)
    ep = C.parse_rss(RSS)[0]
    page = f"<html><nav>menu</nav><h2>Show notes</h2><p>x</p><h2>Transcript</h2><p>{words}</p></html>"
    body, url = C.site_transcript(ep, lambda u, binary=False: page)
    assert url.endswith("/transcripts/250") and len(body.split()) == 1600
    ep2 = dict(ep, links=[])
    body, url = C.site_transcript(ep2, lambda u, binary=False: page)
    assert url == ep["link"]
    body, why = C.site_transcript(ep2, lambda u, binary=False: "<p>no transcript here</p>")
    assert body is None and "no transcript section" in why


def test_episode_spec_and_plan():
    eps = [{"key": f"ep{i:03d}", "number": i, "duration_sec": 600 * i} for i in range(1, 11)]
    eps.append({"key": "x20200101-bonus", "number": None, "duration_sec": 100})
    pred = C.parse_episode_spec("1-3, 7, 9-, x20200101-bonus")
    assert [e["key"] for e in eps if pred(e)] == ["ep001", "ep002", "ep003", "ep007", "ep009", "ep010",
                                                  "x20200101-bonus"]
    prev = {"ep010": {"status": "done"}, "ep009": {"status": "failed"}}
    plan = C.plan_shards(eps, 3, prev)
    keys = sum(plan["shards"], [])
    assert plan["todo"] == 10 and "ep010" not in keys and "ep009" in keys and len(plan["shards"]) == 3
    assert max(plan["load_sec"]) - min(plan["load_sec"]) <= 6000
    assert C.plan_shards(eps, 20, prev, "1-2")["shards"].__len__() == 2
    assert "ep010" in sum(C.plan_shards(eps, 2, prev, force=True)["shards"], [])
    assert C.plan_shards(eps, 4, {e["key"]: {"status": "done"} for e in eps})["todo"] == 0


def test_transcript_roundtrip_and_owner_files(tmp_path):
    ep = C.parse_rss(RSS)[0]
    ep["youtube_id"] = "AbCdEfGhIjK"
    n = C.write_transcript(tmp_path / "ep250.txt", ep, "[00:00:00] hello there trader", "youtube-auto", "u")
    r = C.read_transcript(tmp_path / "ep250.txt")
    assert n == 4 and r["meta"]["episode"] == 250 and r["meta"]["source"] == "youtube-auto"
    assert r["text"] == "[00:00:00] hello there trader" and "Jane trades" in r["notes"]
    (tmp_path / "ep007.txt").write_text("Episode: 7\nTitle: T\nSource: gemini\n\nJane: I buy the ORB.\n")
    r = C.read_transcript(tmp_path / "ep007.txt")
    assert r["meta"]["key"] == "ep007" and r["meta"]["source"] == "gemini" and r["text"] == "Jane: I buy the ORB."
    (tmp_path / "Ep 12 - Someone.txt").write_text("Host: welcome. Guest: thanks.\n")
    r = C.read_transcript(tmp_path / "Ep 12 - Someone.txt")
    assert r["meta"]["episode"] == 12 and r["meta"]["source"] == "owner" and r["text"].startswith("Host:")


def test_merge_status_rules():
    prev = {"a": {"status": "done", "source": "whisper:base.en"}, "b": {"status": "done", "source": "site"},
            "c": {"status": "failed"}}
    new = {"a": {"status": "done", "source": "youtube-manual"}, "b": {"status": "failed"},
           "c": {"status": "deferred"}, "d": {"status": "done", "source": "youtube-auto"}}
    m, take = C.merge_status(prev, new)
    assert m["a"]["source"] == "youtube-manual" and m["b"]["status"] == "done" and m["c"]["status"] == "deferred"
    assert take == {"a", "d"}


def test_cmd_merge_end_to_end(tmp_path):
    lst, shards, dest = tmp_path / "list", tmp_path / "shards", tmp_path / "cwt"
    lst.mkdir()
    eps = C.parse_rss(RSS)
    (lst / "episodes.json").write_text(json.dumps(eps))
    C.write_transcript(shards / "transcripts" / "ep250.txt", eps[0], "text " * 400, "whisper:base.en")
    (shards / "status_shard000.json").write_text(json.dumps(
        {"ep250": {"status": "done", "source": "whisper:base.en", "file": "transcripts/ep250.txt"},
         "ep042": {"status": "failed", "reason": "whisper: no audio"}}))
    (dest / "transcripts").mkdir(parents=True)
    (dest / "transcripts" / "old.txt").write_text("keep me")
    assert C.main(["merge", "--dest", str(dest), "--shards", str(shards), "--list-dir", str(lst)]) == 0
    assert (dest / "transcripts" / "ep250.txt").exists() and (dest / "transcripts" / "old.txt").exists()
    idx = (dest / "index.csv").read_text()
    assert "ep250" in idx and "done" in idx and "ep042" in idx
    # a run in which nothing finished fails loudly
    (shards / "status_shard000.json").write_text(json.dumps({"ep042": {"status": "failed", "reason": "x"}}))
    assert C.main(["merge", "--dest", str(dest), "--shards", str(shards), "--list-dir", str(lst)]) == 2
    assert json.loads((dest / "status.json").read_text())["ep250"]["status"] == "done"


def test_cmd_work_fallbacks_breaker_and_budget(tmp_path, monkeypatch):
    eps = [{"key": f"ep{i:03d}", "number": i, "title": f"Ep {i}", "guest": "", "date": "", "duration_sec": 3600,
            "audio_url": f"https://a/{i}.mp3", "link": "", "links": [], "notes": "", "youtube_id": f"Vid{i:08d}"}
           for i in range(1, 6)]
    lst = tmp_path / "list"
    lst.mkdir()
    (lst / "episodes.json").write_text(json.dumps(eps))
    (lst / "plan.json").write_text(json.dumps({"shards": [[e["key"] for e in eps]]}))
    calls = {"yt": 0, "whisper": 0}

    def blocked(*a, **k):
        calls["yt"] += 1
        raise C.Blocked("Sign in to confirm you're not a bot")
    monkeypatch.setattr(C, "captions_ytdlp", blocked)
    monkeypatch.setattr(C, "captions_api", blocked)
    monkeypatch.setattr(C, "http_get", lambda *a, **k: (_ for _ in ()).throw(OSError("403")))
    monkeypatch.setattr(C, "download", lambda url, path: Path(path).write_bytes(b"x") and url)

    def fake_whisper(path, model, beam=1):
        calls["whisper"] += 1
        return [(0.0, "word " * 400)], 3600.0
    monkeypatch.setattr(C, "whisper_transcribe", fake_whisper)
    out = tmp_path / "out"
    rc = C.main(["work", "--list-dir", str(lst), "--shard", "0", "--mode", "all", "--out", str(out),
                 "--yt-sleep", "0"])
    st = json.loads((out / "status_shard000.json").read_text())
    assert rc == 0 and all(r["status"] == "done" and r["source"] == "whisper:base.en" for r in st.values())
    assert calls["yt"] == 2 * C.BLOCK_LIMIT and calls["whisper"] == 5      # breaker stopped YouTube after 3 eps
    assert "BLOCKING" not in st["ep005"]["attempts"][-1] and "skipped" in st["ep005"]["attempts"][-1]
    # captions-only run with YouTube blocked: every episode fails with a reason, the shard exits non-zero
    out2 = tmp_path / "out2"
    rc = C.main(["work", "--list-dir", str(lst), "--shard", "0", "--mode", "captions", "--out", str(out2),
                 "--yt-sleep", "0"])
    st = json.loads((out2 / "status_shard000.json").read_text())
    assert rc == 3 and all(r["status"] == "failed" and r["reason"] for r in st.values())
    # time budget: a 1-hour episode at the assumed base.en speed (~12 min) does not fit into 5 minutes -> deferred, not failed
    out3 = tmp_path / "out3"
    C.main(["work", "--list-dir", str(lst), "--shard", "0", "--mode", "whisper", "--out", str(out3),
            "--time-budget", "5"])
    st = json.loads((out3 / "status_shard000.json").read_text())
    assert all(r["status"] == "deferred" for r in st.values())


def test_owner_file_starting_with_guest_speaker_label_is_not_a_header(tmp_path):
    (tmp_path / "ep009.txt").write_text("Guest: Thanks for having me.\n\nAaron: Sure.\n")
    r = C.read_transcript(tmp_path / "ep009.txt")
    assert r["meta"]["episode"] == 9 and r["text"].startswith("Guest: Thanks")
