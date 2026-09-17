# Lab 01 - Modelagem de Data Product Canvas & Schema de Dados

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** Markdown Canvas / Python 3.11+ / DuckDB / JSON Schema  
**Duração Estimada:** 20 a 25 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é exercitar o **papel de liderança e engenharia de produtos de dados** através da formalização do **Data Product Canvas** e da especificação técnica de suas interfaces de dados (*output ports*).

Ao final deste laboratório, você será capaz de:
1. Mapear os **7 quadrantes estratégicos** de um Produto de Dados analítico corporativo.
2. Definir e documentar as **portas de saída (*output ports*)** e os **SLAs/SLOs** de negócio (frescor, retenção e integridade).
3. Estruturar a especificação técnica do schema semântico em formato padronizado (`schema_spec.json`).
4. Executar **auditoria analítica de conformidade** com o DuckDB (`validate_schema.py`) para verificar se a base atende rigorosamente aos requisitos do Canvas.

---

## 📋 Pré-requisitos & Materiais

* Conclusão do **Lab 00** (ambiente configurado e dependências instaladas).
* Arquivo de transações gerado (`data/transactions.parquet`).
* Documentos de referência do laboratório:
  * [`data_product_canvas.md`](data_product_canvas.md): Modelo e preenchimento de referência do Canvas.
  * [`schema_spec.json`](schema_spec.json): Especificação técnica de schema e regras semânticas.
  * [`validate_schema.py`](validate_schema.py): Motor de auditoria com DuckDB.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado (`Ctrl + ~`), entre no diretório do Lab 01:

```bash
cd lab01-canvas
```

---

### Passo 2: Análise da Missão Corporativa

Você foi designado como **Lead Data Product Manager** para estruturar o produto de dados **`financial_transactions_product`** de uma grande instituição financeira.

#### Desafio de Negócio:
* O time de **Prevenção a Fraudes** sofre com quebras constantes de pipelines de Machine Learning porque campos como `amount` e `payment_method` frequentemente chegam com tipos alterados ou valores inesperados.
* A área de **Compliance Regulatório** precisa auditar transações consolidadas por método de pagamento com atraso máximo de 15 minutos (*Freshness SLA*).
* A governança corporativa exige que nenhum dado de identificação direta (PII) seja exposto em texto plano.

---

### Passo 3: Exploração e Preenchimento do Data Product Canvas

Abra o arquivo [`data_product_canvas.md`](data_product_canvas.md) no editor. Inspecione e compreenda os 7 blocos estruturais:

1. **Proposta de Valor & Problema:** O valor analítico mensurável entregue aos consumidores.
2. **Consumidores & Personas:** Quem consome e para qual finalidade (Data Science, Compliance, BI).
3. **Portas de Saída (Output Ports):** Como o dado é entregue (Parquet, Views SQL, DuckDB).
4. **Portas de Entrada (Input Ports):** Origem primária (CDC do Core Banking).
5. **Garantias de Serviço (SLAs/SLOs):** Freshness (15 min), Availability (99.5%), Retention (365 dias) e regras de integridade.
6. **Governança & LGPD:** Pseudo-anonimização (`customer_id`) e controle de acesso.
7. **Métricas de Sucesso & ROI:** Redução de Data Downtime e tempo de onboarding.

---

### Passo 4: Especificação Técnica do Schema (`schema_spec.json`)

Para transformar o Canvas de negócio em um artefato verificável por software, abra o arquivo [`schema_spec.json`](schema_spec.json).

Observe como as regras de negócio foram formalizadas em metadados:
* **Chave Primária:** `transaction_id` é obrigatória (`required: true`) e única (`unique: true`).
* **Valores Permitidos:** `payment_method` aceita apenas `['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO']`.
* **Regras Numéricas:** `amount` deve possuir valor mínimo de `0.01` (`amount > 0`).

---

### Passo 5: Auditoria de Conformidade com DuckDB

Execute o script de auditoria para verificar se o dataset `data/transactions.parquet` atende 100% às definições do Canvas e da especificação técnica:

```bash
python validate_schema.py
```

#### Saída Esperada no Terminal:
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

## 🧪 Validação & Critérios de Aceite

Para confirmar a conclusão deste laboratório com sucesso:

1. [x] O arquivo [`data_product_canvas.md`](data_product_canvas.md) foi compreendido e contextualizado para o domínio financeiro.
2. [x] O arquivo [`schema_spec.json`](schema_spec.json) formaliza os 7 campos do produto com tipos, obrigatoriedades e domínios.
3. [x] O script `validate_schema.py` executou com **100% de aprovação (`[PASS]`)** em todos os testes de nulidade, unicidade, domínios e regras numéricas.

---

## 🧹 Cleanup

Para retornar à pasta raiz `labs` e preparar o ambiente para o **Lab 02 (Data Contracts com `datacontract-cli`)**:

```bash
cd ..
```

---

## 💡 Desafios Complementares (Para Praticar)

1. **Simulação de Violação de Negócio:** Adicione temporariamente no `schema_spec.json` um método de pagamento não suportado (ex: `"CRYPTO"`) ou altere a regra para `minimum: 1000.00`. Execute `python validate_schema.py` e observe como o relatório aponta com precisão o volume de registros em não conformidade.
2. **Novo Output Port:** Proponha no Canvas um novo campo derivado para o produto de dados (ex: `is_high_value_transaction: BOOLEAN`) e descreva qual consumidor se beneficiaria desse enriquecimento.
