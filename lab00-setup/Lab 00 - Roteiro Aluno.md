# Lab 00 - Setup Express & Validação de Ambiente

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** Python 3.11+ / DuckDB / datacontract-cli / pip  
**Duração Estimada:** 10 a 15 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório inicial é garantir a **padronização e prontidão técnica** de todo o ambiente de desenvolvimento antes do início dos exercícios práticos de *Data Products*, *Data Contracts* e *Observabilidade*.

Ao final deste laboratório, você será capaz de:
1. Inicializar uma sessão reprodutível no **GitHub Codespaces** ou em ambiente local.
2. Instalar o stack da **Aula 01** em segundos utilizando o gerenciador **`pip`**.
3. Validar a instalação e operabilidade das ferramentas essenciais (`duckdb`, `datacontract-cli`, `pyarrow`).
4. Executar consultas analíticas OLAP locais via **DuckDB** sobre arquivos colunares Parquet (`transactions.parquet`).

---

## 📋 Pré-requisitos & Materiais

* Acesso à internet e conta ativa no **GitHub** com permissões no repositório da disciplina.
* Navegador moderno (Google Chrome, Firefox ou Microsoft Edge) para operar o Codespaces no browser.
* *(Opcional para execução local)*: Python 3.11 ou superior instalado e gerenciador de pacotes (`pip`).

---

## 🚀 Passo a Passo Guiado

### Passo 1: Inicialização do Ambiente no GitHub Codespaces

1. Acesse a página do repositório oficial da disciplina no GitHub.
2. Clique no botão verde **Code** $\rightarrow$ selecione a aba **Codespaces** $\rightarrow$ clique em **Create codespace on main**.
3. Aguarde o provisionamento do container. O DevContainer já vem pré-configurado com as extensões do VS Code, Python e ferramentas de CLI.

> 💡 **Nota para execução Local:** Se preferir rodar em sua máquina, clone o repositório, crie um ambiente virtual e instale os requisitos:
> ```bash
> # Criar ambiente virtual
> python -m venv .venv
> source .venv/bin/activate  # No Windows: .venv\Scripts\activate
> ```

---

### Passo 2: Navegação e Instalação do Stack

Abra o terminal integrado (`Ctrl + ~`). A pasta raiz do terminal é `labs`.

1. Navegue para a pasta deste laboratório:
```bash
cd lab00-setup
```

2. Instale as dependências da **Aula 01** (~5 a 10 segundos):
```bash
pip install -r ../requirements.txt
```

3. Execute o script de validação de ambiente:
```bash
python check_env.py
```

#### Saída Esperada no Terminal:
```text
=================================================================
  [*] MBA ABD - DPM: VERIFICACAO DE AMBIENTE & DEPENDENCIAS
=================================================================
  [OK] Python Runtime: v3.11+ detectado

--- 1. Ferramentas Essenciais (Aula 01: Data Products & Contracts) ---
  [OK] DuckDB Python Engine: Instalado e importavel.
  [OK] datacontract-cli (ODCS Engine): Instalado e importavel.
  [OK] Pandas DataFrame: Instalado e importavel.
  [OK] Apache Arrow (Parquet Engine): Instalado e importavel.

--- 2. Ferramentas das Proximas Aulas (Aulas 02 e 03) ---
  [AVISO] dbt-core (Aula 02): Nao encontrado via Python import.
  [AVISO] dbt-duckdb Adapter (Aula 02): Nao encontrado via Python import.
  [AVISO] Soda Core Engine (Aula 03): Nao encontrado via Python import.

=================================================================
  [OK] AMBIENTE 100% PRONTO PARA OS LABS DA AULA 01!
  (As ferramentas das Aulas 02 e 03 serao adicionadas nas proximas sessoes)
=================================================================
```

---

### Passo 3: Geração do Dataset Base (`transactions.parquet`)

Para os laboratórios de contratos de dados e observabilidade, utilizaremos uma base de transações financeiras e pagamentos corporativos.

Dentro do diretório `lab00-setup`, execute o gerador de dados sintéticos:

```bash
python generate_sample_data.py
```

O script criará o arquivo `data/transactions.parquet` contendo 2.500 registros transacionais com campos de identificação, valores monetários, métodos de pagamento e timestamps.

---

### Passo 4: Consulta Analítica com DuckDB

Vamos testar o processamento colunar em memória do DuckDB consultando diretamente o arquivo Parquet gerado através do script utilitário `query_data.py`:

1. Execute a consulta analítica:
```bash
python query_data.py
```

#### Saída Esperada no Terminal:
```text
=================================================================
  🦆 CONSULTA ANALITICA VIA DUCKDB (EM-MEMORIA)
=================================================================

--- 1. Inspecao de Schema & Tipos (DESCRIBE) ---
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

--- 2. Metricas Agregadas por Metodo de Pagamento ---
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
  [OK] Processamento analitico DuckDB executado com sucesso!
=================================================================
```

2. *(Opcional)* Você também pode rodar consultas SQL rápidas direto da linha de comando via Python:
```bash
python -c "import duckdb; duckdb.sql(\"SELECT payment_method, COUNT(*) AS total FROM 'data/transactions.parquet' GROUP BY payment_method\").show()"
```

---

## 🧪 Validação & Critérios de Aceite

Para garantir que o seu setup está aprovado e pronto para o **Lab 01**:

1. [x] Dependências da Aula 01 instaladas com sucesso (`duckdb`, `datacontract-cli`, `pandas`, `pyarrow`).
2. [x] Script `check_env.py` executou com status `[OK] AMBIENTE 100% PRONTO PARA OS LABS DA AULA 01!`.
3. [x] O arquivo `data/transactions.parquet` foi gerado com sucesso.
4. [x] O script `query_data.py` exibiu o schema e a agregação por método de pagamento.

---

## 🧹 Cleanup

Como o DuckDB executou consultas diretamente sobre o arquivo Parquet em memória (*in-process*), nenhum serviço residente em background ficou em execução.

Para limpar arquivos temporários se necessário:
```bash
rm -f *.tmp *.log dev.duckdb
```

Para retornar à pasta raiz `labs`:
```bash
cd ..
```

---

## 💡 Desafios Complementares (Para Praticar)

1. **Consulta com Filtro Temporal no DuckDB:** Edite o script `query_data.py` e adicione uma query SQL que identifique quais transações ocorreram com status `FAILED` e valor acima de `R$ 1.000,00`.
2. **Exportação de Relatório:** Utilize o comando `COPY (...) TO 'data/report.csv' (HEADER, DELIMITER ',')` no DuckDB para gerar um relatório CSV sumarizado a partir do Parquet.
