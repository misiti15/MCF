"""AUDIT: reproduce the innovation finalists' lab-frame numbers from their own module code (bdlib.score).
Educational only - not financial advice."""
import importlib.util
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/innovation")
sys.path.insert(0, "research/heat/candidates")
import bdlib as B  # noqa: E402


def mod(p):
    s = importlib.util.spec_from_file_location(p.split("/")[-1][:-3].replace("-", "_"), p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


F = {"gapdn": ("research/oct7/innovation/BD-gapdn-reclaim.py", (1300, 1430)),
     "gapdn_rsi3": ("research/oct7/innovation/BD-gapdn-reclaim-rsi3.py", (1300, 1430)),
     "hfl_pdl": ("research/oct7/innovation/BD-hfl-nearPDL.py", (1105, 1330))}
import regime_5  # noqa: E402
for sp in ("train", "valid"):
    df = B.load(sp)
    print(sp, "rows", len(df), "dates", df.date.min(), df.date.max(), df.date.nunique(), flush=True)
    for k, (p, w) in F.items():
        m = mod(p)
        print(" ", k, B.score(df, m.mask(df), m.SIDE, m.GEOM, w), flush=True)
    s = regime_5.score(df)
    print("  hfl_parent", B.score(df, s >= regime_5.LONG_AT, "long", "t1s1", (1105, 1330)), flush=True)
