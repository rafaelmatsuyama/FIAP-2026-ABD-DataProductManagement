from collections import defaultdict, deque
import json
from pathlib import Path

events_file = Path("lineage_events.json")

if not events_file.exists():
    print("[ERRO] Arquivo lineage_events.json nao encontrado. Execute 'python emit_lineage_events.py'.")
    exit(1)

with open(events_file, "r", encoding="utf-8") as f:
    events = json.load(f)

print("=" * 75)
print("⚠️  ANÁLISE DINÂMICA DE IMPACTO DOWNSTREAM (OPENLINEAGE BLAST RADIUS)")
print("=" * 75)

target_column = "amount"
origin_dataset = "transactions.parquet"

print(f"\n[CENÁRIO CORPORATIVO]:")
print(f"O time upstream pretende renomear ou remover a coluna '{target_column}' em '{origin_dataset}'.")
print("Analisando metadados OpenLineage (Eventos COMPLETE) e calculando Blast Radius dinâmico...\n")

# 1. Construir o Grafo Bipartido Direcionado (Dataset -> Job -> Dataset)
dataset_to_jobs = defaultdict(list)
job_to_datasets = defaultdict(list)
dataset_schemas = {}
dataset_namespaces = {}
job_namespaces = {}

for event in events:
    if event.get("eventType") != "COMPLETE":
        continue

    job_info = event.get("job", {})
    job_name = job_info.get("name")
    job_namespaces[job_name] = job_info.get("namespace", "unknown")

    # Mapear Datasets de Entrada -> Job
    for inp in event.get("inputs", []):
        ds_name = inp.get("name")
        dataset_namespaces[ds_name] = inp.get("namespace", "")
        if job_name not in dataset_to_jobs[ds_name]:
            dataset_to_jobs[ds_name].append(job_name)

        if "schema" in inp.get("facets", {}):
            dataset_schemas[ds_name] = [
                field["name"] for field in inp["facets"]["schema"].get("fields", [])
            ]

    # Mapear Job -> Datasets de Saída
    for out in event.get("outputs", []):
        ds_name = out.get("name")
        dataset_namespaces[ds_name] = out.get("namespace", "")
        if ds_name not in job_to_datasets[job_name]:
            job_to_datasets[job_name].append(ds_name)

        if "schema" in out.get("facets", {}):
            dataset_schemas[ds_name] = [
                field["name"] for field in out["facets"]["schema"].get("fields", [])
            ]

# 2. Validar presença da coluna no nó raiz
if origin_dataset in dataset_schemas:
    fields = dataset_schemas[origin_dataset]
    if target_column in fields:
        print(f"[*] Origem confirmada: '{origin_dataset}' contém '{target_column}' no SchemaFacet.")
    else:
        print(f"⚠️ Aviso: '{target_column}' nao encontrada nos campos de '{origin_dataset}'.")

# 3. Busca em Largura (BFS) para percorrer dependências downstream no Grafo
queue = deque([(origin_dataset, 0)])
visited_datasets = {origin_dataset}
visited_jobs = set()

impacted_by_level = defaultdict(list)

while queue:
    current_ds, depth = queue.popleft()

    # Identificar jobs que consomem esse dataset
    consumer_jobs = dataset_to_jobs.get(current_ds, [])
    for job in consumer_jobs:
        if job not in visited_jobs:
            visited_jobs.add(job)
            impacted_by_level[depth + 1].append({
                "type": "JOB",
                "name": job,
                "namespace": job_namespaces.get(job, ""),
                "consumed_from": current_ds
            })

            # Identificar outputs gerados por esse job
            for out_ds in job_to_datasets.get(job, []):
                # Verificar se a coluna propaga para o output
                out_fields = dataset_schemas.get(out_ds, [])
                has_column = target_column in out_fields if out_fields else True

                if out_ds not in visited_datasets and has_column:
                    visited_datasets.add(out_ds)
                    impacted_by_level[depth + 2].append({
                        "type": "DATASET",
                        "name": out_ds,
                        "namespace": dataset_namespaces.get(out_ds, ""),
                        "produced_by": job,
                        "has_column": target_column in out_fields
                    })
                    queue.append((out_ds, depth + 2))

# 4. Apresentação do Blast Radius
print("\n🚨 BLAST RADIUS IDENTIFICADO (GRAFO DE DEPENDÊNCIA DOWNSTREAM):")

total_impacted = 0
for level in sorted(impacted_by_level.keys()):
    items = impacted_by_level[level]
    print(f"\n[Nível {level}] - {len(items)} elemento(s) afetado(s):")
    for item in items:
        total_impacted += 1
        if item["type"] == "JOB":
            print(f"   ⚙️  [PIPELINE/JOB] {item['name']}")
            print(f"       Consome: [{item['consumed_from']}] | Namespace: {item['namespace']}")
        else:
            schema_status = "✅ Coluna confirmada no SchemaFacet" if item["has_column"] else "⚠️ Schema sem validação explícita"
            print(f"   📦 [DATASET IMPACTADO] {item['name']}")
            print(f"       Origem: Job [{item['produced_by']}] | URI: {item['namespace']}/{item['name']}")
            print(f"       Validação: {schema_status}")

# 5. Resumo Executivo e Ação de Governança
print("\n" + "=" * 75)
print(f"📊 RESUMO DO BLAST RADIUS:")
print(f"   ├─ Jobs/Pipelines impactados: {len(visited_jobs)}")
print(f"   ├─ Datasets analíticos corrompidos: {len(visited_datasets) - 1}")
print(f"   └─ Total de nós quebrados em cascata: {total_impacted}")
print("\n💡 AÇÃO RECOMENDADA DE GOVERNANÇA:")
print("   ❌ BLOQUEAR o Pull Request do time upstream!")
print(f"   A quebra de contrato na coluna '{target_column}' derrubaria os produtos finais")
print("   de BI Executivo, Feature Store de Fraude e o Relatório Regulatório do BACEN.")
print("=" * 75)

