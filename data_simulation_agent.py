"""
DataSimulationAgent
-------------------
Generates synthetic datasets for:
  - platform_transactions.csv  (40 transactions, March 2026)
  - bank_settlements.csv       (settlements with intentional reconciliation gaps)

Reconciliation gaps introduced:
  1. One transaction settles in April instead of March  (late settlement)
  2. One duplicate entry in bank settlements            (duplicate)
  3. One small rounding difference in a settlement      (rounding mismatch)
  4. One refund entry with no matching platform txn     (orphan refund)
"""

import random
import os
import pandas as pd
from datetime import date, timedelta


class DataSimulationAgent:
    """Agent responsible for generating and persisting synthetic financial datasets."""

    TRANSACTION_COUNT = 40
    SEED = 42
    MARCH_START = date(2026, 3, 1)
    MARCH_END = date(2026, 3, 31)

    # Indices (0-based) of transactions chosen for the intentional gaps
    LATE_SETTLEMENT_IDX = 5      # gap 1: settles in April
    DUPLICATE_IDX = 12           # gap 2: duplicated in settlements
    ROUNDING_IDX = 20            # gap 3: tiny rounding discrepancy
    ROUNDING_DELTA = 0.01        # amount of the rounding difference

    # Orphan refund details (gap 4)
    ORPHAN_REFUND_ID = "TXN-REFUND-9999"
    ORPHAN_REFUND_AMOUNT = -150.00

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _random_date(rng: random.Random, start: date, end: date) -> date:
        delta = (end - start).days
        return start + timedelta(days=rng.randint(0, delta))

    @staticmethod
    def _random_amount(rng: random.Random) -> float:
        """Return a realistic transaction amount between $10 and $2,000."""
        return round(rng.uniform(10.0, 2000.0), 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_datasets(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate platform_transactions and bank_settlements DataFrames,
        save them to CSV, and print a summary.

        Returns
        -------
        platform_df : pd.DataFrame
        settlements_df : pd.DataFrame
        """
        rng = random.Random(self.SEED)

        # ── 1. Platform Transactions ───────────────────────────────────
        transactions = []
        for i in range(self.TRANSACTION_COUNT):
            txn_date = self._random_date(rng, self.MARCH_START, self.MARCH_END)
            amount = self._random_amount(rng)
            transactions.append(
                {
                    "transaction_id": f"TXN-{1000 + i:04d}",
                    "transaction_date": txn_date,
                    "amount": amount,
                }
            )

        platform_df = pd.DataFrame(transactions)

        # ── 2. Bank Settlements ────────────────────────────────────────
        settlements = []

        for idx, row in platform_df.iterrows():
            txn_date: date = row["transaction_date"]
            amount: float = row["amount"]
            txn_id: str = row["transaction_id"]

            # Gap 1 — late settlement: this txn settles in April
            if idx == self.LATE_SETTLEMENT_IDX:
                settlement_date = date(2026, 4, 1) + timedelta(days=rng.randint(0, 3))
            else:
                # Normal 1–2 day settlement lag
                lag = rng.randint(1, 2)
                raw_date = txn_date + timedelta(days=lag)
                # Clamp to March (unless it's the late one — handled above)
                settlement_date = min(raw_date, date(2026, 3, 31))

            # Gap 3 — rounding discrepancy: add a tiny delta to the settled amount
            if idx == self.ROUNDING_IDX:
                settled_amount = round(amount + self.ROUNDING_DELTA, 2)
            else:
                settled_amount = amount

            settlements.append(
                {
                    "transaction_id": txn_id,
                    "settlement_date": settlement_date,
                    "amount": settled_amount,
                }
            )

            # Gap 2 — duplicate: insert the same settlement record twice
            if idx == self.DUPLICATE_IDX:
                settlements.append(
                    {
                        "transaction_id": txn_id,
                        "settlement_date": settlement_date,
                        "amount": settled_amount,
                    }
                )

        # Gap 4 — orphan refund: a negative settlement with no platform counterpart
        orphan_settlement_date = date(2026, 3, 28)
        settlements.append(
            {
                "transaction_id": self.ORPHAN_REFUND_ID,
                "settlement_date": orphan_settlement_date,
                "amount": self.ORPHAN_REFUND_AMOUNT,
            }
        )

        settlements_df = pd.DataFrame(settlements).reset_index(drop=True)

        # ── 3. Persist to CSV ──────────────────────────────────────────
        platform_path = os.path.join(self.output_dir, "platform_transactions.csv")
        settlements_path = os.path.join(self.output_dir, "bank_settlements.csv")

        platform_df.to_csv(platform_path, index=False)
        settlements_df.to_csv(settlements_path, index=False)

        # ── 4. Print Summary ───────────────────────────────────────────
        self._print_summary(platform_df, settlements_df)

        return platform_df, settlements_df

    # ------------------------------------------------------------------
    # Private display helper
    # ------------------------------------------------------------------

    @staticmethod
    def _print_summary(platform_df: pd.DataFrame, settlements_df: pd.DataFrame) -> None:
        sep = "=" * 60

        print(f"\n{sep}")
        print("  DATA SIMULATION AGENT — DATASET SUMMARY")
        print(sep)

        # Platform transactions
        print("\n📋  PLATFORM TRANSACTIONS — First 5 Rows:")
        print(platform_df.head(5).to_string(index=False))
        print(f"\n  Total records : {len(platform_df)}")
        print(f"  Total amount  : ${platform_df['amount'].sum():,.2f}")

        print()

        # Bank settlements
        print("🏦  BANK SETTLEMENTS — First 5 Rows:")
        print(settlements_df.head(5).to_string(index=False))
        print(f"\n  Total records : {len(settlements_df)}")
        print(f"  Total amount  : ${settlements_df['amount'].sum():,.2f}")

        print(f"\n{sep}")
        print("  INTENTIONAL RECONCILIATION GAPS")
        print(sep)
        print(f"  Gap 1 — Late settlement  : TXN-{1000 + DataSimulationAgent.LATE_SETTLEMENT_IDX:04d} settles in April")
        print(f"  Gap 2 — Duplicate entry  : TXN-{1000 + DataSimulationAgent.DUPLICATE_IDX:04d} appears twice in settlements")
        print(f"  Gap 3 — Rounding diff    : TXN-{1000 + DataSimulationAgent.ROUNDING_IDX:04d} has +${DataSimulationAgent.ROUNDING_DELTA} rounding error")
        print(f"  Gap 4 — Orphan refund    : {DataSimulationAgent.ORPHAN_REFUND_ID} (${DataSimulationAgent.ORPHAN_REFUND_AMOUNT}) has no platform match")
        print(f"{sep}\n")
