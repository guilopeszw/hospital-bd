import { apiGet } from "../core/api.js";
import { esc, fmtData, tabela } from "../core/format.js";
import { DIA_LEGIVEL, TURNO_LEGIVEL } from "../core/constants.js";

export async function carregarIndicadores() {
  apiGet("/analytics/ranking-residentes")
    .then((rows) => {
      document.getElementById("ranking-residentes").innerHTML = tabela(
        ["Residente", "Ano", "Atendimentos"],
        rows,
        (r) => `<tr><td>${esc(r.residente)}</td><td>${esc(r.ano_residencia)}</td><td><strong>${esc(r.total_atendimentos)}</strong></td></tr>`
      );
    })
    .catch(() => { document.getElementById("ranking-residentes").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/analytics/tempo-medio-residente")
    .then((rows) => {
      document.getElementById("tempo-medio").innerHTML = tabela(
        ["Residente", "Especialidade", "Tempo médio"],
        rows,
        (r) => `<tr><td>${esc(r.residente)}</td><td>${esc(r.especialidade)}</td><td>${r.tempo_medio_minutos != null ? esc(r.tempo_medio_minutos) + " min" : "—"}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("tempo-medio").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/analytics/plantoes-mes")
    .then((rows) => {
      document.getElementById("plantoes-mes").innerHTML = tabela(
        ["Unidade", "Residente", "Plantões"],
        rows,
        (r) => `<tr><td>${esc(r.unidade)}</td><td>${esc(r.residente)}</td><td><strong>${esc(r.total_plantoes_no_mes)}</strong></td></tr>`
      );
    })
    .catch(() => { document.getElementById("plantoes-mes").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/analytics/pacientes-sem-risco-alto")
    .then((rows) => {
      document.getElementById("sem-risco-alto").innerHTML = tabela(
        ["Paciente", "Convênio"],
        rows,
        (r) => `<tr><td>${esc(r.paciente)}</td><td>${esc(r.num_convenio || "—")}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("sem-risco-alto").innerHTML = `<div class="empty">Sem dados.</div>`; });

  // stored procedure sp_calcular_tempo_medio_espera
  apiGet("/analytics/tempo-medio-espera")
    .then((rows) => {
      document.getElementById("tempo-medio-espera").innerHTML = tabela(
        ["Unidade", "Atendimentos medidos", "Espera média"],
        rows,
        (r) => `<tr><td>${esc(r.unidade)}</td><td>${esc(r.atendimentos_medidos)}</td><td>${esc(r.espera_media_minutos)} min</td></tr>`
      );
    })
    .catch(() => { document.getElementById("tempo-medio-espera").innerHTML = `<div class="empty">Sem dados.</div>`; });

  // view vw_pacientes_internados
  apiGet("/views/pacientes-internados")
    .then((rows) => {
      document.getElementById("pacientes-internados").innerHTML = tabela(
        ["Paciente", "Unidade", "Entrada", "Motivo"],
        rows,
        (r) => `<tr><td>${esc(r.paciente)}</td><td>${esc(r.unidade)}</td><td>${fmtData(r.data_hora_entrada)}</td><td>${esc(r.motivo || "—")}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("pacientes-internados").innerHTML = `<div class="empty">Sem dados.</div>`; });

  // view vw_residentes_sem_supervisor
  apiGet("/views/residentes-sem-supervisor")
    .then((rows) => {
      document.getElementById("residentes-sem-supervisor").innerHTML = tabela(
        ["Residente", "Unidade", "Dia/turno", "Preceptor", "Titulação"],
        rows,
        (r) => `<tr><td>${esc(r.residente)}</td><td>${esc(r.unidade)}</td><td>${esc(DIA_LEGIVEL[r.dia_semana] || r.dia_semana)}/${esc(TURNO_LEGIVEL[r.turno] || r.turno)}</td><td>${esc(r.preceptor)}</td><td>${esc(r.titulacao)}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("residentes-sem-supervisor").innerHTML = `<div class="empty">Sem dados.</div>`; });

  // view vw_estatisticas_atendimentos_mensal
  apiGet("/views/estatisticas-mensais")
    .then((rows) => {
      document.getElementById("estatisticas-mensais").innerHTML = tabela(
        ["Mês", "Unidade", "Atendimentos", "Duração média", "Procedimento mais comum"],
        rows,
        (r) => `<tr><td>${fmtData(r.mes)}</td><td>${esc(r.unidade)}</td><td><strong>${esc(r.total_atendimentos)}</strong></td><td>${r.duracao_media_minutos != null ? esc(r.duracao_media_minutos) + " min" : "—"}</td><td>${esc(r.procedimento_mais_comum || "—")}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("estatisticas-mensais").innerHTML = `<div class="empty">Sem dados.</div>`; });

  // Etapa 2 — item 5: consultas avançadas via ORM (src/etapa2/consultas_avancadas.py)
  apiGet("/orm/preceptores-supervisionaram-flamenguistas")
    .then((nomes) => {
      document.getElementById("orm-preceptores-flamenguistas").innerHTML = tabela(
        ["Preceptor"],
        nomes,
        (nome) => `<tr><td>${esc(nome)}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("orm-preceptores-flamenguistas").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/orm/ultimo-atendimento-por-paciente")
    .then((rows) => {
      document.getElementById("orm-ultimo-atendimento").innerHTML = tabela(
        ["Paciente", "Data", "Residente", "Preceptor", "Procedimentos"],
        rows,
        (r) => `<tr><td>${esc(r.paciente)}</td><td>${fmtData(r.data_hora)}</td><td>${esc(r.residente)}</td><td>${esc(r.preceptor)}</td><td>${esc(r.procedimentos.join(", ") || "—")}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("orm-ultimo-atendimento").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/orm/percentual-alto-risco-por-residente")
    .then((rows) => {
      document.getElementById("orm-percentual-alto-risco").innerHTML = tabela(
        ["Residente", "Total procedimentos", "Alto risco", "% alto risco"],
        rows,
        (r) => `<tr><td>${esc(r.residente)}</td><td>${esc(r.total_procedimentos)}</td><td>${esc(r.alto_risco)}</td><td><strong>${esc(r.percentual_alto_risco)}%</strong></td></tr>`
      );
    })
    .catch(() => { document.getElementById("orm-percentual-alto-risco").innerHTML = `<div class="empty">Sem dados.</div>`; });
}
