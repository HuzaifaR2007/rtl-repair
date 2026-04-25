# V3 Fine-Tune Summary

V3 added a targeted FSM mini-batch to fix a known failure mode from V2.

## Known V2 Failure

The model incorrectly repaired tick-driven FSMs by changing transitions to use `!tick`, even when the design intent said `tick` should advance the FSM.

## V3 Change

Added targeted FSM examples where:

- tick high means advance
- tick low means hold state
- transitions should not be flipped to `!tick`

## Result

V3 score: 46/48 = 95.8%

Most important improvement:

- `ex003_fsm_wrong_transition` improved from failing the core fix to correctly changing `S1: if (tick) next_state = S0;`

## Remaining Issues

- Some outputs still use markdown code fences.
- Some verification suggestions are slightly broad.
- More automated compile/simulation checks are still needed.