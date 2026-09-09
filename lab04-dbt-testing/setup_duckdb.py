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
        Path("../lab03-dbt-modeling/data/transactions.parquet"),
        Path("../lab02-contracts/data/transactions.parquet"),
        Path("../lab00-setup/data/transactions.parquet"),
        Path("../../data/transactions.parquet")
    ]
    for src in possible_sources:
        if src.exists():
            shutil.copy2(src, parquet_path)
            print(f"Copiado transactions.parquet de {src}")
            break

# 2. Se nao existir em nenhum local, gerar dataset canonico na hora (Self-Healing)
if not parquet_path.exists():
    print("[*] Dataset base nao encontrado. Gerando dados sinteticos canonicos (Self-Healing)...")
    mem_con = duckdb.connect()
    mem_con.execute(f"""
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
        COPY raw_transactions TO '{parquet_path.as_posix()}' (FORMAT PARQUET);
    """)
    mem_con.close()
    print(f"[OK] Arquivo '{parquet_path}' gerado com sucesso!")

con = duckdb.connect(str(db_path))

# 1. Tabela transactions
con.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM '{parquet_path.as_posix()}';")
tx_count = con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
print(f"Tabela transactions inicializada com {tx_count} registros.")

# 2. Tabela customers (para testes relacionais)
con.execute("""
    CREATE OR REPLACE TABLE customers AS
    SELECT 
        'CUST_' || LPAD(i::VARCHAR, 4, '0') AS customer_id,
        'Cliente ' || i::VARCHAR AS customer_name,
        CASE WHEN i % 4 = 0 THEN 'VIP' WHEN i % 4 = 1 THEN 'GOLD' ELSE 'STANDARD' END AS customer_tier,
        'BR' AS country_code,
        DATE '2025-01-01' + INTERVAL (i * 3) DAY AS signup_date
    FROM generate_series(1, 100) t(i);
""")
print(f"Tabela customers criada com {con.execute('SELECT COUNT(*) FROM customers').fetchone()[0]} clientes cadastrados.")

con.close()
print("Setup da base analytics.duckdb concluido com sucesso!")
