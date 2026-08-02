import { apiGet } from "../core/api.js";
import { esc, tabela } from "../core/format.js";
import { DIA_LEGIVEL, TURNO_LEGIVEL } from "../core/constants.js";

export async function carregarEscalas() {
  const alvo = document.getElementById("tabela-escalas");
  try {
    const escalas = await apiGet("/escalas");
    alvo.innerHTML = tabela(
      ["Unidade", "Dia", "Turno", "Residente", "Preceptor"],
      escalas,
      (e) => `<tr>
        <td>${esc(e.unidade)}</td>
        <td>${esc(DIA_LEGIVEL[e.dia_semana] || e.dia_semana)}</td>
        <td>${esc(TURNO_LEGIVEL[e.turno] || e.turno)}</td>
        <td>${esc(e.residente)}</td>
        <td>${esc(e.preceptor)}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar as escalas.</div>`;
  }
}
