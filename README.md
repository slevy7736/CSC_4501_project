# TODO
## - 1. Missing min_latency curve:
    - In edge_weight(), min_latency and student_policy currently select identical paths for the provided topology, resulting in overlapping performance curves. The min_latency implementation is correct. Consider using different markers and plotting styles in plot_metric() to make both curves visible. You may also examine whether your custom policy meaningfully differs from minimum-latency routing.
##- Failed request timing:
    - In simulate(), the failed-link condition may record the previous successful hop's finish time rather than the actual failure time. Use the current link's finish_time to ensure finish_ms reflects when the request terminates.
##- Link utilization:
    - In simulate(), link_results currently stores busy_time as utilization. Since utilization represents the fraction of available capacity used, calculate it as busy_time / (capacity * simulation_duration).
##- Missing per-request results:
    - In run_experiments(), only summary and link results are saved. Collect and export request_df across all experiments, including the corresponding offered load and routing policy.
##- Summary output:
    - In summarize(), the function currently returns a list containing a dictionary. Return the dictionary directly and update run_experiments() to append that dictionary to global_summary.

________________________________________________________________________________________________________________________________________________
# CSC 4501 — QuantumNet Course Project

## Routing and Congestion in a Distributed Quantum Network

This repository contains the starter materials for the CSC 4501 Computer Networks course project.

The project uses a simplified distributed quantum network as an application context for classical networking concepts. **No prior quantum-computing knowledge is required.** The main topics are graph routing, reliability, capacity, queueing, congestion, throughput, and controlled experimental evaluation.

## Repository structure

```text
student/                            # Distribute as CSC4501-QuantumNet-Project
├── README.md
├── requirements.txt
├── data/
│   └── topology.json
├── docs/
│   ├── QuantumNet_Project_Spec.pdf
│   ├── QuantumNet_Project_Spec.tex
│   └── SUBMISSION_CHECKLIST.md
├── src/
│   └── quantumnet.py
└── outputs/
```

Read `docs/QuantumNet_Project_Spec.pdf` before beginning the implementation.

## Setup

Python 3.10 or later is recommended.

```bash
python -m venv .venv
```

Activate the environment and install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the project

From the `src/` directory:

```bash
python quantumnet.py \
    --topology ../data/topology.json \
    --output ../outputs/student_run \
    --requests 500 \
    --seed 42
```

The starter file is intentionally incomplete. Complete the numbered `TODO` sections according to the project specification.

## Required routing policies

Your final implementation must include:

1. minimum-hop routing;
2. minimum-latency routing;
3. maximum-reliability routing; and
4. one student-designed routing policy using at least two link properties.

## Required final figures

Your completed implementation must generate:

- network topology;
- request success rate vs. offered load;
- average end-to-end latency vs. offered load;
- throughput vs. offered load; and
- average queue waiting time vs. offered load.

Use a fixed random seed for the results reported in your submission.
