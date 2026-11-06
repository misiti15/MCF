"""BDI 2026-11-06: append forward rows for 11-06 to research/bdi/swings/forward.csv (idempotent by date+hyp) and update
research/bdi/swings/hypotheses.jsonl: forward tallies of the existing shadows, the new lead swing1106-L10 (SQZ1, failed
two years -> forward shadow), mh1106-p1 (failed two years, relative edge -> forward shadow) and the merged accumulating
swing type swing-burst-chase (11-05 + 11-06). Numbers from forward_1106_out.txt, fb1_live_out.txt, sqz1_out.txt,
mh_p1_out.txt, mh_p1_live_out.txt, nightly1106/forward_out.txt, burst2/NOTES.md. Educational only - not financial advice."""
import json
from pathlib import Path
import pandas as pd
W = Path(__file__).resolve().parents[1] / "swings"; D = "2026-11-06"
rows = [
 ("L1", 20, -0.276, "nightly1106 forward_out: inverse/vol ETP longs A 20 -0.276 vs same setups elsewhere B 240 -0.154; A - B -0.122", False),
 ("L2", 0, None, "no trigger", False),
 ("L3", 0, None, "not qualifying (SPY +0.78%, IWM +0.02% at 10:00)", False),
 ("L6", 546, 0.082, "nightly1106: others n 785 -0.073; counter minus others +0.155; setup-adjusted excess +0.003 (quiet day)", False),
 ("L7", 54, 0.876, "class A shorts with QQQ >= +0.75% (09:50-09:55, heat_fade_short burst) +0.876 vs same-setup B n 148 +0.022: A - B +0.854 (wrong sign for the lead)", False),
 ("L8", 0, None, "IWM min -0.58% (09:35, before entries) -> no class A; class B 339 -0.132 (GY 245 -0.190, T2 94 +0.017)", False),
 ("gate1-checkpoint-gate", 92, None, "states UP 11:00-12:30 + 14:00, MIXED 13:00/13:30/14:30-15:30; dropped 38 entries +11.64R (avg +0.306) -> gated - ungated -11.64R (GY -10.0, Gen -1.1, T2 -0.6); 2-day +2.17R", False),
 ("comp15-w60-early", 1, None, "first confirmed 10:00 UP (low-confidence 09:45 +4); never DOWN; 0 side flips; day closed quiet (SPY +0.07% o-c): an UP compass on a flat close", False),
 ("burst1-openloss-latch3", 166, -0.238, "forward day 1: 12 shadow-latched setup-days, all Graveyard (CWT14 orl/pdl longs 10:01-10:47, heat_fade_long 12:50 / -FD 10:21, CWT12, NS2, ST2); blocked taken entries 166 sum -39.5R -> shadow - live +39.51R (taken entries only); Primary none (MF2-FD wave entered in profit)", False),
 ("swing1105-L9", 0, None, "not qualifying (SPY +0.78% at 09:59)", False),
 ("fb1-flush-chase-shadow", 88, -0.495, "forward day 1: A near-LOD shorts 88 -0.495 vs rest 455 +0.195 (A - rest -0.69: MF2 37 -0.75, MF4 12 -0.50, GEN 31 -0.27); Bn bounce-sold 89 -0.053 vs rest +0.110 (wrong sign)", False),
 ("burst2-flush-gate-short", 0, None, "in-sample (rule built on 11-05/11-06): Primary 11-06 +11.6R (BURST2); forward from 11-09", True),
 ("burst2-openloss-latch4", 0, None, "in-sample: Primary 11-06 -0.6R vs live latch (BURST2); forward from 11-09", True),
 ("swing1106-L10", 219, None, "in-sample (lead from 11-05/11-06): class A 219 entries live -6.89R -> +0.5R what-if +6.21R (+13.1R; Primary 12 +6.8R, Gen 121 +0.5R); 11-05 242 entries +56.8R; forward from 11-09", True),
 ("mh1106-p1", 118, 0.241, "in-sample (lead from 11-06): class A 118 (beta <= 0.5, fromOpen <= +0.10% at 09:50, SPY +0.78%) win 66% +0.241R vs base 870 -0.063R: excess +0.304; forward from 11-09", True),
]
F = pd.read_csv(W / "forward.csv")
new = pd.DataFrame([dict(date=D, hyp=h, n=n, avgR=r, note=nt, in_sample=ins) for h, n, r, nt, ins in rows])
F = pd.concat([F[~((F.date == D) & F.hyp.isin(new.hyp))], new], ignore_index=True); F.to_csv(W / "forward.csv", index=False)
H = [json.loads(l) for l in (W / "hypotheses.jsonl").read_text().splitlines() if l.strip()]
byid = {h["id"]: h for h in H}
def add_day(hid, day, **kw):
    h = byid[hid]; f = h.setdefault("forward", {}); ds = f.setdefault("days", [])
    ds[:] = [d for d in ds if d.get("date") != day] + [dict(date=day, **kw)]
    f["sessions"] = len([d for d in ds if not d.get("in_sample")]); f["through"] = day
add_day("swing1103-L1", D, n_A=20, A_avg=-0.276, n_B=240, B_avg=-0.154, note="quiet day; A - B -0.122")
add_day("swing1103-L2", D, trigger=None, n_tag=0)
add_day("swing1103-L3", D, qualifying=False, spy10=0.78, iwm10=0.02)
add_day("swing1103-L6", D, n_counter=546, counter_avg=0.082, n_other=785, other_avg=-0.073, diff=0.155, setup_adj_excess=0.003, dtype="quiet")
add_day("swing1104-L7", D, n_A=54, A_avg=0.876, n_B=148, B_avg=0.022, diff=0.854, note="wrong sign: the 09:50-09:55 heat_fade_short burst at the QQQ high won")
add_day("swing1104-L8", D, n_A=0, n_B=339, B_avg=-0.132, note="no class A (IWM <= -0.5% only at 09:35)")
add_day("gate1-checkpoint-gate", D, delta_R=-11.64, dropped=38, dropped_avg=0.306, note="UP/MIXED day; dropped GY CWT14 / Gen longs that won")
g = byid["gate1-checkpoint-gate"]["forward"]; g["delta_R_total"] = round(13.81 - 11.64, 2); g["sessions"] = 2
add_day("comp15-w60-early", D, first_confirmed="10:00 UP", flips=0, close_dtype="quiet")
add_day("burst1-openloss-latch3", D, shadow_latched_setup_days=12, blocked_taken=166, shadow_minus_live=39.51, primary=0, note="all Graveyard; taken entries only")
add_day("swing1105-L9", D, qualifying=False, spy10=0.78)
byid["swing1105-L9"]["forward"]["qualifying_days"] = 0
add_day("fb1-flush-chase-shadow", D, n_A=88, A_avg=-0.495, n_rest=455, rest_avg=0.195, n_Bn=89, Bn_avg=-0.053, note="A side replicates (A - rest -0.69); Bn side wrong sign")
add_day("burst2-flush-gate-short", D, in_sample=True, primary=11.6)
add_day("burst2-openloss-latch4", D, in_sample=True, primary=-0.6)
H.append({"id": "swing1106-L10", "date": D, "source": "research/bdi/1106/NOTES.md 0b + SQZ1_PLAN.md (11-06 MF2-FD 14 shorts 10:40 after QQQ -0.9% in 30 min, stopped 10:44-10:52; Gen / GY long bursts 10:46-10:53 at the squeeze top; 11-05 MF4 / RW3S / GEN-261022-09 shorts at the 10:53 low)",
          "type": "exit rework for chase bursts (journal-only forward shadow, no trading change)", "pre_registered_at": "2026-11-06 ~22:50 ET (SQZ1_PLAN.md, commit d5855d6b3, before any two-year read)",
          "rule": "Class A = >= 3rd same-side entry of its setup within 15 min AND QQQ 30-min return at the entry <= -0.40% (short) / >= +0.40% (long). Class A takes a +0.5 x stop-distance target (stop, flatten unchanged).",
          "backtest": {"configs": 1, "lineage": "BURST 30", "bar": 2.61, "TRAIN_delta": -268.3, "VALID_delta": -276.8, "VALID_t": -1.38, "VALID_excess": -84.1, "VALID_excess_t": -0.45, "nA_TRAIN": 52164, "nA_VALID": 32105, "families_harmed": 4, "setups_VALID_better_worse": "20 / 29", "QDAY_VALID": {"down": -287.3, "quiet": 51.6, "up": -41.1}},
          "status": "backtest failed; forward shadow running (from 11-09)", "pass_bar_forward": ">= 5 sessions with class A trades, +0.5R what-if minus live > 0 on >= 60% of them, and > the same scalp on the same setups' other entries",
          "configs_tried": 1, "forward": {"sessions": 0, "days": [{"date": D, "in_sample": True, "n_A": 219, "live": -6.89, "scalp": 6.21}, {"date": "2026-11-05", "in_sample": True, "n_A": 242, "live": -96.52, "scalp": -39.69}], "through": D}})
H.append({"id": "mh1106-p1", "date": D, "source": "research/bdi/1106/MH_PLAN.md (Move Hunt 11-06: 13 of 25 top tradable long moves were low-beta defensives that had not joined the up open)",
          "type": "precursor / QDAY long idea (journal-only forward shadow)", "pre_registered_at": "2026-11-06 ~23:20 ET (MH_PLAN.md, commit 79158e685)",
          "rule": "At the 09:50 bar on days SPY >= +0.40% from its open: long names with 60-session daily beta to SPY <= 0.50 and fromOpen <= +0.10% (adv20 >= $95M, close >= $5), t1s1, production costs.",
          "backtest": {"configs": 1, "bar": "BAR90 1.35 (N 2)", "qual_days": 20, "n_A": 2799, "avgR": -0.023, "TRAIN": -0.040, "VALID": 0.004, "excess": 0.170, "excess_t": 1.51, "VALID_excess": 0.357, "up_days": -0.114, "down_days": 0.158, "months_pos": 0.40, "wo_best_day": -0.066},
          "status": "backtest failed (avg R < 0, 40% months); relative edge vs same-day longs (excess +0.17R, t 1.51) -> forward shadow",
          "pass_bar_forward": ">= 8 qualifying sessions: class A avg R > 0 after costs AND excess >= +0.10R, same signs w/o the best day; then a pre-registered re-test as a hedge leg on up opens",
          "configs_tried": 1, "forward": {"sessions": 0, "days": [{"date": D, "in_sample": True, "n_A": 118, "A_avg": 0.241, "base_avg": -0.063}], "through": D}})
H.append({"id": "swing-burst-chase", "date": D, "type": "accumulating swing type (merged; owner 2026-11-06)",
          "rule": "Swing type: one setup (or a family) fires a same-side burst AFTER the index already moved hard that way (QQQ <= -0.4% / >= +0.4% in 30 min), the entries stop together in the snap-back (squeeze / flush reversal). Each occurrence is logged with the leg R, the burst, the index move and the shadows that would have acted.",
          "occurrences": [
            {"date": "2026-11-05", "account": "Primary", "leg": "10:42-11:22 -19.29R", "burst": "MF4-FD 11 shorts 11:00-11:10 (-11.6R)", "index": "QQQ -4.4% to the 10:53 low", "also": "T2 RW3S 20 shorts -19.2R; Gen GEN-261022-09 48 shorts -58.5R"},
            {"date": "2026-11-06", "account": "Primary", "leg": "10:41-10:51 -46.59R (market -24.21, mismatch -12.60, entries +0.57, stock -10.35)", "burst": "MF2-FD 14 shorts 10:40 + 6 at 10:35, MF4-FD 10 shorts 10:35-10:40; 20 stopped 10:44-10:52", "index": "QQQ +0.68% -> -0.21% 10:00-10:30, SPY squeezed +0.29 -> +0.75% 10:41-10:51", "also": "Gen GEN-261021-07 37 longs 10:46-10:53 -19.2R and GY CWT14 orl longs 54 at 10:46-10:52 -22.8R bought the squeeze top"}],
          "linked_shadows": ["burst1-openloss-latch3", "burst2-openloss-latch4", "burst2-flush-gate-short", "fb1-flush-chase-shadow", "swing1106-L10"],
          "tested_remedies": "BURST1 16 + BURST2 13 + SQZ1 1 = 30 configs, 0 pass (block: blocked trades are not losers on two years; exit scalp: class A not special)",
          "status": "accumulating", "next": "setup-level rework (backlog burst2-mf-after-flush-rework); count occurrences: 2 sessions in 24"})
(W / "hypotheses.jsonl").write_text("".join(json.dumps(h) + "\n" for h in H))
print(len(H), "hypotheses;", len(F), "forward rows")
