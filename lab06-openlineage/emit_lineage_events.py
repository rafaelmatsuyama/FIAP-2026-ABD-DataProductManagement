import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
import duckdb

from openlineage.client import OpenLineageClient
from openlineage.client.facet import (
    DataQualityMetricsInputDatasetFacet,
    NominalTimeRunFacet,
    SchemaDatasetFacet,
    SchemaField,
)
from openlineage.client.run import (
    InputDataset,
    Job,
    OutputDataset,
    Run,
    RunEvent,
    RunState,
)
from openlineage.client.serde import Serde

NAMESPACE = "fiap.mba.dpm"
PRODUCER = "https://github.com/FIAP/8ABDR-DataProductManagement"
OUTPUT_FILE = Path("lineage_events.json")
DB_PATH = Path("data/analytics.duckdb")

def main():
    if not DB_PATH.exists():
        print("[ERROR] Database data/analytics.duckdb not found.")
        print("       Run 'python setup_duckdb.py' before emitting lineage.")
        return

    print("=" * 70)
    print("📡 LINEAGE INSTRUMENTATION WITH OPENLINEAGE PYTHON SDK")
    print("=" * 70)

    # 1. Connect to DuckDB to inspect the real data catalog
    print("\n[*] Inspecting analytical table catalog in DuckDB...")
    con = duckdb.connect(str(DB_PATH))

    def extract_schema_facet(table_name):
        cols = con.execute(f"DESCRIBE {table_name};").fetchall()
        return SchemaDatasetFacet(fields=[SchemaField(name=c[0], type=c[1]) for c in cols])

    raw_schema = extract_schema_facet("transactions")
    stg_schema = extract_schema_facet("stg_transactions")
    dim_schema = extract_schema_facet("dim_customers")
    fct_schema = extract_schema_facet("fct_financial_transactions")
    fct_count = con.execute("SELECT COUNT(*) FROM fct_financial_transactions;").fetchone()[0]
    con.close()

    print(f"  ├─ Table raw/transactions: {len(raw_schema.fields)} columns")
    print(f"  ├─ Table staging/stg_transactions: {len(stg_schema.fields)} columns")
    print(f"  ├─ Dimension/dim_customers: {len(dim_schema.fields)} columns")
    print(f"  └─ Data Mart/fct_financial_transactions: {len(fct_schema.fields)} columns ({fct_count} records)")

    # 2. Initialize OpenLineageClient (automatically reads openlineage.yml)
    print("\n[*] Initializing OpenLineageClient...")
    try:
        client = OpenLineageClient()
        print("  └─ [OK] Client configured via openlineage.yml (Target: http://localhost:5000)")
    except Exception as e:
        client = OpenLineageClient(url="http://localhost:5000")
        print(f"  └─ [INFO] Client initialized with direct fallback: {e}")

    now_iso = datetime.now(timezone.utc).isoformat()
    events = []
    marquez_available = True

    def emit_event(event: RunEvent):
        nonlocal marquez_available
        events.append(event)
        if marquez_available:
            try:
                client.emit(event)
                state_str = event.eventType.value if hasattr(event.eventType, "value") else str(event.eventType)
                print(f"  🚀 [EMIT -> MARQUEZ] Job='{event.job.name}' | RunState={state_str}")
            except Exception as e:
                marquez_available = False
                print(f"  ⚠️  [WARNING] Failed to emit to Marquez (http://localhost:5000): {e}")
                print("            The script will proceed serializing events locally via official Serde.")

    # ==============================================================================
    # Pipeline Step 1: Raw -> Staging Ingestion
    # ==============================================================================
    print("\n[Step 1] Emitting lineage events for 'job_ingestion_raw_to_staging'...")
    job_ingest = Job(namespace=NAMESPACE, name="job_ingestion_raw_to_staging")
    run_ingest = Run(
        runId=str(uuid.uuid4()),
        facets={"nominalTime": NominalTimeRunFacet(nominalStartTime=now_iso)}
    )

    input_raw = InputDataset(
        namespace="storage://datalake/raw",
        name="transactions.parquet",
        facets={"schema": raw_schema}
    )
    output_stg = OutputDataset(
        namespace="duckdb://analytics/staging",
        name="stg_transactions",
        facets={"schema": stg_schema}
    )

    # Evento START
    emit_event(RunEvent(
        eventType=RunState.START,
        eventTime=now_iso,
        run=run_ingest,
        job=job_ingest,
        producer=PRODUCER,
        inputs=[input_raw],
        outputs=[]
    ))

    # Evento COMPLETE
    emit_event(RunEvent(
        eventType=RunState.COMPLETE,
        eventTime=now_iso,
        run=run_ingest,
        job=job_ingest,
        producer=PRODUCER,
        inputs=[input_raw],
        outputs=[output_stg]
    ))

    # ==============================================================================
    # Pipeline Step 2: dbt Analytical Transformation (Staging + Dim -> Data Mart)
    # ==============================================================================
    print("\n[Step 2] Emitting lineage events for 'dbt_build_marts_financial'...")
    job_dbt = Job(namespace=NAMESPACE, name="dbt_build_marts_financial")
    run_dbt = Run(
        runId=str(uuid.uuid4()),
        facets={"nominalTime": NominalTimeRunFacet(nominalStartTime=now_iso)}
    )

    input_stg = InputDataset(
        namespace="duckdb://analytics/staging",
        name="stg_transactions",
        facets={"schema": stg_schema}
    )
    input_dim = InputDataset(
        namespace="duckdb://analytics/dimensions",
        name="dim_customers",
        facets={"schema": dim_schema}
    )

    quality_facet = DataQualityMetricsInputDatasetFacet(
        rowCount=fct_count,
        bytes=fct_count * 128
    )

    output_fct = OutputDataset(
        namespace="duckdb://analytics/marts",
        name="fct_financial_transactions",
        facets={
            "schema": fct_schema,
            "dataQualityMetrics": quality_facet
        }
    )

    # Evento START
    emit_event(RunEvent(
        eventType=RunState.START,
        eventTime=now_iso,
        run=run_dbt,
        job=job_dbt,
        producer=PRODUCER,
        inputs=[input_stg, input_dim],
        outputs=[]
    ))

    # Evento COMPLETE
    emit_event(RunEvent(
        eventType=RunState.COMPLETE,
        eventTime=now_iso,
        run=run_dbt,
        job=job_dbt,
        producer=PRODUCER,
        inputs=[input_stg, input_dim],
        outputs=[output_fct]
    ))

    # ==============================================================================
    # Pipeline Step 3: Downstream Analytical Consumers (Data Products)
    # ==============================================================================
    print("\n[Step 3] Emitting events for Data Mart downstream consumers...")
    input_fct_consumer = InputDataset(
        namespace="duckdb://analytics/marts",
        name="fct_financial_transactions",
        facets={"schema": fct_schema}
    )

    downstream_consumers = [
        {
            "job_name": "job_bi_executive_dashboard",
            "output_namespace": "bi://powerbi/workspaces/finance",
            "output_name": "bi_revenue_executive_dashboard",
            "fields": [
                SchemaField(name="customer_id", type="VARCHAR"),
                SchemaField(name="amount", type="DOUBLE"),
                SchemaField(name="transaction_date", type="DATE"),
            ]
        },
        {
            "job_name": "job_ml_fraud_feature_store",
            "output_namespace": "featurestore://feast/production",
            "output_name": "feature_store_fraud_detection",
            "fields": [
                SchemaField(name="customer_id", type="VARCHAR"),
                SchemaField(name="amount", type="DOUBLE"),
                SchemaField(name="is_fraud", type="BOOLEAN"),
            ]
        },
        {
            "job_name": "job_bacen_regulatory_export",
            "output_namespace": "regulatory://bacen/accounting",
            "output_name": "bacen_regulatory_cadoc_report",
            "fields": [
                SchemaField(name="transaction_id", type="VARCHAR"),
                SchemaField(name="amount", type="DOUBLE"),
                SchemaField(name="tax_id", type="VARCHAR"),
            ]
        }
    ]

    for consumer in downstream_consumers:
        c_job = Job(namespace=NAMESPACE, name=consumer["job_name"])
        c_run = Run(
            runId=str(uuid.uuid4()),
            facets={"nominalTime": NominalTimeRunFacet(nominalStartTime=now_iso)}
        )
        c_out = OutputDataset(
            namespace=consumer["output_namespace"],
            name=consumer["output_name"],
            facets={"schema": SchemaDatasetFacet(fields=consumer["fields"])}
        )
        emit_event(RunEvent(
            eventType=RunState.START,
            eventTime=now_iso,
            run=c_run,
            job=c_job,
            producer=PRODUCER,
            inputs=[input_fct_consumer],
            outputs=[]
        ))
        emit_event(RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=now_iso,
            run=c_run,
            job=c_job,
            producer=PRODUCER,
            inputs=[input_fct_consumer],
            outputs=[c_out]
        ))

    # ==============================================================================
    # 4. Local Persistence via Official OpenLineage Serde
    # ==============================================================================
    serialized_events = [json.loads(Serde.to_json(e)) for e in events]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(serialized_events, f, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ SUCCESS: {len(events)} OpenLineage events processed and saved to '{OUTPUT_FILE}'.")
    if marquez_available:
        print("🌐 Metadata synchronized live in Marquez!")
        print("   Access the web UI at: http://localhost:3000 (Namespace: fiap.mba.dpm)")
    else:
        print("💡 Tip: To view in the Marquez web UI, start the environment with:")
        print("   docker compose up -d")
        print("   and re-run this script!")
    print("=" * 70)

if __name__ == "__main__":
    main()
