from pathlib import Path
import duckdb

db_path = Path("data/analytics.duckdb")

if not db_path.exists():
    print("[ERROR] Database analytics.duckdb not found. Run 'python setup_duckdb.py' and 'dbt build'.")
    exit(1)

con = duckdb.connect(str(db_path))

print("\n=======================================================")
print("🧪 QUALITY INSPECTION: TABLES & DATA PRODUCTS")
print("=======================================================\n")

tables = con.execute("SHOW TABLES;").fetchall()
table_names = [t[0] for t in tables]
print(f"Active tables in DuckDB: {table_names}\n")

if "fct_financial_transactions" in table_names and "dim_customers" in table_names:
    tx_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions;").fetchone()[0]
    cust_count = con.execute("SELECT COUNT(*) FROM dim_customers;").fetchone()[0]
    
    print(f"✅ Customers Dimension: {cust_count:,} active records.")
    print(f"✅ Settled Transactions Fact: {tx_count:,} validated records.")
    
    # Manual referential integrity check
    orphans = con.execute("""
        SELECT COUNT(*) 
        FROM fct_financial_transactions f
        LEFT JOIN dim_customers c ON f.customer_id = c.customer_id
        WHERE c.customer_id IS NULL;
    """).fetchone()[0]
    
    print(f"🔍 Orphan records (Referential Integrity Violations): {orphans}")
    
    # Check negative amounts
    negatives = con.execute("SELECT COUNT(*) FROM fct_financial_transactions WHERE net_amount < 0;").fetchone()[0]
    print(f"🔍 Transactions with negative net amount: {negatives}\n")
    
    print("Sample join between Fact and Dimension:")
    con.sql("""
        SELECT 
            f.transaction_id,
            c.customer_name,
            c.customer_tier,
            f.amount,
            f.net_amount,
            f.status,
            f.payment_method
        FROM fct_financial_transactions f
        JOIN dim_customers c ON f.customer_id = c.customer_id
        LIMIT 5;
    """).show()
else:
    print("Analytical marts not yet materialized. Run 'dbt build --profiles-dir .'.")

con.close()
