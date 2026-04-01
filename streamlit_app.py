import streamlit as st
import pandas as pd
import json
import os
from main import main

st.set_page_config(page_title="AI Payment Reconciliation Analyzer", layout="wide")

st.title("AI Payment Reconciliation Analyzer")

# 1. Run Simulation Button
st.header("Section 1: Run Simulation")
if st.button("Run Reconciliation Pipeline"):
    with st.spinner("Running agents pipeline..."):
        try:
            report, test_results = main()
            st.session_state['test_results'] = test_results
            st.success("Reconciliation completed successfully")
        except Exception as e:
            st.error(f"Pipeline execution failed: {e}")

# Try to load existing data
if not (os.path.exists("data/reconciliation_report.json") and os.path.exists("data/reconciliation_report.txt")):
    st.warning("No reconciliation data found. Please run the pipeline first.")
else:
    # Load JSON Report
    try:
        with open("data/reconciliation_report.json", "r") as f:
            report = json.load(f)
    except Exception as e:
        report = None
        st.warning("Could not parse reconciliation_report.json")

    st.header("Section 2: Dataset Overview")
    if report and "summary_statistics" in report:
        ss = report["summary_statistics"]
        fd = report.get("financial_difference", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Platform Transactions", ss.get("total_platform_transactions", 0))
            st.metric("Platform Total Amount", f"${ss.get('total_platform_amount', 0.0):,.2f}")
        with col2:
            st.metric("Total Bank Settlement Records", ss.get("total_bank_settlements", 0))
            st.metric("Bank Total Amount", f"${ss.get('total_bank_amount', 0.0):,.2f}")
        
        st.metric("Net Difference", f"${fd.get('net_difference', ss.get('net_difference_between_totals', 0.0)):,.2f}")

    st.header("Section 3: Detected Anomalies")
    if report and "anomaly_counts" in report:
        ac = report["anomaly_counts"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Late Settlements", ac.get("late_settlement_anomalies", 0))
        c2.metric("Duplicate Entries", ac.get("duplicate_entry_anomalies", 0))
        c3.metric("Rounding Differences", ac.get("rounding_difference_anomalies", 0))
        c4.metric("Orphan Refunds", ac.get("orphan_refund_anomalies", 0))

    st.header("Section 4: Detailed Explanations Table")
    if report and "explanations" in report and report["explanations"]:
        df_exp = pd.DataFrame(report["explanations"])
        st.dataframe(df_exp, use_container_width=True)
    else:
        st.info("No anomalies or explanations found.")

    st.header("Section 5: Test Results")
    # We might not have test_results saved inside the JSON. 
    # If the user just loaded the page without running the pipeline, we don't have the test_results object from main().
    # Let's run TestCasesAgent dynamically to show results, since it relies on current data,
    # OR, if it's explicitly requested not to modify agent logic, we can just run the test agent over loaded data?
    # Wait, `main()` returns `test_results`. If we want it strictly from `main()`, we can store it in st.session_state when "Run Reconciliation Pipeline" is clicked.
    if 'test_results' in st.session_state:
        tests = st.session_state['test_results']
    else:
        # We can dynamically re-run TestCasesAgent based on loaded data, BUT the data (reconciliation_results, anomaly_results)
        # isn't saved to JSON, only the final report is. 
        # Alternatively, we just display it if it's in session_state, otherwise prompt them to run.
        tests = None

    if tests:
        for k, v in tests.items():
            if v == "PASS":
                st.success(f"{k}: {v}")
            else:
                st.error(f"{k}: {v}")
    elif 'test_results' not in st.session_state and st.button("Show Test Results (Run tests independently)"):
        # Helper to just run the test agent if they haven't re-run the whole pipeline
        # Actually, let's just ask them to click Run Reconciliation Pipeline.
        st.info("Run the reconciliation pipeline to view fresh test results.")

    st.header("Section 6: Download Reports")
    colA, colB = st.columns(2)
    with colA:
        if os.path.exists("data/reconciliation_report.txt"):
            with open("data/reconciliation_report.txt", "r") as f:
                st.download_button("Download Report (TXT)", f.read(), file_name="reconciliation_report.txt")
    with colB:
        if os.path.exists("data/reconciliation_report.json"):
            with open("data/reconciliation_report.json", "r") as f:
                st.download_button("Download Report (JSON)", f.read(), file_name="reconciliation_report.json")
