# Final Submission Text

## Project Name

RTL Repair

## Short Description

RTL Repair is a fine-tuned Verilog/SystemVerilog repair assistant. It takes a design intent and buggy RTL code, then returns fixed RTL, a concise bug explanation, and a verification suggestion.

## Full Description

RTL Repair focuses on common RTL bugs such as blocking vs non-blocking assignment mistakes, reset issues, FSM transition bugs, counter boundary errors, and incomplete combinational logic.

The project started with baseline evaluation using Qwen2.5-Coder-7B-Instruct. The baseline model was useful but unreliable on exact hardware behavior, so I built a curated RTL repair dataset and fine-tuned the model using LoRA.

A key part of the project was failure-driven iteration. One failure mode appeared in tick-driven FSM repairs: the model incorrectly changed transitions to use `!tick`, even when the design intent said `tick` should advance the FSM. I added targeted contrast examples, retrained the model, and fixed that failure in the demo.

The project includes a Gradio demo, manual score summaries, generated RTL compile checks with Icarus Verilog, behavioral simulations for selected repairs, and a one-command project check runner.

I also reproduced the fine-tuning and evaluation workflow on AMD Developer Cloud using ROCm-compatible tooling.

## Built With

- Qwen2.5-Coder-7B-Instruct
- LoRA / PEFT
- PyTorch / TRL
- Gradio
- Icarus Verilog
- AMD Developer Cloud / ROCm
- Hugging Face Spaces

## Results

- Baseline Qwen2.5-Coder: 16/24 = 66.7%
- Local V3: 46/48 = 95.8%
- AMD Cloud V1: 39/48 = 81.3%
- AMD generated RTL compile pass rate: 6/6
- Behavioral simulation regression: 2/2 passing

## Links

- GitHub Repository: https://github.com/HuzaifaR2007/rtl-repair
- Hugging Face Space: https://huggingface.co/spaces/Hoooozii/rtl-repair
- LoRA Adapter: https://huggingface.co/Hoooozii/rtl-repair-lora-v5