import duckdb
from pathlib import Path

db_path = Path("data/analytics.duckdb")

if not db_path.exists():
    print("[ERRO] Banco data/analytics.duckdb nao encontrado. Execute 'python setup_duckdb.py' primeiro.")
    exit(1)

con = duckdb.connect(str(db_path))

print("[!] Injetando anomalias sinteticas na tabela transactions...")

# Inserir transacoes corrompidas para disparar falha no Quality Gate:
# 1. amount negativo (-999.00)
# 2. transaction_id NULL
# 3. status invalido ('CORRUPTED_STATUS')
con.execute("""
    INSERT INTO transactions (transaction_id, customer_id, amount, fee, payment_method, status, currency, created_at)
    VALUES 
        (NULL, 'CUST_0001', -999.50, 0.00, 'PIX', 'CORRUPTED_STATUS', 'BRL', NOW()),
        ('TX_999999', 'CUST_0002', -150.00, 0.00, 'BITCOIN', 'UNKNOWN', 'XYZ', NOW());
""")

count = con.execute("SELECT COUNT(*) FROM transactions WHERE amount < 0 OR transaction_id IS NULL").fetchone()[0]
print(f"[OK] Anomalias injetadas com sucesso! {count} registros defeituosos inseridos.")
print("Agora execute: soda scan -d analytics -c configuration.yml checks.yml")
con.close()
