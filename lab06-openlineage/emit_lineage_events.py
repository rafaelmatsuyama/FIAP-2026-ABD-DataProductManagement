import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import duckdb

NAMESPACE = "fiap.mba.dpm"
OUTPUT_FILE = Path("lineage_events.json")

def create_dataset_facet(fields):
    return {
        "schema": {
            "_producer": "https://github.com/OpenLineage/OpenLineage/tree/1.0.0/client/python",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": fields
        }
    }

def create_event(job_name, run_id, event_type, inputs, outputs, producer="openlineage-dpm-lab"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "eventType": event_type,
        "eventTime": now,
        "run": {
            "runId": run_id,
            "facets": {
                "nominalTime": {
                    "_producer": producer,
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/NominalTimeRunFacet.json",
                    "nominalStartTime": now
                }
            }
        },
        "job": {
            "namespace": NAMESPACE,
            "name": job_name,
            "facets": {}
        },
        "inputs": inputs,
        "outputs": outputs,
        "producer": producer,
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json"
    }

print("[*] Conectando ao DuckDB para inspecionar schemas e metadados operacionais...")
con = duckdb.connect("data/analytics.duckdb")

# Schemas reais obtidos do catálogo
raw_fields = [{"name": col[0], "type": col[1]} for col in con.execute("DESCRIBE transactions;").fetchall()]
stg_fields = [{"name": col[0], "type": col[1]} for col in con.execute("DESCRIBE stg_transactions;").fetchall()]
dim_fields = [{"name": col[0], "type": col[1]} for col in con.execute("DESCRIBE dim_customers;").fetchall()]
fct_fields = [{"name": col[0], "type": col[1]} for col in con.execute("DESCRIBE fct_financial_transactions;").fetchall()]
fct_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions").fetchone()[0]
con.close()

events = []

# ==============================================================================
# Evento 1: Job de Ingestão (transactions.parquet -> stg_transactions)
# ==============================================================================
run_id_ingest = str(uuid.uuid4())
events.append(create_event(
    job_name="job_ingestion_raw_to_staging",
    run_id=run_id_ingest,
    event_type="START",
    inputs=[{
        "namespace": "storage://datalake/raw",
        "name": "transactions.parquet",
        "facets": create_dataset_facet(raw_fields)
    }],
    outputs=[]
))

events.append(create_event(
    job_name="job_ingestion_raw_to_staging",
    run_id=run_id_ingest,
    event_type="COMPLETE",
    inputs=[{
        "namespace": "storage://datalake/raw",
        "name": "transactions.parquet",
        "facets": create_dataset_facet(raw_fields)
    }],
    outputs=[{
        "namespace": "duckdb://analytics/staging",
        "name": "stg_transactions",
        "facets": create_dataset_facet(stg_fields)
    }]
))

# ==============================================================================
# Evento 2: Job Analítico dbt (stg_transactions + dim_customers -> fct_financial_transactions)
# ==============================================================================
run_id_transform = str(uuid.uuid4())
fct_facets = create_dataset_facet(fct_fields)
fct_facets["dataQualityMetrics"] = {
    "_producer": "soda-core-duckdb",
    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DataQualityMetricsInputDatasetFacet.json",
    "rowCount": fct_count,
    "bytes": fct_count * 128
}

events.append(create_event(
    job_name="dbt_build_marts_financial",
    run_id=run_id_transform,
    event_type="START",
    inputs=[
        {"namespace": "duckdb://analytics/staging", "name": "stg_transactions", "facets": create_dataset_facet(stg_fields)},
        {"namespace": "duckdb://analytics/dimensions", "name": "dim_customers", "facets": create_dataset_facet(dim_fields)}
    ],
    outputs=[]
))

events.append(create_event(
    job_name="dbt_build_marts_financial",
    run_id=run_id_transform,
    event_type="COMPLETE",
    inputs=[
        {"namespace": "duckdb://analytics/staging", "name": "stg_transactions", "facets": create_dataset_facet(stg_fields)},
        {"namespace": "duckdb://analytics/dimensions", "name": "dim_customers", "facets": create_dataset_facet(dim_fields)}
    ],
    outputs=[{
        "namespace": "duckdb://analytics/marts",
        "name": "fct_financial_transactions",
        "facets": fct_facets
    }]
))

# Salvar eventos em arquivo JSON formatado
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

print(f"[OK] {len(events)} eventos OpenLineage emitidos com sucesso em '{OUTPUT_FILE}'.")
print("Para inspecionar o grafo de dependências gerado, execute:")
print("  python inspect_lineage.py")
