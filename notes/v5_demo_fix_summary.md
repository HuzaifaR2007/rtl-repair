# V5 Demo Fix Summary

V5 was created after the live Gradio demo exposed a remaining tick-driven FSM failure.

## Failure

The model incorrectly repaired a two-state toggle FSM by changing the S1 transition to use `!tick`:

S1: if (!tick) next_state = S0;

This was wrong because the design intent stated that `tick` is the toggle/advance signal and tick low should hold state.

## Fix

Added targeted contrast examples explaining that:

- tick high means advance/toggle
- tick low means hold state
- using `!tick` is wrong unless the design intent explicitly says so

The prompt was also updated to include this rule.

## Result

The V5 adapter correctly repaired the demo case:

S1: if (tick) next_state = S0;

The generated explanation and verification suggestion were also correct.