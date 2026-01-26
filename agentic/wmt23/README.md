# Evaluation on WMT23 Metrics Shared Task

## Data Preparation
First, extract the original WMT23 dataset using [MT-Metrics-Eval (MTME)](https://github.com/google-research/mt-metrics-eval) and convert it into .jsonl format by `extract_wmt23_ende.py`.
> **⚠️ Note on Unannotated Data:**
> A subset of the WMT23 data lacks human annotations. In the official evaluation, these samples are discarded. To align with this protocol, our scripts flag these entries as `None` and **bypass the agentic workflow** to save computational costs.

## Running RATE
Use `core_agent_wmt23.py` instead of `../core_agent.py`, and this script automatically skips the unannotated data by producing dummy result.

## Released Trajectories
We also release the full evaluation trajectories on WMT 23 En-De in `trajectory_gpt4o_judger.tar.gz`.

## Meta-Evaluation
1. Extract the numerical scores (Segment-level & System-level) from the raw trajectories with `parse_rate`.
2. Use commands in `mtme.sh` to conduct meta-evaluation.
