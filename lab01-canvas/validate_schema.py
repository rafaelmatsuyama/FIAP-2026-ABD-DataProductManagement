"""Schema & Business Rules Validator for Lab 01.

Validates transactions.parquet dataset against schema_spec.json requirements using DuckDB.
"""

import json
from pathlib import Path
import sys

try:
    import duckdb
except ImportError:
    print("[ERROR] DuckDB is not installed. Run 'pip install -r ../requirements-aula01.txt' first.")
    sys.exit(1)


def find_or_copy_parquet() -> Path:
    """Find transactions.parquet in lab01 or copy from lab00-setup."""
    local_path = Path("data/transactions.parquet")
    if local_path.exists():
        return local_path

    # Check in lab00-setup
    source_path = Path("../lab00-setup/data/transactions.parquet")
    if source_path.exists():
        local_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(source_path, local_path)
        print(f"[*] Dataset synchronized from '{source_path}' to '{local_path}'.")
        return local_path

    # Generate if not found anywhere
    local_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""
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
            FROM range(1000)
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
        COPY raw_transactions TO '{local_path.as_posix()}' (FORMAT PARQUET);
    """)
    print(f"[*] Synthetic dataset generated at '{local_path}'.")
    return local_path


def main():
    print("=" * 70)
    print("  📋 LAB 01: SCHEMA AUDIT & DATA PRODUCT COMPLIANCE")
    print("=" * 70)

    spec_file = Path("schema_spec.json")
    if not spec_file.exists():
        print(f"[ERROR] Specification file '{spec_file}' not found.")
        sys.exit(1)

    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    parquet_path = find_or_copy_parquet()

    con = duckdb.connect()
    table_name = "transactions_source"
    con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM '{parquet_path.as_posix()}';")

    # 1. Total records
    total_records = con.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
    print(f"  [i] Data Product: '{spec.get('product_name')}' (v{spec.get('version')})")
    print(f"  [i] Total Records Analyzed: {total_records}\n")

    results = []
    print("--- 1. Mandatory Fields Validation (Not Null) ---")
    for field in spec["fields"]:
        f_name = field["name"]
        if field.get("required"):
            null_count = con.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {f_name} IS NULL;").fetchone()[0]
            if null_count == 0:
                print(f"  [PASS] Field '{f_name}': 0 nulls found.")
                results.append(True)
            else:
                print(f"  [FAIL] Field '{f_name}': {null_count} null records found!")
                results.append(False)

    print("\n--- 2. Primary Key Uniqueness Validation ---")
    for field in spec["fields"]:
        f_name = field["name"]
        if field.get("unique"):
            distinct_count = con.execute(f"SELECT COUNT(DISTINCT {f_name}) FROM {table_name};").fetchone()[0]
            if distinct_count == total_records:
                print(f"  [PASS] Key '{f_name}': 100% unique ({distinct_count}/{total_records}).")
                results.append(True)
            else:
                diff = total_records - distinct_count
                print(f"  [FAIL] Key '{f_name}': {diff} duplicate keys detected!")
                results.append(False)

    print("\n--- 3. Allowed Domain Values Validation ---")
    for field in spec["fields"]:
        f_name = field["name"]
        allowed = field.get("allowed_values")
        if allowed:
            allowed_sql = ", ".join([f"'{v}'" for v in allowed])
            invalid_count = con.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {f_name} NOT IN ({allowed_sql});"
            ).fetchone()[0]
            if invalid_count == 0:
                print(f"  [PASS] Domain of '{f_name}' {allowed}: 100% compliant.")
                results.append(True)
            else:
                print(f"  [FAIL] Domain of '{f_name}': {invalid_count} invalid values outside {allowed}!")
                results.append(False)

    print("\n--- 4. Numerical Business Rules Validation ---")
    for field in spec["fields"]:
        f_name = field["name"]
        min_val = field.get("minimum")
        if min_val is not None:
            invalid_min = con.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {f_name} < {min_val};"
            ).fetchone()[0]
            if invalid_min == 0:
                print(f"  [PASS] Rule '{f_name} >= {min_val}': 100% compliant.")
                results.append(True)
            else:
                print(f"  [FAIL] Rule '{f_name} >= {min_val}': {invalid_min} records violate minimum value!")
                results.append(False)

    print("\n" + "=" * 70)
    if all(results):
        print("  [OK] FULL COMPLIANCE: DATASET MEETS 100% OF DATA PRODUCT CANVAS REQUIREMENTS!")
    else:
        print("  [FAIL] VIOLATIONS DETECTED: Dataset requires fixes prior to publication.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
