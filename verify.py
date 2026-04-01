import pandas as pd

pt = pd.read_csv("data/platform_transactions.csv")
bs = pd.read_csv("data/bank_settlements.csv")

print("=== PLATFORM TRANSACTIONS ===")
print(pt.head(5).to_string(index=False))
print("Total records :", len(pt))
print("Total amount  : $" + f"{pt['amount'].sum():,.2f}")

print()
print("=== BANK SETTLEMENTS ===")
print(bs.head(5).to_string(index=False))
print("Total records :", len(bs))
print("Total amount  : $" + f"{bs['amount'].sum():,.2f}")

print()
print("=== GAP VERIFICATION ===")

# Gap 1 — late settlement (April)
late = bs[pd.to_datetime(bs["settlement_date"]).dt.month == 4]
print("Gap 1 - April settlements :", late["transaction_id"].tolist())

# Gap 2 — duplicates
dups = bs[bs.duplicated(subset=["transaction_id"], keep=False)]
print("Gap 2 - Duplicate txn IDs :", dups["transaction_id"].unique().tolist())

# Gap 3 — rounding difference
merged = pt.merge(bs, on="transaction_id", suffixes=("_plat", "_bank"))
merged["diff"] = (merged["amount_bank"] - merged["amount_plat"]).round(4)
rounding = merged[merged["diff"] != 0]
print("Gap 3 - Rounding diffs    :")
print(rounding[["transaction_id", "amount_plat", "amount_bank", "diff"]].to_string(index=False))

# Gap 4 — orphan refund
orphan = bs[~bs["transaction_id"].isin(pt["transaction_id"])]
print("Gap 4 - Orphan refund     :")
print(orphan[["transaction_id", "amount"]].to_string(index=False))
