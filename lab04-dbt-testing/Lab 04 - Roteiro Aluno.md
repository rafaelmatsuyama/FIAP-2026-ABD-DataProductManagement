# Lab 04 - Esteira Unificada de Testes Nativos & Asserções com dbt-expectations

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** dbt-core / dbt-duckdb / dbt-expectations / DuckDB / Python 3.11+  
**Duração Estimada:** 25 a 30 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é construir uma **esteira industrial de confiabilidade de dados (*Data Quality Pipeline*)**, aplicando a **Pirâmide Completa de Testes no dbt**:
1. **Testes Nativos Genéricos:** unicidade, não-nulidade e integridade referencial (*foreign keys*).
2. **Testes Singulares SQL:** regras de negócio customizadas que expressam invariantes de domínio.
3. **Testes Estatísticos Avançados:** asserções de volumetria, faixas de valores e regex via pacote **`dbt-expectations`** (*port do Great Expectations*).
4. **Execução Atômica & Circuit Breaker:** orquestração com **`dbt build`** para demonstrar o bloqueio preventivo de tabelas de consumo em caso de anomalia upstream.

Ao final deste laboratório, você será capaz de:
* Configurar e gerenciar dependências de pacotes do dbt (`packages.yml` + `dbt deps`).
* Implementar testes de integridade referencial (`relationships`) entre tabelas Fato e Dimensão.
* Criar asserções customizadas em SQL puro para regras financeiras complexas.
* Aplicar asserções estatísticas do `dbt-expectations` diretamente no `schema.yml`.
* Compreender o comportamento de **Circuit Breaker do `dbt build`**, garantindo que nenhum dado corrompido ou anômalo seja servido a relatórios gerenciais ou modelos de ML.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 00 a 03** (ou início a partir de um ambiente novo/zerado).
* Dependências da aula (`dbt-core>=1.8.0`, `dbt-duckdb>=1.8.0`, `duckdb>=1.1.0`).
* Conexão ativa com a internet para baixar o pacote `dbt-expectations` via `dbt deps`.
* Arquivos fornecidos neste laboratório:
  * [`requirements.txt`](requirements.txt): Dependências mínimas de execução.
  * [`dbt_project.yml`](dbt_project.yml): Configuração mestre do projeto.
  * [`profiles.yml`](profiles.yml): Perfil local de conexão ao DuckDB.
  * [`packages.yml`](packages.yml): Declaração do pacote `metaplane/dbt_expectations`.
  * [`setup_duckdb.py`](setup_duckdb.py): Inicializador autônomo com transações e clientes.
  * [`query_test_results.py`](query_test_results.py): Inspecionador Python de integridade e joins.
  * Diretório [`models/staging/`](models/staging/): Modelos `stg_transactions.sql` e `stg_customers.sql` com testes genéricos.
  * Diretório [`models/marts/`](models/marts/): Marts `fct_financial_transactions.sql` e `dim_customers.sql` com testes estatísticos.
  * Diretório [`tests/`](tests/): Teste singular [`assert_positive_net_amount.sql`](tests/assert_positive_net_amount.sql).

> [!TIP]
> **🚀 Começando de um Ambiente Limpo (Zero Friction):**  
> Se você está iniciando este lab em um novo Codespace, não se preocupe! O ambiente é **100% autossuficiente**: os Passos 2 e 3 configuram todas as bibliotecas e tabelas em menos de **30 segundos**.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado do Codespaces (`Ctrl + ~`), entre no diretório do Lab 04:

```bash
cd lab04-dbt-testing
```

> [!NOTE]
> Todos os comandos deste laboratório devem ser executados a partir de `lab04-dbt-testing`.

---

### Passo 2: Instalação das Dependências (Ambiente Limpo)

Caso esteja em um ambiente novo, garanta a presença do dbt com adaptador DuckDB:

```bash
pip install -r requirements.txt
```

* **Duração:** ~15 segundos.
* **O que acontece:** O `pip` instala o `dbt-duckdb` e o pacote `duckdb`.
* *(Caso já tenha os pacotes instalados da aula anterior, o pip apenas confirmará que os requisitos já foram satisfeitos).*

---

### Passo 3: Inicialização das Tabelas no DuckDB

Execute o script de preparação para criar a base com as tabelas `transactions` e `customers`:

```bash
python setup_duckdb.py
```

*Saída Esperada:*
```text
[OK] Table 'transactions' initialized with 1000 records.
[OK] Table 'customers' created with 100 registered customers.
[OK] Database analytics.duckdb setup completed successfully!
```

---

### Passo 4: Download do Pacote `dbt-expectations`

O arquivo [`packages.yml`](packages.yml) contém a dependência oficial do `dbt_expectations` (mantido pela Metaplane):

```yaml
packages:
  - package: metaplane/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
```

Baixe as macros do pacote executando:

```bash
dbt deps --profiles-dir .
```

*Saída Esperada:*
* O dbt baixa o pacote e suas dependências transitivas (`dbt_date`, `dbt_utils`) para o diretório `dbt_packages/`.
* Mensagem final: `Done.`

---

### Passo 5: A Pirâmide de Testes na Prática (Sintaxe Moderna dbt 2.0)

> [!NOTE]
> **💡 Engenharia Moderna: A Evolução da Sintaxe no dbt (data_tests e arguments)**  
> A partir do dbt Core 1.10+ (preparatório para o dbt 2.0), o dbt adota a chave `data_tests:` (em substituição a `tests:`) e aninha parâmetros de teste sob `arguments:`. Isso separa formalmente os **argumentos de negócio** (`values`, `to`, `field`, etc.) das **diretivas de execução do dbt** (`severity`, `tags`, `where`). Neste laboratório, já utilizamos a sintaxe moderna recomendada pela dbt Labs.

Observe a estrutura de testes implementada neste laboratório:

#### 1. Testes Nativos & Integridade Referencial (`models/marts/schema.yml`)
Note a validação relacional que assegura que toda transação pertence a um cliente válido no cadastro:
```yaml
- name: customer_id
  data_tests:
    - not_null
    - relationships:
        arguments:
          to: ref('dim_customers')
          field: customer_id
```

#### 2. Teste Singular SQL de Negócio ([`tests/assert_positive_net_amount.sql`](tests/assert_positive_net_amount.sql))
Um teste singular no dbt é uma consulta SQL que expressa uma violação. Se a consulta retornar **0 linhas**, o teste passa:
```sql
select
    transaction_id,
    net_amount
from {{ ref('fct_financial_transactions') }}
where net_amount < 0
```

#### 3. Asserções Estatísticas Avançadas (`dbt-expectations`)
No arquivo `models/marts/schema.yml`, veja as regras estatísticas configuradas sob a chave `arguments:`:
* **Volumetria do Lote:** `dbt_expectations.expect_table_row_count_to_be_between` (garante entre 500 e 1500 linhas).
* **Faixas de Valor Monetário:** `dbt_expectations.expect_column_values_to_be_between` (valores brutos entre R$ 0,01 e R$ 5.000,00).
* **Padrão de Formato:** `dbt_expectations.expect_column_values_to_match_regex` (valida o padrão `^TX_[0-9]+$`).

---

### Passo 6: Execução Atômica com `dbt build`

Diferente do `dbt run` (que apenas cria tabelas) ou `dbt test` (que apenas testa tabelas já criadas), o **`dbt build`** executa modelos e testes entrelaçados na ordem exata do grafo DAG:

Execute a esteira completa:

```bash
dbt build --profiles-dir .
```

*Saída Esperada:*
* O dbt cria as visões de staging (`stg_transactions`, `stg_customers`).
* Executa imediatamente os testes de staging (`unique`, `not_null`, `accepted_values`).
* Cria os marts analíticos (`dim_customers`, `fct_financial_transactions`).
* Executa os testes de integridade referencial, testes estatísticos e o teste singular SQL.
* Mensagem final com todos os passos aprovados:
  `Done. PASS=27 WARN=0 ERROR=0 SKIP=0 TOTAL=27`

---

### Passo 7: Inspeção dos Resultados de Qualidade via Python

Valide os dados processados e verifique a integridade referencial no DuckDB:

```bash
python query_test_results.py
```

*Saída Esperada:*
* `✅ Dimensão Clientes: 100 registros ativos.`
* `✅ Fato Transações Liquidadas: registros validados.`
* `🔍 Registros órfãos (Violações de Integridade Referencial): 0`
* `🔍 Transações com valor líquido negativo: 0`
* Tabela demonstrativa do join limpo entre a Fato e a Dimensão.

---

### Passo 8: O Experimento do Circuit Breaker (Falha Upstream)

Agora testemunharemos o poder de governança do `dbt build` diante de um incidente de dados.

1. Abra o arquivo [`models/staging/stg_transactions.sql`](models/staging/stg_transactions.sql).
2. Simule a chegada de um dado corrompido com status inválido. Altere a linha do status para:
   ```sql
   -- Simulação de dado corrompido / status desconhecido
   'CORRUPTED_STATUS' as status,
   ```
3. Salve o arquivo e execute o `dbt build`:

```bash
dbt build --profiles-dir .
```

*Resultado Esperado (Circuit Breaker Ativado):*
```text
1 of 27 START sql view model main.stg_transactions ............................. [RUN]
1 of 27 OK created sql view model main.stg_transactions ........................ [OK in 0.08s]
2 of 27 START test accepted_values_stg_transactions_status__COMPLETED__FAILED .. [RUN]
2 of 27 FAIL 1000 accepted_values_stg_transactions_status__COMPLETED__FAILED ... [FAIL in 0.05s]
...
>> CANCELLED or SKIPPED: model main.fct_financial_transactions
```

> [!CAUTION]
> **O que acabou de acontecer?**  
> O teste de qualidade falhou imediatamente na camada de **Staging**!  
> Como resultado, o dbt acionou o **Circuit Breaker**: a materialização da tabela de consumo final (`fct_financial_transactions`) foi **sumariamente abortada (`SKIP`)**.  
> **Impacto de Negócio:** Os dashboards de diretoria e os relatórios financeiros continuam exibindo os últimos dados válidos, impedindo que dados podres gerem decisões erradas!

4. **Reversão:** No arquivo [`models/staging/stg_transactions.sql`](models/staging/stg_transactions.sql), restaure a linha original:
   ```sql
   cast(status as varchar) as status,
   ```
   Salve o arquivo e rode `dbt build --profiles-dir .` para voltar ao estado 100% verde (`PASS=27`).

---

## 🧪 Validação & Critérios de Aceite

Para certificar que sua esteira de qualidade está operando com perfeição:

1. **Esteira 100% Verde:**
   ```bash
   dbt build --profiles-dir .
   ```
   Deve registrar `PASS=27 WARN=0 ERROR=0 SKIP=0 TOTAL=27`.

2. **Inspeção de Integridade:**
   ```bash
   python query_test_results.py
   ```
   Deve registrar 0 violações de integridade referencial e 0 transações negativas.

---

## 🧹 Cleanup

Ao concluir as atividades, retorne ao diretório raiz do repositório:

```bash
cd ..
```

---

## 💡 Desafios Complementares (Para Praticar)

1. **Severidade Gradual (`severity: warn`):** Altere um teste estatístico em `models/marts/schema.yml` adicionando `config: severity: warn`. Observe como o `dbt build` emite um aviso no terminal mas não bloqueia a esteira.
2. **Teste de Proporção:** Adicione a asserção `expect_column_values_to_be_in_set` no campo `payment_method` do mart financeiro.
3. **Teste Singular de Datas:** Escreva um novo teste SQL em `tests/assert_created_at_not_in_future.sql` validando que nenhuma transação possui `created_at > current_timestamp`.
