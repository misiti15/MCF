import warnings,sys; warnings.filterwarnings('ignore')
exec(open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swing1103/load.py').read())
day=pd.Timestamp('2026-11-03',tz=NY)
sec=dict(VG='XLE',MMM='XLI',KMI='XLE',PNC='KRE',KBE='KBE',KBWB='KBWB',SSNC='XLF',TD='XLF',HON='XLI',ISRG='XLV',WDAY='XLK',HIG='XLF',ZM='XLK',
 UVIX='VIXY',UVXY='VIXY')
def P(sym,t): return px(sym,t)
def seg(r,a,b):
    """a..b window within the trade; returns (pnl_usd, mkt_usd, sector_usd) for the slice"""
    a=max(a,r.et); 
    closed = pd.notna(r.xt) and r.xt<=b
    pa = r.entry if a==r.et else P(r.sym,a)
    pb = r.exit if closed else P(r.sym,b)
    if closed: b=r.xt
    if b<=a: return 0,0,0
    sp=P('SPY',b)/P('SPY',a)-1
    pnl=r.side*(pb-pa)*r.qty
    notional=r.qty*pa
    mkt=r.side*r.beta*sp*notional
    s=sec.get(r.sym,r.sym)
    sr=P(s,b)/P(s,a)-1
    sec_x=r.side*(sr-beta[s]*sp)*notional
    return pnl,mkt,sec_x
def decomp(a,b,label):
    out=[]
    for _,r in T.iterrows():
        if r.et>=b or (pd.notna(r.xt) and r.xt<=a): continue
        pnl,mkt,_=seg(r,a,b)
        # entry part: only if the trade entered inside window
        ent=0; first=0
        if r.et>=a:
            m=json.JSONDecoder().raw_decode(r.meta)[0]; mid=(m['bid']+m['ask'])/2
            ent=-r.side*(r.entry-mid)*r.qty   # fill vs mid (cost <0)
            t5=min(r.et+pd.Timedelta(minutes=5),b)
            p5,m5,_=seg(r,r.et,t5)
            # residual first 5 min measured from mid
            first=p5-m5-ent if False else (p5-m5)
            first=first  # includes fill-vs-mid? no: seg uses fill as start; ent separate
            rest_a=t5
        else: rest_a=a
        pr,mr,sx=seg(r,rest_a,b) if rest_a<b and not (pd.notna(r.xt) and r.xt<=rest_a) else (0,0,0)
        idio=pr-mr-sx
        out.append(dict(sym=r.sym,strat=r.strat,side=r.side,et=r.et.strftime('%H:%M'),risk=r.risk,
            pnl=pnl, mkt=mkt, entry_cost=ent, first5=first-0, sector=sx, idio=idio))
    D=pd.DataFrame(out)
    # first5 currently = 5-min P/L minus market over those 5 minutes; mkt column covers whole window
    for c in ['pnl','mkt','entry_cost','first5','sector','idio']: D[c+'_R']=D[c]/D.risk
    D['chk']=D.pnl-(D.mkt+D.first5+D.sector+D.idio)
    print('=== ',label); pd.set_option('display.width',260)
    print(D[['sym','strat','et','pnl','mkt','entry_cost','first5','sector','idio','chk','pnl_R','mkt_R','first5_R','sector_R','idio_R']].round(2).to_string())
    print('SUM usd', D[['pnl','mkt','entry_cost','first5','sector','idio']].sum().round(2).to_dict())
    print('SUM R', D[['pnl_R','mkt_R','entry_cost_R','first5_R','sector_R','idio_R']].sum().round(2).to_dict())
    g=D.groupby('strat')[['pnl','pnl_R','mkt_R']].sum().round(2); print(g)
    return D
a=day+pd.Timedelta(hours=9,minutes=50); tr_=day+pd.Timedelta(hours=10,minutes=54)
D1=decomp(a,tr_,'DIP 09:50-10:54')
D2=decomp(tr_,day+pd.Timedelta(hours=11,minutes=5),'TURN 10:54-11:05')
D3=decomp(tr_,day+pd.Timedelta(hours=12,minutes=35),'RECOVERY 10:54-12:35')
D1.to_csv(sys.argv[1]+'/dip.csv',index=False); D3.to_csv(sys.argv[1]+'/recovery.csv',index=False)
