# Lab 07 - Data SRE: Operational Telemetry, SLO Auditing, and Error Budget with Marquez API

**Course / Subject:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** Python 3.11+ / OpenLineage SDK / Marquez REST API / SRE Metrics  
**Estimated Duration:** 20 to 25 minutes  

---

## 🎯 Lab Objective

The goal of this laboratory is to step into the dual role of **Data Reliability Engineer (Data SRE) & Data Product Lead**, bridging technical data observability with executive business decision-making. You will query the **Marquez REST API** to harvest real operational telemetry from data pipeline executions, compute **Availability SLIs**, quantitatively measure **Data Downtime** (MTTD and MTTR), audit **Error Budget** burn rates, and trigger automated governance policies (**Deploy Freeze** vs **Feature Innovation**).

By the end of this lab, you will be able to:
* Inject operational telemetry run events with terminal states (`COMPLETED` and `FAILED`) using the typed **OpenLineage SDK**.
* Inspect execution histories with interactive health badges directly in the **Marquez UI**.
* Programmatically query the **Marquez REST API** (`/api/v1/namespaces/.../runs`) to audit Data Product reliability metrics.
* Calculate metric **Data Downtime** across an enterprise operational window by summing **MTTD (Mean Time to Detect)** and **MTTR (Mean Time to Resolve)**.
* Evaluate compliance against agreed contractual **Service Level Objectives (99.0% SLO)** and automate **Deploy Freeze** enforcement when the Error Budget is depleted.
* Quantify business financial loss in hard currency ($ / R$) and prove the financial **Return on Investment (ROI)** of data observability platforms to C-Level stakeholders.

---

## 📋 Prerequisites & Materials

* Completion of **Labs 05 and 06** (Marquez Server listening on port 5000 and Marquez Web UI on port 3000).
* Python 3.11+ and packages `requests` and `openlineage-python`.
* Files provided in this laboratory:
  * [`requirements.txt`](requirements.txt): Minimal Python runtime dependencies.
  * [`openlineage.yml`](openlineage.yml): OpenLineage SDK transport configuration targeting port 5000.
  * [`simulate_pipeline_incidents.py`](simulate_pipeline_incidents.py): Operational telemetry and incident injector for Marquez.
  * [`audit_downtime_slo.py`](audit_downtime_slo.py): Data SRE auditing engine consuming the Marquez REST API.

---

## 🚀 Step-by-Step Guided Walkthrough

### Step 1: Navigate to the Lab Directory

In your Codespaces integrated terminal (`Ctrl + ~`), navigate into the lab directory:

```bash
cd lab07-downtime-incident
```

> [!NOTE]
> All commands in this laboratory must be executed from within `lab07-downtime-incident`.

---

### Step 2: Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

---

### Step 3: Inject Operational Telemetry & Incidents into Marquez

Enterprise analytical platforms operate in recurring cycles (hourly/daily batches). We will utilize the **OpenLineage SDK** to emit a historical series of 6 executions for the `dbt_build_marts_financial` job to Marquez, simulating a 24-hour operational window containing regular runs and a major data contract violation:

Execute the telemetry injector:

```bash
python simulate_pipeline_incidents.py
```

**Expected output:**
```text
================================================================================
🚨 OPERATIONAL TELEMETRY & DATA INCIDENT INJECTOR (OPENLINEAGE)
================================================================================
[*] Connecting to Marquez Server via OpenLineageClient (http://localhost:5000)...

[*] Emitting 6-run execution history for Job: [fiap.mba.dpm:dbt_build_marts_financial]...

  ├─ Run 1a2b3c4d... | ✅ COMPLETED | Regular Nightly Execution (Batch D-1)
  ├─ Run 2b3c4d5e... | ✅ COMPLETED | Regular Morning Execution (06:00 Consolidation)
  ├─ Run 3c4d5e6f... | ❌ FAILED    | INCIDENT #1: Data Contract Violation (18.4% nulls in 'customer_id')
  │  └─ 💥 Root Cause: DataContractException: Check 'customer_id_not_null' failed on upstream staging. Null rate=18.4%.
  ├─ Run 4d5e6f7a... | ❌ FAILED    | INCIDENT #2: Automated Retry Without Fix (Airflow Retries Exhausted)
  │  └─ 💥 Root Cause: SodaScanFailed: Quality Gate failed. 184 invalid rows detected in fct_financial_transactions.
  ├─ Run 5e6f7a8b... | ✅ COMPLETED | RECOVERY: Engineering hotfix deployed and pipeline successfully reprocessed
  └─ Run 6f7a8b9c... | ✅ COMPLETED | Current Regular Execution (Healthy State Restored)

================================================================================
🌐 SUCCESS: Telemetry successfully synchronized to Marquez API!
================================================================================
```

---

### Step 4: Visual History Inspection in Marquez UI (Port 3000)

1. Open the **Marquez Web UI** at `http://localhost:3000` (or use VS Code's *Simple Browser*).
2. Select Namespace **`fiap.mba.dpm`**.
3. Click on the job node **`dbt_build_marts_financial`**:
   * Inspect the side panel **Runs** tab: observe the execution timeline with green (**COMPLETED**) and red (**FAILED**) badges.
   * Click on a failed run to inspect the error facet (`ErrorMessageRunFacet`) containing the contract violation diagnostic.

---

### Step 5: Automated SRE Audit & Error Budget Burn Rate Analysis

Now that the run telemetry is recorded in the server, execute the SRE audit engine. It calls the Marquez REST API (`/api/v1/namespaces/fiap.mba.dpm/jobs/dbt_build_marts_financial/runs`) and evaluates core reliability indicators:

```bash
python audit_downtime_slo.py
```

**Expected output:**
```text
================================================================================
📊 DATA SRE AUDITING ENGINE: SLI/SLO, ERROR BUDGET & DATA DOWNTIME
================================================================================
[*] Connecting to Marquez REST API at http://localhost:5000...
  └─ [OK] 6 actual runs collected from Marquez API.

INCIDENT       | STATUS       | MTTD (min) | MTTR (min) | TOTAL DOWNTIME   | ROOT CAUSE
----------------------------------------------------------------------------------------------------
INC-2026-001   | RESOLVED     |      0.8 m |    359.2 m |      360.0 min (6.0h) | DataContractException: Check 'custo...
----------------------------------------------------------------------------------------------------

[📈 SRE INDICATORS & SLIS]:
  ├─ Telemetry Source:                MARQUEZ_REST_API
  ├─ Total Runs Inspected:            6 (Success: 4 | Failures: 2)
  ├─ Actual Availability SLI:         66.7%
  ├─ Mean MTTD (Detection):           0.8 minutes
  ├─ Mean MTTR (Recovery):            359.2 minutes (6.0 hours)
  └─ Accumulated Data Downtime:       360.0 minutes (6.0 hours)

[🎯 SERVICE LEVEL OBJECTIVE (SLO) AUDIT]:
  ├─ Contractual Target (Agreed SLO): 99.0%
  ├─ Error Budget Allowance:          432 minutes/month
  ├─ Time Consumed by Incidents:      360 minutes
  └─ Error Budget Consumption:        83.3%

💡 [BUSINESS CASE & ROI]:
  ├─ Financial Loss Accumulated in Period: $ 90,000.00 (~R$ 486,000.00)
  └─ Generated Executive Report:            'DATA_RELIABILITY_REPORT.md'
================================================================================
```

> [!TIP]
> **Resilience Fallback:** If Marquez is unreachable due to local port restrictions, the script seamlessly falls back to the local snapshot stored in `marquez_runs_fallback.json`, ensuring the full SRE audit runs without interruption.

---

### Step 6: Inspect Generated Governance Artifacts

Open and examine the executive governance reports generated in the lab directory:

1. **[`DATA_RELIABILITY_REPORT.md`](DATA_RELIABILITY_REPORT.md):**
   * Executive briefing tailored for engineering leaders and C-Suite executives, translating technical pipeline failures into business financial impact ($ / R$) and highlighting the ROI of modern data observability.
2. **[`DEPLOY_FREEZE.md`](DEPLOY_FREEZE.md) *(when applicable)*:**
   * When Error Budget burn exceeds 100%, the audit engine automatically generates a binding governance directive halting new feature deployments until technical debt and reliability margins are recovered.

---

## 🧪 Validation & Acceptance Criteria

To consider Lab 07 successfully completed:
1. `simulate_pipeline_incidents.py` emits operational telemetry runs to Marquez.
2. The execution timeline showing green and red health badges is verifiable in the Marquez Web UI (port 3000).
3. `audit_downtime_slo.py` consumes the Marquez REST API and computes availability SLIs, MTTD, MTTR, and Error Budget consumption.
4. The executive report `DATA_RELIABILITY_REPORT.md` is inspected with financial ROI impact numbers.

---

## 🧹 Cleanup

Return to the repository root directory:

```bash
cd ..
```

---

## 💡 Complementary Challenges

1. **Simulate Error Budget Exhaustion (Deploy Freeze):** Modify `simulate_pipeline_incidents.py` to increase outage duration to 8 hours and re-run the audit to trigger >100% Error Budget burn, observing automatic emission of `DEPLOY_FREEZE.md`.
2. **Custom Cost Facet Integration:** Add a custom OpenLineage facet capturing hourly cluster compute cost and incorporate that parameter directly into `audit_downtime_slo.py`'s financial impact model.
