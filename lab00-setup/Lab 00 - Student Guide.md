# Lab 00 - Express Setup & Environment Validation

**Course / Track:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** Python 3.11+ / DuckDB / datacontract-cli / pip  
**Estimated Duration:** 10 to 15 minutes  

---

## 🎯 Lab Objectives

The goal of this foundational lab is to guarantee **standardization and technical readiness** across the development environment before embarking on the hands-on exercises covering *Data Products*, *Data Contracts*, and *Data Observability*.

By the end of this lab, you will be able to:
1. Initialize a reproducible development session in **GitHub Codespaces** or a local virtual environment.
2. Install the **Session 01** dependencies in seconds using **`pip`**.
3. Validate the installation and runtime health of core tools (`duckdb`, `datacontract-cli`, `pyarrow`).
4. Execute in-memory local OLAP queries using **DuckDB** directly against columnar Parquet files (`transactions.parquet`).

---

## 📋 Prerequisites & Materials

* Internet access and an active **GitHub** account with access to the course repository.
* A modern web browser (Google Chrome, Firefox, or Microsoft Edge) to run Codespaces in-browser.
* *(Optional for local execution)*: Python 3.11 or higher installed along with package manager (`pip`).

---

## 🚀 Step-by-Step Guide

### Step 1: Initialize Environment in GitHub Codespaces

1. Navigate to the official repository page on GitHub.
2. Click the green **Code** button $\rightarrow$ select the **Codespaces** tab $\rightarrow$ click **Create codespace on main**.
3. Wait for the container provisioning to complete. The DevContainer comes pre-configured with Python runtime, VS Code extensions, and CLI developer tools.

> 💡 **Local Execution Note:** If running locally on your machine, clone the repository, create a virtual environment, and activate it:
> ```bash
> # Create virtual environment
> python -m venv .venv
> source .venv/bin/activate  # On Windows: .venv\Scripts\activate
> ```

---

### Step 2: Navigate and Install Core Stack

Open the integrated terminal (`Ctrl + ~`).

1. Navigate to this lab's directory:
```bash
cd lab00-setup
```

2. Install Session 01 dependencies (~5 to 10 seconds):
```bash
pip install -r ../requirements-aula01.txt
```

3. Run the environment verification script:
```bash
python check_env.py
```

#### Expected Terminal Output:
```text
=================================================================
  [*] MBA ABD - DPM: ENVIRONMENT & DEPENDENCY VERIFICATION
=================================================================
  [OK] Python Runtime: v3.11+ detected

--- 1. Core Tooling (Session 01: Data Products & Contracts) ---
  [OK] DuckDB Python Engine: Installed and importable.
  [OK] datacontract-cli (ODCS Engine): Installed and importable.
  [OK] Pandas DataFrame: Installed and importable.
  [OK] Apache Arrow (Parquet Engine): Installed and importable.

--- 2. Tooling for Upcoming Sessions (Sessions 02 & 03) ---
  [WARN] dbt-core (Session 02): Not found via Python import.
  [WARN] dbt-duckdb Adapter (Session 02): Not found via Python import.
  [WARN] Soda Core Engine (Session 03): Not found via Python import.

=================================================================
  [OK] ENVIRONMENT 100% READY FOR SESSION 01 LABS!
  (Tools for Sessions 02 & 03 will be installed in upcoming labs)
=================================================================
```

---

### Step 3: Generate Base Dataset (`transactions.parquet`)

For the upcoming data contracts and observability labs, we will leverage a synthetic financial transactions dataset representing enterprise payment operations.

From within the `lab00-setup` directory, execute the synthetic data generator:

```bash
python generate_sample_data.py
```

The script generates `data/transactions.parquet` containing 2,500 transactional records complete with IDs, monetary amounts, payment methods, status codes, and timestamps.

---

### Step 4: Analytical Querying with DuckDB

Let's test DuckDB's in-memory columnar engine by querying the generated Parquet file directly using the `query_data.py` utility script:

1. Execute the analytical query:
```bash
python query_data.py
```

#### Expected Terminal Output:
```text
=================================================================
  🦆 ANALYTICAL QUERY VIA DUCKDB (IN-MEMORY)
=================================================================

--- 1. Schema & Type Inspection (DESCRIBE) ---
┌───────────────────────┬─────────────┬─────────┬─────────┬─────────┬───────┐
│      column_name      │ column_type │  null   │   key   │ default │ extra │
│        varchar        │   varchar   │ varchar │ varchar │ varchar │ int32 │
├───────────────────────┼─────────────┼─────────┼─────────┼─────────┼───────┤
│ transaction_id        │ VARCHAR     │ YES     │ NULL    │ NULL    │  NULL │
│ customer_id           │ VARCHAR     │ YES     │ NULL    │ NULL    │  NULL │
│ amount                │ DECIMAL(18,2)│ YES    │ NULL    │ NULL    │  NULL │
│ payment_method        │ VARCHAR     │ YES     │ NULL    │ NULL    │  NULL │
│ status                │ VARCHAR     │ YES     │ NULL    │ NULL    │  NULL │
│ currency              │ VARCHAR     │ YES     │ NULL    │ NULL    │  NULL │
│ transaction_timestamp │ TIMESTAMP   │ YES     │ NULL    │ NULL    │  NULL │
└───────────────────────┴─────────────┴─────────┴─────────┴─────────┴───────┘

--- 2. Aggregated Metrics by Payment Method ---
┌────────────────┬────────────────────┬──────────────┬────────────┐
│ payment_method │ total_transactions │ total_amount │ avg_ticket │
│    varchar     │       int64        │   decimal    │  decimal   │
├────────────────┼────────────────────┼──────────────┼────────────┤
│ PIX            │                640 │    489210.50 │     764.39 │
│ CREDIT_CARD    │                635 │    481102.10 │     757.64 │
│ DEBIT_CARD     │                615 │    465430.80 │     756.80 │
│ BOLETO         │                610 │    459890.30 │     753.92 │
└────────────────┴────────────────────┴──────────────┴────────────┘
=================================================================
  [OK] DuckDB analytical processing executed successfully!
=================================================================
```

2. *(Optional)* You can also run inline SQL queries directly from your shell via Python:
```bash
python -c "import duckdb; duckdb.sql(\"SELECT payment_method, COUNT(*) AS total FROM 'data/transactions.parquet' GROUP BY payment_method\").show()"
```

---

## 🧪 Validation & Acceptance Criteria

To confirm your setup is validated and ready for **Lab 01**:

1. [x] Session 01 dependencies successfully installed (`duckdb`, `datacontract-cli`, `pandas`, `pyarrow`).
2. [x] `check_env.py` script completed with status `[OK] ENVIRONMENT 100% READY FOR SESSION 01 LABS!`.
3. [x] The file `data/transactions.parquet` was generated successfully.
4. [x] The `query_data.py` script displayed schema inspection and payment method aggregations.

---

## 🧹 Cleanup

Because DuckDB runs in-process directly over the Parquet file, no persistent background services or containers are left running.

To clean up temporary files if needed:
```bash
rm -f *.tmp *.log dev.duckdb
```

To return to the repository root:
```bash
cd ..
```

---

## 💡 Complementary Challenges (Self-Practice)

1. **Time-Filtered Query in DuckDB:** Edit `query_data.py` and add a SQL query to identify all transactions with `FAILED` status and monetary amount exceeding `$1,000.00`.
2. **Exporting Summarized Report:** Use DuckDB's `COPY (...) TO 'data/report.csv' (HEADER, DELIMITER ',')` syntax to generate an aggregated CSV report directly from the Parquet dataset.
