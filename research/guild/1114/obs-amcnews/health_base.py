"""FAMC health base rate (Observer 2026-11-13 night): what share of KNOWN after-close reporters open with |gap| > 2x their
normal gap? Uses the same gap / normal definition as build_famc_cal.health() (open vs prior close; normal = median of the
prior 20 sessions' |gap|). Known AMC = earnings_yf session 'amc' with a reported EPS, lab symbols, report dates
2026-08-03..2026-10-30 (before Yahoo's AMC placeholders began 11-02). Alpaca daily SIP bars, split-adjusted. 0 configs.
Educational only - not financial advice. usage (MCF checkout): python ../guild/research/obs-amcnews/health_base.py <earnings_yf.parquet>"""
import sys, importlib.util, numpy as np, pandas as pd
from pathlib import Path
spec = importlib.util.spec_from_file_location("famc", str(Path(__file__).with_name("build_famc_cal.py"))); F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
yf = pd.read_parquet(sys.argv[1]); lab = set(Path("research/lab_symbols.txt").read_text().split())
ev = yf[(yf.session == "amc") & yf.eps_reported.notna() & yf.symbol.isin(lab)].copy()
ev["date"] = pd.to_datetime(ev.date).dt.strftime("%Y-%m-%d"); ev = ev[(ev.date >= "2026-08-03") & (ev.date <= "2026-10-30")].drop_duplicates(["symbol", "date"])
B = F.daily(sorted(ev.symbol.unique()), "2026-06-15", "2026-11-14"); rows = []
for _, r in ev.iterrows():
    b = B.get(r.symbol); R = (pd.Timestamp(r.date) + pd.offsets.BDay(1)).strftime("%Y-%m-%d")
    if b is None or R not in b.index: continue
    b = b.sort_index(); gap = (b.o / b.c.shift(1) - 1).abs(); i = b.index.get_loc(R); norm = gap.iloc[max(0, i - 21):i - 1].median()
    if norm > 0: rows.append(dict(symbol=r.symbol, date=r.date, ratio=gap.iloc[i] / norm))
h = pd.DataFrame(rows); assert len(h) > 100, len(h)
print(f"known AMC events {len(h)} ({h.symbol.nunique()} names): share ratio > 2: {(h.ratio > 2).mean():.1%}; median ratio {h.ratio.median():.2f}; "
      f"quartiles {h.ratio.quantile([.25, .5, .75]).round(2).tolist()}")
# random non-event days for the same names (control)
ctl = []
rng = np.random.default_rng(7)
for s, b in B.items():
    b = b.sort_index(); gap = (b.o / b.c.shift(1) - 1).abs(); evd = set(ev[ev.symbol == s].date)
    for i in rng.choice(range(25, len(b)), size=min(10, max(0, len(b) - 25)), replace=False):
        if b.index[i - 1] in evd: continue
        n = gap.iloc[i - 21:i - 1].median()
        if n > 0: ctl.append(gap.iloc[i] / n)
ctl = np.array(ctl); print(f"control (random non-event days, same names): n {len(ctl)}, share ratio > 2: {(ctl > 2).mean():.1%}")
p = (h.ratio > 2).mean(); q = (ctl > 2).mean()
for n, k in [(16, 7), (13, 6)]:
    from math import comb
    lik = lambda pr: comb(n, k) * pr**k * (1 - pr)**(n - k)
    print(f"observed {k}/{n} > 2x: precision estimate (mixture of AMC {p:.2f} and non-event {q:.2f}) = {max(0, min(1, (k/n - q) / (p - q))):.2f}")
