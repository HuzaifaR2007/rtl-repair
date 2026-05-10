# RTL Repair Score Summary

| Run | Eval Size | Score | Notes |
|---|---:|---:|---|
| Baseline Qwen2.5-Coder-7B | 3 examples | 16/24 = 66.7% | Base model was useful but unreliable on exact RTL repair and formatting |
| Local LoRA Smoke | 3 examples | 14/24 = 58.3% | Pipeline worked, but dataset was too small |
| Local V2 | 6 examples | 39/48 = 81.3% | Larger dataset improved formatting and correctness |
| Local V3 | 6 examples | 46/48 = 95.8% | Targeted FSM examples fixed the known `!tick` failure |
| AMD Cloud V1 | 6 examples | 39/48 = 81.3% | Full training/eval workflow reproduced on AMD Developer Cloud |

## Compile Check

| Run | Compile Pass Rate |
|---|---:|
| AMD Cloud V1 | 6/6 generated RTL examples compiled |

