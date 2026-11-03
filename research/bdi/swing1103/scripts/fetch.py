import sys, pickle
sys.path.insert(0,'/home/user/MCF')
import pandas as pd
from mcf.data.alpaca_data import fetch_bars
syms="SPY QQQ IWM DIA XLF XLK XLE XLV XLI XLY XLP XLU XLRE XLB XLC KRE SMH VIXY VG MMM IWB IWR IWO KMI KBE PNC SSNC UVIX ISRG UVXY HON IWS WDAY HIG SPLV TD ZM DIA VFLO SOXS PLD BTI ANF KBWB VEA".split()
syms=sorted(set(syms))
st=pd.Timestamp('2026-11-03 09:30',tz='America/New_York'); en=pd.Timestamp.now(tz='America/New_York')-pd.Timedelta(minutes=16)
for feed in ('sip','iex'):
    try:
        b=fetch_bars(syms, st.to_pydatetime(), en.to_pydatetime(), feed=feed); print(feed, len(b)); break
    except Exception as e: print(feed,'ERR',type(e).__name__, str(e)[:200])
pickle.dump(b, open(sys.argv[1],'wb'))
print(b['SPY'].tail(3))
