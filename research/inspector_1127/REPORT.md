Educational only — not financial advice

# Inspector report, week of 2026-11-23..27 (branch claude/charming-mccarthy-i3rhhr @5b9bc5c599)

Six audit dimensions (integrity, claims, live code, compliance, engines, ops). Every finding was put to an adversarial skeptic, which lowered most severities.
Each "where" was re-checked at the branch tip. The raw data is in findings.json and ideas.json.

## MUST FIX BEFORE FRIDAY 11-27 (13:00 half-day close)

**Before 09:40 ET (Hunch start).** Hunch learns from after-hours bars: mcf/hunch has no calendar; rth() cuts at a fixed 16:00 (mcf/data/bars.py:29), the day completes ~15:54 (mcf/hunch/live.py:183), and the 13:00-16:00 bars are guessed, scored, learned and saved as model_2026-11-27.npz for Monday. Fix: cap at market_calendar.session_close, or skip Hunch today and keep the 11-25 model.
**Before 13:15 ET (first post-close compass mark).** compass_live.fetch / compass_cond.fetch_spy fetch to 16:00 with no calendar (compass_live.py:57, :222-240; compass_cond.py:188-209) → 11 fake marks 13:15-15:45 and a full-session cond_obs row. Fix: cap at the calendar close (or skip marks after 13:00 and tag the row); purge the 3 already-contaminated half days (2025-07-03, 2025-11-28, 2025-12-24) before COMPASS research reads cond_obs.csv.
**Before tonight's epoch answers (after the close):**
- HS-SCALE card: say the built version blocks entries only; at N=4 X=32R is beyond the -20R halt so it never fires first; no flatten, no $-mismatch/order-size guard. "Yes" adds only SHOCK-V.
- PRIM-ADD2 re-eval (task fires 21:10Z): show PRIME-RULES ENTRY + C3-BAR2 pass/fail. Both candidates fail best-day share (83%/84% vs 40%/50% caps); RW7 had ~2 On Deck sessions (< 5). Name the PROT-21 exemption.
- L3-OUT card: add PRIME-RULES status, the skipped probation step and a "keep on probation" option; state RW3/RW5 are equally negative on the bench and their removal was never scored; add the survivorship/ETB look-ahead caveat.
- B8-SHADOW card: drop Option B (enforce) until B8 beats a size-matched random block and a constant cut; split "live +27.9R" into current vs departed setups (current trio ≈ -26.6R; MF2/MF4 gone).
- LATCH-OPEN card: remove the off-epoch "now" option; restate on the full-day base (-40.1 → -8.3R engine; journal -42.30R LR8).
- Commit the scratchpad evidence (neveragain, s8cap, hsscale, pyramid PREREGs + scripts, no parquets) before it is cleared; it still exists today.
- End-of-week post task trig_01SdRzMScyrFVKuNJnsVGWMZ (00:47Z): update the prompt (no Team section, 10 accounts, docs/posts/STYLE.md, Graveyard = plain "not exploring" line).

## 1. Verdict on the week (5 lines)
1. The live trading core is sound. The half-day flatten is at 12:55, promotion = move holds, the Friday switches default OFF, 225 tests pass, and the locked block is clean in every committed script.
2. Research was honest: costs are in, and every pass and fail is reported. But the book's own edge after costs is still negative, and no lever this week changed that.
3. The weak link is the step from report to owner card. Cards drop the caveats their reports carry: control-free "passes", departed setups counted in live gains, stale bases, skipped PRIME-RULES steps.
4. Reproducibility slipped. Two open Primary cards rest on scripts that exist only in the scratchpad, and 5 studies committed their PREREG and REPORT together.
5. Ops gaps cluster around non-standard sessions: half days, temp-file leaks, and a borrow recorder dead since 11-05.

## 2. Confirmed findings (survived the skeptic; severity shown is the skeptic's corrected one)
| # | Sev | Title | Where | Impact | Fix |
|---|---|---|---|---|---|
| 1 | MED | HS-SCALE as built does nothing in Primary; the card describes a different package | decisions.json HS-SCALE; risk.py scaled_check; FRIDAY_SWITCHES.md:33 | Owner thinks a scaled stop and bug guards protect Primary | Amend the card; build the flatten and guards separately, or re-scope to SHOCK-V only |
| 2 | MED | Hunch treats half-day after-hours bars as session bars and saves the model | bars.py:29; hunch/live.py:113,183,363 | Wrong hit rate; contaminated model carried to Monday | Calendar close in run_live; drop bars at or after close |
| 3 | MED | Compass and compass_cond use after-hours prints on half days (3 past days already stored) | compass_live.py:57,222; compass_cond.py:188,209 | 11 fake marks today; 108 contaminated rows | Calendar close; purge 2025-07-03, 2025-11-28, 2025-12-24 |
| 4 | MED | PRIM-ADD2 candidates fail the PRIME-RULES and C3-BAR2 entry bars; not flagged | PRIM-ADD2 card; trig_01Y92BPhVjeVwBjQSkSscsv6 | A promotion that breaks the owner's rule, decided tonight | Per-criterion pass/fail; name the PROT-21 exemption |
| 5 | MED | L3-OUT demotion skips the probation path; conflict not named | L3-OUT card (cde9a46c53) | A demotion path PRIME-RULES does not allow | Restate with probation status plus a "keep on probation" option |
| 6 | MED | LATCH-OPEN recommended "now" (off-epoch), against C3-EPOCH and PROT-21 | LATCH-OPEN card; inbox 11-25:96; OPEN_ITEMS:105 | Mid-week change to a protected latch | "friday" only; the recommend field must pick one reply option |
| 7 | MED | B8 "PASS" has no size-matched random-block or constant-cut control | squeeze_1125 PREREG:53-59, REPORT; B8 card | Option B could enforce a rule that may be a plain 29% cut | Run tape_1126's controls; drop Option B until then |
| 8 | MED | B8 card's live +27.9R comes from departed MF2 and MF4; current trio about -26.6R | B8 card numbers[0]; squeeze REPORT:18 | Live evidence reads the wrong way for today's book | Split the live dR; add rule-change context |
| 9 | MED | Two "day t" definitions under one label | inbox 11-25:45,46,64 vs ODP2 card | ODP2 2.53 vs 1.42; L3 +0.59 vs -0.90 (sign flip) | Use footrace day_t everywhere; label the daily-sum t separately |
| 10 | MED | Evidence behind LATCH-OPEN and HS-SCALE (and pyramid PREREGs) is only in the scratchpad | neveragain/s8cap/hsscale/pyramid_1124 hold PLAN/REPORT only | Unauditable once the scratchpad is cleared | Commit scripts, PLAN.sha256 and score outputs now |
| 11 | LOW-MED | intraday.build still leaks its mkstemp journal copy on the normal (snapshot) path | intraday.py:66-74, 291-306 | About 160 MB of /tmp per all-account run | try/finally over build(), or :memory: |
| 12 | LOW | L3-OUT reads its table selectively; RW3/RW5 removal never scored (L3 still worst on Primary like-for-like) | primshorts_1126 REPORT:10-28 | Card overstates how specific the case is to L3 | Disclose; add the RW3-out and RW5-out options |
| 13 | LOW | L3-OUT omits the survivorship and ETB look-ahead bias | primshorts bench_build.py:103-105 | Absolute "every window negative" is biased | Caveat; lead with the relative and live evidence |
| 14 | LOW | LATCH-OPEN headline uses the partial-day base (-37.4) while B8 uses -40.1 | neveragain_1125 (b0a213a8a2) | Two bases shown (stale one understates the benefit) | One base, -40.1 to -8.3R, cost basis stated |
| 15 | LOW | LATCH-OPEN falls back to closed R for the whole setup if any one lot is unmarked; logged once | risk.py _latch_open; runner.py _open_marks | Fail-open, and rare (bars accumulate) | Carry the last mark, as SHOCK-V does; count fallbacks; add a test |
| 16 | LOW | PREREG and REPORT in one commit for 5 studies | 31133ea1dd, 6ddf89fb3e, d10c34bca1, 0dff8ef6c0, bb3f848ba2 | Prereg timing unverifiable (all were FAILs) | CI check: PREREG commit before REPORT |
| 17 | LOW | Since-Day-1 figures miss the 10-23..10-27 rule changes | inbox 11-25:44,103 | Partly breaks the 11-02 rule | Start the in-window list at 10-23 |
| 18 | LOW | End-of-week task prompt stale (Team, 7 accounts, no STYLE.md) | trig_01SdRzMScyrFVKuNJnsVGWMZ | The 11-21 run self-corrected; owner reviews before posting | Update the prompt |
| 19 | LOW | inverse/shadow.py leaves 146 MB of /tmp/invshadow_*.db | research/owner1120/inverse/shadow.py:157-168 | Fixed footprint, not growing | Unlink in finally; delete the files |

## 3. Unverified or low findings (one line each, all UNVERIFIED)
- (unverified) ODB3-G102306 card omits the R3B bench result of -0.40R/trade on 2023-24.
- (unverified) The crypto LOCKED window is lightly contaminated: coverage() is not clipped, and KNOWLEDGE.md describes the LOCKED bear market.
- (unverified) CRYPTO-SCOPE card is stale: N 1,477 should be 1,491, 4 rounds not 3, and its drawdown range differs from r3.
- (unverified) Blocked-signal "saved" figures (-404R, -1,324R) are uncapped what-ifs presented as protection.
- (unverified) ODP2 recommend text is stale: it says 58% best day, the numbers say 62%.
- (unverified) Figure mismatches inside the 11-25 inbox: On Deck $, longs R, the Testing A-F sum, SPY close, compass times.
- (unverified) longs_1125 "+264R" for 10:30-12:30 does not add up; the buckets give 252.1R or 267.9R.
- (unverified) SYNTHESIS says 6 REGSTEER configs, not 7, and gives the B8 worst-5 sign inconsistently.
- (unverified) IDX3-P forward gain is quoted without its `1 day` tag (91% on 11-25).
- (unverified) The setup-freeze CI does not cover config/account_*.yaml or the default.yaml risk: block.
- (unverified) assignments.json stamps first_session 2026-11-26, a holiday; next_session() skips weekends only.
- (unverified) GYH V1: 13 setups approved, 9 moved, and the gap is not explained to the owner.
- (unverified) Cards answer either/or questions with "Yes", and LATCH-OPEN and HS-SCALE lack per-setup remedy effects.
- (unverified) The research engines realise exits inside minute m before that minute's entries. The look-ahead is under 1 minute, favours BASE, and leaves no decision changed.
- (unverified) Sim open marks charge the full round-trip cost while live charges 1bp. Research LATCH-OPEN fires slightly early (11-25: -8.3 vs -9.4R).
- (unverified) The PRIMSHORTS parity claim of ±0.005R is really 0.013R, and 38 trades are missing.
- (unverified) HEDGE-B charges SPY/IWM 1bp per side. The T2 cost verdict flips at a realistic cost; CHECK does not.
- (unverified) test_poll_log has a wall-clock assert that is load-sensitive, and no CI runs pytest.
- (unverified) On the half day, entries are allowed up to the 12:55 flatten, so trades held only minutes pay full cost. Tag 11-27 as a half day in stats.
- (unverified) A sibling inspector left a 450 MB worktree at /home/user/MCF/insp_engine. Disk has about 4.9 GB free.
- (idea panel; recorder branch state checked by the judge) The PRE1 borrow recorder has been dead since 11-05. Late cron runs exit outside 08:45-10:00 ET while showing "success", so about 15 sessions are lost.

## 4. Top 5 research directions (judge ranking; exact test and pass bar in ideas.json)
1. **CF-PRIMARY (8.0).** Test: Part A scores the overdue CF forward test from Testing 1/2 + On Deck "cost filter:" skip rows (10-30..11-25); Part B runs CF-15 and CF-LL15 (LIVE-L predicted cost ≤ 0.15R) on the E4 book in BASE, LO, LO+L3-OUT vs 500 same-share random removals and a constant cut. Pass (CHECK and T2 each): dR/day > 0; above random 95th pct with paired t ≥ 2.8 (global 3.93 shown); red days/month down ≥ 0.5; worst-5 ≤ 5% worse; best-day share < 25%; every Primary setup no worse than -2R/month.
2. **STOPX (7.0).** Test: Step 0 audits live stop slippage vs LR8's 4bp; Step 1 runs 3 configs (close-confirmed stop; + 2x catastrophe stop; 5-min close trigger). Pass (CHECK and T2): paired dR/trade > 0 with t ≥ ~3.4; ≥ 2/3 of setups improve; none worse by > 0.03R; worst-5 ≤ 5% deeper; best-day share < 50%.
3. **TAILEFF (6.5).** Test: LO, G1-3, LO+B8, LO+K4+SHOCK-V, LO+S8, LO+B8+K4 vs an exposure-matched constant cut on the Z/RAW/P books. Pass (Z book, both splits): tail efficiency E ≥ 1.25; 20-session floor and days ≤ -10R beat the matched cut; P book red days up ≤ 1/month and dR ≥ -40R/yr. E < 1 = a size cut in disguise.
4. **BORROW-FLIP (6.5).** Test: fix the recorder now (housekeeping); pre-register the ETB/shortable-flip study and score it once at 60 sessions. Pass: residual short net > 0, t ≥ 1.5, same sign on SPY-up and SPY-down days; as a filter, beats a random skip at the 95th pct.
5. **RESID-MAP (6.0).** Test: 20 pre-registered cells (4 checkpoints × 5 residual features), decile spread in bps net of LR8. Pass: > 0 on FIT, CHECK and T2; t ≥ 2.45; avg w/o best day > 0; best-day share < 50%; same sign on SPY-up and SPY-down days.

## 5. What the inspector would stop doing
- Stop putting "Yes" on cards without picking a reply option, and stop offering off-epoch options for Primary without naming the conflict.
- Stop reporting brakes and caps as passes without a size-matched random-cut and constant-cut control. On a losing book, trading less always "wins".
- Stop citing scratchpad paths as evidence. If a card cites it, it must be in git.
- Stop quoting live gains that include departed setups or stale partial-day bases.
- Stop re-ranking lineups and re-sizing on raw R. Rank persistence has failed 4 times.
- Stop running research and display jobs on the hard-coded 09:30-16:00 assumption. Use market_calendar everywhere.

## Appendix for Claude
- Tip 5b9bc5c599. Severities are the skeptic's corrected ones (original kept as `claimed_severity` in findings.json). Merged duplicates: #10 = integrity + engines scratchpad-evidence findings; #11 = livecode + ops intraday leak.
- Scratch evidence to commit (no parquets/paths.npy): /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/{neveragain,s8cap,hsscale,capfit,ticksel,pyramid}.
- Engine repros held: booksim gives BASE -40.1 / LO -8.3 on 11-25; latch timing, per-symbol cap form and exit-minute look-ahead change no decision; a 29% random block improves CHECK worst-5 only 7-14%, so B8's CHECK tail gain is more than trading less (T2 still uncontrolled).
- Rule-change context, window 10-23..11-25: 10-23 LL-LATCH, ST-A; 10-26/27 MF1 out, CWT13 in/out, ST7 in; 10-28 sizing; 10-29 -2R latch; 10-30 CF in Testing; 11-11 NM-ETF to Primary; 11-12 LR8; 11-17 TSZ1; 11-19 Epoch 1; 11-20 stop rounding; 11-21 cost-basis fix; 11-23 ST7 out + burst brake; 11-27 ROT-B3 and GYH V1/V3 moves (effective today).
