import shutil
from pathlib import Path
import duckdb

data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)
db_path = data_dir / "analytics.duckdb"
parquet_path = data_dir / "transactions.parquet"

# Buscar o arquivo transactions.parquet dos labs anteriores se nao existir localmente
if not parquet_path.exists():
    possible_sources = [
        Path("../lab02-contracts/data/transactions.parquet"),
        Path("../lab00-setup/data/transactions.parquet"),
        Path("../../data/transactions.parquet")
    ]
    for src in possible_sources:
        if src.exists():
            shutil.copy2(src, parquet_path)
            print(f"Copiado transactions.parquet de {src}")
            break

con = duckdb.connect(str(db_path))

if parquet_path.exists():
    con.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM '{parquet_path.as_posix()}';")
    print(f"Base analytics.duckdb inicializada com {con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]} transacoes.")
else:
    # Gerar dados sinteticos minimos se o parquet nao for encontrado
    con.execute("""
        CREATE OR REPLACE TABLE transactions AS
        SELECT 
            'TX_' || LPAD(i::VARCHAR, 6, '0') AS transaction_id,
            'CUST_' || LPAD(((i % 100) + 1)::VARCHAR, 4, '0') AS customer_id,
            ROUND(10.0 + (i * 3.7) % 500, 2) AS amount,
            ROUND((10.0 + (i * 3.7) % 500) * 0.02, 2) AS fee,
            'BRL' AS currency,
            CASE WHEN i % 10 = 0 THEN 'FAILED' ELSE 'COMPLETED' END AS status,
            CASE WHEN i % 3 = 0 THEN 'PIX' WHEN i % 3 = 1 THEN 'CREDIT_CARD' ELSE 'BOLETO' END AS payment_method,
            TIMESTAMP '2026-09-01 10:00:00' + INTERVAL (i * 15) MINUTE AS created_at
        FROM generate_series(1, 1000) t(i);
    """)
    print("Base analytics.duckdb criada com 1.000 transacoes sinteticas.")

con.close()
print("Setup concluido com sucesso!")
