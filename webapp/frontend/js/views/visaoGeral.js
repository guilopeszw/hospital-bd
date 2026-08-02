import { apiGet } from "../core/api.js";
import { esc, fmtData, fmtMoeda, tabela } from "../core/format.js";

export async function carregarVisaoGeral() {
  try {
    const s = await apiGet("/dashboard/summary");
    document.getElementById("stat-grid").innerHTML = `
      <div class="stat-card">
        <p class="stat-card__label">Pacientes cadastrados</p>
        <p class="stat-card__value">${esc(s.total_pacientes)}</p>
      </div>
      <div class="stat-card">
        <p class="stat-card__label">Atendimentos no mês</p>
        <p class="stat-card__value">${esc(s.atendimentos_mes)}</p>
      </div>
      <div class="stat-card stat-card--amber">
        <p class="stat-card__label">Plantões hoje</p>
        <p class="stat-card__value">${esc(s.plantoes_hoje)}</p>
      </div>
      <div class="stat-card stat-card--coral">
        <p class="stat-card__label">Faturamento do mês</p>
        <p class="stat-card__value">${fmtMoeda(s.faturamento_mes)}</p>
      </div>
      <div class="stat-card">
        <p class="stat-card__label">Pacientes internados</p>
        <p class="stat-card__value">${esc(s.pacientes_internados)}</p>
      </div>
      <div class="stat-card stat-card--amber">
        <p class="stat-card__label">Residentes sem supervisor</p>
        <p class="stat-card__value">${esc(s.residentes_sem_supervisor)}</p>
      </div>
    `;
  } catch {
    document.getElementById("stat-grid").innerHTML = `<div class="empty" style="grid-column:1/-1">Não foi possível carregar o resumo. Confira se a API (python app.py) está rodando em localhost:5055.</div>`;
  }

  try {
    const at = await apiGet("/atendimentos?limite=6");
    document.getElementById("preview-atendimentos").innerHTML = tabela(
      ["Data", "Paciente", "Residente", "Preceptor"],
      at,
      (a) => `<tr>
        <td>${fmtData(a.data_hora)}</td>
        <td>${esc(a.paciente)}</td>
        <td>${esc(a.residente)}</td>
        <td>${esc(a.preceptor)}</td>
      </tr>`
    );
  } catch {
    document.getElementById("preview-atendimentos").innerHTML = `<div class="empty">Sem dados disponíveis.</div>`;
  }
}
