# LR6 2026-11-11 (research only): simulate the 41 pre-declared entry policies (PLAN.md) on every live entry with bars.
# Output <S>/lr6/sim.pkl: per trade x policy -> imm, p_fill (point, lo, hi), R if rest-filled, resim flag.
import numpy as np, pandas as pd, re
S = '/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad'
OUT = f'{S}/lr6'
SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
CANCELS = [15, 30, 60, 120, 300]
POL = [('M', 'mkt', 0, 0)]
POL += [(f'O{o}_W{w}', 'bps', o, w) for o in [0, 2, 5, 10, 20] for w in CANCELS]
POL += [(f'K{k}_W{w}', 'spr', k, w) for k in [0.5, 1, 2] for w in CANCELS]
POL += [('P_LR6', 'lr6', 0, 60)]


def classify_asset(name):
    n = name if isinstance(name, str) else ''
    lev = re.search(r'\b(2X|3X|1\.5X|1\.25X|-1X)\b|Ultra|Leveraged|Daily .*(Bull|Bear)|Inverse', n, re.I)
    etf = re.search(r'\bETF\b|\bETN\b|Fund\b|iShares|SPDR|ProShares|Direxion|Invesco QQQ|Trust,? Series|Select Sector', n, re.I)
    return 'lev_etf' if lev and (etf or 'Daily' in n) else ('etf' if etf else 'stock')


def base(t):
    s = t.side.values
    t['f_n'] = s * t.entry.values; t['r_n'] = s * t.ref.values; t['x_n'] = s * t.exit.values
    t['stop_n'] = s * t.stop.values
    t['tg_n'] = np.where(t.target.notna(), s * t.target.fillna(0).values, np.nan)
    allow = (t.pnl - t.pnl_adj.fillna(t.pnl)) / t.shares
    sellpx = np.where(s > 0, t.exit, t.entry)
    t['fee_ps'] = SEC * sellpx + TAF + 2 * CAT
    t['c_ps'] = allow + t.fee_ps
    t['R_mkt'] = (t.x_n - t.f_n - t.c_ps) / t.risk_plan
    t['slip_R'] = (t.f_n - t.r_n) / t.risk_plan
    t['asset'] = t.name.map(classify_asset)
    return t


def limit_price(t, kind, p):
    r = t.r_n.values
    if kind == 'bps': return r + p * t.ref.values / 1e4
    if kind == 'spr': return r + p * (t.ask - t.bid).fillna(0).values
    if kind == 'lr6':
        touch = np.where(t.side.values > 0, t.ask.values, -t.bid.values)
        touch = np.where(np.isfinite(touch) & (touch != 0), touch, r)
        return touch + np.minimum(0.25 * t.risk_plan.values, 20e-4 * t.ref.values)
    return np.full(len(t), np.inf)


def run():
    t = base(pd.read_pickle(f'{OUT}/trades.pkl'))
    bars = pd.read_pickle(f'{OUT}/bars.pkl')
    t = t[(t.date <= '2026-11-10')].reset_index(drop=True)
    # per (symbol, date) bar arrays: minute start (epoch s), low, high, close
    arr = {}
    bars = bars.reset_index()
    bars['date'] = bars.ts.dt.strftime('%Y-%m-%d')
    bars['ep'] = (bars.ts.dt.tz_convert('UTC') - pd.Timestamp('1970-01-01', tz='UTC')).dt.total_seconds().astype(np.int64)
    need = set(zip(t.symbol, t.date))
    for (sym, d), g in bars.groupby(['symbol', 'date']):
        if (sym, d) in need:
            arr[(sym, d)] = (g.ep.values, g.low.values, g.high.values, g.close.values, g.ts.dt.strftime('%H%M').astype(int).values)
    ts_ep = t.ts.map(lambda x: x.timestamp()).values
    tf_ep = t.tf.map(lambda x: x.timestamp()).values
    te_ep = t.te.map(lambda x: x.timestamp()).values
    rows = {}
    for name, kind, p, W in POL:
        L = limit_price(t, kind, p)
        n = len(t)
        imm = t.f_n.values <= L + 1e-9
        pf = np.zeros(n); plo = np.zeros(n); phi = np.zeros(n); Rr = np.zeros(n); rs = np.zeros(n, bool); ok = np.zeros(n, bool)
        if kind != 'mkt':
            for i in range(n):
                key = (t.symbol.iat[i], t.date.iat[i])
                if key not in arr: continue
                ok[i] = True
                if imm[i]: continue
                ep, lo_, hi_, cl, hm = arr[key]
                s = t.side.iat[i]
                low_n = lo_ if s > 0 else -hi_
                high_n = hi_ if s > 0 else -lo_
                tick = 0.01 if t.ref.iat[i] >= 1 else 0.0001
                a, b = max(tf_ep[i], ts_ep[i]), ts_ep[i] + W
                if b <= a: continue
                j0 = np.searchsorted(ep, a - 60, side='right'); j1 = np.searchsorted(ep, b, side='left')
                q = 1.0; first = None; lo_b = 0; hi_b = 0
                for j in range(j0, j1):
                    ov = min(ep[j] + 60, b) - max(ep[j], a)
                    if ov <= 0: continue
                    if low_n[j] <= L[i] - tick:
                        w = ov / 60; q *= (1 - w); hi_b = 1
                        if ep[j] >= a and ep[j] + 60 <= b: lo_b = 1
                        if first is None: first = (j, max(ep[j], a) + ov / 2)
                pf[i] = 1 - q; plo[i] = lo_b; phi[i] = hi_b
                if first is None: continue
                j, tfill = first
                if te_ep[i] > tfill:
                    Rr[i] = (t.x_n.iat[i] - L[i] - t.c_ps.iat[i]) / t.risk_plan.iat[i]
                else:   # observed trade already over: re-simulate the bracket from the fill minute
                    rs[i] = True
                    st = t.stop_n.iat[i]; tg = t.tg_n.iat[i]; x = None; why = 'flatten'
                    for k in range(j, len(ep)):
                        if hm[k] >= 1555: x = (cl[k - 1] if s > 0 else -cl[k - 1]); break
                        if low_n[k] <= st: x = st; why = 'stop'; break
                        if np.isfinite(tg) and high_n[k] >= tg + tick and k > j: x = tg; why = 'target'; break
                    if x is None: x = (cl[-1] if s > 0 else -cl[-1])
                    c = t.fee_ps.iat[i] + (0.02 if why == 'stop' else 0.0)
                    Rr[i] = (x - L[i] - c) / t.risk_plan.iat[i]
        else:
            ok[:] = True
        rows[name] = pd.DataFrame(dict(imm=imm, p=pf, plo=plo, phi=phi, R_rest=Rr, resim=rs, ok=ok))
        print(name, imm.mean().round(3), pf[~imm & ok].mean().round(3) if (~imm & ok).any() else 0, flush=True)
    sim = pd.concat(rows, names=['pol', 'i'])
    t.to_pickle(f'{OUT}/trades_b.pkl'); sim.to_pickle(f'{OUT}/sim.pkl')


if __name__ == '__main__':
    run()
