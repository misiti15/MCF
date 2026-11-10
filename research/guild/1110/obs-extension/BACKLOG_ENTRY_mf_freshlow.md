Educational only — not financial advice.

# Backlog-ready entry (for Lead to route): MF flow-sell short — skip a fresh-low entry (Observer, 2026-11-10 ~00:00 ET)

**Status: idea, weak live evidence. The 2-year lab run decides.** Remedy type: entry timing (targeted, one family), not a new setup.

## Rule (exact, point-in-time)
For an entry of any setup in the MF flow-sell SHORT family (MF1/MF2/MF3/MF4/MF5 incl. -FD; modules research/bdi/fullday/MF*-FD.py and
the Primary/Testing originals), skip the entry when BOTH hold at the signal bar (closed 1-min bars before the entry minute):
- the session low (09:30 onward) was set within the last 15 minutes, and
- (entry ref price - session low) <= X x daily ATR (ATR = mean daily true range of the prior 10 sessions, >= 5 required),
- X in {0.10, 0.20} -> **2 configs**. Lineage: obs-extension's 2 live looks (counted) -> family N 4 -> BAR90 1.67.
  If Lead prefers the conservative reading, add GATE2's market-extension looks; that is Lead's call.

## Scoring (pre-declared)
- Sample: MF family 2-year lab lists (bt_lab1104 / bereplay loader), locked block excluded, production costs, next-bar entry.
- Pass: excess t over a **same-variant, same-day random skip block of equal size** (200 draws) >= bar; TRAIN and VALID excess > 0;
  w/o best day > 0; up AND down days not negative; GROSS first (Lead's standard).
- Retention (BDI charter): keeps >= 80% of each variant's trades and >= 90% of its top-decile winners, per variant.
- Per-variant table: n, skipped n, skipped avg gross R, kept avg gross R, excess, better/worse (Remedies rule), cost/R before/after.
- Forward: tally from the day after freezing in a shadow line only.

## Live evidence (descriptive; extension_out.txt and the within-setup cut below; 18 sessions 10-14..11-06)
Within setup, EXT (0.10 ATR) vs the rest, gross R:
| setup | EXT n | EXT gross | rest gross |
|---|---|---|---|
| MF2-open-rsimidhi-flowsell-FD | 19 | -0.477 | ~+0.29 (MID +0.365 n74, PB +0.040 n24) |
| MF2-open-rsimidhi-flowsell (Primary) | 10 | -0.261 | 3 trades |
| MF4-h40-open-flowsell-FD | 24 | -0.343 | ~-0.03 (MID -0.085, PB +0.008) |
| MF1 / MF3 / MF5 | 0-1 | — | (no fresh-low entries: rule would barely touch them) |
Caveats: ~53 EXT trades, 7 days carry them, the worst day is 72% of the EXT loss. Concentrated. **Correction:** the board post called
RW3 part of this; within setup RW3S's EXT trades did *better* (-0.12 vs MID -0.33). The 'RW3' family number was a mix of two setups.
RW is dropped from the entry.
