import duckdb
from pathlib import Path

db_path = Path("data/analytics.duckdb")
parquet_path = Path("data/transactions.parquet")

if not db_path.exists() or not parquet_path.exists():
    print("[ERROR] Files not found. Run 'python setup_duckdb.py'.")
    exit(1)

con = duckdb.connect(str(db_path))
con.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM '{parquet_path.as_posix()}';")
count = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
con.close()

print(f"[OK] Table transactions restored to canonical state with {count} clean records.")
