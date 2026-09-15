# Lab 05 - Data Quality Gates na Borda com Soda Core (SodaCL)

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** Soda Core / SodaCL / DuckDB / Python 3.11+  
**Duração Estimada:** 30 a 35 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é implementar uma camada industrial de **Quality Gates declarativos na ingestão de dados (*Data Ingestion Quality Gates*)**, utilizando o framework open source **Soda Core** e sua linguagem declarativa **SodaCL (Soda Check Language)**.

Ao final deste laboratório, você será capaz de:
* Configurar fontes de dados no Soda Core conectadas ao motor analítico DuckDB (`configuration.yml`).
* Redigir suítes completas de regras declarativas de dados com SodaCL (`checks.yml`), cobrindo integridade estrutural, faixas numéricas de domínio, valores categóricos válidos e frescor temporal.
* Executar varreduras automatizadas de qualidade via CLI (`soda scan`).
* Compreender e simular o funcionamento de um **Circuit Breaker** de dados em produção corporativa, bloqueando a ingestão de registros anômalos antes que poluam os Data Marts ou Dashboards executivos.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 00 a 04** (ou início a partir de um ambiente novo/zerado).
* Dependências da Aula 03 (`duckdb>=1.1.0`, `soda-core-duckdb>=3.0.0`).
* Arquivos fornecidos neste laboratório:
  * [`requirements.txt`](requirements.txt): Dependências de runtime do lab.
  * [`setup_duckdb.py`](setup_duckdb.py): Inicializador autônomo com transações e clientes.
  * [`configuration.yml`](configuration.yml): Configuração de conexão do Soda Core com DuckDB.
  * [`checks.yml`](checks.yml): Arquivo de regras declarativas SodaCL.
  * [`inject_anomaly.py`](inject_anomaly.py): Script de simulação de incidente com injeção de dados corrompidos.
  * [`restore_data.py`](restore_data.py): Script de restauração para o estado canônico limpo.

> [!TIP]
> **🚀 Começando de um Ambiente Limpo (Zero Friction):**  
> Caso esteja iniciando este lab em um novo Codespace, o script `setup_duckdb.py` é 100% autossuficiente (*Self-Healing*). Ele gera e valida todos os dados em menos de 10 segundos.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado do Codespaces (`Ctrl + ~`), navegue até a pasta do laboratório:

```bash
cd lab05-soda-quality
```

> [!NOTE]
> Todos os comandos deste laboratório devem ser executados a partir de `lab05-soda-quality`.

---

### Passo 2: Instalação das Dependências

Instale os pacotes específicos da Aula 03 (Soda Core com conector DuckDB):

```bash
pip install -r requirements.txt
```

> [!IMPORTANT]
> **Compatibilidade no Codespaces (Python 3.14+):**  
> Caso o seu Codespaces esteja rodando Python 3.14 e apresente erro no `protobuf` ou `distutils` ao executar o Soda, execute o comando abaixo para aplicar a correção de compatibilidade:
> ```bash
> python -c "import pathlib, site; p = pathlib.Path(site.getsitepackages()[0]) / 'google/protobuf/internal/api_implementation.py'; p.write_text(p.read_text().replace('except ImportError:', 'except (ImportError, TypeError):')); print('Protobuf corrigido com sucesso')"
> ```
> *(Ou alternativamente execute: `python fix_protobuf_python314.py`)*

---

### Passo 3: Inicialização da Base DuckDB

Execute o script de setup para criar o banco `data/analytics.duckdb` com as tabelas canônicas `transactions` e `customers`:

```bash
python setup_duckdb.py
```

**Saída esperada:**
```text
Tabela transactions inicializada com 1000 registros.
Tabela customers criada com 100 clientes cadastrados.
[OK] Setup da base analytics.duckdb concluido com sucesso!
```

---

### Passo 4: Inspeção da Configuração do Soda Core (`configuration.yml`)

Abra o arquivo [`configuration.yml`](configuration.yml). Ele define para o Soda Core como se conectar ao DuckDB:

```yaml
data_source analytics:
  type: duckdb
  path: data/analytics.duckdb
```

Essa declaração nomeia a fonte de dados como `analytics`, que será referenciada no comando de scan pela flag `-d analytics`.

---

### Passo 5: Inspeção das Regras Declarativas SodaCL (`checks.yml`)

Abra o arquivo [`checks.yml`](checks.yml). O SodaCL permite expressar regras semânticas de alta legibilidade corporativa:

```yaml
checks for transactions:
  # 1. Integridade Estrutural & Volumetria
  - row_count > 0
  - missing_count(transaction_id) = 0
  - duplicate_count(transaction_id) = 0

  # 2. Regras de Domínio Financeiro & Limites
  - min(amount) > 0
  - max(amount) <= 10000
  - missing_count(amount) = 0

  # 3. Categorias e Valores Aceitos
  - invalid_count(status) = 0:
      valid values: ['COMPLETED', 'FAILED', 'PENDING']

  - invalid_count(payment_method) = 0:
      valid values: ['PIX', 'CREDIT_CARD', 'BOLETO']

  - invalid_count(currency) = 0:
      valid values: ['BRL', 'USD', 'EUR']

  # 4. Integridade Temporal
  - missing_count(created_at) = 0
```

---

### Passo 6: Execução do Scan Inicial de Confiabilidade

Execute a auditoria do Soda Core no terminal:

```bash
soda scan -d analytics -c configuration.yml checks.yml
```

**Saída esperada:**
```text
Soda Core 3.x.x
Scan summary:
All checks passed!
All [X] checks passed! No failures, no warnings.
```

O código de retorno do processo no terminal é `0` (`exit code 0`), indicando que o Quality Gate está **aberto para liberação dos dados**.

---

### Passo 7: Simulação de Incidente Corporativo (Circuit Breaker)

Agora vamos simular um incidente clássico de produção: uma mutação silenciosa na origem injeta transações com valores negativos, IDs nulos e status corrompidos:

```bash
python inject_anomaly.py
```

Em seguida, execute novamente o scan do Soda Core:

```bash
soda scan -d analytics -c configuration.yml checks.yml
```

**Comportamento esperado do Circuit Breaker:**
* O Soda identificará violações em múltiplos checks:
  * `missing_count(transaction_id) = 0` $\rightarrow$ **FAIL** (encontrou valores nulos).
  * `min(amount) > 0` $\rightarrow$ **FAIL** (encontrou valor negativo `-999.50`).
  * `invalid_count(status) = 0` $\rightarrow$ **FAIL** (encontrou `CORRUPTED_STATUS`).
* O comando encerra com **exit code diferente de 0** (`exit code 2` ou `3`), interrompendo imediatamente esteiras de orquestração (ex: Airflow, GitHub Actions).

---

### Passo 8: Restauração do Estado Canônico

Para retornar a base ao estado saudável, execute o script de restauração:

```bash
python restore_data.py
```

E valide que a esteira voltou a ficar verde:

```bash
soda scan -d analytics -c configuration.yml checks.yml
```

---

## 🧪 Validação & Critérios de Aceite

Para considerar o Lab 05 concluído com êxito:
1. O arquivo `configuration.yml` deve conectar corretamente no DuckDB local.
2. O scan inicial em dados canônicos deve apresentar **100% de aprovação** (*All checks passed*).
3. A execução após `python inject_anomaly.py` deve **bloquear a esteira** com detecção explícita das violações de contrato e regras de domínio.
4. A restauração com `python restore_data.py` deve normalizar o resultado para aprovação total.

---

## 🧹 Cleanup

Após concluir as validações, retorne para o diretório raiz dos laboratórios:

```bash
cd ..
```

---

## 💡 Desafios Complementares

1. **Checagem de Anomalia Volumétrica:** Adicione no `checks.yml` uma validação de linha que garanta que a contagem total de transações esteja estritamente entre `900` e `1100` (`row_count between 900 and 1100`).
2. **Checagem Relacional com Customers:** Adicione uma regra no `checks.yml` validando que todo `customer_id` existente na tabela `transactions` obrigatoriamente exista na tabela `customers` (integridade de chave estrangeira).
