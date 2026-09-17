# Lab 05 - Data Quality Gates at the Edge with Soda Core (SodaCL)

**Course / Subject:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** Soda Core / SodaCL / DuckDB / Python 3.11+  
**Estimated Duration:** 30 to 35 minutes  

---

## 🎯 Lab Objective

The goal of this laboratory is to implement an enterprise-grade **declarative Quality Gate layer at the data ingestion boundary (*Data Ingestion Quality Gates*)**, utilizing the open-source framework **Soda Core** and its human-readable declarative language **SodaCL (Soda Check Language)**.

By the end of this lab, you will be able to:
* Configure data sources in Soda Core connected to the DuckDB analytical engine (`configuration.yml`).
* Author comprehensive declarative data quality rule suites with SodaCL (`checks.yml`), covering structural integrity, numerical domain thresholds, valid categorical enumerations, and temporal freshness.
* Execute automated quality audits via the CLI (`soda scan`).
* Understand and simulate the operational mechanics of an enterprise data **Circuit Breaker**, stopping corrupted or anomalous records before they contaminate downstream Data Marts or executive dashboards.

---

## 📋 Prerequisites & Materials

* Completion of **Labs 00 to 04** (or starting fresh in a new environment).
* Class 03 dependencies (`duckdb>=1.1.0`, `soda-core-duckdb>=3.0.0`).
* Files provided in this laboratory:
  * [`requirements.txt`](requirements.txt): Lab runtime dependencies.
  * [`setup_duckdb.py`](setup_duckdb.py): Autonomous bootstrapper initializing `transactions` and `customers` tables.
  * [`configuration.yml`](configuration.yml): Soda Core connection configuration for DuckDB.
  * [`checks.yml`](checks.yml): SodaCL declarative quality rules specification.
  * [`inject_anomaly.py`](inject_anomaly.py): Incident simulation script injecting corrupted records.
  * [`restore_data.py`](restore_data.py): Recovery script restoring tables to their canonical clean state.
  * [`fix_protobuf_python314.py`](fix_protobuf_python314.py): Hotfix patch for protobuf compatibility in Python 3.14+ environments.

> [!TIP]
> **🚀 Starting Fresh (Zero-Friction Self-Healing):**  
> If you are launching this lab in a clean Codespace or folder, `setup_duckdb.py` is 100% self-sufficient (*Self-Healing*). It generates and validates all synthetic data in under 10 seconds.

---

## 🚀 Step-by-Step Guided Walkthrough

### Step 1: Navigate to the Lab Directory

In your Codespaces integrated terminal (`Ctrl + ~`), navigate to the lab folder:

```bash
cd lab05-soda-quality
```

> [!NOTE]
> All commands in this laboratory must be executed from within `lab05-soda-quality`.

---

### Step 2: Install Dependencies

Install the specific packages required for Class 03 (Soda Core with DuckDB connector):

```bash
pip install -r requirements.txt
```

> [!IMPORTANT]
> **Compatibility Note (Python 3.14+):**  
> If your environment is running Python 3.14+ and throws a `protobuf` or `distutils` exception when running Soda, run the compatibility patch below:
> ```bash
> python fix_protobuf_python314.py
> ```

---

### Step 3: Initialize the DuckDB Database

Run the setup script to create the local `data/analytics.duckdb` database populated with the canonical `transactions` and `customers` tables:

```bash
python setup_duckdb.py
```

**Expected output:**
```text
Table transactions initialized with 1000 records.
Table customers created with 100 registered customers.
[OK] Database analytics.duckdb setup completed successfully!
```

---

### Step 4: Inspect Soda Core Configuration (`configuration.yml`)

Open [`configuration.yml`](configuration.yml). It informs Soda Core how to connect to DuckDB:

```yaml
data_source analytics:
  type: duckdb
  path: data/analytics.duckdb
```

This configuration names the data source `analytics`, which is referenced in CLI scan commands via `-d analytics`.

---

### Step 5: Inspect SodaCL Declarative Rules (`checks.yml`)

Open [`checks.yml`](checks.yml). SodaCL enables engineers and product managers to express business contracts with high semantic readability:

```yaml
# SodaCL checks for the Financial Transactions Data Product
checks for transactions:
  # 1. Structural Integrity & Volumetrics
  - row_count > 0
  - missing_count(transaction_id) = 0
  - duplicate_count(transaction_id) = 0

  # 2. Financial Domain Rules & Thresholds
  - min(amount) > 0
  - max(amount) <= 10000
  - missing_count(amount) = 0

  # 3. Valid Categories and Accepted Values
  - invalid_count(status) = 0:
      valid values: ['COMPLETED', 'FAILED', 'PENDING']

  - invalid_count(payment_method) = 0:
      valid values: ['PIX', 'CREDIT_CARD', 'BOLETO']

  - invalid_count(currency) = 0:
      valid values: ['BRL', 'USD', 'EUR']

  # 4. Temporal Integrity
  - missing_count(created_at) = 0

checks for customers:
  - row_count >= 100
  - missing_count(customer_id) = 0
  - duplicate_count(customer_id) = 0
  - invalid_count(customer_tier) = 0:
      valid values: ['STANDARD', 'GOLD', 'VIP']
```

---

### Step 6: Run the Initial Quality Scan

Execute the Soda Core quality audit in your terminal:

```bash
soda scan -d analytics -c configuration.yml checks.yml
```

**Expected output:**
```text
Soda Core 3.x.x
Scan summary:
All checks passed!
All [X] checks passed! No failures, no warnings.
```

The CLI process returns exit code `0` (`exit code 0`), indicating that the Quality Gate is **open and data is safe for consumption**.

---

### Step 7: Simulate an Enterprise Data Incident (Circuit Breaker)

Now simulate a real-world upstream failure: an undocumented schema drift or upstream bug injects negative amounts, NULL IDs, and corrupted statuses:

```bash
python inject_anomaly.py
```

Then, re-run the Soda Core scan:

```bash
soda scan -d analytics -c configuration.yml checks.yml
```

**Expected Circuit Breaker Behavior:**
* Soda detects explicit violations across multiple checks:
  * `missing_count(transaction_id) = 0` $\rightarrow$ **FAIL** (found NULL IDs).
  * `min(amount) > 0` $\rightarrow$ **FAIL** (found negative amount `-999.50`).
  * `invalid_count(status) = 0` $\rightarrow$ **FAIL** (found `CORRUPTED_STATUS`).
* The process terminates with a **non-zero exit code** (`exit code 2` or `3`), immediately triggering a Circuit Breaker and halting orchestration pipelines (e.g., Airflow DAGs, GitHub Actions workflows).

---

### Step 8: Restore Canonical State

To recover the database to its pristine, healthy state, run the restoration script:

```bash
python restore_data.py
```

Verify that the Quality Gate turns green again:

```bash
soda scan -d analytics -c configuration.yml checks.yml
```

---

## 🧪 Validation & Acceptance Criteria

To consider Lab 05 successfully completed:
1. `configuration.yml` successfully connects to local DuckDB.
2. The initial scan on canonical data achieves **100% pass rate** (*All checks passed*).
3. The scan following `python inject_anomaly.py` **halts the pipeline** with clear detection of contract and business rule violations.
4. Database restoration via `python restore_data.py` returns the scan to a 100% passing state.

---

## 🧹 Cleanup

After completing validations, return to the repository root directory:

```bash
cd ..
```

---

## 💡 Complementary Challenges

1. **Volumetric Anomaly Check:** Add a SodaCL check to `checks.yml` ensuring total transaction volume is strictly between `900` and `1100` (`row_count between 900 and 1100`).
2. **Referential Integrity Check:** Add a SodaCL rule validating that every `customer_id` present in the `transactions` table exists in the `customers` dimension table.
