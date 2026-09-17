from pathlib import Path
import duckdb

db_path = Path("data/analytics.duckdb")

if not db_path.exists():
    print("[ERROR] Database analytics.duckdb not found. Run 'python setup_duckdb.py' and 'dbt run'.")
    exit(1)

con = duckdb.connect(str(db_path))

print("\n=======================================================")
print("📊 DATA PRODUCT INSPECTION: fct_financial_transactions")
print("=======================================================\n")

# Check existing tables
tables = con.execute("SHOW TABLES;").fetchall()
table_names = [t[0] for t in tables]
print(f"Tables present in DuckDB: {table_names}\n")

if "fct_financial_transactions" in table_names:
    total_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions;").fetchone()[0]
    total_volume = con.execute("SELECT SUM(amount), SUM(fee), SUM(net_amount) FROM fct_financial_transactions;").fetchone()
    
    print(f"Total Settled Transactions (COMPLETED): {total_count:,}")
    print(f"Gross Transaction Volume: $ {total_volume[0]:,.2f}")
    print(f"Retained Take Rate / Fees: $ {total_volume[1]:,.2f}")
    print(f"Net Settled Volume:        $ {total_volume[2]:,.2f}\n")
    
    print("Sample of first 5 rows in Consumption Mart:")
    con.sql("SELECT transaction_id, customer_id, amount, net_amount, status, payment_method FROM fct_financial_transactions LIMIT 5;").show()
else:
    print("Table 'fct_financial_transactions' not yet created. Run 'dbt run --select marts'.")

con.close()
