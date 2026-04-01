import pandas as pd
import json
import os

class ReportingAgent:
    def __init__(self):
        pass

    def generate_report(self, reconciliation_results, anomaly_results, explanation_results):
        # 1) Load both datasets
        platform_df = pd.read_csv("data/platform_transactions.csv")
        bank_df = pd.read_csv("data/bank_settlements.csv")

        # 2) Calculate and store
        total_platform_transactions = len(platform_df)
        total_bank_settlements = len(bank_df)
        total_platform_amount = round(platform_df['amount'].sum(), 2)
        total_bank_amount = round(bank_df['amount'].sum(), 2)
        net_difference_between_totals = round(total_bank_amount - total_platform_amount, 2)

        # 3) Count anomalies detected in each category
        late_settlement_anomalies = len(anomaly_results.get("late_settlement_anomalies", []))
        duplicate_entry_anomalies = len(anomaly_results.get("duplicate_entry_anomalies", []))
        rounding_difference_anomalies = len(anomaly_results.get("rounding_difference_anomalies", []))
        orphan_refund_anomalies = len(anomaly_results.get("orphan_refund_anomalies", []))

        # 4) Generate a structured reconciliation summary dictionary
        report_dict = {
            "summary_statistics": {
                "total_platform_transactions": total_platform_transactions,
                "total_bank_settlements": total_bank_settlements,
                "total_platform_amount": total_platform_amount,
                "total_bank_amount": total_bank_amount,
                "net_difference_between_totals": net_difference_between_totals
            },
            "anomaly_counts": {
                "late_settlement_anomalies": late_settlement_anomalies,
                "duplicate_entry_anomalies": duplicate_entry_anomalies,
                "rounding_difference_anomalies": rounding_difference_anomalies,
                "orphan_refund_anomalies": orphan_refund_anomalies
            },
            "financial_difference": {
                "net_difference": net_difference_between_totals
            },
            "explanations": explanation_results.get("explanations", [])
        }

        # 5) Print a readable reconciliation report
        print("RECONCILIATION SUMMARY\n")
        print(f"Total platform transactions: {total_platform_transactions}")
        print(f"Total bank settlement records: {total_bank_settlements}\n")
        print(f"Platform total amount: {total_platform_amount:.2f}")
        print(f"Bank total amount: {total_bank_amount:.2f}\n")
        print(f"Net difference: {net_difference_between_totals:.2f}\n")
        print(f"Late settlements: {late_settlement_anomalies}")
        print(f"Duplicate entries: {duplicate_entry_anomalies}")
        print(f"Rounding differences: {rounding_difference_anomalies}")
        print(f"Orphan refunds: {orphan_refund_anomalies}\n")
        print("These anomalies explain why the platform ledger and bank settlement totals differ at month end.\n")

        # 6) Save the report as JSON
        os.makedirs("data", exist_ok=True)
        with open("data/reconciliation_report.json", "w") as f:
            json.dump(report_dict, f, indent=4)

        # 7) Also create a simple text report
        with open("data/reconciliation_report.txt", "w") as f:
            f.write("RECONCILIATION SUMMARY\n\n")
            f.write(f"Total platform transactions: {total_platform_transactions}\n")
            f.write(f"Total bank settlement records: {total_bank_settlements}\n\n")
            f.write(f"Platform total amount: {total_platform_amount:.2f}\n")
            f.write(f"Bank total amount: {total_bank_amount:.2f}\n\n")
            f.write(f"Net difference: {net_difference_between_totals:.2f}\n\n")
            f.write(f"Late settlements: {late_settlement_anomalies}\n")
            f.write(f"Duplicate entries: {duplicate_entry_anomalies}\n")
            f.write(f"Rounding differences: {rounding_difference_anomalies}\n")
            f.write(f"Orphan refunds: {orphan_refund_anomalies}\n\n")
            f.write("These anomalies explain why the platform ledger and bank settlement totals differ at month end.\n")

        # 8) Return the final report dictionary
        return report_dict
