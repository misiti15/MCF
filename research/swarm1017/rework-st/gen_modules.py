"""Write the candidate lab modules (modules/*.py). Educational only - not financial advice."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "modules"
OUT.mkdir(exist_ok=True)

DOW_HELPER = '''

def _dow(df) -> np.ndarray:
    """Day of week (Mon=0) per row: offline frames carry `date`; the live lab frame has a DatetimeIndex."""
    if "date" in df:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return np.asarray(df.index.dayofweek)
'''

L3HEAD = '''"""{name} - swarm1017 rework of {parent} (research/swarm1017/rework-st, 2026-10-17).
{what}
Side {side}, exit {geom} (R = 0.25 x daily ATR, exit by 15:55). Run with min_adv 0, window {win} (bar close ET), prefilter
'gap_le:-2.6573517322540283' (as the parent).{refire}
Open 2-year history (train 2024-10 + 2025-03..12, valid 2026-01..2026-10-07; locked block never loaded; production costs):
{stats}
{caveat}
NOT scored on any locked holdout. Below the lineage try-count bar ({bar}). Research candidate only.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "{side}"
GEOM = "{geom}"
WINDOW = ({w0}, {w1})
LAYERS = {layers}
'''

mods = []
# 1. L3a + SPY > +0.5% from open, 13:35-15:00, t05s1 short
txt = L3HEAD.format(
    name="RST1-l3fromopen-spyup-pm-t05s1-short", parent="L3-gap-slope-fromopen(-FD)",
    what="Gap-down (<= -2.66%) name that has bounced > 3.46% off its open with a steep 5-min SMA20 slope, shorted late in the\n"
         "day only when SPY itself is up > 0.5% from its open (strong-tape day: the bounce is market beta, not news).",
    side="short", geom="t05s1", win="[1335, 1500]", refire="",
    stats="n 1662 (train 1029 / valid 633), exp +0.176R (train +0.175 / valid +0.178), day-clustered t 4.70; regime up +0.171 /\n"
          "down +0.322; walk-forward share 0.857; day-equal-weighted +0.104R (t 2.86); top-3 days carry 73% of total R;\n"
          "10-trades/day cap: train +0.013 / valid +0.093. SPY-threshold neighbours (0.25/0.75/1.0) at 13:35-15:00 all positive\n"
          "in train and valid; 13:00 start falls to +0.08.",
    caveat="LIVE CODE NEEDED: the live lab frame has no SPY fromOpen ('spy_fo'); without it this mask returns no trades.\n"
           "Concentration: a few mass gap-down days (2025-04) carry most of the R.",
    bar="t 5.03, N_L3 ~ 316k", w0=1335, w1=1500,
    layers=["gap <= -2.657", "sma20_slope_pct > 0.3724", "fromOpen > 3.46", "SPY fromOpen > +0.5% (same bar) [live code needed]",
            "bar close 13:35-15:00 ET"])
txt += '''

def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    if "spy_fo" not in df:          # live frame lacks SPY context: fail safe (no trades) until the code exists
        return np.zeros(len(df), dtype=bool)
    tod = c("tod")
    with np.errstate(invalid="ignore"):
        return ((c("gap") <= -2.6573517322540283) & (c("sma20_slope_pct") > 0.37244729995727527)
                & (c("fromOpen") > 3.460294628143309) & (c("spy_fo") > 0.5)
                & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
'''
mods.append(("RST1-l3fromopen-spyup-pm-t05s1-short", txt, {"parent": "L3a", "min_adv": 0, "window": [1335, 1500],
             "prefilter": "gap_le:-2.6573517322540283", "refire": False, "live_code": "spy_fo"}))

# 2. L3a + Monday + RSI5 <= 30, LONG (opposite side), full day, t1s1
txt = L3HEAD.format(
    name="RST2-l3fromopen-mon-rsi5dip-long-t1s1", parent="L3-gap-slope-fromopen(-FD)",
    what="OPPOSITE SIDE. Monday gap-down (<= -2.66%, weekend gap) that has reversed > 3.46% above its open with a steep slope;\n"
         "buy the first 5-min RSI(5) dip to <= 30 (continuation of the weekend-gap reversal).",
    side="long", geom="t1s1", win="[950, 1500]", refire="",
    stats="n 836 (train 514 / valid 322), exp +0.163R (train +0.121 / valid +0.231), day-clustered t 4.56; regime up +0.187 /\n"
          "down +0.011; walk-forward share 0.636; 65 Mondays; day-equal-weighted +0.121R (t 1.53; train +0.046, t 0.39).\n"
          "RSI5 neighbours 20/40 positive in train and valid. The same rule on Tue-Fri is negative (-0.12..+0.11).",
    caveat="WEAK: 2025-04-07 alone holds 254 of 408 morning trades; top-3 days carry 78% of total R. Day-of-week filter with\n"
           "only a weekend-gap story. Not recommended for live without the lead's locked-block score.",
    bar="t 5.03, N_L3 ~ 316k", w0=950, w1=1500,
    layers=["gap <= -2.657", "sma20_slope_pct > 0.3724", "fromOpen > 3.46", "RSI(5) <= 30", "Monday", "bar close 09:50-15:00 ET"])
txt += DOW_HELPER + '''

def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    tod = c("tod")
    with np.errstate(invalid="ignore"):
        return ((c("gap") <= -2.6573517322540283) & (c("sma20_slope_pct") > 0.37244729995727527)
                & (c("fromOpen") > 3.460294628143309) & (c("rsi5") <= 30) & (_dow(df) == 0)
                & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
'''
mods.append(("RST2-l3fromopen-mon-rsi5dip-long-t1s1", txt, {"parent": "L3a", "min_adv": 0, "window": [950, 1500],
             "prefilter": "gap_le:-2.6573517322540283", "refire": False, "live_code": ""}))

# 3. ST1 in its source window, not Monday, refire cd1
src = (ROOT / "research/bdi/fullday/ST1-ordn-long-pm-t05s1-FD.py").read_text()
body = src[src.index('import numpy as np'):]
body = body.replace('import numpy as np', 'import numpy as np\nimport pandas as pd', 1)
body = body.replace('WINDOW = None  # full day (source: WINDOW = (1335, 1500)); window = YAML [950, 1500]',
                    'WINDOW = (1335, 1500)  # the stack1009 source window (YAML [1335, 1500])')
body = body.replace('    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",\n',
                    '    "not Monday",\n    "bar close 13:35-15:00 ET (YAML window [1335, 1500]); refire cooldown 1",\n')
body = body.replace('        return np.asarray(m, dtype=bool)',
                    '        m = m & (_dow(df) != 0) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])\n        return np.asarray(m, dtype=bool)')
assert body.count("_dow(df)") == 1 and "WINDOW = (1335, 1500)" in body
body = body.replace('\n\ndef mask(df)', DOW_HELPER + '\n\ndef mask(df)', 1)
doc = '''"""RST3-st1-ordn-notmon-pm-refire-t05s1-long - swarm1017 rework of ST1-ordn-long-pm-t05s1(-FD)
(research/swarm1017/rework-st, 2026-10-17). The ST1 stack (close crosses below the 09:30-10:00 opening-range low; stock
down > 3% from the open; volume ratio >= 1.5; close inside the prior-day range) back in its source window 13:35-15:00,
skipping Mondays, with refire (cooldown 1).
Side long, exit t05s1. Run with min_adv 95000000, window [1335, 1500], refire: true, refire_cooldown: 1.
Open 2-year history (train 2024-10 + 2025-03..12, valid 2026-01..2026-10-07; production costs): n 346 (0.81/day), exp
+0.112R (train +0.125 / valid +0.101), day-clustered t 2.97; regime up +0.140 / down +0.126; walk-forward 0.857;
day-equal-weighted +0.098R (t 2.43; valid +0.029, t 0.51); top-3 days 34% of R; all 4 half-years positive.
Without the Monday skip (= ST1 in its window, refire): n 409, +0.092R, t 2.55. The full-day ST1-FD is -0.056R (n 1621).
The 13:35 window was chosen on the whole open history in stack1009 (not out of sample).
NOT scored on any locked holdout. Below the ST lineage try-count bar (t 4.97, N_ST ~ 227k). Research candidate only.
Educational only - not financial advice."""
'''
mods.append(("RST3-st1-ordn-notmon-pm-refire-t05s1-long", doc + body, {"parent": "ST1", "min_adv": 95000000,
             "window": [1335, 1500], "prefilter": None, "refire": True, "refire_cooldown": 1, "live_code": ""}))

idx = {}
for name, text, meta in mods:
    (OUT / f"{name}.py").write_text(text)
    idx[name] = meta
json.dump(idx, open(OUT / "index.json", "w"), indent=1)
print(list(idx))
