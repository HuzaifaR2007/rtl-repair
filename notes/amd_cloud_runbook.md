# AMD Cloud Runbook

This runbook documents how to reproduce the RTL Repair fine-tuning pipeline on AMD cloud infrastructure.

## Goal

Reproduce the local RTL Repair workflow on AMD GPU infrastructure using ROCm-compatible PyTorch tooling.

Pipeline:

1. Clone GitHub repo
2. Validate dataset
3. Format training data
4. Run LoRA fine-tuning
5. Run adapter inference
6. Compile generated RTL
7. Save results

## Environment Setup

Use an AMD ROCm PyTorch environment if available.

Basic GPU checks:

```bash
rocm-smi
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"