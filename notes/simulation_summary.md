# Simulation Summary

A targeted behavioral simulation was added for the traffic-light FSM repair example.

## Tested Case

- Example: ex003_fsm_wrong_transition
- Bug class: FSM transition bug
- Generated RTL source: results/generated_rtl_v5/ex003_fsm_wrong_transition.sv
- Testbench: testbenches/traffic_fsm_tb.sv

## Checks

The testbench verifies:

- reset starts the FSM in S0
- S0 drives green
- tick moves S0 to S1
- S1 drives red
- tick low holds the current state
- tick moves S1 back to S0

## Result

The generated RTL passed the targeted behavioral simulation.