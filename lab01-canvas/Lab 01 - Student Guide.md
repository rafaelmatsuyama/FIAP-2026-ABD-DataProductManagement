# Lab 01 - Data Product Canvas Modeling & Schema Specification

**Course / Track:** MBA in Data Engineering (ABD) — Data Product Management & Value Delivery (DPM)  
**Environment:** GitHub Codespaces (Linux DevContainer) or Local (Python 3.11+)  
**Language / Stack:** Markdown Canvas / Python 3.11+ / DuckDB / JSON Schema  
**Estimated Duration:** 20 to 25 minutes  

---

## 🎯 Lab Objectives

The goal of this laboratory is to step into the role of **Data Product Manager & Data Product Architect** by formalizing an enterprise **Data Product Canvas** and crafting the technical contract specifications of its interfaces (*output ports*).

By the end of this lab, you will be able to:
1. Map the **7 strategic quadrants** of an enterprise analytical Data Product.
2. Define and document **output ports** alongside business **SLAs/SLOs** (freshness, retention, and integrity).
3. Structure the semantic schema specification in standardized format (`schema_spec.json`).
4. Execute an **automated compliance audit** using DuckDB (`validate_schema.py`) to verify that the underlying dataset strictly satisfies the Canvas requirements.

---

## 📋 Prerequisites & Materials

* Completion of **Lab 00** (environment verified and base dependencies installed).
* Base transactions dataset generated (`data/transactions.parquet`).
* Lab reference artifacts:
  * [`data_product_canvas.md`](data_product_canvas.md): Reference Canvas template and documented baseline.
  * [`schema_spec.json`](schema_spec.json): Technical schema specification and semantic domain rules.
  * [`validate_schema.py`](validate_schema.py): DuckDB-powered schema auditing engine.

---

## 🚀 Step-by-Step Guide

### Step 1: Navigate to Lab Directory

In your integrated terminal (`Ctrl + ~`), switch to the Lab 01 directory:

```bash
cd lab01-canvas
```

---

### Step 2: Understand the Corporate Mission

You have been appointed as **Lead Data Product Manager** tasked with architecting the **`financial_transactions_product`** for a large-scale financial institution.

#### Business Challenge:
* The **Fraud Prevention** team suffers from frequent downstream pipeline failures because fields like `amount` and `payment_method` arrive with altered data types or unexpected values.
* The **Regulatory Compliance** department requires consolidated transaction audits partitioned by payment method with a maximum latency of 15 minutes (*Freshness SLA*).
* Corporate governance mandates that no Personally Identifiable Information (PII) is exposed in plaintext.

---

### Step 3: Explore and Structure the Data Product Canvas

Open [`data_product_canvas.md`](data_product_canvas.md) in the editor. Inspect and master the 7 architectural building blocks:

1. **Value Proposition & Problem Statement:** Measurable analytical value delivered to business consumers.
2. **Consumers & Personas:** Who consumes the data and for what purpose (Data Science, Compliance, BI).
3. **Output Ports:** Delivery mechanisms and protocols (Parquet files, SQL Views, DuckDB).
4. **Input Ports:** Upstream source origins (Core Banking CDC streams).
5. **Service Level Agreements (SLAs/SLOs):** Freshness (15 min), Availability (99.5%), Retention (365 days), and integrity gates.
6. **Governance & Privacy (LGPD/GDPR):** Pseudonymization (`customer_id`) and role-based access control.
7. **Success Metrics & ROI:** Reduction in Data Downtime and onboarding cycle time.

---

### Step 4: Technical Schema Specification (`schema_spec.json`)

To bridge business design with automated programmatic verification, open [`schema_spec.json`](schema_spec.json).

Observe how business domain rules are codified into metadata:
* **Primary Key:** `transaction_id` is mandatory (`required: true`) and unique (`unique: true`).
* **Allowed Values:** `payment_method` only accepts `['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO']`.
* **Numerical Bounds:** `amount` enforces a minimum value threshold of `0.01` (`amount > 0`).

---

### Step 5: Compliance Auditing with DuckDB

Run the validation engine to verify whether `data/transactions.parquet` satisfies 100% of the Canvas definitions:

```bash
python validate_schema.py
```

#### Expected Terminal Output:
```text
======================================================================
  📋 LAB 01: SCHEMA AUDIT & DATA PRODUCT COMPLIANCE
======================================================================
  [i] Data Product: 'financial_transactions_product' (v1.0.0)
  [i] Total Records Analyzed: 2500

--- 1. Mandatory Fields Validation (Not Null) ---
  [PASS] Field 'transaction_id': 0 nulls found.
  [PASS] Field 'customer_id': 0 nulls found.
  [PASS] Field 'amount': 0 nulls found.
  [PASS] Field 'payment_method': 0 nulls found.
  [PASS] Field 'status': 0 nulls found.
  [PASS] Field 'currency': 0 nulls found.
  [PASS] Field 'transaction_timestamp': 0 nulls found.

--- 2. Primary Key Uniqueness Validation ---
  [PASS] Key 'transaction_id': 100% unique (2500/2500).

--- 3. Allowed Domain Values Validation ---
  [PASS] Domain of 'payment_method' ['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO']: 100% compliant.
  [PASS] Domain of 'status' ['COMPLETED', 'PENDING', 'FAILED']: 100% compliant.
  [PASS] Domain of 'currency' ['BRL', 'USD', 'EUR']: 100% compliant.

--- 4. Numerical Business Rules Validation ---
  [PASS] Rule 'amount >= 0.01': 100% compliant.

======================================================================
  [OK] FULL COMPLIANCE: DATASET MEETS 100% OF DATA PRODUCT CANVAS REQUIREMENTS!
======================================================================
```

---

## 🧪 Validation & Acceptance Criteria

To confirm successful completion of this lab:

1. [x] [`data_product_canvas.md`](data_product_canvas.md) is contextualized and aligned with financial domain requirements.
2. [x] [`schema_spec.json`](schema_spec.json) formalizes all 7 fields with explicit types, nullability, uniqueness, and value domains.
3. [x] `validate_schema.py` executes with **100% approval (`[PASS]`)** across nullability, uniqueness, domain validity, and range tests.

---

## 🧹 Cleanup

To return to the workspace root and prepare for **Lab 02 (Data Contracts with `datacontract-cli`)**:

```bash
cd ..
```

---

## 💡 Complementary Challenges (Self-Practice)

1. **Simulate a Business Rule Violation:** Temporarily add an unsupported payment method (e.g. `"CRYPTO"`) to `schema_spec.json` or increase `minimum: 1000.00`. Run `python validate_schema.py` and inspect how the audit report pinpoints non-compliant records.
2. **Design a New Output Port:** Add a derived analytical field to the Canvas (e.g., `is_high_value_transaction: BOOLEAN`) and describe which downstream consumer persona benefits from this enrichment.
