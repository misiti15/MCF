# taileff_1127 — how to re-run (Educational only — not financial advice)
Inputs (not in git): W = a work dir holding cand.parquet + paths.npy built by `research/squeeze_1125/gen.py W sig1|walk1|t2`
then `research/hedgeb_1126/build.py W` (cwd = repo). Then, from this folder:
`python sim.py W RAW BASE,LO,G1-3,LO+B8,LO+K4+SHK,LO+S8,LO+B8+K4; python prep.py W avg;`
`python sim.py W Z <same>; python sim.py W P <same>; python prep.py W q RAW; python prep.py W q Z;`
random blocks: `python sim.py W RAW|Z RBLO~LO+B8~1127,...,RBLO~LO+B8~1146,RBLO~LO+B8+K4~1127,...`; `python score.py W`.
