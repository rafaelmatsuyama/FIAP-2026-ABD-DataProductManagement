# Data Product Canvas: Financial Risk & Payment Transactions

**Data Product Name:** `financial_transactions_product`  
**Domain:** `Fintech & Core Banking`  
**Data Product Owner (DPO):** `Fraud Prevention & Risk Analytics Squad`  
**Lifecycle Status:** `Development / Pre-Production (v1.0.0)`  

---

## 1. 🎯 Value Proposition & Business Problem
* **Problem:** Fraud Prevention and Credit Risk teams consumed raw, volatile transaction tables directly from transactional systems, resulting in frequent downstream model pipeline breakages and severe delays in fraud anomaly detection.
* **Value Proposition:** Deliver a trustworthy, clean, enriched analytical view of payment transactions backed by explicit SLAs/SLOs (15-minute freshness, strict schema enforcement, and zero silent schema drift).

---

## 2. 👥 Consumers & Use Cases (Personas)
1. **Fraud Detection Squad (Data Science):** Feature generation, model training, and near-real-time suspicious transaction scoring.
2. **Regulatory Compliance & Audit Team:** Continuous auditing of transactional volumes, settlement fees, and payment channel distribution.
3. **Operations & Revenue Analytics (BI):** Executive dashboards tracking throughput, gross volume, and average ticket across payment rails.

---

## 3. 🔌 Output Ports & Consumption Interfaces
* **Delivery Format:** In-memory columnar Parquet dataset (`data/transactions.parquet`) and registered DuckDB analytical views.
* **Access Protocol:** OLAP In-Memory / Object Storage / SQL Interface.
* **Semantic Contract:** Versioned OpenDataContract Standard (ODCS v1.0.0) specification.

---

## 4. 📥 Input Ports & Source Lineage
* **Primary Source:** CDC (Change Data Capture) stream from Core Banking Relational Ledger.
* **Ingestion Cadence:** Micro-batch stream every 5 minutes.
* **Data Classification:** Sensitive Financial Data with tokenized PII identifiers (`customer_id`).

---

## 5. 🛡️ Service Level Objectives (SLOs) & Quality Gates
* **Data Freshness:** Maximum **15-minute** latency between transaction execution and analytical availability.
* **Availability:** 99.5% uptime for analytical output ports.
* **Data Retention:** 365 days of partitioned operational history for regulatory audits.
* **Critical Quality Gates (Hard Constraints):**
  * `transaction_id`: Primary key, mandatory, unique, not null.
  * `amount`: Positive financial value $> 0.00$.
  * `fee`: Non-negative settlement fee $\ge 0.00$.
  * `payment_method`: Restricted domain `['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO']`.
  * `status`: Restricted domain `['COMPLETED', 'PENDING', 'FAILED']`.
  * `created_at`: Valid ISO-8601 transaction timestamp.

---

## 6. 🔒 Governance, Security & Compliance
* **Privacy & Compliance (GDPR/LGPD):** Zero plaintext PII stored (no customer names, tax IDs, or raw credit card numbers). Uses pseudonymized identifiers (`customer_id = cust_XXXX`).
* **Access Classification:** Confidential / Restricted Internal Use.

---

## 7. 📈 Success Metrics & Product ROI
* **Data Downtime Reduction:** 80% decrease in downstream ML pipeline incidents and schema drift failures.
* **Consumer Onboarding Velocity:** Reduced time-to-first-query from days to under 10 minutes via machine-readable contract specifications.
* **Contract Compliance Rate:** 100% of published transactions pass automated schema and quality gates.
