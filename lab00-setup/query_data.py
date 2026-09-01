"""Query transactions dataset using Python DuckDB engine.

Executes schema inspection and aggregation queries directly on Parquet files.
"""

from pathlib import Path

try:
    import duckdb
except ImportError:
    print("[ERRO] DuckDB nao instalado. Execute 'pip install -r ../requirements.txt' primeiro.")
    exit(1)


def main():
    parquet_file = Path("data/transactions.parquet")
    if not parquet_file.exists():
        print(f"[ERRO] Arquivo '{parquet_file}' nao encontrado.")
        print("Execute 'python generate_sample_data.py' primeiro.")
        exit(1)

    con = duckdb.connect()

    print("=" * 65)
    print("  🦆 CONSULTA ANALITICA VIA DUCKDB (EM-MEMORIA)")
    print("=" * 65)

    print("\n--- 1. Inspecao de Schema & Tipos (DESCRIBE) ---")
    con.sql("DESCRIBE SELECT * FROM 'data/transactions.parquet';").show()

    print("\n--- 2. Metricas Agregadas por Metodo de Pagamento ---")
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
    print("  [OK] Processamento analitico DuckDB executado com sucesso!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
