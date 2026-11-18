"""Build research/graveyard_review_1118/TRIAGE.csv from raw_stats.csv + the triage calls (RULE.md criteria).
Educational only - not financial advice."""
import sys, yaml, pandas as pd, numpy as np
S, OUT = sys.argv[1], sys.argv[2]
NM = yaml.safe_load(open(f"{S}/wt/config/setup_names.yaml"))
r = pd.read_csv(f"{S}/out/raw_stats.csv")
ARCH = set(open(f"{S}/arch.txt").read().split())
TUNE = {"NS3-failed-vwap-reclaim-short-FD", "MF1-945-flowsell-vwapup-FD", "MF3-open-flowsell-rsi5hi-FD"}
ARENA = {"RW6-ns2-up3-short-FD", "ST4-emadn-long-am-t1s05-FD"}
MECH = {
 "heat_fade_long": "gap-up stock pulls back hard midday (heat score); buy the dip - mean reversion inside a gap-up trend",
 "RW2-exhaustion-noon-adv150-short-FD": "RSI(5)>90 + bearish divergence on $150M+ names; short exhaustion - momentum fade",
 "LIQ-orl-sweep-open15-s25-long": "sweep under the opening-range low then 15-min reclaim; liquidity-grab reversal long",
 "CWT14": "failed break of a key level (ORL/PDL long, PDH short) closed back inside within 3 bars; trap reversal",
 "heat_fade_short": "stock below its open bounces too far too fast (heat score); short the bounce - fade against trend",
 "NS2": "big gainer (+2%) re-crosses above SMA50 while overbought; short - overextension fade",
 "MF": "bearish heat + net selling (order-flow) while price still strong (above VWAP / RSI5>70); short - flow-leads-price",
 "ST1-ordn-long-pm-t05s1-FD": "opening-range breakdown on a -3% stock with volume, inside prior range; buy - capitulation reversal",
 "ST2-slope20up-long-am-t05s1-FD": "20-bar 5-min slope turns up on a -3% stock near VWAP with buyers; buy - trend turn",
 "CWT09-gapdn-bounce-g5-lowerhalf-short": "5% gap-down that reclaimed VWAP early; short the later bounce rejection - gap continuation",
 "CWT09-gapdn-vwaploss-g5-short": "5% gap-down that reclaimed VWAP early; short the first close back below VWAP - gap continuation",
 "CWT13-vwapstretch-z05-short": "price at HOD 0.5 daily ATR above VWAP, then a lower high; short - VWAP stretch reversion",
 "CWT12": "HOD tested 3+ times, tight coil under it; buy the break for a half-R target - compression breakout",
 "NS3": "down-2% stock reclaims VWAP while above SMA50; short the failed reclaim - trend continuation",
 "NS5-sma50-flush-oversold-long-FD": "down-2% stock flushes through SMA50 with RSI14<=30; buy - oversold snap-back (Primary NS5's -FD twin)",
 "RW6": "big gainer (+3%) SMA50 cross fade; RW6G1 adds 'never above the +2SD VWAP band' guard - overextension fade",
 "ST4-emadn-long-am-t1s05-FD": "EMA cross-down dip buy in the morning",
 "RW3S-gapdn-flowsell-short-FD": "gap-down + bearish heat + heavy net selling, no RSI condition; short - Primary RW3's sibling",
}
def mech(s):
    for k in MECH:
        if s == k or s.startswith(k): return MECH[k]
    return ""
UNTRIED = {
 "heat_fade_long": "none needed now; U8 C1+S1 failed CHECK. Next: let reps build (record turned positive in GY)",
 "NS2-sma50break-overbought-short": "windowed copy, only 13 GY trades; no tune - reps first",
 "NS2-sma50break-overbought-short-FD": "U8 X3+T3 negative on FIT; untested: RW6G1-style VWAP-band guard (exists only on RW6)",
 "ST1-ordn-long-pm-t05s1-FD": "U8 X3 negative; reps first (3.3 GY trades/session)",
 "RW6G1-ns2-up3-vwap2sd-short-FD": "U8 X1+T3 FAILED (-5.4R CHECK); WB3 copy in arena since 11-17 (ledger 2026-11-16-wb-rw6g1-wb3); untouched parent keeps collecting",
 "NS5-sma50-flush-oversold-long-FD": "U8 X3+C1 negative; follows C3-NS5 (windowed NS5 leaves Primary) - judge both twins together",
 "MF5-flowsell-vwapup-rsi5hi-FD": "U8 T3 (+0.048 FIT, -0.040 w/o best); waits on C3-WB5 #3 like MF1/MF3",
 "RW3S-gapdn-flowsell-short-FD": "none (3 GY sessions); re-score at 15 GY active days (U8)",
 "CWT09-gapdn-bounce-g5-lowerhalf-short": "U8 S2+G2 FAILED CHECK (one-day gain); family test C3-WB5 #1 (CWT09 g10->g15) runs elsewhere",
 "NS3-failed-vwap-reclaim-short-FD": "C3-WB5 #2 (09:50-10:30 + SPY/QQQ up gate) pending - the family's one revival test",
 "MF1-945-flowsell-vwapup-FD": "C3-WB5 #3 (MF2/MF4 2-part gate); if it passes, same gate on MF1 (U8 K2 lifted CHECK +0.41R, 92nd pct, t 1.66 < 3.74)",
 "MF3-open-flowsell-rsi5hi-FD": "C3-WB5 #3; if it passes, same gate on MF3 (U8 T3+V2 lifted CHECK +0.15R, t 0.70)",
 "heat_fade_short": "real-time day-type gate (SPY below open at entry) untested as a single change; up days -0.57R vs down +0.04R (hindsight labels); revival via C3-MECH day-type research",
 "heat_fade_short-FD": "same day-type gate (up -0.61R n192, down +0.16R n298, hindsight); U8 FIT best K2+T3 -0.015 w/o best, S2 gate in menu not chosen",
 "RW4-ns3-adv150-short-FD": "NS3 family test (C3-WB5 #2) covers it; no second copy (U8)",
 "CWT13-vwapstretch-z05-short": "U8 X1+G1 FAILED CHECK",
 "LIQ-orl-sweep-open15-s25-long": "U8 S1+G2 FAILED CHECK (gate picked the worst trades, 0.6th pct)",
 "heat_fade_long-FD": "U8 X1+S2 negative on FIT; windowed parent (heat_fade_long) is the better copy",
 "ST2-slope20up-long-am-t05s1-FD": "U8 G2+C1 FIT -0.031 w/o best; none",
 "RW2-exhaustion-noon-adv150-short-FD": "U8 X3 negative; none",
 "CWT09-gapdn-vwaploss-g5-short": "U8 X3+M2 negative; none",
}
def untried(s):
    if s in UNTRIED: return UNTRIED[s]
    if s.startswith(("CWT12", "CWT14")):
        return "closed by U8 guardrail (no new CWT12/14 variants); C3-ROT caps 2 CWT14 per session" + \
               ("; WB5 tune copy runs in the arena (ledger 2026-11-16-wb-cwt14-orl-p10-wb5)" if s == "CWT14-failbrk-orl-p10-long" else "")
    return ""
WHY = {
 "heat_fade_long": "GY record positive (+0.093, w/o best +0.012), last-10 +0.27R/trade; former primary; mechanism sound",
 "NS2-sma50break-overbought-short": "GY n 13 (too few); whole record from Primary days",
 "NS2-sma50break-overbought-short-FD": "GY +0.116 but w/o best -0.114; last-10 +34.2R - trending up, one-day risk; rho 0.49 with Primary winners",
 "ST1-ordn-long-pm-t05s1-FD": "GY n 49 < 100; last-10 +3.7R",
 "RW6G1-ns2-up3-vwap2sd-short-FD": "U8 tier-A watch: GY 37 trades +0.171, w/o best +0.120; whole record -0.055 w/o best; best day 297% of total",
 "NS5-sma50-flush-oversold-long-FD": "GY n 47 < 100",
 "MF5-flowsell-vwapup-rsi5hi-FD": "GY n 98 < 100; last-5 +14.1R",
 "RW3S-gapdn-flowsell-short-FD": "only 3 GY sessions (in since 11-16); whole record -0.199 (Testing E)",
 "CWT09-gapdn-bounce-g5-lowerhalf-short": "GY avg -0.028 (above the -0.05 archive line); down days +0.345R (n 82)",
 "NS3-failed-vwap-reclaim-short-FD": "meets archive numbers but a pre-registered family test (C3-WB5 #2) is pending",
 "MF1-945-flowsell-vwapup-FD": "meets archive numbers but C3-WB5 #3 is pending and U8 named it the natural revival target",
 "MF3-open-flowsell-rsi5hi-FD": "meets archive numbers but C3-WB5 #3 is pending; last-5 +10.6R",
}
rows = []
for _, x in r.iterrows():
    s = x.setup
    if s in ARENA: tri = "N/A-IN-ARENA"; why = "enabled:false in GY since 11-13 (ledger 2026-11-13-gy-rw6-st4-arena); judged in its arena"
    elif s in ARCH: tri = "ARCHIVE"; why = WHY.get(s, f"GY {int(x.gy_n)} trades {x.gy_avg:+.3f} (w/o best {x.gy_wo_best:+.3f}); whole {x.avgR:+.3f} (w/o best {x.avg_wo_best:+.3f}); last-10 {x.last10_totR:+.1f}R; no pending test")
    elif s in TUNE: tri = "TUNE-CANDIDATE"; why = WHY[s]
    else: tri = "KEEP-TESTING"; why = WHY[s]
    fam = "CWT14" if s.startswith("CWT14") else "CWT12" if s.startswith("CWT12") else s.split("-")[0].split("_")[0] if not s.startswith("heat") else "heat_fade"
    rows.append(dict(setup=s, name=x["name"], family=fam, side=(NM.get(s) or {}).get("side", x.side), status_1118=x.status, former_primary=x.former_primary,
        triage=tri, live_trades=x.n, live_sessions=x.sessions, avg_R=round(x.avgR, 3), avg_R_wo_best_day=round(x.avg_wo_best, 3),
        best_day=x.best_day, best_day_share=("" if pd.isna(x.best_share) else round(x.best_share, 2)), one_day_flag=("1 day" if (not pd.isna(x.best_share) and x.best_share >= .5) else ""),
        total_R=round(x.totR, 1), green_day_pct=round(x.green_pct, 2), accounts=x.accts,
        gy_trades=int(x.gy_n), gy_sessions=int(x.gy_sessions), gy_trades_per_session=round(x.gy_trades_per_session, 1),
        gy_avg_R=round(x.gy_avg, 3), gy_avg_R_wo_best_day=round(x.gy_wo_best, 3), gy_total_R=round(x.gy_totR, 1),
        last5_trades=int(x.last5_n), last5_avg_R=round(x.last5_avg, 3), last5_total_R=round(x.last5_totR, 1),
        last10_trades=int(x.last10_n), last10_avg_R=round(x.last10_avg, 3), last10_total_R=round(x.last10_totR, 1),
        up_n=int(x.up_n), up_avg_R=round(x.up_avg, 3), down_n=int(x.down_n), down_avg_R=round(x.down_avg, 3),
        quiet_n=int(x.quiet_n), quiet_avg_R=round(x.quiet_avg, 3),
        rho_primary_winners=round(x.rho_primary_winners, 2), overlap_primary_winners_pct=round(x.overlap_primary_winner_pct * 100, 1),
        mechanism=mech(s), untried_or_pending_tunes=untried(s), reason=why))
T = pd.DataFrame(rows)
order = {"TUNE-CANDIDATE": 0, "KEEP-TESTING": 1, "ARCHIVE": 2, "N/A-IN-ARENA": 3}
T = T.sort_values(["triage", "avg_R_wo_best_day"], key=lambda c: c.map(order) if c.name == "triage" else -c).reset_index(drop=True)
T.to_csv(f"{OUT}/TRIAGE.csv", index=False)
print(T.triage.value_counts()); print(T[["setup", "triage"]].to_string())
