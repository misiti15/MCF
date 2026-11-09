"""BDI 2026-11-09: append forward rows for 11-09 to research/bdi/swings/forward.csv (idempotent by date+hyp) and update
research/bdi/swings/hypotheses.jsonl: forward tallies of the existing shadows (nightly1109 forward_out / openloss_out for
L1 / L2 / L3 / L6 / burst1; forward_1109_out, fb1_live_out, mh_p1_live_out for the rest), the new lead swing1109-L11 (ECG1,
failed two years -> forward shadow) and the 11-09 instance added to the accumulating swing type swing-burst-chase (merged
as its counter-tape variant). Educational only - not financial advice."""
import json
from pathlib import Path
import pandas as pd
W = Path(__file__).resolve().parents[1] / "swings"; D = "2026-11-09"
rows = [
 ("L1", 29, -0.877, "nightly1109: inverse/vol ETP longs A 29 -0.877 vs same setups elsewhere B 126 +0.147; A - B -1.02 (right sign)", False),
 ("L2", 0, None, "no rotation trigger (nightly1109)", False),
 ("L3", 27, -0.612, "qualifying up morning (SPY +0.78% / IWM +0.54% at 10:00): family shorts 27 avg -0.612 (right sign)", False),
 ("L6", 430, -0.516, "nightly1109: counter-index 430 -0.516 vs others 536 +0.122; diff -0.637 (right sign; opposite of 11-06)", False),
 ("swing1104-L7", 430, -0.516, "class A shorts with QQQ >= +0.75% 430 -0.516; no same-setup class B (QQQ above +0.75% nearly all day)", False),
 ("swing1104-L8", 0, None, "no class A (IWM min -0.20%); class B 194 +0.206", False),
 ("burst1-openloss-latch3", 54, None, "nightly1109 openloss: Primary MF4-FD shadow-latched 10:40 (3 entries -1.66R), shadow - live P +0.89R, GY +10.56R (7 better / 2 worse)", False),
 ("burst2-openloss-latch4", 51, -0.325, "forward day 1, 7 accounts: 10 shadow-latched setup-days, blocked taken entries 51, shadow - live +16.59R (Gen GEN-261029-08 10:36 10 -7.9R, GY heat_fade_short-FD 9 -5.0R, P MF4-FD 10:40 3 -1.7R; GY RW6-FD 13 +4.5R the cost)", False),
 ("burst2-flush-gate-short", 3, -0.319, "forward day 1: 3 GY shorts blocked, gate gain +0.96R (QQQ 30-min min -0.56%)", False),
 ("swing1105-L9", 0, None, "not qualifying (SPY +0.78% at 09:59)", False),
 ("swing1106-L10", 89, 0.153, "forward day 1: class A 89 (86 long chase bursts on the up tape): live +13.66R vs +0.5R scalp +17.08R -> scalp - live +3.42R (GY +2.4, T1 +1.0, T2 +1.5, Gen -1.5)", False),
 ("fb1-flush-chase-shadow", 59, -0.508, "A (near-LOD shorts) 59 -0.508 vs rest 361 -0.500 (no separation on a trend-up day); Bn (bounce-sold) 168 -0.384 vs -0.578 (right sign)", False),
 ("mh1106-p1", 226, 0.275, "forward day 1 (SPY +0.69% at 09:50, up-close day): class A 226 win 68% +0.275 vs base 763 +0.561 -> excess -0.286 (wrong sign; matches the 2-year up-close split -0.114)", False),
 ("swing1109-L11", 86, -0.469, "in-sample (lead from 11-09): family shorts 86 (MF / flowsell / L3, 7 accounts), shadow-blocked 70 live -40.32R -> gate gain +40.32R (P 35 +18.58, GY 29 +25.47, T2 6 -3.72); forward from 11-10", True),
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
add_day("swing1103-L1", D, n_A=29, A_avg=-0.877, n_B=126, B_avg=0.147, note="up day; A - B -1.02")
add_day("swing1103-L2", D, trigger=None, n_tag=0)
add_day("swing1103-L3", D, qualifying=True, spy10=0.78, iwm10=0.54, n_family=27, family_avg=-0.612)
add_day("swing1103-L6", D, n_counter=430, counter_avg=-0.516, n_other=536, other_avg=0.122, diff=-0.637, dtype="up")
add_day("swing1104-L7", D, n_A=430, A_avg=-0.516, n_B=0, B_avg=None, note="QQQ >= +0.75% nearly all day: no class B")
add_day("swing1104-L8", D, n_A=0, n_B=194, B_avg=0.206, note="no class A (IWM min -0.20%)")
add_day("burst1-openloss-latch3", D, shadow_minus_live_p=0.89, shadow_minus_live_gy=10.56, primary="MF4-FD 10:40, 3 entries -1.66R")
add_day("burst2-openloss-latch4", D, shadow_latched_setup_days=10, blocked_taken=51, shadow_minus_live=16.59, primary="MF4-FD 10:40, 3 entries -1.7R")
add_day("burst2-flush-gate-short", D, blocked=3, gate_gain=0.96)
add_day("swing1105-L9", D, qualifying=False, spy10=0.78)
add_day("swing1106-L10", D, n_A=89, live=13.66, scalp=17.08, diff=3.42)
add_day("fb1-flush-chase-shadow", D, n_A=59, A_avg=-0.508, n_rest=361, rest_avg=-0.500, n_Bn=168, Bn_avg=-0.384, note="A no separation on a trend-up day; Bn right sign")
add_day("mh1106-p1", D, n_A=226, A_avg=0.275, base_avg=0.561, excess=-0.286, dtype="up")
if "swing1109-L11" not in byid:
    H.append({"id": "swing1109-L11", "date": D,
              "source": "research/bdi/1109/NOTES.md 0b + ECG1_PLAN.md (11-09 Primary MF4-FD 17 shorts 10:20-10:51 after the live W60 compass confirmed UP at 10:00; GY MF3 / MF5 / MF1 shorts the same)",
              "type": "early compass gate for momentum shorts (journal-only forward shadow, no trading change)",
              "pre_registered_at": "2026-11-09 ~22:45 ET (ECG1_PLAN.md + ecg1.py, commit 58c58843e, before any two-year read)",
              "rule": "Block a new momentum short (lab/live setups matching ^(NM-)?MF\\d | flowsell | ^L3-) entered at/after 10:00 while the W60 15-min compass at the latest mark <= entry reads UP-confirmed (state, not latch).",
              "evidence": "2 years (bt_lab1104, 158,472 family shorts, 14 setups, costs in, locked block excluded), 1 config (MF short-gate lineage N 34, bar 2.66 / BAR90 2.39): blocked 34.9%; TRAIN delta -463.9R (t -0.18), VALID +605.7R (t 0.67; best day 66% of it), LATE (10-06..11-04) +319.4R; VALID setups 12 better / 2 worse (L3-fromopen -110R, L3-rsi5hi -8R) -> FAIL. QDAY: the gate gains on up-close days (TRAIN +879R, VALID +2,472R, LATE +549R) and loses on quiet (VALID -1,360R) and down-close days (-507R) - a W60 UP-confirmed morning that ends quiet or down is where the blocked shorts win.",
              "pass_bar": "Forward: after 15 sessions with >= 1 blocked entry, gate gain > 0 on >= 60% of them and in total; then a pre-registered 2-year re-test of a strength-conditioned version (backlog ecg2-1109-strong-up-gate) before any DECISION.",
              "status": "backtest failed; forward shadow running (from 11-10)", "configs_tried": 1,
              "linked": ["swing-burst-chase", "gate1-checkpoint-gate", "comp15-w60-early", "nightly-1109-mf-short-upconfirmed-gate"],
              "forward": {"sessions": 0, "days": [{"date": D, "in_sample": True, "n_family": 86, "blocked": 70, "blocked_R": -40.32, "gain": 40.32,
                                                   "by_acct": {"p": 18.58, "gy": 25.47, "t2": -3.72}}], "through": D}})
sb = byid["swing-burst-chase"]
inst = sb.setdefault("instances", [])
if not any(i.get("date") == D for i in inst):
    inst.append({"date": D, "account": "Primary", "variant": "counter-tape (no flush): shorting into a confirmed-UP compass before 11:00",
                 "leg": "10:05-10:58 -19.20R (market -13.75, mismatch -2.37, entries -2.64, stock -0.44)",
                 "burst": "MF4-FD 17 shorts 10:20-10:51 (12 broad / factor ETFs), 16 stopped; L3-fromopen 10 shorts",
                 "index": "W60 UP-confirmed 10:00 all day, SPY +0.94 -> +1.40% in the leg, closed +1.44% (QQQ +2.43%)",
                 "also": "GY MF3-FD / MF5-FD / MF1-FD bursts 29 shorts 09:55-10:05 -32.7R (11 + 11 + 7 stops); Gen GEN-261029-08 36 shorts 10:05-10:25 -28.4R"})
sb["linked_shadows"] = sorted(set(sb.get("linked_shadows", [])) | {"swing1109-L11"})
sb["tested_remedies"] = "BURST1 16 + BURST2 13 + SQZ1 1 + MF1109 4 (nightly) + ECG1 1 = 35 configs, 0 pass (block: blocked trades are not losers on two years; exit scalp: class A not special; up-confirmed gate: pays on up-close days only)"
sb["next"] = "count occurrences (3 sessions in 25: 11-05, 11-06, 11-09); strength-conditioned gate (ecg2) queued; setup-level rework of MF shorts (DM-MF2 / DM-MF4 pending)"
(W / "hypotheses.jsonl").write_text("".join(json.dumps(h) + "\n" for h in H))
print(len(H), "hypotheses;", len(F), "forward rows")
