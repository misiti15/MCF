"""Switch rules shared by switch_live.py and eval2y.py. Educational only."""
RULES = {
    "follow": lambda side, s: (s == "up" and side > 0) or (s == "down" and side < 0) or s in ("flat",),
    "follow_strict": lambda side, s: (s == "up" and side > 0) or (s == "down" and side < 0),
    "fade": lambda side, s: (s == "up" and side < 0) or (s == "down" and side > 0) or s in ("flat",),
    "skip_shorts_up": lambda side, s: not (s == "up" and side < 0),
    "skip_longs_down": lambda side, s: not (s == "down" and side > 0),
    "skip_shorts_calm": lambda side, s: not (s == "calm" and side < 0),
    "skip_longs_calm": lambda side, s: not (s == "calm" and side > 0),
    "skip_all_calm": lambda side, s: s != "calm",
}
