# Data Product Canvas: Financial Risk & Payment Transactions

**Nome do Produto de Dados:** `financial_transactions_product`  
**Domínio:** `Fintech & Core Banking`  
**Data Product Owner (DPO):** `Squad de Risco & Prevenção a Fraudes`  
**Status do Ciclo de Vida:** `Development / Pre-Production (v1.0.0)`  

---

## 1. 🎯 Proposta de Valor & Problema de Negócio
* **Problema:** Times de Prevenção a Fraudes e Risco de Crédito consumiam dados brutos de transações com esquemas voláteis, gerando quebras recorrentes de modelos e atrasos na detecção de anomalias.
* **Proposta de Valor:** Entregar uma visão transacional analítica confiável, limpa, enriquecida e com garantias de entrega contínua (SLAs de frescor de 15 minutos e integridade de tipos).

---

## 2. 👥 Consumidores & Casos de Uso (Personas)
1. **Time de Detecção de Fraude (Data Science):** Treinamento e inferência de modelos de detecção de transações suspeitas em tempo quase-real.
2. **Time de Compliance & Risco Regulatório:** Auditoria de volumes financeiros por método de pagamento (PIX, Cartão, Boleto).
3. **Executivos de Operações (Analytics):** Dashboards de faturamento e ticket médio por canal de pagamento.

---

## 3. 🔌 Portas de Saída (Output Ports / Interfaces)
* **Formato de Entrega:** Arquivo colunar Parquet (`data/transactions.parquet`) e Views Analíticas DuckDB.
* **Protocolo de Acesso:** OLAP In-Memory / Object Storage / SQL Interface.
* **Contrato Semântico:** Schema Versionado v1.0.0 (OpenDataContract Standard - ODCS).

---

## 4. 📥 Portas de Entrada & Fontes de Dados (Input Ports)
* **Origem Primária:** CDC (Change Data Capture) do Banco Relacional Transacional de Core Banking.
* **Frequência de Ingestão:** Micro-batch a cada 5 minutos.
* **Classificação de Dados:** Dados Financeiros Crônicos com identificadores ofuscados (Tokenização de `customer_id`).

---

## 5. 🛡️ Garantias de Serviço & SLOs (Service Level Objectives)
* **Frescor do Dado (Freshness):** Máximo de **15 minutos** de atraso entre a transação e a disponibilidade analítica.
* **Disponibilidade (Availability):** 99.5% de disponibilidade das portas de saída.
* **Retenção (Data Retention):** Histórico de 365 dias para auditoria financeira.
* **Qualidade Crítica (Hard Constraints):**
  * `transaction_id`: Chave primária única, não nula.
  * `amount`: Valor numérico positivo $> 0.00$.
  * `payment_method`: Domínio restrito a `['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO']`.
  * `status`: Domínio restrito a `['COMPLETED', 'PENDING', 'FAILED']`.

---

## 6. 🔒 Governança, Segurança & Compliance
* **LGPD / Privacidade:** Não armazena dados PII em texto plano (nomes, CPFs ou cartões completos). Identificador pseudo-anonimizado (`customer_id = cust_XXXX`).
* **Classificação de Acesso:** Confidencial / Uso Interno Autorizado.

---

## 7. 📈 Métricas de Sucesso & ROI do Produto
* **Redução de Incidentes (Data Downtime):** Redução de 80% nas quebras de pipelines analíticos downstream.
* **Tempo de Onboarding:** Novo analista/cientista de dados consome o produto em menos de 10 minutos via especificação formal.
* **Taxa de Conformidade:** 100% das transações validadas contra o schema antes da publicação.
