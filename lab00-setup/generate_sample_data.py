"""Sample data generator for 8ABDR - DPM Labs.

Generates transactions dataset in Parquet format for Data Product & Contract Labs.
"""

from pathlib import Path

try:
    import duckdb
except ImportError:
    print("DuckDB not installed. Run 'pip install duckdb' first.")
    exit(1)


def generate_transactions(num_records: int = 2500) -> None:
    """Generate synthetic transactions and write to data/transactions.parquet."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = data_dir / "transactions.parquet"

    conn = duckdb.connect(database=":memory:")

    # Generate synthetic transactional records using DuckDB SQL generators
    conn.execute(f"""
        CREATE TABLE raw_transactions AS
        SELECT
            'tx_' || LPAD(range::VARCHAR, 6, '0') AS transaction_id,
            'cust_' || LPAD((FLOOR(RANDOM() * 500) + 1)::INT::VARCHAR, 4, '0') AS customer_id,
            ROUND((RANDOM() * 1500 + 10.50)::NUMERIC, 2) AS amount,
            ['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO'][FLOOR(RANDOM() * 4 + 1)::INT] AS payment_method,
            ['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'FAILED'][FLOOR(RANDOM() * 5 + 1)::INT] AS status,
            ['BRL', 'BRL', 'USD', 'EUR'][FLOOR(RANDOM() * 4 + 1)::INT] AS currency,
            TIMESTAMP '2026-01-01 00:00:00' + INTERVAL (RANDOM() * 60 * 24 * 60) MINUTE AS transaction_timestamp
        FROM range({num_records});
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
