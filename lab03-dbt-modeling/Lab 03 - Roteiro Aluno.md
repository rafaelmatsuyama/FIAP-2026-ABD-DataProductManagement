# Lab 03 - Modelagem de Data Products & Model Contracts com dbt

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** dbt-core / dbt-duckdb / SQL Modular / DuckDB / Python 3.11+  
**Duração Estimada:** 25 a 30 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é construir a esteira analítica interna de um **Produto de Dados Corporativo**, aplicando **Model Contracts nativos do dbt (`contract: {enforced: true}`)** para garantir que as tabelas de consumo (*Marts / Output Ports*) jamais sofram com quebras silenciosas de schema ou desvios de tipos de dados.

Ao final deste laboratório, você será capaz de:
1. Estruturar um projeto dbt corporativo modular em camadas analíticas (**Staging** e **Marts de Domínio**).
2. Configurar a conexão do dbt com o banco analítico **DuckDB** de forma isolada e portável (`--profiles-dir .`).
3. Implementar e ativar **Model Contracts estritos** no arquivo de metadados (`schema.yml`).
4. Entender as garantias de integridade em tempo de compilação: **tipagem forçada**, **constraints obrigatórias (`not_null`)** e **rejeição de colunas não documentadas**.
5. Simular um incidente real de **quebra de contrato interno (*Breaking Change*)** e analisar o comportamento defensivo do dbt.
6. Inspecionar e validar o *Data Product* resultante persistido no DuckDB.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 00, 01 e 02** (ou início a partir de um ambiente novo/zerado).
* Dependências da aula (`dbt-core>=1.8.0`, `dbt-duckdb>=1.8.0`, `duckdb>=1.1.0`).
* Arquivos fornecidos neste laboratório:
  * [`requirements.txt`](requirements.txt): Dependências isoladas e enxutas do dbt com DuckDB.
  * [`dbt_project.yml`](dbt_project.yml): Configuração mestre do projeto dbt.
  * [`profiles.yml`](profiles.yml): Perfil local de conexão ao DuckDB.
  * [`setup_duckdb.py`](setup_duckdb.py): Inicializador e gerador autônomo da base `data/analytics.duckdb`.
  * [`query_mart.py`](query_mart.py): Inspecionador em Python do Mart gerado.
  * Diretório [`models/staging/`](models/staging/): Fontes e modelo de limpeza (`stg_transactions.sql`).
  * Diretório [`models/marts/`](models/marts/): Modelo de valor e contrato enforced (`fct_financial_transactions.sql` e `schema.yml`).

> [!TIP]
> **🚀 Começando de um Ambiente Limpo (Zero Friction):**  
> Se você abriu um novo Codespace, não participou dos labs anteriores ou teve o container recriado, não há problema! Este laboratório é **100% autossuficiente**: os Passos 2 e 3 preparam todas as dependências e o banco de dados em menos de **30 segundos**, sem depender de Docker ou servidores externos.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado do Codespaces (`Ctrl + ~`), entre no diretório do Lab 03:

```bash
cd lab03-dbt-modeling
```

> [!NOTE]
> Todos os comandos deste laboratório devem ser executados a partir de `labs/lab03-dbt-modeling`.

---

### Passo 2: Instalação das Dependências (Essencial para Ambiente Limpo)

Se você acabou de abrir um Codespace limpo ou ainda não possui o `dbt` instalado, execute:

```bash
pip install -r requirements.txt
```

* **Duração:** ~15 segundos.
* **O que acontece:** O `pip` instala o `dbt-duckdb`, que traz automaticamente como dependências o `dbt-core` e o motor embarcado do `duckdb`.
* *(Caso já tenha os pacotes instalados da aula anterior, o pip apenas confirmará que os requisitos já foram satisfeitos).*

---

### Passo 3: Inicialização da Base Analítica DuckDB

Execute o script de preparação para criar a base de dados local:

```bash
python setup_duckdb.py
```

* **Comportamento Inteligente:**
  * Se você veio dos Labs anteriores, o script reaproveita seu arquivo `transactions.parquet`.
  * Se você está em um ambiente zerado, o script gera instantaneamente **1.000 transações financeiras sintéticas** completas no banco `data/analytics.duckdb`.

*Saída Esperada:*
```text
Base analytics.duckdb inicializada com 1000 transacoes.
Setup concluido com sucesso!
```

---

### Passo 4: Verificação da Conexão do dbt com DuckDB

Antes de compilar os modelos, valide se o dbt consegue se conectar ao DuckDB utilizando a configuração local:

```bash
dbt debug --profiles-dir .
```

*Saída Esperada:*
* Todas as checagens com status `OK` (Python, profiles.yml, dbt_project.yml e Connection test).
* Mensagem final: `All checks passed!`

---

### Passo 5: Inspeção e Execução da Camada de Staging

A camada de Staging é responsável por padronizar nomes, realizar casts de tipos e isolar os modelos analíticos das peculiaridades das fontes brutas.

1. Inspecione o modelo [`models/staging/stg_transactions.sql`](models/staging/stg_transactions.sql):
   * Note o uso de `{{ source('raw_sources', 'transactions') }}`.
   * Todos os campos são tipados explicitamente (`varchar`, `double`, `timestamp`).

2. Execute a materialização da camada de staging:

```bash
dbt run --select staging --profiles-dir .
```

*Saída Esperada:*
```text
1 of 1 START sql view model main.stg_transactions .............................. [RUN]
1 of 1 OK created sql view model main.stg_transactions ......................... [OK in 0.08s]
Finished running 1 view model in 0.15s.
Completed successfully
Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1
```

---

### Passo 6: O Coração do Lab — Model Contracts Enforced

Agora examinaremos o mart analítico [`models/marts/fct_financial_transactions.sql`](models/marts/fct_financial_transactions.sql) e sua especificação formal em [`models/marts/schema.yml`](models/marts/schema.yml).

Observe o bloco no `schema.yml`:

```yaml
models:
  - name: fct_financial_transactions
    description: "Mart analítico de transações financeiras liquidadas (Data Product de Consumo)."
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
> **Por que isso é revolucionário?**  
> Quando `contract: {enforced: true}` está ativo:
> 1. O dbt **rejeita** a criação da tabela se o SQL retornar qualquer coluna não declarada explicitamente no YAML.
> 2. O dbt **rejeita** o modelo se o tipo de dados retornado divergir do `data_type` contratado.
> 3. O dbt aplica DDL constraints (como `NOT NULL`) diretamente no banco de dados.

Execute o modelo com o contrato ativado:

```bash
dbt run --select marts --profiles-dir .
```

*Saída Esperada:*
```text
1 of 1 START sql table model main.fct_financial_transactions ................... [RUN]
1 of 1 OK created sql table model main.fct_financial_transactions .............. [OK in 0.12s]
Finished running 1 table model in 0.20s.
Completed successfully
Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1
```

---

### Passo 7: Inspeção do Produto de Dados via Python

Inspecione os dados liquidados no banco de dados usando o utilitário Python:

```bash
python query_mart.py
```

*Saída Esperada:*
* Lista das tabelas presentes (`stg_transactions`, `fct_financial_transactions`, `transactions`).
* Total de transações com status `COMPLETED`.
* Total do volume bruto transacionado e taxas retidas calculadas.
* Amostra formatada das primeiras 5 linhas.

---

### Passo 8: Simulação de Incidente de Quebra de Contrato (*Breaking Change*)

Como líder ou engenheiro de dados, você deve provar que o contrato realmente protege os consumidores contra alterações acidentais de desenvolvedores.

Vamos simular uma alteração no código SQL do Mart introduzindo uma coluna extra não documentada.

1. Abra o arquivo [`models/marts/fct_financial_transactions.sql`](models/marts/fct_financial_transactions.sql).
2. Adicione temporariamente uma coluna extra na consulta final, por exemplo:
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
       'MARKETING_TAG' as extra_uncontracted_column  -- << COLUNA NÃO CONTRATADA
   from transactions
   where status = 'COMPLETED'
   ```
3. Salve o arquivo e tente executar novamente o dbt:

```bash
dbt run --select marts --profiles-dir .
```

*Resultado Esperado (Falha Defensiva do Contrato):*
```text
Compilation Error in model fct_financial_transactions (models/marts/fct_financial_transactions.sql)
This model has an enforced contract that was violated:
  - Additional column 'extra_uncontracted_column' found in SQL model, but not in contract.
```

> [!TIP]
> **Conclusão:** O dbt impediu a compilação e bloqueou a materialização! O contrato protegeu a tabela contra alteração de schema surpresa sem versionamento.

4. **Reversão:** Remova a linha `'MARKETING_TAG' as extra_uncontracted_column` e a vírgula anterior no arquivo [`models/marts/fct_financial_transactions.sql`](models/marts/fct_financial_transactions.sql), salve e reexecute para restaurar o estado verde:

```bash
dbt run --select marts --profiles-dir .
```

---

## 🧪 Validação & Critérios de Aceite

Para garantir que o seu laboratório está 100% concluído com sucesso:

1. **Compilação do Projeto Completo:**
   ```bash
   dbt run --profiles-dir .
   ```
   Deve exibir `PASS=2 WARN=0 ERROR=0 SKIP=0 TOTAL=2`.

2. **Inspeção de Dados:**
   ```bash
   python query_mart.py
   ```
   Deve exibir os dados da tabela `fct_financial_transactions` com sucesso.

---

## 🧹 Cleanup

Após concluir todas as validações, retorne ao diretório raiz de laboratórios:

```bash
cd ..
```

---

## 💡 Desafios Complementares (Para Praticar)

1. **Enforcement em Camada de Staging:** Aplique um `contract: {enforced: true}` também na visão `stg_transactions` e observe se visões aceitam constraints no DuckDB.
2. **Alteração de Tipo Incompatível:** Tente alterar intencionalmente no `schema.yml` o tipo da coluna `amount` de `double` para `varchar` e observe a mensagem de erro do compilador dbt.
3. **Constraint Adicional:** Adicione a constraint `not_null` na coluna `amount` e valide a compilação com `dbt run`.
