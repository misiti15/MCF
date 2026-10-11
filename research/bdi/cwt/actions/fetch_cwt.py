"""Collect "Chat With Traders" episode transcripts (run on GitHub Actions; see .github/workflows/cwt-transcripts.yml -
the Claude container's proxy blocks youtube.com and chatwithtraders.com). Research input for the CWT setup study
(research/bdi/cwt/README.md). Educational only - not financial advice.

Subcommands
  list   Build the episode list and the work plan.
         Podcast RSS: every feed that answers is parsed and merged (iTunes search API -> feedUrl first, then the known
         candidates in FEED_CANDIDATES, then --feed-url). Last resort: iTunes lookup entity=podcastEpisode (<= 200
         newest episodes, warned). Per episode: number, title, guest (best effort), date, duration, audio URL, page
         link, show-notes text and links.
         YouTube: `yt-dlp --flat-playlist -J` on the channel tabs in YT_CHANNELS (+ YouTube links in the show notes),
         matched to episodes by episode number, then title/guest similarity (+ duration check). A blocked listing is a
         warning, not an error (captions then fall back to whisper in mode=all).
         Writes episodes.json, youtube_videos.json, plan.json (LPT-balanced shards of the episodes still to do).
  work   Process one shard of plan.json. Per episode, in order (mode=all): (a) a transcript linked from the show notes
         or the episode page, (b) YouTube captions (yt-dlp, then youtube-transcript-api), (c) faster-whisper on the
         podcast MP3 (int8 on CPU). A circuit breaker turns captions off for the shard after BLOCK_LIMIT consecutive
         bot-checks / 429s. Every finished episode is written immediately (checkpoint); the shard stops starting new
         episodes when the time budget would be exceeded and marks the rest "deferred" (a rerun picks them up).
  merge  Merge shard outputs into the published cwt/ folder: transcripts/<key>.txt, status.json (a new failure never
         overwrites an earlier "done"), index.csv / index.json. Exit 2 when a non-list run finished no episode.

Transcript file format (also what the owner's fallback files may look like; see read_transcript):
  header lines "Field: value" up to the first blank line, then "== SHOW NOTES ==" (optional) and "== TRANSCRIPT ==".
"""
from __future__ import annotations

import argparse
import csv
import difflib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus

DISCLAIMER = "Educational only - not financial advice."
UA = "Mozilla/5.0 (X11; Linux x86_64) MCF-research/1.0 (podcast transcript study)"
ITUNES_SEARCH = "https://itunes.apple.com/search?term={q}&entity=podcast&limit=25"
ITUNES_EPISODES = "https://itunes.apple.com/lookup?id={id}&entity=podcastEpisode&limit=200"
FEED_CANDIDATES = [  # tried in addition to whatever iTunes reports; dead ones just log a warning
    "https://chatwithtraders.com/feed/podcast/",
    "https://chatwithtraders.libsyn.com/rss",
    "https://feeds.megaphone.fm/chatwithtraders",
    "https://feeds.simplecast.com/chatwithtraders",
    "https://anchor.fm/s/chatwithtraders/podcast/rss",
]
YT_CHANNELS = [
    "https://www.youtube.com/@chatwithtraders/videos",
    "https://www.youtube.com/@chatwithtraders/streams",
    "https://www.youtube.com/@ChatWithTradersPodcast/videos",
    "https://www.youtube.com/c/ChatWithTraders/videos",
]
NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd", "content": "http://purl.org/rss/1.0/modules/content/"}
BOT_MARKERS = ("sign in to confirm", "not a bot", "http error 429", "too many requests", "requestblocked",
               "ipblocked", "rate-limit", "rate limit", "try again later", "consent.youtube")
BLOCK_LIMIT = 3            # consecutive YouTube blocks before captions are switched off for the shard
MIN_VIDEO_SEC = 15 * 60    # shorter videos are clips/shorts, never matched to a full episode
MIN_WORDS = 1500           # a "transcript" shorter than this is treated as a stub
# Assumed whisper speed (x realtime) on a 2-vCPU GitHub runner, int8, beam 1, VAD on. Refine from the smoke test:
# the work step records the measured factor ("rtf") per episode in status.json.
RTF_GUESS = {"tiny.en": 12.0, "base.en": 6.0, "small.en": 2.5, "medium.en": 0.8}
SOURCE_RANK = {"site": 5, "gemini": 4, "youtube-manual": 4, "whisper": 3, "youtube-auto": 2}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ----------------------------------------------------------------------------------------------------------- network
def http_get(url, binary=False, timeout=60, tries=3):
    import requests  # imported lazily so the parsing helpers work without it
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise OSError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r.content if binary else r.text
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise OSError(f"GET {url} failed: {last}")


def download(url, path, timeout=120):
    """Stream an enclosure to disk; if the tracking-prefixed URL fails, retry the unwrapped host URL."""
    import requests
    errors = []
    for u in dict.fromkeys([url, unwrap_tracking(url)]):
        try:
            with requests.get(u, headers={"User-Agent": UA}, timeout=timeout, stream=True) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if os.path.getsize(path) > 100_000:
                return u
            errors.append(f"{u}: tiny file")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{u}: {e}")
    raise OSError("; ".join(errors))


_TRACKERS = [r"dts\.podtrac\.com/redirect\.[a-z0-9]+/", r"www\.podtrac\.com/pts/redirect\.[a-z0-9]+/",
             r"chtbl\.com/track/[^/]+/", r"chrt\.fm/track/[^/]+/", r"pdst\.fm/e/", r"op3\.dev/e/(?:[^/]+/)?",
             r"pfx\.vpixl\.com/[^/]+/", r"arttrk\.com/p/[^/]+/", r"mgln\.ai/e/[^/]+/", r"prfx\.byspotify\.com/e/",
             r"verifi\.podscribe\.com/rss/p/", r"pscrb\.fm/rss/p/", r"claritaspod\.com/measure/"]


def unwrap_tracking(url):
    """https://chtbl.com/track/X/traffic.libsyn.com/a.mp3 -> https://traffic.libsyn.com/a.mp3 (repeatedly)."""
    u = url
    for _ in range(6):
        m = re.match(r"^(https?://)(?:" + "|".join(_TRACKERS) + r")(.+)$", u, re.I)
        if not m:
            break
        rest = m.group(2)
        u = rest if re.match(r"^https?://", rest) else "https://" + rest
    return u


# ------------------------------------------------------------------------------------------------------ text helpers
class _Html2Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article",
             "blockquote", "pre", "hr"}
    SKIP = {"script", "style", "noscript", "nav", "footer", "header", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self._href, self._atext, self._skip = [], [], None, [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "a":
            self._href, self._atext = dict(attrs).get("href"), []

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "a" and self._href:
            self.links.append({"href": self._href, "text": " ".join("".join(self._atext).split())})
            self._href = None

    def handle_data(self, data):
        if self._skip:
            return
        self.parts.append(data)
        if self._href is not None:
            self._atext.append(data)


def html_to_text(s):
    """-> (plain text with paragraph breaks, [{'href','text'}])."""
    p = _Html2Text()
    p.feed(s or "")
    p.close()
    lines = [" ".join(ln.split()) for ln in "".join(p.parts).split("\n")]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return text, p.links


def norm(s):
    s = html.unescape(s or "").lower()
    s = re.sub(r"chat\s*with\s*traders|podcast|episode|\bep\b\.?|#\d+", " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def slug(s, n=40):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (s or "").lower())).strip("-")[:n].strip("-")


def parse_number(title, itunes_episode=None):
    """Episode number from <itunes:episode> or the title ("Ep 42: ...", "042 | ...", "... (Ep. 42)", "#42")."""
    if itunes_episode and str(itunes_episode).strip().isdigit():
        return int(str(itunes_episode).strip())
    t = html.unescape(title or "")
    m = re.match(r"^\s*(?:ep(?:isode)?\.?\s*#?|#)?\s*(\d{1,3})\s*(?:[:|.)\]]|\s[-–—]\s)", t, re.I)
    if not m:
        m = re.search(r"\b(?:ep(?:isode)?\.?\s*#?\s*|#)(\d{1,3})\b", t, re.I)
    return int(m.group(1)) if m else None


_NOT_NAME = {"the", "how", "why", "what", "trading", "trader", "traders", "market", "markets", "with", "and", "of",
             "in", "a", "an", "to", "on", "for", "chat", "podcast", "episode", "bonus", "special", "live", "q&a"}


def _namey(s):
    w = s.strip().split()
    return (2 <= len(w) <= 4 and len(s) <= 40 and not re.search(r"\d", s)
            and all(x[:1].isupper() for x in w if x.lower() not in {"de", "van", "von", "da", "la"})
            and not any(x.lower() in _NOT_NAME for x in w))


def parse_guest(title):
    t = html.unescape(title or "")
    t = re.sub(r"^\s*(?:ep(?:isode)?\.?\s*#?|#)?\s*\d{1,3}\s*(?:[:|.)\]]|\s[-–—]\s)\s*", "", t, flags=re.I)
    t = re.sub(r"\s*[(\[]\s*(?:ep(?:isode)?\.?\s*#?)\s*\d+\s*[)\]]\s*$", "", t, flags=re.I)
    m = re.search(r"(?:\bw/|\bwith\b|\bft\.?|\bfeat\.?|\bfeaturing\b)\s+([A-Z][\w.'’-]+(?:\s+[A-Z][\w.'’-]+){0,3})\s*$", t)
    if m and _namey(m.group(1)):
        return m.group(1).strip()
    parts = [p.strip() for p in re.split(r"\s+[|–—-]\s+|:\s+|,\s+", t) if p.strip()]
    for p in parts[:1] + parts[-1:]:
        if _namey(p):
            return p
    return ""


def parse_duration(s):
    s = (s or "").strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    try:
        n = [int(x) for x in s.split(":")]
    except ValueError:
        return None
    sec = 0
    for x in n:
        sec = sec * 60 + x
    return sec


def episode_key(ep):
    if ep.get("number") is not None:
        return f"ep{ep['number']:03d}"
    return f"x{(ep.get('date') or '00000000').replace('-', '')}-{slug(ep.get('title'), 30)}"


YT_ID = re.compile(r"(?:youtube\.com/(?:watch\?(?:[^ \"'<>]*&)?v=|embed/|live/|shorts/)|youtu\.be/)([\w-]{11})")


# -------------------------------------------------------------------------------------------------------- episodes
def parse_rss(xml_text, feed_url=""):
    root = ET.fromstring(xml_text.encode() if isinstance(xml_text, str) else xml_text)
    out = []
    for it in root.iter("item"):
        def tx(tag):
            el = it.find(tag, NS)
            return (el.text or "").strip() if el is not None and el.text else ""
        title = tx("title") or tx("itunes:title")
        notes_html = tx("content:encoded") or tx("description") or tx("itunes:summary")
        notes, links = html_to_text(notes_html)
        enc = it.find("enclosure")
        date = ""
        if tx("pubDate"):
            try:
                date = parsedate_to_datetime(tx("pubDate")).date().isoformat()
            except (TypeError, ValueError):
                date = ""
        ep = {"number": parse_number(title, tx("itunes:episode")), "title": html.unescape(title),
              "guest": parse_guest(title), "date": date, "duration_sec": parse_duration(tx("itunes:duration")),
              "audio_url": enc.get("url", "") if enc is not None else "", "link": tx("link"), "guid": tx("guid"),
              "episode_type": tx("itunes:episodeType") or "full", "notes": notes,
              "links": [lk for lk in links if lk["href"].startswith("http")],
              "youtube_ids": list(dict.fromkeys(YT_ID.findall(notes_html))), "feeds": [feed_url] if feed_url else []}
        if ep["episode_type"] == "trailer" and not ep["audio_url"]:
            continue
        ep["key"] = episode_key(ep)
        out.append(ep)
    return out


def merge_episodes(lists):
    """Union of episodes from several feeds, keyed by episode key; the richer record wins, feeds are concatenated."""
    by = {}
    for lst in lists:
        for ep in lst:
            k = ep["key"]
            if k not in by:
                by[k] = dict(ep)
                continue
            cur = by[k]
            score = lambda e: (bool(e.get("audio_url")), len(e.get("notes") or ""))  # noqa: E731
            best = dict(ep) if score(ep) > score(cur) else cur
            best["feeds"] = list(dict.fromkeys(cur.get("feeds", []) + ep.get("feeds", [])))
            best["youtube_ids"] = list(dict.fromkeys(cur.get("youtube_ids", []) + ep.get("youtube_ids", [])))
            for f in ("duration_sec", "link", "guest", "audio_url"):
                best[f] = best.get(f) or cur.get(f) or ep.get(f)
            by[k] = best
    return sorted(by.values(), key=lambda e: (e.get("number") is None, e.get("number") or 0, e.get("date") or ""))


def discover_feeds(get, term="chat with traders"):
    """iTunes search -> [(feedUrl, collectionId)] for collections named like Chat With Traders, most episodes first."""
    try:
        data = json.loads(get(ITUNES_SEARCH.format(q=quote_plus(term))))
    except Exception as e:  # noqa: BLE001
        log("WARN iTunes search failed:", e)
        return []
    hits = [r for r in data.get("results", []) if "chat with traders" in (r.get("collectionName") or "").lower()]
    hits.sort(key=lambda r: -(r.get("trackCount") or 0))
    return [(r.get("feedUrl"), r.get("collectionId")) for r in hits if r.get("feedUrl") or r.get("collectionId")]


def itunes_episodes(get, collection_id):
    data = json.loads(get(ITUNES_EPISODES.format(id=collection_id)))
    out = []
    for r in data.get("results", []):
        if r.get("wrapperType") != "podcastEpisode" and r.get("kind") != "podcast-episode":
            continue
        title = r.get("trackName", "")
        notes, links = html_to_text(r.get("description") or r.get("shortDescription") or "")
        ep = {"number": parse_number(title, r.get("episodeNumber")), "title": title, "guest": parse_guest(title),
              "date": (r.get("releaseDate") or "")[:10],
              "duration_sec": int(r["trackTimeMillis"] / 1000) if r.get("trackTimeMillis") else None,
              "audio_url": r.get("episodeUrl", ""), "link": r.get("trackViewUrl", ""), "guid": r.get("episodeGuid", ""),
              "episode_type": "full", "notes": notes, "links": links, "youtube_ids": [], "feeds": ["itunes-lookup"]}
        ep["key"] = episode_key(ep)
        out.append(ep)
    return out


def build_episode_list(get, extra_feeds=()):
    found, report, ids = [], [], []
    disc = discover_feeds(get)
    urls = [u for u, _ in disc if u] + list(FEED_CANDIDATES) + [u for u in extra_feeds if u]
    for url in dict.fromkeys(urls):
        try:
            eps = parse_rss(get(url), url)
            report.append({"feed": url, "episodes": len(eps)})
            log(f"feed {url}: {len(eps)} episodes")
            if eps:
                found.append(eps)
        except Exception as e:  # noqa: BLE001
            report.append({"feed": url, "error": str(e)[:200]})
            log(f"WARN feed {url}: {e}")
    ids = [cid for _, cid in disc if cid]
    if not found and ids:
        log("WARN no RSS feed answered; falling back to the iTunes episode lookup (only the newest <= 200 episodes)")
        try:
            eps = itunes_episodes(get, ids[0])
            report.append({"feed": "itunes-lookup", "episodes": len(eps)})
            found.append(eps)
        except Exception as e:  # noqa: BLE001
            report.append({"feed": "itunes-lookup", "error": str(e)[:200]})
    return merge_episodes(found), report


# --------------------------------------------------------------------------------------------------------- youtube
class Blocked(Exception):
    """YouTube refused the request (bot check / 429)."""


class NoCaptions(Exception):
    pass


def _is_blocked(msg):
    m = (msg or "").lower()
    return any(b in m for b in BOT_MARKERS)


def run_cmd(cmd, timeout=600):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def list_youtube(run=run_cmd, channels=None):
    """-> (videos [{id,title,duration}], report). Raises nothing; a blocked channel is reported."""
    vids, report = {}, []
    for url in channels or YT_CHANNELS:
        try:
            rc, out, err = run(["yt-dlp", "--flat-playlist", "-J", "--no-warnings", url])
        except Exception as e:  # noqa: BLE001
            report.append({"channel": url, "error": str(e)[:200]})
            continue
        if rc != 0:
            report.append({"channel": url, "error": ("BLOCKED: " if _is_blocked(err) else "") + err.strip()[-300:]})
            log(f"WARN youtube {url}: rc={rc} {err.strip()[-200:]}")
            continue
        n = 0
        for e in json.loads(out).get("entries") or []:
            for sub in (e.get("entries") or [e]):   # a channel root returns tabs with nested entries
                if sub.get("id") and len(sub["id"]) == 11:
                    vids.setdefault(sub["id"], {"id": sub["id"], "title": sub.get("title") or "",
                                                "duration": sub.get("duration")})
                    n += 1
        report.append({"channel": url, "videos": n})
        log(f"youtube {url}: {n} videos")
    return list(vids.values()), report


def match_youtube(episodes, videos):
    """Sets ep['youtube_id'] / ep['youtube_match']. Order: show-notes link, episode number, title/guest similarity."""
    long_v = [v for v in videos if not v.get("duration") or v["duration"] >= MIN_VIDEO_SEC]
    by_num = {}
    for v in long_v:
        n = parse_number(v["title"])
        if n is not None:
            by_num.setdefault(n, v)
    used = set()
    for ep in episodes:
        ep["youtube_id"], ep["youtube_match"] = None, None
        if ep.get("youtube_ids"):
            ep["youtube_id"], ep["youtube_match"] = ep["youtube_ids"][0], "show-notes"
        elif ep.get("number") is not None and ep["number"] in by_num and by_num[ep["number"]]["id"] not in used:
            ep["youtube_id"], ep["youtube_match"] = by_num[ep["number"]]["id"], "number"
        if ep["youtube_id"]:
            used.add(ep["youtube_id"])
    cands = []
    for ep in episodes:
        if ep["youtube_id"]:
            continue
        et, g = norm(ep["title"]), norm(ep.get("guest"))
        for v in long_v:
            if v["id"] in used:
                continue
            n = parse_number(v["title"])
            if n is not None and ep.get("number") is not None and n != ep["number"]:
                continue
            vt = norm(v["title"])
            s = difflib.SequenceMatcher(None, et, vt).ratio()
            if g and g in vt:
                s = max(s, 0.75)
            d1, d2 = ep.get("duration_sec"), v.get("duration")
            if d1 and d2 and abs(d1 - d2) > 0.2 * max(d1, d2):
                s -= 0.3
            if s >= 0.6:
                cands.append((s, ep["key"], v["id"]))
    eps = {e["key"]: e for e in episodes}
    for s, k, vid in sorted(cands, reverse=True):
        if eps[k]["youtube_id"] or vid in used:
            continue
        eps[k]["youtube_id"], eps[k]["youtube_match"] = vid, f"title:{s:.2f}"
        used.add(vid)
    return episodes


def _ts(t):
    h, rest = (t.split(":", 1) if t.count(":") == 2 else ("0", t))
    m, s = rest.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))


def vtt_to_segments(vtt):
    """WebVTT -> [(start_sec, text)], with YouTube auto-caption roll-up duplicates removed."""
    segs, recent = [], []
    for block in re.split(r"\n\s*\n", vtt.replace("\r", "")):
        lines = block.strip().split("\n")
        idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if idx is None:
            continue
        start = _ts(lines[idx].split("-->")[0].strip().split(" ")[0])
        for ln in lines[idx + 1:]:
            t = " ".join(html.unescape(re.sub(r"<[^>]+>", "", ln)).split())
            if not t or t in recent:
                continue
            segs.append((start, t))
            recent = (recent + [t])[-3:]
    return segs


def segments_to_text(segs, para_sec=120):
    out, cur, t0 = [], [], None
    for start, t in segs:
        if t0 is None:
            t0 = start
        if start - t0 >= para_sec and cur:
            out.append(f"[{_hms(t0)}] " + " ".join(cur))
            cur, t0 = [], start
        cur.append(t.strip())
    if cur:
        out.append(f"[{_hms(t0)}] " + " ".join(cur))
    return "\n\n".join(out)


def _hms(s):
    s = int(s or 0)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def captions_ytdlp(vid, tmpdir, run=run_cmd):
    """-> (segments, 'youtube-manual'|'youtube-auto'). Raises Blocked / NoCaptions."""
    cmd = ["yt-dlp", "--skip-download", "--no-simulate", "-j", "--no-warnings", "--write-subs", "--write-auto-subs",
           "--sub-langs", "en.*,en,-live_chat", "--sub-format", "vtt", "-o", f"{tmpdir}/%(id)s.%(ext)s",
           f"https://www.youtube.com/watch?v={vid}"]
    rc, out, err = run(cmd)
    if rc != 0 or (_is_blocked(err) and not out.strip()):
        if _is_blocked(err):
            raise Blocked(err.strip()[-200:])
        raise NoCaptions(f"yt-dlp rc={rc}: {err.strip()[-200:]}")
    try:
        info = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        info = {}
    manual = set((info.get("subtitles") or {}).keys())
    files = sorted(Path(tmpdir).glob(f"{vid}*.vtt"))
    if not files:
        raise NoCaptions("no English subtitles")

    def lang(p):
        return p.name[len(vid) + 1:-4]
    order = sorted(files, key=lambda p: (lang(p) not in manual, lang(p) != "en-orig", lang(p) != "en", lang(p)))
    best = order[0]
    segs = vtt_to_segments(best.read_text(encoding="utf-8", errors="replace"))
    if not segs:
        raise NoCaptions("empty subtitle file")
    return segs, "youtube-manual" if lang(best) in manual else "youtube-auto"


def captions_api(vid):
    """youtube-transcript-api (v1.x .fetch or legacy get_transcript). Raises Blocked / NoCaptions."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as e:
        raise NoCaptions("youtube-transcript-api not installed") from e
    langs = ["en", "en-US", "en-GB"]
    try:
        api = YouTubeTranscriptApi()
        if hasattr(api, "fetch"):
            ft = api.fetch(vid, languages=langs)
            segs = [(s.start, s.text) for s in ft]
            kind = "youtube-auto" if getattr(ft, "is_generated", True) else "youtube-manual"
        else:
            segs = [(d["start"], d["text"]) for d in YouTubeTranscriptApi.get_transcript(vid, languages=langs)]
            kind = "youtube-auto"
    except Exception as e:  # noqa: BLE001
        name = type(e).__name__
        if _is_blocked(name) or _is_blocked(str(e)) or name in ("RequestBlocked", "IpBlocked", "TooManyRequests"):
            raise Blocked(f"{name}: {str(e)[:150]}") from e
        raise NoCaptions(f"{name}: {str(e)[:150]}") from e
    segs = [(st, " ".join(html.unescape(t).split())) for st, t in segs if t and t.strip()]
    if not segs:
        raise NoCaptions("empty transcript")
    return segs, kind


# ------------------------------------------------------------------------------------------------- site transcripts
def extract_transcript_from_page(page_html):
    """Text after a 'Transcript' heading on an episode page (or the whole page if it is a transcript page)."""
    text, _ = html_to_text(page_html)
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(?:full\s+|episode\s+)?transcript(?:ion)?\s*:?\s*$", ln, re.I):
            body = "\n".join(lines[i + 1:]).strip()
            if len(body.split()) >= MIN_WORDS:
                return body
    return None


def site_transcript(ep, get):
    """-> (text, url) or (None, reason). Looks at show-notes links mentioning 'transcript', then the episode page."""
    links = [lk["href"] for lk in ep.get("links", []) if "transcript" in (lk["href"] + " " + lk["text"]).lower()]
    tried = []
    for url in links:
        try:
            if url.lower().split("?")[0].endswith(".pdf"):
                import io
                from pypdf import PdfReader
                body = "\n".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(get(url, binary=True))).pages)
            elif url.lower().split("?")[0].endswith(".txt"):
                body = get(url)
            else:
                page = get(url)
                body = extract_transcript_from_page(page) or html_to_text(page)[0]
            if body and len(body.split()) >= MIN_WORDS:
                return body.strip(), url
            tried.append(f"{url}: too short")
        except Exception as e:  # noqa: BLE001
            tried.append(f"{url}: {str(e)[:80]}")
    if ep.get("link"):
        try:
            body = extract_transcript_from_page(get(ep["link"]))
            if body:
                return body, ep["link"]
            tried.append("episode page: no transcript section")
        except Exception as e:  # noqa: BLE001
            tried.append(f"episode page: {str(e)[:80]}")
    return None, "; ".join(tried) or "no transcript link"


# ---------------------------------------------------------------------------------------------------- output files
HEADER_FIELDS = ["Episode", "Key", "Title", "Guest", "Date", "Source", "Source-URL", "Audio-URL", "YouTube",
                 "Duration-sec", "Words", "Fetched"]


def write_transcript(path, ep, body, source, source_url=""):
    h = {"Episode": ep.get("number") if ep.get("number") is not None else "", "Key": ep["key"],
         "Title": ep.get("title", ""), "Guest": ep.get("guest", ""), "Date": ep.get("date", ""), "Source": source,
         "Source-URL": source_url, "Audio-URL": ep.get("audio_url", ""),
         "YouTube": f"https://youtu.be/{ep['youtube_id']}" if ep.get("youtube_id") else "",
         "Duration-sec": ep.get("duration_sec") or "", "Words": len(body.split()),
         "Fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    txt = [f"# Chat With Traders transcript (research input). {DISCLAIMER}"]
    txt += [f"{k}: {' '.join(str(h[k]).split())}" for k in HEADER_FIELDS]
    txt += ["", "== SHOW NOTES ==", (ep.get("notes") or "").strip(), "", "== TRANSCRIPT ==", body.strip(), ""]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(txt), encoding="utf-8")
    return h["Words"]


def read_transcript(path):
    """Read a published transcript or an owner-supplied one (header optional). -> dict with 'meta' and 'text'.
    Accepted names: ep042.txt / 042.txt / ep42.txt / "Ep 42 - Guest.txt" (episode number taken from the name)."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8", errors="replace").lstrip("﻿")
    lines = raw.split("\n")
    meta, i = {}, 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    j = i
    while j < len(lines) and re.match(r"^[A-Za-z][\w-]{1,20}:\s", lines[j]):
        k, v = lines[j].split(":", 1)
        meta[k.strip().lower()] = v.strip()
        j += 1
    if meta and (j >= len(lines) or not lines[j].strip()):
        body = "\n".join(lines[j:])
    else:
        meta, body = {}, raw
    notes = ""
    if "== TRANSCRIPT ==" in body:
        pre, body = body.split("== TRANSCRIPT ==", 1)
        notes = pre.split("== SHOW NOTES ==", 1)[-1].strip() if "== SHOW NOTES ==" in pre else ""
    num = meta.get("episode")
    if not num:
        m = re.match(r"^(?:ep(?:isode)?[ ._-]*)?0*(\d{1,3})(?:\D|$)", p.stem, re.I)
        num = m.group(1) if m else ""
    meta["episode"] = int(num) if str(num).isdigit() else None
    meta.setdefault("key", f"ep{meta['episode']:03d}" if meta["episode"] is not None else p.stem)
    meta.setdefault("source", "owner")
    return {"meta": meta, "notes": notes, "text": body.strip(), "path": str(p)}


# ----------------------------------------------------------------------------------------------------------- plan
def parse_episode_spec(spec):
    """'1-10, 15, 300-, ep042, x20200101-foo' -> predicate on episode dicts. Empty -> everything."""
    spec = (spec or "").strip()
    if not spec:
        return lambda ep: True
    nums, ranges, keys = set(), [], set()
    for tok in re.split(r"[,\s]+", spec):
        if not tok:
            continue
        m = re.match(r"^(\d+)-(\d*)$", tok)
        if m:
            ranges.append((int(m.group(1)), int(m.group(2)) if m.group(2) else 10**6))
        elif tok.isdigit():
            nums.add(int(tok))
        else:
            keys.add(tok.lower())

    def pred(ep):
        n = ep.get("number")
        return ep["key"].lower() in keys or (n is not None and (n in nums or any(a <= n <= b for a, b in ranges)))
    return pred


def plan_shards(episodes, parallel, prev_status, spec="", force=False, mode="all"):
    pick = parse_episode_spec(spec)
    todo = [e for e in episodes if pick(e) and (force or (prev_status.get(e["key"], {}).get("status") != "done"))]
    if mode == "captions":
        cost = lambda e: 1.0  # noqa: E731
    else:
        cost = lambda e: float(e.get("duration_sec") or 3600)  # noqa: E731
    n = max(1, min(int(parallel), len(todo))) if todo else 0
    shards, load = [[] for _ in range(n)], [0.0] * n
    for e in sorted(todo, key=lambda e: -cost(e)):   # longest-processing-time first: balanced job lengths
        i = load.index(min(load))
        shards[i].append(e["key"])
        load[i] += cost(e)
    return {"shards": shards, "load_sec": load, "todo": len(todo)}


def estimate(episodes_todo, n_shards, model):
    hrs = sum((e.get("duration_sec") or 3600) for e in episodes_todo) / 3600
    rtf = RTF_GUESS.get(model, 5.0)
    whisper_min = hrs * 60 / rtf
    overhead = n_shards * 4   # checkout, pip, model download per job
    return {"audio_hours": round(hrs, 1), "assumed_rtf": rtf, "whisper_runner_minutes": round(whisper_min + overhead),
            "per_shard_minutes": round(whisper_min / max(1, n_shards) + 4)}


# ------------------------------------------------------------------------------------------------------- commands
def cmd_list(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    episodes, feed_report = build_episode_list(http_get, [a.feed_url] if a.feed_url else [])
    if not episodes:
        log("::error::no episode list from any feed / iTunes")
        (out / "list_status.json").write_text(json.dumps({"feeds": feed_report}, indent=1))
        return 1
    videos, yt_report = ([], [{"skipped": "mode=whisper"}]) if a.mode == "whisper" else list_youtube()
    match_youtube(episodes, videos)
    prev = json.loads(Path(a.prev_status).read_text()) if a.prev_status and Path(a.prev_status).exists() else {}
    plan = plan_shards(episodes, a.parallel, prev, a.episodes, a.force, a.mode)
    todo_eps = [e for e in episodes if any(e["key"] in s for s in plan["shards"])]
    est = estimate(todo_eps, len(plan["shards"]), a.model)
    matched_ids = {e.get("youtube_id") for e in episodes}
    unmatched = [v for v in videos if v["id"] not in matched_ids and (v.get("duration") or 0) >= MIN_VIDEO_SEC]
    nums = [e["number"] for e in episodes if e.get("number") is not None]
    missing = sorted(set(range(1, max(nums) + 1)) - set(nums)) if nums else []
    summary = {"episodes": len(episodes), "numbered": len(nums), "max_number": max(nums) if nums else None,
               "missing_numbers": missing, "with_audio": sum(bool(e["audio_url"]) for e in episodes),
               "youtube_videos": len(videos), "youtube_matched": sum(bool(e.get("youtube_id")) for e in episodes),
               "youtube_unmatched_long_videos": len(unmatched), "todo": plan["todo"], "shards": len(plan["shards"]),
               "estimate": est, "feeds": feed_report, "youtube": yt_report, "disclaimer": DISCLAIMER}
    (out / "episodes.json").write_text(json.dumps(episodes, indent=1, ensure_ascii=False))
    (out / "youtube_videos.json").write_text(json.dumps({"videos": videos, "unmatched": unmatched}, indent=1,
                                                        ensure_ascii=False))
    (out / "plan.json").write_text(json.dumps(plan, indent=1))
    (out / "list_status.json").write_text(json.dumps(summary, indent=1))
    log(json.dumps({k: v for k, v in summary.items() if k not in ("feeds", "youtube")}))
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"shards={json.dumps(list(range(len(plan['shards']))))}\ntodo={plan['todo']}\n")
    gh_sum = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh_sum:
        with open(gh_sum, "a") as f:
            f.write(f"## CWT episode list\n{DISCLAIMER}\n\n```\n{json.dumps(summary, indent=1)[:6000]}\n```\n")
    return 0


def cmd_work(a):
    t0 = time.time()
    lst = Path(a.list_dir)
    eps = {e["key"]: e for e in json.loads((lst / "episodes.json").read_text())}
    keys = json.loads((lst / "plan.json").read_text())["shards"][a.shard]
    out = Path(a.out)
    (out / "transcripts").mkdir(parents=True, exist_ok=True)
    status_path = out / f"status_shard{a.shard:03d}.json"
    status = {}
    yt_blocks, yt_off = 0, a.mode == "whisper"
    rtf_seen = []
    log(f"shard {a.shard}: {len(keys)} episodes, mode={a.mode}, model={a.model}, cpus={os.cpu_count()}")

    def save():
        status_path.write_text(json.dumps(status, indent=1))

    for n, k in enumerate(keys):
        ep = eps[k]
        rec = {"status": "failed", "attempts": [], "updated": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        elapsed = (time.time() - t0) / 60
        need = 0.0
        if a.mode in ("whisper", "all"):
            rtf = (sum(rtf_seen) / len(rtf_seen)) if rtf_seen else RTF_GUESS.get(a.model, 5.0)
            need = (ep.get("duration_sec") or 3600) / rtf / 60 + 2
        if elapsed + need > a.time_budget:
            for kk in keys[n:]:
                status[kk] = {"status": "deferred", "reason": f"time budget {a.time_budget} min reached",
                              "updated": rec["updated"]}
            log(f"time budget reached after {elapsed:.0f} min; {len(keys) - n} episodes deferred")
            break
        body = source = src_url = None
        if a.mode in ("captions", "all"):
            try:
                body, src_url = site_transcript(ep, http_get)
                if body:
                    source = "site"
                else:
                    rec["attempts"].append(f"site: {src_url}")
            except Exception as e:  # noqa: BLE001
                rec["attempts"].append(f"site: {e}")
        if body is None and a.mode in ("captions", "all"):
            if not ep.get("youtube_id"):
                rec["attempts"].append("captions: no matched YouTube video")
            elif yt_off:
                rec["attempts"].append("captions: skipped (YouTube blocking this runner)")
            else:
                for fn in ("ytdlp", "api"):
                    try:
                        with tempfile.TemporaryDirectory() as td:
                            segs, source = (captions_ytdlp(ep["youtube_id"], td) if fn == "ytdlp"
                                            else captions_api(ep["youtube_id"]))
                        body, src_url, yt_blocks = segments_to_text(segs), f"https://youtu.be/{ep['youtube_id']}", 0
                        break
                    except Blocked as e:
                        rec["attempts"].append(f"captions-{fn}: BLOCKED {e}")
                        yt_blocks += 1
                    except NoCaptions as e:
                        rec["attempts"].append(f"captions-{fn}: {e}")
                    except Exception as e:  # noqa: BLE001
                        rec["attempts"].append(f"captions-{fn}: {type(e).__name__} {str(e)[:150]}")
                if yt_blocks >= BLOCK_LIMIT * 2:   # two methods per episode
                    yt_off = True
                    log("::warning::YouTube is blocking this runner (bot check / 429); captions off for this shard")
                time.sleep(a.yt_sleep)
        if body is None and a.mode in ("whisper", "all"):
            if not ep.get("audio_url"):
                rec["attempts"].append("whisper: no audio URL")
            else:
                try:
                    with tempfile.TemporaryDirectory() as td:
                        audio = Path(td) / "audio.mp3"
                        t1 = time.time()
                        src_url = download(ep["audio_url"], audio)
                        t2 = time.time()
                        segs, dur = whisper_transcribe(str(audio), a.model, a.beam)
                        took = time.time() - t2
                    body, source = segments_to_text(segs), f"whisper:{a.model}"
                    rec.update(audio_sec=round(dur), download_sec=round(t2 - t1), transcribe_sec=round(took),
                               rtf=round(dur / max(took, 1), 2))
                    rtf_seen.append(dur / max(took, 1))
                except Exception as e:  # noqa: BLE001
                    rec["attempts"].append(f"whisper: {type(e).__name__} {str(e)[:200]}")
        if body and len(body.split()) >= 300:
            words = write_transcript(out / "transcripts" / f"{k}.txt", ep, body, source, src_url or "")
            rec.update(status="done", source=source, words=words, file=f"transcripts/{k}.txt")
        else:
            if body:
                rec["attempts"].append(f"text too short ({len(body.split())} words)")
            rec["reason"] = " | ".join(rec["attempts"])[-600:] or "nothing tried"
        status[k] = rec
        save()
        log(f"[{n + 1}/{len(keys)}] {k} {rec['status']} {rec.get('source') or rec.get('reason', '')[:160]}"
            + (f" rtf={rec['rtf']}" if rec.get("rtf") else ""))
    save()
    done = sum(r["status"] == "done" for r in status.values())
    log(f"shard {a.shard}: done {done}/{len(keys)} in {(time.time() - t0) / 60:.0f} min")
    return 0 if done or not keys else 3


_MODEL = {}


def whisper_transcribe(path, model_name, beam=1):
    from faster_whisper import WhisperModel
    if model_name not in _MODEL:
        _MODEL[model_name] = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
    segments, info = _MODEL[model_name].transcribe(path, language="en", beam_size=beam, vad_filter=True,
                                                   condition_on_previous_text=False)
    segs = [(s.start, s.text.strip()) for s in segments if s.text.strip()]
    return segs, float(info.duration)


def _rank(source):
    s = (source or "").split(":")[0]
    return SOURCE_RANK.get(s, 1)


def merge_status(prev, new):
    """A new 'done' replaces an older one only if its source ranks at least as high (site > manual captions /
    gemini > whisper > auto captions); a new failure / deferral never overwrites 'done'. -> (merged, keep_file)."""
    merged, take = dict(prev), set()
    for k, r in new.items():
        p = prev.get(k)
        if r.get("status") == "done":
            if not p or p.get("status") != "done" or _rank(r.get("source")) >= _rank(p.get("source")):
                merged[k] = r
                take.add(k)
        elif not p or p.get("status") != "done":
            merged[k] = r
    return merged, take


def cmd_merge(a):
    dest, shards, lst = Path(a.dest), Path(a.shards), Path(a.list_dir)
    (dest / "transcripts").mkdir(parents=True, exist_ok=True)
    prev = json.loads((dest / "status.json").read_text()) if (dest / "status.json").exists() else {}
    new = {}
    for f in sorted(shards.rglob("status_shard*.json")):
        new.update(json.loads(f.read_text()))
    merged, take = merge_status(prev, new)
    copied = 0
    for k in take:
        src = next(iter(shards.rglob(f"transcripts/{k}.txt")), None)
        if src:
            (dest / "transcripts" / f"{k}.txt").write_bytes(src.read_bytes())
            copied += 1
    episodes = json.loads((lst / "episodes.json").read_text())
    for name in ("episodes.json", "youtube_videos.json", "list_status.json"):
        if (lst / name).exists():
            (dest / name).write_bytes((lst / name).read_bytes())
    (dest / "status.json").write_text(json.dumps(merged, indent=1, sort_keys=True))
    cols = ["key", "number", "title", "guest", "date", "duration_sec", "audio_url", "youtube_id", "youtube_match",
            "status", "source", "words", "file", "reason"]
    rows = []
    for e in episodes:
        s = merged.get(e["key"], {})
        rows.append({**{c: e.get(c) for c in cols[:9]}, "status": s.get("status", "todo"), "source": s.get("source"),
                     "words": s.get("words"), "file": s.get("file"), "reason": (s.get("reason") or "")[:300]})
    with open(dest / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    (dest / "index.json").write_text(json.dumps({"disclaimer": DISCLAIMER, "episodes": rows}, indent=1,
                                                ensure_ascii=False))
    (dest / "README.md").write_text(
        "# Chat With Traders transcripts (research input)\n\n"
        f"{DISCLAIMER}\n\nWritten by .github/workflows/cwt-transcripts.yml (research/bdi/cwt/actions/fetch_cwt.py). "
        "`index.csv` lists every episode with status/source; `status.json` has per-episode attempts and failure "
        "reasons; `transcripts/<key>.txt` holds the text with a metadata header.\n")
    counts = {}
    for r in merged.values():
        counts[r.get("status")] = counts.get(r.get("status"), 0) + 1
    by_src = {}
    for r in merged.values():
        if r.get("status") == "done":
            s = (r.get("source") or "?").split(":")[0]
            by_src[s] = by_src.get(s, 0) + 1
    this_run = {"new_status": len(new), "new_done": sum(r.get("status") == "done" for r in new.values()),
                "files_copied": copied, "totals": counts, "done_by_source": by_src, "episodes_listed": len(episodes)}
    log(json.dumps(this_run))
    gh_sum = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh_sum:
        with open(gh_sum, "a") as f:
            f.write(f"## CWT transcripts publish\n{DISCLAIMER}\n\n```\n{json.dumps(this_run, indent=1)}\n```\n")
    if a.mode != "list" and new and this_run["new_done"] == 0:
        log("::error::no episode finished in this run - see status.json reasons")
        return 2
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--out", required=True)
    p.add_argument("--prev-status", default="")
    p.add_argument("--episodes", default="")
    p.add_argument("--parallel", type=int, default=16)
    p.add_argument("--mode", default="all", choices=["list", "captions", "whisper", "all"])
    p.add_argument("--model", default="base.en")
    p.add_argument("--force", action="store_true")
    p.add_argument("--feed-url", default="")
    p = sub.add_parser("work")
    p.add_argument("--list-dir", required=True)
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--mode", default="all", choices=["captions", "whisper", "all"])
    p.add_argument("--model", default="base.en")
    p.add_argument("--beam", type=int, default=1)
    p.add_argument("--out", required=True)
    p.add_argument("--time-budget", type=float, default=320, help="minutes; no new episode starts past this")
    p.add_argument("--yt-sleep", type=float, default=4.0)
    p = sub.add_parser("merge")
    p.add_argument("--dest", required=True)
    p.add_argument("--shards", required=True)
    p.add_argument("--list-dir", required=True)
    p.add_argument("--mode", default="all")
    a = ap.parse_args(argv)
    return {"list": cmd_list, "work": cmd_work, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
