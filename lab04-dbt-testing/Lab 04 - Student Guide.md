# Lab 04 - Advanced Data Quality Gates & Statistical Testing with dbt

**Course / Track:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** dbt-core / dbt-expectations / Great Expectations semantics / DuckDB / Python 3.11+  
**Estimated Duration:** 25 to 30 minutes  

---

## 🎯 Lab Objectives

The goal of this laboratory is to establish an **Enterprise Data Quality Testing Pyramid** directly within the transformation layer of your Data Product, combining **generic native dbt tests**, **cross-model referential integrity checks**, **statistical volumetric assertions via Great Expectations (`dbt-expectations`)**, and **custom business SQL tests (singular tests)**.

By the end of this lab, you will be able to:
1. Implement the modern **`data_tests` syntax (dbt 2.0)** across Staging and Marts layers.
2. Install, configure, and execute the **`dbt-expectations`** package (Great Expectations port for dbt).
3. Enforce **referential integrity** between transactional fact tables (`fct_financial_transactions`) and dimension tables (`dim_customers`).
4. Apply **statistical distribution assertions**: row count thresholds, value ranges, and regex validation.
5. Create a **singular business test** in modular SQL to block negative financial settlement values.
6. Execute an integrated build using **`dbt build`**, observing atomic Directed Acyclic Graph (DAG) execution.

---

## 📋 Prerequisites & Materials

* Completion of **Lab 03** (or self-healing bootstrap in a fresh environment).
* Python runtime with `dbt-duckdb` installed.
* Reference files provided in this lab:
  * [`packages.yml`](packages.yml): Package declaration importing `metaplane/dbt_expectations`.
  * [`dbt_project.yml`](dbt_project.yml): Project-level configuration.
  * [`profiles.yml`](profiles.yml): Local DuckDB connection profile.
  * [`setup_duckdb.py`](setup_duckdb.py): Self-healing initializer creating `transactions` and `customers`.
  * [`query_test_results.py`](query_test_results.py): Python quality inspector verifying constraints.
  * [`tests/assert_positive_net_amount.sql`](tests/assert_positive_net_amount.sql): Custom singular SQL test.
  * Directory [`models/staging/`](models/staging/): Sources and staging models with generic tests.
  * Directory [`models/marts/`](models/marts/): Marts with referential integrity, regex, and statistical tests.

---

## 🚀 Step-by-Step Guide

### Step 1: Navigate to Lab Directory

Open your integrated terminal (`Ctrl + ~`) and navigate to the Lab 04 directory:

```bash
cd lab04-dbt-testing
```

> [!NOTE]
> All commands in this lab should be executed from within `lab04-dbt-testing`.

---

### Step 2: Install Dependencies (Fresh Environments)

If opening a new Codespace or starting from scratch:

```bash
pip install -r requirements.txt
```

---

### Step 3: Initialize Database Tables in DuckDB

Run the setup script to seed `analytics.duckdb` with both the **transactions** and **customers** tables:

```bash
python setup_duckdb.py
```

*Expected Output:*
```text
[OK] Table 'transactions' initialized with 1000 records.
[OK] Table 'customers' created with 100 registered customers.
[OK] Database analytics.duckdb setup completed successfully!
```

---

### Step 4: Install the `dbt-expectations` Package

Open [`packages.yml`](packages.yml) to inspect the Great Expectations package declaration:

```yaml
packages:
  - package: metaplane/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
```

Download package macros by executing:

```bash
dbt deps --profiles-dir .
```

*Expected Output:*
* dbt installs `dbt_expectations` along with upstream dependencies (`dbt_date`, `dbt_utils`) into `dbt_packages/`.
* Final confirmation: `Done.`

---

### Step 5: The Enterprise Testing Pyramid in Action

Inspect [`models/marts/schema.yml`](models/marts/schema.yml) to understand the 4 tiers of automated quality tests:

1. **Tier 1: Generic Tests (Schema & Nullability):**
   * `unique` and `not_null` on primary keys (`transaction_id`, `customer_id`).
   * `accepted_values` on `status` ensuring only `['COMPLETED']` is exposed to consumers.

2. **Tier 2: Relational Tests (Cross-Model Referential Integrity):**
   * Validates that every `customer_id` in `fct_financial_transactions` exists in `dim_customers`:
     ```yaml
     - relationships:
         arguments:
           to: ref('dim_customers')
           field: customer_id
     ```

3. **Tier 3: Statistical Tests (`dbt-expectations`):**
   * Table volumetry bounds: `expect_table_row_count_to_be_between: {min_value: 500, max_value: 1500}`.
   * Format regex validation: `expect_column_values_to_match_regex: {regex: '^TX_[0-9]+$'}`.
   * Numerical bounds: `expect_column_values_to_be_between: {min_value: 0.01, max_value: 5000.00}`.

4. **Tier 4: Singular Business SQL Tests:**
   * Open [`tests/assert_positive_net_amount.sql`](tests/assert_positive_net_amount.sql) ensuring `net_amount >= 0`.

---

### Step 6: Atomic Execution with `dbt build`

Rather than running `dbt run` followed by `dbt test`, use **`dbt build`**, which compiles models and tests in topological dependency order:

```bash
dbt build --profiles-dir .
```

*Expected Output:*
```text
1 of 17 START sql view model main.stg_customers ................................ [RUN]
...
17 of 17 PASS assert_positive_net_amount ....................................... [PASS in 0.04s]
Finished running 2 view models, 2 table models, 13 data tests in 1.45s.
Completed successfully
Done. PASS=17 WARN=0 ERROR=0 SKIP=0 TOTAL=17
```

All 17 nodes (models and tests) passed with zero errors!

---

### Step 7: Inspect Quality Gates via Python

Verify table contents and test results with the companion inspector:

```bash
python query_test_results.py
```

*Expected Output:*
```text
=======================================================
🧪 QUALITY INSPECTION: TABLES & DATA PRODUCTS
=======================================================

Active tables in DuckDB: ['customers', 'transactions', 'stg_customers', 'stg_transactions', 'dim_customers', 'fct_financial_transactions']

✅ Customers Dimension: 100 active records.
✅ Settled Transactions Fact: 900 validated records.
🔍 Orphan records (Referential Integrity Violations): 0
🔍 Transactions with negative net amount: 0

Sample join between Fact and Dimension:
┌────────────────┬───────────────┬───────────────┬────────┬────────────┬───────────┬────────────────┐
│ transaction_id │ customer_name │ customer_tier │ amount │ net_amount │  status   │ payment_method │
│    varchar     │    varchar    │    varchar    │ double │   double   │  varchar  │    varchar     │
├────────────────┼───────────────┼───────────────┼────────┼────────────┼───────────┼────────────────┤
│ TX_000001      │ Customer 1    │ GOLD          │ 438.38 │     429.61 │ COMPLETED │ CREDIT_CARD    │
...
└────────────────┴───────────────┴───────────────┴────────┴────────────┴───────────┴────────────────┘
```

---

### Step 8: Simulate a Quality Gate Failure (Defense in Depth)

Prove that an anomaly triggers an immediate build halt:

1. Open [`models/marts/schema.yml`](models/marts/schema.yml).
2. Temporarily edit the volumetry test threshold to impossible bounds:
   ```yaml
   - dbt_expectations.expect_table_row_count_to_be_between:
       arguments:
         min_value: 50000  # Impossible expectation
         max_value: 100000
   ```
3. Run `dbt test --select fct_financial_transactions --profiles-dir .` and observe the test failure (`FAIL 1`).
4. Revert `min_value: 500` and `max_value: 1500`, then re-run to return to green.

---

## 🧪 Validation & Acceptance Criteria

To confirm successful completion of Lab 04:

1. [x] `dbt deps` installs `dbt-expectations` successfully.
2. [x] `dbt build --profiles-dir .` passes 100% of nodes (`PASS=17 WARN=0 ERROR=0`).
3. [x] `python query_test_results.py` confirms 0 orphan records and 0 negative amounts.

---

## 🧹 Cleanup

Return to the repository root:

```bash
cd ..
```

---

## 💡 Complementary Challenges (Self-Practice)

1. **Custom Warning Severity:** Configure `severity: warn` on a non-critical test in `schema.yml`. Observe that `dbt build` emits a warning without terminating execution.
2. **Set Inclusion Test:** Add `expect_column_values_to_be_in_set` on `payment_method` in the mart schema.
3. **Future Timestamp Check:** Author a new singular test in `tests/assert_created_at_not_in_future.sql` validating that `created_at <= current_timestamp`.
