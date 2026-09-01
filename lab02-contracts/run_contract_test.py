"""Runner and validator for OpenDataContract Standard (ODCS) in Lab 02.

Executes contract testing against data/analytics.duckdb using datacontract-cli.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def ensure_data_and_db_exist() -> None:
    """Ensure data/transactions.parquet and data/analytics.duckdb exist."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = data_dir / "transactions.parquet"
    db_path = data_dir / "analytics.duckdb"

    # 1. Sync parquet if missing
    if not parquet_path.exists():
        for candidate in [
            Path("../lab00-setup/data/transactions.parquet"),
            Path("../lab01-canvas/data/transactions.parquet"),
        ]:
            if candidate.exists():
                shutil.copy2(candidate, parquet_path)
                print(f"[*] Base sincronizada de '{candidate}' para '{parquet_path}'.")
                break

    # 2. Build or refresh DuckDB table
    try:
        import duckdb
        con = duckdb.connect(str(db_path))
        if parquet_path.exists():
            con.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM '{parquet_path.as_posix()}';")
        else:
            con.execute("""
                CREATE TABLE IF NOT EXISTS transactions AS
                SELECT
                    'tx_' || LPAD(range::VARCHAR, 6, '0') AS transaction_id,
                    'cust_' || LPAD((FLOOR(RANDOM() * 500) + 1)::INT::VARCHAR, 4, '0') AS customer_id,
                    ROUND((RANDOM() * 1500 + 10.50)::NUMERIC, 2) AS amount,
                    ['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO'][FLOOR(RANDOM() * 4 + 1)::INT] AS payment_method,
                    ['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'FAILED'][FLOOR(RANDOM() * 5 + 1)::INT] AS status,
                    ['BRL', 'BRL', 'USD', 'EUR'][FLOOR(RANDOM() * 4 + 1)::INT] AS currency,
                    TIMESTAMP '2026-01-01 00:00:00' + INTERVAL (RANDOM() * 60 * 24 * 60) MINUTE AS transaction_timestamp
                FROM range(2500);
            """)
            con.execute(f"COPY transactions TO '{parquet_path.as_posix()}' (FORMAT PARQUET);")
        con.close()
    except Exception as e:
        print(f"[AVISO] Erro ao preparar DuckDB: {e}")


def run_contract_test(contract_path: str) -> bool:
    """Execute datacontract test command."""
    ensure_data_and_db_exist()
    print("=" * 70)
    print(f"  📜 TESTANDO DATA CONTRACT: '{contract_path}'")
    print("=" * 70)

    cli_bin = shutil.which("datacontract")
    if cli_bin:
        cmd = [cli_bin, "test", contract_path]
    else:
        cmd = [sys.executable, "-m", "datacontract.cli", "test", contract_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"[AVISO] Erro ao invocar CLI: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Data Contract via CLI.")
    parser.add_argument(
        "--contract",
        default="datacontract.yaml",
        help="Path to contract YAML (default: datacontract.yaml)",
    )
    args = parser.parse_args()

    success = run_contract_test(args.contract)
    if success:
        print("  [OK] CONTRATO DE DADOS 100% APROVADO PELO QUALITY GATE!")
    else:
        print("  [FAIL] VIOLACOES DETECTADAS NO CONTRATO DE DADOS.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
