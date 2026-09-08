from pathlib import Path
import duckdb

db_path = Path("data/analytics.duckdb")

if not db_path.exists():
    print("Erro: Base analytics.duckdb nao encontrada. Execute 'python setup_duckdb.py' e 'dbt run'.")
    exit(1)

con = duckdb.connect(str(db_path))

print("\n=======================================================")
print("📊 INSPEÇÃO DE DATA PRODUCT: fct_financial_transactions")
print("=======================================================\n")

# Checagem de tabelas existentes
tables = con.execute("SHOW TABLES;").fetchall()
table_names = [t[0] for t in tables]
print(f"Tabelas presentes no DuckDB: {table_names}\n")

if "fct_financial_transactions" in table_names:
    total_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions;").fetchone()[0]
    total_volume = con.execute("SELECT SUM(amount), SUM(fee), SUM(net_amount) FROM fct_financial_transactions;").fetchone()
    
    print(f"Total de Transações Liquidadas (COMPLETED): {total_count:,}")
    print(f"Volume Bruto Transacionado: R$ {total_volume[0]:,.2f}")
    print(f"Taxas Retidas (Take Rate): R$ {total_volume[1]:,.2f}")
    print(f"Volume Líquido Creditado:  R$ {total_volume[2]:,.2f}\n")
    
    print("Amostra das 5 primeiras linhas do Mart de Consumo:")
    con.sql("SELECT transaction_id, customer_id, amount, net_amount, status, payment_method FROM fct_financial_transactions LIMIT 5;").show()
else:
    print("Tabela 'fct_financial_transactions' ainda não foi criada. Execute 'dbt run --select marts'.")

con.close()
