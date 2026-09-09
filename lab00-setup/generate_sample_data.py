"""Sample data generator for MBA ABD - DPM Labs.

Generates transactions dataset in Parquet format for Data Product & Contract Labs.
"""

from pathlib import Path

try:
    import duckdb
except ImportError:
    print("DuckDB not installed. Run 'pip install duckdb' first.")
    exit(1)


def generate_transactions(num_records: int = 1000) -> None:
    """Generate synthetic transactions and write to data/transactions.parquet."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = data_dir / "transactions.parquet"

    conn = duckdb.connect(database=":memory:")

    # Generate synthetic transactional records using DuckDB SQL generators
    conn.execute(f"""
        CREATE TABLE raw_transactions AS
        WITH base AS (
            SELECT
                'TX_' || LPAD((range + 1)::VARCHAR, 6, '0') AS transaction_id,
                'CUST_' || LPAD(((range % 100) + 1)::VARCHAR, 4, '0') AS customer_id,
                ROUND((RANDOM() * 450 + 15.50)::NUMERIC, 2) AS amount,
                ['PIX', 'CREDIT_CARD', 'BOLETO'][FLOOR(RANDOM() * 3 + 1)::INT] AS payment_method,
                CASE WHEN range % 10 = 0 THEN 'FAILED' ELSE 'COMPLETED' END AS status,
                ['BRL', 'BRL', 'USD', 'EUR'][FLOOR(RANDOM() * 4 + 1)::INT] AS currency,
                TIMESTAMP '2026-09-01 10:00:00' + INTERVAL (range * 5) MINUTE AS created_at
            FROM range({num_records})
        )
        SELECT
            transaction_id,
            customer_id,
            amount,
            ROUND(amount * 0.02, 2) AS fee,
            payment_method,
            status,
            currency,
            created_at
        FROM base;
    """)

    # Export to Parquet
    conn.execute(
        f"COPY raw_transactions TO '{parquet_path.as_posix()}' (FORMAT PARQUET);"
    )

    # Get count and sample
    count = conn.execute("SELECT COUNT(*) FROM raw_transactions;").fetchone()[0]
    print(f"[OK] Gerado com sucesso: '{parquet_path}' ({count} registros).")

    # Show quick preview
    print("\nPreview dos primeiros 3 registros:")
    preview = conn.execute("SELECT * FROM raw_transactions LIMIT 3;").df()
    print(preview.to_string(index=False))


if __name__ == "__main__":
    generate_transactions()
