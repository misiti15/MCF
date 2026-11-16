# WORKBENCH MODULE COPY for orb20_a-WB2 / orb20_a-WB3 (research only, not enabled in any account; not imported by mcf).
# parent: orb20_a (builtin class mcf.strategies.research_setups.ORB20); ONE new part: P2 price floor `min_price`
# (prior close >= min_price; the class's own _liquid floor is $5). Everything else is the parent class unchanged.
# Deploy route (after close, not applied): add the same one-line check to ORB20.eligible with default 5.0 so the parent is
# untouched, or register this subclass as class `orb20_wb`. Educational only - not financial advice.
from mcf.strategies.research_setups import ORB20


class ORB20WB(ORB20):
    name = "orb20_wb"

    def eligible(self, ctx):
        return super().eligible(ctx) and ctx.prev_close >= float(self.params.get("min_price", 5.0))
