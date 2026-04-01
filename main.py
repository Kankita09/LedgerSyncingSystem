"""
main.py
-------
Entry point for the agent-based reconciliation system.

Pipeline:
    1. DataSimulationAgent      — generate synthetic datasets
    2. ReconciliationAgent      — compare & classify mismatches
    3. AnomalyDetectionAgent    — interpret mismatches as anomaly insights
    4. ExplanationAgent         — produce audit-style reconciliation narratives
    5. ReportingAgent           — generate final JSON + TXT reconciliation report
"""

from agents.data_simulation_agent import DataSimulationAgent
from agents.reconciliation_agent import ReconciliationAgent
from agents.anomaly_detection_agent import AnomalyDetectionAgent
from agents.explanation_agent import ExplanationAgent
from agents.reporting_agent import ReportingAgent


def main():
    # ── Stage 1: Generate datasets ────────────────────────────────────
    print("🚀  Stage 1 — DataSimulationAgent")
    sim_agent = DataSimulationAgent(output_dir="data")
    sim_agent.generate_datasets()

    # ── Stage 2: Reconcile transactions ──────────────────────────────
    print("🔍  Stage 2 — ReconciliationAgent")
    rec_agent = ReconciliationAgent(
        platform_path="data/platform_transactions.csv",
        settlements_path="data/bank_settlements.csv",
    )
    reconciliation_results = rec_agent.reconcile_transactions()

    # ── Stage 3: Detect anomalies ────────────────────────────────────
    print("🧠  Stage 3 — AnomalyDetectionAgent")
    anomaly_agent = AnomalyDetectionAgent()
    anomaly_results = anomaly_agent.detect_anomalies(reconciliation_results)

    # ── Stage 4: Generate explanations ───────────────────────────────
    print("📝  Stage 4 — ExplanationAgent")
    explanation_agent = ExplanationAgent()
    explanation_results = explanation_agent.generate_explanations(anomaly_results)

    # ── Stage 5: Generate final report ───────────────────────────────
    print("📊  Stage 5 — ReportingAgent")
    reporting_agent = ReportingAgent()
    report = reporting_agent.generate_report(
        reconciliation_results,
        anomaly_results,
        explanation_results,
    )

    # ── Stage 6: Run Tests ───────────────────────────────────────────
    print("🧪  Stage 6 — TestCasesAgent")
    from agents.test_cases_agent import TestCasesAgent
    test_agent = TestCasesAgent()
    test_results = test_agent.run_tests(reconciliation_results, anomaly_results)

    return report, test_results



if __name__ == "__main__":
    main()


