# Lab 02 - Implementação e Validação de Data Contract com datacontract-cli (ODCS)

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** OpenDataContract Standard (ODCS / YAML) / Python 3.11+ / datacontract-cli / DuckDB  
**Duração Estimada:** 25 a 30 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é aplicar o **padrão líder da indústria de Data Contracts (OpenDataContract Standard - ODCS)** para formalizar, testar e proteger os *output ports* do Produto de Dados contra alterações incompatíveis (*breaking changes*) e perda de qualidade.

Ao final deste laboratório, você será capaz de:
1. Compreender a anatomia completa de um **Data Contract em ODCS (YAML)**: `info`, `servers`, `models`, `servicelevels` e regras de integridade.
2. Executar validação estática e linting de contratos com o **`datacontract-cli`**.
3. Realizar **testes automatizados de conformidade (*Quality Gates*)** comparando o contrato contra dados físicos (`data/analytics.duckdb`).
4. Simular um cenário real de **quebra de contrato (*Breaking Change*)** e observar como a esteira automatizada bloqueia dados corrompidos antes que afetem modelos analíticos em produção.
5. Exportar schemas derivados (JSON Schema, DDL SQL) a partir da especificação única da verdade.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 00 e 01**.
* Base de dados colunar gerada (`data/transactions.parquet`).
* Arquivos fornecidos neste laboratório:
  * [`datacontract.yaml`](datacontract.yaml): Contrato canônico de produção (v1.0.0).
  * [`datacontract_breaking.yaml`](datacontract_breaking.yaml): Contrato com quebras deliberadas de negócio.
  * [`setup_duckdb.py`](setup_duckdb.py): Utilitário de preparação da base analítica DuckDB.
  * [`run_contract_test.py`](run_contract_test.py): Executor e formatador de testes de contrato.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado (`Ctrl + ~`), entre no diretório do Lab 02:

```bash
cd lab02-contracts
```

---

### Passo 2: Anatomia do OpenDataContract Standard (`datacontract.yaml`)

Abra o arquivo [`datacontract.yaml`](datacontract.yaml) no editor e explore as 4 seções mandatórias do padrão ODCS:

1. **`info` (Metadados do Produto):**
   * Título, versão semântica (`v1.0.0`), status (`active`), descrição de negócio e squad responsável (`owner`).
2. **`servers` (Portas de Saída / Protocolos):**
   * Especifica o banco e a engine de conexão (`type: duckdb`, `database: data/analytics.duckdb`).
3. **`models` (Schema & Restrições Semânticas):**
   * Tipos de dados (`varchar`, `decimal`, `timestamp`).
   * Chave primária única (`primary: true`, `unique: true`).
   * Domínios restritos via `enum` (`payment_method`, `status`, `currency`).
   * Regras de privacidade (`pii: true`, `classification: confidential`).
4. **`servicelevels` (Garantias de Serviço / SLAs):**
   * `freshness: 15m` (latência máxima de 15 minutos).
   * `retention: 365d` (retenção de 1 ano para conformidade fiscal).

---

### Passo 3: Linting e Validação Sintática do Contrato

Antes de rodar qualquer teste contra o banco de dados, verifique se a sintaxe do arquivo YAML respeita as especificações do padrão ODCS:

```bash
datacontract lint datacontract.yaml
```

*(Caso utilize execução via Python:* `python -m datacontract.cli lint datacontract.yaml`*)*

#### Saída Esperada no Terminal:
```text
Schema validation passed!
datacontract.yaml is valid.
```

---

### Passo 4: Preparação e Execução do Teste de Conformidade (Quality Gate v1.0.0)

1. Inicialize a tabela analítica no DuckDB a partir do Parquet:
```bash
python setup_duckdb.py
```

2. Execute o teste de contrato com o `datacontract-cli`:
```bash
datacontract test datacontract.yaml
```

*(Ou utilize o utilitário integrado:* `python run_contract_test.py --contract datacontract.yaml`*)*

#### Saída Esperada no Terminal:
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

### Passo 5: Simulação de Breaking Change e Atuação do Quality Gate

Imagine que o time produtor decidiu arbitrariamente **remover os métodos de pagamento PIX e Boleto** e adicionar uma regra de que o valor mínimo deve ser `R$ 2.000,00` (`datacontract_breaking.yaml`).

Execute o teste contra esse contrato incompatível para observar como o *Shift-Left Quality Gate* atua:

```bash
datacontract test datacontract_breaking.yaml
```

*(Ou via utilitário:* `python run_contract_test.py --contract datacontract_breaking.yaml`*)*

#### Saída Esperada no Terminal:
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

> 🎯 **Conclusão de Liderança Técnica:** O pipeline falha imediatamente na esteira de integração contínua (CI/CD), impedindo que dados fora de conformidade cheguem à produção ou quebrem os modelos de Machine Learning de Prevenção a Fraudes.

---

### Passo 6: Exportação de Schemas a partir do Contrato (Single Source of Truth)

O Data Contract serve como especificação central a partir da qual outros formatos podem ser gerados automaticamente:

1. **Exportar como JSON Schema:**
```bash
datacontract export --format jsonschema datacontract.yaml
```

2. **Exportar como DDL SQL (Tabela PostgreSQL / DuckDB):**
```bash
datacontract export --format sql datacontract.yaml
```

---

## 🧪 Validação & Critérios de Aceite

Para garantir a conclusão com sucesso do Lab 02:

1. [x] O comando `datacontract lint datacontract.yaml` validou a sintaxe do ODCS com sucesso.
2. [x] O teste de conformidade com `datacontract.yaml` foi executado e obteve aprovação total `[passed]` no Quality Gate.
3. [x] O teste com `datacontract_breaking.yaml` disparou o bloqueio esperado `[failed]`, identificando as violações de negócio.
4. [x] Foi demonstrada a capacidade de exportar schemas (JSON Schema / SQL DDL) a partir do contrato único.

---

## 🧹 Cleanup

Para finalizar e retornar à pasta raiz `labs`:

```bash
cd ..
```

---

## 💡 Desafios Complementares (Para Praticar)

1. **Custom Quality Check no ODCS:** Adicione uma nova regra na seção `quality` do `datacontract.yaml` que verifique se o número de linhas da tabela é superior a 1.000 (`rowCount >= 1000`).
2. **Versionamento Semântico:** Se você precisasse adicionar um novo campo opcional `channel_id: varchar` (não obrigatório), qual seria a nova versão semântica do contrato seguindo o SemVer (`1.1.0` ou `2.0.0`)? Justifique com base no impacto para os consumidores existentes.
