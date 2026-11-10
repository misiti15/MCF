# Skeptic pre-score audits: CWT14SKIP and SC1 (2026-11-09 ~12:50 ET)

*Educational only — not financial advice.* Code reads only (no cache in this container); nothing scored.

## CWT14SKIP (research/cwt14skip/) — mostly clean
Checked: lab `fromOpen` is % ((c/open-1)*100, mcf/research/heat.py:73), `tod` is the bar END (heat.py:75), `atr_d` uses
prior days only (heat.py:77), so `dist` is point-in-time at the entry bar close. Same-day random-block control removes
market direction. Asks (reporting, no new configs):
1. **Stratify the random block by variant** (same day, same variant, same count). Variants differ in mean R (orl vs pdl,
   p05 vs p10); if skips fall mostly on the weaker variant, an unstratified block credits variant mix, not the rule.
2. **Retention per variant**, not only pooled: a pooled 80% can hide one variant losing 40% of its trades.
3. **Frame-join misses** become "kept" (NaN -> not skipped). Report the missing share by variant and month; if > 2%,
   rerun with misses dropped from both sides.
4. **Down-day dependence:** "already >= 1 ATR below the open" is far more common on down days. Report excess and skip
   counts by up / down / quiet, and say if the up-day excess is negative.
5. Motivation came from 6 live sessions (11-04 = 42% of the wrong-way R); the 2-year lists are the real test. Any forward
   tally starts 11-10.

## SC1 (research/sc1/) — path clean, two realism gaps on big gaps
Checked: event proxy uses volume through the 09:55 bar (known before T 10:00); hold test on the bar close T; entry next
bar open; LOD/HOD stop from bars <= T; trail uses closed bars, applied from the next bar; prior close masked after the
locked gap; opening-volume norm restarts after the gap.
1. **Short-sale restriction (Reg SHO 201):** a name down >= 10% from its prior close can only be shorted on an uptick for
   the rest of that day and the next. SC1-S gap <= -6% often trips it (and every > 10% gap-down has it on at the open).
   Market-style short entries at the next bar open are not realistic there. Report the short side with the > 10%
   bucket (and any name that touched -10% before entry) split out, and treat that bucket as not tradable as modeled.
2. **Halts / 5-min stop fills:** event names halt (LULD). A stop inside a 5-minute bar fills at the stop price even if the
   1-minute path gapped through it after a halt. Report the stop fills re-priced on 1-minute bars (gap-through at the
   1-minute open), at least for the > 10% bucket.
3. **C1 (failed-hold gaps, same side) is not a neutral baseline:** failed holds are fades by construction, so r - C1 is a
   hold-vs-fail spread and will look strong even with no edge. Keep it descriptive; the pass rightly uses C2.
4. Borrow: hard-to-borrow event names cannot always be shorted; state it next to any short result.
5. Survivorship: today's lab list misses names that gapped down and were later delisted; matters most for SC1-S.

Would convince me (SC1-L, the long side Lead wants): C2-excess t >= 1.84, TRAIN and VALID > 0, positive on up AND down
days, avg R w/o best day > 0, results holding in the 4-6% bucket (not only > 10%), and 1-minute stop re-pricing
changing avg R by < 0.03R. Then forward sessions from the pre-registration date.
