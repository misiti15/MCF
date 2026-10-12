"""Testing 2 batch: the CWT configurations chosen for the owner-directed forward test (2026-10-12).
Educational only - not financial advice. NONE of these passed the gates; see NOTES.md for how they were chosen.

Each entry: code name -> scored source configuration, the call into cwt_live_lib, side, exit geometry, window and a
plain-English description. `build.py` writes the modules and config blocks from this list, `verify.py` checks
trade-for-trade parity against the scored trades.
"""

GUEST = {"B1": (1030, 1500), "B2": (1100, 1500), "B3": (950, 1200), "B4": (950, 1130), "B5": (950, 1130)}
FULL = (950, 1500)

S = []


def add(name, pkg, cid, cfg, call, side, geom, window, title, what):
    S.append(dict(name=name, pkg=pkg, cid=cid, cfg=cfg, call=call, side=side, geom=geom, window=list(window),
                  title=title, what=what))


# ---- B1 CWT04 Backside lower-high short (a = run from the open to the high in daily ATRs)
add("CWT04-backside-lh-a25-short", "B", 27, "B1-a2.5-trigT2-t1s1-guest", "b1(df, a=2.5, trig=2)", "short", "t1s1",
    GUEST["B1"], "Backside Lower-High Short (big runner)",
    "10:30-15:00: a stock that ran 2.5+ daily ATRs off the open has broken down (40% off the high, below VWAP); "
    "the bounce retraces 38-62% of the drop and a bar closes below the prior bar's low; short.")
add("CWT04-backside-lh-a15-short", "B", 11, "B1-a1.5-trigT2-t1s1-guest", "b1(df, a=1.5, trig=2)", "short", "t1s1",
    GUEST["B1"], "Backside Lower-High Short",
    "10:30-15:00: as the big-runner version but the run off the open only needs 1.5 daily ATRs; short the failed "
    "38-62% bounce.")
add("CWT04-backside-vwaptest-a25-short", "B", 18, "B1-a2.5-trigT1-t1s1-full", "b1(df, a=2.5, trig=1)", "short",
    "t1s1", FULL, "Backside VWAP-Test Short (big runner)",
    "09:50-15:00: after a 2.5-ATR run breaks down below VWAP, a bar reaches back up to VWAP and closes below it; short.")
add("CWT04-backside-vwaptest-a15-short", "B", 6, "B1-a1.5-trigT1-t1s05-full", "b1(df, a=1.5, trig=1)", "short",
    "t1s05", FULL, "Backside VWAP-Test Short",
    "09:50-15:00: after a 1.5-ATR run breaks down below VWAP, a bar reaches back up to VWAP and closes below it; "
    "short with a tight half-R stop.")
# ---- B2 CWT13 Stretched-from-VWAP fade (z = distance from VWAP in daily ATRs)
add("CWT13-vwapstretch-z075-long", "B", 74, "B2-z0.75-Uall-sidelong-t1s1-full", "b2(df, z=0.75, side='long')",
    "long", "t1s1", FULL, "Stretched Below VWAP Bounce (far)",
    "09:50-15:00: price sits at the low of day 0.75+ daily ATRs below VWAP after using 40% of its range; the next "
    "bar makes a higher low; buy.")
add("CWT13-vwapstretch-z05-long", "B", 45, "B2-z0.5-Uall-sidelong-t05s1-guest", "b2(df, z=0.5, side='long')",
    "long", "t05s1", GUEST["B2"], "Stretched Below VWAP Bounce",
    "11:00-15:00: price at the low of day 0.5+ daily ATRs below VWAP; the next bar makes a higher low; buy for a "
    "quick half-R target.")
add("CWT13-vwapstretch-z075-short", "B", 67, "B2-z0.75-Uall-sideshort-t1s1-guest", "b2(df, z=0.75, side='short')",
    "short", "t1s1", GUEST["B2"], "Stretched Above VWAP Fade (far)",
    "11:00-15:00: price at the high of day 0.75+ daily ATRs above VWAP; the next bar makes a lower high; short.")
add("CWT13-vwapstretch-z05-short", "B", 35, "B2-z0.5-Uall-sideshort-t1s1-guest", "b2(df, z=0.5, side='short')",
    "short", "t1s1", GUEST["B2"], "Stretched Above VWAP Fade",
    "11:00-15:00: price at the high of day 0.5+ daily ATRs above VWAP; the next bar makes a lower high; short.")
# ---- B3 CWT14 Failed breakout / stop-run reversal
add("CWT14-failbrk-pdl-p10-long", "B", 130, "B3-LPD-p0.1-Vany-sidelong-t05s1-full",
    "b3(df, level='PD', p=0.10, lowvol=False, side='long')", "long", "t05s1", FULL,
    "Failed Prior-Day-Low Break Long",
    "09:50-15:00: price pokes 0.1+ ATR under yesterday's low, then closes back above it within 3 bars; buy.")
add("CWT14-failbrk-pdl-p05-long", "B", 106, "B3-LPD-p0.05-Vany-sidelong-t05s1-full",
    "b3(df, level='PD', p=0.05, lowvol=False, side='long')", "long", "t05s1", FULL,
    "Failed Prior-Day-Low Break Long (shallow)",
    "09:50-15:00: price pokes 0.05+ ATR under yesterday's low, then closes back above it within 3 bars; buy.")
add("CWT14-failbrk-pdh-p10-lowvol-short", "B", 136, "B3-LPD-p0.1-Vlowvol-sideshort-t05s1-full",
    "b3(df, level='PD', p=0.10, lowvol=True, side='short')", "short", "t05s1", FULL,
    "Failed Prior-Day-High Break Short (low volume)",
    "09:50-15:00: price pokes 0.1+ ATR over yesterday's high on below-average volume, then closes back under it "
    "within 3 bars; short.")
add("CWT14-failbrk-orl-p10-lowvol-long", "B", 190, "B3-LOR-p0.1-Vlowvol-sidelong-t05s1-full",
    "b3(df, level='OR', p=0.10, lowvol=True, side='long')", "long", "t05s1", FULL,
    "Failed Opening-Range-Low Break Long (low volume)",
    "10:05-15:00: price pokes 0.1+ ATR under the 09:30-10:00 low on below-average volume, then closes back above it "
    "within 3 bars; buy.")
# ---- B4 CWT12 Coil / flag breakout
add("CWT12-coil-k6-long", "B", 207, "B4-parta-k6-t1s05-guest", "b4a(df, nco=6)", "long", "t1s05", GUEST["B4"],
    "Coil Under the High (6 bars)",
    "09:50-11:30: the high of day has been tested 3+ times and the last 6 bars are tight (half the usual range) just "
    "under it; buy the coil.")
add("CWT12-coil-k4-long", "B", 197, "B4-parta-k4-t05s1-guest", "b4a(df, nco=4)", "long", "t05s1", GUEST["B4"],
    "Coil Under the High (4 bars)",
    "09:50-11:30: the high of day tested 3+ times and the last 4 bars tight just under it; buy for a half-R target.")
add("CWT12-flag-s1-long", "B", 212, "B4-partb-k1-t05s1-full", "b4b(df, s=1.0)", "long", "t05s1", FULL,
    "Spike-Pullback Flag Breakout",
    "09:50-15:00: a 1-ATR push off the open, a 30-50% pullback that stays above VWAP, then the first close above the "
    "push high; buy.")
# ---- B5 CWT05 Panic flush V-reversal long
add("CWT05-flush-m075-v5-long", "B", 276, "B5-m0.75-v5-Dnone-t05s1-full", "b5(df, m=0.75, v=5)", "long", "t05s1",
    FULL, "Panic Flush Reversal (deep, 5x volume)",
    "09:50-15:00: a 0.75-ATR drop in 30 minutes to a new low of day with a 5x volume bar, then the first bar closing "
    "above the prior bar's high; buy.")
add("CWT05-flush-m05-v5-long", "B", 244, "B5-m0.5-v5-Dnone-t05s1-full", "b5(df, m=0.5, v=5)", "long", "t05s1",
    FULL, "Panic Flush Reversal (5x volume)",
    "09:50-15:00: a 0.5-ATR drop in 30 minutes to a new low of day with a 5x volume bar, then the first bar closing "
    "above the prior bar's high; buy.")
add("CWT05-flush-m05-v3-long", "B", 228, "B5-m0.5-v3-Dnone-t05s1-full", "b5(df, m=0.5, v=3)", "long", "t05s1",
    FULL, "Panic Flush Reversal (3x volume)",
    "09:50-15:00: a 0.5-ATR drop in 30 minutes to a new low of day with a 3x volume bar, then the first bar closing "
    "above the prior bar's high; buy.")
add("CWT05-flush-m075-v3-long", "B", 260, "B5-m0.75-v3-Dnone-t05s1-full", "b5(df, m=0.75, v=3)", "long", "t05s1",
    FULL, "Panic Flush Reversal (deep, 3x volume)",
    "09:50-15:00: a 0.75-ATR drop in 30 minutes to a new low of day with a 3x volume bar, then the first bar closing "
    "above the prior bar's high; buy.")
