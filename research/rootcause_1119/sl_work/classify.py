"""Symbol class: stock / etf (plain) / lev (leveraged long) / inv (inverse, any leverage). Research only."""
import re, pandas as pd
ROOT='/home/user/MCF'
def classes():
    m=pd.read_csv(f'{ROOT}/research/swarm1010/w3_daily/assets_meta.csv')
    u=pd.read_csv(f'{ROOT}/data/universe.csv')
    names=dict(zip(u.symbol,u.name)); names.update(dict(zip(m.symbol,m.name)))
    etf=set(m.loc[m.is_etf,'symbol'])
    out={}
    for s,n in names.items():
        n=str(n)
        is_etf = s in etf or bool(re.search(r'\bETF\b|\bETNs?\b|ProShares|Direxion|Daily .* (Bull|Bear)|Fund, LP|Ether|Bitcoin', n, re.I))
        if not is_etf: out[s]='stock'; continue
        inv = bool(re.search(r'\bBear\b|\bShort\b|UltraShort|Inverse|\bShort\b', n, re.I)) and not re.search(r'Short[- ]Term|Short Duration|Short Maturity', n, re.I)
        lev = bool(re.search(r'\b[1-9](\.\d+)?[xX]\b|\bUltra|Leveraged|\bBull\b|\b[23]x\b', n))
        vixlong = bool(re.search(r'VIX', n)) and not re.search(r'Short VIX|-1x', n)
        vixshort = bool(re.search(r'Short VIX|-1x Short VIX', n))
        if vixlong: out[s]='inv'; continue          # long VIX = market-inverse exposure
        if vixshort: out[s]='lev'; continue          # short VIX = market-long exposure
        out[s]='inv' if inv else ('lev' if lev else 'etf')
    return out, names
if __name__=='__main__':
    c,n=classes()
    for k in ['inv','lev']:
        print(k, sorted(s for s,v in c.items() if v==k))
    print('etf', len([1 for v in c.values() if v=='etf']), 'stock', len([1 for v in c.values() if v=='stock']))
    for s in ['SPXS','SQQQ','ETHA','FTEC','MUU','SMH','TER','TECL','IWN','ASML','AVS']: print(s,c.get(s),n.get(s))
