# AMD Cloud V1 Summary

AMD V1 was the first full training/evaluation run reproduced on AMD Developer Cloud.

## Environment

- Cloud: AMD Developer Cloud / GPU Droplet
- GPU: AMD Instinct MI300X
- ROCm: 7.2 image
- Python: 3.12.3
- Training approach: LoRA fine-tuning without 4-bit quantization
- Base model: Qwen/Qwen2.5-Coder-7B-Instruct

## Pipeline Run

The following workflow was completed on the AMD GPU instance:

1. Cloned the GitHub repository
2. Installed AMD-compatible Python dependencies
3. Validated the RTL repair dataset
4. Regenerated formatted train/eval data
5. Ran LoRA fine-tuning
6. Ran adapter inference on the eval set
7. Extracted generated RTL
8. Compiled generated RTL with Icarus Verilog

## Results

Manual eval score:

- AMD V1: 39/48 = 81.3%

Compile check:

- Generated RTL compile pass rate: 6/6

## Strengths

- The full fine-tuning and evaluation loop was reproduced on AMD cloud infrastructure.
- All generated RTL examples compiled successfully.
- FSM and counter repair examples were mostly strong.
- The known tick-driven FSM failure was correctly repaired in the AMD run.

## Remaining Weaknesses

- Some explanations were incorrect even when the RTL fix was correct.
- The reset repair example produced a syntactically valid but logically weak fix.
- Compile checks are useful but do not prove functional correctness.

## Takeaway

The AMD cloud run proved that the RTL Repair pipeline can be reproduced on AMD infrastructure. The run produced valid compilable RTL for all eval examples, while also revealing remaining quality gaps around explanation accuracy and reset repair behavior.