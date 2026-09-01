from pathlib import Path
import duckdb

data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)
db_path = data_dir / "analytics.duckdb"
parquet_path = data_dir / "transactions.parquet"

# Ensure parquet exists
if not parquet_path.exists():
    source_p = Path("../lab00-setup/data/transactions.parquet")
    if source_p.exists():
        import shutil
        shutil.copy2(source_p, parquet_path)

con = duckdb.connect(str(db_path))
con.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM '{parquet_path.as_posix()}';")
con.close()
print("Created analytics.duckdb with transactions table.")
