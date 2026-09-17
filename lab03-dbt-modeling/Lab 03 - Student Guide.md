# Lab 03 - Data Product Modeling & Model Contracts with dbt

**Course / Track:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** dbt-core / dbt-duckdb / Modular SQL / DuckDB / Python 3.11+  
**Estimated Duration:** 25 to 30 minutes  

---

## 🎯 Lab Objectives

The goal of this laboratory is to engineer the internal analytics pipeline of an **Enterprise Data Product**, applying **native dbt Model Contracts (`contract: {enforced: true}`)** to ensure that consumption tables (*Domain Marts / Output Ports*) never suffer from silent schema drift, missing columns, or unexpected data type mutations.

By the end of this lab, you will be able to:
1. Structure a modular, production-grade dbt project across distinct architectural layers (**Staging** and **Domain Marts**).
2. Configure dbt's connection to **DuckDB** in an isolated, portable, reproducible setup (`--profiles-dir .`).
3. Implement and activate **strict Model Contracts** directly in the metadata specification (`schema.yml`).
4. Understand compile-time contract enforcement guarantees: **strict typing**, **mandatory constraints (`not_null`)**, and **rejection of undocumented columns**.
5. Simulate an authentic **internal breaking change incident** and evaluate dbt's defensive build-breaking behavior.
6. Query, inspect, and validate the resulting persisted *Data Product* inside DuckDB using Python.

---

## 📋 Prerequisites & Materials

* Completion of **Labs 00, 01, and 02** (or starting fresh in a brand-new container).
* Session dependencies (`dbt-core>=1.8.0`, `dbt-duckdb>=1.8.0`, `duckdb>=1.1.0`).
* Files provided in this lab:
  * [`requirements.txt`](requirements.txt): Lean dbt and DuckDB runtime dependencies.
  * [`dbt_project.yml`](dbt_project.yml): Master dbt project configuration.
  * [`profiles.yml`](profiles.yml): Local DuckDB connection profile.
  * [`setup_duckdb.py`](setup_duckdb.py): Self-healing DuckDB initializer (`data/analytics.duckdb`).
  * [`query_mart.py`](query_mart.py): Python analytical inspector for the materialized mart.
  * Directory [`models/staging/`](models/staging/): Raw sources definition and cleaning model (`stg_transactions.sql`).
  * Directory [`models/marts/`](models/marts/): Value-delivery consumption mart with enforced contract (`fct_financial_transactions.sql` and `schema.yml`).

> [!TIP]
> **🚀 Starting from a Clean Environment (Zero Friction):**  
> If you opened a fresh Codespace or had your container rebuilt, no problem! This lab is **100% self-healing**: Steps 2 and 3 bootstrap all dependencies and seed the local database in under **30 seconds** without requiring Docker or external servers.

---

## 🚀 Step-by-Step Guide

### Step 1: Navigate to Lab Directory

In your terminal (`Ctrl + ~`), switch to the Lab 03 directory:

```bash
cd lab03-dbt-modeling
```

> [!NOTE]
> All commands in this lab should be executed from within `lab03-dbt-modeling`.

---

### Step 2: Install Dependencies

If running in a fresh environment or if dbt is not yet installed:

```bash
pip install -r requirements.txt
```

* **Duration:** ~15 seconds.
* **What happens:** `pip` installs `dbt-duckdb`, which automatically brings `dbt-core` and the embedded `duckdb` SQL engine.

---

### Step 3: Initialize Analytical DuckDB Database

Run the database setup script to seed the local database:

```bash
python setup_duckdb.py
```

* **Smart Behavior:**
  * If continuing from earlier labs, the script reuses your existing `transactions.parquet`.
  * If running from a clean state, it instantaneously synthesizes **1,000 canonical financial transactions** directly inside `data/analytics.duckdb`.

*Expected Output:*
```text
[OK] Database analytics.duckdb initialized with 1000 records.
[OK] Setup completed successfully!
```

---

### Step 4: Verify dbt Connection to DuckDB

Before compiling models, confirm that dbt connects seamlessly to DuckDB using the local profile:

```bash
dbt debug --profiles-dir .
```

*Expected Output:*
* All checks pass with `OK` (Python, profiles.yml, dbt_project.yml, and Connection test).
* Final confirmation: `All checks passed!`

---

### Step 5: Inspect and Build the Staging Layer

The Staging layer standardizes naming conventions, applies explicit type casting, and isolates downstream models from raw upstream volatility.

1. Inspect the model [`models/staging/stg_transactions.sql`](models/staging/stg_transactions.sql):
   * Note the use of `{{ source('raw_sources', 'transactions') }}`.
   * All fields are explicitly typed (`varchar`, `double`, `timestamp`).

2. Materialize the staging view:

```bash
dbt run --select staging --profiles-dir .
```

*Expected Output:*
```text
1 of 1 START sql view model main.stg_transactions .............................. [RUN]
1 of 1 OK created sql view model main.stg_transactions ......................... [OK in 0.08s]
Finished running 1 view model in 0.15s.
Completed successfully
Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1
```

---

### Step 6: The Core of the Lab — Enforced Model Contracts

Now examine the analytical consumption mart [`models/marts/fct_financial_transactions.sql`](models/marts/fct_financial_transactions.sql) and its formal specification in [`models/marts/schema.yml`](models/marts/schema.yml).

Observe the configuration in `schema.yml`:

```yaml
models:
  - name: fct_financial_transactions
    description: "Analytical mart of settled financial transactions (Enterprise Consumption Data Product)."
    config:
      contract:
        enforced: true
    columns:
      - name: transaction_id
        data_type: varchar
        constraints:
          - type: not_null
      - name: customer_id
        data_type: varchar
        constraints:
          - type: not_null
      - name: amount
        data_type: double
      - name: fee
        data_type: double
      - name: net_amount
        data_type: double
      - name: currency
        data_type: varchar
      - name: status
        data_type: varchar
      - name: payment_method
        data_type: varchar
      - name: created_at
        data_type: timestamp
```

> [!IMPORTANT]
> **Why is this transformative?**  
> When `contract: {enforced: true}` is enabled:
> 1. dbt **strictly rejects** table compilation if the SQL query returns any column not explicitly defined in the YAML contract.
> 2. dbt **strictly rejects** the build if column data types deviate from the contracted `data_type`.
> 3. dbt enforces database-level constraints (such as `NOT NULL`) directly during DDL generation.

Run the contracted model:

```bash
dbt run --select marts --profiles-dir .
```

*Expected Output:*
```text
1 of 1 START sql table model main.fct_financial_transactions ................... [RUN]
1 of 1 OK created sql table model main.fct_financial_transactions .............. [OK in 0.12s]
Finished running 1 table model in 0.20s.
Completed successfully
Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1
```

---

### Step 7: Inspect Data Product via Python

Inspect the settled transactional records in DuckDB using the Python inspection script:

```bash
python query_mart.py
```

*Expected Output:*
* Confirms present tables (`stg_transactions`, `fct_financial_transactions`, `transactions`).
* Total count of settled transactions (`status = 'COMPLETED'`).
* Financial metrics: Gross Volume, Retained Take Rate / Fees, and Net Settled Volume.
* Formatted 5-row preview of the consumption mart.

---

### Step 8: Simulate a Breaking Change Incident

As a Data Architect, prove that the enforced contract actively safeguards downstream consumers against rogue developer commits.

Let's simulate an accidental change by injecting an uncontracted column into the mart.

1. Open [`models/marts/fct_financial_transactions.sql`](models/marts/fct_financial_transactions.sql).
2. Temporarily inject an uncontracted column in the final SELECT:
   ```sql
   select
       transaction_id,
       customer_id,
       amount,
       fee,
       round(amount - fee, 2) as net_amount,
       currency,
       status,
       payment_method,
       created_at,
       'MARKETING_TAG' as extra_uncontracted_column  -- << UNCONTRACTED COLUMN
   from transactions
   where status = 'COMPLETED'
   ```
3. Save the file and trigger dbt:

```bash
dbt run --select marts --profiles-dir .
```

*Expected Compilation Error (Contract Defense Mechanism):*
```text
Compilation Error in model fct_financial_transactions (models/marts/fct_financial_transactions.sql)
This model has an enforced contract that was violated:
  - Additional column 'extra_uncontracted_column' found in SQL model, but not in contract.
```

> [!TIP]
> **Takeaway:** dbt halted compilation and refused to build the table! The contract successfully protected the analytical output port against silent schema drift.

4. **Reversion:** Remove `'MARKETING_TAG' as extra_uncontracted_column` and the preceding comma from [`models/marts/fct_financial_transactions.sql`](models/marts/fct_financial_transactions.sql), save, and re-run to restore green status:

```bash
dbt run --select marts --profiles-dir .
```

---

## 🧪 Validation & Acceptance Criteria

To confirm successful completion of Lab 03:

1. **Full Project Compilation:**
   ```bash
   dbt run --profiles-dir .
   ```
   Must display `PASS=2 WARN=0 ERROR=0 SKIP=0 TOTAL=2`.

2. **Data Product Inspection:**
   ```bash
   python query_mart.py
   ```
   Must display settled records and financial aggregations from `fct_financial_transactions`.

---

## 🧹 Cleanup

Return to the root workspace:

```bash
cd ..
```

---

## 💡 Complementary Challenges (Self-Practice)

1. **Staging Contract Enforcement:** Add `contract: {enforced: true}` to `stg_transactions` in `models/staging/schema.yml` and explore how DuckDB handles view constraints.
2. **Type Mismatch Simulation:** Intentionally change `amount`'s `data_type` from `double` to `varchar` in `schema.yml` and observe dbt's type mismatch error.
3. **Additional Constraint:** Add a `not_null` constraint to the `amount` column and validate successful compilation with `dbt run`.
