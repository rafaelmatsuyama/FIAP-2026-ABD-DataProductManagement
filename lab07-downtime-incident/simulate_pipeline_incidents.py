from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import uuid

from openlineage.client import OpenLineageClient
from openlineage.client.facet import (
    ErrorMessageRunFacet,
    NominalTimeRunFacet,
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
JOB_NAME = "dbt_build_marts_financial"
PRODUCER = "https://github.com/FIAP/8ABDR-DataProductManagement"
FALLBACK_FILE = Path("marquez_runs_fallback.json")

def main():
    print("=" * 80)
    print("🚨 OPERATIONAL TELEMETRY & DATA INCIDENT INJECTOR (OPENLINEAGE)")
    print("=" * 80)
    print("[*] Connecting to Marquez Server via OpenLineageClient (http://localhost:5000)...")

    try:
        client = OpenLineageClient()
    except Exception as e:
        client = OpenLineageClient(url="http://localhost:5000")

    now = datetime.now(timezone.utc)
    events_record = []
    marquez_online = True

    def emit(event: RunEvent):
        nonlocal marquez_online
        events_record.append(event)
        if marquez_online:
            try:
                client.emit(event)
            except Exception as ex:
                marquez_online = False
                print(f"  ⚠️  [WARNING] Marquez unavailable ({ex}). Storing in local buffer...")

    # Execution scenarios across a 24-hour operational window
    scenarios = [
        {
            "offset_hours": 24,
            "duration_sec": 120,
            "state": RunState.COMPLETE,
            "desc": "Regular Nightly Execution (Batch D-1)",
            "error": None
        },
        {
            "offset_hours": 18,
            "duration_sec": 115,
            "state": RunState.COMPLETE,
            "desc": "Regular Morning Execution (06:00 Consolidation)",
            "error": None
        },
        {
            "offset_hours": 12,
            "duration_sec": 45,
            "state": RunState.FAIL,
            "desc": "INCIDENT #1: Data Contract Violation (18.4% nulls in 'customer_id')",
            "error": "DataContractException: Check 'customer_id_not_null' failed on upstream staging. Null rate=18.4%."
        },
        {
            "offset_hours": 10,
            "duration_sec": 40,
            "state": RunState.FAIL,
            "desc": "INCIDENT #2: Automated Retry Without Fix (Airflow Retries Exhausted)",
            "error": "SodaScanFailed: Quality Gate failed. 184 invalid rows detected in fct_financial_transactions."
        },
        {
            "offset_hours": 6,
            "duration_sec": 145,
            "state": RunState.COMPLETE,
            "desc": "RECOVERY: Engineering hotfix deployed and pipeline successfully reprocessed",
            "error": None
        },
        {
            "offset_hours": 1,
            "duration_sec": 110,
            "state": RunState.COMPLETE,
            "desc": "Current Regular Execution (Healthy State Restored)",
            "error": None
        }
    ]

    job = Job(namespace=NAMESPACE, name=JOB_NAME)
    inputs = [
        InputDataset(namespace="duckdb://analytics/staging", name="stg_transactions"),
        InputDataset(namespace="duckdb://analytics/dimensions", name="dim_customers")
    ]
    outputs = [
        OutputDataset(namespace="duckdb://analytics/marts", name="fct_financial_transactions")
    ]

    print(f"\n[*] Emitting 6-run execution history for Job: [{NAMESPACE}:{JOB_NAME}]...\n")

    runs_summary = []

    for sc in scenarios:
        run_id = str(uuid.uuid4())
        start_time = now - timedelta(hours=sc["offset_hours"])
        end_time = start_time + timedelta(seconds=sc["duration_sec"])

        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()

        run = Run(
            runId=run_id,
            facets={"nominalTime": NominalTimeRunFacet(nominalStartTime=start_iso)}
        )

        # 1. START Event
        emit(RunEvent(
            eventType=RunState.START,
            eventTime=start_iso,
            run=run,
            job=job,
            producer=PRODUCER,
            inputs=inputs,
            outputs=[]
        ))

        # 2. Terminal Event (COMPLETE or FAIL)
        end_facets = {}
        if sc["state"] == RunState.FAIL and sc["error"]:
            end_facets["errorMessage"] = ErrorMessageRunFacet(
                message=sc["error"],
                programmingLanguage="python"
            )

        run_ended = Run(runId=run_id, facets=end_facets)

        emit(RunEvent(
            eventType=sc["state"],
            eventTime=end_iso,
            run=run_ended,
            job=job,
            producer=PRODUCER,
            inputs=inputs,
            outputs=outputs if sc["state"] == RunState.COMPLETE else []
        ))

        status_icon = "✅ COMPLETED" if sc["state"] == RunState.COMPLETE else "❌ FAILED"
        print(f"  ├─ Run {run_id[:8]}... | {status_icon} | {sc['desc']}")
        if sc["error"]:
            print(f"  │  └─ 💥 Root Cause: {sc['error']}")

        runs_summary.append({
            "id": run_id,
            "startedAt": start_iso,
            "endedAt": end_iso,
            "state": "COMPLETED" if sc["state"] == RunState.COMPLETE else "FAILED",
            "durationMs": sc["duration_sec"] * 1000,
            "errorMessage": sc["error"]
        })

    # Record local snapshot for fallback
    with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "namespace": NAMESPACE,
            "jobName": JOB_NAME,
            "generatedAt": now.isoformat(),
            "runs": runs_summary
        }, f, indent=2)

    print("\n" + "=" * 80)
    if marquez_online:
        print("🌐 SUCCESS: Telemetry successfully synchronized to Marquez API!")
        print("   Open Marquez UI at http://localhost:3000 and select Namespace 'fiap.mba.dpm'.")
        print(f"   Click Job '{JOB_NAME}' to view green and red run badges history.")
    else:
        print(f"💾 Local contingency snapshot saved successfully to '{FALLBACK_FILE}'.")
    print("=" * 80)

if __name__ == "__main__":
    main()
