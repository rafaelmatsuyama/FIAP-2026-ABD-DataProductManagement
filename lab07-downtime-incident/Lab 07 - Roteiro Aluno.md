# Lab 07 - Data SRE: Telemetria Operacional, Auditoria de SLOs e Error Budget com Marquez API

**Curso / Disciplina:** MBA em Engenharia de Dados (ABD) — Data Product Management & Value Delivery (DPM)  
**Ambiente:** GitHub Codespaces (Linux DevContainer) ou Local (Python 3.11+)  
**Linguagem / Stack:** Python 3.11+ / OpenLineage SDK / Marquez REST API / SRE Metrics  
**Duração Estimada:** 20 a 25 minutos  

---

## 🎯 Objetivo do Lab

O objetivo deste laboratório é atuar como **Data Reliability Engineer (Data SRE) & Data Product Lead**, conectando a observabilidade de dados à tomada de decisão executiva. Você utilizará a **API REST do Marquez** para coletar a telemetria real de execuções de pipelines, calcular **SLIs de Disponibilidade**, medir metricamente o **Data Downtime** (MTTD e MTTR), auditar o consumo de **Error Budget** e acionar políticas automáticas de governança (**Deploy Freeze** vs **Inovação**).

Ao final deste laboratório, você será capaz de:
* Injetar eventos de telemetria operacional com estados de sucesso (`COMPLETED`) e quebra (`FAILED`) usando o **OpenLineage SDK**.
* Visualizar o histórico de execuções com badges de saúde diretamente no **Marquez UI**.
* Consumir programaticamente a **API REST do Marquez** (`/api/v1/namespaces/.../runs`) para auditar a confiabilidade do Data Product.
* Calcular metricamente o **Data Downtime** real corporativo através da soma de **MTTD (Mean Time to Detect)** e **MTTR (Mean Time to Resolve)**.
* Avaliar o cumprimento do **SLO contratual (99.0%)** e automatizar a ativação de um **Deploy Freeze** quando o Error Budget é esgotado.
* Quantificar em moeda corrente ($ / R$) o prejuízo prevenido e provar o **ROI financeiro** de plataformas de observabilidade para o C-Level.

---

## 📋 Pré-requisitos & Materiais

* Conclusão dos **Labs 05 e 06** (Marquez Server rodando na porta 5000 e Web UI na porta 3000).
* Python 3.11+ e pacotes `requests` e `openlineage-python`.
* Arquivos fornecidos neste laboratório:
  * [`requirements.txt`](requirements.txt): Dependências Python do laboratório.
  * [`openlineage.yml`](openlineage.yml): Configuração de transporte do OpenLineage SDK para a porta 5000.
  * [`simulate_pipeline_incidents.py`](simulate_pipeline_incidents.py): Injetor de telemetria operacional e incidentes reais no Marquez.
  * [`audit_downtime_slo.py`](audit_downtime_slo.py): Motor de auditoria de SRE que consome a API REST do Marquez.

---

## 🚀 Passo a Passo Guiado

### Passo 1: Navegação para a Pasta do Lab

No terminal integrado do Codespaces (`Ctrl + ~`), entre no diretório do Lab 07:

```bash
cd lab07-downtime-incident
```

> [!NOTE]
> Todos os comandos deste laboratório devem ser executados a partir de `lab07-downtime-incident`.

---

### Passo 2: Instalação das Dependências

Instale os pacotes requeridos:

```bash
pip install -r requirements.txt
```

---

### Passo 3: Injeção de Telemetria Operacional & Incidentes no Marquez

O ecossistema analítico corporativo opera em ciclos contínuos (horários/diários). Vamos utilizar o **OpenLineage SDK** para emitir uma série histórica de 6 execuções do job `dbt_build_marts_financial` no Marquez, simulando um ciclo operacional de 24 horas contendo execuções regulares e um incidente grave de violação de contrato de dados:

Execute o injetor de telemetria:

```bash
python simulate_pipeline_incidents.py
```

**Saída esperada:**
```text
================================================================================
🚨 INJETOR DE TELEMETRIA OPERACIONAL & INCIDENTES DE DADOS (OPENLINEAGE)
================================================================================
[*] Conectando ao Marquez Server via OpenLineageClient (http://localhost:5000)...

[*] Emitindo histórico de 6 execuções para o Job: [fiap.mba.dpm:dbt_build_marts_financial]...

  ├─ Run 1a2b3c4d... | ✅ COMPLETED | Execução Regular Noturna (Batch D-1)
  ├─ Run 2b3c4d5e... | ✅ COMPLETED | Execução Regular Matutina (Consolidação 06:00)
  ├─ Run 3c4d5e6f... | ❌ FAILED    | INCIDENTE #1: Violação de Data Contract (18.4% nulls em 'customer_id')
  │  └─ 💥 Causa Raiz: DataContractException: Check 'customer_id_not_null' failed on upstream staging. Null rate=18.4%.
  ├─ Run 4d5e6f7a... | ❌ FAILED    | INCIDENTE #2: Retry Automático sem Correção (Airflow Retries Esgotados)
  │  └─ 💥 Causa Raiz: SodaScanFailed: Quality Gate failed. 184 invalid rows detected in fct_financial_transactions.
  ├─ Run 5e6f7a8b... | ✅ COMPLETED | RECUPERAÇÃO: Hotfix publicado pela engenharia e reprocessamento com sucesso
  └─ Run 6f7a8b9c... | ✅ COMPLETED | Execução Regular Atual (Estado Saudável Restaurado)

================================================================================
🌐 SUCESSO: Telemetria sincronizada com sucesso na API do Marquez!
================================================================================
```

---

### Passo 4: Inspeção Visual do Histórico no Marquez UI (Porta 3000)

1. Acesse o **Marquez Web UI** em `http://localhost:3000` (ou utilize o *Simple Browser* do VS Code).
2. Selecione o Namespace **`fiap.mba.dpm`**.
3. Clique no nó do job **`dbt_build_marts_financial`**:
   * Observe a aba lateral de **Runs**: você verá o histórico com badges verdes (**COMPLETED**) e vermelhos (**FAILED**).
   * Clique em uma das execuções em vermelho para ver a mensagem de erro do facet (`ErrorMessageRunFacet`) com o diagnóstico de violação de contrato.

---

### Passo 5: Auditoria Automatizada de SRE & Consumo de Error Budget

Agora que os metadados de execução estão registrados no servidor, execute o motor de auditoria de SRE. Ele consumirá a API REST do Marquez (`/api/v1/namespaces/fiap.mba.dpm/jobs/dbt_build_marts_financial/runs`) e calculará os indicadores reais de confiabilidade:

```bash
python audit_downtime_slo.py
```

**Saída esperada:**
```text
================================================================================
📊 MOTOR DE AUDITORIA DE DATA SRE: SLI/SLO, ERROR BUDGET & DATA DOWNTIME
================================================================================
[*] Conectando à API REST do Marquez em http://localhost:5000...
  └─ [OK] 6 execuções reais coletadas da API do Marquez.

INCIDENTE      | STATUS       | MTTD (min) | MTTR (min) | DOWNTIME TOTAL   | CAUSA RAIZ
----------------------------------------------------------------------------------------------------
INC-2026-001   | RESOLVIDO    |      0.8 m |    359.2 m |      360.0 min (6.0h) | DataContractException: Check 'custo...
----------------------------------------------------------------------------------------------------

[📈 INDICADORES SRE & SLIS]:
  ├─ Fonte de Telemetria:              MARQUEZ_REST_API
  ├─ Total de Execuções Inspecionadas: 6 (Sucesso: 4 | Falhas: 2)
  ├─ SLI Real de Disponibilidade:      66.7%
  ├─ MTTD Médio (Detecção):            0.8 minutos
  ├─ MTTR Médio (Recuperação):         359.2 minutos (6.0 horas)
  └─ Data Downtime Acumulado:          360.0 minutos (6.0 horas)

[🎯 AUDITORIA DE CONTRATO DE SERVIÇO (SLO)]:
  ├─ Meta Contratual (SLO Acordado):   99.0%
  ├─ Orçamento de Falha (Budget):      432 minutos/mês
  ├─ Tempo Consumido por Incidentes:   360 minutos
  └─ Consumo do Error Budget:          83.3%

💡 [CASO DE NEGÓCIO & ROI]:
  ├─ Prejuízo Financeiro Acumulado no Período: $ 90,000.00 (~R$ 486,000.00)
  └─ Relatório Executivo Gerado:               'DATA_RELIABILITY_REPORT.md'
================================================================================
```

> [!TIP]
> **Modo de Contingência (Resiliência):** Caso o Marquez não esteja respondendo por restrições locais de rede, o script automaticamente recorre ao snapshot local gravado em `marquez_runs_fallback.json`, garantindo a execução integral da auditoria sem interrupção.

---

### Passo 6: Análise dos Artefatos de Governança Gerados

Abra e examine os relatórios executivos gerados na pasta do laboratório:

1. **[`DATA_RELIABILITY_REPORT.md`](DATA_RELIABILITY_REPORT.md):**
   * Relatório executivo formatado para diretores e C-Level, traduzindo falhas técnicas em impacto de negócio ($ / R$) e apresentando a taxa de retorno sobre investimento (ROI) da observabilidade de dados.
2. **[`DEPLOY_FREEZE.md`](DEPLOY_FREEZE.md) *(quando aplicável)*:**
   * Se o consumo do Error Budget ultrapassar 100%, o script gera automaticamente a ordem formal de congelamento de novos deploys até que a dívida técnica seja quitada pela engenharia.

---

## 🧪 Validação & Critérios de Aceite

Para considerar o Lab 07 concluído:
1. O script `simulate_pipeline_incidents.py` deve emitir as execuções de telemetria operacional para o Marquez.
2. O histórico de execuções com badges verdes e vermelhos deve ser visualizado no Marquez UI (porta 3000).
3. O script `audit_downtime_slo.py` deve consumir a API REST do Marquez e calcular disponibilidade, MTTD, MTTR e consumo de Error Budget.
4. O relatório executivo `DATA_RELIABILITY_REPORT.md` deve ser inspecionado com as métricas financeiras de ROI.

---

## 🧹 Cleanup

Retorne para a raiz dos laboratórios:

```bash
cd ..
```

---

## 💡 Desafios Complementares

1. **Simulação de Esgotamento de Error Budget (Freeze):** Modifique o `simulate_pipeline_incidents.py` para aumentar a duração do downtime da falha para 8 horas e reexecute a auditoria para forçar a queima de mais de 100% do Error Budget, observando a emissão automática do `DEPLOY_FREEZE.md`.
2. **Inclusão de Facet de Custo:** Adicione um facet customizado no OpenLineage com o custo operacional por hora do cluster de computação e integre esse valor diretamente no cálculo financeiro do `audit_downtime_slo.py`.
