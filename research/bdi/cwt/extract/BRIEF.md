# Chat with Traders setup extraction: shared brief (owner request 2026-10-11)

*Educational only - not financial advice.*

## Source
Transcripts of all 336 Chat with Traders episodes, produced by speech-to-text (`whisper base.en`). They are stored ONLY in the
private repo clone at `/home/user/mcf-private/cwt/transcripts/<key>.txt`. Each file has a metadata header (episode, title,
guest, date). The text has timestamps and some transcription errors; for example "S&P Capital" is "SMB Capital".

## Copyright rule (hard)
This repository (`/home/user/MCF`) is PUBLIC. Write only your own **paraphrased** notes here.
- Never copy transcript text, except quotes of 12 words or fewer, and only when the exact wording is essential (for
  example the trader's name for a setup).
- Never copy, move or commit transcript files into /home/user/MCF.

## Goal
The owner wants more intraday setups from real traders and a better understanding of how small edges are gained. For
every episode, extract each concrete, testable trading setup or rule the guest describes. Secondary: a short list of
"edge principles" (risk management, trade selection, execution, sizing, time-of-day habits) that could improve how MCF
runs its setups.

## Output: one JSON object per setup, appended to `research/bdi/cwt/extract/<batch>.jsonl`
```
{"episode": 331, "key": "ep331", "guest": "...", "firm_or_style": "prop / retail / fund / ...",
 "setup_name": "trader's name for it, or a short descriptive name",
 "instrument": "US stocks / ETFs / futures (ES, NQ) / options / FX / crypto ...",
 "horizon": "scalp (<5 min) / intraday (minutes-hours) / overnight / swing (days) / position",
 "time_of_day": "e.g. first 30 min, 10:00-11:30, close, any",
 "universe_filter": "e.g. stocks in play: gap > 4%, relative volume > 3, news catalyst, float < 50M",
 "conditions": ["precise, measurable conditions in order"],
 "entry_trigger": "exact trigger (e.g. break of the 5-min opening range high on volume)",
 "stop": "...", "target_or_exit": "...", "management": "scaling, trailing, time stops",
 "stated_edge": "why the trader thinks it works (paraphrase)",
 "stated_stats": "win rate / R multiple / frequency if the guest gives numbers, else null",
 "testable_with_mcf_data": "yes / partly / no",
 "data_needed": "what MCF lacks if not fully testable (Level 2, news feed, options chain, futures, float...)",
 "mcf_translation": "how it maps onto MCF lab features (5-min bars, VWAP, ORB, RSI, gap, rvol, prior-day levels, daily bars) - concrete enough to code",
 "discretion_level": "low (fully rule-based) / medium / high (mostly feel/read)",
 "confidence": "high / medium / low (how clearly the guest specified it)",
 "timestamp": "approximate [hh:mm:ss] in the episode"}
```
Also append one line per episode to `research/bdi/cwt/extract/<batch>_episodes.jsonl`:
```
{"episode": ..., "key": ..., "guest": ..., "style": "...", "markets": "...", "n_setups": k,
 "edge_principles": ["paraphrased principle", ...], "notes": "1-2 sentences"}
```
Write an episode's record even when it has no concrete setups (`n_setups` 0); many episodes are about psychology or careers.

## How to work
- Read each transcript in chunks with the Read tool (offset/limit); some are 20k+ words.
- Append results after EACH episode, so progress survives an interruption. Re-running a batch skips episodes already in
  `_episodes.jsonl`.
- Be precise. Vague advice ("cut losers fast") is not a setup; put it under `edge_principles`.
- Use one process and no network. Do not edit `config/`, `mcf/` or workflows. Do not commit or push; the lead does that.

## Final report to the lead (concise)
- Episodes done, and setups found by horizon and instrument.
- The 10 most concrete intraday stock/ETF setups that are testable with MCF data.
- Recurring themes across guests.
