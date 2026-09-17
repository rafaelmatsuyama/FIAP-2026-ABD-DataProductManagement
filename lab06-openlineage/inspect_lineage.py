import json
from pathlib import Path

events_file = Path("lineage_events.json")

if not events_file.exists():
    print("[ERROR] File lineage_events.json not found. Run 'python emit_lineage_events.py' first.")
    exit(1)

with open(events_file, "r", encoding="utf-8") as f:
    events = json.load(f)

print("=" * 70)
print("📊 OPERATIONAL LINEAGE CATALOG (OPENLINEAGE STANDARD)")
print("=" * 70)

complete_events = [e for e in events if e.get("eventType") == "COMPLETE"]

print(f"\n[+] Total Lifecycle Events: {len(events)} ({len(complete_events)} Completed Jobs)")
print("\n" + "-" * 70)
print("🔗 OPERATIONAL LINEAGE GRAPH (DAG)")
print("-" * 70)

for idx, e in enumerate(complete_events, 1):
    job_name = e["job"]["name"]
    inputs = [f"{inp['name']} ({inp['namespace']})" for inp in e.get("inputs", [])]
    outputs = [f"{out['name']} ({out['namespace']})" for out in e.get("outputs", [])]
    
    print(f"\nStep {idx}: JOB [{job_name}]")
    print(f"  ├─ INPUTS:  {', '.join(inputs)}")
    print(f"  └─ OUTPUTS: {', '.join(outputs)}")
    
    # Inspect Facets if present
    for out in e.get("outputs", []):
        facets = out.get("facets", {})
        if "schema" in facets:
            fields = [f["name"] + ":" + f["type"] for f in facets["schema"]["fields"][:4]]
            print(f"     ├─ Schema Facet: [{', '.join(fields)}...]")
        if "dataQualityMetrics" in facets:
            dq = facets["dataQualityMetrics"]
            print(f"     └─ Quality Facet: rowCount={dq.get('rowCount')}, producer={dq.get('_producer')}")

print("\n" + "=" * 70)
print("🔍 SIMPLIFIED END-TO-END FLOW REPRESENTATION:")
print("   [raw/transactions.parquet]")
print("              │")
print("              ▼ (job_ingestion_raw_to_staging)")
print("   [stg_transactions]  +  [dim_customers]")
print("              │                 │")
print("              └────────┬────────┘")
print("                       ▼ (dbt_build_marts_financial)")
print("           [fct_financial_transactions]")
print("              ┌────────┼────────┐")
print("              ▼        ▼        ▼")
print("         [BI Exec]  [ML Fraud]  [BACEN]")
print("=" * 70)

