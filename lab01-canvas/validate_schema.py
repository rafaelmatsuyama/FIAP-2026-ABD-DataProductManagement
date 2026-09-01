"""Schema & Business Rules Validator for Lab 01.

Validates transactions.parquet dataset against schema_spec.json requirements using DuckDB.
"""

import json
from pathlib import Path
import sys

try:
    import duckdb
except ImportError:
    print("[ERRO] DuckDB nao instalado. Execute 'pip install -r ../requirements.txt' primeiro.")
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
        print(f"[*] Base sincronizada de '{source_path}' para '{local_path}'.")
        return local_path

    # Generate if not found anywhere
    local_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE raw_transactions AS
        SELECT
            'tx_' || LPAD(range::VARCHAR, 6, '0') AS transaction_id,
            'cust_' || LPAD((FLOOR(RANDOM() * 500) + 1)::INT::VARCHAR, 4, '0') AS customer_id,
            ROUND((RANDOM() * 1500 + 10.50)::NUMERIC, 2) AS amount,
            ['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO'][FLOOR(RANDOM() * 4 + 1)::INT] AS payment_method,
            ['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'FAILED'][FLOOR(RANDOM() * 5 + 1)::INT] AS status,
            ['BRL', 'BRL', 'USD', 'EUR'][FLOOR(RANDOM() * 4 + 1)::INT] AS currency,
            TIMESTAMP '2026-01-01 00:00:00' + INTERVAL (RANDOM() * 60 * 24 * 60) MINUTE AS transaction_timestamp
        FROM range(2500);
        COPY raw_transactions TO '{local_path.as_posix()}' (FORMAT PARQUET);
    """)
    print(f"[*] Base sintetica gerada em '{local_path}'.")
    return local_path


def main():
    print("=" * 70)
    print("  📋 LAB 01: AUDITORIA DE SCHEMA & CONFORMIDADE DO PRODUTO DE DADOS")
    print("=" * 70)

    spec_file = Path("schema_spec.json")
    if not spec_file.exists():
        print(f"[ERRO] Arquivo de especificacao '{spec_file}' nao encontrado.")
        sys.exit(1)

    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    parquet_path = find_or_copy_parquet()

    con = duckdb.connect()
    table_name = "transactions_source"
    con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM '{parquet_path.as_posix()}';")

    # 1. Total records
    total_records = con.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
    print(f"  [i] Produto de Dados: '{spec.get('product_name')}' (v{spec.get('version')})")
    print(f"  [i] Total de Registros Analisados: {total_records}\n")

    results = []
    print("--- 1. Validacao de Campos Obrigatorios (Not Null) ---")
    for field in spec["fields"]:
        f_name = field["name"]
        if field.get("required"):
            null_count = con.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {f_name} IS NULL;").fetchone()[0]
            if null_count == 0:
                print(f"  [PASS] Campo '{f_name}': 0 nulos encontrados.")
                results.append(True)
            else:
                print(f"  [FAIL] Campo '{f_name}': {null_count} registros nulos!")
                results.append(False)

    print("\n--- 2. Validacao de Unicidade de Chave Primaria ---")
    for field in spec["fields"]:
        f_name = field["name"]
        if field.get("unique"):
            distinct_count = con.execute(f"SELECT COUNT(DISTINCT {f_name}) FROM {table_name};").fetchone()[0]
            if distinct_count == total_records:
                print(f"  [PASS] Chave '{f_name}': 100% unica ({distinct_count}/{total_records}).")
                results.append(True)
            else:
                diff = total_records - distinct_count
                print(f"  [FAIL] Chave '{f_name}': {diff} chaves duplicadas detectadas!")
                results.append(False)

    print("\n--- 3. Validacao de Dominios de Valores Permitidos ---")
    for field in spec["fields"]:
        f_name = field["name"]
        allowed = field.get("allowed_values")
        if allowed:
            allowed_sql = ", ".join([f"'{v}'" for v in allowed])
            invalid_count = con.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {f_name} NOT IN ({allowed_sql});"
            ).fetchone()[0]
            if invalid_count == 0:
                print(f"  [PASS] Dominio de '{f_name}' {allowed}: 100% conforme.")
                results.append(True)
            else:
                print(f"  [FAIL] Dominio de '{f_name}': {invalid_count} valores invalidos fora de {allowed}!")
                results.append(False)

    print("\n--- 4. Validacao de Regras Numericas de Negocio ---")
    for field in spec["fields"]:
        f_name = field["name"]
        min_val = field.get("minimum")
        if min_val is not None:
            invalid_min = con.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {f_name} < {min_val};"
            ).fetchone()[0]
            if invalid_min == 0:
                print(f"  [PASS] Regra '{f_name} >= {min_val}': 100% conforme.")
                results.append(True)
            else:
                print(f"  [FAIL] Regra '{f_name} >= {min_val}': {invalid_min} registros violam o valor minimo!")
                results.append(False)

    print("\n" + "=" * 70)
    if all(results):
        print("  [OK] CONFORMIDADE TOTAL: O DATASET ATENDE 100% AO DATA PRODUCT CANVAS!")
    else:
        print("  [FAIL] VIOLACOES DETECTADAS: O dataset requer correcoes antes da publicacao.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
