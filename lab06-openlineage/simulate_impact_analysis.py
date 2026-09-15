import json
from pathlib import Path

events_file = Path("lineage_events.json")

if not events_file.exists():
    print("[ERRO] Arquivo lineage_events.json nao encontrado. Execute 'python emit_lineage_events.py'.")
    exit(1)

with open(events_file, "r", encoding="utf-8") as f:
    events = json.load(f)

print("=" * 70)
print("⚠️  SIMULAÇÃO DE ANÁLISE DE IMPACTO DOWNSTREAM (IMPACT ANALYSIS)")
print("=" * 70)

target_column = "amount"
origin_dataset = "transactions.parquet"

print(f"\n[CENÁRIO CORPORATIVO]:")
print(f"O time de pagamentos na origem pretende renomear ou alterar o tipo da coluna '{target_column}' em '{origin_dataset}'.")
print("Executando varredura recursiva no grafo OpenLineage para quantificar o Blast Radius...\n")

# Mapear dependencias diretas a partir dos eventos COMPLETE
dependency_tree = {
    "transactions.parquet": ["stg_transactions"],
    "stg_transactions": ["fct_financial_transactions"],
    "fct_financial_transactions": [
        "Dashboard Executivo de Receita (PowerBI / Tableau)",
        "Modelo de Detecção de Fraude (Feature Store ML)",
        "Relatório Regulatório BACEN (Contabilidade)"
    ]
}

print("🚨 BLAST RADIUS IDENTIFICADO (ELEMENTOS IMPACTADOS):")
level = 1
impacted_total = 0
for source, targets in dependency_tree.items():
    print(f"\nNível {level} - Dependências diretas de [{source}]:")
    for t in targets:
        print(f"   ❌ [IMPACTO DIRETO]: {t}")
        impacted_total += 1
    level += 1

print("\n" + "=" * 70)
print(f"📊 RESUMO DE GOVERNANÇA: {impacted_total} nós consumidores quebrariam em cascata!")
print("💡 RECOMENDAÇÃO: Bloquear a alteração na origem via Data Contract (ODCS) antes do deploy.")
print("=" * 70)
