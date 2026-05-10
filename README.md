# RTL Repair

RTL Repair is a fine-tuned Verilog/SystemVerilog bug repair assistant built for the AMD Developer Hackathon.

The project takes:

- a design intent
- buggy RTL code

and returns:

- fixed RTL
- a concise bug explanation
- a verification suggestion

The goal is not just to make an LLM “write code.” The goal is to specialize a code model for common RTL repair patterns and evaluate whether fine-tuning improves correctness, formatting, and verification usefulness.

---

## Why This Project Exists

RTL bugs can be annoying because the code may look reasonable while the behavior is completely wrong.

This project focuses on common beginner/intermediate RTL issues such as:

- blocking vs non-blocking assignment mistakes
- reset logic bugs
- FSM transition bugs
- counter width and off-by-one bugs
- incomplete combinational logic / latch-prone outputs

The model is trained to repair the code and explain the actual hardware issue, not just produce a random patch.

---

## Example Task

### Input

Design intent:

```text
Two-state toggle FSM. Reset returns to S0. When tick is high, the FSM toggles between S0 and S1. When tick is low, it holds its current state.
```

Buggy RTL:

```systemverilog
module toggle_fsm (
    input logic clk,
    input logic rst,
    input logic tick,
    output logic in_s0,
    output logic in_s1
);
    typedef enum logic {S0, S1} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: if (tick) next_state = S1;
            S1: if (tick) next_state = S1;
        endcase
    end

    assign in_s0 = (state == S0);
    assign in_s1 = (state == S1);
endmodule
```

### Output

Fixed RTL:

```systemverilog
module toggle_fsm (
    input logic clk,
    input logic rst,
    input logic tick,
    output logic in_s0,
    output logic in_s1
);
    typedef enum logic [1:0] {S0, S1} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: if (tick) next_state = S1;
            S1: if (tick) next_state = S0;
        endcase
    end

    assign in_s0 = (state == S0);
    assign in_s1 = (state == S1);
endmodule
```

Bug explanation:

```text
The FSM gets stuck in S1 because the S1 state transitions back to itself when tick is high. Since tick is the toggle signal, S1 should transition back to S0 on tick. When tick is low, the default next_state assignment already holds the current state.
```

Verification suggestion:

```text
After reset, apply repeated tick pulses and verify the FSM alternates S0, S1, S0, S1. Also hold tick low in each state and verify the state does not change.
```

---

## Current Status

The project currently includes:

- curated RTL repair dataset
- dataset validation script
- prompt/response formatting script
- baseline inference script
- LoRA fine-tuning script
- LoRA adapter inference script
- generated RTL compile checker
- reusable model score summarizer
- Gradio demo app
- local NVIDIA prototype results
- AMD Developer Cloud training/evaluation results

---

## Dataset

Current dataset size:

```text
Total examples: 39
Train examples: 33
Eval examples: 6
```

Bug classes:

```text
blocking_vs_nonblocking
reset_logic
fsm_bug
counter_width_boundary
incomplete_combinational_logic
```

Dataset files:

```text
data/train.jsonl
data/eval.jsonl
data/formatted_train.jsonl
data/formatted_eval.jsonl
```

The raw dataset uses this structure:

```json
{
  "id": "example_id",
  "design_intent": "...",
  "bug_class": "...",
  "buggy_rtl": "...",
  "fixed_rtl": "...",
  "explanation": "...",
  "verification_suggestion": "..."
}
```

The formatted dataset converts each example into a prompt/response format for supervised fine-tuning.

---

## Model

Base model:

```text
Qwen/Qwen2.5-Coder-7B-Instruct
```

Fine-tuning method:

```text
LoRA / QLoRA-style local runs
LoRA AMD cloud run
```

Local development used 4-bit loading because the laptop GPU had limited memory.

AMD Developer Cloud training was run without 4-bit quantization.

---

## Evaluation Rubric

Each output is manually scored across four categories:

```text
Fix correctness: /2
Format adherence: /2
Explanation quality: /2
Verification quality: /2
```

Each example is scored out of 8.

---

## Results

### Baseline

Base model:

```text
Qwen/Qwen2.5-Coder-7B-Instruct
```

Baseline score:

```text
16/24 = 66.7%
```

Key observation:

```text
The base model could often identify the general bug, but it was unreliable on exact RTL repair and often failed the required output format.
```

---

### Local LoRA Smoke Run

First local LoRA smoke run:

```text
14/24 = 58.3%
```

This run proved the fine-tuning pipeline worked, but quality did not improve yet.

Main issue:

```text
The dataset was too small and too clean.
```

---

### Local V2

Dataset expanded to 30 examples.

V2 score:

```text
39/48 = 81.3%
```

Improvements:

- cleaner formatting
- more complete outputs
- better reset/counter/blocking repairs
- stronger overall behavior

Remaining issue:

```text
The model still failed a tick-driven FSM example by incorrectly changing the transition to use !tick.
```

---

### Local V3

V3 added targeted FSM examples to fix the tick-driven FSM failure mode.

V3 score:

```text
46/48 = 95.8%
```

Key improvement:

```text
The model fixed the known FSM failure from V2 by correctly changing:
S1: if (tick) next_state = S0;
```

Remaining issues:

- occasional markdown code fences
- some broad verification suggestions
- compile checks still needed to supplement manual scoring

---

### Local V5 Demo Fix

The Gradio demo exposed another live tick-driven FSM failure.

The model incorrectly generated:

```systemverilog
S1: if (!tick) next_state = S0;
```

This was wrong because the design intent said:

```text
tick high means toggle
tick low means hold
```

V5 added contrast examples and stronger prompt guidance.

The demo case now repairs correctly:

```systemverilog
S1: if (tick) next_state = S0;
```

---

### AMD Developer Cloud V1

The full fine-tuning/evaluation workflow was reproduced on AMD Developer Cloud.

Environment:

```text
GPU: AMD Instinct MI300X
ROCm image: 7.2
Python: 3.12.3
Training: LoRA without 4-bit quantization
```

AMD V1 score:

```text
39/48 = 81.3%
```

Compile check:

```text
6/6 generated RTL examples compiled successfully
```

Important note:

```text
Compile passing proves the generated RTL is syntactically valid, but it does not prove functional correctness.
```

Remaining AMD V1 weaknesses:

- some explanations were wrong even when the RTL fix was correct
- one reset repair was syntactically valid but logically weak
- more functional simulation checks are needed

---

## Compile Checking

Generated RTL can be extracted and compiled with Icarus Verilog.

Example:

```bash
python scripts/compile_model_outputs.py \
  --input results/lora_v3_eval_outputs_350.jsonl \
  --rtl-dir results/generated_rtl_v3 \
  --build-dir results/compile_build_v3 \
  --report results/lora_v3_compile_report.csv
```

This checks whether the model output produces syntactically valid SystemVerilog.

---

## Behavioral Simulation

Targeted behavioral simulations were added for selected generated RTL repairs.

### Simulation Regression Runner

Behavioral simulations can be run with one command:

```bash
python scripts/run_simulation_checks.py

### FSM Repair Simulation


The FSM testbench checks that the generated RTL:

- resets into the expected initial state
- drives the correct output for each state
- advances on `tick`
- holds state when `tick` is low
- toggles back correctly on the next `tick`

Result:

```text
FSM generated RTL passed targeted behavioral simulation.

---

## Local Setup

Install local dependencies:

```bash
pip install -r requirements-local.txt
```

Local requirements do not include a pinned PyTorch install because PyTorch installation depends on your machine and GPU.

For local NVIDIA testing, install the correct CUDA-enabled PyTorch build for your GPU.

---

## AMD Cloud Setup

Install AMD/cloud dependencies:

```bash
pip install -r requirements-amd.txt
```

The AMD requirement file intentionally does not include `bitsandbytes`.

AMD training command:

```bash
python scripts/run_sft_lora.py \
  --epochs 5 \
  --output-dir artifacts/qwen7b-rtl-lora-amd-v1
```

The AMD runbook is documented here:

```text
notes/amd_cloud_runbook.md
```

---

## Common Commands

Validate dataset:

```bash
python scripts/validate_dataset.py
```

Format training data:

```bash
python scripts/format_training_data.py
```

Run baseline inference:

```bash
python scripts/run_baseline_inference.py \
  --max-new-tokens 350 \
  --output results/baseline_eval_outputs_350.jsonl
```

Run local LoRA training:

```bash
python scripts/run_sft_lora.py \
  --use-4bit \
  --epochs 5 \
  --output-dir artifacts/qwen7b-rtl-lora-v5-demo-fix
```

Run LoRA inference:

```bash
python scripts/run_lora_inference.py \
  --use-4bit \
  --adapter artifacts/qwen7b-rtl-lora-v5-demo-fix \
  --max-new-tokens 350 \
  --output results/lora_v5_eval_outputs_350.jsonl
```

Summarize scores:

```bash
python scripts/summarize_model_scores.py \
  --input results/lora_v3_scores_350.csv
```

Compile generated RTL:

```bash
python scripts/compile_model_outputs.py \
  --input results/lora_v5_eval_outputs_350.jsonl \
  --rtl-dir results/generated_rtl_v5 \
  --build-dir results/compile_build_v5 \
  --report results/lora_v5_compile_report.csv
```

Run demo:

```bash
python demo/app.py \
  --use-4bit \
  --adapter artifacts/qwen7b-rtl-lora-v5-demo-fix
```

---

## Demo

The project includes a Gradio demo:

```text
demo/app.py
```

The demo allows users to paste:

- design intent
- buggy RTL

and returns:

- fixed RTL
- bug explanation
- verification suggestion

The demo is intended as a lightweight project interface, not a full production IDE.

---

## Project Structure

```text
rtl-repair/
  data/
    train.jsonl
    eval.jsonl
    formatted_train.jsonl
    formatted_eval.jsonl

  demo/
    app.py

  notes/
    amd_cloud_runbook.md
    amd_v1_summary.md
    baseline_summary.md
    v3_summary.md
    v5_demo_fix_summary.md

  results/
    baseline_scores_350.csv
    lora_v3_scores_350.csv
    lora_amd_v1_scores_350.csv
    amd_v1_outputs_for_review.txt
    lora_amd_v1_compile_report.csv

  scripts/
    validate_dataset.py
    format_training_data.py
    run_baseline_inference.py
    run_sft_lora.py
    run_lora_inference.py
    summarize_model_scores.py
    compile_model_outputs.py

  requirements-local.txt
  requirements-amd.txt
  README.md
```

---

## What Is Not Committed

Model artifacts are intentionally not committed to GitHub.

Ignored files include:

```text
artifacts/
*.safetensors
*.bin
*.pt
*.tar.gz
```

This prevents large model adapters and checkpoints from being accidentally pushed.

---

## Key Takeaway

The project demonstrates an end-to-end RTL repair fine-tuning pipeline:

```text
curated RTL dataset
→ baseline model evaluation
→ LoRA fine-tuning
→ targeted failure analysis
→ improved model behavior
→ generated RTL compile checks
→ AMD Developer Cloud reproduction
→ working demo
```

The strongest result is not just that the model improved.

The stronger result is that a known failure mode was identified, targeted with new examples, retrained, and fixed in the demo.

That is the actual engineering loop.