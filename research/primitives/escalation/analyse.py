"""Summarise search results per family / window. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
fams = sys.argv[1:] or ["gapfade", "bottom", "orbext", "failbo", "mexh", "vwaploss", "lowerhigh", "lodbreak"]
for fam in fams:
    rows = [json.loads(l) for l in open(HERE / f"results_{fam}.jsonl")]
    print(f"\n===== {fam}  configs-with-trades {len(rows)}  passers {sum(r['gate'] for r in rows)}")
    for win in sorted({r["window"] for r in rows}):
        for g in ("t1s1", "t05s1", "t1s05"):
            rr = [r for r in rows if r["window"] == win and r["geom"] == g and r["train"]["n"] >= 30 and r["valid"]["n"] >= 30]
            if not rr: continue
            tr = np.array([r["train"]["exp_r"] for r in rr]); va = np.array([r["valid"]["exp_r"] for r in rr])
            core = [r for r in rr if all(c == 0 for c in r["combo"])]
            cs = f"core tr {core[0]['train']['exp_r']:+.3f} (t{core[0]['train']['t']:+.1f}, n{core[0]['train']['n']}) va {core[0]['valid']['exp_r']:+.3f} (t{core[0]['valid']['t']:+.1f}, n{core[0]['valid']['n']})" if core else ""
            print(f" {win} {g}: n={len(rr)} share tr>0 {np.mean(tr>0):.2f} va>0 {np.mean(va>0):.2f} both {np.mean((tr>0)&(va>0)):.2f} corr {np.corrcoef(tr,va)[0,1]:+.2f} | base tr {rr[0]['base_train']:+.3f}/{rr[0]['base_train_univ']:+.3f} va {rr[0]['base_valid']:+.3f}/{rr[0]['base_valid_univ']:+.3f} | {cs} | passers {sum(r['gate'] for r in rr)}")
    ok = [r for r in rows if r["gate"]]
    ok.sort(key=lambda r: -min(r["train"]["t"] or 0, r["valid"]["t"] or 0))
    for r in ok[:12]:
        print(f"  {r['window']} {r['geom']} {r['combo']} | tr {r['train']['exp_r']:+.3f} t{r['train']['t']:+.2f} n{r['train']['n']} | va {r['valid']['exp_r']:+.3f} t{r['valid']['t']:+.2f} n{r['valid']['n']} exb {r['valid']['exb']:+.3f} grn {r['valid']['green']:.2f} prod {r['valid']['exp_prod']:+.3f} | pl {r['plateau_valid']:+.3f}/{r['plateau_valid_min']:+.3f} plt {r['plateau_train']:+.3f} | {'; '.join(r['layers'])}")
