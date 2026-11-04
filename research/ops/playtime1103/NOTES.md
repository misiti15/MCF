Educational only — not financial advice

# playtime1103 — are any setups starved by account capacity? (owner GY-BP refined, 2026-11-03)

Research / ops only. Nothing in `config/`, the trading path, the ledger or the backlog was changed. Window: sessions
2026-10-27..2026-11-03 (6 sessions; journals pulled after the 11-03 close). Costs in everywhere (production layer:
$0.01/sh + 1 bp per side, +$0.02/sh on stop exits, no exit cost on target fills).

## Answer: no account starves a setup. No change.

- **Starved** here means a signal turned away for capacity: buying power, slots, the per-setup cap or the scale-out
  cap. It excludes borrow/ETB, spread/realism, the cost filter, twin / opposite side / lot cap, the −2R daily latch and
  setups that are rare by design.
- **Primary, Testing 1: 0** capacity blocks.
- **Testing 2: 1** per-setup-cap skip (CWT12-coil-k4-long 10-27 11:30, what-if +0.5R).
- **Slots (max concurrent): 0 in every account.**
- **Scale-out cap (T1/T2, 2 a day):** never blocks an entry. When it binds, the lot keeps its bracket (the runner log
  only), so it cannot starve a setup's signals.
- **Generated:**
  - per-setup cap: 14 skips across 2 setups (GEN-261020-07 9 on 10-29 from 10:45; GEN-261021-06 5 on 11-02 from 11:50),
    what-if −7.4R;
  - buying power: 12 rejects, all on 10-30 at 14:35-15:00 (the HK-RECON booking lag, not real capacity), +8.0R.
- **Graveyard is the only account where capacity binds.** It trims; it does not starve:
  - **per-setup cap (25):** 502 skips, 11 setups, what-if **−96.5R**. Most of it is CWT12-coil-k4 (194, −70.9R),
    CWT14-orl-p05 (114, +3.5R), CWT14-orl-p05-lowvol (83, −1.6R), CWT09-vwaploss (54, −45.4R) and CWT09-bounce
    (32, +23.8R). It starts as early as 09:50-10:40.
  - **buying power:** 101 rejects, 17 setups, what-if **+2.7R**. They come on 10-28 (2, 11:30), 10-29 (2, 11:05),
    11-02 (38, 10:40-10:59) and 11-03 (59, 10:50-11:59). Buying power runs out at about 10:40-10:50 and comes back
    within about an hour as lots close.
  - **Every capacity-hit setup still traded in every session it was enabled.** The only setup-session with 0 trades and
    a buying-power reject is CWT09-vwaploss on 11-02: 1 reject of 20 signals; 13 of the others were not shortable.
  - The most-hit on buying power were MF3-FD (6 of 33 signals) and MF5-FD (8 of 24) on their first Graveyard day,
    11-03 (what-if +5.0R / +5.9R). That is one session: watch it, no action.
- Tables: `starve.csv` (account × setup × block kind: count, sessions, first / median time, trades and signals in the
  window, what-if R) and `starve_time.csv` (account × session: first buying-power reject and first cap skip).

## Replays (Graveyard, Gen): today's rules vs per-setup cap 12 vs rotation

**Configurations tried: 3** (V0 / V1 / V2), all fixed before any result was read. There is also 1 input
model (the buying-power ceiling below). Every result is reported.
- **V0 (today's rules):** the frozen setups and the config at each open.
- **V1 (cap 12):** max_positions_per_strategy → 12. Graveyard 25 → 12. Gen gets the same absolute cap (48 → 12).
- **V2 (rotation):** the account's top 3 setups by live trade count are benched (whole sessions off) on 10-27, 10-29 and
  11-02. Benched setup-sessions have no trades and are left out of per-session stats.
  - Graveyard: CWT14-orl-p05, CWT14-orl-p05-lowvol, CWT12-coil-k4.
  - Gen: GEN-261021-06, GEN-261020-07, GEN-261022-07.

**How the replays were run:**
- **Runner:** the real PaperRunner (`mcf.replay.harness.run_session`), Alpaca-paper fills, limits fill on touch.
- **Graveyard = night1102 "FB":** full live universe (~4,700-4,880 names) plus the NBBO and borrow answers live
  recorded.
- **Gen = "B" (lab universe ∩ live, recorded quotes and borrow):** CPU forced this. One full-universe Gen session took
  about 39 min. The 10-27 full-universe Gen runs are in the store but not used.
- **Buying power:** the simulated broker never rejects for buying power. Each Graveyard session therefore gets a ceiling
  on gross open notional (plus working entries), calibrated from live: gross open at the first live reject plus the
  buying power Alpaca reported in that reject. The ceilings are $263k / $208k / $242k / $232k on 10-28 / 10-29 / 11-02 /
  11-03, with no ceiling on 10-27 or 10-30. **It over-binds:** V0 gives 318 rejects vs 101 live, mostly 10-29. Gen has no
  ceiling.

| variant | acct | trades | setups with ≥1 trade after 10:45 (window / per session) | total R | avg R | avg R w/o best day |
|---|---|---|---|---|---|---|
| live | GY | 2,269 | 27 / 16.5 | −440.1 | −0.194 | −0.211 |
| V0 today | GY | 2,255 | 28 / 17.3 | −370.5 | −0.164 | −0.182 |
| V1 cap 12 | GY | 1,927 | 27 / 16.7 | −291.6 | −0.151 | −0.171 |
| V2 rotation | GY | 1,909 | 28 / 15.7 | −352.3 | −0.185 | −0.212 |
| live (lab names) | Gen | 839 | 52 / 15.7 | −293.0 | −0.349 | −0.403 |
| V0 today | Gen | 836 | 53 / 15.2 | −274.7 | −0.329 | −0.382 |
| V1 cap 12 | Gen | 648 | 53 / 15.0 | −193.8 | −0.299 | −0.350 |
| V2 rotation | Gen | 663 | 53 / 14.2 | −198.4 | −0.299 | −0.330 |

- **Best-day share is not defined:** every total is negative. The best days are GY 11-03 (replay) / 10-29 (live) and Gen
  10-27.
- **Playing time does not improve.** Leave out the top 3 setups and count the *other* setups with a trade after 10:45
  per session (`late_ex_top3.csv`):
  - GY: V0 15.0, V1 14.3, V2 14.7;
  - Gen: 13.5 in all three variants.
  - Neither variant gives more turns to the quieter setups.
- **The R "gain" of V1 / V2 is fewer trades of losing setups** (V1 vs V0: GY +79R, Gen +81R; V2: GY +18R, Gen +76R).
  It is not more playing time. A demotion question like this belongs to the normal live review, not a capacity fix.
- **Fidelity (Graveyard and Gen are not cleared by the rule-21 audit):** GY V0 matches the live trade count (2,255 vs
  2,269) but is +0.030R optimistic on average. Gen V0 is 836 vs 839 trades on lab names, +0.020R. **Rule 21: these
  replays are context only and count toward no decision.**
- **Daily R by variant:** `variants_day.csv`. Summary: `variants.csv`.

## Rule / config changes in effect inside the window (research/ledger.jsonl effective dates)

- **10-27:**
  - GX1 5-minute lab clock (all accounts);
  - session guard;
  - setup-load guard;
  - CWT12-coil-k6 → Graveyard (D3);
  - CWT13-z05-long → Testing 2.
- **10-28:**
  - Primary size ~$4k (77 slots, per-setup 30);
  - rotations: CWT14-pdl-p10-lowvol, NS4-pm, MF2-base.
- **10-29:**
  - Primary −2R per-setup stop (ST-P);
  - generator paused;
  - CWT12-coil-k4 → Graveyard (K4-2);
  - BAR90;
  - REPS.
- **10-30:**
  - Testing 1/2 cost filter CF;
  - CWT14-pdl-p05 (+lowvol) → Graveyard (D1/D2);
  - L3 rsi5hi-FD / fromopen-FD → Primary.
- **11-02:**
  - R2A legs into Testing 2 (PDL-1a);
  - NS3-FD / RW4-FD → Graveyard (DM-NS3).
- **11-03:**
  - MF3-FD / MF5-FD → Graveyard (DM-MF);
  - SO-1A (R2A legs scale-out cap exempt);
  - RW3S into Testing 2.
- **From 11-04 (after the window):** DM-N3 adds NS5-FD, ST4-FD and RW6G1-FD to the Graveyard. That is more load on its
  buying power from tomorrow. Re-run `starve.py` after 11-06.
- **Effect on the counts:** Graveyard capacity counts before and after 10-29 / 10-30 / 11-02 / 11-03 cover a growing setup
  list (CWT12-k4 from 10-29, so its 194 cap skips are over 4 sessions). The ET clock moved from EDT to EST on 11-01.

## Re-run

```
S=<scratch>; for b in mcf-data mcf-data-testing mcf-data-testing2 mcf-data-gen mcf-data-graveyard; do
  mkdir -p $S/j/$b; git show origin/$b:journal.db > $S/j/$b/journal.db; ln -sf $S/j/$b/journal.db $S/jd/$b.db; done
python research/ops/playtime1103/starve.py $S
MCF_REPLAY_STORE=$S/store python research/ops/playtime1103/prep.py 2026-10-27 ... 2026-11-03
PYTHONPATH=.:research/bdi/night1102/replay MCF_REPLAY_STORE=$S/store python research/ops/playtime1103/run.py V0,V1,V2 \
  2026-10-27..2026-11-03 --accounts graveyard --journals $S/jd        # and --accounts gen --conf B
MCF_REPLAY_STORE=$S/store python research/ops/playtime1103/compare.py $S/j
```

Educational only — not financial advice.
