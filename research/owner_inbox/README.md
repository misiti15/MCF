# Owner inbox (owner 2026-10-19: "anything at night that needs my attention must be obvious")

Each nightly routine (learning loop, BDI daily, top-5 tuning, Setup Generator, scheduled reviews) appends its items to
`research/owner_inbox/<YYYY-MM-DD>.md` instead of messaging the owner separately:

    ## DECISION | <routine> | <one-line question>
    Recommendation: <one line>. Evidence: <one line, numbers>. Reply: "<code> yes" / "<code> no".

    ## FYI | <routine> | <one line>

Inactive-setups check (owner INACT1 / INACT2, 2026-11-03): the nightly loop runs
`python -m mcf.report.inactive --date <today> --next <next session> --inbox` before the brief. It adds ONE FYI line
(P-rule: watch P < 5%, alarm P < 1%, index-gated setups exempt) and a DECISION only when a fix needs the owner; on
Mondays it also writes the INACT2 sessions-to-verdict list (rare setups judged on 60 trades,
research/ops/inactive/verdicts_<date>.md) with one FYI line.

One brief per night (19:17 ET) reads the file and sends a single message: decisions first (numbered, with reply codes),
then at most 5 one-line FYIs and links. Nothing needing the owner is posted anywhere else.
Educational only — not financial advice.
