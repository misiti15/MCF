# Plain setup display names (owner 2026-11-14: "Plain names yes")

Display names only: no setup id, config, module or trading behaviour changed. Files: `config/setup_names.yaml` and its dashboard copy `docs/live/setup_names.json` (kept in sync, `tests/test_setup_names.py`).

- **89 generated (GEN-*) setups** renamed from code-style names to plain names (idea + time + side). The `Generated: ` prefix is kept because `tests/test_gen_account.py` / `tests/test_generator.py` use it to tell machine-generated setups from hand-added ones (the dashboard itself identifies GEN setups by the `GEN-` id prefix). `GEN-261020-07` already had a plain name ("Generated: Morning RSI Surge Buy") and is unchanged.
- **19 enabled full-day (-FD) copies** that had no display name (reports showed the raw code) now have one, following the house style `<base name> (all day)`.
- The two names invented in the end-of-week write-up: `GEN-261019-04` is now officially "Generated: Midday Oversold Buy (RSI < 22)"; `ST4-emadn-long-am-t1s05-FD` is "EMA Cross-Down Dip Buy (all day)" (it trades all day, so "Morning" would mislead).
- Time words: Open = 09:50-10:30, Morning = 09:50-11:00, Late-AM = 10:30-12:00, Midday = 11:00-13:00, Lunch = 11:30-14:00, PM = 13:00-15:00, Late = 14:00-15:00 (ET bar close). Parentheses give the main qualifier (market context such as SPY/QQQ direction or breadth, or a key indicator). Full rules stay in each setup's `what` text.
- Not changed: `mcf/research/generator/spec.py::display_name` still builds code-style names for any *future* generator run (no runs since 2026-10-29).

No rule / config change: display text only (no `research/ledger.jsonl` entry needed).

## Generated setups

| id | old name | new name |
|---|---|---|
| `GEN-261019-01-VWAPxUp-ATRdge3p6-FromPCATRlem0p68-OPEN-BRvwgt0p7-t05s05-long` | Generated: VWAPxUp OPEN long (BRvwgt0p7, t05s05) | Generated: Open VWAP Reclaim Buy (down stock) |
| `GEN-261019-02-BBpctle0p017-SMA20slopege0p46-PM-QQQdn-t05s1-long` | Generated: BBpctle0p017 PM long (QQQdn, t05s1) | Generated: PM Lower-Band Dip Buy (uptrend) |
| `GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long` | Generated: Ret15mATRlem0p12 PM long (BRoplt0p5, t05s1) | Generated: PM Sharp-Drop Buy (in uptrend) |
| `GEN-261019-04-EMAdChgge0p15-RSI14le22-MID-BRoplt0p5-t1s1-long` | Generated: EMAdChgge0p15 MID long (BRoplt0p5, t1s1) | Generated: Midday Oversold Buy (RSI < 22) |
| `GEN-261019-05-RSIslopelem9-PDLdistle0p14-EMAdifflem0p46-OPEN-SPYltm0p5-t1s1-long` | Generated: RSIslopelem9 OPEN long (SPYltm0p5, t1s1) | Generated: Open Prior-Day-Low Buy (SPY down) |
| `GEN-261019-06-VWAPxUp-EMAdiffge0p29-PM-SPYgt0p5-holdtr-long` | Generated: VWAPxUp PM long (SPYgt0p5, holdtr) | Generated: PM VWAP Reclaim Buy (SPY up) |
| `GEN-261019-07-VolRatioge2-UpWickge0p59-DayRngVsPrevge1p5-LATE-SPYgt0p5-t05s1-long` | Generated: VolRatioge2, UpWickge0p59 LATE long (SPYgt0p5, t05s1) | Generated: Late Volume Spike Buy (wide day) |
| `GEN-261019-08-NewHOD-Slope6ge0p03-DayRngVsPrevge1p5-AM-SPYdn-hold-short` | Generated: NewHOD AM short (SPYdn, hold) | Generated: Morning New-High Short (SPY down) |
| `GEN-261019-09-EMAdChgge0p15-Since950ATRge0p6-PM-SPYltm0p5-t05s1-short` | Generated: EMAdChgge0p15 PM short (SPYltm0p5, t05s1) | Generated: PM Runner Fade (SPY down) |
| `GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short` | Generated: FlowShiftge0p42 PM short (BRoplt0p5, t1s1) | Generated: PM Buying-Surge Fade (extended) |
| `GEN-261020-01-MACDhge0p12-RSI5le25-PM-BRvwgt0p6-t1s05-long` | Generated: MACDhge0p12, RSI5le25 PM long (BRvwgt0p6, t1s05) | Generated: PM Oversold Turn Buy (MACD rising) |
| `GEN-261020-02-RSIslopelem19-BarRngATRge0p14-BuyPressge0p17-LATE-BRvwgt0p7-t05s1-short` | Generated: RSIslopelem19, BarRngATRge0p14 LATE short (BRvwgt0p7, t05s1) | Generated: Late RSI Drop Short (big bar) |
| `GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID-BRvwlt0p3-t05s05-long` | Generated: MACDhge0p079 MID long (BRvwlt0p3, t05s05) | Generated: Midday Low Bounce Buy (MACD up) |
| `GEN-261020-04-MACDhge0p12-BullDiv-MID-SPYgt0p25-t05s1-short` | Generated: MACDhge0p12, BullDiv MID short (SPYgt0p25, t05s1) | Generated: Midday Divergence Short (SPY up) |
| `GEN-261020-05-ORBfailDn-VWAPcrossesge4-SMA20dlem0p31-LUNCH-SPYgt0p25-holdtr-long` | Generated: ORBfailDn LUNCH long (SPYgt0p25, holdtr) | Generated: Lunch Failed Breakdown Buy |
| `GEN-261020-06-VWAPxDn-Slope6lem0p011-BarsSinceHODge35-MID-BRoplt0p5-holdtr-long` | Generated: VWAPxDn MID long (BRoplt0p5, holdtr) | Generated: Midday VWAP Loss Buy (fading) |
| `GEN-261020-08-FlowShiftlem0p41-Compress6le0p077-OPEN-QQQup-t05s05-long` | Generated: FlowShiftlem0p41 OPEN long (QQQup, t05s05) | Generated: Open Tight-Range Sell-Off Buy |
| `GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long` | Generated: EMAdChgge0p093, Z12lem0p82 MID long (QQQltm0p3, holdtr) | Generated: Midday Stretched Dip Buy |
| `GEN-261020-10-BBpctge0p81-ORBfailDn-AM-BRvwlt0p3-hold-short` | Generated: BBpctge0p81, ORBfailDn AM short (BRvwlt0p3, hold) | Generated: Morning Failed-Breakdown Short |
| `GEN-261021-01-BearDiv-RVolDayle0p47-BarsSinceHODle0-LAM-SPYltm0p25-t1s1-short` | Generated: BearDiv LAM short (SPYltm0p25, t1s1) | Generated: Late-AM Divergence Short (quiet) |
| `GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long` | Generated: BarRngATRge0p14 OPEN long (SPYgt0p5, t1s1) | Generated: Open Below-Prior-Low Buy (big bar) |
| `GEN-261021-03-RSI5le34-Ret15mATRge0p12-DayRngVsPrevge1p2-LUNCH-SPYltm0p25-t05s1-short` | Generated: RSI5le34, Ret15mATRge0p12 LUNCH short (SPYltm0p25, t05s1) | Generated: Lunch Wide-Range Short (SPY down) |
| `GEN-261021-04-NewHOD-PDHdistlem0p65-LAM-QQQltm0p6-hold-short` | Generated: NewHOD LAM short (QQQltm0p6, hold) | Generated: Late-AM New-High Short (QQQ down) |
| `GEN-261021-05-RSIslopelem14-ORHdistge0p42-LAM-BRvwlt0p3-t1s05-long` | Generated: RSIslopelem14 LAM long (BRvwlt0p3, t1s05) | Generated: Late-AM Strong-Stock Dip Buy |
| `GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long` | Generated: ORBfailUp MID long (BRopgt0p5, hold) | Generated: Midday Gap-Up Failed-Break Buy |
| `GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYgt0p5-hold-long` | Generated: VWAPxUp, ORBfailUp AM long (SPYgt0p5, hold) | Generated: Morning VWAP Reclaim Buy (SPY up) |
| `GEN-261021-08-RSI2le0-Ret15mATRge0p16-ATRdge3p6-LUNCH-QQQgt0p6-holdtr-long` | Generated: RSI2le0, Ret15mATRge0p16 LUNCH long (QQQgt0p6, holdtr) | Generated: Lunch RSI(2) Flush Buy (volatile) |
| `GEN-261021-09-RSIslopelem19-ORHdistlem0p73-AM-BRvwgt0p7-t1s1-long` | Generated: RSIslopelem19 AM long (BRvwgt0p7, t1s1) | Generated: Morning RSI Drop Buy (strong mkt) |
| `GEN-261021-10-MACDhge0p079-VWAPbarslem7-OPEN-QQQup-t1s05-long` | Generated: MACDhge0p079 OPEN long (QQQup, t1s05) | Generated: Open Below-VWAP Turn Buy (QQQ up) |
| `GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6ge0p55-AM-SPYdn-hold-long` | Generated: ORBfailUp AM long (SPYdn, hold) | Generated: Morning Failed-Break Buy (wild) |
| `GEN-261022-02-ORBfailUp-EMAdChglem0p094-ADX7ge57-LATE-BRvwgt0p7-t05s1-long` | Generated: ORBfailUp, EMAdChglem0p094 LATE long (BRvwgt0p7, t05s1) | Generated: Late Failed-Breakout Buy (trend) |
| `GEN-261022-03-NewHOD-Ret15mATRge0p12-SMA20dge0p59-LATE-QQQdn-t05s1-short` | Generated: NewHOD, Ret15mATRge0p12 LATE short (QQQdn, t05s1) | Generated: Late New-High Short (QQQ down) |
| `GEN-261022-04-RSI2le0-Eff6ge0p83-SMA20dge0p59-OPEN-BRvwlt0p5-t1s1-short` | Generated: RSI2le0 OPEN short (BRvwlt0p5, t1s1) | Generated: Open First-Dip Short (extended) |
| `GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short` | Generated: MACDhge0p079, UpWickge0p71 PM short (BRoplt0p35, holdtr) | Generated: PM Upper-Wick Short (weak mkt) |
| `GEN-261022-06-NewLOD-ORBfailUp-BuyPresslem0p49-PM-SPYltm0p5-t1s1-long` | Generated: NewLOD, ORBfailUp PM long (SPYltm0p5, t1s1) | Generated: PM New-Low Buy (failed breakout) |
| `GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short` | Generated: Z12lem1p9, FlowShiftlem0p96 AM short (BRopgt0p5, t1s1) | Generated: Morning Breakdown Short (volatile) |
| `GEN-261022-08-EMAdChglem0p094-Flow3ge1-RVolDayle0p59-AM-SPYgt0p25-holdtr-short` | Generated: EMAdChglem0p094, Flow3ge1 AM short (SPYgt0p25, holdtr) | Generated: Morning Weak-Bounce Short (quiet) |
| `GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short` | Generated: Ret15mATRlem0p16, BarRngATRge0p11 AM short (BRvwlt0p3, hold) | Generated: Morning Strong-Trend Drop Short |
| `GEN-261022-10-EMAdChgge0p15-ORLdistge0p41-PDLdistle0p14-PM-BRoplt0p5-holdtr-short` | Generated: EMAdChgge0p15 PM short (BRoplt0p5, holdtr) | Generated: PM Prior-Low Bounce Short |
| `GEN-261023-01-VWAPxUp-VWAPatrge0p33-LAM-SPYgt0p5-t05s05-short` | Generated: VWAPxUp LAM short (SPYgt0p5, t05s05) | Generated: Late-AM VWAP Pop Short (SPY up) |
| `GEN-261023-02-Ret15mATRlem0p068-EMAdChgge0p028-ATRdge6-PM-BRopgt0p65-hold-long` | Generated: Ret15mATRlem0p068, EMAdChgge0p028 PM long (BRopgt0p65, hold) | Generated: PM Volatile Dip Buy (strong mkt) |
| `GEN-261023-03-RSI5le13-VWAPatrlem0p34-OPEN-BRvwgt0p6-holdtr-short` | Generated: RSI5le13 OPEN short (BRvwgt0p6, holdtr) | Generated: Open Oversold Below-VWAP Short |
| `GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long` | Generated: EMAdChglem0p028 PM long (QQQltm0p6, t1s1) | Generated: PM Prior-High Dip Buy (QQQ down) |
| `GEN-261023-05-NewLOD-SMA20dlem0p94-ORLdistlem0p24-PM-BRopgt0p65-hold-long` | Generated: NewLOD PM long (BRopgt0p65, hold) | Generated: PM New-Low Buy (strong mkt) |
| `GEN-261023-06-RSI7le38-Ret15mge0p54-EMAdiffge0p29-LAM-SPYltm0p25-t1s05-short` | Generated: RSI7le38, Ret15mge0p54 LAM short (SPYltm0p25, t1s05) | Generated: Late-AM Pop Fade (SPY down) |
| `GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long` | Generated: RSIslopege9p1, BarRngATRge0p087 LUNCH long (BRvwgt0p7, hold) | Generated: Lunch Choppy RSI Turn Buy |
| `GEN-261023-08-RSIslopelem5p5-VWAPcrossesge8-SMA50dlem1p7-LATE-SPYltm0p5-t1s1-long` | Generated: RSIslopelem5p5 LATE long (SPYltm0p5, t1s1) | Generated: Late Choppy Dip Buy (SPY down) |
| `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short` | Generated: ORBfailDn, Ret15mge0p54 LATE short (BRvwgt0p7, holdtr) | Generated: Late Failed-Breakdown Pop Short |
| `GEN-261023-10-MACDhge0p12-VWAPcrossesle0-EMAdiffge0p16-LUNCH-BRvwlt0p4-hold-long` | Generated: MACDhge0p12 LUNCH long (BRvwlt0p4, hold) | Generated: Lunch Trend Buy (MACD rising) |
| `GEN-261026-01-UpWickge0p59-Since950ATRlem0p61-AM-BRopgt0p5-holdtr-short` | Generated: UpWickge0p59 AM short (BRopgt0p5, holdtr) | Generated: Morning Upper-Wick Short (falling) |
| `GEN-261026-02-VolRatioge2-SMA20dlem0p58-BarsSinceLODle1-LATE-BRoplt0p35-t1s1-long` | Generated: VolRatioge2 LATE long (BRoplt0p35, t1s1) | Generated: Late Volume-Spike Low Buy |
| `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short` | Generated: NewLOD, Flow3lem0p37 LUNCH short (BRopgt0p5, holdtr) | Generated: Lunch New-Low Short (selling) |
| `GEN-261026-04-ORBfailDn-Ret15mlem0p55-SMA50dlem0p3-OPEN-BRvwgt0p5-holdtr-short` | Generated: ORBfailDn, Ret15mlem0p55 OPEN short (BRvwgt0p5, holdtr) | Generated: Open Failed-Breakdown Short |
| `GEN-261026-05-Ret15mATRge0p042-FromPCATRge0p28-ORHdistlem0p38-OPEN-BRopgt0p5-hold-short` | Generated: Ret15mATRge0p042 OPEN short (BRopgt0p5, hold) | Generated: Open Up-Day Bounce Short |
| `GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long` | Generated: NewLOD LATE long (SPYltm0p25, t1s1) | Generated: Late New-Low Buy (SPY down) |
| `GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short` | Generated: Flow3ge0p56, BBpctge0p98 PM short (BRvwlt0p3, holdtr) | Generated: PM Upper-Band Fade (weak mkt) |
| `GEN-261026-08-RSIslopege19-Ret5mge0p063-DayRngVsPrevge1p2-OPEN-SPYup-holdtr-short` | Generated: RSIslopege19, Ret5mge0p063 OPEN short (SPYup, holdtr) | Generated: Open RSI Surge Short (wide day) |
| `GEN-261026-09-BBpctle0p3-SMA20slopege0p46-FromPCATRge0p45-LATE-BRvwgt0p6-t05s05-long` | Generated: BBpctle0p3 LATE long (BRvwgt0p6, t05s05) | Generated: Late Uptrend Dip Buy (up day) |
| `GEN-261026-10-ORBfailDn-EMAdChglem0p051-PM-BRopgt0p65-t1s1-long` | Generated: ORBfailDn, EMAdChglem0p051 PM long (BRopgt0p65, t1s1) | Generated: PM Failed-Breakdown Buy |
| `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long` | Generated: MACDhge0p12, Ret15mATRlem0p069 LATE long (BRvwgt0p5, t05s1) | Generated: Late Pullback Buy (MACD rising) |
| `GEN-261027-02-NewLOD-RSI14le35-Gapge2-PM-SPYup-holdtr-long` | Generated: NewLOD PM long (SPYup, holdtr) | Generated: PM Gap-Up New-Low Buy (SPY up) |
| `GEN-261027-03-NewLOD-DayPosle0p19-SMA20dlem0p59-LAM-SPYgt0p5-hold-long` | Generated: NewLOD LAM long (SPYgt0p5, hold) | Generated: Late-AM New-Low Buy (SPY up) |
| `GEN-261027-04-VWAPatrge0-Gaplem2-FromOpenlem2-PM-SPYdn-t1s1-short` | Generated: VWAPatrge0, Gaplem2, FromOpenlem2 PM short (SPYdn, t1s1) | Generated: PM Gap-Down Above-VWAP Short |
| `GEN-261027-05-VolRatioge1p5-ORLdistge0p41-ATRdge6-MID-BRvwgt0p7-t05s1-long` | Generated: VolRatioge1p5 MID long (BRvwgt0p7, t05s1) | Generated: Midday Volume Buy (volatile) |
| `GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long` | Generated: ORBfailUp MID long (BRoplt0p35, holdtr) | Generated: Midday Failed-Breakout Low Buy |
| `GEN-261027-07-RSI14le35-FromOpenge2-AM-BRvwlt0p5-t1s1-short` | Generated: RSI14le35, FromOpenge2 AM short (BRvwlt0p5, t1s1) | Generated: Morning Up-Stock Dip Short |
| `GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short` | Generated: ORBfailDn LUNCH short (QQQltm0p6, hold) | Generated: Lunch Failed-Breakdown Short |
| `GEN-261027-09-ORBfailDn-Gapge2-Slope6ge0p03-LAM-BRvwlt0p5-t05s05-short` | Generated: ORBfailDn LAM short (BRvwlt0p5, t05s05) | Generated: Late-AM Gap-Up Failed-Break Short |
| `GEN-261027-10-FlowShiftlem1p2-MACDhge0p079-SMA20dge0p59-LUNCH-BRopgt0p65-holdtr-long` | Generated: FlowShiftlem1p2, MACDhge0p079 LUNCH long (BRopgt0p65, holdtr) | Generated: Lunch Selling-Flush Buy (extended) |
| `GEN-261028-01-MACDhge0p12-Since950ATRlem0p25-LATE-SPYgt0p5-holdtr-long` | Generated: MACDhge0p12 LATE long (SPYgt0p5, holdtr) | Generated: Late Down-Stock Turn Buy (SPY up) |
| `GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p6-t1s1-long` | Generated: VWAPxDn, NewLOD AM long (QQQgt0p6, t1s1) | Generated: Morning VWAP-Loss Low Buy (QQQ up) |
| `GEN-261028-03-EMAdChgge0p15-VWAPxUp-Since950ATRlem0p43-LUNCH-SPYgt0p25-hold-long` | Generated: EMAdChgge0p15, VWAPxUp LUNCH long (SPYgt0p25, hold) | Generated: Lunch VWAP Reclaim Buy |
| `GEN-261028-04-ORBfailUp-RSI14le22-Gaplem1p2-LATE-BRvwgt0p5-holdtr-long` | Generated: ORBfailUp LATE long (BRvwgt0p5, holdtr) | Generated: Late Gap-Down Oversold Buy |
| `GEN-261028-05-EMAdChgge0p093-ORLdistlem0p42-LAM-QQQgt0p6-holdtr-long` | Generated: EMAdChgge0p093 LAM long (QQQgt0p6, holdtr) | Generated: Late-AM Below-Range Turn Buy |
| `GEN-261028-06-RSI5le13-VWAPatrlem0p15-DayRngVsPrevle0p34-MID-BRoplt0p35-hold-short` | Generated: RSI5le13 MID short (BRoplt0p35, hold) | Generated: Midday Oversold Short (quiet day) |
| `GEN-261028-07-Z12ge1p6-Eff6le0p034-MID-SPYltm0p25-hold-short` | Generated: Z12ge1p6 MID short (SPYltm0p25, hold) | Generated: Midday Spike Fade (SPY down) |
| `GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long` | Generated: Ret5mge0p21 LUNCH long (BRoplt0p35, holdtr) | Generated: Lunch Tight-Range Pop Buy |
| `GEN-261028-09-FlowShiftlem0p65-ADX7le23-AM-BRoplt0p35-t05s1-long` | Generated: FlowShiftlem0p65 AM long (BRoplt0p35, t05s1) | Generated: Morning Selling-Burst Buy |
| `GEN-261028-10-BarRngATRge0p18-Flow3lem0p54-FromPCATRge0p28-PM-SPYgt0p5-hold-long` | Generated: BarRngATRge0p18, Flow3lem0p54 PM long (SPYgt0p5, hold) | Generated: PM Big Red Bar Buy (up day) |
| `GEN-261029-01-ORBfailUp-RSI14le41-ADX7le29-LAM-QQQgt0p3-hold-long` | Generated: ORBfailUp LAM long (QQQgt0p3, hold) | Generated: Late-AM Failed-Breakout Buy |
| `GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long` | Generated: RSI2le0 MID long (BRvwlt0p4, hold) | Generated: Midday Choppy Oversold Buy |
| `GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long` | Generated: MACDhlem0p12, Ret5mlem0p062 PM long (QQQup, hold) | Generated: PM Gap-Up Dip Buy (MACD falling) |
| `GEN-261029-04-Ret15mge0p54-RVolDayle0p59-VWAPcrossesle1-LUNCH-SPYgt0p25-hold-long` | Generated: Ret15mge0p54 LUNCH long (SPYgt0p25, hold) | Generated: Lunch Quiet Breakout Buy (SPY up) |
| `GEN-261029-05-BearDiv-RSI14ge78-Compress6le0p091-AM-BRopgt0p5-t05s05-long` | Generated: BearDiv AM long (BRopgt0p5, t05s05) | Generated: Morning Overbought Coil Buy |
| `GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short` | Generated: EMAdChgge0p092 LATE short (QQQltm0p3, t1s1) | Generated: Late Quiet-Day Short (QQQ down) |
| `GEN-261029-07-UpWickge0p59-DayRngVsPrevle0p42-LATE-SPYltm0p5-t05s1-short` | Generated: UpWickge0p59 LATE short (SPYltm0p5, t05s1) | Generated: Late Upper-Wick Short (SPY down) |
| `GEN-261029-08-Ret15mlem0p36-Flow3lem0p54-RSI14ge65-AM-SPYgt0p5-hold-short` | Generated: Ret15mlem0p36, Flow3lem0p54 AM short (SPYgt0p5, hold) | Generated: Morning Overbought Drop Short |
| `GEN-261029-09-RangeExpge1p6-Since950ATRlem0p43-OPEN-BRvwgt0p5-hold-short` | Generated: RangeExpge1p6 OPEN short (BRvwgt0p5, hold) | Generated: Open Range-Expansion Short |
| `GEN-261029-10-RSIslopege19-Ret5mlem0p21-EMAdiffge0p29-OPEN-BRvwgt0p5-t1s1-short` | Generated: RSIslopege19, Ret5mlem0p21 OPEN short (BRvwgt0p5, t1s1) | Generated: Open RSI Pop Reversal Short |

## Full-day copies that had no name

| id | old name | new name |
|---|---|---|
| `RW2-exhaustion-noon-adv150-short-FD` | (none - showed the code) | Big-Stock Blow-off Short (all day) |
| `NS2-sma50break-overbought-short-FD` | (none - showed the code) | Big Gainer Average Reclaim Fade (all day) |
| `MF1-945-flowsell-vwapup-FD` | (none - showed the code) | Early Sellers Above VWAP (all day) |
| `ST1-ordn-long-pm-t05s1-FD` | (none - showed the code) | Opening-Range Breakdown Buy (all day) |
| `ST2-slope20up-long-am-t05s1-FD` | (none - showed the code) | Down-Stock Trend-Turn Buy (all day) |
| `heat_fade_long-FD` | (none - showed the code) | Midday Gap-Up Dip Buy (all day) |
| `RW4-ns3-adv150-short-FD` | (none - showed the code) | Big-Stock VWAP Reclaim Fade (all day) |
| `MF5-flowsell-vwapup-rsi5hi-FD` | (none - showed the code) | Sellers into Strength (full-day copy) |
| `NS5-sma50-flush-oversold-long-FD` | (none - showed the code) | Big Loser Flush Buy (all day) |
| `RW6G1-ns2-up3-vwap2sd-short-FD` | (none - showed the code) | Big Gainer Fade, VWAP Band Guard (all day) |
| `ST4-emadn-long-am-t1s05-FD` | (none - showed the code) | EMA Cross-Down Dip Buy (all day) |
| `ST8-volspikedn-long-pm-t1s1-FD` | (none - showed the code) | Down-Stock Volume Spike Buy (all day) |
| `ST5-pdbrkup-short-mid-t05s1-FD` | (none - showed the code) | Prior-Day-High Break Fade (all day) |
| `ST3-rsi5up-short-pm-t1s1-FD` | (none - showed the code) | Gap-Up Faller Bounce Short (all day) |
| `L3-gap-slope-lowdist-FD` | (none - showed the code) | Gap-Down Bounce-off-Low Fade (all day) |
| `ST6-volspikeup-short-mid-t1s1-FD` | (none - showed the code) | Gap-Up Faller Volume Spike Short (all day) |
| `exhaustion_short-FD` | (none - showed the code) | Afternoon Blow-off Short (all day) |
| `NS1-rsidip-rsi5pop-long-FD` | (none - showed the code) | Big Gainer Dip-and-Pop (all day) |
| `NS4-pm-vwap-reclaim-oversold-short-FD` | (none - showed the code) | Afternoon VWAP Reclaim Fade (all day) |

Educational only — not financial advice.
