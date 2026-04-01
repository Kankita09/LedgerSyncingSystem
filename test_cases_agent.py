class TestCasesAgent:
    def __init__(self):
        pass

    def run_tests(self, reconciliation_results, anomaly_results):
        # 1) Verify exactly one late settlement anomaly exists
        late_settlement_test = "PASS" if len(anomaly_results.get("late_settlement_anomalies", [])) == 1 else "FAIL"

        # 2) Verify exactly one duplicate bank entry anomaly exists
        duplicate_entry_test = "PASS" if len(anomaly_results.get("duplicate_entry_anomalies", [])) == 1 else "FAIL"

        # 3) Verify exactly one rounding difference anomaly exists
        rounding_difference_test = "PASS" if len(anomaly_results.get("rounding_difference_anomalies", [])) == 1 else "FAIL"

        # 4) Verify exactly one orphan refund anomaly exists
        orphan_refund_test = "PASS" if len(anomaly_results.get("orphan_refund_anomalies", [])) == 1 else "FAIL"

        # 5) Verify total matched transactions equals 38
        matched_transactions_test = "PASS" if len(reconciliation_results.get("matched_transactions", [])) == 38 else "FAIL"

        test_results = {
            "late_settlement_test": late_settlement_test,
            "duplicate_entry_test": duplicate_entry_test,
            "rounding_difference_test": rounding_difference_test,
            "orphan_refund_test": orphan_refund_test,
            "matched_transactions_test": matched_transactions_test
        }

        print("\nTEST RESULTS SUMMARY\n")
        print(f"Late settlement test: {late_settlement_test}")
        print(f"Duplicate entry test: {duplicate_entry_test}")
        print(f"Rounding difference test: {rounding_difference_test}")
        print(f"Orphan refund test: {orphan_refund_test}")
        print(f"Matched transactions test: {matched_transactions_test}\n")

        return test_results
