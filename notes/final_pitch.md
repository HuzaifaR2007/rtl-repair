# Final Pitch

## One-Sentence Pitch

RTL Repair is a fine-tuned Verilog/SystemVerilog repair assistant that takes a design intent and buggy RTL, then returns fixed RTL, a concise bug explanation, and a verification suggestion.

## Short Pitch

RTL Repair is built for hardware learners and engineers working with RTL bugs.

The system focuses on common Verilog/SystemVerilog mistakes such as blocking vs non-blocking assignment issues, reset bugs, FSM transition errors, counter boundary bugs, and incomplete combinational logic.

I started by evaluating a base code model, Qwen2.5-Coder-7B-Instruct, on curated RTL bug-repair examples. The baseline model was often directionally useful, but it was unreliable on exact hardware behavior and formatting.

I then fine-tuned the model using LoRA on a curated RTL repair dataset. During testing, I found a specific failure mode where the model incorrectly repaired tick-driven FSMs by changing transitions to use `!tick`, even when the design intent said `tick` should advance the FSM. I added targeted contrast examples, retrained, and fixed that failure in the demo.

The project includes a Gradio demo, manual scoring, generated RTL compile checks, behavioral simulation tests, a one-command project check runner, and an AMD Developer Cloud training/evaluation run.

## Technical Summary

The project includes:

- curated RTL repair dataset
- prompt/response formatting pipeline
- baseline model inference
- LoRA fine-tuning
- adapter inference
- manual scoring rubric
- generated RTL compile checks with Icarus Verilog
- behavioral simulation tests for FSM and modulo counter repairs
- one-command project check runner
- Gradio demo app
- AMD Developer Cloud reproduction

## Best Results

- Baseline Qwen2.5-Coder score: 16/24 = 66.7%
- Local V3 score: 46/48 = 95.8%
- AMD Cloud V1 score: 39/48 = 81.3%
- AMD generated RTL compile pass rate: 6/6
- Behavioral simulation regression: 2/2 passing

## Key Engineering Iteration

The strongest part of the project was the iteration loop.

The model initially failed a tick-driven FSM repair by generating:

```systemverilog
S1: if (!tick) next_state = S0;

This was wrong because the design intent said tick was the advance signal and tick low should hold state.

I added targeted contrast examples explaining that tick high means advance and tick low means hold. After retraining, the demo correctly generated:

S1: if (tick) next_state = S0;

This showed that targeted dataset improvements could fix a concrete model failure mode.

Why AMD Developer Cloud Matters

The local prototype proved the idea and helped debug the training pipeline.

The AMD Developer Cloud run showed that the fine-tuning and evaluation workflow could be reproduced on AMD GPU infrastructure using ROCm-compatible tooling. The AMD run produced valid generated RTL for all eval examples, with a 6/6 compile pass rate.

What Makes This More Than a Chatbot

RTL Repair does not just generate text.

The project checks model outputs with:

manual scoring for correctness, formatting, explanation quality, and verification quality
Icarus Verilog compile checks
behavioral simulations for selected generated repairs
one-command project regression checks

This matters because RTL can look syntactically reasonable while still being functionally wrong.

Remaining Work

The next improvements would be:

expand the dataset
add more behavioral simulations across bug classes
improve explanation accuracy
generate testbenches automatically
add stronger functional scoring
package the trained adapter for easier reuse