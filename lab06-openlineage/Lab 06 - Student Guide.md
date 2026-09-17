# Lab 06 - Traceability & Lineage with OpenLineage + Marquez

**Course / Subject:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Docker + Python 3.11+)  
**Language / Stack:** OpenLineage SDK / Marquez / DuckDB / Docker Compose  
**Estimated Duration:** 30 to 35 minutes  

---

## 🎯 Lab Objective

The goal of this laboratory is to instrument **end-to-end traceability and operational observability (*End-to-End Lineage*)** for an analytical Data Product using the open standard **OpenLineage** (Linux Foundation) and its reference visual metadata implementation **Marquez**.

By the end of this lab, you will be able to:
* Understand OpenLineage's core operational metadata model: the core triad of **Job**, **Dataset**, and **Run**, alongside extensible metadata containers (**Facets**).
* Configure transport mechanisms in the OpenLineage SDK via standard [`openlineage.yml`](openlineage.yml).
* Instrument Python data pipelines using typed classes from the official client (`openlineage-python`).
* Deploy Marquez Server locally via Docker Compose and explore the interactive DAG lineage graph.
* Inspect **Schema Facets** and **Quality Facets** captured dynamically at runtime.
* Perform **Downstream Impact Analysis** to quantify the *Blast Radius* of enterprise breaking changes before releasing schema modifications.

---

## 📋 Prerequisites & Materials

* Completion of **Labs 00 to 05** (or starting fresh in a new environment).
* Class 03 dependencies (`duckdb>=1.1.0`, `openlineage-python>=1.0.0`).
* Files provided in this laboratory:
  * [`requirements.txt`](requirements.txt): Minimal Python runtime dependencies.
  * [`docker-compose.yml`](docker-compose.yml): Lean Marquez orchestration (PostgreSQL Alpine + Marquez API + Marquez Web UI).
  * [`openlineage.yml`](openlineage.yml): OpenLineage SDK transport configuration targeting Marquez.
  * [`setup_duckdb.py`](setup_duckdb.py): Autonomous bootstrapper initializing staging, dimension, and mart tables.
  * [`emit_lineage_events.py`](emit_lineage_events.py): Official lineage instrumentation script using `openlineage-python`.
  * [`inspect_lineage.py`](inspect_lineage.py): CLI metadata catalog inspector and ASCII graph renderer.
  * [`simulate_impact_analysis.py`](simulate_impact_analysis.py): Automated downstream impact analyzer and Blast Radius calculator.

> [!TIP]
> **🚀 Starting Fresh (Zero-Friction Self-Healing):**  
> The script `setup_duckdb.py` is 100% self-sufficient (*Self-Healing*). It generates and prepares the full analytical catalog in under 5 seconds.

---

## 🚀 Step-by-Step Guided Walkthrough

### Step 1: Navigate to the Lab Directory

In your Codespaces integrated terminal (`Ctrl + ~`), navigate into the lab directory:

```bash
cd lab06-openlineage
```

> [!NOTE]
> All commands in this laboratory must be executed from within `lab06-openlineage`.

---

### Step 2: Install Python Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

---

### Step 3: Initialize DuckDB Analytical Database

Execute the setup script to generate the end-to-end analytical data layer inside DuckDB (`data/analytics.duckdb`):

```bash
python setup_duckdb.py
```

**Expected output:**
```text
[OK] Complete analytical pipeline prepared: transactions (1000) -> fct_financial_transactions (1000).
```

---

### Step 4: Launch Marquez Server (Docker Compose)

**Marquez** is the open-source reference implementation maintained by the Linux Foundation to collect, aggregate, and visualize OpenLineage events.

Start the Marquez containers in detached mode:

```bash
docker compose up -d
```

> [!NOTE]
> **Lean Architecture:** The `docker-compose.yml` in this lab has been optimized for low memory footprints in cloud DevContainers: it utilizes PostgreSQL Alpine and disables heavy search indexing (`SEARCH_ENABLED=false`), booting cleanly within 45 to 60 seconds.

Wait approximately 30 to 45 seconds for database migrations to settle, then verify container health:

```bash
docker compose ps
```

**Expected output:**
Services `marquez-db`, `marquez-api`, and `marquez-web` should display `running` or `Up` status.

---

### Step 5: Inspect OpenLineage SDK Configuration (`openlineage.yml`)

Open [`openlineage.yml`](openlineage.yml). In the OpenLineage ecosystem, pipeline code remains fully decoupled from metadata sinks through **Transports**:

```yaml
# OpenLineage SDK Transport Configuration
# By default, emits events via HTTP to Marquez Server (port 5000)
transport:
  type: http
  url: http://localhost:5000
  endpoint: api/v1/lineage
```

This configuration instructs the SDK to emit each lineage run event via HTTP POST directly to the Marquez REST API (`port 5000`).

---

### Step 6: Emit Lineage Events with the Official SDK (`openlineage-python`)

Open [`emit_lineage_events.py`](emit_lineage_events.py). Notice how it leverages official typed classes from the SDK:
* `OpenLineageClient`: manages transport protocols and HTTP serialization.
* `Job` and `Run`: models the analytical task and the single point-in-time execution instance.
* `InputDataset` and `OutputDataset`: consumed sources and produced data assets.
* `SchemaDatasetFacet` and `SchemaField`: captures exact column names and datatypes queried from DuckDB.
* `DataQualityMetricsInputDatasetFacet`: associates data quality indicators (row counts and byte metrics).

Run the instrumentation script in your terminal:

```bash
python emit_lineage_events.py
```

**Expected output:**
```text
======================================================================
📡 LINEAGE INSTRUMENTATION WITH OPENLINEAGE PYTHON SDK
======================================================================

[*] Inspecting analytical table catalog in DuckDB...
  ├─ Table raw/transactions: 8 columns
  ├─ Table staging/stg_transactions: 8 columns
  ├─ Dimension/dim_customers: 5 columns
  └─ Data Mart/fct_financial_transactions: 10 columns (1000 records)

[*] Initializing OpenLineageClient...
  └─ [OK] Client configured via openlineage.yml (Target: http://localhost:5000)

[Step 1] Emitting lineage events for 'job_ingestion_raw_to_staging'...
  🚀 [EMIT -> MARQUEZ] Job='job_ingestion_raw_to_staging' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_ingestion_raw_to_staging' | RunState=COMPLETE

[Step 2] Emitting lineage events for 'dbt_build_marts_financial'...
  🚀 [EMIT -> MARQUEZ] Job='dbt_build_marts_financial' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='dbt_build_marts_financial' | RunState=COMPLETE

[Step 3] Emitting events for Data Mart downstream consumers...
  🚀 [EMIT -> MARQUEZ] Job='job_bi_executive_dashboard' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_bi_executive_dashboard' | RunState=COMPLETE
  🚀 [EMIT -> MARQUEZ] Job='job_ml_fraud_feature_store' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_ml_fraud_feature_store' | RunState=COMPLETE
  🚀 [EMIT -> MARQUEZ] Job='job_bacen_regulatory_export' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_bacen_regulatory_export' | RunState=COMPLETE

======================================================================
✅ SUCCESS: 10 OpenLineage events processed and saved to 'lineage_events.json'.
🌐 Metadata synchronized live in Marquez!
   Access the web UI at: http://localhost:3000 (Namespace: fiap.mba.dpm)
======================================================================
```

> [!TIP]
> **Offline Mode:** If Marquez is offline or unreachable, the script gracefully logs a friendly warning and serializes all events locally using OpenLineage's official `Serde` into `lineage_events.json`, ensuring downstream analysis steps continue without interruption.

---

### Step 7: Visual Lineage Exploration in Marquez UI (Port 3000)

1. In Codespaces, navigate to the **PORTS** tab (next to Terminal) and locate port **3000**.
2. Click the globe icon (*Open in Browser*) or open `http://localhost:3000` if running locally.

> [!IMPORTANT]
> **Resolving HTTP ERROR 401 in Codespaces:**  
> By default, forwarded ports in Codespaces are marked *Private*. If your browser returns `HTTP ERROR 401`:
> * In the **PORTS** tab, right-click port **3000** $\rightarrow$ **Port Visibility** $\rightarrow$ switch to **Public**.
> * *Or alternatively:* open internally via VS Code by pressing `Ctrl + Shift + P` $\rightarrow$ type `Simple Browser: Show` $\rightarrow$ enter `http://localhost:3000`.

3. In the top Marquez navigation bar, select Namespace: **`fiap.mba.dpm`**.
4. **Explore the DAG Graph:**
   * Observe the end-to-end dependency graph rendered automatically:  
     `transactions.parquet` $\rightarrow$ `job_ingestion_raw_to_staging` $\rightarrow$ `stg_transactions` + `dim_customers` $\rightarrow$ `dbt_build_marts_financial` $\rightarrow$ `fct_financial_transactions`.
5. **Inspect Modular Facets:**
   * Click the `fct_financial_transactions` dataset node.
   * On the right panel, inspect the **Schema** facet showing synchronized column types.
   * Review the **Data Quality Metrics** facet confirming row counts (1,000 records).

---

### Step 8: Terminal Inspection & Downstream Impact Analysis (Blast Radius)

Beyond web interfaces, lineage metadata is heavily consumed programmatically in CI/CD pipelines to prevent cascading breaking changes.

1. Inspect the metadata catalog in your terminal:
   ```bash
   python inspect_lineage.py
   ```

2. Run the automated downstream impact simulation:
   ```bash
   python simulate_impact_analysis.py
   ```

**Expected output:**
The breadth-first graph traversal algorithm identifies that modifying or renaming `amount` in `transactions.parquet` causes a cascading break affecting the Staging layer, the final Data Mart, and 3 downstream consumer products (Executive BI Dashboard, ML Fraud Feature Store, and the BACEN Regulatory Report).

---

### Step 9: Shutdown Marquez Server

When finished, release system resources by stopping the containers:

```bash
docker compose down
```

---

## 🧪 Validation & Acceptance Criteria

To consider Lab 06 successfully completed:
1. Marquez containers boot properly and listen on ports `3000` and `5000`.
2. `emit_lineage_events.py` utilizes the official `openlineage-python` SDK to emit events to Marquez and serialize to `lineage_events.json`.
3. The end-to-end lineage DAG is verifiable both via Marquez Web UI and `inspect_lineage.py`.
4. Downstream impact analysis accurately reports the Blast Radius across all downstream consumers.

---

## 🧹 Cleanup

Return to the repository root directory:

```bash
cd ..
```

---

## 💡 Complementary Challenges

1. **Add OwnershipJobFacet via SDK:** Modify `emit_lineage_events.py` using SDK classes `OwnershipJobFacet` and `OwnershipJobFacetOwners` to assign squad accountability (`Data Platform & Governance Squad`).
2. **Simulate Job Failure (RunState.FAIL):** Emit a failed run event simulating an unhandled contract violation and observe the node status color shift from green to red in the Marquez UI.
