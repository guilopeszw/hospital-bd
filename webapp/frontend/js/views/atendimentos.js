import { apiGet } from "../core/api.js";
import { esc, fmtData, idChip, tabela } from "../core/format.js";

export async function carregarAtendimentos() {
  const alvo = document.getElementById("tabela-atendimentos");
  try {
    const at = await apiGet("/atendimentos?limite=200");
    alvo.innerHTML = tabela(
      ["Data", "Paciente", "Residente", "Preceptor", "Duração", "ID"],
      at,
      (a) => `<tr>
        <td>${fmtData(a.data_hora)}</td>
        <td>${esc(a.paciente)}</td>
        <td>${esc(a.residente)}</td>
        <td>${esc(a.preceptor)}</td>
        <td>${esc(a.duracao_minutos)} min</td>
        <td>${idChip(a.id_atendimento)}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar os atendimentos.</div>`;
  }
}
