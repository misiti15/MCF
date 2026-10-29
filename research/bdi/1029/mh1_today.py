"""MH1 on today's frames (descriptive, one day): first signal per symbol, non-blackout ADV >= $95M names, 09:50-15:00,
and whether it was one of the Move Hunt 'tradable' movers. hold outcome: stop 1R = 0.25 daily ATR, flat 15:55 on 1-minute
bars, cost 1c + 1 bp per side (no tod multiplier). Usage: python mh1_today.py <scratch>. Educational only - not financial advice."""
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = "2026-10-29"
F = pd.read_parquet(S / "mh" / D / "frames.parquet"); R = pd.read_parquet(S / "mh" / D / "rows.parquet")
B = pd.read_parquet(S / "cov" / "days" / D / "bars.parquet")
ok = set(R.loc[~R.blackout, "symbol"]); F = F[F.symbol.isin(ok) & (F.tod >= 950)].reset_index(drop=True)
C = pd.read_csv("/home/user/MCF/research/bdi/moves/moves.csv"); C = C[(C.date == D) & (C.set == "tradable")]
for p in sorted(Path("/home/user/MCF/research/bdi/1029/modules").glob("*-hold-*.py")):
    sp = importlib.util.spec_from_file_location("m", p); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    x = F[m.mask(F)].groupby("symbol").head(1); sg = 1 if m.SIDE == "long" else -1; rs = []
    for _, r in x.iterrows():
        g = B[B.symbol == r.symbol]; t0 = r.ts + pd.Timedelta(minutes=5); g = g[(g.index >= t0) & (g.index.strftime("%H%M") < "1555")]
        R1 = 0.25 * r.atr_d; stop = r.close - sg * R1; ex = g.close.iloc[-1] if len(g) else r.close
        hit = (g.low <= stop) if sg == 1 else (g.high >= stop)
        if hit.any(): ex = stop - sg * 0.02
        rs.append((sg * (ex - r.close) - 2 * (0.01 + r.close * 1e-4)) / R1)
    mv = set(C[C.side == m.SIDE].symbol)
    print(f"{p.stem}: {len(x)} trades, avg R {np.mean(rs) if rs else float('nan'):+.3f}, movers hit {len(mv & set(x.symbol))}/25 {sorted(mv & set(x.symbol))}")
