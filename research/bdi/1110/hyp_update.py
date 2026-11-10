"""BDI 2026-11-10: append forward rows for 11-10 to research/bdi/swings/forward.csv (idempotent by date+hyp) and update
research/bdi/swings/hypotheses.jsonl: forward tallies of the running shadows (nightly1110 forward_out / forward_gate1_out /
openloss_out for L1 / L2 / L3 / L6 / gate1 / comp15 / burst1; 1110 forward_1110_out, fb1_live_out, mh_p1_live_out,
l11_live_out for the rest), the new lead swing1110-L12 (MFX1, pre-registered, two years failed -> forward shadow) and the
new accumulating swing type swing-midday-flip (11-10 first instance). Educational only - not financial advice."""
import json
from pathlib import Path
import pandas as pd
W = Path(__file__).resolve().parents[1] / "swings"; D = "2026-11-10"
rows = [
 ("L1", 35, -0.243, "nightly1110: inverse/vol ETP longs A 35 -0.243 vs same setups elsewhere B 420 +0.118; A - B -0.36 (right sign)", False),
 ("L2", 0, None, "no rotation trigger (nightly1110); the 10:55-12:45 tech-out rotation (XLK -1.12%, XLP / XLU / XLV / XLF +0.5..+0.7%) had no QQQ new high, so L2's trigger cannot fire on it", False),
 ("L3", 129, -0.394, "qualifying up morning (SPY +0.37% / IWM +0.34% at 10:00): family shorts 129 avg -0.394 (right sign)", False),
 ("L6", 100, 0.328, "nightly1110: counter-index 100 +0.328 vs others 1,194 -0.103; diff +0.431 (wrong sign; opposite of 11-09)", False),
 ("swing1104-L7", 69, 0.250, "class A shorts with QQQ >= +0.75% (max +1.21% 10:01) 69 +0.250 vs same-setup B 162 -0.269; A - B +0.518 (wrong sign)", False),
 ("swing1104-L8", 16, -0.079, "IWM min -0.65%: class A 16 -0.079 vs class B 398 +0.194; A - B -0.273 (right sign)", False),
 ("gate1-checkpoint-gate", 43, -0.155, "nightly1110 forward_gate1: dropped 43 -6.67R, gated - ungated +6.67R (P +9.06, GY +0.29, Gen -2.68)", False),
 ("comp15-w60-early", 0, None, "W60 UP-confirmed 10:00 (first), 30-min 10:30; flipped to DOWN-confirmed 11:30-14:00, UP-confirmed again 15:30 (close +0.27%): early UP right at the close, wrong for 11:30-14:00", False),
 ("burst1-openloss-latch3", 60, None, "nightly1110 openloss: shadow - live P +11.29R (24 blocked, 4 better / 0 worse), GY -2.45R (36, 2 better / 3 worse)", False),
 ("burst2-openloss-latch4", 109, -0.190, "forward day 2, 7 accounts: 12 shadow-latched setup-days, 109 blocked taken entries, shadow - live +20.72R (T1 RW7-FD 12:35 45 -25.4R; P RW5 12:31 8 -3.1R, RW3 12:35 2 -0.8R, MF4 14:10 3 -0.9R; Gen GEN-261027-06 12:00 17 +11.3R the other way)", False),
 ("burst2-flush-gate-short", 122, -0.465, "forward day 2: 122 shorts blocked -56.68R -> gate gain +56.68R (Gen 55 +44.0, T2 30 +8.7, P 12 +4.1, T1 6 +1.9, GY 19 -2.0); QQQ 30-min min -0.93%", False),
 ("swing1105-L9", 0, None, "not qualifying (SPY +0.37% at 09:59)", False),
 ("swing1106-L10", 314, -0.202, "forward day 2: class A 314 (192 long, 122 short): live -63.33R vs +0.5R scalp -35.31R -> scalp - live +28.02R (Gen +10.4, GY +10.7, T2 +7.7, P -0.8, T1 0.0)", False),
 ("fb1-flush-chase-shadow", 99, -0.503, "A (near-LOD shorts) 99 -0.503 vs rest 433 -0.284 (right sign, -0.22); Bn (bounce-sold) 101 -0.143 vs -0.367 (right sign)", False),
 ("mh1106-p1", 0, None, "not qualifying (SPY +0.07% at the 09:50 bar); descriptive class A 225 -0.117 vs base +0.217", False),
 ("swing1109-L11", 26, 0.542, "forward day 1: W60 UP-confirmed 10:00-10:44 and 15:30-; 220 family shorts, 26 shadow-blocked live +14.10R -> gate gain -14.10R (P 13 -8.29: L3-fromopen 9 -7.82R; T2 RW3S 13 -5.81R) - wrong way; the 2-year harm was in L3 too", False),
 ("swing1110-L12", 289, None, "in-sample (lead from 11-10): flip 14:31 ET (SPY below its open at 12:00); shorts open at the flip closed at the 14:30 bar close, costs in: P 50 lots -23.97R -> -19.28R (+4.69R, 5 setups better / 1 worse), T1 +16.15R, T2 +23.71R, GY +10.37R, Gen +1.36R; total +56.28R", True),
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
add_day("swing1103-L1", D, n_A=35, A_avg=-0.243, n_B=420, B_avg=0.118, note="up day (late flip); A - B -0.36")
add_day("swing1103-L2", D, trigger=None, n_tag=0, note="tech-out rotation 10:55-12:45 without a QQQ new high")
add_day("swing1103-L3", D, qualifying=True, spy10=0.37, iwm10=0.34, n_family=129, family_avg=-0.394)
add_day("swing1103-L6", D, n_counter=100, counter_avg=0.328, n_other=1194, other_avg=-0.103, diff=0.431, dtype="up (V)")
add_day("swing1104-L7", D, n_A=69, A_avg=0.250, n_B=162, B_avg=-0.269, note="wrong sign")
add_day("swing1104-L8", D, n_A=16, A_avg=-0.079, n_B=398, B_avg=0.194, note="right sign")
add_day("gate1-checkpoint-gate", D, dropped=43, gain=6.67, by_acct={"p": 9.06, "gy": 0.29, "gen": -2.68})
add_day("comp15-w60-early", D, first="10:00 UP-confirmed", c30_first="10:30", flips=1, close_side="up", note="DOWN-confirmed 11:30-14:00")
add_day("burst1-openloss-latch3", D, shadow_minus_live_p=11.29, shadow_minus_live_gy=-2.45)
add_day("burst2-openloss-latch4", D, shadow_latched_setup_days=12, blocked_taken=109, shadow_minus_live=20.72)
add_day("burst2-flush-gate-short", D, blocked=122, gate_gain=56.68)
add_day("swing1105-L9", D, qualifying=False, spy10=0.37)
add_day("swing1106-L10", D, n_A=314, live=-63.33, scalp=-35.31, diff=28.02)
add_day("fb1-flush-chase-shadow", D, n_A=99, A_avg=-0.503, n_rest=433, rest_avg=-0.284, n_Bn=101, Bn_avg=-0.143, note="both right sign")
add_day("mh1106-p1", D, qualifying=False, spy950=0.07)
add_day("swing1109-L11", D, n_family=220, blocked=26, blocked_R=14.10, gain=-14.10, by_acct={"p": -8.29, "t2": -5.81})
mfx = (Path(__file__).resolve().parent / "mfx1_out.txt").read_text()
if "swing1110-L12" not in byid:
    H.append({"id": "swing1110-L12", "date": D,
              "source": "research/bdi/1110/NOTES.md 0b (Primary +9.1R 10:55 -> -34.5R 15:51; 12:45->15:51 leg -26.9R, market -30.2R with 45 shorts open) + nightly-1110-midday-flip-open-book-exit",
              "type": "exit: midday-flip open-book exit (journal-only forward shadow, no trading change)",
              "pre_registered_at": "2026-11-10 ~22:50 ET (MFX1_PLAN.md, commit c25f74282, before the two-year read)",
              "rule": "Morning side M = sign of SPY's 11:59 1-min close vs its 09:30 open. Flip F = end of the first run of 15 consecutive 1-min SPY closes (12:00-15:29) on side -M of the open. At F close every open trade on side M (entered before F) at the last 5-min bar close <= F, minus 1 bp + $0.01/share. Entries after F and side -M untouched.",
              "side": "both (the morning side)", "account_to_test": "all (Primary reported alone)",
              "pass_bar_backtest": "VALID day-t >= 2.66 (lineage N 34: 33 compass-learn FLIP configs + 1), TRAIN delta > 0, VALID delta w/o best day > 0, >= 60% of families (>= 30 affected) better",
              "backtest": {"configs": 1, "lists": "bt_lab1104 + burst1 5-min marks", "flip_days": "107 of 457 (23%), median 13:10, 44 false (closed back on the morning side)",
                           "TRAIN": "12,196 trades / 59 days: delta +1,555.9R, day-t 2.92, 71% days better",
                           "VALID": "10,162 / 36 days: delta -79.8R, day-t -0.17, 64% days better; w/o best day -209.7R; true flips +713.7R, false flips -793.6R",
                           "LATE": "1,097 / 5 days: delta +202.4R, day-t 2.60", "families_VALID": "4 better / 5 worse of 9 (NS -67.3, GEN -42.2, exhaustion -22.9, L -15.8, RW -8.2; MF +31.1, CWT +28.2, ST +12.8, NM +4.4)",
                           "verdict": "FAIL (VALID t -0.17 < 2.66; families 4/9)"},
              "pass_bar_forward": "15 flip sessions: total delta > 0 and > 0 on >= 60% of flip sessions (P + T1 + T2 + GY pooled; Primary alone reported); then a pre-registered magnitude-conditioned re-test (mfx2 idea) before any DECISION (Testing trial, never Primary first)",
              "status": "backtest failed; forward shadow running (from 11-11)", "configs_tried": 1,
              "linked": ["swing-midday-flip", "nightly-1110-midday-flip-open-book-exit", "nightly-1110-latch-closes-open-lots", "compass-learn D1-k3"],
              "forward": {"sessions": 0, "days": [{"date": D, "in_sample": True, "flip": "14:31", "delta": {"p": 4.69, "t1": 16.15, "t2": 23.71, "gy": 10.37, "gen": 1.36}}], "through": D}})
if "swing-midday-flip" not in byid:
    H.append({"id": "swing-midday-flip", "date": D, "type": "accumulating swing type",
              "rule": "Swing type: the book builds a one-sided position with the midday index move (SPY on one side of its open around 11:00-13:00), then SPY crosses back over its open and holds; the open book gives back on the flip (market part) while new entries keep the old side.",
              "occurrences": 1,
              "instances": [{"date": D, "account": "Primary", "leg": "10:55->12:45 -16.68R (market +6.59, mismatch -12.96, entries -4.07, stock -6.25); 12:45->15:51 -26.91R (market -30.21, mismatch +10.22, entries -0.93, stock -5.99)",
                             "index": "SPY +0.61% 10:07 -> -0.33% 12:45 -> +0.32% close; XLK -1.12% / XLP +0.71% / XLU +0.73% / XLV +0.47% 10:55-12:45 (tech-out rotation), XLK +1.68% 12:45-15:51",
                             "book": "45 shorts open at 12:45 (net beta -29.8R per +1% SPY); RW3 / RW5 gap-down shorts in staples / health / utilities rose with the rotation, then the flip took the rest",
                             "also": "T2 12:40->15:59 -39.4R (RW3S-FD -35.4R, market -33.8R); Gen 09:50->12:41 -114.2R then +54.3R"}],
              "linked_shadows": ["swing1110-L12"], "tested_remedies": "MFX1 1 config (fail: false flips cost as much as true flips earn on VALID)",
              "status": "accumulating", "next": "mfx2 idea: flip only once SPY is >= 0.15% across its open (pre-register before running); latch-close idea (nightly-1110-latch-closes-open-lots) is the setup-level version"})
(W / "hypotheses.jsonl").write_text("".join(json.dumps(h) + "\n" for h in H))
print(len(H), "hypotheses;", len(F), "forward rows")
