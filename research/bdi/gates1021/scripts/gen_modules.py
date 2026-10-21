"""gates1021: write a gated module (<parent>-g1.py) for every B2 finalist / near-miss and every Part A candidate
listed in modules.json. Each module = the parent module's source (copied, logic unchanged) + ONE context clause.
Educational only - not financial advice."""
from __future__ import annotations

import ast
import json

from common import HERE, ROOT

CLAUSES = {
    # gate name -> (python expression over arrays spy, qqq, brd, d2, tod that is True where entry is BLOCKED, layer)
    "U1 spy_fo>=+0.50": ("spy >= 0.5", "skip while SPY is >= +0.50% from its open [context: spy_fo]", ["spy_fo"]),
    "U2 spy_fo>=+0.25 & breadth rising": ("(spy >= 0.25) & (d2 > 0)", "skip while SPY >= +0.25% from open AND breadth is above its level two bars earlier [context: spy_fo, breadth]", ["spy_fo", "breadth"]),
    "U3 qqq_fo>=+0.50": ("qqq >= 0.5", "skip while QQQ is >= +0.50% from its open [context: qqq_fo]", ["qqq_fo"]),
    "U4 qqq_fo>=+0.25 & breadth rising": ("(qqq >= 0.25) & (d2 > 0)", "skip while QQQ >= +0.25% from open AND breadth rising [context: qqq_fo, breadth]", ["qqq_fo", "breadth"]),
    "U5 breadth>=0.65": ("brd >= 0.65", "skip while >= 65% of the universe is above VWAP [context: breadth]", ["breadth"]),
    "U6 breadth d2>=+0.10": ("d2 >= 0.10", "skip while breadth is >= 10 points above its level two bars earlier [context: breadth]", ["breadth"]),
    "U7 prior day SPY>=+0.5% & spy_fo>=+0.25": ("(pv >= 0.5) & (spy >= 0.25)", "skip while SPY's prior session closed >= +0.5% above the session before AND SPY is >= +0.25% from today's open [context: spy_fo + spy_prev - spy_prev is NOT a LabStrategy context column yet: live code needed]", ["spy_fo", "spy_prev"]),
    "D7 prior day SPY<=-0.5% & spy_fo<=-0.25": ("(pv <= -0.5) & (spy <= -0.25)", "skip while SPY's prior session closed <= -0.5% AND SPY is <= -0.25% from today's open [context: spy_fo + spy_prev (live code needed)]", ["spy_fo", "spy_prev"]),
    "D1 spy_fo<=-0.50": ("spy <= -0.5", "skip while SPY is <= -0.50% from its open [context: spy_fo]", ["spy_fo"]),
    "D2 spy_fo<=-0.25 & breadth falling": ("(spy <= -0.25) & (d2 < 0)", "skip while SPY <= -0.25% from open AND breadth falling [context: spy_fo, breadth]", ["spy_fo", "breadth"]),
    "D3 qqq_fo<=-0.50": ("qqq <= -0.5", "skip while QQQ is <= -0.50% from its open [context: qqq_fo]", ["qqq_fo"]),
    "D4 qqq_fo<=-0.25 & breadth falling": ("(qqq <= -0.25) & (d2 < 0)", "skip while QQQ <= -0.25% from open AND breadth falling [context: qqq_fo, breadth]", ["qqq_fo", "breadth"]),
    "D5 breadth<=0.35": ("brd <= 0.35", "skip while <= 35% of the universe is above VWAP [context: breadth]", ["breadth"]),
    "D6 breadth d2<=-0.10": ("d2 <= -0.10", "skip while breadth is >= 10 points below its level two bars earlier [context: breadth]", ["breadth"]),
    "g4 skip qqq_fo>=0.25": ("qqq >= 0.25", "skip while QQQ is >= +0.25% from its open [context: qqq_fo]", ["qqq_fo"]),
    "g4 skip qqq_fo>=0.50": ("qqq >= 0.5", "skip while QQQ is >= +0.50% from its open [context: qqq_fo]", ["qqq_fo"]),
    "g3 skip spy_fo>=0.25 & breadth rising": ("(spy >= 0.25) & (d2 > 0)", "skip while SPY >= +0.25% from open AND breadth rising [context: spy_fo, breadth]", ["spy_fo", "breadth"]),
    "g3 skip spy_fo>=0.50 & breadth rising": ("(spy >= 0.5) & (d2 > 0)", "skip while SPY >= +0.50% from open AND breadth rising [context: spy_fo, breadth]", ["spy_fo", "breadth"]),
}

TAIL = '''

# ---------------------------------------------------------------- gates1021 check-gate (one layer)
_parent_mask = mask
LAYERS = list(LAYERS) + [{layer!r}]
CONTEXT = {ctx!r}


def _g21_keys(df):
    import pandas as _pd
    if "symbol" in df and "date" in df:
        return _pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    if "date" in df:
        return _pd.factorize(df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)


def _g21_block(df):
    n = len(df)
    nan = np.full(n, np.nan)
    spy = df["spy_fo"].to_numpy(dtype=float) if "spy_fo" in df else nan
    qqq = df["qqq_fo"].to_numpy(dtype=float) if "qqq_fo" in df else nan
    brd = df["breadth"].to_numpy(dtype=float) if "breadth" in df else nan
    pv = df["spy_prev"].to_numpy(dtype=float) if "spy_prev" in df else nan   # prior-session SPY close-to-close %
    tod = df["tod"].to_numpy(dtype=float)
    key = _g21_keys(df)
    p2 = np.r_[np.full(2, np.nan), brd[:-2]] if n > 2 else np.full(n, np.nan)
    same = np.r_[np.zeros(min(2, n), bool), key[2:] == key[:-2]] if n > 2 else np.zeros(n, bool)
    d2 = np.where(same & (tod >= 1000), brd - p2, np.nan)   # breadth slope from the 10:00 bar (as scored)
    with np.errstate(invalid="ignore"):
        return np.asarray({expr}, dtype=bool)


def mask(df) -> np.ndarray:
    """Parent mask AND NOT the gate state. Missing context -> the gate never blocks (NaN compares False)."""
    return np.asarray(_parent_mask(df), dtype=bool) & ~_g21_block(df)
'''


def make(name: str, parent: str, parent_module: str, gate: str, doc: str) -> str:
    src = (ROOT / parent_module).read_text()
    tree = ast.parse(src)
    body = src
    if ast.get_docstring(tree) is not None:
        d0 = tree.body[0]
        lines = src.splitlines(keepends=True)
        body = "".join(lines[d0.end_lineno:])
    expr, layer, ctx = CLAUSES[gate]
    head = f'"""{name} - research/bdi/gates1021 check-gate variant of {parent} (parent module {parent_module},\n' \
           f'copied below with its logic unchanged) plus ONE layer: {layer}.\n{doc}\nEducational only - not financial advice."""\n'
    if "import numpy as np" not in body:
        head += "import numpy as np\n"
    return head + body + TAIL.format(layer=layer, ctx=ctx, expr=expr)


def main():
    spec = json.load(open(HERE / "modules.json"))
    for m in spec:
        txt = make(m["name"], m["parent"], m["parent_module"], m["gate"], m["doc"])
        (HERE / "modules" / f"{m['name']}.py").write_text(txt)
        print("wrote", m["name"])


if __name__ == "__main__":
    main()
