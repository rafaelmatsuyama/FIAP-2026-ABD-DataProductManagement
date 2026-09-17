import duckdb
from pathlib import Path

db_path = Path("data/analytics.duckdb")

if not db_path.exists():
    print("[ERROR] Database data/analytics.duckdb not found. Run 'python setup_duckdb.py' first.")
    exit(1)

con = duckdb.connect(str(db_path))

print("[!] Injecting synthetic anomalies into transactions table...")

# Insert corrupted transactions to trigger Quality Gate failure:
# 1. Negative amount (-999.50)
# 2. NULL transaction_id
# 3. Invalid status ('CORRUPTED_STATUS')
con.execute("""
    INSERT INTO transactions (transaction_id, customer_id, amount, fee, payment_method, status, currency, created_at)
    VALUES 
        (NULL, 'CUST_0001', -999.50, 0.00, 'PIX', 'CORRUPTED_STATUS', 'BRL', NOW()),
        ('TX_999999', 'CUST_0002', -150.00, 0.00, 'BITCOIN', 'UNKNOWN', 'XYZ', NOW());
""")

count = con.execute("SELECT COUNT(*) FROM transactions WHERE amount < 0 OR transaction_id IS NULL").fetchone()[0]
print(f"[OK] Anomalies successfully injected! {count} defective records inserted.")
print("Now run: soda scan -d analytics -c configuration.yml checks.yml")
con.close()
