# AI Payment Reconciliation Analyzer

This project is an agent-based reconciliation system that simulates platform and bank transaction datasets, detects mismatches, generates audit-style explanations, validates results with automated tests, and provides an interactive Streamlit dashboard.

## Problem Statement

Payment platforms record transactions instantly, but banks settle funds later. At month end these datasets should match, but discrepancies occur. This system detects and explains those discrepancies using a modular agent pipeline.

## Solution Overview

The system uses a multi-agent architecture consisting of:
- DataSimulationAgent
- ReconciliationAgent
- AnomalyDetectionAgent
- ExplanationAgent
- ReportingAgent
- TestCasesAgent

Each agent performs a specialized role in reconciliation analysis.

## Project Architecture

```
project/
│
├── agents/
├── data/
├── streamlit_app.py
├── main.py
├── requirements.txt
└── README.md
```

## Agent Responsibilities

- **DataSimulationAgent** generates synthetic transaction datasets with controlled reconciliation gaps.
- **ReconciliationAgent** compares platform and bank records and classifies mismatches.
- **AnomalyDetectionAgent** converts mismatches into structured anomaly categories.
- **ExplanationAgent** generates audit-style narratives with financial impact and recommended actions.
- **ReportingAgent** produces JSON and text reconciliation reports summarizing results.
- **TestCasesAgent** validates that all expected anomalies are detected correctly.

## Example Detected Issues

- late settlement
- duplicate bank entry
- rounding difference
- orphan refund

## How to Run the Project Locally

```bash
pip install -r requirements.txt
python main.py
```

## Running the Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will open at:
http://localhost:8501

## Output Reports Generated

The system produces:
- `data/reconciliation_report.json`
- `data/reconciliation_report.txt`

These contain structured reconciliation summaries and anomaly explanations.

## Automated Test Validation

TestCasesAgent verifies:
- late settlement detection
- duplicate entry detection
- rounding difference detection
- orphan refund detection
- matched transaction count validation

## Production Limitations

- This system assumes transaction IDs are consistent across platform and bank datasets, which may not hold in real-world payment processor integrations.
- It does not currently handle partial settlements, split payouts, or multi-currency conversions that can affect reconciliation accuracy.
- The pipeline assumes settlement delays of only 1–2 days and would require extension to support longer settlement windows or timezone-based cutoff differences.

## Tech Stack

- Python
- Pandas
- Streamlit

## Future Improvements

- support multi-currency reconciliation
- handle partial refunds and split settlements
- integrate real payment processor APIs
- deploy anomaly alerts as real-time monitoring signals

## Author Section

Author: <Your Name>
Role: AI Native Engineer Assessment Submission
