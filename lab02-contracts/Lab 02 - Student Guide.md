# Lab 02 - Implementation and Validation of Data Contracts with datacontract-cli (ODCS)

**Course / Track:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** OpenDataContract Standard (ODCS / YAML) / Python 3.11+ / datacontract-cli / DuckDB  
**Estimated Duration:** 25 to 30 minutes  

---

## 🎯 Lab Objectives

The objective of this laboratory is to implement the **industry-standard OpenDataContract Standard (ODCS)** to formalize, test, and protect the Data Product's *output ports* against breaking schema changes and downstream data degradation.

By the end of this lab, you will be able to:
1. Master the complete architecture of an **ODCS Data Contract (YAML)**: `info`, `servers`, `models`, `servicelevels`, and integrity constraints.
2. Perform static schema validation and linting using **`datacontract-cli`**.
3. Execute **automated compliance testing (*Quality Gates*)** validating contract specifications against physical data assets (`data/analytics.duckdb`).
4. Simulate a real-world **breaking change scenario** and verify how the automated gate prevents corrupted data from propagating to production ML pipelines.
5. Export derived schemas (JSON Schema, DDL SQL) from a single source of truth.

---

## 📋 Prerequisites & Materials

* Access to the repository in GitHub Codespaces or local environment with Python 3.11+.
* *(Autonomous Setup)*: The environment is 100% self-healing and automatically generates or syncs sample data if this is the first lab executed in the session.
* Reference files provided in this lab:
  * [`datacontract.yaml`](datacontract.yaml): Canonical production contract (v1.0.0).
  * [`datacontract_breaking.yaml`](datacontract_breaking.yaml): Contract demonstrating deliberate breaking changes.
  * [`setup_duckdb.py`](setup_duckdb.py): DuckDB analytical database initializer.
  * [`run_contract_test.py`](run_contract_test.py): CLI runner and test report formatter.

---

## 🚀 Step-by-Step Guide

### Step 1: Navigate to Lab Directory

Open the integrated terminal (`Ctrl + ~`), navigate to `lab02-contracts`, and ensure Session 02 dependencies are installed:

```bash
cd lab02-contracts
pip install -r ../requirements-aula02.txt
```

---

### Step 2: Anatomy of the OpenDataContract Standard (`datacontract.yaml`)

Open [`datacontract.yaml`](datacontract.yaml) in the editor and examine the 4 mandatory sections of the ODCS specification:

1. **`info` (Product Metadata):**
   * Title, semantic version (`v1.0.0`), lifecycle status (`active`), business description, and owning squad (`owner`).
2. **`servers` (Output Ports & Protocols):**
   * Specifies connection engines and locations (`type: duckdb`, `database: data/analytics.duckdb`).
3. **`models` (Schema & Semantic Constraints):**
   * Strict data types (`varchar`, `decimal`, `timestamp`).
   * Primary key integrity (`primary: true`, `unique: true`).
   * Restricted domains via `enum` (`payment_method`, `status`, `currency`).
   * Privacy tags (`pii: true`, `classification: confidential`).
4. **`servicelevels` (Service Guarantees & SLAs):**
   * `freshness: 15m` (maximum 15-minute latency).
   * `retention: 365d` (1-year compliance retention).

---

### Step 3: Linting and Syntax Validation

Before executing tests against data files, verify that the contract's YAML syntax conforms to the official ODCS JSON Schema:

```bash
datacontract lint datacontract.yaml
```

*(Or via Python module:* `python -m datacontract.cli lint datacontract.yaml`*)*

#### Expected Terminal Output:
```text
Schema validation passed!
datacontract.yaml is valid.
```

---

### Step 4: Prepare Database & Run Quality Gate Test (v1.0.0)

1. Initialize the analytical table in DuckDB from the Parquet dataset:
```bash
python setup_duckdb.py
```

2. Run the automated contract compliance test:
```bash
datacontract test datacontract.yaml
```

*(Or use the companion runner script:* `python run_contract_test.py --contract datacontract.yaml`*)*

#### Expected Terminal Output:
```text
Testing datacontract.yaml
Server: local (type=duckdb, database=data/analytics.duckdb)
╭────────┬────────────────────────────────┬────────────────────────────────┬─────────╮
│ Result │ Check                          │ Field                          │ Details │
├────────┼────────────────────────────────┼────────────────────────────────┼─────────┤
│ passed │ Check that field 'amount' is   │ transactions.amount            │         │
│        │ present                        │                                │         │
│ passed │ Check that field amount has    │ transactions.amount            │         │
│        │ type number                    │                                │         │
│ passed │ Check that field amount has no │ transactions.amount            │         │
│        │ missing values                 │                                │         │
│ passed │ Check that field amount has a  │ transactions.amount            │         │
│        │ minimum of 0.01                │                                │         │
│ passed │ Check that field 'currency' is │ transactions.currency          │         │
│        │ present                        │                                │         │
│ passed │ Check that field currency has  │ transactions.currency          │         │
│        │ type string                    │                                │         │
│ passed │ Check that field               │ transactions.payment_method    │         │
│        │ 'payment_method' is present    │                                │         │
│ passed │ Check that field               │ transactions.payment_method    │         │
│        │ payment_method has type string │                                │         │
│ passed │ Check that field               │ transactions.transaction_id    │         │
│        │ 'transaction_id' is present    │                                │         │
│ passed │ Check that unique field        │ transactions.transaction_id    │         │
│        │ transaction_id has no          │                                │         │
│        │ duplicate values               │                                │         │
│ passed │ Check that field               │ transactions.transaction_time… │         │
│        │ 'transaction_timestamp' is     │                                │         │
│        │ present                        │                                │         │
╰────────┴────────────────────────────────┴────────────────────────────────┴─────────╯
```

---

### Step 5: Breaking Change Simulation & Quality Gate Enforcement

Imagine an upstream team arbitrarily decided to **remove PIX and Boleto** from the payment methods and raised the minimum transaction amount to `$2,000.00` (`datacontract_breaking.yaml`).

Execute the test against this incompatible contract to observe how the *Shift-Left Quality Gate* intervenes:

```bash
datacontract test datacontract_breaking.yaml
```

*(Or via companion script:* `python run_contract_test.py --contract datacontract_breaking.yaml`*)*

#### Expected Terminal Output:
```text
╭────────┬────────────────────────────────┬────────────────────────────────┬───────────────────────────────╮
│ Result │ Check                          │ Field                          │ Details                       │
├────────┼────────────────────────────────┼────────────────────────────────┼───────────────────────────────┤
│ failed │ Check that field amount has a  │ transactions.amount            │ Found 2470 rows with amount   │
│        │ minimum of 2000.00             │                                │ < 2000.00                     │
│ failed │ Check that field               │ transactions.payment_method    │ Found rows with values 'PIX', │
│        │ payment_method has             │                                │ 'BOLETO' outside enum         │
│ failed │ Check that field               │ transactions.merchant_tax_id   │ Field 'merchant_tax_id' is    │
│        │ 'merchant_tax_id' is present   │                                │ missing in source table       │
╰────────┴────────────────────────────────┴────────────────────────────────┴───────────────────────────────╯
```

> 🎯 **Key Architectural Takeaway:** The pipeline fails immediately in CI/CD before data enters production analytics, protecting downstream Machine Learning models and dashboards from silent corruption.

---

### Step 6: Exporting Schemas from the Contract (Single Source of Truth)

The Data Contract acts as the central authoritative specification from which other formats can be automatically generated:

1. **Export as JSON Schema:**
```bash
datacontract export jsonschema datacontract.yaml
```

2. **Export as SQL DDL (PostgreSQL / DuckDB Table):**
```bash
datacontract export sql datacontract.yaml
```

---

## 🧪 Validation & Acceptance Criteria

To confirm successful completion of Lab 02:

1. [x] `datacontract lint datacontract.yaml` validates ODCS syntax without errors.
2. [x] Compliance testing against `datacontract.yaml` produces a 100% `[passed]` Quality Gate status.
3. [x] Testing against `datacontract_breaking.yaml` successfully triggers `[failed]` results, blocking schema drift.
4. [x] Successful export of schemas (JSON Schema and SQL DDL) from the single source of truth.

---

## 🧹 Cleanup

To return to the workspace root:

```bash
cd ..
```

---

## 💡 Complementary Challenges (Self-Practice)

1. **Custom Quality Rule in ODCS:** Add a custom rule under the `quality` section of `datacontract.yaml` verifying that table row count exceeds 1,000 (`rowCount >= 1000`).
2. **Semantic Versioning Strategy:** If an optional new field `channel_id: varchar` (nullable) were added, what semantic version bump would you assign according to SemVer (`1.1.0` or `2.0.0`)? Justify your choice based on consumer impact.
