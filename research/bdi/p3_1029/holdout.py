"""p3_1029: the ONE locked-block look (2024-11..2025-02) for finalist A3_cost015 vs the parent (PLAN.md, look 1).
Run once:  MCF_HIST_ALLOW_LOCKED=1 python holdout.py <scratch>   (bt.py / evalp.py logic, locked months only).
Educational only - not financial advice."""
import math, os, sys, types
from pathlib import Path
import numpy as np, pandas as pd
assert os.environ.get("MCF_HIST_ALLOW_LOCKED") == "1"
HERE = Path(__file__).resolve().parent; S = Path(sys.argv[1])
done = HERE / "holdout_out.txt"
assert not done.exists(), "the locked block is scored once per version"
src = (HERE / "bt.py").read_text().replace('assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "p3_1029 never reads the locked block"', "")
src = src.replace('OUTD = S / "p3bt"', 'OUTD = S / "p3hold"').replace("no_locked(", "(lambda *a: None)(").replace('if __name__ == "__main__":', "if False:")
src = src.replace("lib.load_month(month, context=True)", "lib.load_month(month)")   # no locked context table exists; none of the 8 masks reads a context column
sys.argv = ["bt.py", str(S)]
os.environ.pop("MCF_HIST_ALLOW_LOCKED")   # gates1021/common asserts at import; the lib guard is checked at load time
bt = types.ModuleType("bt_locked"); exec(compile(src, "bt_locked", "exec"), bt.__dict__)
os.environ["MCF_HIST_ALLOW_LOCKED"] = "1"
import lib  # noqa: E402  (path set by bt)
for m in lib.LOCKED_MONTHS:
    if not (S / "p3hold" / f"sig_{m}.parquet").exists():
        print(bt.month_job(m), flush=True)
esrc = (HERE / "evalp.py").read_text().replace('assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")', "")
esrc = esrc.replace('(S / "p3bt").glob("sig_*.parquet")', '(S / "p3hold").glob("sig_*.parquet")')
esrc = esrc.replace('assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked row"', 'assert ((d >= LOCK[0]) & (d <= LOCK[1])).all()')
esrc = esrc.replace("reg = lib.regimes()", "reg = lib.regimes(include_locked=True)").replace('if __name__ == "__main__":', "if False:")
sys.argv = ["evalp.py", str(S), "1"]
E = types.ModuleType("evalp_locked"); E.__dict__["__file__"] = str(HERE / "evalp.py"); exec(compile(esrc, "evalp_locked", "exec"), E.__dict__)
E.TRAIN_END = pd.Timestamp("2024-12-31").date()   # "train"/"valid" columns here = Nov-Dec / Jan-Feb halves of the block
E.SESS = [x for x in E.SESS if "2024-11-01" <= x <= "2025-02-28"]
par, pday = E.score(E.simulate({}), "PARENT (locked)")
a3, _ = E.score(E.simulate(dict(max_cost=0.15)), "A3_cost015 (locked)", pday)
df = pd.DataFrame([par, a3])
p = (a3["delta_day"] > 0) and (a3["delta_t"] is not None and a3["delta_t"] >= 1.0) and (a3["shrunk"] >= par["shrunk"])
txt = df.to_string() + f"\n\nholdout look 1 (lineage bar t >= 1.0): {'PASS' if p else 'FAIL'}\n\nEducational only - not financial advice.\n"
done.write_text(txt); print(txt)
