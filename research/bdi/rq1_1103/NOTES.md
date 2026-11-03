Educational only — not financial advice

# RQ1 + REG1 (owner 2026-11-03 ~07:45 ET): the replay's 10-session audit, and what the 10:00 fade switch did on replays

Research only. No change to `config/`, setups, exits, the live path, the ledger or the backlog; nothing merged. Costs in
everywhere (the production cost layer on top of Alpaca-paper fills, applied the same way to live and replay trades). The
locked block was never loaded (sessions 2026-08-24..2026-11-02 only). Disk was tight, so a rolling store was used
(fetch a session, replay it, delete it; ~30 MB per full-universe session); the store was deleted at the end.

## Short answer

1. **RQ1: the fixed replay passes rule 21 for Primary on 10 sessions. Testing 1 and Testing 2 pass on the 5 clean
   sessions but miss on 10.** The fixed replay = full live universe + the quotes and borrow answers live recorded (night1102
   config FB). Results:
   - **Primary, 10 sessions: 99.5% trade match, avg R gap −0.018. Pass.**
   - **10 sessions, all three accounts:** Testing 1 94.1% / +0.007 and Testing 2 94.4% / +0.036 (optimistic). Both fail.
     Overall 94.9% / +0.021 fails by 0.1 point.
   - **5 sessions since the GX1 fix (10-27..11-02):** Primary 99.1% / −0.023, T1 99.2% / +0.010, T2 97.9% / +0.030
     (right at the edge), overall 98.5% / +0.019. All pass.
   - **Where T1 and T2 fall short:** almost all of it is 10-20..10-22. Before 10-27, live ran with the lab-gate bug
     (`len(bars) % 5`). The replay copies that bug with the same monkeypatch the GX1 study used. For Primary the copy
     reproduces live 99.7% of the time. It does not reproduce T2's refire / CWT setups (590 replay-only trades flagged
     "no live signal (gate era)"), and on 10-20 it does not reproduce T1's per-setup −2R latch timing.
   - **What this does not show:** the bug era is a weak test of today's replay. Five more live sessions (11-03..11-07,
     one replayed each night) would give 10 clean sessions for T1 and T2. Graveyard and Gen were not run (time, CPU and
     disk). They are not cleared.
2. **REP-Q1 (historical quotes for a new setup, no recordings): close to passing on 3 sessions.** This is the "new setup"
   input: SIP NBBO at the replay poll time + the account's live delay, and other accounts' borrow answers only.
   - **Result (10-29, 10-30, 11-02):** 94.8% match / +0.028. Primary 100% / +0.120 (43 trades, 10 extras: optimistic),
     T1 97.2% / +0.009, T2 92.9% / +0.038.
   - **Compared with:** the old new-setup configuration (FC) got 83.3%, and recorded quotes (FB) get 98.8% / +0.025 on the
     same three sessions.
   - Three sessions are not an audit. This is the next thing to run to 10 sessions.
3. **REG1: switch A on replays re-tells the live result and adds no new evidence. On sessions live never traded it is
   weak, and it is carried by one day.**
   - **Replay of the 10 audit sessions (10-20..11-02):** kept +31.2R vs all −6.8R, beat-random +35.5R, t 1.19. Live on
     the same sessions: +40.5R vs +0.6R, t 1.30.
   - **These are the same days as the live sample.** The replay matches live 99.5% on Primary, so it repeats live by
     construction. It is **not independent evidence**, and both versions lean on 10-22 (kept R share 154–195%; kept avg
     R without 10-22 is −0.14 / −0.19).
   - **Independent sessions:** 30 pre-live sessions (08-24..10-05), Primary's current 10 setups and config. Kept +7.7R vs
     all −25.2R, beat-random +20.0R, **t 0.51**. One session (08-28) carries 533% of kept R. Without it, kept avg R is
     −0.053 and beat-random is −2.6R.
   - **Split by side (independent sessions):** shorts t 0.76. **On longs the switch hurts:** it drops +0.27R-average
     longs, t −1.15.
   - **Rule 21:** replays never count toward a decision. These numbers are context only.
4. **Recommendation for the 5-session test: a journal-only shadow on Primary (option S below), not a copy in a Testing
   account.**
   - **The evidence does not show a "positive benefit"** that would justify putting copies of Primary's setups into a
     Testing account: live t 1.45 and replay t 1.19 on the same days, independent replay t 0.51, two-year VALID t 0.62,
     and every version carried by one session.
   - **A shadow measures almost the same thing at no risk.** A copy would take the same signals and get similar fills.
   - **Five sessions cannot decide it either way.** Even if live's effect were real, the chance of t ≥ 1 in 5 sessions is
     about 40%.
   - **What the 5 sessions can show:** whether the pattern breaks. They should feed the 20-session forward rule already
     on file (`regime1102-fade-1000-forward`).

## 1. RQ1 — rule-21 audit (replay vs live), fixed replay FB

Bar (rule 21): ≥ 95% of live trades matched (same setup + symbol + decision minute), avg R after costs within ±0.03 of live
per account and overall, never optimistic (replay better than live by > 0.03R fails).

**What was run.** Inputs: the real `PaperRunner` via `mcf.replay.harness.run_session`, frozen `setups/<d>.json`, the
account config committed before that open, the full live universe (~4,840 names, live-prep priors from the real historical
client: `night1102/replay/prep_full.py`), the NBBO live journaled at symbol + minute, and the borrow answers live recorded
(`night1102/replay/recorded.py`). Fills = Alpaca paper, limits touch.

**Sessions.** The 10 most recent sessions with recordings: 11-02, 10-30, 10-29, 10-28, 10-27, 10-26, 10-23, 10-22, 10-21,
10-20.
- **Before 10-27 (the old gate):** live ran the pre-GX1 lab gate, so those replays use the same old-gate monkeypatch as
  `research/ops/gx1clockgate1026_oldgate.py`.
- **10-26 (late start):** every live account started at ~10:39, so that replay's clock starts at 10:39.

**Totals.** 30 account-sessions (Primary, T1, T2), 0 errors. Configurations: FB (10 sessions) and FHB (3 sessions).

| account | sessions | live trades | replay trades | **match** | live avg R | replay avg R | **gap** | rule 21 |
|---|---|---|---|---|---|---|---|---|
| Primary | 10 | 411 | 414 | **99.5%** | +0.001 | −0.017 | **−0.018** | **pass** |
| Testing 1 | 10 | 1,450 | 1,434 | 94.1% | −0.172 | −0.165 | +0.007 | fail (match) |
| Testing 2 | 10 | 1,558 | 2,168 | 94.4% | −0.126 | −0.090 | +0.036 | fail (match, optimistic) |
| **overall** | 30 | 3,419 | 4,016 | 94.9% | −0.130 | −0.109 | +0.021 | fail (match by 0.1 pt) |
| *post-fix 5 (10-27..11-02)* | | | | | | | | |
| Primary | 5 | 115 | 118 | 99.1% | −0.136 | −0.159 | −0.023 | pass |
| Testing 1 | 5 | 605 | 616 | 99.2% | −0.246 | −0.236 | +0.010 | pass |
| Testing 2 | 5 | 904 | 939 | 97.9% | −0.186 | −0.156 | +0.030 | pass (at the edge) |
| overall | 15 | 1,624 | 1,673 | 98.5% | −0.205 | −0.186 | +0.019 | pass (5 sessions only) |
| *pre-fix 5, old gate emulated (10-20..10-26)* | | | | | | | | |
| Primary | 5 | 296 | 296 | 99.7% | +0.055 | +0.040 | −0.015 | pass |
| Testing 1 | 5 | 845 | 818 | 90.4% | −0.119 | −0.111 | +0.008 | fail (match) |
| Testing 2 | 5 | 654 | 1,229 | 89.6% | −0.043 | −0.039 | +0.004 | fail (match; 643 extras) |

**Per session.** Primary matches 98.3–100% every day. Its daily gaps run from −0.13 to +0.14 on 12–126 trades and they
average out. T1 is 98.1–100% on every day except 10-20 (71.1%). T2 is 96.2–99.2% on every post-fix day and 74.6–94.4%
on 10-20, 10-21, 10-22 and 10-26.

**Where the misses come from (10 sessions).**
- **Testing 1, 10-20 (missed live trades):** the replay's per-setup −2R latch (T1 had it from 10-19 to 10-22) fired where
  live's did not. That accounts for 66 of T1's 85 missed live trades, and it is path dependent.
- **Testing 2, 10-20..10-22 (replay-only extras):** 590 replay-only trades with no live signal. They come from CWT09 /
  CWT12 / CWT14 / RW2 refire setups (e.g. 10-20: replay 930 signals vs live 259). Copying the old gate does not reproduce
  how live missed refire chains. There is no poll log for 10-20 / 10-21 to check against.
- **After the fix, the replay-only extras are small:** −2R latch timing, broker rejects, caps.
- **Matched trades:** the R difference is −0.015 (Primary), +0.017 (T1) and +0.001 (T2).

**Verdict per rule 21.**
- **Primary is cleared with recorded inputs** (10 sessions: ≥ 95%, gap within ±0.03, not optimistic).
- **Testing 1 / Testing 2 are not cleared on 10 sessions.** They are cleared on the 5 post-fix sessions, which is fewer
  than rule 21's minimum.
- **Graveyard / Gen were not run.** Night1102 found a live journal gap in Gen on 11-02 (39 market entries with no trade
  row), which still needs the ops check.

What a clearance means here:
- **It covers sessions live traded and recorded.** A new setup has no recordings; that is the REP-Q1 configuration below.
- **Even after clearance, rule 21 makes a replay a filter only, never a record.**
- **The simplest clean way to finish T1 / T2:** replay each new session the night after it trades (11-03, 11-04, …). That
  gives 10 post-fix sessions by 11-09 with no bug-era emulation.

### REP-Q1 — historical quotes for signals with no recording (`hq.py`, run.py conf FHB)

**Method.**
- **Pass 1:** the FB replay; its quote-checked signals give the (symbol, poll time) list.
- **Quotes:** for each, the last SIP NBBO at or before (replay poll time + the account's median poll-to-submit delay:
  Primary 28 s, T1 22 s, T2 56 s). One read-only GET per quote; 31–256 per account-session; 0 missing.
- **Pass 2:** replays with those quotes and **only the other accounts'** borrow answers. Quote requests that pass 1 did
  not make fall back to the synthetic draw (0–4 per session).

| 10-29 + 10-30 + 11-02 | live trades | FB match / gap (recorded) | **FHB match / gap (historical)** | night1102 FC (nearby recordings), 10-30 + 11-02 |
|---|---|---|---|---|
| Primary | 43 | 100.0% / −0.004 | **100.0% / +0.120** (10 replay-only extras) | 88.9% / +0.044 |
| Testing 1 | 254 | 99.2% / +0.019 | **97.2% / +0.009** | 91.2% / −0.011 |
| Testing 2 | 451 | 98.4% / +0.034 | **92.9% / +0.038** (spread disagreements both ways) | 88.7% / +0.007 |
| overall | 748 | 98.8% / +0.025 | **94.8% / +0.028** | 83.3% / +0.064 (all 5 accounts) |

Historical quotes recover most of the gap between "new setup" inputs and recorded inputs. Two things remain:
- **Spread decisions:** they still disagree on about 4% of T2's trades.
- **Primary's extras:** 10 extras over 3 sessions are optimistic (+0.12R on 43 trades).

Next steps: run FHB on 10 sessions; check whether the delay offset should be per symbol rather than per account; then
judge it against rule 21 on its own.

## 2. REG1 — switch A on the Primary book

**Switch A** (pre-declared in `night1102/regime/PLAN.md`):
- Trades entered before 10:00 ET are untouched.
- After 10:00, a short is **kept** only if SPY's 09:59-bar close is at or above SPY's 09:30 open; a long is kept only if
  it is below. Everything else is **dropped**.

**Scoring.** "Beat-random" = kept R − total R × kept share, with a day-clustered t. Trades are only tagged, not removed,
so slots or a −2R latch freed by a dropped trade are not modelled (second order for Primary at 12–16 trades a day).
`reg1.py`, `reg1_results.json` (incl. per-day tables).

| book | sessions | trades | all R (avg) | kept R (avg) | dropped R (avg) | kept % | beat-random (t) | best kept session (share of kept R) | kept avg R w/o best session | beat-random w/o best |
|---|---|---|---|---|---|---|---|---|---|---|
| **live, 10-06..11-02** (R = pnl_adj, regime's definition) | 20 | 761 | −32.1 (−0.042) | **+43.3 (+0.106)** | −75.4 (−0.213) | 53% | +60.5 (**1.45**) | 10-22 (163%, `1 day`) | **−0.091** | +25.0 |
| live, same 10 audit sessions (R = r_multiple − cost layer) | 10 | 411 | +0.6 (+0.001) | +40.5 (+0.153) | −39.9 (−0.271) | 64% | +40.1 (1.30) | 10-22 (154%, `1 day`) | −0.141 | +13.7 |
| **replay FB, same 10 audit sessions** | 10 | 414 | −6.8 (−0.017) | **+31.2 (+0.118)** | −38.0 (−0.253) | 64% | +35.5 (**1.19**) | 10-22 (195%, `1 day`) | **−0.190** | +10.8 |
| **replay, 30 independent sessions 08-24..10-05** (current Primary setups) | 30 | 1,444 | −25.2 (−0.017) | **+7.7 (+0.011)** | −32.9 (−0.045) | 49% | +20.0 (**0.51**) | 08-28 (533%, `1 day`) | **−0.053** | **−2.6** |
| — independent, shorts only | 30 | 1,242 | −47.0 (−0.038) | +6.0 (+0.010) | −53.0 (−0.080) | 46% | +27.8 (0.76) | 08-28 (690%) | −0.070 | +5.7 |
| — independent, longs only | 28 | 202 | +21.8 (+0.108) | +1.8 (+0.014) | +20.1 (**+0.271**) | 63% | **−12.1 (−1.15)** | 09-10 (191%) | −0.013 | −13.3 |

**Independent or the same days?**
- **The 10 audit replays are the same days as the live sample** (all inside 10-06..11-02). They match live trade for
  trade, so they re-tell live and add no evidence. Their slightly lower t (1.19 vs 1.30) is fill noise.
- **The 30 sessions before 10-06 are new days for the live engine.** No Primary account traded them. They are
  **not new to the research, though**: they sit inside the two-year VALID window (2026-01-01..10-05) where A already
  scored t 0.62. They are also **replay results under inputs not cleared by rule 21**: lab universe, synthetic spread
  draw, default borrow flags, no earnings blackout on record; night1102's config A matched Primary 72–78%.
- **What they show:** the same story as the two-year check. A small edge on shorts on up-at-10:00 days, all of it from
  one session, and it costs money on longs.

**Day by day on the independent sessions.**
- **SPY was up at 10:00 on 14 of the 30 days.** The switch beat random on 15 of 30.
- **The 08-28 up-day** had shorts kept at +41R. Remove it and nothing is left.
- **Live:** the beat-random edge came from 10-06..10-28 (t 1.30, 17 sessions). 10-29..11-02 (3 sessions, after the
  Primary −2R latch and the ~$4k size) is +6.2R, t 1.07, on 43 trades.

**Rule / config changes inside these windows** (`research/ledger.jsonl`; results mix these periods):
- **Live and audit sessions:**
  - 10-21 / 10-22 / 10-26 / 10-30: Primary promotions and demotions (L3-fromopen-FD in, out on 10-22, back in on 10-30;
    CWT14-pdl-p10-lowvol, MF3-FD, NS3-FD, RW6G1, MF1, CWT13-z05-long, ST7-FD, L3-rsi5hi-FD).
  - 10-23: per-setup −2R latch off in Testing / Gen (it was on in T1 / T2 from 10-19).
  - **10-27: GX1 5-minute clock gate (all accounts).**
  - **10-28: Primary size ~$4k (slots 77, per-setup 30)**; rotations CWT14-pdl-p10-lowvol, NS4-pm and MF2-base out.
  - **10-29: Primary per-setup −2R daily stop (latched).**
  - 10-30: Testing cost filter CF and BAR90.
  - 11-02: Graveyard moves.
  - Primary averaged ~42 trades per session before 10-29 and 12–16 after.
- **The audit replays use each session's own frozen setups and config,** so replay and live are always under the same
  rules.
- **The independent replay uses one fixed config:** today's Primary (10 setups, slots 77, −2R latch), so no rule changes
  fall inside it. Its trade rate (48 per session) is higher than live's because no earnings blackout was applied.

## 3. Design — "test it over a Testing account for 5 sessions" (not built, not merged)

### Option S — journal-only shadow on Primary (recommended)

**What it is.** No trading change. After each close, tag every Primary trade kept or dropped by A and keep the running
table: kept / dropped / all R, beat-random t, kept avg R without the best session, best-session share. Optionally tag the
T1 / T2 books as a second read.

**Config pieces: none.**
- Research code only: a nightly runner around `research/bdi/rq1_1103/reg1.py`. It reads `origin/mcf-data:journal.db` and
  SPY 1-minute SIP bars (read-only GETs).
- A results file (e.g. `research/bdi/rq1_1103/shadow.jsonl`, one row per session).
- One owner-inbox FYI line per night.
- The backlog entry `regime1102-fade-1000-forward` already exists for the 20-session rule.

**Risk: none to trading.**
- **Limit:** it does not model the slots or the −2R latch that dropped trades would free up. For Primary that is second
  order: 12–16 trades a day against 77 slots, and the latch fires later only when losers are dropped.
- **Limit:** like any 5-session read, it is underpowered.

**Pre-declared reading for the 5 sessions (11-03..11-07).** "Positive benefit" only if all three hold:
1. dropped avg R < kept avg R;
2. beat-random > 0;
3. no single session carries ≥ 50% of the beat-random R.

This reading only says whether the pattern held. Any Primary change still waits for the 20-session forward rule on file:
dropped below kept, beat-random t ≥ 1.0, kept avg R > 0 without its best session, on the new sessions alone.

**Starts:** tonight, with the 11-03 session. Nothing to merge, so no setup-freeze issue.

### Option T — constant-size copy of Primary's current setups in one Testing account, switch applied; Primary as the control

**Config pieces (all of them):**
1. **A wrapper lab module per setup, or one generic wrapper.** Each takes the original module's `mask` and ANDs in A. It
   reads SPY's `spy_fo` (lab context, `mcf/strategies/lab_context.py`: SPY from the first 5-minute open to that bar's
   close) at the 09:55–10:00 bar of the same date, which is exactly A's state. Shorts are allowed only if it is ≥ 0, longs
   only if < 0. A missing value leaves NaN, which is False, so the setup fires nothing (fail safe). All 10 current Primary
   setups are `type: lab`, so all can be wrapped: L3-fromopen-FD, L3-rsi5hi-FD, ST7-FD, RW5-FD, RW3-FD, MF2-FD, MF4-FD,
   MF4-base, NS1, NS5.
2. **10 entries in `config/account_testing.yaml` or `config/account_testing2.yaml`** (equal weight, either is fine). Each
   copies the Primary entry (module → wrapper, `min_adv`, `prefilter`, `refire`, `refire_cooldown`, `geom`) and adds
   `context: [spy_fo]` and a name suffix `-A10`. The window is **[1000, 1500]** (NS1 / NS5 [1000, 1130], MF4-base
   [1000, 1100]): trades before 10:00 are identical to Primary's, so copying them only uses slots.
3. **Tests:** the wrapper is point-in-time (`tests/test_lab_context.py` style); assignments.
4. **Paperwork:** a `research/backlog.jsonl` entry (rules 15–17: a setup idea goes to the backlog first) and a
   `research/ledger.jsonl` entry re-checked with `python -m mcf.research.ledger check`. `docs/live/assignments.json` is
   regenerated in the same commit (`python -m mcf.report.assignments`).
5. **Merge timing:** merge outside 09:30–16:00 (`setup-freeze`). First session 11-04; 5 sessions = 11-04..11-10.
6. **Owner confirmation that these copies are wanted.** "Promotion = move" forbids running a setup as a copy in two
   accounts unless the owner asks. REG1 reads like that ask, but it should be confirmed.

**Risks:**
- **The control is not clean.** Testing runs the CF cost filter (`max_stop_cost_r 0.15`) and has the per-setup −2R latch
  off; Primary has no CF and has the latch on. Testing also has 400 slots and a per-setup cap of 150 / 50, against 77 /
  30. So "copy minus Primary" mixes the switch with those rules unless the comparison is done trade by trade on matched
  signals, which the shadow does anyway.
- **Position size differs** (~$950 vs ~$4k). R is per trade, so this is mostly cosmetic, but share rounding differs.
- **Doubled exposure:** the same names in two paper accounts.
- **New code on the live path** (a wrapper module) with a 5-session payoff. If the wrapper is wrong, it fires the wrong
  side or nothing.
- **The Testing account's record gets 10 temporary entries.**
- **Five sessions cannot decide it,** and the first usable session is 11-04, a day later than the shadow.

### Option P — apply A on Primary itself

Not asked for and not recommended. The evidence (one-day carried, t 0.51–1.45, two-year VALID fail) is below Primary's
full bar.

**Recommendation:** Option S from tonight for 11-03..11-07, reported with this table. Build Option T only if the owner
specifically wants it to run live as orders. In that case use one Testing account, after-10:00 windows only, and the
pieces listed above, and confirm the copy exception first.

## Files

`run.py` (FB / FHB with the old-gate and late-start patches; wraps `night1102/replay/run.py`), `hq.py` (historical NBBO),
`indep.py` (Primary current config on pre-live sessions), `reg1.py` (switch A scoring), `results.json` (FB 10 sessions,
FB_postfix5, FB_prefix5_oldgate, FB_same3, FHB: per account and per day), `reg1_results.json`.

Reproduce:
1. Build the full store: `MCF_REPLAY_STORE=<store> python research/bdi/night1102/replay/prep_full.py data/replay <day>`.
2. Replay: `python run.py FB <day> --accounts testing2,testing,primary --journals <dir of the five journal.db copies>`.
3. Historical quotes: `python hq.py <store>/runs/rq1_1103/FB <journals> <day> primary,testing,testing2`, then
   `run.py FHB <day> ...`.
4. Compare: `python research/bdi/night1102/replay/compare.py <store>/runs/rq1_1103 FB --full-universe <store>/universe`.
5. Independent sessions: `MCF_REPLAY_STORE=<lab store> python indep.py 2026-08-24..2026-10-05 --out <dir>`.
6. Switch A scoring: `python reg1.py <scratch>`.

Scratch (journals, bars, priors, replay outputs) was deleted after the run.

Configurations counted: 2 replay input configurations (FB on 30 account-sessions, FHB on 9) + 1 independent replay
(30 sessions). Switch A is the single pre-declared rule, scored on 4 books, plus 2 side splits and 2 rule-change
sub-windows. No new switch was searched.
