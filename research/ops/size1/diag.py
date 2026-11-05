"""SIZE1 diagnostics (counted in NOTES): named live top-5 on the 2-year lists (hindsight book, labelled), and how often
buying power is what blocks a signal. Educational only - not financial advice.  usage: python diag.py <scratch_dir>"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim  # noqa: E402

S = Path(sys.argv[1])
lab = pd.read_pickle(S / "lab.pkl"); live = pd.read_pickle(S / "live.pkl")
tr = lab[sim.TRAIN(lab.date)]
q = pd.DataFrame({"qs": tr.groupby("setup").r.apply(sim.shrunk), "qx": tr.groupby("setup").r_xm.apply(sim.shrunk)})
rows = []
for win, src in [("TRAIN", tr), ("VALID", lab[sim.VALID(lab.date)])]:
    d = sim.day_arrays(sim.prepare(src, sim.LIVE_A, q, {}, False)); ss = sorted(src.date.unique())
    for cfg in (sim.BASE, dict(sim.BASE, risk=0.10, bp=4)):
        m = sim.metrics(sim.run(d, ss, cfg)); m.update(book="A-named (hindsight)", window=win, config=sim.cfgname(cfg)); rows.append(m)
# BP binding: signals available vs taken at very large BP vs 4x/1x (live, both books)
for b, setups in [("A", sim.LIVE_A), ("B", sim.PRIMARY)]:
    d = sim.day_arrays(sim.prepare(live, setups, q, {}, True)); ss = sorted(live.date.unique())
    for bp in (1000, 4, 2, 1):
        for r in (0.10, 0.25, 0.50):
            m = sim.metrics(sim.run(d, ss, dict(sim.BASE, risk=r, bp=bp)))
            m.update(book=b, window="LIVE", config=f"{r:.2f}%/{bp}x (BP check)"); rows.append(m)
out = pd.DataFrame(rows)[["book", "window", "config", "ret", "dd", "green", "avgR", "avgR_wob", "best_share", "trades", "t"]]
print(out.round(3).to_string(index=False))
out.to_csv(Path(__file__).resolve().parent / "diag.csv", index=False, float_format="%.4f")
