import sys, pickle
sys.path.insert(0,'/home/user/MCF')
import pandas as pd
from mcf.data.alpaca_data import fetch_bars
b=pickle.load(open(sys.argv[1],'rb'))
syms=sorted(b)
st=pd.Timestamp('2026-10-06 09:30',tz='America/New_York'); en=pd.Timestamp('2026-11-02 16:00',tz='America/New_York')
h=fetch_bars(syms, st.to_pydatetime(), en.to_pydatetime(), feed='sip', minutes=5)
pickle.dump(h, open(sys.argv[2],'wb')); print(len(h))
