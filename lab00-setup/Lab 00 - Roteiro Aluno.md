# Lab 00 - Setup Express & Validação de Ambiente

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** Python 3.11+ / DuckDB / datacontract-cli / dbt-duckdb / Soda Core  
**Duração Estimada:** 15 a 20 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório inicial é garantir a **padronização e prontidão técnica** de todo o ambiente de desenvolvimento antes do início dos exercícios práticos de *Data Products*, *Data Contracts* e *Observabilidade*.

Ao final deste laboratório, você será capaz de:
1. Inicializar uma sessão reprodutível no **GitHub Codespaces** ou em ambiente local.
2. Validar a instalação e operabilidade das ferramentas essenciais do curso (`duckdb`, `datacontract-cli`, `dbt-duckdb`, `soda-core`).
3. Executar consultas analíticas OLAP locais via **DuckDB** sobre arquivos colunares Parquet (`transactions.parquet`).
4. Reconhecer a arquitetura de workspaces e diretórios dos próximos laboratórios.

---

## 📋 Pré-requisitos & Materiais

* Acesso à internet e conta ativa no **GitHub** com permissões no repositório da disciplina.
* Navegador moderno (Google Chrome, Firefox ou Microsoft Edge) para operar o Codespaces no browser.
* *(Opcional para execução local)*: Python 3.11 ou superior instalado e gerenciador de pacotes (`uv` ou `pip`).

---

## 🚀 Passo a Passo Guiado

### Passo 1: Inicialização do Ambiente no GitHub Codespaces

1. Acesse a página do repositório oficial da disciplina no GitHub.
2. Clique no botão verde **Code** $\rightarrow$ selecione a aba **Codespaces** $\rightarrow$ clique em **Create codespace on main**.
3. Aguarde o provisionamento do container. O DevContainer já vem pré-configurado com as extensões do VS Code, Python e ferramentas de CLI.

> 💡 **Nota para execução Local:** Se preferir rodar em sua máquina, clone o repositório, crie um ambiente virtual e instale os requisitos:
> ```bash
> python -m venv .venv
> source .venv/bin/activate  # No Windows: .venv\Scripts\activate
> pip install duckdb datacontract-cli dbt-duckdb soda-core
> ```

---

### Passo 2: Navegação e Sanity Check do Stack com `check_env.py`

Abra o terminal integrado (`Ctrl + ~`). Navegue até a pasta deste laboratório e execute o script de validação:

```bash
cd lab00-setup
python check_env.py
```

#### Saída Esperada no Terminal:
```text
=================================================================
  [*] MBA ABD - DPM: VERIFICACAO DE AMBIENTE & DEPENDENCIAS
=================================================================
  [OK] Python Runtime: v3.11+ detectado

--- 1. Bancos & Motores Analiticos ---
  [OK] DuckDB Python Engine: Instalado e importavel.
  [OK] CLI `duckdb` (DuckDB Interactive CLI): Disponivel em /usr/local/bin/duckdb

--- 2. Data Contracts & Modelagem ---
  [OK] datacontract-cli (ODCS Engine): Instalado e importavel.
  [OK] CLI `datacontract` (datacontract CLI): Disponivel em /usr/local/bin/datacontract

--- 3. Analytics Engineering & Transformacao ---
  [OK] dbt-core: Instalado e importavel.
  [OK] dbt-duckdb Adapter: Instalado e importavel.

--- 4. Data Quality & Observabilidade ---
  [OK] Soda Core Engine: Instalado e importavel.

=================================================================
  [OK] AMBIENTE 100% PRONTO PARA OS LABS DA DISCIPLINA!
=================================================================
```

Caso alguma biblioteca apresente aviso de ausência, execute a instalação rápida:
```bash
pip install -r ../requirements.txt
```

---

### Passo 3: Geração e Exploração do Dataset Base (`transactions.parquet`)

Para os laboratórios de contratos de dados e observabilidade, utilizaremos uma base de transações financeiras e pagamentos.

Dentro do diretório `lab00-setup`, execute o script utilitário para gerar a base sintética inicial:

```bash
python generate_sample_data.py
```

O script criará o arquivo `data/transactions.parquet` contendo registros transacionais corporativos com campos de identificação, valores monetários, métodos de pagamento e timestamps.

---

### Passo 4: Consulta Analítica Rápida com DuckDB

Vamos testar o processamento colunar em memória do DuckDB consultando diretamente o arquivo Parquet gerado:

1. Inicie o cliente interativo do DuckDB:
```bash
duckdb
```

2. Execute as seguintes consultas SQL analíticas:
```sql
-- 1. Inspecionar o schema e tipos de dados do arquivo Parquet
DESCRIBE SELECT * FROM 'data/transactions.parquet';

-- 2. Calcular métricas agregadas de transações por método de pagamento
SELECT 
    payment_method,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_amount,
    ROUND(AVG(amount), 2) AS avg_ticket
FROM 'data/transactions.parquet'
GROUP BY payment_method
ORDER BY total_amount DESC;
```

3. Para sair da interface interativa do DuckDB:
```sql
.exit
```

---

## 🧪 Validação & Critérios de Aceite

Para garantir que o seu setup está aprovado e pronto para o **Lab 01**:

1. [x] Script `check_env.py` executou com sucesso a partir de `lab00-setup`.
2. [x] O arquivo `data/transactions.parquet` foi gerado e possui registros consolidados.
3. [x] A query de agregação no DuckDB retornou as métricas de transações por `payment_method`.
4. [x] O comando `datacontract --help` responde com a listagem de comandos do OpenDataContract CLI.

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

1. **Consulta com Filtro Temporal no DuckDB:** Escreva uma query SQL que identifique quais transações ocorreram no último trimestre e filtre valores acima de `R$ 1.000,00`.
2. **Exploração via Python:** Crie um script rápido `test_duckdb.py` utilizando `import duckdb` e imprima o resultado da query em formato de DataFrame Pandas (`duckdb.sql("...").df()`).
