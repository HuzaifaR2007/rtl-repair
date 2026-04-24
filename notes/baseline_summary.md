# Baseline Summary (Qwen2.5-Coder-7B-Instruct, 350 tokens)

Official baseline eval used 3 held-out examples.

Scores:
- ex003_fsm_wrong_transition: 4/8
- ex011_edge_detector_blocking: 7/8
- ex015_alu_zero_flag_incomplete_comb: 5/8

Overall:
- Total: 16/24
- Average: 5.33/8
- Percent: 66.7%

Key takeaway:
The base model often identifies the general RTL bug and can sometimes produce a plausible fix, but it is inconsistent on exact repair correctness, strict format adherence, and concise verification guidance.