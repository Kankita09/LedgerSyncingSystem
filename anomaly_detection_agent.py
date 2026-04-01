"""
AnomalyDetectionAgent
---------------------
Consumes the reconciliation result dictionary produced by ReconciliationAgent
and converts each detected mismatch into a structured anomaly record that
explains *what* went wrong and *why* the platform/bank totals diverge.

Anomaly categories
------------------
    late_settlement_anomalies       – settlement date falls outside March 2026
    duplicate_entry_anomalies       – same transaction_id appears >1× in bank file
    rounding_difference_anomalies   – amount difference ≤ ROUNDING_THRESHOLD
    orphan_refund_anomalies         – negative amount with no platform counterpart

Returns a dict that can be passed directly to ExplanationAgent / ReportingAgent.
"""


class AnomalyDetectionAgent:
    """Agent responsible for interpreting reconciliation mismatches as anomalies."""

    # Differences at or below this value are classified as rounding issues
    ROUNDING_THRESHOLD = 0.05

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_anomalies(self, reconciliation_results: dict) -> dict:
        """
        Analyse the reconciliation results dictionary and produce structured
        anomaly records for each mismatch category.

        Parameters
        ----------
        reconciliation_results : dict
            Output of ReconciliationAgent.reconcile_transactions()

        Returns
        -------
        dict with keys:
            late_settlement_anomalies
            duplicate_entry_anomalies
            rounding_difference_anomalies
            orphan_refund_anomalies
        """
        anomalies = {
            "late_settlement_anomalies":     [],
            "duplicate_entry_anomalies":     [],
            "rounding_difference_anomalies": [],
            "orphan_refund_anomalies":       [],
        }

        self._detect_late_settlements(reconciliation_results, anomalies)
        self._detect_duplicates(reconciliation_results, anomalies)
        self._detect_rounding_differences(reconciliation_results, anomalies)
        self._detect_orphan_refunds(reconciliation_results, anomalies)

        self._print_summary(anomalies)

        return anomalies

    # ------------------------------------------------------------------
    # Private detection methods
    # ------------------------------------------------------------------

    def _detect_late_settlements(
        self, reconciliation_results: dict, anomalies: dict
    ) -> None:
        """
        Gap 1 — Settlement date falls outside the March 2026 month-end cutoff.
        These entries are absent from the March bank report even though the
        platform recorded the payment during March.
        """
        for record in reconciliation_results.get("late_settlements", []):
            txn_id          = record["transaction_id"]
            txn_date        = record["transaction_date"]
            settlement_date = record["settlement_date"]

            anomalies["late_settlement_anomalies"].append(
                {
                    "transaction_id":  txn_id,
                    "issue_type":      "LATE_SETTLEMENT",
                    "short_explanation": (
                        f"Transaction {txn_id} was recorded on the platform on "
                        f"{txn_date} but did not settle until {settlement_date}, "
                        f"which is after the March month-end cutoff. "
                        f"This causes a temporary reconciliation gap where the "
                        f"platform shows the payment but the bank statement does not."
                    ),
                    "transaction_date":  txn_date,
                    "settlement_date":   settlement_date,
                    "amount_match":      record.get("amount_match", True),
                }
            )

    def _detect_duplicates(
        self, reconciliation_results: dict, anomalies: dict
    ) -> None:
        """
        Gap 2 — The same transaction_id appears more than once in the bank
        settlement file, inflating the bank's total and making it higher than
        the platform total for that transaction.
        """
        for record in reconciliation_results.get("duplicate_bank_entries", []):
            txn_id     = record["transaction_id"]
            count      = record["occurrences"]
            rows       = record.get("rows", [])
            amount     = rows[0]["amount"] if rows else "N/A"

            anomalies["duplicate_entry_anomalies"].append(
                {
                    "transaction_id": txn_id,
                    "issue_type":     "DUPLICATE_BANK_ENTRY",
                    "short_explanation": (
                        f"Transaction {txn_id} appears {count} times in the bank "
                        f"settlement file (amount: ${amount:.2f} each). "
                        f"Duplicate entries inflate the bank total by "
                        f"${amount * (count - 1):.2f}, creating a systematic "
                        f"overpayment risk and reconciliation mismatch."
                    ),
                    "occurrences": count,
                    "duplicated_amount": amount,
                    "inflation":  round(amount * (count - 1), 2),
                }
            )

    def _detect_rounding_differences(
        self, reconciliation_results: dict, anomalies: dict
    ) -> None:
        """
        Gap 3 — The settled amount differs from the platform amount by a very
        small margin (≤ ROUNDING_THRESHOLD).  These are classified as rounding
        anomalies rather than genuine financial discrepancies.
        """
        for record in reconciliation_results.get("amount_mismatches", []):
            diff = abs(record.get("difference", 0))

            if diff <= self.ROUNDING_THRESHOLD:
                txn_id       = record["transaction_id"]
                plat_amount  = record["platform_amount"]
                bank_amount  = record["bank_amount"]

                anomalies["rounding_difference_anomalies"].append(
                    {
                        "transaction_id": txn_id,
                        "issue_type":     "ROUNDING_DIFFERENCE",
                        "short_explanation": (
                            f"Transaction {txn_id} shows a minor amount discrepancy: "
                            f"platform recorded ${plat_amount:.2f} while the bank "
                            f"settled ${bank_amount:.2f} (difference: "
                            f"${record['difference']:+.4f}). "
                            f"This is within the rounding tolerance "
                            f"(≤ ${self.ROUNDING_THRESHOLD:.2f}) and is likely caused "
                            f"by floating-point rounding in payment processing systems."
                        ),
                        "platform_amount": plat_amount,
                        "bank_amount":     bank_amount,
                        "difference":      record["difference"],
                        "settlement_date": record.get("settlement_date"),
                    }
                )

    def _detect_orphan_refunds(
        self, reconciliation_results: dict, anomalies: dict
    ) -> None:
        """
        Gap 4 — A negative-amount bank entry has no matching platform transaction.
        This indicates a refund was processed at the bank level without a
        corresponding refund record on the platform, creating a phantom credit.
        """
        for record in reconciliation_results.get("orphan_bank_transactions", []):
            amount = float(record["amount"])

            if amount < 0:
                txn_id          = record["transaction_id"]
                settlement_date = record["settlement_date"]

                anomalies["orphan_refund_anomalies"].append(
                    {
                        "transaction_id": txn_id,
                        "issue_type":     "ORPHAN_REFUND",
                        "short_explanation": (
                            f"Bank entry {txn_id} records a refund of "
                            f"${abs(amount):.2f} (settled {settlement_date}) "
                            f"with no matching original transaction on the platform. "
                            f"This orphan refund reduces the bank total without any "
                            f"corresponding platform debit, causing the platform "
                            f"and bank totals to diverge."
                        ),
                        "refund_amount":   amount,
                        "settlement_date": settlement_date,
                    }
                )

    # ------------------------------------------------------------------
    # Private display helper
    # ------------------------------------------------------------------

    @staticmethod
    def _print_summary(anomalies: dict) -> None:
        sep = "=" * 60

        total = sum(len(v) for v in anomalies.values())

        print(f"\n{sep}")
        print("  ANOMALY DETECTION AGENT — SUMMARY")
        print(sep)
        print(f"  Total anomalies detected        : {total}")
        print(sep)
        print(
            f"  🕐 Late settlement anomalies    : "
            f"{len(anomalies['late_settlement_anomalies'])}"
        )
        print(
            f"  🔁 Duplicate entry anomalies    : "
            f"{len(anomalies['duplicate_entry_anomalies'])}"
        )
        print(
            f"  ⚠️  Rounding difference anomalies: "
            f"{len(anomalies['rounding_difference_anomalies'])}"
        )
        print(
            f"  💸 Orphan refund anomalies      : "
            f"{len(anomalies['orphan_refund_anomalies'])}"
        )
        print(sep)

        # ── Per-anomaly detail blocks ──────────────────────────────────
        for category, label in [
            ("late_settlement_anomalies",     "🕐 LATE SETTLEMENTS"),
            ("duplicate_entry_anomalies",     "🔁 DUPLICATE ENTRIES"),
            ("rounding_difference_anomalies", "⚠️  ROUNDING DIFFERENCES"),
            ("orphan_refund_anomalies",       "💸 ORPHAN REFUNDS"),
        ]:
            if anomalies[category]:
                print(f"\n  {label}:")
                for a in anomalies[category]:
                    print(f"\n    [{a['issue_type']}] {a['transaction_id']}")
                    # Word-wrap the explanation at 56 characters
                    words = a["short_explanation"].split()
                    line, prefix = "    ", "      "
                    for word in words:
                        if len(line) + len(word) + 1 > 60:
                            print(line)
                            line = prefix + word
                        else:
                            line += (" " if line.strip() else "") + word
                    if line.strip():
                        print(line)

        print(f"\n{sep}\n")
