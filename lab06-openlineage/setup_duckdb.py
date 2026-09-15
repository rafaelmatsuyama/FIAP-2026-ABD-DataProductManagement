import shutil
from pathlib import Path
import duckdb

data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)
db_path = data_dir / "analytics.duckdb"
parquet_path = data_dir / "transactions.parquet"

# 1. Buscar o arquivo transactions.parquet dos labs anteriores se nao existir localmente
if not parquet_path.exists():
    possible_sources = [
        Path("../lab05-soda-quality/data/transactions.parquet"),
        Path("../lab04-dbt-testing/data/transactions.parquet"),
        Path("../lab03-dbt-modeling/data/transactions.parquet"),
        Path("../lab02-contracts/data/transactions.parquet"),
        Path("../lab00-setup/data/transactions.parquet")
    ]
    for src in possible_sources:
        if src.exists():
            shutil.copy2(src, parquet_path)
            print(f"Copiado transactions.parquet de {src}")
            break

# 2. Se nao existir, gerar dataset canonico na hora (Self-Healing)
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

# 2. Tabela customers
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

# 3. Modelos analiticos de downstream para demonstracao de linhagem
con.execute("""
    CREATE OR REPLACE TABLE stg_transactions AS
    SELECT 
        transaction_id,
        customer_id,
        amount,
        fee,
        payment_method,
        status,
        currency,
        created_at
    FROM transactions;

    CREATE OR REPLACE TABLE dim_customers AS
    SELECT 
        customer_id,
        customer_name,
        customer_tier,
        country_code,
        signup_date
    FROM customers;

    CREATE OR REPLACE TABLE fct_financial_transactions AS
    SELECT 
        t.transaction_id,
        t.customer_id,
        c.customer_tier,
        t.amount,
        t.fee,
        ROUND(t.amount - t.fee, 2) AS net_amount,
        t.payment_method,
        t.status,
        t.currency,
        t.created_at
    FROM stg_transactions t
    INNER JOIN dim_customers c ON t.customer_id = c.customer_id;
""")

tx_count = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
fct_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions").fetchone()[0]
con.close()

print(f"[OK] Pipeline analitico completo preparado: transactions ({tx_count}) -> fct_financial_transactions ({fct_count}).")
