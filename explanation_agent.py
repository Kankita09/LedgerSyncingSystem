"""
ExplanationAgent
----------------
Transforms structured anomaly records produced by AnomalyDetectionAgent into
clear, audit-style explanations suitable for finance teams, auditors, and
operations analysts.

Each explanation entry contains:
    transaction_id       – the affected transaction
    issue_type           – category of anomaly
    detailed_explanation – narrative describing what happened and why
    financial_impact     – quantified or qualified effect on totals
    recommended_action   – actionable next step for the finance team

Returns a dict  {"explanations": [...]}  that feeds directly into ReportingAgent.
"""


class ExplanationAgent:
    """Agent responsible for converting anomaly records into audit narratives."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_explanations(self, anomaly_results: dict) -> dict:
        """
        Process every anomaly category and produce structured explanation
        entries.

        Parameters
        ----------
        anomaly_results : dict
            Output of AnomalyDetectionAgent.detect_anomalies()

        Returns
        -------
        dict  {"explanations": [list of explanation dicts]}
        """
        explanations: list[dict] = []

        self._explain_late_settlements(
            anomaly_results.get("late_settlement_anomalies", []),
            explanations,
        )
        self._explain_duplicates(
            anomaly_results.get("duplicate_entry_anomalies", []),
            explanations,
        )
        self._explain_rounding_differences(
            anomaly_results.get("rounding_difference_anomalies", []),
            explanations,
        )
        self._explain_orphan_refunds(
            anomaly_results.get("orphan_refund_anomalies", []),
            explanations,
        )

        result = {"explanations": explanations}
        self._print_narrative(result)
        return result

    # ------------------------------------------------------------------
    # Private explanation builders
    # ------------------------------------------------------------------

    @staticmethod
    def _explain_late_settlements(
        anomalies: list, explanations: list
    ) -> None:
        """
        Late settlements — payment crossed the month-end boundary.
        The platform captured the payment in March; the bank settled in April,
        so the transaction is missing from the March bank statement entirely.
        """
        for a in anomalies:
            txn_id          = a["transaction_id"]
            txn_date        = a.get("transaction_date", "N/A")
            settlement_date = a.get("settlement_date", "N/A")

            explanations.append(
                {
                    "transaction_id": txn_id,
                    "issue_type":     "LATE_SETTLEMENT",
                    "detailed_explanation": (
                        f"Transaction {txn_id} was captured on the platform on "
                        f"{txn_date} but the corresponding funds did not clear "
                        f"the banking system until {settlement_date}, which falls "
                        f"after the March 31, 2026 month-end cutoff. "
                        f"As a result, this transaction is visible in the platform "
                        f"ledger for March but is absent from the March bank "
                        f"settlement report. It will appear in the April bank "
                        f"statement instead, creating a temporary timing gap "
                        f"between the two records."
                    ),
                    "financial_impact": (
                        "Platform ledger overstates March receipts relative to "
                        "the bank statement by the amount of this transaction. "
                        "The gap self-corrects when the April bank statement is "
                        "received and matched."
                    ),
                    "recommended_action": (
                        "Flag this transaction as 'Timing Difference — Pending "
                        "April Settlement'. Re-run reconciliation after the "
                        "April bank statement is available to confirm clearance. "
                        "No financial adjustment is required at this stage."
                    ),
                }
            )

    @staticmethod
    def _explain_duplicates(
        anomalies: list, explanations: list
    ) -> None:
        """
        Duplicate entries — same transaction_id settled more than once in the
        bank file, inflating the bank total artificially.
        """
        for a in anomalies:
            txn_id    = a["transaction_id"]
            count     = a.get("occurrences", 2)
            amount    = a.get("duplicated_amount", 0.0)
            inflation = a.get("inflation", 0.0)

            explanations.append(
                {
                    "transaction_id": txn_id,
                    "issue_type":     "DUPLICATE_BANK_ENTRY",
                    "detailed_explanation": (
                        f"Transaction {txn_id} (amount: ${amount:.2f}) appears "
                        f"{count} times in the bank settlement file. "
                        f"Only one settlement record is expected per transaction. "
                        f"The extra {count - 1} occurrence(s) are duplicate entries "
                        f"likely introduced by a retry mechanism, a double-posting "
                        f"in the payment processor, or an ingestion error in the "
                        f"bank data pipeline. These duplicates inflate the bank "
                        f"settlement total by ${inflation:.2f} compared to the "
                        f"platform ledger."
                    ),
                    "financial_impact": (
                        f"Bank total is overstated by ${inflation:.2f} due to "
                        f"{count - 1} duplicate settlement record(s) for {txn_id}. "
                        f"This causes the platform-to-bank reconciliation to show "
                        f"an apparent surplus in the bank that does not reflect "
                        f"actual funds received."
                    ),
                    "recommended_action": (
                        f"Investigate the payment processor log for {txn_id} to "
                        f"confirm that only one settlement was actually processed. "
                        f"Remove or void the duplicate bank record(s) after "
                        f"confirmation. If a genuine double-payment occurred, "
                        f"initiate a reversal or refund process immediately."
                    ),
                }
            )

    @staticmethod
    def _explain_rounding_differences(
        anomalies: list, explanations: list
    ) -> None:
        """
        Rounding differences — cent-level discrepancies between the platform
        amount and the settled bank amount.
        """
        for a in anomalies:
            txn_id       = a["transaction_id"]
            plat_amount  = a.get("platform_amount", 0.0)
            bank_amount  = a.get("bank_amount", 0.0)
            diff         = a.get("difference", 0.0)
            settle_date  = a.get("settlement_date", "N/A")

            explanations.append(
                {
                    "transaction_id": txn_id,
                    "issue_type":     "ROUNDING_DIFFERENCE",
                    "detailed_explanation": (
                        f"Transaction {txn_id} shows a minor discrepancy between "
                        f"the platform-recorded amount (${plat_amount:.2f}) and "
                        f"the bank-settled amount (${bank_amount:.2f}), settled on "
                        f"{settle_date}. The difference of ${diff:+.4f} is "
                        f"sub-cent and falls within accepted rounding tolerance. "
                        f"Such differences commonly arise from floating-point "
                        f"arithmetic in payment gateways, intermediary currency "
                        f"conversion rounding, or truncation versus rounding "
                        f"policies applied differently across systems."
                    ),
                    "financial_impact": (
                        f"Net discrepancy of ${abs(diff):.4f} — immaterial for "
                        f"individual transactions. If the same rounding bias "
                        f"applies across many transactions, cumulative drift "
                        f"across large transaction volumes could become "
                        f"significant at an aggregate level."
                    ),
                    "recommended_action": (
                        "Post a rounding adjustment journal entry of "
                        f"${abs(diff):.4f} to clear the balance. "
                        "Review the payment gateway's rounding configuration "
                        "to align it with the platform's rounding rules and "
                        "prevent recurring cent-level differences. "
                        "Consider automating a tolerance-based auto-match rule "
                        "for differences ≤ $0.05 to reduce manual effort."
                    ),
                }
            )

    @staticmethod
    def _explain_orphan_refunds(
        anomalies: list, explanations: list
    ) -> None:
        """
        Orphan refunds — negative bank entries with no matching platform record.
        These reduce the bank total without a corresponding platform debit.
        """
        for a in anomalies:
            txn_id       = a["transaction_id"]
            refund_amt   = a.get("refund_amount", 0.0)
            settle_date  = a.get("settlement_date", "N/A")

            explanations.append(
                {
                    "transaction_id": txn_id,
                    "issue_type":     "ORPHAN_REFUND",
                    "detailed_explanation": (
                        f"Bank entry {txn_id} records a refund of "
                        f"${abs(refund_amt):.2f} credited on {settle_date}, "
                        f"but there is no corresponding transaction in the "
                        f"platform ledger. This is an orphan refund — the bank "
                        f"processed a credit without a matching original "
                        f"transaction being present in the platform data. "
                        f"Possible causes include: (1) the original transaction "
                        f"was never ingested into the platform due to a pipeline "
                        f"failure, (2) the refund was initiated externally via the "
                        f"bank or payment processor and not reflected in the "
                        f"platform, or (3) the refund relates to a transaction "
                        f"from a prior period that has since been archived."
                    ),
                    "financial_impact": (
                        f"Bank settlement total is understated by "
                        f"${abs(refund_amt):.2f} relative to the platform "
                        f"ledger. This unmatched credit reduces net bank receipts "
                        f"for March without a corresponding platform expense, "
                        f"causing a genuine financial discrepancy rather than a "
                        f"timing difference."
                    ),
                    "recommended_action": (
                        f"Immediately investigate the source of refund {txn_id}. "
                        f"Search payment processor logs, customer service records, "
                        f"and dispute management systems for the underlying "
                        f"transaction. If a platform transaction is found, ingest "
                        f"it retroactively and re-run reconciliation. "
                        f"If no original transaction exists, raise an audit "
                        f"exception for finance team review and consider reversing "
                        f"the bank credit if it was processed in error."
                    ),
                }
            )

    # ------------------------------------------------------------------
    # Private display helper
    # ------------------------------------------------------------------

    @staticmethod
    def _print_narrative(result: dict) -> None:
        explanations = result["explanations"]
        total = len(explanations)
        sep = "=" * 60

        print(f"\n{sep}")
        print("  EXPLANATION AGENT — RECONCILIATION NARRATIVE")
        print(sep)
        print(
            f"\n  {total} anomaly/anomalies explain why the platform ledger "
            f"does not fully\n  match the March bank settlement totals.\n"
        )

        for i, entry in enumerate(explanations, start=1):
            print(f"  {'─' * 56}")
            print(f"  [{i}] {entry['issue_type']}  |  {entry['transaction_id']}")
            print(f"  {'─' * 56}")

            # Word-wrap at ~58 chars
            for field, label in [
                ("detailed_explanation", "📝 Explanation"),
                ("financial_impact",     "💰 Financial Impact"),
                ("recommended_action",   "✅ Recommended Action"),
            ]:
                print(f"\n  {label}:")
                text = entry[field]
                words = text.split()
                line = "    "
                for word in words:
                    if len(line) + len(word) + 1 > 62:
                        print(line)
                        line = "    " + word
                    else:
                        line += (" " if line.strip() else "") + word
                if line.strip():
                    print(line)

            print()

        print(f"{sep}\n")
