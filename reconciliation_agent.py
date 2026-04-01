"""
ReconciliationAgent
-------------------
Compares platform_transactions.csv against bank_settlements.csv and
classifies every record into one of five categories:

    matched_transactions      – id in both, amount matches, settled in March
    late_settlements          – id in both, settlement_date outside March 2026
    duplicate_bank_entries    – same transaction_id appears >1 time in bank file
    amount_mismatches         – id in both, but amounts differ
    orphan_bank_transactions  – id only in bank file (no platform record)

Returns a structured result dictionary that downstream agents
(AnomalyDetectionAgent, ReportingAgent, …) can consume directly.
"""

import pandas as pd
from datetime import date


class ReconciliationAgent:
    """Agent responsible for matching and classifying payment records."""

    MARCH_START = date(2026, 3, 1)
    MARCH_END   = date(2026, 3, 31)

    def __init__(
        self,
        platform_path: str = "data/platform_transactions.csv",
        settlements_path: str = "data/bank_settlements.csv",
    ):
        self.platform_path   = platform_path
        self.settlements_path = settlements_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reconcile_transactions(self) -> dict:
        """
        Load both datasets, classify every record, print a summary,
        and return the full reconciliation result dictionary.

        Returns
        -------
        dict with keys:
            matched_transactions
            late_settlements
            duplicate_bank_entries
            amount_mismatches
            orphan_bank_transactions
        """
        platform_df, settlements_df = self._load_data()

        results = {
            "matched_transactions":   [],
            "late_settlements":       [],
            "duplicate_bank_entries": [],
            "amount_mismatches":      [],
            "orphan_bank_transactions": [],
        }

        # ── Step 1: duplicate bank entries ────────────────────────────
        # Identified before de-duplication so we capture every duplicate row.
        dup_mask = settlements_df.duplicated(subset=["transaction_id"], keep=False)
        dup_ids  = set(settlements_df.loc[dup_mask, "transaction_id"])

        for txn_id in dup_ids:
            dup_rows = settlements_df[settlements_df["transaction_id"] == txn_id]
            results["duplicate_bank_entries"].append(
                {
                    "transaction_id": txn_id,
                    "occurrences":    len(dup_rows),
                    "rows": dup_rows.to_dict(orient="records"),
                }
            )

        # Work with one bank record per transaction_id for the remaining checks
        # (keep first occurrence — the duplicate is already captured above).
        bank_deduped = settlements_df.drop_duplicates(
            subset=["transaction_id"], keep="first"
        ).set_index("transaction_id")

        platform_indexed = platform_df.set_index("transaction_id")

        platform_ids  = set(platform_indexed.index)
        bank_ids      = set(bank_deduped.index)

        # ── Step 2: orphan bank transactions ─────────────────────────
        orphan_ids = bank_ids - platform_ids
        for txn_id in orphan_ids:
            row = bank_deduped.loc[txn_id]
            results["orphan_bank_transactions"].append(
                {
                    "transaction_id":  txn_id,
                    "settlement_date": str(row["settlement_date"]),
                    "amount":          row["amount"],
                }
            )

        # ── Step 3: classify matched / late / amount-mismatch ─────────
        common_ids = platform_ids & bank_ids

        for txn_id in common_ids:
            plat_row = platform_indexed.loc[txn_id]
            bank_row = bank_deduped.loc[txn_id]

            plat_amount      = round(float(plat_row["amount"]), 2)
            bank_amount      = round(float(bank_row["amount"]), 2)
            settlement_date  = pd.to_datetime(bank_row["settlement_date"]).date()
            transaction_date = pd.to_datetime(plat_row["transaction_date"]).date()

            in_march = self.MARCH_START <= settlement_date <= self.MARCH_END
            amounts_match = plat_amount == bank_amount

            record = {
                "transaction_id":  txn_id,
                "transaction_date": str(transaction_date),
                "platform_amount":  plat_amount,
                "bank_amount":      bank_amount,
                "settlement_date":  str(settlement_date),
            }

            if not in_march:
                # Gap 1 — late settlement
                results["late_settlements"].append(
                    {**record, "amount_match": amounts_match}
                )
            elif not amounts_match:
                # Gap 3 — amount / rounding mismatch
                results["amount_mismatches"].append(
                    {
                        **record,
                        "difference": round(bank_amount - plat_amount, 4),
                    }
                )
            else:
                # Fully matched
                results["matched_transactions"].append(record)

        # ── Step 4: print summary ─────────────────────────────────────
        self._print_summary(platform_df, settlements_df, results)

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        platform_df   = pd.read_csv(self.platform_path,   parse_dates=["transaction_date"])
        settlements_df = pd.read_csv(self.settlements_path, parse_dates=["settlement_date"])
        return platform_df, settlements_df

    @staticmethod
    def _print_summary(
        platform_df: pd.DataFrame,
        settlements_df: pd.DataFrame,
        results: dict,
    ) -> None:
        sep = "=" * 60

        print(f"\n{sep}")
        print("  RECONCILIATION AGENT — SUMMARY")
        print(sep)
        print(f"  Total platform transactions  : {len(platform_df)}")
        print(f"  Total bank settlement records: {len(settlements_df)}")
        print(sep)
        print(f"  ✅ Matched transactions       : {len(results['matched_transactions'])}")
        print(f"  🕐 Late settlements           : {len(results['late_settlements'])}")
        print(f"  🔁 Duplicate bank entries     : {len(results['duplicate_bank_entries'])}")
        print(f"  ⚠️  Amount mismatches          : {len(results['amount_mismatches'])}")
        print(f"  ❓ Orphan bank transactions   : {len(results['orphan_bank_transactions'])}")
        print(sep)

        # ── Detail blocks ─────────────────────────────────────────────
        if results["late_settlements"]:
            print("\n  🕐 LATE SETTLEMENTS:")
            for r in results["late_settlements"]:
                print(
                    f"     {r['transaction_id']} | txn {r['transaction_date']} "
                    f"→ settled {r['settlement_date']} | "
                    f"amount_match={r['amount_match']}"
                )

        if results["duplicate_bank_entries"]:
            print("\n  🔁 DUPLICATE BANK ENTRIES:")
            for r in results["duplicate_bank_entries"]:
                print(
                    f"     {r['transaction_id']} appears "
                    f"{r['occurrences']}× in bank settlements"
                )

        if results["amount_mismatches"]:
            print("\n  ⚠️  AMOUNT MISMATCHES:")
            for r in results["amount_mismatches"]:
                print(
                    f"     {r['transaction_id']} | platform ${r['platform_amount']:.2f} "
                    f"vs bank ${r['bank_amount']:.2f} "
                    f"(diff ${r['difference']:+.4f})"
                )

        if results["orphan_bank_transactions"]:
            print("\n  ❓ ORPHAN BANK TRANSACTIONS:")
            for r in results["orphan_bank_transactions"]:
                print(
                    f"     {r['transaction_id']} | "
                    f"settled {r['settlement_date']} | "
                    f"amount ${r['amount']:.2f}"
                )

        print(f"{sep}\n")
