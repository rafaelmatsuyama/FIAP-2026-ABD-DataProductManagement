from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import requests

MARQUEZ_API_URL = "http://localhost:5000/api/v1/namespaces/fiap.mba.dpm/jobs/dbt_build_marts_financial/runs"
FALLBACK_FILE = Path("marquez_runs_fallback.json")
REPORT_FILE = Path("DATA_RELIABILITY_REPORT.md")
FREEZE_FILE = Path("DEPLOY_FREEZE.md")

# Parâmetros Contratuais de Confiabilidade (SLO)
TARGET_SLO_PERCENT = 99.0
COST_PER_DOWNTIME_HOUR_USD = 15000.0  # Impacto financeiro de downtime corporativo em decisões de risco/crédito

def parse_iso(ts_str):
    if not ts_str:
        return None
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

def fetch_runs_telemetry():
    """Fetch telemetry directly from Marquez REST API or use local fallback."""
    print("[*] Connecting to Marquez REST API at http://localhost:5000...")
    try:
        resp = requests.get(MARQUEZ_API_URL, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("runs", [])
            print(f"  └─ [OK] {len(runs)} actual runs collected from Marquez API.")
            return runs, "MARQUEZ_REST_API"
    except Exception as e:
        print(f"  ⚠️  [INFO] Connection to Marquez API unavailable: {e}")

    if FALLBACK_FILE.exists():
        print(f"  └─ [OK] Loading telemetry from local snapshot '{FALLBACK_FILE}'...")
        with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("runs", []), "LOCAL_SNAPSHOT_FALLBACK"

    print("[ERROR] No telemetry source available. Run 'python simulate_pipeline_incidents.py' first.")
    sys.exit(1)

def main():
    print("=" * 80)
    print("📊 DATA SRE AUDITING ENGINE: SLI/SLO, ERROR BUDGET & DATA DOWNTIME")
    print("=" * 80)

    raw_runs, source = fetch_runs_telemetry()
    if not raw_runs:
        print("[ERROR] No runs found for job 'dbt_build_marts_financial'.")
        return

    # Sort runs chronologically
    runs = []
    for r in raw_runs:
        started = parse_iso(r.get("startedAt"))
        ended = parse_iso(r.get("endedAt"))
        state = r.get("state")
        error_msg = r.get("errorMessage") or r.get("facets", {}).get("errorMessage", {}).get("message")
        runs.append({
            "id": r.get("id"),
            "state": state,
            "startedAt": started,
            "endedAt": ended,
            "error": error_msg
        })

    runs.sort(key=lambda x: x["startedAt"] or datetime.min.replace(tzinfo=timezone.utc))

    total_runs = len(runs)
    completed_runs = sum(1 for r in runs if r["state"] == "COMPLETED")
    failed_runs = sum(1 for r in runs if r["state"] == "FAILED")

    # 1. Operational Availability SLI Calculation
    availability_sli = (completed_runs / total_runs) * 100.0 if total_runs > 0 else 0.0

    # 2. Incident Identification, MTTD and MTTR
    incidents = []
    current_incident = None

    for i, r in enumerate(runs):
        if r["state"] == "FAILED":
            if current_incident is None:
                current_incident = {
                    "incident_id": f"INC-2026-{len(incidents) + 1:03d}",
                    "failed_run_id": r["id"],
                    "failure_time": r["startedAt"],
                    "detection_time": r["endedAt"],  # Detected immediately by Quality Gate/OpenLineage
                    "resolution_time": None,
                    "error_cause": r["error"] or "Data pipeline runtime error"
                }
        elif r["state"] == "COMPLETED":
            if current_incident is not None:
                current_incident["resolution_time"] = r["endedAt"]
                incidents.append(current_incident)
                current_incident = None

    if current_incident is not None:
        current_incident["resolution_time"] = datetime.now(timezone.utc)
        incidents.append(current_incident)

    total_downtime_minutes = 0.0
    mttd_list = []
    mttr_list = []

    print(f"\n{'INCIDENT':<14} | {'STATUS':<12} | {'MTTD (min)':<10} | {'MTTR (min)':<10} | {'TOTAL DOWNTIME':<16} | ROOT CAUSE")
    print("-" * 100)

    for inc in incidents:
        t_fail = inc["failure_time"]
        t_det = inc["detection_time"]
        t_res = inc["resolution_time"]

        mttd = (t_det - t_fail).total_seconds() / 60.0 if (t_det and t_fail) else 0.0
        mttr = (t_res - t_det).total_seconds() / 60.0 if (t_res and t_det) else 0.0
        downtime = (t_res - t_fail).total_seconds() / 60.0 if (t_res and t_fail) else 0.0

        mttd_list.append(mttd)
        mttr_list.append(mttr)
        total_downtime_minutes += downtime

        cause_short = inc["error_cause"][:35] + "..." if len(inc["error_cause"]) > 35 else inc["error_cause"]
        print(f"{inc['incident_id']:<14} | {'RESOLVED':<12} | {mttd:>8.1f} m | {mttr:>8.1f} m | {downtime:>10.1f} min ({downtime/60:.1f}h) | {cause_short}")

    avg_mttd = sum(mttd_list) / len(mttd_list) if mttd_list else 0.0
    avg_mttr = sum(mttr_list) / len(mttr_list) if mttr_list else 0.0

    # 3. Error Budget Audit (Monthly Operational Window of 43,200 minutes)
    MONTH_MINUTES = 30 * 24 * 60
    ALLOWED_DOWNTIME_MINUTES = MONTH_MINUTES * ((100.0 - TARGET_SLO_PERCENT) / 100.0)  # 432 min for 99.0%
    budget_consumed_percent = (total_downtime_minutes / ALLOWED_DOWNTIME_MINUTES) * 100.0

    total_loss_usd = (total_downtime_minutes / 60.0) * COST_PER_DOWNTIME_HOUR_USD
    total_loss_brl = total_loss_usd * 5.40

    print("-" * 100)
    print(f"\n[📈 SRE INDICATORS & SLIS]:")
    print(f"  ├─ Telemetry Source:                {source}")
    print(f"  ├─ Total Runs Inspected:            {total_runs} (Success: {completed_runs} | Failures: {failed_runs})")
    print(f"  ├─ Actual Availability SLI:         {availability_sli:.1f}%")
    print(f"  ├─ Mean MTTD (Detection):           {avg_mttd:.1f} minutes")
    print(f"  ├─ Mean MTTR (Recovery):            {avg_mttr:.1f} minutes ({avg_mttr/60:.1f} hours)")
    print(f"  └─ Accumulated Data Downtime:       {total_downtime_minutes:.1f} minutes ({total_downtime_minutes/60:.1f} hours)")

    print(f"\n[🎯 SERVICE LEVEL OBJECTIVE (SLO) AUDIT]:")
    print(f"  ├─ Contractual Target (Agreed SLO): {TARGET_SLO_PERCENT:.1f}%")
    print(f"  ├─ Error Budget Allowance:          {ALLOWED_DOWNTIME_MINUTES:.0f} minutes/month")
    print(f"  ├─ Time Consumed by Incidents:      {total_downtime_minutes:.0f} minutes")
    print(f"  └─ Error Budget Consumption:        {budget_consumed_percent:.1f}%")

    is_freeze = budget_consumed_percent > 100.0

    if is_freeze:
        print(f"\n🚨 [CRITICAL]: ERROR BUDGET EXHAUSTED ({budget_consumed_percent:.1f}%)!")
        print("   Data Product reliability contract has been breached in this cycle.")
        print(f"   Generating mandatory governance policy in '{FREEZE_FILE}'...")

        with open(FREEZE_FILE, "w", encoding="utf-8") as f:
            f.write(f"""# 🚨 ENGINEERING DIRECTIVE: ACTIVE DEPLOY FREEZE
**Data Product:** `dbt_build_marts_financial` (Namespace: `fiap.mba.dpm`)  
**Audit Timestamp:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Error Budget Status:** **EXHAUSTED ({budget_consumed_percent:.1f}% consumed)**  

---

## 🛑 Governance Decision
The allowable failure budget stipulated in the SLO agreement ({TARGET_SLO_PERCENT}%) has been **exceeded by {budget_consumed_percent - 100:.1f}%**.

In adherence to enterprise **Site Reliability Engineering (SRE)** principles applied to Data Products:
1. **FEATURE FREEZE IN EFFECT:** Deployment of new dbt models, transformations, or schema fields to this data product is strictly halted.
2. **RELIABILITY SPRINT (100% FOCUS):** The engineering team must dedicate the upcoming sprint exclusively to:
   * Hardening **Data Quality Gates** using Soda Core on the staging layer.
   * Enabling proactive automated alerts via OpenLineage before downstream consumers break.
   * Investigating and mitigating the root cause of NULL anomalies in `customer_id`.
3. **UNFREEZE CRITERIA:** The freeze directive will only be revoked following 7 consecutive days of 100% successful executions and restoration of the Error Budget safety margin.
""")

    # Generation of Executive ROI & Reliability Report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"""# 📋 Executive Data Reliability & Observability ROI Report
**Data Product:** `fct_financial_transactions`  
**Pipeline:** `dbt_build_marts_financial`  
**Namespace:** `fiap.mba.dpm`  
**Generated At:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  

---

## 1. Operational Diagnostic (SLIs & Incidents)
* **Actual Availability:** {availability_sli:.1f}% (SLO Target: {TARGET_SLO_PERCENT:.1f}%)
* **Recorded Incidents:** {len(incidents)}
* **Mean Time to Detect (MTTD):** {avg_mttd:.1f} minutes
* **Mean Time to Resolve (MTTR):** {avg_mttr:.1f} minutes ({avg_mttr/60:.1f} hours)
* **Total Accumulated Data Downtime:** {total_downtime_minutes:.1f} minutes ({total_downtime_minutes/60:.1f} hours)
* **Estimated Financial Impact:** **$ {total_loss_usd:,.2f}** (~R$ {total_loss_brl:,.2f})

---

## 2. Governance Status & Error Budget
* **Allowable Error Budget:** {ALLOWED_DOWNTIME_MINUTES:.0f} minutes/month
* **Actual Consumption:** {budget_consumed_percent:.1f}%
* **Current Status:** **{'🚨 ACTIVE DEPLOY FREEZE' if is_freeze else '✅ WITHIN SAFETY BUDGET'}**

---

## 3. Business Justification & Observability ROI
Deploying **Soda Core** (CI/CD Quality Gates) and **OpenLineage + Marquez** (Lineage Traceability & Operational Telemetry) drives down MTTD and MTTR from hours to minutes:
* **Silent Failure Prevention:** Fast circuit breaking at ingestion before corrupted records contaminate the Data Mart and Executive BI.
* **Projected Annualized Savings:** 80% reduction in Data Downtime delivers estimated annual savings exceeding **$ {total_loss_usd * 0.8 * 12:,.2f}/year**.
""")

    print(f"\n💡 [BUSINESS CASE & ROI]:")
    print(f"  ├─ Financial Loss Accumulated in Period: $ {total_loss_usd:,.2f} (~R$ {total_loss_brl:,.2f})")
    print(f"  ├─ Generated Executive Report:            '{REPORT_FILE}'")
    if is_freeze:
        print(f"  └─ Generated Deploy Freeze Policy:        '{FREEZE_FILE}'")
    print("=" * 80)

if __name__ == "__main__":
    main()
