# Lab 06 - Rastreabilidade & Linhagem com OpenLineage + Marquez

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Docker + Python 3.11+)  
**Linguagem / Stack:** OpenLineage SDK / Marquez / DuckDB / Docker Compose  
**Duração Estimada:** 30 a 35 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é instrumentar a **rastreabilidade e observabilidade de ponta a ponta (*End-to-End Lineage*)** de um Produto de Dados analítico utilizando a especificação aberta **OpenLineage** (Linux Foundation) e a interface visual de referência **Marquez**.

Ao final deste laboratório, você será capaz de:
* Compreender a arquitetura canônica de metadados operacionais do OpenLineage: a tríade **Job**, **Dataset** e **Run**, além de metadados modulares (**Facets**).
* Configurar transportes no OpenLineage SDK via arquivo padronizado [`openlineage.yml`](openlineage.yml).
* Instrumentar pipelines de dados em Python utilizando o SDK oficial (`openlineage-python`) com classes tipadas.
* Executar o Marquez Server localmente via Docker Compose e visualizar o grafo DAG interativo de linhagem.
* Inspecionar **Schema Facets** e **Quality Facets** emitidos em runtime.
* Realizar **Análise de Impacto Downstream (*Impact Analysis*)** para mensurar o *Blast Radius* de breaking changes corporativas.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 00 a 05** (ou início a partir de um ambiente novo/zerado).
* Dependências da Aula 03 (`duckdb>=1.1.0`, `openlineage-python>=1.0.0`).
* Arquivos fornecidos neste laboratório:
  * [`requirements.txt`](requirements.txt): Dependências mínimas de runtime Python.
  * [`docker-compose.yml`](docker-compose.yml): Orquestração enxuta do Marquez (PostgreSQL Alpine + Marquez API + Marquez Web UI).
  * [`openlineage.yml`](openlineage.yml): Configuração de transporte do SDK OpenLineage para o Marquez.
  * [`setup_duckdb.py`](setup_duckdb.py): Inicializador autônomo com tabelas de staging, dimensões e marts.
  * [`emit_lineage_events.py`](emit_lineage_events.py): Script de instrumentação oficial com `openlineage-python`.
  * [`inspect_lineage.py`](inspect_lineage.py): Inspecionador CLI do catálogo de metadados e visualizador de grafo textual.
  * [`simulate_impact_analysis.py`](simulate_impact_analysis.py): Simulador de análise de impacto e cálculo de Blast Radius.

> [!TIP]
> **🚀 Começando de um Ambiente Limpo (Zero Friction):**  
> O script `setup_duckdb.py` é 100% autossuficiente (*Self-Healing*). Ele gera o catálogo de dados completo em poucos segundos.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado do Codespaces (`Ctrl + ~`), entre no diretório do Lab 06:

```bash
cd lab06-openlineage
```

> [!NOTE]
> Todos os comandos deste laboratório devem ser executados a partir de `lab06-openlineage`.

---

### Passo 2: Instalação das Dependências Python

Instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

---

### Passo 3: Inicialização da Base Analítica DuckDB

Execute o script de setup para criar a cadeia completa de tabelas analíticas no DuckDB (`data/analytics.duckdb`):

```bash
python setup_duckdb.py
```

**Saída esperada:**
```text
[OK] Pipeline analitico completo preparado: transactions (1000) -> fct_financial_transactions (1000).
```

---

### Passo 4: Inicialização do Marquez Server (Docker Compose)

O **Marquez** é a implementação de referência mantida pela Linux Foundation para coletar, agregar e visualizar eventos OpenLineage.

Inicie os containers do Marquez em segundo plano:

```bash
docker compose up -d
```

> [!NOTE]
> **Arquitetura Enxuta:** O arquivo `docker-compose.yml` deste lab foi customizado para máxima eficiência no Codespaces: utiliza PostgreSQL Alpine e desativa motores de busca pesados (`SEARCH_ENABLED=false`), consumindo pouca memória RAM e subindo em cerca de 45 a 60 segundos.

Aguarde cerca de 30 a 45 segundos para que as migrações do banco sejam concluídas e verifique se os containers estão saudáveis:

```bash
docker compose ps
```

**Saída esperada:**
Os serviços `marquez-db`, `marquez-api` e `marquez-web` devem constar com status `running` / `Up`.

---

### Passo 5: Inspeção da Configuração do SDK OpenLineage (`openlineage.yml`)

Abra o arquivo [`openlineage.yml`](openlineage.yml). No ecossistema OpenLineage, o código do pipeline de dados é desacoplado do destino dos metadados através de **Transportes**:

```yaml
transport:
  type: http
  url: http://localhost:5000
  endpoint: api/v1/lineage
```

Essa configuração instrui o SDK a enviar cada evento de linhagem via HTTP POST diretamente para a API do Marquez (`porta 5000`).

---

### Passo 6: Emissão de Eventos com o SDK Oficial (`openlineage-python`)

Abra o arquivo [`emit_lineage_events.py`](emit_lineage_events.py). Observe que ele utiliza as classes oficiais do SDK:
* `OpenLineageClient`: cliente gerenciador de transporte.
* `Job` e `Run`: representação da tarefa analítica e da execução pontual.
* `InputDataset` e `OutputDataset`: datasets consumidos e gerados.
* `SchemaDatasetFacet` e `SchemaField`: facets que capturam a estrutura real de colunas do DuckDB.
* `DataQualityMetricsInputDatasetFacet`: facet que acopla as métricas de qualidade (volumetria e integridade).

Execute a emissão dos eventos no terminal:

```bash
python emit_lineage_events.py
```

**Saída esperada:**
```text
======================================================================
📡 INSTRUMENTAÇÃO DE LINHAGEM COM OPENLINEAGE PYTHON SDK
======================================================================

[*] Inspecionando catálogo de tabelas analíticas no DuckDB...
  ├─ Tabela raw/transactions: 8 colunas
  ├─ Tabela staging/stg_transactions: 8 colunas
  ├─ Dimensão/dim_customers: 6 colunas
  └─ Data Mart/fct_financial_transactions: 10 colunas (1000 registros)

[*] Inicializando OpenLineageClient...
  └─ [OK] Cliente configurado via openlineage.yml (Target: http://localhost:5000)

[Step 1] Emitindo eventos de linhagem para 'job_ingestion_raw_to_staging'...
  🚀 [EMIT -> MARQUEZ] Job='job_ingestion_raw_to_staging' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_ingestion_raw_to_staging' | RunState=COMPLETE

[Step 2] Emitindo eventos de linhagem para 'dbt_build_marts_financial'...
  🚀 [EMIT -> MARQUEZ] Job='dbt_build_marts_financial' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='dbt_build_marts_financial' | RunState=COMPLETE

[Step 3] Emitindo eventos para consumidores downstream do Data Mart...
  🚀 [EMIT -> MARQUEZ] Job='job_bi_executive_dashboard' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_bi_executive_dashboard' | RunState=COMPLETE
  🚀 [EMIT -> MARQUEZ] Job='job_ml_fraud_feature_store' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_ml_fraud_feature_store' | RunState=COMPLETE
  🚀 [EMIT -> MARQUEZ] Job='job_bacen_regulatory_export' | RunState=START
  🚀 [EMIT -> MARQUEZ] Job='job_bacen_regulatory_export' | RunState=COMPLETE

======================================================================
✅ SUCESSO: 10 eventos OpenLineage processados e salvos em 'lineage_events.json'.
🌐 Metadados sincronizados ao vivo no Marquez!
   Acesse a UI web em: http://localhost:3000 (Namespace: fiap.mba.dpm)
======================================================================
```

> [!TIP]
> **Modo Offline:** Caso o Marquez não esteja rodando, o script detecta a indisponibilidade, emite um aviso amigável e salva os eventos serializados com `Serde` oficial em `lineage_events.json`, garantindo que os passos seguintes funcionem sem bloqueio.

---

### Passo 7: Exploração Visual no Marquez UI (Porta 3000)

1. No Codespaces, clique na aba lateral **PORTS** (ao lado de Terminal) e localize a porta **3000**.
2. Clique no ícone de globo (*Open in Browser*) ou acesse `http://localhost:3000` se estiver rodando localmente.

> [!IMPORTANT]
> **Resolução do HTTP ERROR 401 no Codespaces:**  
> Por padrão, as portas no Codespaces têm visibilidade *Private*. Se o seu navegador exibir `HTTP ERROR 401`:
> * Na aba **PORTS**, clique com o **botão direito** na linha da porta **3000** $\rightarrow$ **Port Visibility** $\rightarrow$ mude para **Public**.
> * *Ou alternativamente:* abra internamente pelo VS Code pressionando `Ctrl + Shift + P` $\rightarrow$ digite `Simple Browser: Show` $\rightarrow$ informe `http://localhost:3000`.

3. Na barra superior do Marquez, selecione o Namespace: **`fiap.mba.dpm`**.
4. **Navegue no Grafo DAG:**
   * Observe o fluxo end-to-end desenhado automaticamente:  
     `transactions.parquet` $\rightarrow$ `job_ingestion_raw_to_staging` $\rightarrow$ `stg_transactions` + `dim_customers` $\rightarrow$ `dbt_build_marts_financial` $\rightarrow$ `fct_financial_transactions`.
5. **Inspecione os Facets:**
   * Clique no nó do dataset `fct_financial_transactions`.
   * Na aba lateral, veja o **Schema** com todos os tipos de dados sincronizados do catálogo.
   * Inspecione o facet **Data Quality Metrics** com a contagem de registros (1.000 linhas).

---

### Passo 8: Inspeção no Terminal & Análise de Impacto Downstream (Blast Radius)

Além da interface web, metadados de linhagem são frequentemente consumidos programaticamente em pipelines de CI/CD para auditoria e prevenção de quebras.

1. Inspecione o catálogo via terminal:
   ```bash
   python inspect_lineage.py
   ```

2. Execute a simulação de análise de impacto corporativo:
   ```bash
   python simulate_impact_analysis.py
   ```

**Saída esperada:**
O script percorre as arestas do grafo e identifica que uma alteração em `transactions.parquet` quebrará em cascata a camada Staging, o Data Mart final e 3 nós consumidores downstream (Dashboard Executivo, Feature Store de ML e Relatório Regulatório do BACEN).

---

### Passo 9: Encerramento do Marquez

Ao finalizar o laboratório, libere os recursos de memória parando os containers:

```bash
docker compose down
```

---

## 🧪 Validação & Critérios de Aceite

Para considerar o Lab 06 concluído com êxito:
1. Os containers do Marquez devem subir e responder na porta `3000` e `5000`.
2. O script `emit_lineage_events.py` deve utilizar o SDK oficial `openlineage-python` e registrar eventos no Marquez e em `lineage_events.json`.
3. O grafo de linhagem ponta a ponta deve ser visualizado na interface web do Marquez e via `inspect_lineage.py`.
4. O relatório de Blast Radius deve mapear os consumidores downstream que dependem do Data Product.

---

## 🧹 Cleanup

Retorne para a raiz dos laboratórios:

```bash
cd ..
```

---

## 💡 Desafios Complementares

1. **Adicionar OwnershipJobFacet usando o SDK:** Modifique o `emit_lineage_events.py` utilizando as classes `OwnershipJobFacet` e `OwnershipJobFacetOwners` do SDK para atribuir o squad dono do pipeline (`Data Platform & Governance Squad`).
2. **Simular Falha de Job (RunState.FAIL):** Crie um novo evento simulando que o job analítico falhou devido a violação de contrato e observe a mudança de cor do nó no Marquez UI de verde para vermelho.
