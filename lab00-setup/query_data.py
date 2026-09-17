"""Query transactions dataset using Python DuckDB engine.

Executes schema inspection and aggregation queries directly on Parquet files.
"""

from pathlib import Path

try:
    import duckdb
except ImportError:
    print("[ERROR] DuckDB is not installed. Run 'pip install -r ../requirements-aula01.txt' first.")
    exit(1)


def main():
    parquet_file = Path("data/transactions.parquet")
    if not parquet_file.exists():
        print(f"[ERROR] File '{parquet_file}' not found.")
        print("Run 'python generate_sample_data.py' first.")
        exit(1)

    con = duckdb.connect()

    print("=" * 65)
    print("  🦆 ANALYTICAL QUERY VIA DUCKDB (IN-MEMORY)")
    print("=" * 65)

    print("\n--- 1. Schema & Type Inspection (DESCRIBE) ---")
    con.sql("DESCRIBE SELECT * FROM 'data/transactions.parquet';").show()

    print("\n--- 2. Aggregated Metrics by Payment Method ---")
    query_agg = """
        SELECT 
            payment_method,
            COUNT(*) AS total_transactions,
            ROUND(SUM(amount), 2) AS total_amount,
            ROUND(AVG(amount), 2) AS avg_ticket
        FROM 'data/transactions.parquet'
        GROUP BY payment_method
        ORDER BY total_amount DESC;
    """
    con.sql(query_agg).show()

    print("=" * 65)
    print("  [OK] DuckDB analytical processing executed successfully!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
