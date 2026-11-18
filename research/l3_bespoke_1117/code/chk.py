import load4 as L, sim4, sim, sim2
for test,(c,g) in L.TESTS.items():
    t = sim4.trades(c, sim4.P, g)
    if test=="replay": t0 = t[t.date<="2026-11-13"]
    else: t0 = t
    b_old = sim.book(t0.drop(columns=["mfe","atr_d","e"]), sim4.P)
    b_new = sim4.book(t0, sim4.P, -2.0)
    print(test, "raw", len(t), "old book", len(b_old), round(b_old.r.mean(),4), "new latch book", len(b_new), round(b_new.r.mean(),4))
    if test=="replay":
        b=sim4.book(t, sim4.P, -2.0); print(" full replay to 11-17", len(b), round(b.r.mean(),4), b.groupby('date').r.sum().round(2).tail(4).to_dict())
