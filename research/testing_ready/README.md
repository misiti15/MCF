# Testing account: staged setups (2026-10-09)

*Educational only - not financial advice.*

`account_testing_additions.yaml` holds every setup currently worth forward-testing in the Testing ("mct-") account.
It is not live: it is merged into `config/account_testing.yaml` after market hours once the owner has created the
account and added `ALPACA_TESTING_API_KEY` / `ALPACA_TESTING_SECRET_KEY`. All entries load in `build_strategies`.

| Setup | Source | Evidence |
|---|---|---|
| ST1-ST8 | BDI basic stacks (research/bdi/stack1009) | 2-yr positive in up AND down sessions; locked block: ST3 and ST5 pass, the rest fail |
| RW4, RW6 | BDI rework (research/bdi/rework1008) | 2-yr slightly positive, down-session driven |
| RW5 | BDI rework | positive on both old holdouts; 2-yr about flat |

Already in the Testing config: the three L3 gap-down shorts. Not staged (and why): RW1/RW3/RW7 (2-yr negative, only down
sessions positive), RW2/RW8 and the 9 retire verdicts (2-yr negative), VID1-8 (need a hold-to-close exit LabStrategy
does not have yet).
