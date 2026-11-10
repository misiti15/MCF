"""ROTA1: per-setup effects of the representative plateau config, frozen-book check, light-version detail.
Post hoc diagnostics on the 2-year lab lists (not part of the pass test). Educational only — not financial advice.

    python research/rota1/effects.py <scratch_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wf  # noqa: E402
from common import split_of, tstat  # noqa: E402

S = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent
REP = (5, 90, "S2", 0.20, 1, 8, 0)


def main():
    B = pd.read_pickle(S / "wf_books.pkl")
    setups, dates, static = B["setups"], B["dates"], B["static"]
    out, held, sw, book = B["books"][REP]
    k = REP[5]
    R, N = wf.load("bt")
    Rv = R.to_numpy()[wf.START:]
    splits = np.array([split_of(d) for d in dates])
    lines = []
    # frozen book: the first review's pick, never changed
    cfg = dict(zip(wf.GRID, REP))
    first = list(np.where(held[0])[0])
    frozen = Rv[:, first].mean(1)
    for name, x in (("rolling", out), ("frozen first pick", frozen), ("static (Primary today)", static)):
        lines.append(f"| {name} | " + " | ".join(f"{x[splits == s].mean():+.3f}" for s in ("TRAIN", "VALID", "FWD"))
                     + f" | {tstat(x[(splits == 'TRAIN') | (splits == 'VALID')]):.2f} |")
    d = out - frozen
    lines.append(f"| rolling - frozen | " + " | ".join(f"{d[splits == s].mean():+.3f}" for s in ("TRAIN", "VALID", "FWD"))
                 + f" | {tstat(d[(splits == 'TRAIN') | (splits == 'VALID')]):.2f} |")
    # per-setup effects
    contrib = (Rv * held) / k
    st_idx = [setups.index(s) for s in wf.PRIMARY]
    rows = []
    for j, s in enumerate(setups):
        hs = held[:, j]
        ins = sum(1 for x in sw if x[2] == j)
        outs = sum(1 for x in sw if x[1] == j)
        static_c = Rv[:, j].sum() / len(st_idx) if j in st_idx else 0.0
        if hs.any() or j in st_idx:
            rows.append({"setup": s, "primary_today": j in st_idx, "sessions_held": int(hs.sum()),
                         "share_held": round(hs.mean(), 2), "entries": ins, "exits": outs,
                         "R_in_rolling(per-setup-session units)": round(contrib[:, j].sum(), 2),
                         "R_per_session_held": round(Rv[hs, j].mean(), 3) if hs.any() else np.nan,
                         "R_in_static": round(static_c, 2),
                         "R_when_not_held(if Primary)": round(Rv[~hs, j].sum() / len(st_idx), 2) if j in st_idx else np.nan})
    eff = pd.DataFrame(rows).sort_values("sessions_held", ascending=False)
    eff.to_csv(OUT / "effects_rep.csv", index=False)
    swl = pd.DataFrame([{"review_date": dates[i - wf.START] if i - wf.START < len(dates) else None,
                         "out": setups[a], "in": setups[b], "why": w} for i, a, b, w in sw])
    swl.to_csv(OUT / "swaps_rep.csv", index=False)
    print("\n".join(lines))
    print(eff.to_string(index=False))
    print(swl.to_string(index=False))
    print("first book:", [setups[j] for j in first])
    print("final book:", [setups[j] for j in book])


if __name__ == "__main__":
    main()
