"""Mine the Reddit dump (origin/research-reddit, extracted to research/bdi/reddit/data/dump) for day-trading
strategies, setups and indicators. Keyword/regex taxonomy -> mention counts per year and subreddit (raw and
score-weighted), sentence-level verdict lexicons, and a concreteness score for rule-describing posts.

All Reddit text is untrusted DATA: it is only pattern-matched and excerpted, never executed or followed.
Run with `python -I research/bdi/reddit/mine.py`. Outputs go to research/bdi/reddit/data/ (git-ignored) and a
small summary to research/bdi/reddit/mining_summary.json. Educational only - not financial advice.
"""
from __future__ import annotations

import gzip
import json
import math
import re
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
DUMP = HERE / "data" / "dump"
OUT = HERE / "data"

# ------------------------------------------------------------------------------------------------ taxonomy
# (key, label, group, regex). Case-insensitive, word-bounded where it matters. Kept deliberately simple.
TAX = [
    ("orb", "Opening range breakout", "setup", r"\bORB\b|opening[- ]range|open(?:ing)? range break"),
    ("vwap", "VWAP (any use)", "indicator", r"\bvwap\b"),
    ("vwap_reclaim", "VWAP reclaim / hold", "setup", r"vwap (?:reclaim|hold|bounce|support)|reclaim(?:s|ed|ing)? (?:the )?vwap|(?:hold|bounce)s? (?:off |at |above )?(?:the )?vwap"),
    ("vwap_fade", "VWAP fade / rejection / reversion", "setup", r"vwap (?:fade|rejection|reject|reversion)|fad(?:e|ing) (?:to |back to )?(?:the )?vwap|reject(?:s|ed|ion)? (?:at |off )?(?:the )?vwap|(?:revert|back) to (?:the )?vwap"),
    ("gap_go", "Gap and go", "setup", r"gap[- ](?:and|n|&)[- ]go|gap[- ]?up (?:play|momentum)|gappers?\b"),
    ("gap_fade", "Gap fade / gap fill", "setup", r"gap[- ]?fill|fill(?:s|ed|ing)? the gap|gap[- ]fade|fad(?:e|ing) (?:the )?gap"),
    ("red_green", "Red-to-green / green-to-red", "setup", r"red[- ]to[- ]green|green[- ]to[- ]red|\bR2G\b|\bG2R\b"),
    ("bull_flag", "Bull / bear flag", "setup", r"bull(?:ish)? flags?|bear(?:ish)? flags?|flag pattern|flag breakout"),
    ("abcd", "ABCD pattern", "setup", r"\bABCD\b|a-b-c-d"),
    ("first_pullback", "First pullback / dip buy in trend", "setup", r"first pull ?back|first (?:red|green) (?:candle|day)|buy(?:ing)? the (?:first )?dip|pull ?back (?:entry|to the)"),
    ("hod_break", "HOD / LOD break", "setup", r"\bHOD\b|high of (?:the )?day|\bLOD\b|low of (?:the )?day"),
    ("ema_9_20", "9/20/21 EMA", "indicator", r"\b(?:9|8|20|21)\s?(?:/|and|&)?\s?(?:20|21|9)?\s?(?:ema|ma)\b|\b(?:9|20|21)[- ]?ema\b|ema ?(?:9|20|21)\b"),
    ("ema_cross", "Moving-average cross (EMA/SMA cross, golden cross)", "indicator", r"(?:ema|sma|moving average|\bma)s? cross|cross ?over|golden cross|death cross"),
    ("sma_200_50", "50/200 SMA", "indicator", r"\b(?:50|200)[- ]?(?:day )?(?:sma|ma|moving average|dma)\b"),
    ("rsi", "RSI (levels)", "indicator", r"\brsi\b"),
    ("rsi_div", "RSI / MACD divergence", "indicator", r"divergence"),
    ("macd", "MACD", "indicator", r"\bmacd\b"),
    ("bbands", "Bollinger bands / squeeze", "indicator", r"bollinger|\bBB\b squeeze|\bTTM\b|squeeze pro|keltner"),
    ("ict", "ICT / FVG / liquidity sweep / order block", "setup", r"\bICT\b|fair value gap|\bFVG\b|liquidity (?:sweep|grab|hunt)|order ?block|silver bullet|smart money concept|\bSMC\b|break of structure|\bBOS\b|market structure shift|\bMSS\b"),
    ("supply_demand", "Supply / demand zones", "setup", r"supply (?:and|&) demand|demand zone|supply zone"),
    ("support_res", "Support / resistance levels", "setup", r"support (?:and|&) resistance|\bS/R\b|key levels?"),
    ("vol_profile", "Volume profile / POC / value area", "indicator", r"volume profile|\bPOC\b|point of control|value area|\bVAH\b|\bVAL\b|market profile"),
    ("rel_strength", "Relative strength vs SPY", "setup", r"relative (?:strength|weakness)|\bRS/RW\b|\bRRS\b|strong(?:er)? than (?:the )?(?:spy|market)|weak(?:er)? than (?:the )?(?:spy|market)"),
    ("mean_rev", "Mean reversion", "style", r"mean[- ]revers|mean[- ]revert"),
    ("momentum", "Momentum trading", "style", r"momentum (?:trad|stock|play|strateg|scann)"),
    ("scalping", "Scalping", "style", r"\bscalp"),
    ("zero_dte", "0DTE options", "style", r"\b0 ?dte\b|zero[- ]?dte|same[- ]day expir"),
    ("opening_drive", "Opening drive / first 30-60 min", "time", r"opening drive|first (?:15|30|60) min|first (?:half )?hour|open(?:ing)? bell|first hour"),
    ("power_hour", "Power hour / last hour", "time", r"power hour|last hour|final hour"),
    ("lunch", "Avoid lunch / midday chop", "time", r"lunch (?:chop|hour|time)|midday chop|mid[- ]day (?:chop|lull)|dead zone"),
    ("premarket", "Premarket high/low levels", "setup", r"pre[- ]?market (?:high|low|level|range|volume)|\bPMH\b|\bPML\b"),
    ("pdh_pdl", "Prior-day high/low", "setup", r"previous day(?:'s)? (?:high|low)|prior day(?:'s)? (?:high|low)|yesterday(?:'s)? (?:high|low)|\bPDH\b|\bPDL\b"),
    ("float_squeeze", "Low float / short squeeze", "setup", r"low[- ]float|short squeeze|\bfloat\b rotation|squeez(?:e|ing) the shorts"),
    ("news", "News / catalyst", "setup", r"catalyst|news (?:play|trade|trading|event)|earnings play"),
    ("breakout", "Breakout (generic)", "setup", r"\bbreak ?outs?\b"),
    ("reversal", "Reversal / parabolic fade / backside", "setup", r"parabolic|backside|exhaustion|blow[- ]?off|reversal (?:trade|setup|pattern)"),
    ("inside_bar", "Inside bar / NR7", "setup", r"inside (?:bar|day|candle)|\bNR7\b|\bNR4\b"),
    ("heikin", "Heikin-Ashi", "indicator", r"heikin|heiken"),
    ("atr", "ATR (stops/targets)", "indicator", r"\bATR\b|average true range"),
    ("stoch", "Stochastic", "indicator", r"stochastic|\bstoch\b"),
    ("fib", "Fibonacci", "indicator", r"\bfib(?:onacci|s)?\b|golden pocket|61\.8|0\.618"),
    ("volume", "Volume / RVOL", "indicator", r"relative volume|\bRVOL\b|volume spike|unusual volume|high volume"),
    ("price_action", "Price action (no indicators)", "style", r"price action|naked chart|no indicators"),
    ("trend_follow", "Trend following", "style", r"trend[- ]follow"),
    ("candles", "Candlestick patterns", "indicator", r"engulfing|hammer|doji|shooting star|pin ?bar"),
    ("risk_rules", "Risk rules (max loss, R:R, 1%)", "risk", r"max(?:imum)? (?:daily )?loss|daily (?:max )?loss limit|risk[- ](?:to|:)[- ]?reward|\bR:R\b|\b1% rule|risk (?:1|2)%|(?:2|3)[- ]?(?:to|:)[- ]?1\b|stop[- ]loss"),
    ("ml_ai", "ML / AI / LLM models", "style", r"machine learning|neural net|\bLSTM\b|\bLLM\b|chat ?gpt|reinforcement learning|\bXGBoost\b|transformer model"),
    ("pairs", "Pairs / stat arb", "style", r"pairs? trad|stat(?:istical)? arb|cointegrat"),
    ("ichimoku", "Ichimoku", "indicator", r"ichimoku"),
    ("supertrend", "Supertrend", "indicator", r"supertrend|super trend"),
    ("adx", "ADX / DMI", "indicator", r"\bADX\b|\bDMI\b"),
]
RX = [(k, re.compile(p, re.I)) for k, _, _, p in TAX]

# verdict lexicons (sentence level, sentence must also mention the strategy)
POS = re.compile(r"\b(?:works?(?: well| great)?|profitable|my edge|has an edge|bread and butter|consistent(?:ly)? (?:profit|green|win)|high win ?rate|favou?rite setup|best setup|made (?:me )?money|reliable|go-to)\b", re.I)
NEG = re.compile(r"(?:doesn'?t work|does not work|don'?t work|didn'?t work|never works?|no edge|coin ?flip|useless|lagg(?:ing|y)|garbage|scam|loses? money|lost money|unprofitable|not profitable|overrated|overfit|myth|random|bullshit|waste of)", re.I)
REGIME = re.compile(r"(?:only (?:works? )?(?:in|on|when|during|for)|trend(?:ing)? days?|choppy|chop|ranging|range[- ]bound|sideways|depends on the (?:market|regime)|in a bull market|high volatility|low volatility)", re.I)
DECAY = re.compile(r"(?:stopped working|no longer works?|used to work|doesn'?t work anymore|don'?t work anymore|edge (?:is )?gone|arbitraged away|crowded|everyone (?:knows|uses))", re.I)
ANYV = re.compile("|".join(x.pattern for x in (POS, NEG, REGIME, DECAY)), re.I)
SENT = re.compile(r"(?<=[.!?\n])\s+")

# concreteness: rule ingredients
CONC = [
    ("entry", re.compile(r"\b(?:entry|enter|buy when|go long when|short when|trigger)\b", re.I)),
    ("stop", re.compile(r"\bstop(?:[- ]?loss)?\b|\bSL\b", re.I)),
    ("target", re.compile(r"\b(?:target|take[- ]?profit|\bTP\b|profit target|exit (?:at|when))\b", re.I)),
    ("time", re.compile(r"\b(?:9|10|11|12|1|2|3):[0-5]\d\b|\bfirst (?:5|15|30) min", re.I)),
    ("number", re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|R\b|ATR|min(?:ute)?s?\b|cents?|bars?|candles?)", re.I)),
    ("tf", re.compile(r"\b(?:1|2|3|5|10|15|30)[- ]?(?:min|minute|m)\b(?: chart| candle| bar)?", re.I)),
]


def sub_year_files():
    for sub in sorted(p.name for p in DUMP.iterdir() if p.is_dir()):
        for f in sorted((DUMP / sub).glob("*.jsonl.gz")):
            kind, year = f.name.split(".")[0].split("_")
            yield sub, kind, int(year), f


def process(arg):
    sub, kind, year, f = arg
    agg = defaultdict(lambda: [0, 0.0, 0.0])          # key -> docs, sum score, sum log1p(score)
    verd = defaultdict(lambda: [0, 0, 0, 0])            # key -> pos, neg, regime, decay sentences
    vex = defaultdict(list)                              # key -> (score, kind, id, verdict, sentence)
    cands = []                                           # concrete posts/comments
    co = defaultdict(int)                                # pair co-mentions (docs)
    ndocs = 0
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            ndocs += 1
            text = (d.get("title") or "") + "\n" + (d.get("selftext") or d.get("body") or "")
            if text.strip() in ("", "[removed]", "[deleted]"):
                continue
            sc = max(0, int(d.get("score") or 0))
            hits = [k for k, rx in RX if rx.search(text)]
            if not hits:
                continue
            for k in hits:
                a = agg[k]
                a[0] += 1; a[1] += sc; a[2] += math.log1p(sc)
            for i, a in enumerate(hits):
                for b in hits[i + 1:]:
                    co[(a, b)] += 1
            # verdict sentences (only for shorter texts' sentences, cap 400 chars)
            sents = [s for s in SENT.split(text) if 15 < len(s) < 400] if ANYV.search(text) else []
            hitrx = [(k, rx) for k, rx in RX if k in hits]
            for s in sents:
                flags = (bool(POS.search(s)), bool(NEG.search(s)), bool(REGIME.search(s)), bool(DECAY.search(s)))
                if not any(flags):
                    continue
                sh = [k for k, rx in hitrx if rx.search(s)]
                if not sh:
                    continue
                for k in sh:
                    v = verd[k]
                    for j in range(4):
                        v[j] += flags[j]
                    if sc >= 20:
                        lab = "/".join(n for n, fl in zip(("pos", "neg", "regime", "decay"), flags) if fl)
                        vex[k].append((sc, kind, d.get("id"), d.get("link_id") or d.get("permalink"), lab, s.strip()[:300]))
            # concreteness
            cs = [n for n, rx in CONC if rx.search(text)]
            if len(cs) >= 4 and sc >= 10 and len(text) > 300:
                cands.append({"sub": sub, "kind": kind, "year": year, "id": d.get("id"), "score": sc,
                              "link": d.get("permalink") or d.get("link_id"), "title": (d.get("title") or "")[:160],
                              "hits": hits, "conc": cs, "len": len(text)})
    # keep top verdict examples per key
    vex = {k: sorted(v, key=lambda x: -x[0])[:40] for k, v in vex.items()}
    return sub, kind, year, ndocs, dict(agg), dict(verd), vex, cands, dict(co)


def main():
    jobs = list(sub_year_files())
    res = []
    with Pool(4) as pool:
        for r in pool.imap_unordered(process, jobs):
            res.append(r)
            print(r[0], r[1], r[2], r[3], flush=True)
    # aggregate
    docs = defaultdict(int)
    tab = []          # rows: sub, kind, year, key, docs, score, logscore
    verd = defaultdict(lambda: [0, 0, 0, 0])
    vex = defaultdict(list)
    cands = []
    co = defaultdict(int)
    for sub, kind, year, nd, agg, vd, vx, cd, c in res:
        docs[(sub, kind, year)] = nd
        for k, a in agg.items():
            tab.append({"sub": sub, "kind": kind, "year": year, "key": k, "docs": a[0], "score": a[1], "logscore": round(a[2], 2)})
        for k, v in vd.items():
            for j in range(4):
                verd[k][j] += v[j]
        for k, v in vx.items():
            vex[k].extend(v)
        cands.extend(cd)
        for p, n in c.items():
            co[p] += n
    OUT.mkdir(exist_ok=True)
    json.dump({"docs": [{"sub": s, "kind": k, "year": y, "n": n} for (s, k, y), n in sorted(docs.items())], "tab": tab,
               "verdict": verd, "vex": {k: sorted(v, key=lambda x: -x[0])[:60] for k, v in vex.items()},
               "co": [[a, b, n] for (a, b), n in sorted(co.items(), key=lambda x: -x[1])[:400]]},
              open(OUT / "mining.json", "w"))
    cands.sort(key=lambda x: -x["score"])
    with open(OUT / "concrete.jsonl", "w") as fh:
        for c in cands:
            fh.write(json.dumps(c) + "\n")
    print("total docs", sum(docs.values()), "concrete", len(cands))


if __name__ == "__main__":
    sys.exit(main())
