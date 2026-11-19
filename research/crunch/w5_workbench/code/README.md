Run order (set S / W5S to a scratch dir holding j/<branch>.db journals from the mcf-data* state branches, and copies of
u7_candidates.csv as u7c.csv, u7_parents.csv as u7p.csv, l3_bespoke_1117/C_workbench.csv as l3c.csv):
jl.py (loader; python -c "import jl; jl.load().to_pickle(S+'/trades.pkl')") -> diag.py -> noise.py -> bars.py (streams
public release packs) -> demo.py -> wb2.py -> power.py -> powersim.py -> refire_check.py. Paths were replaced by <scratch>.
Educational only - not financial advice.
