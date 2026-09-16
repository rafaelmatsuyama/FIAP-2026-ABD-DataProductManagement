from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import requests

MARQUEZ_API_URL = "http://localhost:5000/api/v1/namespaces/fiap.mba.dpm/jobs/dbt_build_marts_financial/runs"
FALLBACK_FILE = Path("marquez_runs_fallback.json")
REPORT_FILE = Path("DATA_RELIABILITY_REPORT.md")
FREEZE_FILE = Path("DEPLOY_FREEZE.md")

# Parâmetros Contratuais de Confiabilidade (SLO)
TARGET_SLO_PERCENT = 99.0
COST_PER_DOWNTIME_HOUR_USD = 15000.0  # Impacto financeiro de downtime corporativo em decisões de risco/crédito

def parse_iso(ts_str):
    if not ts_str:
        return None
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

def fetch_runs_telemetry():
    """Busca telemetria diretamente da API REST do Marquez ou recorre ao fallback local."""
    print("[*] Conectando à API REST do Marquez em http://localhost:5000...")
    try:
        resp = requests.get(MARQUEZ_API_URL, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("runs", [])
            print(f"  └─ [OK] {len(runs)} execuções reais coletadas da API do Marquez.")
            return runs, "MARQUEZ_REST_API"
    except Exception as e:
        print(f"  ⚠️  [INFO] Conexão com Marquez API indisponível: {e}")

    if FALLBACK_FILE.exists():
        print(f"  └─ [OK] Carregando telemetria a partir do snapshot local '{FALLBACK_FILE}'...")
        with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("runs", []), "LOCAL_SNAPSHOT_FALLBACK"

    print("[ERRO] Nenhuma fonte de telemetria disponível. Execute 'python simulate_pipeline_incidents.py' primeiro.")
    sys.exit(1)

def main():
    print("=" * 80)
    print("📊 MOTOR DE AUDITORIA DE DATA SRE: SLI/SLO, ERROR BUDGET & DATA DOWNTIME")
    print("=" * 80)

    raw_runs, source = fetch_runs_telemetry()
    if not raw_runs:
        print("[ERRO] Nenhuma execução encontrada para o job 'dbt_build_marts_financial'.")
        return

    # Ordenar execuções cronologicamente
    runs = []
    for r in raw_runs:
        started = parse_iso(r.get("startedAt"))
        ended = parse_iso(r.get("endedAt"))
        state = r.get("state")
        error_msg = r.get("errorMessage") or r.get("facets", {}).get("errorMessage", {}).get("message")
        runs.append({
            "id": r.get("id"),
            "state": state,
            "startedAt": started,
            "endedAt": ended,
            "error": error_msg
        })

    runs.sort(key=lambda x: x["startedAt"] or datetime.min.replace(tzinfo=timezone.utc))

    total_runs = len(runs)
    completed_runs = sum(1 for r in runs if r["state"] == "COMPLETED")
    failed_runs = sum(1 for r in runs if r["state"] == "FAILED")

    # 1. Cálculo de SLI de Disponibilidade Operacional
    availability_sli = (completed_runs / total_runs) * 100.0 if total_runs > 0 else 0.0

    # 2. Identificação de Incidentes, MTTD e MTTR
    incidents = []
    current_incident = None

    for i, r in enumerate(runs):
        if r["state"] == "FAILED":
            if current_incident is None:
                current_incident = {
                    "incident_id": f"INC-2026-{len(incidents) + 1:03d}",
                    "failed_run_id": r["id"],
                    "failure_time": r["startedAt"],
                    "detection_time": r["endedAt"],  # Detectado imediatamente pelo Quality Gate/OpenLineage
                    "resolution_time": None,
                    "error_cause": r["error"] or "Data pipeline runtime error"
                }
        elif r["state"] == "COMPLETED":
            if current_incident is not None:
                current_incident["resolution_time"] = r["endedAt"]
                incidents.append(current_incident)
                current_incident = None

    if current_incident is not None:
        current_incident["resolution_time"] = datetime.now(timezone.utc)
        incidents.append(current_incident)

    total_downtime_minutes = 0.0
    mttd_list = []
    mttr_list = []

    print(f"\n{'INCIDENTE':<14} | {'STATUS':<12} | {'MTTD (min)':<10} | {'MTTR (min)':<10} | {'DOWNTIME TOTAL':<16} | CAUSA RAIZ")
    print("-" * 100)

    for inc in incidents:
        t_fail = inc["failure_time"]
        t_det = inc["detection_time"]
        t_res = inc["resolution_time"]

        mttd = (t_det - t_fail).total_seconds() / 60.0 if (t_det and t_fail) else 0.0
        mttr = (t_res - t_det).total_seconds() / 60.0 if (t_res and t_det) else 0.0
        downtime = (t_res - t_fail).total_seconds() / 60.0 if (t_res and t_fail) else 0.0

        mttd_list.append(mttd)
        mttr_list.append(mttr)
        total_downtime_minutes += downtime

        cause_short = inc["error_cause"][:35] + "..." if len(inc["error_cause"]) > 35 else inc["error_cause"]
        print(f"{inc['incident_id']:<14} | {'RESOLVIDO':<12} | {mttd:>8.1f} m | {mttr:>8.1f} m | {downtime:>10.1f} min ({downtime/60:.1f}h) | {cause_short}")

    avg_mttd = sum(mttd_list) / len(mttd_list) if mttd_list else 0.0
    avg_mttr = sum(mttr_list) / len(mttr_list) if mttr_list else 0.0

    # 3. Auditoria do Error Budget (Janela Operacional Mensal de 43.200 minutos)
    MONTH_MINUTES = 30 * 24 * 60
    ALLOWED_DOWNTIME_MINUTES = MONTH_MINUTES * ((100.0 - TARGET_SLO_PERCENT) / 100.0)  # 432 min para 99.0%
    budget_consumed_percent = (total_downtime_minutes / ALLOWED_DOWNTIME_MINUTES) * 100.0

    total_loss_usd = (total_downtime_minutes / 60.0) * COST_PER_DOWNTIME_HOUR_USD
    total_loss_brl = total_loss_usd * 5.40

    print("-" * 100)
    print(f"\n[📈 INDICADORES SRE & SLIS]:")
    print(f"  ├─ Fonte de Telemetria:            {source}")
    print(f"  ├─ Total de Execuções Inspecionadas: {total_runs} (Sucesso: {completed_runs} | Falhas: {failed_runs})")
    print(f"  ├─ SLI Real de Disponibilidade:    {availability_sli:.1f}%")
    print(f"  ├─ MTTD Médio (Detecção):          {avg_mttd:.1f} minutos")
    print(f"  ├─ MTTR Médio (Recuperação):       {avg_mttr:.1f} minutos ({avg_mttr/60:.1f} horas)")
    print(f"  └─ Data Downtime Acumulado:        {total_downtime_minutes:.1f} minutos ({total_downtime_minutes/60:.1f} horas)")

    print(f"\n[🎯 AUDITORIA DE CONTRATO DE SERVIÇO (SLO)]:")
    print(f"  ├─ Meta Contratual (SLO Acordado): {TARGET_SLO_PERCENT:.1f}%")
    print(f"  ├─ Orçamento de Falha (Budget):    {ALLOWED_DOWNTIME_MINUTES:.0f} minutos/mês")
    print(f"  ├─ Tempo Consumido por Incidentes: {total_downtime_minutes:.0f} minutos")
    print(f"  └─ Consumo do Error Budget:        {budget_consumed_percent:.1f}%")

    is_freeze = budget_consumed_percent > 100.0

    if is_freeze:
        print(f"\n🚨 [CRÍTICO]: ERROR BUDGET ESGOTADO ({budget_consumed_percent:.1f}%)!")
        print("   A confiabilidade do Data Product foi rompida neste ciclo.")
        print(f"   Gerando política de governança mandatória em '{FREEZE_FILE}'...")

        with open(FREEZE_FILE, "w", encoding="utf-8") as f:
            f.write(f"""# 🚨 DIRETRIZ DE ENGENHARIA: DEPLOY FREEZE ATIVO
**Data Product:** `dbt_build_marts_financial` (Namespace: `fiap.mba.dpm`)  
**Data da Auditoria:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Status do Error Budget:** **ESGOTADO ({budget_consumed_percent:.1f}% consumido)**  

---

## 🛑 Decisão de Governança
O orçamento de falhas permitido pelo contrato de SLO ({TARGET_SLO_PERCENT}%) foi **ultrapassado em {budget_consumed_percent - 100:.1f}%**.

De acordo com as boas práticas de **Site Reliability Engineering (SRE)** aplicadas a Produtos de Dados:
1. **CONGELAMENTO DE NOVAS FEATURES:** Fica terminantemente suspenso o deploy de novos modelos dbt, transformações ou novos campos neste produto de dados.
2. **PRIORIZAÇÃO DE CONFIABILIDADE (100% SPRINT):** A equipe de engenharia deve dedicar a próxima sprint exclusivamente a:
   * Endurecer **Data Quality Gates** com Soda Core na camada de staging.
   * Ativar alertas automáticos via OpenLineage antes da quebra de downstream consumers.
   * Investigar e sanar a causa raiz da violação de nulls em `customer_id`.
3. **CRITÉRIO DE DESCONGELAMENTO:** O freeze será revogado apenas após 7 dias corridos de execuções com 100% de sucesso e restauração da margem do Error Budget.
""")

    # Geração do Relatório Executivo de ROI
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"""# 📋 Relatório Executivo de Confiabilidade & ROI de Observabilidade
**Data Product:** `fct_financial_transactions`  
**Pipeline:** `dbt_build_marts_financial`  
**Namespace:** `fiap.mba.dpm`  
**Data:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  

---

## 1. Diagnóstico Operacional (SLIs & Incidentes)
* **Disponibilidade Real:** {availability_sli:.1f}% (Meta SLO: {TARGET_SLO_PERCENT:.1f}%)
* **Incidentes Registrados:** {len(incidents)}
* **Tempo Médio de Detecção (MTTD):** {avg_mttd:.1f} minutos
* **Tempo Médio de Recuperação (MTTR):** {avg_mttr:.1f} minutos ({avg_mttr/60:.1f} horas)
* **Data Downtime Total Acumulado:** {total_downtime_minutes:.1f} minutos ({total_downtime_minutes/60:.1f} horas)
* **Impacto Financeiro Estimado:** **$ {total_loss_usd:,.2f}** (~R$ {total_loss_brl:,.2f})

---

## 2. Status de Governança & Error Budget
* **Error Budget Permitido:** {ALLOWED_DOWNTIME_MINUTES:.0f} minutos/mês
* **Consumo Real:** {budget_consumed_percent:.1f}%
* **Status Atual:** **{'🚨 DEPLOY FREEZE ATIVO' if is_freeze else '✅ DENTRO DA MARGEM'}**

---

## 3. Justificativa de Negócio & ROI da Observabilidade
A implantação combinada de **Soda Core** (Quality Gates no CI/CD) e **OpenLineage + Marquez** (Rastreabilidade e telemetria operacional) reduz o MTTD e o MTTR médio de horas para minutos:
* **Prevenção de Quebras Silenciosas:** Bloqueio imediato na ingestão antes que dados corrompidos atinjam o Data Mart e o BI Executivo.
* **Economia Projetada Anualizada:** Redução de 80% no Data Downtime, gerando economia estimada superior a **$ {total_loss_usd * 0.8 * 12:,.2f}/ano**.
""")

    print(f"\n💡 [CASO DE NEGÓCIO & ROI]:")
    print(f"  ├─ Prejuízo Financeiro Acumulado no Período: $ {total_loss_usd:,.2f} (~R$ {total_loss_brl:,.2f})")
    print(f"  ├─ Relatório Executivo Gerado:               '{REPORT_FILE}'")
    if is_freeze:
        print(f"  └─ Política de Deploy Freeze Gerada:         '{FREEZE_FILE}'")
    print("=" * 80)

if __name__ == "__main__":
    main()
