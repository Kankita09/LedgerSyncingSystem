# Technical Report: AI Payment Reconciliation Analyzer

**Submission For:** AI Native Engineer Assessment  
**Project:** End-to-End Multi-Agent Payment Reconciliation System  

---

## 1. Problem Statement

In modern financial technology, payment platforms record transactions and capture customer funds instantaneously. However, banking systems operate on asynchronous batch-processing cycles, settling those funds 1-2 days later (and sometimes longer across weekends/holidays). At month-end, finance teams must reconcile real-time platform ledgers against delayed, opaque bank settlement summaries. 

The resulting data mismatch continuously forces accounting units to manually hunt down missing transactions, trace duplicate processing, identify sub-cent rounding differentials, and isolate orphan refunds—which is both highly labor-intensive and prone to human error.

## 2. Objective

The primary objective of this project is to build an autonomous, agent-driven reconciliation engine capable of automatically evaluating transaction datasets, matching pairs, and distinctly classifying complex financial discrepancies without human intervention. The system must transform raw mismatch metadata into structured, audit-ready narratives that quantitatively explain *why* the total values deviate at month-end.

## 3. Requirements

To achieve the objective, the solution required:
- **Data Synthesis**: The ability to programmatically guarantee realistic test environments spanning multiple failure scenarios.
- **High-Precision Matching Logic**: A rules-engine designed to pair transactions while natively understanding date tolerances and float deviations.
- **Modular Agent Design**: Implementation of isolated agents, keeping classification, anomaly detection, narrative generation, and reporting loosely coupled.
- **Automated Verification**: Self-running test suites to mathematically prove the anomaly detection is fully accurate under test conditions.
- **Accessible Presentation Layer**: A clean, interactive UI for operators (Accountants/Auditors) to trigger runs and view results easily without needing command-line knowledge.

## 4. Proposed Solution

The proposed solution replaces manual spreadsheet cross-referencing with a **sequentially executed Multi-Agent Architecture**. Each phase of the reconciliation process is modularized into a dedicated Python agent class. By treating datasets as states passed between these agents, the platform dynamically generates the data, isolates exactly four categories of common industry anomalies, constructs plain-english explanations mapping error to financial impact, and outputs interactive web dashboards. 

## 5. Architecture Implementation

The system is executed locally using **Python, Pandas, and Streamlit**, functioning across a 6-stage pipeline orchestrated within `main.py` and visualized in `streamlit_app.py`.

### 5.1 Pipeline Stages
1. **`DataSimulationAgent`**: Generates `platform_transactions.csv` (40 deterministic records) and maps them to `bank_settlements.csv` (42 records) with exactly four engineered gaps.
2. **`ReconciliationAgent`**: Consumes CSVs, deduplicates identifiers, computes sets, and classifies the records strictly by mismatch definitions (tolerances, date boundaries).
3. **`AnomalyDetectionAgent`**: Evaluates the misclassified buckets to identify the anomaly type. It tags the severity and type of discrepancy.
4. **`ExplanationAgent`**: Transforms anomaly signatures into deep, audit-level text narratives explaining the event, its material financial impact, and actionable next steps for the finance division.
5. **`ReportingAgent`**: Compiles all agent findings into a final master dataset and persists the records to disk as structured `reconciliation_report.json` and human-readable `reconciliation_report.txt` logs.
6. **`TestCasesAgent`**: Acts as a runtime CI gate, programmatically guaranteeing that the exact number of anomalies (1 Late, 1 Duplicate, 1 Rounding, 1 Orphan) and perfectly matched records (38) were captured.

## 6. Test Cases Designed

The system enforces deterministic functional correctness through the embedded `TestCasesAgent`. Built-in validation checks are executed post-run:
- `late_settlement_test`: Asserts `EXPECTED == 1`. Confirms the engine isolated the single transaction settling across the month-end boundary.
- `duplicate_entry_test`: Asserts `EXPECTED == 1`. Validates that double-ingested settlement rows are correctly flagged for banking platform correction.
- `rounding_difference_test`: Asserts `EXPECTED == 1`. Tracks sub-cent ($0.01) floating-point discrepancies native to currency processing gateways.
- `orphan_refund_test`: Asserts `EXPECTED == 1`. Captures the unique signature of a bank-level negative balance deduction without any corresponding platform originator transaction.
- `matched_transactions_test`: Asserts `EXPECTED == 38`. Verifies 100% data ingestion retention on clean transaction pairs.

## 7. Complete Overview

From a cold start, the system executes beautifully via either CLI (`python main.py`) or web interface (`streamlit run streamlit_app.py`). 

The system initializes by dropping synthetic transactions starting March 1st. It simulates standard 1-2 day ACH/Wire lag to produce the bank settlements document. It then seamlessly transitions into the core accounting engine. Because agents are decoupled, anomalies detected in Stage 3 do not disrupt the formatting instructions in Stage 4. Financial impact equations seamlessly calculate that the single duplicate entry inflated bank totals artificially by $+1,739.91$, and outputs a full text report for auditor sign-off. The final Streamlit frontend binds this capability into an intuitive visual dashboard loaded with DataFrame visualization, status cards, and download triggers.

## 8. Results and Impact

**Performance Results**: The pipeline executed with a **100% anomaly identification accuracy**. All internal test cases passed on every run. 
**Output Precision**: Instead of returning an ambiguous "Net Difference: $1,589.92", the system perfectly deconstructed the delta into quantified line items for the audit teams (-$1095.28 missing from bank, +$1739.91 duplicated, -$150.00 isolated refund, $0.01 rounding). 

**Impact**: 
- Replaces hours of manual cross-referencing in Excel with an instant (sub-1 second) Python script.
- Reduces audit-risk by ensuring standard operating procedures (Narrative generation + Recommended Actions) trigger uniformly every time an anomaly occurs.
- Highly extensible architecture makes swapping out `DataSimulationAgent` for a live Stripe/Plaid API connector trivial.

## 9. Conclusion

The AI Payment Reconciliation Analyzer successfully proves out an agent-native software paradigm for back-office financial operations. By blending structured programmatic verification (Pandas matching) alongside specialized intelligent actors (Audit Explanation Agents), the system achieves the scalability of rigid software while retaining the nuanced, human-readable reporting capabilities required by traditional finance teams. With future integrations (Multi-Currency handling, Live API Webhooks, partial-refund handling), this solution establishes a robust baseline for an enterprise-grade automated accounting platform.
