from pathlib import Path
import duckdb

db_path = Path("data/analytics.duckdb")

if not db_path.exists():
    print("Erro: Base analytics.duckdb nao encontrada. Execute 'python setup_duckdb.py' e 'dbt build'.")
    exit(1)

con = duckdb.connect(str(db_path))

print("\n=======================================================")
print("🧪 INSPEÇÃO DE QUALIDADE: TABELAS E DATA PRODUCTS")
print("=======================================================\n")

tables = con.execute("SHOW TABLES;").fetchall()
table_names = [t[0] for t in tables]
print(f"Tabelas ativas no DuckDB: {table_names}\n")

if "fct_financial_transactions" in table_names and "dim_customers" in table_names:
    tx_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions;").fetchone()[0]
    cust_count = con.execute("SELECT COUNT(*) FROM dim_customers;").fetchone()[0]
    
    print(f"✅ Dimensão Clientes: {cust_count:,} registros ativos.")
    print(f"✅ Fato Transações Liquidadas: {tx_count:,} registros validados.")
    
    # Validação de integridade referencial manual
    orphans = con.execute("""
        SELECT COUNT(*) 
        FROM fct_financial_transactions f
        LEFT JOIN dim_customers c ON f.customer_id = c.customer_id
        WHERE c.customer_id IS NULL;
    """).fetchone()[0]
    
    print(f"🔍 Registros órfãos (Violações de Integridade Referencial): {orphans}")
    
    # Checagem de valores negativos
    negatives = con.execute("SELECT COUNT(*) FROM fct_financial_transactions WHERE net_amount < 0;").fetchone()[0]
    print(f"🔍 Transações com valor líquido negativo: {negatives}\n")
    
    print("Amostra do join entre Fato e Dimensão:")
    con.sql("""
        SELECT 
            f.transaction_id,
            c.customer_name,
            c.customer_tier,
            f.amount,
            f.net_amount,
            f.status,
            f.payment_method
        FROM fct_financial_transactions f
        JOIN dim_customers c ON f.customer_id = c.customer_id
        LIMIT 5;
    """).show()
else:
    print("Marts analíticos ainda não materializados. Execute 'dbt build --profiles-dir .'.")

con.close()
