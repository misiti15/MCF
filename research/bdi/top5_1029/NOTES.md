*Educational only — not financial advice.*

# Top-5 execution tuning, 2026-10-29 — covered by today's larger swarms (no separate run)

Today's owner-ordered studies already tuned a superset of this routine's scope, on the same rules (costs in, locked
block never read in sweeps, every config counted, bar max(1.5, sqrt(2 ln N)), vs parent and random entries):

- **research/bdi/swarm15_1029** — the 15 most-traded live setups (all five accounts merged; this routine's top 5 by
  Primary + Testing trade count are all in it), 287 one-knob variants (stop, target/scale-out, time stop, entry window,
  market filter, re-entry cooldown, per-symbol cap, cost floor): **0 pass, 0 near-miss**. Wider stops at the same $ risk
  beat the parent on 36/39 rows and cost floors on 28/29, but every variant stays below zero after costs.
- **research/bdi/p1_1029** — Primary's top 3 short families (MF2-FD, RW5-FD, RW3-FD): 10-30 point stop / scale-out
  sweeps; wide stops beat the parent on RW3-FD and RW5-FD but still lose; backlog `p1_1029-primary-shorts-wide-stop`.
- **research/bdi/p3_1029** — cost filter A3 (stop-exit cost <= 0.15R) now in forward test in Testing 1/2 (CF, from 10-30).

Re-running the same grids tonight would only add configurations to the same lineages (raising their bars) without new
information, so this run adds **0 configurations**. Next run (10-30) rotates to setups not covered by swarm15_1029.
