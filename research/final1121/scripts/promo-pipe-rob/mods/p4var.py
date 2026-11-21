"""P4 neighbourhood wrapper: CWT09-gapdn-vwaploss mask with gap set by the loader (research only)."""
import sys
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox/research/bdi/cwt/live")
import cwt_live_lib as L
SIDE = "short"; GEOM = "S"
P = dict(gap=10)
def mask(df): return L.a7(df, gap=P['gap'], trig=1)
def stop_price(f, i): return L.a7_stop(f, i)
