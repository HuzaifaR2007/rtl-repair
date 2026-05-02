# Simulation Summary

## FSM

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

## Modulo-6 Counter Simulation

A targeted behavioral simulation was added for the modulo-6 counter repair example.

### Tested Case

- Example: ex025_counter_mod6_wrong_terminal
- Bug class: counter width / boundary bug
- Generated RTL source: results/generated_rtl_v5/ex025_counter_mod6_wrong_terminal.sv
- Testbench: testbenches/mod6_counter_tb.sv

### Checks

The testbench verifies:

- reset clears count to 0
- with enable high, count increments from 0 through 5
- count wraps from 5 back to 0
- count never reaches invalid value 6
- with enable low, count holds its current value
- reset works during operation

### Result

The generated RTL passed the targeted modulo-6 counter behavioral simulation.