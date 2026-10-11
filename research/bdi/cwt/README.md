# Chat With Traders (CWT) transcripts - collection

Educational only - not financial advice.

Research input for extracting intraday setups from the ~372 "Chat With Traders" interviews and testing them in MCF.
The Claude container cannot reach youtube.com or chatwithtraders.com (proxy 403), so collection runs on GitHub
Actions: `.github/workflows/cwt-transcripts.yml` + `research/bdi/cwt/actions/fetch_cwt.py`
(offline tests: `tests/test_cwt_fetch.py`).

## What the workflow does

1. **list** job - episode list and work plan.
   - Podcast RSS: iTunes search API (`itunes.apple.com/search?term=chat+with+traders&entity=podcast`) -> `feedUrl`,
     plus the known candidate feeds in `FEED_CANDIDATES` and the optional `feed_url` input. Every feed that answers
     is parsed and merged (union by episode key). If no RSS answers, the iTunes episode lookup is used (only the
     newest <= 200 episodes - warned in `list_status.json`).
   - Per episode: number (`<itunes:episode>` or title), title, guest (best effort from the title), date, duration,
     audio URL, page link, show-notes text and links. Key: `ep042`; un-numbered bonus episodes `xYYYYMMDD-slug`.
   - YouTube: `yt-dlp --flat-playlist -J` on `@chatwithtraders` (and a few alternative channel URLs) plus YouTube
     links in the show notes. Matched by show-notes link, then episode number, then title/guest similarity with a
     duration check; videos under 15 min (clips/shorts) are never matched. A blocked listing is only a warning.
   - Skips episodes already `done` in `cwt/status.json` on `research-data` (unless `force`), and splits the rest
     into `parallel` shards balanced by audio length.
2. **work** matrix (one job per shard). Per episode, first success wins:
   a. a transcript linked from the show notes ("transcript" in the link) or a "Transcript" section on the episode
      page (>= 1500 words; HTML, .txt or PDF). Unverified whether chatwithtraders.com publishes any - the
      list/status files will show it.
   b. YouTube captions: yt-dlp (manual English subs preferred over auto captions), then youtube-transcript-api.
      Bot checks / 429 ("Sign in to confirm you're not a bot") are detected; after 3 blocked episodes the shard
      turns captions off and goes straight to (c).
   c. faster-whisper on the podcast MP3 (`int8`, CPU, beam 1, VAD, English). Tracking-prefixed enclosure URLs
      (podtrac/chartable/...) are retried unwrapped. The measured speed (`rtf`, x realtime) is stored per episode.
   Mode `captions` = a + b, `whisper` = c only, `all` = a -> b -> c. Every finished episode is written at once; a
   shard stops starting episodes past a 320-minute budget and marks the rest `deferred` (rerun picks them up).
3. **publish** job (single, `research-data-publish` concurrency group, after all shards): merges into `cwt/` on
   `research-data` - `transcripts/<key>.txt`, `status.json` (done/failed/deferred per episode with every attempt
   and the reason), `index.csv` / `index.json`, `episodes.json`, `youtube_videos.json` (incl. unmatched long
   videos), `list_status.json` (feeds, coverage, missing episode numbers, minutes estimate). Earlier files are kept;
   a new failure never overwrites a `done`; a better source (site > manual captions/gemini > whisper > auto
   captions) replaces a worse one. The job fails (red) when a non-list run finished zero episodes.

Transcript file layout:

```
# Chat With Traders transcript (research input). Educational only - not financial advice.
Episode: 42
Key: ep042
Title: ...
Guest: ...
Date: 2016-02-01
Source: youtube-auto | youtube-manual | whisper:base.en | site | gemini
Source-URL: ...
Audio-URL: ...
YouTube: https://youtu.be/...
Duration-sec: 3900
Words: 10500
Fetched: 2026-10-12T03:00:00Z

== SHOW NOTES ==
...
== TRANSCRIPT ==
[00:00:00] text of the first ~2 minutes ...

[00:02:01] ...
```

`fetch_cwt.read_transcript(path)` reads these and the owner's fallback files (below).

## How to dispatch (Actions -> cwt-transcripts -> Run workflow)

| step | mode | episodes | parallel | model | purpose |
|---|---|---|---|---|---|
| 1 smoke | `list` | (empty) | 16 | base.en | feeds, episode count, YouTube reachability, matching, minutes estimate |
| 2 smoke | `all` | three recent numbers, e.g. `370-372` | 3 | base.en | site/captions/whisper path per episode end to end |
| 3 smoke (only if step 2 used captions) | `whisper` | one number, e.g. `371` with `force` on | 1 | base.en | measured whisper speed (`rtf` in `status.json`) |
| full | `all` | (empty) | 20 | base.en | everything not yet done |
| rerun | `all` | (empty) | 20 | base.en | picks up failed/deferred only |

After step 1 read `cwt/list_status.json`: `episodes`, `max_number`, `missing_numbers` (should be ~empty),
`with_audio`, `youtube_videos` / `youtube_matched` (0 with a `BLOCKED` entry = YouTube refuses Actions IPs -> captions
will not work and everything goes to whisper), `estimate`.

If the feed lacks old episodes (`missing_numbers` long), find another feed URL (Apple Podcasts page, Podcast Index,
the show's site) and pass it as `feed_url` - feeds are merged.

## Runtime and minutes

- Audio: ~372 episodes x ~60-75 min = roughly 370-450 hours.
- **This repository is public** (checked 2026-10-11: `misiti15/MCF`, visibility public). Standard GitHub-hosted
  runners are free with no minute meter for public repos, and run on 4 vCPU. The only limit is 20 concurrent jobs
  (Free plan) and 6 h per job. If the repo is made private, Linux minutes are metered (Free plan 2,000 min/month,
  Pro 3,000) on 2-vCPU runners and the whisper run below WOULD exceed the free allowance.
- Whisper speed assumptions (x realtime, int8, beam 1, VAD; conservative 2-vCPU figures, 4 vCPU is roughly 1.5-2x
  faster; step 3 measures the real number):

| model | x realtime (2 vCPU) | runner minutes for ~400 h audio (2 vCPU) | on 4 vCPU (public) | wall time, 20 jobs (4 vCPU) |
|---|---|---|---|---|
| tiny.en | ~12 | ~2,000 | ~1,200 | ~1 h |
| base.en (default) | ~6 | ~4,000 | ~2,400 | ~2-2.5 h |
| small.en | ~2.5 | ~9,600 | ~5,500 | ~4.5-5 h (use parallel 30-40; runs in two waves) |

  Plus ~4 min setup per job. Captions take seconds per episode, so if YouTube answers, the whisper share (and the
  minutes) drop sharply. On a private repo at ~$0.006-0.008/min beyond the allowance, base.en would cost about
  $15-35 and small.en $60-80 (and the default $0 spending limit would simply stop the jobs).
- Keep each shard under the 320-min budget: `parallel` >= audio hours x 60 / rtf / 300. The list job prints
  `per_shard_minutes`; if it is above ~300 raise `parallel` (max 256; 20 run at a time). Deferred episodes are
  picked up by a rerun anyway.
- base.en is good enough for setup extraction (trader jargon like "VWAP", "ORB", tickers may be misspelled);
  rerun selected high-value episodes with `small.en` + `force` if needed.

## Fallback: the owner's Gemini transcripts

If every automated path fails (no feed, YouTube blocked and audio downloads refused), the owner supplies text:

- Folder: `research/bdi/cwt/transcripts/` in this repo (commit via the GitHub web UI "Add file -> Upload files" is
  fine; ~372 files x ~60 KB = ~25 MB total).
- One UTF-8 `.txt` per episode named **`epNNN.txt`** with the 3-digit episode number (`ep007.txt`, `ep042.txt`,
  `ep372.txt`). Un-numbered bonus episodes: `bonus-YYYY-MM-DD.txt`. (Names like `Ep 42 - Name.txt` are also
  understood, but `epNNN.txt` avoids ambiguity.)
- Optional header block at the top, then one blank line, then the transcript:

```
Episode: 42
Title: <episode title>
Guest: <guest name>
Date: 2016-02-01
Source: gemini

Aaron: Welcome to the show ...
Guest: Thanks for having me ...
```

- Content: the full conversation, verbatim (not a summary), speaker labels `Name:` at the start of each turn if
  available, optional `[hh:mm:ss]` timestamps. Summaries lose the exact rule details (entry trigger, stop,
  timeframe) the setup extraction needs.
- Partial coverage is fine; the analysis merges these with whatever the workflow published (`Source: gemini` ranks
  above whisper / auto captions).

## Risks

- **Copyright / public branch**: the repo and the `research-data` branch are public, so publishing full transcripts
  republishes the show's content. Decide before the full run (make the repo private - then minutes are metered as
  above - or keep only derived setup notes public).
- YouTube very likely blocks Actions IPs (bot check); expected outcome is whisper for most episodes.
- yt-dlp needs a JS runtime for YouTube (Deno is installed); yt-dlp changes often - pinning is deliberately loose.
- Feed coverage: the candidate feed URLs are unverified (could not be reached from the container); discovery via
  iTunes is the primary path, `feed_url` the manual override.
- Guest names are parsed from titles (best effort); episode numbering of specials/bonus episodes may vary by feed.

## Copyright guard (2026-10-11)
`misiti15/MCF` is a **public** repository, so its `research-data` branch is public. Full episode transcripts are the show's
copyrighted content and must not be published there. The workflow therefore refuses every mode except `list` while
the repository is public. Before transcription runs, the owner chooses one of:
1. A separate **private** repository for transcripts. The public repo's free runners do the work and push only to the private repo, using a fine-grained token stored as a secret. This needs a small workflow change.
2. Owner-supplied transcripts (e.g. via Gemini), kept in that private repository.

Only derived, paraphrased setup rules (no verbatim transcript text) go into this public repository.

### Owner chose option 1 (2026-10-11): private repository
- The workflow pushes transcripts, status and index only to the private repo `misiti15/mcf-private`. A different repo can be set with the repository variable `CWT_PRIVATE_REPO`.
- It authenticates with the secret `CWT_PRIVATE_TOKEN`: a fine-grained token with Contents read/write on that one repo.
- Shard artifacts contain transcript text. They are kept for 1 day at most and deleted by the publish job right after the push.
- Without the secret, only `mode=list` runs.
