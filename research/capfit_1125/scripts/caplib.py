import numpy as np, pandas as pd
GRID=[round(-1.0-0.25*i,2) for i in range(13)]
LEVELS=GRID+[None]
def latch_day(e,x,r,L):
    """e,x numeric arrays (entry/exit times), sorted by e. returns keep mask."""
    n=len(e); keep=np.zeros(n,bool)
    if L is None: keep[:]=True; return keep
    kx=[];kr=[]
    for i in range(n):
        closed=sum(rr for xx,rr in zip(kx,kr) if xx<=e[i])
        if closed<=L+1e-12: continue
        keep[i]=True; kx.append(x[i]); kr.append(r[i])
    return keep
def path_min(e,x,r):
    """min of cumulative closed R (no cap), evaluated at exits"""
    o=np.argsort(x,kind='mergesort'); c=np.cumsum(r[o]); return c.min() if len(c) else 0.0
def calib(G,T,K_ok=True):
    """G: dict L->gain (sum), T: dict L->touch count. returns P1,P3 levels"""
    p1=None
    for i,L in enumerate(GRID):
        if T[L]>=2 and G[L]>1e-9 and all(G[M]>=-1e-9 for M in GRID[i+1:] if T[M]>=1):
            p1=L; break
    best=max(GRID,key=lambda L:G[L]); p3=best if G[best]>1e-9 else None
    return p1,p3
def clamp(L):
    if L is None: return None
    return min(-1.5,max(-4.0,L))
def clustered_t(d):
    d=np.asarray(d,float); n=len(d)
    if n<3 or d.std(ddof=1)==0: return float('nan')
    return d.mean()/(d.std(ddof=1)/np.sqrt(n))
