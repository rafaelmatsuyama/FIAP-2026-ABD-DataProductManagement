# Lab 06 - Rastreabilidade & Linhagem com OpenLineage + Marquez

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** OpenLineage / Marquez / DuckDB / Python 3.11+  
**Duração Estimada:** 25 a 30 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é instrumentar a **rastreabilidade e observabilidade de ponta a ponta (*End-to-End Lineage*)** do nosso Produto de Dados utilizando a especificação aberta **OpenLineage** (mantida pela Linux Foundation).

Ao final deste laboratório, você será capaz de:
* Compreender a arquitetura canônica de metadados operacionais do OpenLineage: a tríade **Job**, **Dataset** e **Run**, além de extensões modulares (**Facets**).
* Emitir eventos padronizados de linhagem operacional cobrindo a ingestão bruta, transformação analítica e publicação de Data Marts.
* Inspecionar e auditar a árvore de linhagem (*DAG*) do Data Product.
* Realizar **Análise de Impacto (*Impact Analysis*)** para mensurar o *Blast Radius* de breaking changes antes que atinjam o consumo corporativo.
* Compreender como a linhagem operacional viabiliza a rápida **Auditoria de Causa-Raiz (*Root Cause Analysis*)** diante de anomalias em produção.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 00 a 05** (ou início a partir de um ambiente novo/zerado).
* Dependências da Aula 03 (`duckdb>=1.1.0`, `openlineage-python>=1.0.0`).
* Arquivos fornecidos neste laboratório:
  * [`requirements.txt`](requirements.txt): Dependências mínimas de runtime.
  * [`setup_duckdb.py`](setup_duckdb.py): Inicializador autônomo com tabelas de staging, dimensões e marts.
  * [`emit_lineage_events.py`](emit_lineage_events.py): Script de instrumentação e emissão de eventos OpenLineage.
  * [`inspect_lineage.py`](inspect_lineage.py): Inspecionador do catálogo de metadados e visualizador de grafo.
  * [`simulate_impact_analysis.py`](simulate_impact_analysis.py): Simulador de análise de impacto downstream.

> [!TIP]
> **🚀 Começando de um Ambiente Limpo (Zero Friction):**  
> Caso esteja iniciando este lab em um novo Codespace, o script `setup_duckdb.py` é 100% autossuficiente (*Self-Healing*).

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

### Passo 2: Instalação das Dependências

Instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

---

### Passo 3: Inicialização da Base Analítica e Camadas

Execute o script de setup para criar a cadeia completa de tabelas analíticas no DuckDB:

```bash
python setup_duckdb.py
```

**Saída esperada:**
```text
[OK] Pipeline analitico completo preparado: transactions (1000) -> fct_financial_transactions (1000).
```

---

### Passo 4: Emissão de Eventos OpenLineage

Abra o arquivo [`emit_lineage_events.py`](emit_lineage_events.py) para inspecionar como os eventos são construídos. O script captura:
1. **Job de Ingestão:** Entrada `transactions.parquet` $\rightarrow$ Saída `stg_transactions`.
2. **Job de Modelagem dbt:** Entradas `stg_transactions` + `dim_customers` $\rightarrow$ Saída `fct_financial_transactions`.
3. **Facets:** Injeção do schema de cada tabela e das métricas de qualidade calculadas pelo Soda Core (`dataQualityMetrics`).

Agora, execute a emissão dos eventos no terminal:

```bash
python emit_lineage_events.py
```

**Saída esperada:**
```text
[*] Conectando ao DuckDB para inspecionar schemas e metadados operacionais...
[OK] 4 eventos OpenLineage emitidos com sucesso em 'lineage_events.json'.
```

---

### Passo 5: Inspeção do Grafo de Linhagem e Facets

Execute o script de inspeção para visualizar o catálogo operacional no terminal:

```bash
python inspect_lineage.py
```

Observe como cada nó do pipeline registra suas entradas, saídas e metadados de governança:
* O nó final `fct_financial_transactions` traz acoplado o **Schema Facet** com os tipos de colunas e o **DataQuality Facet** com a volumetria de 1000 linhas auditadas.

---

### Passo 6: Execução de Análise de Impacto Downstream (Blast Radius)

Em cenários corporativos, antes de autorizar qualquer mudança em tabelas upstream, os engenheiros consultam o grafo de linhagem para responder: *"Se alterarmos a origem, o que quebra?"*

Execute a simulação de análise de impacto:

```bash
python simulate_impact_analysis.py
```

**Saída esperada:**
* O script demonstra que uma alteração em `transactions.parquet` quebraria não apenas a camada Staging, mas também o Data Mart `fct_financial_transactions` e 3 consumidores downstream críticos:
  1. Dashboard Executivo de Receita
  2. Feature Store do Modelo de Fraude
  3. Relatório Regulatório do BACEN

Isso evidencia o valor prático de manter a linhagem viva e automatizada no Data Mesh.

---

## 🧪 Validação & Critérios de Aceite

Para considerar o Lab 06 concluído com êxito:
1. O arquivo `lineage_events.json` deve ser gerado contendo a estrutura válida da especificação OpenLineage.
2. A execução do `inspect_lineage.py` deve exibir os 2 jobs operacionais e seus respectivos datasets de entrada e saída.
3. O relatório do `simulate_impact_analysis.py` deve mapear com clareza as dependências downstream em cascata.

---

## 🧹 Cleanup

Após concluir as validações, retorne para a raiz dos laboratórios:

```bash
cd ..
```

---

## 💡 Desafios Complementares

1. **Adicionar Facet de Governança/Owner:** Modifique o `emit_lineage_events.py` para incluir o facet de propriedade (*OwnershipJobFacet*) identificando o time responsável pelo pipeline (ex: `team: Data Platform & Analytics`).
2. **Conexão com Marquez Server (Docker):** Se o seu ambiente suportar Docker, inicie o Marquez (`docker compose up marquez`) e aponte o transporte do OpenLineage para `http://localhost:5000/api/v1` para navegar no grafo interativo pela interface web.
