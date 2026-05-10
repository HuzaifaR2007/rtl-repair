# Submission Summary

## Project

RTL Repair is a fine-tuned Verilog/SystemVerilog repair assistant.

It takes:

- design intent
- buggy RTL

and returns:

- fixed RTL
- bug explanation
- verification suggestion

## Main Technical Work

- Built a curated RTL repair dataset
- Ran baseline inference with Qwen2.5-Coder-7B-Instruct
- Fine-tuned using LoRA
- Added targeted examples after finding a tick-driven FSM failure mode
- Built a Gradio demo
- Added generated RTL compile checks
- Added behavioral simulations for FSM and modulo-6 counter repairs
- Added a reusable simulation regression runner
- Reproduced the fine-tuning/evaluation workflow on AMD Developer Cloud

## Best Results

- Local V3 score: 46/48
- AMD Cloud V1 score: 39/48
- AMD generated RTL compile pass rate: 6/6
- Simulation regression: 2/2 passing

## Key Iteration

The model originally failed tick-driven FSM repairs by changing transitions to use `!tick`.

Targeted FSM contrast examples fixed this failure in the demo.

## Remaining Work

- Add broader simulation coverage
- Improve explanation accuracy
- Expand dataset size
- Add automatic testbench generation
- Add stronger functional scoring